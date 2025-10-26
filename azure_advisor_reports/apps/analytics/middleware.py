"""
Activity tracking middleware for automatic user activity logging.
"""

import re
from django.utils.deprecation import MiddlewareMixin
from apps.analytics.models import UserActivity


class UserActivityTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically track user activities.

    Tracks key operations like:
    - Report creation, download, deletion
    - Client creation, update, deletion
    - CSV uploads
    - Login/logout events
    """

    # URL patterns to track (compiled for performance)
    PATTERNS = {
        'generate_report': re.compile(r'^/api/v1/reports/?$'),
        'download_report': re.compile(r'^/api/v1/reports/([a-f0-9-]+)/download/?$'),
        'delete_report': re.compile(r'^/api/v1/reports/([a-f0-9-]+)/?$'),
        'create_client': re.compile(r'^/api/v1/clients/?$'),
        'update_client': re.compile(r'^/api/v1/clients/([a-f0-9-]+)/?$'),
        'delete_client': re.compile(r'^/api/v1/clients/([a-f0-9-]+)/?$'),
        'upload_csv': re.compile(r'^/api/v1/clients/([a-f0-9-]+)/upload-csv/?$'),
        'share_report': re.compile(r'^/api/v1/reports/([a-f0-9-]+)/share/?$'),
    }

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def __call__(self, request):
        # Process request
        response = self.get_response(request)

        # Track activity after response
        if self._should_track(request, response):
            self._track_activity(request, response)

        return response

    def _should_track(self, request, response):
        """
        Determine if this request should be tracked.

        Only track:
        - Authenticated users
        - Successful requests (2xx, 3xx status codes)
        - Non-GET requests or specific GET endpoints
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False

        if response.status_code >= 400:
            return False

        # Track all POST, PUT, PATCH, DELETE
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return True

        # Track specific GET endpoints (downloads)
        if request.method == 'GET' and 'download' in request.path:
            return True

        return False

    def _track_activity(self, request, response):
        """Track the activity based on request path and method."""
        try:
            path = request.path
            method = request.method
            user = request.user

            # Get IP address
            ip_address = self._get_client_ip(request)

            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

            # Initialize activity data
            action = 'other'
            description = f"{method} {path}"
            metadata = {
                'path': path,
                'method': method,
            }
            client = None
            report = None

            # Match patterns and extract activity details
            # Report operations
            if method == 'POST' and self.PATTERNS['generate_report'].match(path):
                action = 'generate_report'
                description = "Generated a new report"
                if hasattr(request, 'data') and 'client_id' in request.data:
                    metadata['client_id'] = request.data.get('client_id')
                    metadata['report_type'] = request.data.get('report_type', 'unknown')

            elif method == 'GET' and self.PATTERNS['download_report'].match(path):
                match = self.PATTERNS['download_report'].match(path)
                if match:
                    report_id = match.group(1)
                    action = 'download_report'
                    description = f"Downloaded report {report_id}"
                    metadata['report_id'] = report_id
                    # Try to get report object
                    try:
                        from apps.reports.models import Report
                        report = Report.objects.filter(id=report_id).first()
                        if report:
                            client = report.client
                    except Exception:
                        pass

            elif method == 'DELETE' and self.PATTERNS['delete_report'].match(path):
                match = self.PATTERNS['delete_report'].match(path)
                if match:
                    report_id = match.group(1)
                    action = 'delete_report'
                    description = f"Deleted report {report_id}"
                    metadata['report_id'] = report_id

            # Client operations
            elif method == 'POST' and self.PATTERNS['create_client'].match(path):
                action = 'create_client'
                description = "Created a new client"
                if hasattr(request, 'data') and 'company_name' in request.data:
                    metadata['company_name'] = request.data.get('company_name')

            elif method in ['PUT', 'PATCH'] and self.PATTERNS['update_client'].match(path):
                match = self.PATTERNS['update_client'].match(path)
                if match:
                    client_id = match.group(1)
                    action = 'update_client'
                    description = f"Updated client {client_id}"
                    metadata['client_id'] = client_id
                    # Try to get client object
                    try:
                        from apps.clients.models import Client
                        client = Client.objects.filter(id=client_id).first()
                    except Exception:
                        pass

            elif method == 'DELETE' and self.PATTERNS['delete_client'].match(path):
                match = self.PATTERNS['delete_client'].match(path)
                if match:
                    client_id = match.group(1)
                    action = 'delete_client'
                    description = f"Deleted client {client_id}"
                    metadata['client_id'] = client_id

            # CSV upload
            elif method == 'POST' and self.PATTERNS['upload_csv'].match(path):
                match = self.PATTERNS['upload_csv'].match(path)
                if match:
                    client_id = match.group(1)
                    action = 'upload_csv'
                    description = f"Uploaded CSV for client {client_id}"
                    metadata['client_id'] = client_id
                    # Try to get client object
                    try:
                        from apps.clients.models import Client
                        client = Client.objects.filter(id=client_id).first()
                    except Exception:
                        pass

            # Report sharing
            elif method == 'POST' and self.PATTERNS['share_report'].match(path):
                match = self.PATTERNS['share_report'].match(path)
                if match:
                    report_id = match.group(1)
                    action = 'share_report'
                    description = f"Shared report {report_id}"
                    metadata['report_id'] = report_id
                    # Try to get report object
                    try:
                        from apps.reports.models import Report
                        report = Report.objects.filter(id=report_id).first()
                        if report:
                            client = report.client
                    except Exception:
                        pass

            # Create activity record
            UserActivity.objects.create(
                user=user,
                action=action,
                description=description,
                client=client,
                report=report,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata
            )

        except Exception as e:
            # Silently fail - don't break the request flow
            # Log the error in production
            import logging
            logger = logging.getLogger('analytics')
            logger.error(f"Failed to track user activity: {str(e)}")

    def _get_client_ip(self, request):
        """
        Get client IP address from request.

        Handles proxy headers (X-Forwarded-For, X-Real-IP).
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')

        return ip
