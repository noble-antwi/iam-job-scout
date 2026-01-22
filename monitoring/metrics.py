"""
Prometheus metrics for IAM Job Scout application.
Organized by the 4 Golden Signals + Business Metrics.
"""

import time
from prometheus_client import Counter, Gauge, Histogram, Info
from typing import Optional
from db.database import SessionLocal


# ==============================================================================
# 1. LATENCY METRICS - How long things take
# ==============================================================================

HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint', 'status_code'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

EXTERNAL_API_DURATION = Histogram(
    'external_api_duration_seconds',
    'External API call duration in seconds',
    ['api_name', 'endpoint'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)

SCAN_DURATION = Histogram(
    'scan_duration_seconds',
    'Job scan operation duration in seconds',
    buckets=(10, 30, 60, 120, 300, 600, 1800, 3600)
)


# ==============================================================================
# 2. TRAFFIC METRICS - Request rate and volume
# ==============================================================================

HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently being processed',
    ['method', 'endpoint']
)

ACTIVE_SESSIONS = Gauge(
    'active_user_sessions',
    'Number of active user sessions'
)

EXTERNAL_API_REQUESTS_TOTAL = Counter(
    'external_api_requests_total',
    'Total external API requests',
    ['api_name', 'status']
)


# ==============================================================================
# 3. ERRORS METRICS - Error rates
# ==============================================================================

APPLICATION_ERRORS = Counter(
    'application_errors_total',
    'Total application errors',
    ['error_type', 'endpoint', 'severity']
)

DB_ERRORS_TOTAL = Counter(
    'database_errors_total',
    'Total database errors',
    ['operation', 'error_type']
)

EXTERNAL_API_ERRORS = Counter(
    'external_api_errors_total',
    'External API errors',
    ['api_name', 'error_type']
)

SCAN_ERRORS = Counter(
    'scan_errors_total',
    'Job scan errors',
    ['error_type']
)


# ==============================================================================
# 4. SATURATION METRICS - Resource utilization
# ==============================================================================

DB_CONNECTIONS_ACTIVE = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

DB_CONNECTIONS_IDLE = Gauge(
    'db_connections_idle',
    'Number of idle database connections'
)

MEMORY_USAGE_BYTES = Gauge(
    'process_memory_bytes',
    'Process memory usage in bytes'
)

UPTIME_SECONDS = Gauge(
    'application_uptime_seconds',
    'Application uptime in seconds'
)


# ==============================================================================
# BUSINESS METRICS - Domain-specific metrics for IAM Job Scout
# ==============================================================================

JOBS_TOTAL = Gauge(
    'iam_jobs_total',
    'Total number of jobs in database'
)

JOBS_NEW_THIS_WEEK = Gauge(
    'iam_jobs_new_this_week',
    'Number of jobs added in the last 7 days'
)

JOBS_SAVED = Gauge(
    'iam_jobs_saved',
    'Number of jobs marked as saved'
)

JOBS_APPLIED = Gauge(
    'iam_jobs_applied',
    'Number of jobs marked as applied'
)

JOBS_HIDDEN = Gauge(
    'iam_jobs_hidden',
    'Number of jobs marked as hidden'
)

SCAN_RUNS_TOTAL = Counter(
    'iam_scan_runs_total',
    'Total number of scan runs',
    ['status']  # success, failed, error
)

SCAN_JOBS_FOUND = Gauge(
    'iam_scan_jobs_found_last',
    'Number of jobs found in last scan'
)

SCAN_NEW_JOBS = Gauge(
    'iam_scan_new_jobs_last',
    'Number of new jobs added in last scan'
)

LAST_SUCCESSFUL_SCAN_TIMESTAMP = Gauge(
    'iam_last_successful_scan_timestamp',
    'Unix timestamp of last successful scan'
)

JOB_STATUS_UPDATES = Counter(
    'iam_job_status_updates_total',
    'Total job status updates',
    ['status']  # saved, applied, hidden
)


# ==============================================================================
# DATABASE OPERATION METRICS
# ==============================================================================

DB_OPERATIONS_TOTAL = Counter(
    'db_operations_total',
    'Total database operations',
    ['operation', 'table', 'status']  # operation: select, insert, update, delete
)


# ==============================================================================
# APPLICATION INFO
# ==============================================================================

APP_INFO = Info(
    'iam_job_scout_app',
    'Application information'
)


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def update_business_metrics():
    """
    Update business metrics by querying the database.
    Call this periodically (e.g., every 30 seconds) or after significant events.
    """
    from jobs.job_service import JobService
    
    db = SessionLocal()
    try:
        job_service = JobService(db)
        stats = job_service.get_job_stats()
        
        # Update gauges with current values
        JOBS_TOTAL.set(stats.get('total_jobs', 0))
        JOBS_NEW_THIS_WEEK.set(stats.get('new_this_week', 0))
        JOBS_SAVED.set(stats.get('saved_count', 0))
        JOBS_APPLIED.set(stats.get('applied_count', 0))
        
        # Get latest scan info
        latest_scan = job_service.get_latest_scan()
        if latest_scan:
            SCAN_JOBS_FOUND.set(latest_scan.jobs_found or 0)
            SCAN_NEW_JOBS.set(latest_scan.new_jobs or 0)
            
            # Update last successful scan timestamp
            if latest_scan.status == 'completed' and latest_scan.completed_at:
                LAST_SUCCESSFUL_SCAN_TIMESTAMP.set(latest_scan.completed_at.timestamp())
                
    except Exception as e:
        # Log error but don't raise - metrics updates should not break the app
        import logging
        logging.error(f"Error updating business metrics: {e}")
    finally:
        db.close()


def track_db_query(operation: str, table: str):
    """
    Context manager to track database query duration.
    
    Usage:
        with track_db_query('select', 'jobs'):
            # Your database query here
            pass
    """
    from contextlib import contextmanager
    
    @contextmanager
    def _tracker():
        start_time = time.time()
        status = 'success'
        try:
            yield
        except Exception as e:
            status = 'error'
            DB_ERRORS_TOTAL.labels(operation=operation, error_type=type(e).__name__).inc()
            raise
        finally:
            duration = time.time() - start_time
            DB_QUERY_DURATION.labels(operation=operation, table=table).observe(duration)
            DB_OPERATIONS_TOTAL.labels(operation=operation, table=table, status=status).inc()
    
    return _tracker()


def track_external_api(api_name: str, endpoint: str = ''):
    """
    Context manager to track external API call duration and errors.
    
    Usage:
        with track_external_api('jsearch', '/search'):
            response = await httpx.get(url)
    """
    from contextlib import contextmanager
    
    @contextmanager
    def _tracker():
        start_time = time.time()
        status = 'success'
        try:
            yield
        except Exception as e:
            status = 'error'
            EXTERNAL_API_ERRORS.labels(api_name=api_name, error_type=type(e).__name__).inc()
            EXTERNAL_API_REQUESTS_TOTAL.labels(api_name=api_name, status='error').inc()
            raise
        finally:
            duration = time.time() - start_time
            EXTERNAL_API_DURATION.labels(api_name=api_name, endpoint=endpoint).observe(duration)
            if status == 'success':
                EXTERNAL_API_REQUESTS_TOTAL.labels(api_name=api_name, status='success').inc()
    
    return _tracker()


# Initialize app info (call this once at startup)
def initialize_metrics():
    """Initialize static metrics and app info."""
    import os
    APP_INFO.info({
        'version': '1.0.0',
        'python_version': os.sys.version.split()[0],
        'environment': os.getenv('ENVIRONMENT', 'production')
    })
    
    # Set initial uptime
    import time
    _start_time = time.time()
    
    def update_uptime():
        UPTIME_SECONDS.set(time.time() - _start_time)
    
    return update_uptime
