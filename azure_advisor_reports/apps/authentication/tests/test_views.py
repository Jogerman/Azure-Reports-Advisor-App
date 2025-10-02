"""
Test cases for authentication views
Tests all API endpoints in apps.authentication.views
"""

import pytest
from unittest.mock import patch, Mock
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.authentication.services import JWTService

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.api
@pytest.mark.azure_ad
class TestAzureADLoginView:
    """Test suite for Azure AD login endpoint"""

    def test_successful_login_with_new_user(self, api_client, azure_token_mock, azure_user_info, mock_graph_api_success):
        """Test successful login creates new user"""
        with patch('apps.authentication.views.AzureADService') as mock_service:
            instance = mock_service.return_value
            instance.validate_token.return_value = (True, azure_user_info)

            # Mock user creation
            new_user = User.objects.create_user(
                username='testuser',
                email=azure_user_info['mail'],
                first_name=azure_user_info['givenName'],
                last_name=azure_user_info['surname'],
                azure_object_id=azure_user_info['id']
            )
            instance.create_or_update_user.return_value = new_user

            url = '/api/v1/auth/login/'
            data = {'access_token': azure_token_mock}

            response = api_client.post(url, data, format='json')

            assert response.status_code == status.HTTP_200_OK
            assert 'access_token' in response.data
            assert 'refresh_token' in response.data
            assert 'user' in response.data
            assert response.data['user']['email'] == azure_user_info['mail']

    def test_successful_login_with_existing_user(self, api_client, user, azure_token_mock, mock_graph_api_success):
        """Test successful login with existing user"""
        azure_info = {
            'id': user.azure_object_id or 'azure-id-123',
            'mail': user.email,
            'userPrincipalName': user.email,
            'givenName': user.first_name,
            'surname': user.last_name,
        }

        with patch('apps.authentication.views.AzureADService') as mock_service:
            instance = mock_service.return_value
            instance.validate_token.return_value = (True, azure_info)
            instance.create_or_update_user.return_value = user

            url = '/api/v1/auth/login/'
            data = {'access_token': azure_token_mock}

            response = api_client.post(url, data, format='json')

            assert response.status_code == status.HTTP_200_OK
            assert response.data['user']['id'] == str(user.id)

    def test_login_with_invalid_token(self, api_client):
        """Test login with invalid Azure AD token"""
        with patch('apps.authentication.views.AzureADService') as mock_service:
            instance = mock_service.return_value
            instance.validate_token.return_value = (False, None)

            url = '/api/v1/auth/login/'
            data = {'access_token': 'invalid_token'}

            response = api_client.post(url, data, format='json')

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert 'error' in response.data

    def test_login_without_token(self, api_client):
        """Test login without providing token"""
        url = '/api/v1/auth/login/'
        data = {}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'access_token' in response.data

    def test_login_updates_last_login(self, api_client, user, azure_token_mock):
        """Test that login updates last_login timestamp"""
        azure_info = {
            'id': user.azure_object_id or 'azure-id-123',
            'mail': user.email,
            'userPrincipalName': user.email,
            'givenName': user.first_name,
            'surname': user.last_name,
        }

        with patch('apps.authentication.views.AzureADService') as mock_service:
            instance = mock_service.return_value
            instance.validate_token.return_value = (True, azure_info)
            instance.create_or_update_user.return_value = user

            original_last_login = user.last_login

            url = '/api/v1/auth/login/'
            data = {'access_token': azure_token_mock}

            response = api_client.post(url, data, format='json')

            user.refresh_from_db()
            assert response.status_code == status.HTTP_200_OK
            assert user.last_login is not None

    def test_login_failure_on_user_creation_error(self, api_client, azure_token_mock, azure_user_info, mock_graph_api_success):
        """Test login fails when user creation fails"""
        with patch('apps.authentication.views.AzureADService') as mock_service:
            instance = mock_service.return_value
            instance.validate_token.return_value = (True, azure_user_info)
            instance.create_or_update_user.return_value = None  # Simulate failure

            url = '/api/v1/auth/login/'
            data = {'access_token': azure_token_mock}

            response = api_client.post(url, data, format='json')

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert 'error' in response.data


@pytest.mark.django_db
@pytest.mark.api
@pytest.mark.jwt
class TestTokenRefreshView:
    """Test suite for token refresh endpoint"""

    def test_successful_token_refresh(self, api_client, user):
        """Test successful token refresh"""
        tokens = JWTService.generate_token(user)
        refresh_token = tokens['refresh_token']

        url = '/api/v1/auth/refresh/'
        data = {'refresh_token': refresh_token}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data
        assert 'expires_in' in response.data
        assert 'token_type' in response.data

    def test_refresh_with_invalid_token(self, api_client):
        """Test refresh with invalid token"""
        url = '/api/v1/auth/refresh/'
        data = {'refresh_token': 'invalid_token'}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data

    def test_refresh_with_expired_token(self, api_client, expired_jwt_token):
        """Test refresh with expired token"""
        url = '/api/v1/auth/refresh/'
        data = {'refresh_token': expired_jwt_token}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_without_token(self, api_client):
        """Test refresh without providing token"""
        url = '/api/v1/auth/refresh/'
        data = {}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'refresh_token' in response.data


@pytest.mark.django_db
@pytest.mark.api
class TestLogoutView:
    """Test suite for logout endpoint"""

    def test_successful_logout(self, authenticated_client):
        """Test successful logout"""
        url = '/api/v1/auth/logout/'
        data = {}

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data

    def test_logout_with_refresh_token(self, authenticated_client, user):
        """Test logout with refresh token provided"""
        tokens = JWTService.generate_token(user)

        url = '/api/v1/auth/logout/'
        data = {'refresh_token': tokens['refresh_token']}

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK

    def test_logout_requires_authentication(self, api_client):
        """Test that logout requires authentication"""
        url = '/api/v1/auth/logout/'
        data = {}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@pytest.mark.api
class TestCurrentUserView:
    """Test suite for current user endpoint"""

    def test_get_current_user(self, authenticated_client, user):
        """Test getting current user information"""
        url = '/api/v1/auth/user/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(user.id)
        assert response.data['email'] == user.email
        assert 'full_name' in response.data
        assert 'role' in response.data

    def test_get_current_user_requires_authentication(self, api_client):
        """Test that getting current user requires authentication"""
        url = '/api/v1/auth/user/'

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_current_user_profile(self, authenticated_client, user):
        """Test updating current user profile"""
        url = '/api/v1/auth/user/'
        data = {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast',
            'phone_number': '+1234567890'
        }

        response = authenticated_client.put(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'UpdatedFirst'
        assert response.data['last_name'] == 'UpdatedLast'
        assert response.data['phone_number'] == '+1234567890'

    def test_partial_update_current_user_profile(self, authenticated_client, user):
        """Test partially updating current user profile"""
        url = '/api/v1/auth/user/'
        data = {'first_name': 'NewFirst'}

        response = authenticated_client.put(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'NewFirst'

    def test_update_profile_with_invalid_data(self, authenticated_client):
        """Test updating profile with invalid data"""
        url = '/api/v1/auth/user/'
        data = {'phone_number': 'invalid-phone'}

        response = authenticated_client.put(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.api
@pytest.mark.permissions
class TestUserViewSet:
    """Test suite for user management endpoints (admin only)"""

    def test_list_users_as_admin(self, admin_client, user, manager_user):
        """Test listing users as admin"""
        url = '/api/v1/users/'

        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2  # At least admin and other users

    def test_list_users_as_non_admin_denied(self, authenticated_client):
        """Test that non-admin cannot list users"""
        url = '/api/v1/users/'

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_filter_users_by_role(self, admin_client, analyst_user, manager_user):
        """Test filtering users by role"""
        url = '/api/v1/users/?role=analyst'

        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # All returned users should be analysts
        for user_data in response.data['results']:
            assert user_data['role'] == 'analyst'

    def test_filter_users_by_active_status(self, admin_client, user):
        """Test filtering users by active status"""
        user.is_active = False
        user.save()

        url = '/api/v1/users/?is_active=true'

        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # User should not be in results
        user_ids = [u['id'] for u in response.data['results']]
        assert str(user.id) not in user_ids

    def test_search_users(self, admin_client, user):
        """Test searching users by name or email"""
        user.first_name = "SearchTest"
        user.save()

        url = f'/api/v1/users/?search=SearchTest'

        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_get_user_detail_as_admin(self, admin_client, user):
        """Test getting user detail as admin"""
        url = f'/api/v1/users/{user.id}/'

        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(user.id)
        assert response.data['email'] == user.email

    def test_create_user_as_admin(self, admin_client):
        """Test creating a user as admin"""
        url = '/api/v1/users/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'analyst'
        }

        response = admin_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == 'newuser@example.com'

    def test_update_user_as_admin(self, admin_client, user):
        """Test updating a user as admin"""
        url = f'/api/v1/users/{user.id}/'
        data = {
            'first_name': 'UpdatedName',
            'role': 'manager'
        }

        response = admin_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'UpdatedName'

    def test_delete_user_as_admin(self, admin_client, user):
        """Test deleting a user as admin"""
        url = f'/api/v1/users/{user.id}/'

        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(id=user.id).exists()

    def test_activate_user(self, admin_client, user):
        """Test activating a deactivated user"""
        user.is_active = False
        user.save()

        url = f'/api/v1/users/{user.id}/activate/'

        response = admin_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active is True

    def test_deactivate_user(self, admin_client, user):
        """Test deactivating a user"""
        url = f'/api/v1/users/{user.id}/deactivate/'

        response = admin_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active is False

    def test_cannot_deactivate_self(self, admin_client, admin_user):
        """Test that admin cannot deactivate their own account"""
        url = f'/api/v1/users/{admin_user.id}/deactivate/'

        response = admin_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_change_user_role(self, admin_client, user):
        """Test changing user role"""
        url = f'/api/v1/users/{user.id}/change-role/'
        data = {'role': 'manager'}

        response = admin_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.role == 'manager'

    def test_cannot_change_own_role(self, admin_client, admin_user):
        """Test that admin cannot change their own role"""
        url = f'/api/v1/users/{admin_user.id}/change-role/'
        data = {'role': 'viewer'}

        response = admin_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_role_with_invalid_role(self, admin_client, user):
        """Test changing role with invalid role value"""
        url = f'/api/v1/users/{user.id}/change-role/'
        data = {'role': 'invalid_role'}

        response = admin_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_user_statistics(self, admin_client, user, admin_user, manager_user):
        """Test getting user statistics"""
        url = '/api/v1/users/statistics/'

        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'total_users' in response.data
        assert 'active_users' in response.data
        assert 'inactive_users' in response.data
        assert 'users_by_role' in response.data


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.api
class TestAuthenticationFlowIntegration:
    """Integration tests for complete authentication flows"""

    def test_complete_login_and_profile_update_flow(self, api_client, azure_token_mock, azure_user_info, mock_graph_api_success):
        """Test complete flow: login -> get profile -> update profile"""
        # Step 1: Login
        with patch('apps.authentication.views.AzureADService') as mock_service:
            instance = mock_service.return_value
            instance.validate_token.return_value = (True, azure_user_info)

            new_user = User.objects.create_user(
                username='testuser',
                email=azure_user_info['mail'],
                first_name=azure_user_info['givenName'],
                last_name=azure_user_info['surname'],
                azure_object_id=azure_user_info['id']
            )
            instance.create_or_update_user.return_value = new_user

            login_response = api_client.post(
                '/api/v1/auth/login/',
                {'access_token': azure_token_mock},
                format='json'
            )

            assert login_response.status_code == status.HTTP_200_OK
            access_token = login_response.data['access_token']

        # Step 2: Get profile
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        profile_response = api_client.get('/api/v1/auth/user/')

        assert profile_response.status_code == status.HTTP_200_OK

        # Step 3: Update profile
        update_response = api_client.put(
            '/api/v1/auth/user/',
            {'first_name': 'Updated', 'last_name': 'Name'},
            format='json'
        )

        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.data['first_name'] == 'Updated'

    def test_token_refresh_and_access_flow(self, api_client, user):
        """Test flow: generate tokens -> use access -> refresh -> use new access"""
        # Generate initial tokens
        tokens = JWTService.generate_token(user)

        # Use access token
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}')
        response1 = api_client.get('/api/v1/auth/user/')
        assert response1.status_code == status.HTTP_200_OK

        # Refresh token
        refresh_response = api_client.post(
            '/api/v1/auth/refresh/',
            {'refresh_token': tokens['refresh_token']},
            format='json'
        )
        assert refresh_response.status_code == status.HTTP_200_OK
        new_access_token = refresh_response.data['access_token']

        # Use new access token
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        response2 = api_client.get('/api/v1/auth/user/')
        assert response2.status_code == status.HTTP_200_OK
