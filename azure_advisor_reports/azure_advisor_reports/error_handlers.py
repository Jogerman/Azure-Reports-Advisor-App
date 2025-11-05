"""
Custom Error Handlers for Production Environment
Prevents exposure of sensitive information in error responses
"""

import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

# Initialize security logger
security_logger = logging.getLogger('security')
error_logger = logging.getLogger('django.request')


def handler400(request, exception=None):
    """
    Custom handler for 400 Bad Request errors.

    Returns user-friendly error page without exposing system details.
    Logs the error internally for debugging.
    """
    error_logger.warning(
        f'Bad Request (400): {request.path}',
        extra={
            'status_code': 400,
            'request': request,
        }
    )

    # Return JSON for API requests
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Bad Request',
            'message': 'The request could not be understood or was missing required parameters.',
            'status': 400
        }, status=400)

    # Return HTML for regular requests
    return render(request, '400.html', status=400)


def handler403(request, exception=None):
    """
    Custom handler for 403 Forbidden errors.

    Returns user-friendly error page without exposing system details.
    Logs security-relevant access attempts.
    """
    security_logger.warning(
        f'Forbidden Access (403): {request.path}',
        extra={
            'status_code': 403,
            'request': request,
            'user': request.user if hasattr(request, 'user') else 'Anonymous',
        }
    )

    # Return JSON for API requests
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource.',
            'status': 403
        }, status=403)

    # Return HTML for regular requests
    return render(request, '403.html', status=403)


def handler404(request, exception=None):
    """
    Custom handler for 404 Not Found errors.

    Returns user-friendly error page without exposing system details.
    Logs unusual 404 patterns that might indicate scanning/probing.
    """
    # Log suspicious paths that might indicate security scanning
    suspicious_paths = [
        '.env', 'wp-admin', 'phpMyAdmin', '.git', 'admin.php',
        'config.php', 'backup', '.sql', 'xmlrpc.php'
    ]

    if any(suspicious in request.path.lower() for suspicious in suspicious_paths):
        security_logger.warning(
            f'Suspicious 404 Request: {request.path}',
            extra={
                'status_code': 404,
                'request': request,
                'ip_address': get_client_ip(request),
            }
        )
    else:
        error_logger.info(
            f'Not Found (404): {request.path}',
            extra={
                'status_code': 404,
                'request': request,
            }
        )

    # Return JSON for API requests
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Not Found',
            'message': 'The requested resource was not found.',
            'status': 404
        }, status=404)

    # Return HTML for regular requests
    return render(request, '404.html', status=404)


def handler500(request):
    """
    Custom handler for 500 Internal Server Error.

    Returns generic error page to prevent information disclosure.
    Logs detailed error information internally.

    IMPORTANT: This handler is called when DEBUG=False and an unhandled
    exception occurs. Never expose stack traces or system details to users.
    """
    error_logger.error(
        f'Internal Server Error (500): {request.path}',
        extra={
            'status_code': 500,
            'request': request,
        },
        exc_info=True  # Include exception information in logs
    )

    # Return JSON for API requests
    if request.path.startswith('/api/'):
        response_data = {
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred. Our team has been notified.',
            'status': 500
        }

        # Include request ID if available (useful for support)
        if hasattr(request, 'request_id'):
            response_data['request_id'] = request.request_id

        return JsonResponse(response_data, status=500)

    # Return HTML for regular requests
    return render(request, '500.html', status=500)


def get_client_ip(request):
    """
    Extract client IP address from request.
    Handles X-Forwarded-For header for proxied requests.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Get first IP in chain (original client)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


# Additional error handling utilities

def is_api_request(request):
    """
    Determine if request is an API request.
    Can be extended with additional checks (Accept headers, etc.)
    """
    return (
        request.path.startswith('/api/') or
        request.META.get('HTTP_ACCEPT', '').startswith('application/json')
    )


def sanitize_error_message(message):
    """
    Sanitize error messages to prevent information disclosure.

    Removes file paths, SQL queries, and other sensitive information
    that might be present in exception messages.
    """
    if not settings.DEBUG:
        # In production, return generic message
        return "An error occurred while processing your request."

    # In development, return actual message
    return message
