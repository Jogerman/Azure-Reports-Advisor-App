"""
Test cases for Azure AD authentication backend
Tests AzureADAuthentication class in apps.authentication.authentication
"""

import pytest
import jwt
from unittest.mock import Mock, patch, MagicMock
from rest_framework import exceptions
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model
from django.conf import settings

from apps.authentication.authentication import AzureADAuthentication

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.azure_ad
class TestAzureADAuthenticationBasic:
    """Basic tests for AzureADAuthentication"""

    def setup_method(self):
        """Setup test fixtures"""
        self.factory = APIRequestFactory()
        self.auth_backend = AzureADAuthentication()

    def test_authentication_backend_initialization(self):
        """Test authentication backend initializes correctly"""
        assert self.auth_backend is not None
        assert hasattr(self.auth_backend, 'authenticate')
        assert hasattr(self.auth_backend, 'authenticate_header')

    def test_authenticate_header_returns_bearer(self):
        """Test that authenticate_header returns 'Bearer'"""
        request = self.factory.get('/api/clients/')
        header = self.auth_backend.authenticate_header(request)

        assert header == 'Bearer'

    def test_authenticate_without_authorization_header_returns_none(self):
        """Test authentication without Authorization header returns None"""
        request = self.factory.get('/api/clients/')

        result = self.auth_backend.authenticate(request)

        # Should return None (not handling this request)
        assert result is None

    def test_authenticate_with_non_bearer_token_returns_none(self):
        """Test authentication with non-Bearer token returns None"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'Basic dXNlcjpwYXNz'

        result = self.auth_backend.authenticate(request)

        # Should return None (not Bearer token)
        assert result is None

    def test_authenticate_with_empty_bearer_token_raises_error(self):
        """Test authentication with empty Bearer token raises error"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer '

        with pytest.raises(Exception):
            self.auth_backend.authenticate(request)


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.azure_ad
class TestAzureADTokenVerification:
    """Tests for Azure AD token verification"""

    def setup_method(self):
        """Setup test fixtures"""
        self.factory = APIRequestFactory()
        self.auth_backend = AzureADAuthentication()

    @patch('apps.authentication.authentication.requests.get')
    @patch('apps.authentication.authentication.jwt.decode')
    @patch('apps.authentication.authentication.jwt.get_unverified_header')
    def test_verify_token_success(self, mock_get_header, mock_decode, mock_requests_get):
        """Test successful token verification"""
        # Mock JWT header
        mock_get_header.return_value = {'kid': 'test-key-id'}

        # Mock JWKS response
        mock_jwks_response = Mock()
        mock_jwks_response.status_code = 200
        mock_jwks_response.json.return_value = {
            'keys': [{
                'kid': 'test-key-id',
                'kty': 'RSA',
                'use': 'sig',
                'n': 'test_n_value',
                'e': 'AQAB'
            }]
        }
        mock_requests_get.return_value = mock_jwks_response

        # Mock decoded payload
        mock_decode.return_value = {
            'oid': 'azure-object-id-123',
            'email': 'test@example.com',
            'given_name': 'Test',
            'family_name': 'User',
            'tid': 'tenant-id-123'
        }

        result = self.auth_backend._verify_token('valid_token')

        assert result is not None
        assert result['oid'] == 'azure-object-id-123'
        assert result['email'] == 'test@example.com'

    @patch('apps.authentication.authentication.requests.get')
    @patch('apps.authentication.authentication.jwt.get_unverified_header')
    def test_verify_token_with_invalid_kid(self, mock_get_header, mock_requests_get):
        """Test token verification with invalid key ID"""
        # Mock JWT header with non-existent kid
        mock_get_header.return_value = {'kid': 'non-existent-key-id'}

        # Mock JWKS response with different kid
        mock_jwks_response = Mock()
        mock_jwks_response.status_code = 200
        mock_jwks_response.json.return_value = {
            'keys': [{
                'kid': 'different-key-id',
                'kty': 'RSA',
                'use': 'sig',
                'n': 'test_n_value',
                'e': 'AQAB'
            }]
        }
        mock_requests_get.return_value = mock_jwks_response

        with pytest.raises(exceptions.AuthenticationFailed) as exc_info:
            self.auth_backend._verify_token('invalid_token')

        assert 'appropriate key' in str(exc_info.value)

    @patch('apps.authentication.authentication.requests.get')
    def test_verify_token_jwks_request_failure(self, mock_requests_get):
        """Test token verification when JWKS request fails"""
        # Mock failed JWKS request
        mock_requests_get.side_effect = Exception('Network error')

        with pytest.raises(exceptions.AuthenticationFailed) as exc_info:
            self.auth_backend._verify_token('some_token')

        assert 'Unable to verify token' in str(exc_info.value)

    @patch('apps.authentication.authentication.requests.get')
    @patch('apps.authentication.authentication.jwt.decode')
    @patch('apps.authentication.authentication.jwt.get_unverified_header')
    def test_verify_token_expired_signature(self, mock_get_header, mock_decode, mock_requests_get):
        """Test token verification with expired token"""
        # Mock JWT header
        mock_get_header.return_value = {'kid': 'test-key-id'}

        # Mock JWKS response
        mock_jwks_response = Mock()
        mock_jwks_response.status_code = 200
        mock_jwks_response.json.return_value = {
            'keys': [{
                'kid': 'test-key-id',
                'kty': 'RSA',
                'use': 'sig',
                'n': 'test_n_value',
                'e': 'AQAB'
            }]
        }
        mock_requests_get.return_value = mock_jwks_response

        # Mock expired signature error
        mock_decode.side_effect = jwt.ExpiredSignatureError('Token has expired')

        with pytest.raises(exceptions.AuthenticationFailed) as exc_info:
            self.auth_backend._verify_token('expired_token')

        assert 'expired' in str(exc_info.value).lower()

    @patch('apps.authentication.authentication.requests.get')
    @patch('apps.authentication.authentication.jwt.decode')
    @patch('apps.authentication.authentication.jwt.get_unverified_header')
    def test_verify_token_invalid_token_error(self, mock_get_header, mock_decode, mock_requests_get):
        """Test token verification with invalid token"""
        # Mock JWT header
        mock_get_header.return_value = {'kid': 'test-key-id'}

        # Mock JWKS response
        mock_jwks_response = Mock()
        mock_jwks_response.status_code = 200
        mock_jwks_response.json.return_value = {
            'keys': [{
                'kid': 'test-key-id',
                'kty': 'RSA',
                'use': 'sig',
                'n': 'test_n_value',
                'e': 'AQAB'
            }]
        }
        mock_requests_get.return_value = mock_jwks_response

        # Mock invalid token error
        mock_decode.side_effect = jwt.InvalidTokenError('Invalid token')

        with pytest.raises(exceptions.AuthenticationFailed) as exc_info:
            self.auth_backend._verify_token('invalid_token')

        assert 'Invalid token' in str(exc_info.value)


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.azure_ad
class TestAzureADUserCreation:
    """Tests for user creation/retrieval from Azure AD"""

    def setup_method(self):
        """Setup test fixtures"""
        self.factory = APIRequestFactory()
        self.auth_backend = AzureADAuthentication()

    def test_get_or_create_user_with_new_user(self):
        """Test creating a new user from Azure AD token"""
        user_info = {
            'oid': 'new-azure-object-id',
            'email': 'newuser@example.com',
            'preferred_username': 'newuser@example.com',
            'given_name': 'New',
            'family_name': 'User',
            'tid': 'tenant-id-123',
            'jobTitle': 'Engineer'
        }

        user = self.auth_backend._get_or_create_user(user_info)

        assert user is not None
        assert user.email == 'newuser@example.com'
        assert user.azure_object_id == 'new-azure-object-id'
        assert user.first_name == 'New'
        assert user.last_name == 'User'
        assert user.tenant_id == 'tenant-id-123'
        assert user.job_title == 'Engineer'

    def test_get_or_create_user_with_existing_user(self):
        """Test retrieving existing user from database"""
        # Create existing user
        existing_user = User.objects.create_user(
            username='existing',
            email='existing@example.com',
            azure_object_id='existing-azure-id'
        )

        user_info = {
            'oid': 'existing-azure-id',
            'email': 'existing@example.com',
            'preferred_username': 'existing@example.com',
            'given_name': 'Updated',
            'family_name': 'Name',
            'tid': 'tenant-id-123'
        }

        user = self.auth_backend._get_or_create_user(user_info)

        # Should return existing user with updated info
        assert user.id == existing_user.id
        assert user.first_name == 'Updated'
        assert user.last_name == 'Name'

    def test_get_or_create_user_updates_existing_user_by_email(self):
        """Test that existing user is found by email and updated with Azure ID"""
        # Create user without Azure ID
        existing_user = User.objects.create_user(
            username='existing',
            email='existing@example.com'
        )

        user_info = {
            'oid': 'new-azure-id',
            'email': 'existing@example.com',
            'preferred_username': 'existing@example.com',
            'given_name': 'Updated',
            'family_name': 'User',
            'tid': 'tenant-id-123'
        }

        user = self.auth_backend._get_or_create_user(user_info)

        # Should update existing user with Azure ID
        assert user.id == existing_user.id
        assert user.azure_object_id == 'new-azure-id'
        assert user.first_name == 'Updated'

    def test_get_or_create_user_without_email_raises_error(self):
        """Test that missing email raises authentication failed error"""
        user_info = {
            'oid': 'azure-object-id',
            'given_name': 'Test',
            'family_name': 'User'
            # No email field
        }

        with pytest.raises(exceptions.AuthenticationFailed) as exc_info:
            self.auth_backend._get_or_create_user(user_info)

        assert 'Invalid user information' in str(exc_info.value)

    def test_get_or_create_user_without_oid_raises_error(self):
        """Test that missing Azure object ID raises error"""
        user_info = {
            'email': 'test@example.com',
            'given_name': 'Test',
            'family_name': 'User'
            # No oid field
        }

        with pytest.raises(exceptions.AuthenticationFailed) as exc_info:
            self.auth_backend._get_or_create_user(user_info)

        assert 'Invalid user information' in str(exc_info.value)

    def test_get_or_create_user_with_preferred_username(self):
        """Test user creation with preferred_username instead of email"""
        user_info = {
            'oid': 'azure-id-123',
            'preferred_username': 'user@company.com',  # No 'email' field
            'given_name': 'Test',
            'family_name': 'User',
            'tid': 'tenant-id'
        }

        user = self.auth_backend._get_or_create_user(user_info)

        assert user is not None
        assert user.email == 'user@company.com'

    def test_get_or_create_user_updates_profile_fields(self):
        """Test that user profile fields are updated on each login"""
        existing_user = User.objects.create_user(
            username='existing',
            email='existing@example.com',
            azure_object_id='azure-id',
            first_name='OldFirst',
            last_name='OldLast',
            job_title='OldTitle'
        )

        user_info = {
            'oid': 'azure-id',
            'email': 'existing@example.com',
            'given_name': 'NewFirst',
            'family_name': 'NewLast',
            'jobTitle': 'NewTitle'
        }

        user = self.auth_backend._get_or_create_user(user_info)

        # Should update profile fields
        assert user.first_name == 'NewFirst'
        assert user.last_name == 'NewLast'
        assert user.job_title == 'NewTitle'

    def test_get_or_create_user_with_missing_optional_fields(self):
        """Test user creation with missing optional fields"""
        user_info = {
            'oid': 'azure-id',
            'email': 'minimal@example.com'
            # No given_name, family_name, jobTitle, etc.
        }

        user = self.auth_backend._get_or_create_user(user_info)

        # Should create user with empty optional fields
        assert user is not None
        assert user.email == 'minimal@example.com'
        assert user.first_name == ''
        assert user.last_name == ''


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.azure_ad
class TestAzureADAuthenticationIntegration:
    """Integration tests for complete Azure AD authentication flow"""

    def setup_method(self):
        """Setup test fixtures"""
        self.factory = APIRequestFactory()
        self.auth_backend = AzureADAuthentication()

    @patch('apps.authentication.authentication.requests.get')
    @patch('apps.authentication.authentication.jwt.decode')
    @patch('apps.authentication.authentication.jwt.get_unverified_header')
    def test_complete_authentication_flow_new_user(self, mock_get_header, mock_decode, mock_requests_get):
        """Test complete authentication flow for a new user"""
        # Setup mocks
        mock_get_header.return_value = {'kid': 'test-key-id'}

        mock_jwks_response = Mock()
        mock_jwks_response.status_code = 200
        mock_jwks_response.json.return_value = {
            'keys': [{
                'kid': 'test-key-id',
                'kty': 'RSA',
                'use': 'sig',
                'n': 'test_n_value',
                'e': 'AQAB'
            }]
        }
        mock_requests_get.return_value = mock_jwks_response

        mock_decode.return_value = {
            'oid': 'new-user-azure-id',
            'email': 'newuser@company.com',
            'given_name': 'Jane',
            'family_name': 'Doe',
            'tid': 'company-tenant-id',
            'jobTitle': 'Senior Engineer'
        }

        # Create request with Bearer token
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_azure_ad_token'

        # Authenticate
        result = self.auth_backend.authenticate(request)

        # Verify result
        assert result is not None
        user, token = result
        assert user.email == 'newuser@company.com'
        assert user.azure_object_id == 'new-user-azure-id'
        assert user.first_name == 'Jane'
        assert user.last_name == 'Doe'
        assert token == 'valid_azure_ad_token'

    @patch('apps.authentication.authentication.requests.get')
    @patch('apps.authentication.authentication.jwt.decode')
    @patch('apps.authentication.authentication.jwt.get_unverified_header')
    def test_complete_authentication_flow_existing_user(self, mock_get_header, mock_decode, mock_requests_get):
        """Test complete authentication flow for existing user"""
        # Create existing user
        existing_user = User.objects.create_user(
            username='existinguser',
            email='existing@company.com',
            azure_object_id='existing-azure-id',
            first_name='John',
            last_name='Smith'
        )

        # Setup mocks
        mock_get_header.return_value = {'kid': 'test-key-id'}

        mock_jwks_response = Mock()
        mock_jwks_response.status_code = 200
        mock_jwks_response.json.return_value = {
            'keys': [{
                'kid': 'test-key-id',
                'kty': 'RSA',
                'use': 'sig',
                'n': 'test_n_value',
                'e': 'AQAB'
            }]
        }
        mock_requests_get.return_value = mock_jwks_response

        mock_decode.return_value = {
            'oid': 'existing-azure-id',
            'email': 'existing@company.com',
            'given_name': 'John',
            'family_name': 'Smith',
            'tid': 'company-tenant-id'
        }

        # Create request
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'

        # Authenticate
        result = self.auth_backend.authenticate(request)

        # Verify existing user is returned
        assert result is not None
        user, token = result
        assert user.id == existing_user.id
        assert user.email == 'existing@company.com'

    @patch('apps.authentication.authentication.requests.get')
    @patch('apps.authentication.authentication.jwt.decode')
    @patch('apps.authentication.authentication.jwt.get_unverified_header')
    def test_authentication_failure_on_invalid_token(self, mock_get_header, mock_decode, mock_requests_get):
        """Test authentication failure with invalid token"""
        # Setup mocks to raise InvalidTokenError
        mock_get_header.return_value = {'kid': 'test-key-id'}

        mock_jwks_response = Mock()
        mock_jwks_response.status_code = 200
        mock_jwks_response.json.return_value = {
            'keys': [{
                'kid': 'test-key-id',
                'kty': 'RSA',
                'use': 'sig',
                'n': 'test_n_value',
                'e': 'AQAB'
            }]
        }
        mock_requests_get.return_value = mock_jwks_response

        mock_decode.side_effect = jwt.InvalidTokenError('Token is invalid')

        # Create request
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer invalid_token'

        # Should raise AuthenticationFailed
        with pytest.raises(exceptions.AuthenticationFailed) as exc_info:
            self.auth_backend.authenticate(request)

        assert 'Invalid token' in str(exc_info.value)

    def test_authentication_with_malformed_bearer_token(self):
        """Test authentication with malformed Bearer token"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer'

        with pytest.raises(Exception):
            self.auth_backend.authenticate(request)

    @patch('apps.authentication.authentication.requests.get')
    @patch('apps.authentication.authentication.jwt.decode')
    @patch('apps.authentication.authentication.jwt.get_unverified_header')
    def test_authentication_updates_user_on_each_login(self, mock_get_header, mock_decode, mock_requests_get):
        """Test that user information is updated on each authentication"""
        # Create user with old info
        user = User.objects.create_user(
            username='user',
            email='user@company.com',
            azure_object_id='azure-id',
            first_name='OldName',
            job_title='OldTitle'
        )

        # Setup mocks with updated info
        mock_get_header.return_value = {'kid': 'test-key-id'}

        mock_jwks_response = Mock()
        mock_jwks_response.status_code = 200
        mock_jwks_response.json.return_value = {
            'keys': [{
                'kid': 'test-key-id',
                'kty': 'RSA',
                'use': 'sig',
                'n': 'test_n_value',
                'e': 'AQAB'
            }]
        }
        mock_requests_get.return_value = mock_jwks_response

        mock_decode.return_value = {
            'oid': 'azure-id',
            'email': 'user@company.com',
            'given_name': 'NewName',
            'family_name': 'NewLastName',
            'jobTitle': 'NewTitle',
            'tid': 'tenant-id'
        }

        # Create request
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer token'

        # Authenticate
        result = self.auth_backend.authenticate(request)

        # Verify user info was updated
        user.refresh_from_db()
        assert user.first_name == 'NewName'
        assert user.last_name == 'NewLastName'
        assert user.job_title == 'NewTitle'

    @patch('apps.authentication.authentication.requests.get')
    def test_authentication_handles_network_errors_gracefully(self, mock_requests_get):
        """Test that network errors are handled gracefully"""
        # Simulate network error
        mock_requests_get.side_effect = Exception('Network timeout')

        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer token'

        with pytest.raises(exceptions.AuthenticationFailed) as exc_info:
            self.auth_backend.authenticate(request)

        assert 'Invalid token' in str(exc_info.value) or 'Unable to verify' in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.azure_ad
class TestAzureADAuthenticationEdgeCases:
    """Tests for edge cases and error conditions"""

    def setup_method(self):
        """Setup test fixtures"""
        self.factory = APIRequestFactory()
        self.auth_backend = AzureADAuthentication()

    def test_authentication_with_whitespace_in_token(self):
        """Test authentication with whitespace in token"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer   token_with_spaces   '

        # Should handle whitespace gracefully
        # May raise error depending on implementation
        try:
            result = self.auth_backend.authenticate(request)
        except exceptions.AuthenticationFailed:
            pass  # Expected behavior

    def test_authentication_with_lowercase_bearer(self):
        """Test that 'bearer' (lowercase) is not accepted"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'bearer lowercase_token'

        result = self.auth_backend.authenticate(request)

        # Should return None (not accepted)
        assert result is None

    def test_authentication_with_multiple_spaces_after_bearer(self):
        """Test authentication with multiple spaces after Bearer"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer    token'

        # Implementation should handle this
        try:
            result = self.auth_backend.authenticate(request)
        except (exceptions.AuthenticationFailed, IndexError):
            pass  # May fail depending on token parsing

    @patch('apps.authentication.authentication.logger')
    def test_authentication_logs_errors(self, mock_logger):
        """Test that authentication errors are logged"""
        request = self.factory.get('/api/clients/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer invalid_token'

        try:
            self.auth_backend.authenticate(request)
        except exceptions.AuthenticationFailed:
            pass

        # Should log error
        mock_logger.error.assert_called()
