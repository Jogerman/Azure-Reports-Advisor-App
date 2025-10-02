"""
Django REST Framework serializers for authentication.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with all fields.
    """
    full_name = serializers.ReadOnlyField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'role_display',
            'job_title',
            'department',
            'phone_number',
            'azure_object_id',
            'tenant_id',
            'is_active',
            'is_staff',
            'is_superuser',
            'last_login',
            'last_login_ip',
            'date_joined',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'azure_object_id',
            'tenant_id',
            'is_staff',
            'is_superuser',
            'last_login',
            'last_login_ip',
            'date_joined',
            'created_at',
            'updated_at',
        ]


class UserListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for user lists.
    """
    full_name = serializers.ReadOnlyField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'full_name',
            'role',
            'role_display',
            'job_title',
            'department',
            'is_active',
            'last_login',
            'created_at',
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    full_name = serializers.ReadOnlyField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'role_display',
            'job_title',
            'department',
            'phone_number',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'username',
            'email',
            'role',
            'created_at',
        ]


class AzureADLoginSerializer(serializers.Serializer):
    """
    Serializer for Azure AD login request.
    """
    access_token = serializers.CharField(
        required=True,
        help_text="Azure AD access token obtained from frontend"
    )


class TokenResponseSerializer(serializers.Serializer):
    """
    Serializer for JWT token response.
    """
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)
    expires_in = serializers.IntegerField(read_only=True)
    token_type = serializers.CharField(read_only=True)
    user = UserProfileSerializer(read_only=True)


class TokenRefreshSerializer(serializers.Serializer):
    """
    Serializer for token refresh request.
    """
    refresh_token = serializers.CharField(
        required=True,
        help_text="Valid refresh token"
    )


class RefreshTokenResponseSerializer(serializers.Serializer):
    """
    Serializer for refreshed access token response.
    """
    access_token = serializers.CharField(read_only=True)
    expires_in = serializers.IntegerField(read_only=True)
    token_type = serializers.CharField(read_only=True)


class LogoutSerializer(serializers.Serializer):
    """
    Serializer for logout request.
    """
    refresh_token = serializers.CharField(
        required=False,
        help_text="Refresh token to invalidate (optional)"
    )


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password.
    Note: This is for local users, not Azure AD users.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        """Validate that new passwords match."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': "New passwords do not match."
            })
        return attrs

    def validate_new_password(self, value):
        """Validate password strength."""
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )
        return value


class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'phone_number',
        ]

    def validate_phone_number(self, value):
        """Validate phone number format."""
        if value and not value.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise serializers.ValidationError(
                "Invalid phone number format."
            )
        return value