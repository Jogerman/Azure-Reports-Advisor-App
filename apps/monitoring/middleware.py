"""
Monitoring Middleware for Request Tracking

Automatically tracks all requests with Application Insights
"""

import time
from django.utils.deprecation import MiddlewareMixin
from .telemetry import track_request, BusinessMetrics


class TelemetryMiddleware(MiddlewareMixin):
    """
    Middleware to automatically track HTTP requests to Application Insights
    """

    def process_request(self, request):
        """Store start time on request"""
        request._monitoring_start_time = time.time()

    def process_response(self, request, response):
        """Track request to Application Insights"""
        if hasattr(request, '_monitoring_start_time'):
            duration_ms = int((time.time() - request._monitoring_start_time) * 1000)

            # Skip static files and media
            if not (request.path.startswith('/static/') or request.path.startswith('/media/')):
                success = 200 <= response.status_code < 400

                track_request(
                    name=f'{request.method} {request.path}',
                    url=request.build_absolute_uri(),
                    duration_ms=duration_ms,
                    response_code=response.status_code,
                    success=success,
                    properties={
                        'method': request.method,
                        'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
                        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100],
                    },
                    measurements={
                        'content_length': len(response.content) if hasattr(response, 'content') else 0,
                    }
                )

                # Track API calls separately
                if request.path.startswith('/api/'):
                    BusinessMetrics.track_api_call(
                        endpoint=request.path,
                        method=request.method,
                        status_code=response.status_code,
                        duration_ms=duration_ms,
                        user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None
                    )

        return response
