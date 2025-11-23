"""
Audit Middleware for automatic request logging

This middleware automatically captures and logs all HTTP requests,
providing comprehensive audit trails for compliance and security.
"""

import time
import json
from typing import Callable
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from .models import AuditLog, AuditAction, AuditSeverity
from .utils import get_client_ip


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log all HTTP requests and responses
    """

    # Paths to exclude from audit logging
    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/favicon.ico',
        '/health/',
        '/metrics/',
    ]

    # Sensitive headers to redact from logs
    SENSITIVE_HEADERS = [
        'Authorization',
        'Cookie',
        'X-API-Key',
        'X-Auth-Token',
    ]

    def process_request(self, request: HttpRequest) -> None:
        """
        Called before view processing.
        Store start time for duration calculation.
        """
        request._audit_start_time = time.time()

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Called after view processing.
        Log the request/response to audit trail.
        """
        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return response

        # Calculate duration
        duration_ms = None
        if hasattr(request, '_audit_start_time'):
            duration_ms = int((time.time() - request._audit_start_time) * 1000)

        # Determine action type based on method and path
        action = self._determine_action(request)

        # Determine severity based on method and status code
        severity = self._determine_severity(request.method, response.status_code)

        # Extract metadata
        metadata = self._extract_metadata(request, response)

        # Get user information
        user = None if isinstance(request.user, AnonymousUser) else request.user

        # Create audit log entry
        try:
            AuditLog.log_action(
                action=action,
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
                request_path=request.path,
                request_method=request.method,
                session_id=request.session.session_key if hasattr(request, 'session') else '',
                success=200 <= response.status_code < 400,
                status_code=response.status_code,
                severity=severity,
                metadata=metadata,
                duration_ms=duration_ms,
            )
        except Exception as e:
            # Don't break the request if audit logging fails
            print(f'Audit logging failed: {str(e)}')

        return response

    def _determine_action(self, request: HttpRequest) -> str:
        """
        Determine the audit action type based on the request
        """
        path = request.path.lower()
        method = request.method.upper()

        # Authentication endpoints
        if '/auth/login' in path:
            return AuditAction.LOGIN
        if '/auth/logout' in path:
            return AuditAction.LOGOUT

        # API endpoints
        if '/api/' in path:
            if method in ['GET', 'HEAD', 'OPTIONS']:
                if 'download' in path:
                    return AuditAction.REPORT_DOWNLOADED
                return AuditAction.API_CALL
            elif method == 'POST':
                if '/reports/' in path:
                    return AuditAction.REPORT_CREATED
                elif '/clients/' in path:
                    return AuditAction.CLIENT_CREATED
                elif '/users/' in path:
                    return AuditAction.USER_CREATED
            elif method in ['PUT', 'PATCH']:
                if '/reports/' in path:
                    return AuditAction.REPORT_UPDATED
                elif '/clients/' in path:
                    return AuditAction.CLIENT_UPDATED
                elif '/users/' in path:
                    return AuditAction.USER_UPDATED
            elif method == 'DELETE':
                if '/reports/' in path:
                    return AuditAction.REPORT_DELETED
                elif '/clients/' in path:
                    return AuditAction.CLIENT_DELETED
                elif '/users/' in path:
                    return AuditAction.USER_DELETED

        # CSV operations
        if '/csv' in path:
            if method == 'POST':
                return AuditAction.CSV_UPLOADED

        # Default to generic API call
        return AuditAction.API_CALL

    def _determine_severity(self, method: str, status_code: int) -> str:
        """
        Determine log severity based on method and status code
        """
        # Critical: Server errors
        if status_code >= 500:
            return AuditSeverity.CRITICAL

        # High: Client errors (except 404), DELETE operations
        if status_code >= 400 or method == 'DELETE':
            return AuditSeverity.HIGH if status_code != 404 else AuditSeverity.MEDIUM

        # Medium: Modify operations
        if method in ['POST', 'PUT', 'PATCH']:
            return AuditSeverity.MEDIUM

        # Low: Read operations
        return AuditSeverity.LOW

    def _extract_metadata(self, request: HttpRequest, response: HttpResponse) -> dict:
        """
        Extract relevant metadata from request and response
        """
        metadata = {
            'query_params': dict(request.GET),
            'content_type': request.content_type,
            'response_content_type': response.get('Content-Type', ''),
        }

        # Add request body for POST/PUT/PATCH (but sanitize sensitive data)
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                if request.content_type == 'application/json':
                    body = json.loads(request.body)
                    metadata['request_body'] = self._sanitize_data(body)
                elif request.POST:
                    metadata['request_body'] = self._sanitize_data(dict(request.POST))
            except (json.JSONDecodeError, ValueError):
                pass

        return metadata

    def _sanitize_data(self, data: dict) -> dict:
        """
        Remove sensitive information from data before logging
        """
        sensitive_fields = [
            'password',
            'token',
            'secret',
            'api_key',
            'credit_card',
            'ssn',
            'authorization',
        ]

        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value

        return sanitized
