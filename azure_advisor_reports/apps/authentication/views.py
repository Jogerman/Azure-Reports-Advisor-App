"""
Authentication views for Azure AD login, JWT token management, and user profile.
"""

import logging
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.utils import timezone

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


class AzureADLoginView(views.APIView):
    """
    API endpoint for Azure AD authentication.

    POST /api/v1/auth/login/
    {
        "access_token": "azure_ad_access_token"
    }
    """
    permission_classes = [AllowAny]
    serializer_class = AzureADLoginSerializer

    def post(self, request):
        """
        Authenticate user with Azure AD access token and return JWT tokens.
        """
        serializer = AzureADLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        azure_token = serializer.validated_data['access_token']
        azure_service = AzureADService()

        # Validate Azure AD token and get user info
        is_valid, azure_user_info = azure_service.validate_token(azure_token)

        if not is_valid or not azure_user_info:
            return Response(
                {'error': 'Invalid Azure AD token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Create or update user from Azure AD profile
        user = azure_service.create_or_update_user(azure_user_info)

        if not user:
            return Response(
                {'error': 'Failed to create/update user'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Update last login info
        user.last_login = timezone.now()
        user.last_login_ip = self.get_client_ip(request)
        user.save(update_fields=['last_login', 'last_login_ip'])

        # Generate JWT tokens
        tokens = JWTService.generate_token(user)

        response_data = {
            **tokens,
            'user': UserProfileSerializer(user).data
        }

        logger.info(f"User {user.email} successfully logged in via Azure AD")

        return Response(response_data, status=status.HTTP_200_OK)

    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TokenRefreshView(views.APIView):
    """
    API endpoint for refreshing JWT access token.

    POST /api/v1/auth/refresh/
    {
        "refresh_token": "your_refresh_token"
    }
    """
    permission_classes = [AllowAny]
    serializer_class = TokenRefreshSerializer

    def post(self, request):
        """
        Generate new access token using refresh token.
        """
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data['refresh_token']
        new_tokens = JWTService.refresh_access_token(refresh_token)

        if not new_tokens:
            return Response(
                {'error': 'Invalid or expired refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        logger.info("Access token refreshed successfully")
        return Response(new_tokens, status=status.HTTP_200_OK)


class LogoutView(views.APIView):
    """
    API endpoint for user logout.

    POST /api/v1/auth/logout/
    {
        "refresh_token": "your_refresh_token"  // optional
    }
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        """
        Logout user and invalidate tokens.
        Note: In a stateless JWT system, actual token invalidation
        requires implementing a token blacklist.
        """
        # In production, implement token blacklisting here
        # For now, just log the logout
        logger.info(f"User {request.user.email} logged out")

        return Response(
            {'message': 'Successfully logged out'},
            status=status.HTTP_200_OK
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
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(username__icontains=search)
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
            'users_by_role': dict(
                User.objects.values_list('role').annotate(count=Count('role'))
            ),
        }

        return Response(stats, status=status.HTTP_200_OK)