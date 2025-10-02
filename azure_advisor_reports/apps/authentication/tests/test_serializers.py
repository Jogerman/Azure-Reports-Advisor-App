"""
Test cases for authentication serializers
Tests all serializers in apps.authentication.serializers
"""

import pytest
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

from apps.authentication.serializers import (
    UserSerializer,
    UserListSerializer,
    UserProfileSerializer,
    AzureADLoginSerializer,
    TokenResponseSerializer,
    TokenRefreshSerializer,
    RefreshTokenResponseSerializer,
    LogoutSerializer,
    ChangePasswordSerializer,
    UpdateProfileSerializer,
)

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.unit
class TestUserSerializer:
    """Test suite for UserSerializer"""

    def test_user_serialization(self, user):
        """Test serializing a user object"""
        serializer = UserSerializer(user)
        data = serializer.data

        assert 'id' in data
        assert data['username'] == user.username
        assert data['email'] == user.email
        assert data['first_name'] == user.first_name
        assert data['last_name'] == user.last_name
        assert data['full_name'] == user.full_name
        assert data['role'] == user.role
        assert 'role_display' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_user_serialization_includes_full_name(self, user):
        """Test that serialized data includes full_name property"""
        user.first_name = "John"
        user.last_name = "Doe"
        user.save()

        serializer = UserSerializer(user)
        assert serializer.data['full_name'] == "John Doe"

    def test_user_serialization_includes_role_display(self, manager_user):
        """Test that serialized data includes role_display"""
        serializer = UserSerializer(manager_user)
        assert serializer.data['role_display'] == "Manager"

    def test_user_serialization_read_only_fields(self, user):
        """Test that certain fields are read-only"""
        serializer = UserSerializer(user)
        read_only_fields = [
            'id', 'azure_object_id', 'tenant_id', 'is_staff',
            'is_superuser', 'last_login', 'last_login_ip',
            'date_joined', 'created_at', 'updated_at'
        ]

        for field in read_only_fields:
            assert field in serializer.fields
            assert serializer.fields[field].read_only is True

    def test_user_deserialization(self):
        """Test deserializing user data"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'analyst',
            'job_title': 'Data Analyst',
            'department': 'Analytics'
        }

        serializer = UserSerializer(data=data)
        assert serializer.is_valid()

    def test_user_update(self, user):
        """Test updating a user with serializer"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'job_title': 'Senior Engineer'
        }

        serializer = UserSerializer(user, data=data, partial=True)
        assert serializer.is_valid()
        updated_user = serializer.save()

        assert updated_user.first_name == 'Updated'
        assert updated_user.last_name == 'Name'
        assert updated_user.job_title == 'Senior Engineer'


@pytest.mark.django_db
@pytest.mark.unit
class TestUserListSerializer:
    """Test suite for UserListSerializer"""

    def test_user_list_serialization(self, user):
        """Test serializing a user for list view"""
        serializer = UserListSerializer(user)
        data = serializer.data

        # Check that only list-relevant fields are included
        expected_fields = [
            'id', 'username', 'email', 'full_name', 'role',
            'role_display', 'job_title', 'department',
            'is_active', 'last_login', 'created_at'
        ]

        for field in expected_fields:
            assert field in data

        # Check that detailed fields are NOT included
        assert 'azure_object_id' not in data
        assert 'tenant_id' not in data
        assert 'phone_number' not in data

    def test_multiple_users_serialization(self, user, admin_user, manager_user):
        """Test serializing multiple users"""
        users = [user, admin_user, manager_user]
        serializer = UserListSerializer(users, many=True)

        assert len(serializer.data) == 3


@pytest.mark.django_db
@pytest.mark.unit
class TestUserProfileSerializer:
    """Test suite for UserProfileSerializer"""

    def test_user_profile_serialization(self, user):
        """Test serializing user profile"""
        serializer = UserProfileSerializer(user)
        data = serializer.data

        assert data['id'] == str(user.id)
        assert data['username'] == user.username
        assert data['email'] == user.email
        assert 'full_name' in data
        assert 'role' in data
        assert 'role_display' in data

    def test_user_profile_read_only_fields(self, user):
        """Test that profile has appropriate read-only fields"""
        serializer = UserProfileSerializer(user)
        read_only_fields = ['id', 'username', 'email', 'role', 'created_at']

        for field in read_only_fields:
            assert serializer.fields[field].read_only is True

    def test_user_profile_update(self, user):
        """Test updating user profile"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Profile',
            'phone_number': '+9876543210'
        }

        serializer = UserProfileSerializer(user, data=data, partial=True)
        assert serializer.is_valid()
        updated_user = serializer.save()

        assert updated_user.first_name == 'Updated'
        assert updated_user.last_name == 'Profile'
        assert updated_user.phone_number == '+9876543210'


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.azure_ad
class TestAzureADLoginSerializer:
    """Test suite for AzureADLoginSerializer"""

    def test_valid_azure_ad_login_data(self, azure_token_mock):
        """Test serializer with valid Azure AD token"""
        data = {'access_token': azure_token_mock}

        serializer = AzureADLoginSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['access_token'] == azure_token_mock

    def test_missing_access_token(self):
        """Test serializer with missing access_token"""
        data = {}

        serializer = AzureADLoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'access_token' in serializer.errors

    def test_empty_access_token(self):
        """Test serializer with empty access_token"""
        data = {'access_token': ''}

        serializer = AzureADLoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'access_token' in serializer.errors


@pytest.mark.unit
@pytest.mark.jwt
class TestTokenResponseSerializer:
    """Test suite for TokenResponseSerializer"""

    def test_token_response_serialization(self, user):
        """Test serializing token response"""
        data = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 3600,
            'token_type': 'Bearer',
            'user': user
        }

        serializer = TokenResponseSerializer(data)
        response_data = serializer.data

        assert response_data['access_token'] == 'test_access_token'
        assert response_data['refresh_token'] == 'test_refresh_token'
        assert response_data['expires_in'] == 3600
        assert response_data['token_type'] == 'Bearer'
        assert 'user' in response_data


@pytest.mark.unit
@pytest.mark.jwt
class TestTokenRefreshSerializer:
    """Test suite for TokenRefreshSerializer"""

    def test_valid_refresh_token(self, jwt_refresh_token):
        """Test serializer with valid refresh token"""
        data = {'refresh_token': jwt_refresh_token}

        serializer = TokenRefreshSerializer(data=data)
        assert serializer.is_valid()

    def test_missing_refresh_token(self):
        """Test serializer with missing refresh_token"""
        data = {}

        serializer = TokenRefreshSerializer(data=data)
        assert not serializer.is_valid()
        assert 'refresh_token' in serializer.errors

    def test_empty_refresh_token(self):
        """Test serializer with empty refresh_token"""
        data = {'refresh_token': ''}

        serializer = TokenRefreshSerializer(data=data)
        assert not serializer.is_valid()


@pytest.mark.unit
@pytest.mark.jwt
class TestRefreshTokenResponseSerializer:
    """Test suite for RefreshTokenResponseSerializer"""

    def test_refresh_token_response_serialization(self):
        """Test serializing refreshed token response"""
        data = {
            'access_token': 'new_access_token',
            'expires_in': 3600,
            'token_type': 'Bearer'
        }

        serializer = RefreshTokenResponseSerializer(data)
        response_data = serializer.data

        assert response_data['access_token'] == 'new_access_token'
        assert response_data['expires_in'] == 3600
        assert response_data['token_type'] == 'Bearer'


@pytest.mark.unit
class TestLogoutSerializer:
    """Test suite for LogoutSerializer"""

    def test_logout_with_refresh_token(self, jwt_refresh_token):
        """Test logout serializer with refresh token"""
        data = {'refresh_token': jwt_refresh_token}

        serializer = LogoutSerializer(data=data)
        assert serializer.is_valid()

    def test_logout_without_refresh_token(self):
        """Test logout serializer without refresh token (optional)"""
        data = {}

        serializer = LogoutSerializer(data=data)
        assert serializer.is_valid()  # refresh_token is optional


@pytest.mark.unit
class TestChangePasswordSerializer:
    """Test suite for ChangePasswordSerializer"""

    def test_valid_password_change(self):
        """Test serializer with valid password change data"""
        data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass456',
            'confirm_password': 'newpass456'
        }

        serializer = ChangePasswordSerializer(data=data)
        assert serializer.is_valid()

    def test_passwords_dont_match(self):
        """Test validation when passwords don't match"""
        data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass456',
            'confirm_password': 'different789'
        }

        serializer = ChangePasswordSerializer(data=data)
        assert not serializer.is_valid()
        assert 'confirm_password' in serializer.errors

    def test_password_too_short(self):
        """Test validation for password length"""
        data = {
            'old_password': 'oldpass123',
            'new_password': 'short',
            'confirm_password': 'short'
        }

        serializer = ChangePasswordSerializer(data=data)
        assert not serializer.is_valid()
        assert 'new_password' in serializer.errors

    def test_missing_fields(self):
        """Test validation with missing required fields"""
        data = {'old_password': 'oldpass123'}

        serializer = ChangePasswordSerializer(data=data)
        assert not serializer.is_valid()
        assert 'new_password' in serializer.errors
        assert 'confirm_password' in serializer.errors


@pytest.mark.django_db
@pytest.mark.unit
class TestUpdateProfileSerializer:
    """Test suite for UpdateProfileSerializer"""

    def test_valid_profile_update(self, user):
        """Test updating profile with valid data"""
        data = {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast',
            'phone_number': '+1234567890'
        }

        serializer = UpdateProfileSerializer(user, data=data, partial=True)
        assert serializer.is_valid()
        updated_user = serializer.save()

        assert updated_user.first_name == 'UpdatedFirst'
        assert updated_user.last_name == 'UpdatedLast'
        assert updated_user.phone_number == '+1234567890'

    def test_update_only_first_name(self, user):
        """Test partial update with only first_name"""
        data = {'first_name': 'NewFirst'}

        serializer = UpdateProfileSerializer(user, data=data, partial=True)
        assert serializer.is_valid()
        updated_user = serializer.save()

        assert updated_user.first_name == 'NewFirst'

    def test_valid_phone_number_formats(self, user):
        """Test various valid phone number formats"""
        valid_numbers = [
            '+1234567890',
            '123-456-7890',
            '123 456 7890',
            '+1-234-567-8900'
        ]

        for phone in valid_numbers:
            data = {'phone_number': phone}
            serializer = UpdateProfileSerializer(user, data=data, partial=True)
            assert serializer.is_valid(), f"Phone {phone} should be valid"

    def test_invalid_phone_number(self, user):
        """Test invalid phone number format"""
        data = {'phone_number': 'abc-def-ghij'}

        serializer = UpdateProfileSerializer(user, data=data, partial=True)
        assert not serializer.is_valid()
        assert 'phone_number' in serializer.errors

    def test_empty_phone_number(self, user):
        """Test empty phone number (should be valid)"""
        data = {'phone_number': ''}

        serializer = UpdateProfileSerializer(user, data=data, partial=True)
        assert serializer.is_valid()

    def test_update_with_empty_names(self, user):
        """Test updating with empty first/last names"""
        data = {
            'first_name': '',
            'last_name': ''
        }

        serializer = UpdateProfileSerializer(user, data=data, partial=True)
        assert serializer.is_valid()
        updated_user = serializer.save()

        assert updated_user.first_name == ''
        assert updated_user.last_name == ''
