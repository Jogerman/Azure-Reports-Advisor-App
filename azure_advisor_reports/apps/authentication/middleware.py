"""
Custom middleware for JWT authentication and request processing.
"""

import logging
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import AuthenticationFailed

from .services import JWTService

User = get_user_model()
logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to authenticate requests using JWT tokens.

    This middleware extracts JWT tokens from the Authorization header
    and authenticates the user for Django views (not DRF views).

    For DRF views, use the authentication classes in authentication.py
    """

    def process_request(self, request):
        """
        Process incoming request and attach user if JWT token is valid.
        """
        # Skip authentication for certain paths
        excluded_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/health/',
            '/api/auth/login/',
            '/api/auth/refresh/',
        ]

        if any(request.path.startswith(path) for path in excluded_paths):
            return None

        # Get Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        # Extract token
        token = auth_header.split(' ')[1]

        try:
            # Validate JWT token
            is_valid, payload = JWTService.validate_token(token, token_type='access')

            if is_valid and payload:
                # Get user from database
                user_id = payload.get('user_id')
                try:
                    user = User.objects.get(id=user_id)

                    # Attach user to request
                    request.user = user

                    logger.debug(f"Authenticated user {user.email} via JWT")

                except User.DoesNotExist:
                    logger.warning(f"User {user_id} from JWT token does not exist")

        except Exception as e:
            # Log error but don't fail the request
            # DRF will handle authentication for API endpoints
            logger.debug(f"JWT middleware authentication failed: {str(e)}")

        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests for auditing and debugging.
    """

    def process_request(self, request):
        """
        Log incoming request details.
        """
        # Only log API requests
        if not request.path.startswith('/api/'):
            return None

        user_info = "Anonymous"
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_info = f"{request.user.email} ({request.user.role})"

        logger.info(
            f"API Request: {request.method} {request.path} | "
            f"User: {user_info} | "
            f"IP: {self.get_client_ip(request)}"
        )

        return None

    def process_response(self, request, response):
        """
        Log response status code for API requests.
        """
        if not request.path.startswith('/api/'):
            return response

        if response.status_code >= 400:
            logger.warning(
                f"API Response: {request.method} {request.path} | "
                f"Status: {response.status_code}"
            )

        return response

    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SessionTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track user sessions and last activity.
    """

    def process_request(self, request):
        """
        Update user's last activity timestamp.
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Update last login IP if different
            client_ip = self.get_client_ip(request)

            if request.user.last_login_ip != client_ip:
                request.user.last_login_ip = client_ip
                request.user.save(update_fields=['last_login_ip'])

                logger.info(f"Updated IP for user {request.user.email}: {client_ip}")

        return None

    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class APIVersionMiddleware(MiddlewareMixin):
    """
    Middleware to add API version to response headers.
    """

    def process_response(self, request, response):
        """
        Add API version header to response.
        """
        if request.path.startswith('/api/'):
            response['X-API-Version'] = 'v1'
            response['X-API-Build'] = '1.0.0'

        return response
