"""
Custom middleware for automatic request tracking with Prometheus metrics.
This middleware captures HTTP request metrics without manual instrumentation.
"""

import time
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from .metrics import (
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUESTS_IN_PROGRESS,
    APPLICATION_ERRORS,
)

logger = logging.getLogger(__name__)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically track HTTP requests with Prometheus metrics.
    
    Captures:
    - Request duration (latency)
    - Request count by method, endpoint, status
    - Requests in progress
    - Errors with context
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    @staticmethod
    def _get_endpoint_name(request: Request) -> str:
        """
        Extract a normalized endpoint name from the request path.
        Converts paths like /job/123 to /job/{id} for better cardinality.
        """
        path = request.url.path
        
        # Health and metrics endpoints
        if path == "/health":
            return "/health"
        if path == "/metrics":
            return "/metrics"
        
        # Static files
        if path.startswith("/static"):
            return "/static"
        
        # Root dashboard
        if path == "/":
            return "/"
        
        # Login/logout
        if path == "/login":
            return "/login"
        if path == "/logout":
            return "/logout"
        
        # Admin endpoints
        if path.startswith("/admin/"):
            if "run-scan" in path:
                return "/admin/run-scan"
            if "cleanup" in path:
                return "/admin/cleanup"
            return "/admin"
        
        # API endpoints
        if path.startswith("/api/"):
            if path == "/api/jobs":
                return "/api/jobs"
            if path == "/api/stats":
                return "/api/stats"
            return "/api"
        
        # Job detail pages - parameterized routes
        if path.startswith("/job/"):
            parts = path.split("/")
            if len(parts) >= 3:
                # /job/123 -> /job/{id}
                if parts[2].isdigit():
                    if len(parts) == 3:
                        return "/job/{id}"
                    # /job/123/status -> /job/{id}/status
                    elif len(parts) == 4:
                        return f"/job/{{id}}/{parts[3]}"
        
        # Saved jobs
        if path == "/saved":
            return "/saved"
        
        # Default: return first path segment
        parts = path.strip("/").split("/")
        if parts and parts[0]:
            return f"/{parts[0]}"
        
        return path
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request and track metrics.
        """
        method = request.method
        endpoint = self._get_endpoint_name(request)
        
        # Track request in progress
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
        
        start_time = time.time()
        status_code = 500  # Default to error if something goes wrong
        
        try:
            # Process the request
            response = await call_next(request)
            status_code = response.status_code
            return response
            
        except Exception as e:
            # Track application errors
            error_type = type(e).__name__
            severity = 'critical' if status_code >= 500 else 'warning'
            
            APPLICATION_ERRORS.labels(
                error_type=error_type,
                endpoint=endpoint,
                severity=severity
            ).inc()
            
            logger.error(
                f"Error processing request: {method} {endpoint}",
                exc_info=True,
                extra={
                    'method': method,
                    'endpoint': endpoint,
                    'error_type': error_type,
                }
            )
            
            # Re-raise the exception to let FastAPI handle it
            raise
            
        finally:
            # Always track metrics, even if there was an error
            duration = time.time() - start_time
            
            # Record request duration
            HTTP_REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).observe(duration)
            
            # Increment request counter
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            # Decrement in-progress counter
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()
            
            # Log slow requests
            if duration > 2.0:  # Log requests taking more than 2 seconds
                logger.warning(
                    f"Slow request: {method} {endpoint} took {duration:.2f}s",
                    extra={
                        'method': method,
                        'endpoint': endpoint,
                        'duration': duration,
                        'status_code': status_code,
                    }
                )


class SessionMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track active user sessions.
    Updates the ACTIVE_SESSIONS gauge based on session data.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Count active sessions from request.
        Note: This is a simple implementation. For production, consider using
        a session store (Redis) for accurate session counting.
        """
        from .metrics import ACTIVE_SESSIONS
        
        # Check if user has active session
        has_session = request.session.get("user") is not None if hasattr(request, 'session') else False
        
        # This is approximate - real implementation would query session store
        # For now, we'll update it in the main app based on actual session data
        
        response = await call_next(request)
        return response
