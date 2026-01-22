"""
Database instrumentation for tracking database operations.
Use these decorators and context managers to track DB performance.
"""

import time
import functools
import inspect
import logging
from contextlib import contextmanager
from typing import Callable, Any

from .metrics import (
    DB_QUERY_DURATION,
    DB_OPERATIONS_TOTAL,
    DB_ERRORS_TOTAL,
    DB_CONNECTIONS_ACTIVE,
    DB_CONNECTIONS_IDLE,
)

logger = logging.getLogger(__name__)


@contextmanager
def track_db_operation(operation: str, table: str):
    """
    Context manager to track database operations.
    
    Args:
        operation: Type of operation (select, insert, update, delete, count)
        table: Table name being operated on
    
    Usage:
        with track_db_operation('select', 'jobs'):
            results = db.query(Job).all()
    """
    start_time = time.time()
    status = 'success'
    
    try:
        yield
    except Exception as e:
        status = 'error'
        error_type = type(e).__name__
        DB_ERRORS_TOTAL.labels(operation=operation, error_type=error_type).inc()
        logger.error(
            f"Database error: {operation} on {table}",
            exc_info=True,
            extra={'operation': operation, 'table': table}
        )
        raise
    finally:
        duration = time.time() - start_time
        DB_QUERY_DURATION.labels(operation=operation, table=table).observe(duration)
        DB_OPERATIONS_TOTAL.labels(operation=operation, table=table, status=status).inc()
        
        # Log slow queries
        if duration > 1.0:
            logger.warning(
                f"Slow query: {operation} on {table} took {duration:.2f}s",
                extra={'operation': operation, 'table': table, 'duration': duration}
            )


def track_db_method(operation: str, table: str):
    """
    Decorator to automatically track database methods.
    
    Usage:
        @track_db_method('select', 'jobs')
        def get_jobs(self, db):
            return db.query(Job).all()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            with track_db_operation(operation, table):
                return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            with track_db_operation(operation, table):
                return await func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def update_connection_pool_metrics(engine):
    """
    Update database connection pool metrics.
    Call this periodically to track connection pool status.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    try:
        pool = engine.pool
        
        # Get pool statistics
        # Note: Not all pool implementations support all these attributes
        if hasattr(pool, 'size'):
            # Total connections (checked out + checked in)
            total_connections = pool.size()
            
            # Checked out connections (active)
            checked_out = pool.checkedout() if hasattr(pool, 'checkedout') else 0
            
            # Idle connections
            idle = total_connections - checked_out
            
            DB_CONNECTIONS_ACTIVE.set(checked_out)
            DB_CONNECTIONS_IDLE.set(idle)
            
    except Exception as e:
        logger.error(f"Error updating connection pool metrics: {e}")


# Example instrumented database service methods
# You can copy these patterns to your job_service.py

class InstrumentedDBExample:
    """
    Example of how to instrument your database service methods.
    Apply these patterns to your actual JobService class.
    """
    
    @track_db_method('select', 'jobs')
    def get_all_jobs(self, db):
        """Example: Get all jobs with automatic tracking."""
        from db.models import Job
        return db.query(Job).all()
    
    @track_db_method('select', 'jobs')
    def search_jobs(self, db, query: str):
        """Example: Search jobs with automatic tracking."""
        from db.models import Job
        return db.query(Job).filter(Job.title.contains(query)).all()
    
    @track_db_method('insert', 'jobs')
    def create_job(self, db, job_data: dict):
        """Example: Create job with automatic tracking."""
        from db.models import Job
        job = Job(**job_data)
        db.add(job)
        db.commit()
        return job
    
    @track_db_method('update', 'jobs')
    def update_job_status(self, db, job_id: int, status: str):
        """Example: Update job status with automatic tracking."""
        from db.models import Job
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            db.commit()
        return job
    
    @track_db_method('delete', 'jobs')
    def delete_old_jobs(self, db, days: int):
        """Example: Delete old jobs with automatic tracking."""
        from datetime import datetime, timedelta
        from db.models import Job
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(Job).filter(Job.created_at < cutoff_date).delete()
        db.commit()
        return deleted
    
    def complex_operation_with_manual_tracking(self, db):
        """
        Example: For complex operations, use the context manager manually
        to track specific portions of the code.
        """
        # Track the query portion
        with track_db_operation('select', 'jobs'):
            jobs = db.query(Job).all()
        
        # Do some processing (not tracked as DB operation)
        processed_jobs = [self._process_job(job) for job in jobs]
        
        # Track the update portion
        with track_db_operation('update', 'jobs'):
            for job in processed_jobs:
                db.merge(job)
            db.commit()
        
        return processed_jobs
