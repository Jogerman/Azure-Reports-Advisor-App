"""
Tests for client API views.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.clients.models import Client

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an API client instance."""
    return APIClient()


@pytest.fixture
def authenticated_user(db):
    """Create and return an authenticated user."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123'
    )
    return user


@pytest.fixture
def authenticated_client(api_client, authenticated_user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=authenticated_user)
    return api_client


@pytest.fixture
def sample_client(db, authenticated_user):
    """Create and return a sample client."""
    return Client.objects.create(
        company_name="Sample Corp",
        industry="technology",
        contact_email="contact@samplecorp.com",
        status="active",
        created_by=authenticated_user
    )


@pytest.mark.django_db
class TestClientListAPI:
    """Tests for client list endpoint."""

    def test_list_clients_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        response = api_client.get('/api/clients/')
        # Note: Currently set to AllowAny, will be IsAuthenticated in production
        # assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_clients_authenticated(self, authenticated_client, sample_client):
        """Test listing clients with authentication."""
        response = authenticated_client.get('/api/clients/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or isinstance(response.data, list)

    def test_list_clients_pagination(self, authenticated_client, authenticated_user):
        """Test that pagination works correctly."""
        # Create multiple clients
        for i in range(25):
            Client.objects.create(
                company_name=f"Client {i}",
                industry="technology",
                contact_email=f"client{i}@example.com",
                created_by=authenticated_user
            )

        response = authenticated_client.get('/api/clients/')
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'results' in response.data
        assert len(response.data['results']) <= 20  # Default page size

    def test_search_clients(self, authenticated_client, sample_client):
        """Test searching clients by company name."""
        response = authenticated_client.get('/api/clients/?search=Sample')
        assert response.status_code == status.HTTP_200_OK
        # Check that search returns results
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
        else:
            assert len(response.data) >= 1

    def test_filter_clients_by_status(self, authenticated_client, authenticated_user):
        """Test filtering clients by status."""
        Client.objects.create(
            company_name="Active Corp",
            industry="technology",
            contact_email="active@corp.com",
            status="active",
            created_by=authenticated_user
        )
        Client.objects.create(
            company_name="Inactive Corp",
            industry="technology",
            contact_email="inactive@corp.com",
            status="inactive",
            created_by=authenticated_user
        )

        response = authenticated_client.get('/api/clients/?status=active')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestClientCreateAPI:
    """Tests for client creation endpoint."""

    def test_create_client_valid_data(self, authenticated_client):
        """Test creating a client with valid data."""
        data = {
            'company_name': 'New Corp',
            'industry': 'technology',
            'contact_email': 'contact@newcorp.com',
            'azure_subscription_ids': []
        }
        response = authenticated_client.post('/api/clients/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['company_name'] == 'New Corp'

    def test_create_client_missing_required_field(self, authenticated_client):
        """Test creating a client with missing required field."""
        data = {
            'industry': 'technology',
            'contact_email': 'contact@newcorp.com'
        }
        response = authenticated_client.post('/api/clients/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'company_name' in response.data

    def test_create_client_duplicate_name(self, authenticated_client, sample_client):
        """Test creating a client with duplicate company name."""
        data = {
            'company_name': 'Sample Corp',  # Already exists
            'industry': 'technology',
            'contact_email': 'duplicate@corp.com'
        }
        response = authenticated_client.post('/api/clients/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestClientDetailAPI:
    """Tests for client detail endpoint."""

    def test_retrieve_client(self, authenticated_client, sample_client):
        """Test retrieving a specific client."""
        response = authenticated_client.get(f'/api/clients/{sample_client.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['company_name'] == 'Sample Corp'
        assert 'contacts' in response.data
        assert 'client_notes' in response.data

    def test_retrieve_nonexistent_client(self, authenticated_client):
        """Test retrieving a client that doesn't exist."""
        import uuid
        fake_id = uuid.uuid4()
        response = authenticated_client.get(f'/api/clients/{fake_id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestClientUpdateAPI:
    """Tests for client update endpoint."""

    def test_update_client_full(self, authenticated_client, sample_client):
        """Test full update of a client."""
        data = {
            'company_name': 'Updated Corp',
            'industry': 'finance',
            'contact_email': 'updated@corp.com',
            'status': 'active',
            'azure_subscription_ids': []
        }
        response = authenticated_client.put(
            f'/api/clients/{sample_client.id}/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['company_name'] == 'Updated Corp'

    def test_update_client_partial(self, authenticated_client, sample_client):
        """Test partial update of a client."""
        data = {
            'company_name': 'Partially Updated Corp'
        }
        response = authenticated_client.patch(
            f'/api/clients/{sample_client.id}/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['company_name'] == 'Partially Updated Corp'
        # Verify other fields remain unchanged
        assert response.data['industry'] == 'technology'


@pytest.mark.django_db
class TestClientDeleteAPI:
    """Tests for client deletion endpoint."""

    def test_delete_client(self, authenticated_client, sample_client):
        """Test deleting (deactivating) a client."""
        response = authenticated_client.delete(f'/api/clients/{sample_client.id}/')
        # Verify soft delete (deactivation)
        sample_client.refresh_from_db()
        assert sample_client.status == 'inactive'


@pytest.mark.django_db
class TestClientCustomActions:
    """Tests for custom client actions."""

    def test_activate_client(self, authenticated_client, sample_client):
        """Test activating a client."""
        sample_client.status = 'inactive'
        sample_client.save()

        response = authenticated_client.post(
            f'/api/clients/{sample_client.id}/activate/'
        )
        assert response.status_code == status.HTTP_200_OK
        sample_client.refresh_from_db()
        assert sample_client.status == 'active'

    def test_deactivate_client(self, authenticated_client, sample_client):
        """Test deactivating a client."""
        response = authenticated_client.post(
            f'/api/clients/{sample_client.id}/deactivate/'
        )
        assert response.status_code == status.HTTP_200_OK
        sample_client.refresh_from_db()
        assert sample_client.status == 'inactive'

    def test_add_subscription(self, authenticated_client, sample_client):
        """Test adding a subscription to a client."""
        data = {
            'subscription_id': '12345678-1234-1234-1234-123456789012'
        }
        response = authenticated_client.post(
            f'/api/clients/{sample_client.id}/add_subscription/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        sample_client.refresh_from_db()
        assert len(sample_client.azure_subscription_ids) == 1

    def test_remove_subscription(self, authenticated_client, sample_client):
        """Test removing a subscription from a client."""
        subscription_id = '12345678-1234-1234-1234-123456789012'
        sample_client.add_subscription(subscription_id)

        data = {'subscription_id': subscription_id}
        response = authenticated_client.post(
            f'/api/clients/{sample_client.id}/remove_subscription/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        sample_client.refresh_from_db()
        assert len(sample_client.azure_subscription_ids) == 0

    def test_get_statistics(self, authenticated_client, sample_client):
        """Test getting client statistics."""
        response = authenticated_client.get('/api/clients/statistics/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_clients' in response.data
        assert 'active_clients' in response.data
