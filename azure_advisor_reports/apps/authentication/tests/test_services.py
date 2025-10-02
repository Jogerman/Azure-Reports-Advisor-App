"""
Test cases for authentication services
Tests AzureADService, JWTService, and RoleService
"""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone

from apps.authentication.services import AzureADService, JWTService, RoleService

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.azure_ad
class TestAzureADService:
    """Test suite for AzureADService"""

    def test_service_initialization(self):
        """Test AzureADService initialization"""
        service = AzureADService()

        assert service.client_id is not None
        assert service.client_secret is not None
        assert service.tenant_id is not None
        assert service.authority is not None

    @patch('requests.get')
    def test_validate_token_success(self, mock_get, azure_user_info):
        """Test successful token validation"""
        # Mock Microsoft Graph API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = azure_user_info
        mock_get.return_value = mock_response

        service = AzureADService()
        is_valid, user_info = service.validate_token("valid_token")

        assert is_valid is True
        assert user_info is not None
        assert user_info['mail'] == 'testuser@example.com'
        assert user_info['givenName'] == 'Test'
        assert user_info['surname'] == 'User'

    @patch('requests.get')
    def test_validate_token_failure(self, mock_get):
        """Test token validation with invalid token"""
        # Mock failed Graph API response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'error': 'Unauthorized'}
        mock_get.return_value = mock_response

        service = AzureADService()
        is_valid, user_info = service.validate_token("invalid_token")

        assert is_valid is False
        assert user_info is None

    @patch('requests.get')
    def test_validate_token_network_error(self, mock_get):
        """Test token validation with network error"""
        # Mock network error
        mock_get.side_effect = Exception("Network error")

        service = AzureADService()
        is_valid, user_info = service.validate_token("some_token")

        assert is_valid is False
        assert user_info is None

    def test_create_new_user_from_azure_ad(self, azure_user_info):
        """Test creating a new user from Azure AD profile"""
        service = AzureADService()
        user = service.create_or_update_user(azure_user_info)

        assert user is not None
        assert user.email == azure_user_info['mail']
        assert user.first_name == azure_user_info['givenName']
        assert user.last_name == azure_user_info['surname']
        assert user.azure_object_id == azure_user_info['id']
        assert user.role == 'analyst'  # Default role
        assert user.is_active is True

    def test_update_existing_user_from_azure_ad(self, user, azure_user_info):
        """Test updating an existing user from Azure AD profile"""
        # Set Azure ID to match the mock data
        user.azure_object_id = azure_user_info['id']
        user.first_name = 'OldFirst'
        user.last_name = 'OldLast'
        user.save()

        service = AzureADService()
        updated_user = service.create_or_update_user(azure_user_info)

        assert updated_user.id == user.id
        assert updated_user.first_name == azure_user_info['givenName']
        assert updated_user.last_name == azure_user_info['surname']
        assert updated_user.job_title == azure_user_info.get('jobTitle', '')
        assert updated_user.department == azure_user_info.get('department', '')

    def test_create_user_with_userprincipalname(self):
        """Test creating user when 'mail' is not present but 'userPrincipalName' is"""
        azure_info = {
            'id': 'azure-id-123',
            'userPrincipalName': 'user@example.com',
            'givenName': 'Test',
            'surname': 'User'
        }

        service = AzureADService()
        user = service.create_or_update_user(azure_info)

        assert user is not None
        assert user.email == 'user@example.com'

    def test_create_user_without_required_fields(self):
        """Test that user creation fails without required fields"""
        azure_info = {
            'givenName': 'Test',
            'surname': 'User'
        }  # Missing 'id' and email

        service = AzureADService()
        user = service.create_or_update_user(azure_info)

        assert user is None

    @patch('requests.get')
    def test_get_user_profile_success(self, mock_get, azure_user_info):
        """Test fetching user profile from Graph API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = azure_user_info
        mock_get.return_value = mock_response

        service = AzureADService()
        profile = service.get_user_profile("valid_token")

        assert profile is not None
        assert profile['mail'] == azure_user_info['mail']

    @patch('requests.get')
    def test_get_user_profile_failure(self, mock_get):
        """Test failed profile fetch"""
        mock_get.side_effect = Exception("API error")

        service = AzureADService()
        profile = service.get_user_profile("invalid_token")

        assert profile is None


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.jwt
class TestJWTService:
    """Test suite for JWTService"""

    def test_generate_token(self, user):
        """Test JWT token generation"""
        tokens = JWTService.generate_token(user)

        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert 'expires_in' in tokens
        assert 'token_type' in tokens
        assert tokens['expires_in'] == 3600
        assert tokens['token_type'] == 'Bearer'

    def test_access_token_payload(self, user):
        """Test access token contains correct payload"""
        tokens = JWTService.generate_token(user)
        access_token = tokens['access_token']

        # Decode without verification to inspect payload
        payload = jwt.decode(access_token, options={"verify_signature": False})

        assert payload['user_id'] == str(user.id)
        assert payload['email'] == user.email
        assert payload['role'] == user.role
        assert payload['type'] == 'access'
        assert 'exp' in payload
        assert 'iat' in payload

    def test_refresh_token_payload(self, user):
        """Test refresh token contains correct payload"""
        tokens = JWTService.generate_token(user)
        refresh_token = tokens['refresh_token']

        # Decode without verification to inspect payload
        payload = jwt.decode(refresh_token, options={"verify_signature": False})

        assert payload['user_id'] == str(user.id)
        assert payload['type'] == 'refresh'
        assert 'exp' in payload
        assert 'iat' in payload

    def test_validate_valid_access_token(self, user):
        """Test validating a valid access token"""
        tokens = JWTService.generate_token(user)
        access_token = tokens['access_token']

        is_valid, payload = JWTService.validate_token(access_token, token_type='access')

        assert is_valid is True
        assert payload is not None
        assert payload['user_id'] == str(user.id)
        assert payload['type'] == 'access'

    def test_validate_valid_refresh_token(self, user):
        """Test validating a valid refresh token"""
        tokens = JWTService.generate_token(user)
        refresh_token = tokens['refresh_token']

        is_valid, payload = JWTService.validate_token(refresh_token, token_type='refresh')

        assert is_valid is True
        assert payload is not None
        assert payload['user_id'] == str(user.id)
        assert payload['type'] == 'refresh'

    def test_validate_expired_token(self, expired_jwt_token):
        """Test validating an expired token"""
        is_valid, payload = JWTService.validate_token(expired_jwt_token, token_type='access')

        assert is_valid is False
        assert payload is None

    def test_validate_invalid_token(self, invalid_jwt_token):
        """Test validating a token with wrong secret"""
        is_valid, payload = JWTService.validate_token(invalid_jwt_token, token_type='access')

        assert is_valid is False
        assert payload is None

    def test_validate_wrong_token_type(self, user):
        """Test validating access token as refresh token"""
        tokens = JWTService.generate_token(user)
        access_token = tokens['access_token']

        is_valid, payload = JWTService.validate_token(access_token, token_type='refresh')

        assert is_valid is False
        assert payload is None

    def test_refresh_access_token_success(self, user):
        """Test refreshing access token with valid refresh token"""
        tokens = JWTService.generate_token(user)
        refresh_token = tokens['refresh_token']

        new_tokens = JWTService.refresh_access_token(refresh_token)

        assert new_tokens is not None
        assert 'access_token' in new_tokens
        assert 'expires_in' in new_tokens
        assert 'token_type' in new_tokens

    def test_refresh_access_token_with_invalid_token(self):
        """Test refreshing access token with invalid refresh token"""
        new_tokens = JWTService.refresh_access_token("invalid_token")

        assert new_tokens is None

    def test_refresh_access_token_with_expired_token(self, expired_jwt_token):
        """Test refreshing access token with expired refresh token"""
        new_tokens = JWTService.refresh_access_token(expired_jwt_token)

        assert new_tokens is None

    def test_refresh_access_token_with_nonexistent_user(self):
        """Test refreshing token for a deleted user"""
        # Create token for a non-existent user
        payload = {
            'user_id': '00000000-0000-0000-0000-000000000000',
            'exp': datetime.utcnow() + timedelta(days=7),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        fake_refresh_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        new_tokens = JWTService.refresh_access_token(fake_refresh_token)

        assert new_tokens is None

    def test_token_expiration_times(self, user):
        """Test that tokens have correct expiration times"""
        before_generation = datetime.utcnow()
        tokens = JWTService.generate_token(user)
        after_generation = datetime.utcnow()

        # Decode tokens
        access_payload = jwt.decode(tokens['access_token'], options={"verify_signature": False})
        refresh_payload = jwt.decode(tokens['refresh_token'], options={"verify_signature": False})

        # Check access token expires in ~1 hour
        access_exp = datetime.fromtimestamp(access_payload['exp'])
        expected_access_exp = after_generation + timedelta(hours=1)
        assert abs((access_exp - expected_access_exp).total_seconds()) < 10  # Within 10 seconds

        # Check refresh token expires in ~7 days
        refresh_exp = datetime.fromtimestamp(refresh_payload['exp'])
        expected_refresh_exp = after_generation + timedelta(days=7)
        assert abs((refresh_exp - expected_refresh_exp).total_seconds()) < 10  # Within 10 seconds


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestRoleService:
    """Test suite for RoleService"""

    def test_role_hierarchy(self):
        """Test that role hierarchy is correctly defined"""
        assert RoleService.ROLE_HIERARCHY['viewer'] < RoleService.ROLE_HIERARCHY['analyst']
        assert RoleService.ROLE_HIERARCHY['analyst'] < RoleService.ROLE_HIERARCHY['manager']
        assert RoleService.ROLE_HIERARCHY['manager'] < RoleService.ROLE_HIERARCHY['admin']

    def test_admin_has_all_permissions(self, admin_user):
        """Test that admin has all permissions"""
        assert RoleService.has_permission(admin_user, 'viewer')
        assert RoleService.has_permission(admin_user, 'analyst')
        assert RoleService.has_permission(admin_user, 'manager')
        assert RoleService.has_permission(admin_user, 'admin')

    def test_manager_has_manager_and_below_permissions(self, manager_user):
        """Test that manager has manager and below permissions"""
        assert RoleService.has_permission(manager_user, 'viewer')
        assert RoleService.has_permission(manager_user, 'analyst')
        assert RoleService.has_permission(manager_user, 'manager')
        assert not RoleService.has_permission(manager_user, 'admin')

    def test_analyst_has_analyst_and_below_permissions(self, analyst_user):
        """Test that analyst has analyst and below permissions"""
        assert RoleService.has_permission(analyst_user, 'viewer')
        assert RoleService.has_permission(analyst_user, 'analyst')
        assert not RoleService.has_permission(analyst_user, 'manager')
        assert not RoleService.has_permission(analyst_user, 'admin')

    def test_viewer_has_only_viewer_permissions(self, viewer_user):
        """Test that viewer has only viewer permissions"""
        assert RoleService.has_permission(viewer_user, 'viewer')
        assert not RoleService.has_permission(viewer_user, 'analyst')
        assert not RoleService.has_permission(viewer_user, 'manager')
        assert not RoleService.has_permission(viewer_user, 'admin')

    def test_superuser_has_all_permissions(self, user):
        """Test that superuser bypasses role checks"""
        user.is_superuser = True
        user.role = 'viewer'  # Even with viewer role
        user.save()

        assert RoleService.has_permission(user, 'admin')
        assert RoleService.has_permission(user, 'manager')

    def test_can_manage_users_admin_only(self, admin_user, manager_user):
        """Test that only admins can manage users"""
        assert RoleService.can_manage_users(admin_user)
        assert not RoleService.can_manage_users(manager_user)

    def test_can_create_clients(self, admin_user, manager_user, analyst_user, viewer_user):
        """Test client creation permissions"""
        assert RoleService.can_create_clients(admin_user)
        assert RoleService.can_create_clients(manager_user)
        assert not RoleService.can_create_clients(analyst_user)
        assert not RoleService.can_create_clients(viewer_user)

    def test_can_generate_reports(self, admin_user, manager_user, analyst_user, viewer_user):
        """Test report generation permissions"""
        assert RoleService.can_generate_reports(admin_user)
        assert RoleService.can_generate_reports(manager_user)
        assert RoleService.can_generate_reports(analyst_user)
        assert not RoleService.can_generate_reports(viewer_user)

    def test_can_view_reports(self, admin_user, manager_user, analyst_user, viewer_user):
        """Test report viewing permissions"""
        assert RoleService.can_view_reports(admin_user)
        assert RoleService.can_view_reports(manager_user)
        assert RoleService.can_view_reports(analyst_user)
        assert RoleService.can_view_reports(viewer_user)

    def test_can_delete_clients_admin_only(self, admin_user, manager_user):
        """Test that only admins can delete clients"""
        assert RoleService.can_delete_clients(admin_user)
        assert not RoleService.can_delete_clients(manager_user)

    def test_invalid_role(self):
        """Test permission check with invalid role"""
        from tests.factories import UserFactory

        user = UserFactory(role='viewer')
        # has_permission should handle invalid required_role gracefully
        result = RoleService.has_permission(user, 'invalid_role')
        assert result is False
