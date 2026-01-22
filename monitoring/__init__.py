"""
Monitoring module for IAM Job Scout application.
Provides Prometheus metrics following the 4 Golden Signals:
1. Latency - How long requests take
2. Traffic - How many requests
3. Errors - Rate of failed requests
4. Saturation - Resource utilization
"""

from .metrics import (
    # Application metrics
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUESTS_IN_PROGRESS,
    APPLICATION_ERRORS,
    ACTIVE_SESSIONS,
    
    # Business metrics
    JOBS_TOTAL,
    JOBS_NEW_THIS_WEEK,
    JOBS_SAVED,
    JOBS_APPLIED,
    SCAN_RUNS_TOTAL,
    SCAN_JOBS_FOUND,
    SCAN_NEW_JOBS,
    SCAN_DURATION,
    SCAN_ERRORS,
    
    # Database metrics
    DB_QUERY_DURATION,
    DB_CONNECTIONS_ACTIVE,
    DB_OPERATIONS_TOTAL,
    DB_ERRORS_TOTAL,
    
    # External API metrics
    EXTERNAL_API_DURATION,
    EXTERNAL_API_REQUESTS_TOTAL,
    EXTERNAL_API_ERRORS,
    
    # System metrics
    LAST_SUCCESSFUL_SCAN_TIMESTAMP,
    UPTIME_SECONDS,
    JOB_STATUS_UPDATES,
    
    # Helper functions
    update_business_metrics,
    initialize_metrics,
)

from .middleware import PrometheusMiddleware

__all__ = [
    # Middleware
    'PrometheusMiddleware',
    
    # Metrics
    'HTTP_REQUEST_DURATION',
    'HTTP_REQUESTS_TOTAL',
    'HTTP_REQUESTS_IN_PROGRESS',
    'APPLICATION_ERRORS',
    'ACTIVE_SESSIONS',
    'JOBS_TOTAL',
    'JOBS_NEW_THIS_WEEK',
    'JOBS_SAVED',
    'JOBS_APPLIED',
    'SCAN_RUNS_TOTAL',
    'SCAN_JOBS_FOUND',
    'SCAN_NEW_JOBS',
    'SCAN_DURATION',
    'SCAN_ERRORS',
    'DB_QUERY_DURATION',
    'DB_CONNECTIONS_ACTIVE',
    'DB_OPERATIONS_TOTAL',
    'DB_ERRORS_TOTAL',
    'EXTERNAL_API_DURATION',
    'EXTERNAL_API_REQUESTS_TOTAL',
    'EXTERNAL_API_ERRORS',
    'LAST_SUCCESSFUL_SCAN_TIMESTAMP',
    'UPTIME_SECONDS',
    'JOB_STATUS_UPDATES',
    'update_business_metrics',
    'initialize_metrics',
]
