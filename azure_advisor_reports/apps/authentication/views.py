"""
Authentication views for Azure AD login, JWT token management, and user profile.
"""

import logging
import jwt
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from .serializers import (
    UserSerializer,
    UserListSerializer,
    UserProfileSerializer,
    AzureADLoginSerializer,
    TokenResponseSerializer,
    TokenRefreshSerializer,
    RefreshTokenResponseSerializer,
    LogoutSerializer,
    UpdateProfileSerializer,
)
from .services import AzureADService, JWTService, RoleService
from .permissions import IsAdmin, CanManageClients

User = get_user_model()
logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')


def get_client_ip(request):
    """
    Get client IP address from request.
    Handles X-Forwarded-For header for proxied requests.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


class AzureADLoginView(views.APIView):
    """
    API endpoint for Azure AD authentication with rate limiting and progressive lockout.

    POST /api/v1/auth/login/
    {
        "access_token": "azure_ad_access_token"
    }

    Rate Limits:
    - 5 requests per minute per IP
    - 10 requests per minute per User-Agent
    - Progressive lockout: 5 failures = 15 min, 10 failures = 1 hour, 15 failures = 24 hours
    """
    permission_classes = [AllowAny]
    serializer_class = AzureADLoginSerializer

    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True))
    @method_decorator(ratelimit(key='header:user-agent', rate='10/m', method='POST', block=True))
    def post(self, request):
        """
        Authenticate user with Azure AD access token - rate limited.
        """
        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')[:100]

        # Check if IP is in lockout
        lockout_key = f'auth_lockout:{ip}'
        lockout_until = cache.get(lockout_key)

        if lockout_until:
            security_logger.warning(
                f'Authentication attempt from locked out IP: {ip} (locked until {lockout_until})'
            )
            return Response(
                {
                    'error': 'Too many failed authentication attempts. Account temporarily locked.',
                    'detail': 'Please try again later or contact support if you believe this is an error.'
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Validate request data
        serializer = AzureADLoginSerializer(data=request.data)

        if not serializer.is_valid():
            # Track failed attempt
            self._track_failed_attempt(ip)
            security_logger.warning(
                f'Authentication failed from IP {ip}: Invalid request data - {serializer.errors}'
            )
            return Response(
                {'error': 'Invalid request data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        azure_token = serializer.validated_data['access_token']
        azure_service = AzureADService()

        # Validate Azure AD token and get user info
        is_valid, azure_user_info = azure_service.validate_token(azure_token)

        if not is_valid or not azure_user_info:
            # Track failed attempt
            self._track_failed_attempt(ip)
            security_logger.warning(
                f'Authentication failed from IP {ip}: Invalid Azure AD token'
            )
            return Response(
                {'error': 'Invalid Azure AD token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Create or update user from Azure AD profile
        user = azure_service.create_or_update_user(azure_user_info)

        if not user:
            # Track failed attempt
            self._track_failed_attempt(ip)
            security_logger.error(
                f'Authentication failed from IP {ip}: Failed to create/update user'
            )
            return Response(
                {'error': 'Failed to create/update user'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # SUCCESS: Clear failed attempts for this IP
        self._clear_failed_attempts(ip)

        # Update last login info
        user.last_login = timezone.now()
        user.last_login_ip = ip
        user.save(update_fields=['last_login', 'last_login_ip'])

        # Generate JWT tokens
        tokens = JWTService.generate_token(user)

        response_data = {
            **tokens,
            'user': UserProfileSerializer(user).data
        }

        security_logger.info(
            f'User {user.email} successfully logged in via Azure AD from IP {ip}'
        )
        logger.info(f"User {user.email} successfully logged in via Azure AD")

        return Response(response_data, status=status.HTTP_200_OK)

    def _track_failed_attempt(self, ip):
        """
        Track failed authentication attempts and implement progressive lockout.

        Progressive lockout thresholds:
        - 5 failures = 15 minute lockout
        - 10 failures = 1 hour lockout
        - 15 failures = 24 hour lockout
        """
        key = f'auth_failures:{ip}'
        failures = cache.get(key, 0) + 1
        cache.set(key, failures, 3600)  # Track failures for 1 hour

        security_logger.info(f'Failed authentication attempt #{failures} from IP {ip}')

        # Progressive lockout implementation
        if failures >= 15:
            lockout_duration = 86400  # 24 hours
            lockout_label = '24 hours'
        elif failures >= 10:
            lockout_duration = 3600  # 1 hour
            lockout_label = '1 hour'
        elif failures >= 5:
            lockout_duration = 900  # 15 minutes
            lockout_label = '15 minutes'
        else:
            return  # No lockout yet

        # Set lockout
        lockout_key = f'auth_lockout:{ip}'
        lockout_until = timezone.now() + timezone.timedelta(seconds=lockout_duration)
        cache.set(lockout_key, lockout_until.isoformat(), lockout_duration)

        security_logger.error(
            f'IP {ip} locked out for {lockout_label} after {failures} failed authentication attempts'
        )

    def _clear_failed_attempts(self, ip):
        """Clear failed authentication attempts for an IP after successful login."""
        key = f'auth_failures:{ip}'
        failures = cache.get(key, 0)
        if failures > 0:
            cache.delete(key)
            security_logger.info(
                f'Cleared {failures} failed authentication attempts for IP {ip} after successful login'
            )

    # Keep legacy method for backward compatibility
    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request. (Deprecated - use module-level function)"""
        return get_client_ip(request)


class TokenRefreshView(views.APIView):
    """
    API endpoint for refreshing JWT access token with rate limiting.

    POST /api/v1/auth/refresh/
    {
        "refresh_token": "your_refresh_token"
    }

    Rate Limits:
    - 30 requests per hour per IP
    """
    permission_classes = [AllowAny]
    serializer_class = TokenRefreshSerializer

    @method_decorator(ratelimit(key='ip', rate='30/h', method='POST', block=True))
    def post(self, request):
        """
        Generate new access token using refresh token - rate limited.
        """
        ip = get_client_ip(request)

        serializer = TokenRefreshSerializer(data=request.data)

        if not serializer.is_valid():
            security_logger.warning(
                f'Token refresh failed from IP {ip}: Invalid request data - {serializer.errors}'
            )
            return Response(
                {'error': 'Invalid request data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        refresh_token = serializer.validated_data['refresh_token']
        new_tokens = JWTService.refresh_access_token(refresh_token)

        if not new_tokens:
            security_logger.warning(
                f'Token refresh failed from IP {ip}: Invalid or expired refresh token'
            )
            return Response(
                {'error': 'Invalid or expired refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        security_logger.info(f"Access token refreshed successfully from IP {ip}")
        logger.info("Access token refreshed successfully")
        return Response(new_tokens, status=status.HTTP_200_OK)


class LogoutView(views.APIView):
    """
    API endpoint for user logout with token blacklisting.

    This endpoint revokes both access and refresh tokens by adding them
    to the blacklist. Once revoked, these tokens cannot be used again.

    POST /api/v1/auth/logout/
    Authorization: Bearer <access_token>
    {
        "refresh_token": "your_refresh_token"  // optional
    }

    Returns:
        200: Logout successful, tokens revoked
        400: Invalid request or token format
        401: Unauthorized or invalid token
        500: Server error during logout
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        """
        Logout user by revoking their access and refresh tokens.

        Extracts the access token from Authorization header and optionally
        the refresh token from request body, then revokes both in the blacklist.
        """
        ip = get_client_ip(request)

        try:
            # Get access token from Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if not auth_header.startswith('Bearer '):
                return Response(
                    {'error': 'Invalid authorization header format'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            access_token = auth_header.split(' ')[1]

            # Decode access token to get JTI (allow expired tokens for logout)
            try:
                access_payload = jwt.decode(
                    access_token,
                    settings.SECRET_KEY,
                    algorithms=['HS256'],
                    options={"verify_exp": False}  # Allow expired tokens for logout
                )
                access_jti = access_payload.get('jti')

                if access_jti:
                    # Revoke access token
                    if JWTService.revoke_token(access_jti, reason='logout'):
                        logger.debug(f"Revoked access token {access_jti[:8]}...")
                    else:
                        logger.warning(f"Could not revoke access token {access_jti[:8]}...")
                else:
                    logger.warning("Access token missing JTI - cannot revoke")

            except jwt.InvalidTokenError as e:
                logger.warning(f"Could not decode access token for logout: {str(e)}")
                # Continue with logout even if access token is invalid

            # Optionally revoke refresh token if provided
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                try:
                    refresh_payload = jwt.decode(
                        refresh_token,
                        settings.SECRET_KEY,
                        algorithms=['HS256'],
                        options={"verify_exp": False}  # Allow expired tokens for logout
                    )
                    refresh_jti = refresh_payload.get('jti')

                    if refresh_jti:
                        # Revoke refresh token
                        if JWTService.revoke_token(refresh_jti, reason='logout'):
                            logger.debug(f"Revoked refresh token {refresh_jti[:8]}...")
                        else:
                            logger.warning(f"Could not revoke refresh token {refresh_jti[:8]}...")
                    else:
                        logger.warning("Refresh token missing JTI - cannot revoke")

                except jwt.InvalidTokenError as e:
                    logger.warning(f"Could not decode refresh token for logout: {str(e)}")
                    # Continue with logout even if refresh token is invalid

            # Log successful logout
            security_logger.info(
                f'User {request.user.email} logged out successfully from IP {ip}'
            )

            return Response(
                {
                    'message': 'Logged out successfully',
                    'detail': 'Your tokens have been revoked and can no longer be used.'
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Logout error for user {request.user.email}: {str(e)}")
            security_logger.error(
                f'Logout failed for user {request.user.email} from IP {ip}: {str(e)}'
            )
            return Response(
                {
                    'error': 'Logout failed',
                    'detail': 'An error occurred during logout. Please try again.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CurrentUserView(views.APIView):
    """
    API endpoint to get current authenticated user information.

    GET /api/v1/auth/user/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get(self, request):
        """
        Return current user profile information.
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        """
        Update current user profile information.
        """
        serializer = UpdateProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(f"User {request.user.email} updated profile")

        return Response(
            UserProfileSerializer(request.user).data,
            status=status.HTTP_200_OK
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management (admin only).

    List users: GET /api/v1/users/
    Get user: GET /api/v1/users/{id}/
    Create user: POST /api/v1/users/
    Update user: PUT /api/v1/users/{id}/
    Delete user: DELETE /api/v1/users/{id}/
    """
    queryset = User.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'list':
            return UserListSerializer
        return UserSerializer

    def get_queryset(self):
        """
        Optionally filter users by role, active status, or search query.
        """
        queryset = super().get_queryset()

        # Filter by role
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Search by name or email
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(username__icontains=search)
            )

        return queryset

    @action(detail=True, methods=['post'], url_path='activate')
    def activate_user(self, request, pk=None):
        """
        Activate a user account.

        POST /api/v1/users/{id}/activate/
        """
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=['is_active'])

        logger.info(f"Admin {request.user.email} activated user {user.email}")

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate_user(self, request, pk=None):
        """
        Deactivate a user account.

        POST /api/v1/users/{id}/deactivate/
        """
        user = self.get_object()

        # Prevent deactivating self
        if user.id == request.user.id:
            return Response(
                {'error': 'Cannot deactivate your own account'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = False
        user.save(update_fields=['is_active'])

        logger.info(f"Admin {request.user.email} deactivated user {user.email}")

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='change-role')
    def change_role(self, request, pk=None):
        """
        Change user role.

        POST /api/v1/users/{id}/change-role/
        {
            "role": "manager"
        }
        """
        user = self.get_object()
        new_role = request.data.get('role')

        if not new_role:
            return Response(
                {'error': 'Role is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate role
        valid_roles = [role[0] for role in User.ROLE_CHOICES]
        if new_role not in valid_roles:
            return Response(
                {'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prevent changing own role
        if user.id == request.user.id:
            return Response(
                {'error': 'Cannot change your own role'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.role = new_role
        user.save(update_fields=['role'])

        logger.info(f"Admin {request.user.email} changed user {user.email} role to {new_role}")

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """
        Get user statistics.

        GET /api/v1/users/statistics/
        """
        from django.db.models import Count

        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'inactive_users': User.objects.filter(is_active=False).count(),
            'users_by_role': {
                item['role']: item['count']
                for item in User.objects.values('role').annotate(count=Count('role'))
            },
        }

        return Response(stats, status=status.HTTP_200_OK)