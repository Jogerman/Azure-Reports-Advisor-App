"""
Comprehensive tests for Azure Integration API views.

Tests all endpoints in AzureSubscriptionViewSet including:
- CRUD operations (list, retrieve, create, update, destroy)
- Custom actions (test-connection, statistics, sync-now, reports)
- Permissions (owner vs non-owner, authenticated vs anonymous)
- Filtering and searching
- Error handling
"""

import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.utils import timezone
from rest_framework import status


@pytest.fixture
def azure_subscription_data():
    """Valid Azure subscription creation data."""
    return {
        'name': 'Test Subscription',
        'subscription_id': '12345678-1234-1234-1234-123456789012',
        'tenant_id': '87654321-4321-4321-4321-210987654321',
        'client_id': 'abcdef12-ab12-ab12-ab12-abcdef123456',
        'client_secret': 'test-secret-key-12345678901234567890',
        'is_active': True,
    }


@pytest.fixture
def azure_subscription(db, test_user):
    """Create a test Azure subscription."""
    from apps.azure_integration.models import AzureSubscription

    subscription = AzureSubscription.objects.create(
        name='Test Subscription',
        subscription_id='12345678-1234-1234-1234-123456789012',
        tenant_id='87654321-4321-4321-4321-210987654321',
        client_id='abcdef12-ab12-ab12-ab12-abcdef123456',
        created_by=test_user,
        is_active=True,
        sync_status='never_synced',
    )
    # Set encrypted secret
    subscription.client_secret = 'test-secret-key-12345678901234567890'
    subscription.save()
    return subscription


@pytest.fixture
def other_user_subscription(db, django_user_model):
    """Create a subscription owned by a different user."""
    from apps.azure_integration.models import AzureSubscription

    other_user = django_user_model.objects.create_user(
        username='otheruser',
        email='other@example.com',
        password='testpass123'
    )

    subscription = AzureSubscription.objects.create(
        name='Other User Subscription',
        subscription_id='99999999-9999-9999-9999-999999999999',
        tenant_id='88888888-8888-8888-8888-888888888888',
        client_id='77777777-7777-7777-7777-777777777777',
        created_by=other_user,
        is_active=True,
        sync_status='never_synced',
    )
    subscription.client_secret = 'other-user-secret-key-123456789012'
    subscription.save()
    return subscription


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestAzureSubscriptionViewSetList:
    """Test GET /api/v1/azure/subscriptions/ - List subscriptions."""

    def test_list_subscriptions_authenticated(self, authenticated_api_client, azure_subscription):
        """Test authenticated user can list their own subscriptions."""
        response = authenticated_api_client.get('/api/v1/azure/subscriptions/')

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(azure_subscription.id)
        assert response.data['results'][0]['name'] == 'Test Subscription'
        # Verify client_secret is not exposed
        assert 'client_secret' not in response.data['results'][0]
        assert 'client_secret_encrypted' not in response.data['results'][0]

    def test_list_subscriptions_unauthenticated(self, api_client):
        """Test unauthenticated request is rejected."""
        response = api_client.get('/api/v1/azure/subscriptions/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_subscriptions_only_shows_own(
        self, authenticated_api_client, azure_subscription, other_user_subscription
    ):
        """Test users only see their own subscriptions."""
        response = authenticated_api_client.get('/api/v1/azure/subscriptions/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(azure_subscription.id)
        # Should not include other user's subscription
        subscription_ids = [s['id'] for s in response.data['results']]
        assert str(other_user_subscription.id) not in subscription_ids

    def test_list_subscriptions_filter_by_is_active(
        self, authenticated_api_client, azure_subscription
    ):
        """Test filtering by is_active."""
        # Create inactive subscription
        from apps.azure_integration.models import AzureSubscription
        inactive_sub = AzureSubscription.objects.create(
            name='Inactive Subscription',
            subscription_id='11111111-1111-1111-1111-111111111111',
            tenant_id='22222222-2222-2222-2222-222222222222',
            client_id='33333333-3333-3333-3333-333333333333',
            created_by=azure_subscription.created_by,
            is_active=False,
        )
        inactive_sub.client_secret = 'inactive-secret-key-1234567890123'
        inactive_sub.save()

        # Filter for active only
        response = authenticated_api_client.get('/api/v1/azure/subscriptions/?is_active=true')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['is_active'] is True

        # Filter for inactive only
        response = authenticated_api_client.get('/api/v1/azure/subscriptions/?is_active=false')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['is_active'] is False

    def test_list_subscriptions_filter_by_sync_status(
        self, authenticated_api_client, azure_subscription
    ):
        """Test filtering by sync_status."""
        # Update subscription sync status
        azure_subscription.sync_status = 'success'
        azure_subscription.save()

        response = authenticated_api_client.get(
            '/api/v1/azure/subscriptions/?sync_status=success'
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['sync_status'] == 'success'

    def test_list_subscriptions_search_by_name(
        self, authenticated_api_client, azure_subscription
    ):
        """Test searching by subscription name."""
        response = authenticated_api_client.get('/api/v1/azure/subscriptions/?search=Test')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

        response = authenticated_api_client.get('/api/v1/azure/subscriptions/?search=NonExistent')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0

    def test_list_subscriptions_ordering(self, authenticated_api_client, azure_subscription):
        """Test ordering results."""
        # Create another subscription
        from apps.azure_integration.models import AzureSubscription
        newer_sub = AzureSubscription.objects.create(
            name='Newer Subscription',
            subscription_id='44444444-4444-4444-4444-444444444444',
            tenant_id='55555555-5555-5555-5555-555555555555',
            client_id='66666666-6666-6666-6666-666666666666',
            created_by=azure_subscription.created_by,
            is_active=True,
        )
        newer_sub.client_secret = 'newer-secret-key-12345678901234567'
        newer_sub.save()

        # Default ordering (newest first)
        response = authenticated_api_client.get('/api/v1/azure/subscriptions/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['id'] == str(newer_sub.id)

        # Order by name
        response = authenticated_api_client.get('/api/v1/azure/subscriptions/?ordering=name')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['name'] == 'Newer Subscription'


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestAzureSubscriptionViewSetRetrieve:
    """Test GET /api/v1/azure/subscriptions/{id}/ - Retrieve subscription."""

    def test_retrieve_subscription_success(self, authenticated_api_client, azure_subscription):
        """Test retrieving own subscription."""
        response = authenticated_api_client.get(
            f'/api/v1/azure/subscriptions/{azure_subscription.id}/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(azure_subscription.id)
        assert response.data['name'] == 'Test Subscription'
        assert response.data['subscription_id'] == '12345678-1234-1234-1234-123456789012'
        # Verify sensitive data not exposed
        assert 'client_secret' not in response.data
        assert 'client_secret_encrypted' not in response.data

    def test_retrieve_subscription_not_found(self, authenticated_api_client):
        """Test retrieving non-existent subscription."""
        response = authenticated_api_client.get(
            '/api/v1/azure/subscriptions/00000000-0000-0000-0000-000000000000/'
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_subscription_not_owner(
        self, authenticated_api_client, other_user_subscription
    ):
        """Test cannot retrieve other user's subscription."""
        response = authenticated_api_client.get(
            f'/api/v1/azure/subscriptions/{other_user_subscription.id}/'
        )
        # Should return 404 (not found) because queryset is filtered by owner
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_subscription_unauthenticated(self, api_client, azure_subscription):
        """Test unauthenticated request is rejected."""
        response = api_client.get(f'/api/v1/azure/subscriptions/{azure_subscription.id}/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestAzureSubscriptionViewSetCreate:
    """Test POST /api/v1/azure/subscriptions/ - Create subscription."""

    def test_create_subscription_success(
        self, authenticated_api_client, azure_subscription_data
    ):
        """Test creating a subscription with valid data."""
        from apps.azure_integration.models import AzureSubscription

        response = authenticated_api_client.post(
            '/api/v1/azure/subscriptions/',
            azure_subscription_data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert response.data['name'] == 'Test Subscription'
        assert response.data['is_active'] is True
        assert response.data['sync_status'] == 'never_synced'
        # Verify client_secret not in response
        assert 'client_secret' not in response.data

        # Verify subscription was created in database
        subscription = AzureSubscription.objects.get(id=response.data['id'])
        assert subscription.name == 'Test Subscription'
        assert subscription.created_by.id == authenticated_api_client.handler._force_user.id
        # Verify secret was encrypted
        assert subscription.client_secret_encrypted
        # Verify secret can be decrypted
        assert subscription.client_secret == 'test-secret-key-12345678901234567890'

    def test_create_subscription_missing_required_fields(self, authenticated_api_client):
        """Test creating subscription without required fields."""
        response = authenticated_api_client.post(
            '/api/v1/azure/subscriptions/',
            {'name': 'Incomplete'},
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'subscription_id' in response.data or 'tenant_id' in response.data

    def test_create_subscription_invalid_uuid_format(
        self, authenticated_api_client, azure_subscription_data
    ):
        """Test creating subscription with invalid UUID format."""
        azure_subscription_data['subscription_id'] = 'invalid-uuid'
        response = authenticated_api_client.post(
            '/api/v1/azure/subscriptions/',
            azure_subscription_data,
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_subscription_duplicate_subscription_id(
        self, authenticated_api_client, azure_subscription, azure_subscription_data
    ):
        """Test creating subscription with duplicate subscription_id."""
        # Use same subscription_id as existing subscription
        azure_subscription_data['subscription_id'] = azure_subscription.subscription_id
        response = authenticated_api_client.post(
            '/api/v1/azure/subscriptions/',
            azure_subscription_data,
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_subscription_weak_client_secret(
        self, authenticated_api_client, azure_subscription_data
    ):
        """Test creating subscription with weak client secret."""
        azure_subscription_data['client_secret'] = 'short'
        response = authenticated_api_client.post(
            '/api/v1/azure/subscriptions/',
            azure_subscription_data,
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'client_secret' in response.data

    def test_create_subscription_unauthenticated(self, api_client, azure_subscription_data):
        """Test unauthenticated request is rejected."""
        response = api_client.post(
            '/api/v1/azure/subscriptions/',
            azure_subscription_data,
            format='json'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestAzureSubscriptionViewSetUpdate:
    """Test PUT/PATCH /api/v1/azure/subscriptions/{id}/ - Update subscription."""

    def test_update_subscription_success(self, authenticated_api_client, azure_subscription):
        """Test updating own subscription."""
        update_data = {
            'name': 'Updated Subscription Name',
            'is_active': False,
        }
        response = authenticated_api_client.patch(
            f'/api/v1/azure/subscriptions/{azure_subscription.id}/',
            update_data,
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Subscription Name'
        assert response.data['is_active'] is False

        # Verify in database
        azure_subscription.refresh_from_db()
        assert azure_subscription.name == 'Updated Subscription Name'
        assert azure_subscription.is_active is False

    def test_update_subscription_client_secret(
        self, authenticated_api_client, azure_subscription
    ):
        """Test updating client secret."""
        update_data = {
            'client_secret': 'new-secret-key-12345678901234567890',
        }
        response = authenticated_api_client.patch(
            f'/api/v1/azure/subscriptions/{azure_subscription.id}/',
            update_data,
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        # Verify secret not in response
        assert 'client_secret' not in response.data

        # Verify secret was updated and re-encrypted
        azure_subscription.refresh_from_db()
        assert azure_subscription.client_secret == 'new-secret-key-12345678901234567890'

    def test_update_subscription_not_owner(
        self, authenticated_api_client, other_user_subscription
    ):
        """Test cannot update other user's subscription."""
        update_data = {'name': 'Hacked Name'}
        response = authenticated_api_client.patch(
            f'/api/v1/azure/subscriptions/{other_user_subscription.id}/',
            update_data,
            format='json'
        )
        # Should return 404 because queryset is filtered by owner
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_subscription_invalid_data(
        self, authenticated_api_client, azure_subscription
    ):
        """Test updating with invalid data."""
        update_data = {'tenant_id': 'invalid-uuid'}
        response = authenticated_api_client.patch(
            f'/api/v1/azure/subscriptions/{azure_subscription.id}/',
            update_data,
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestAzureSubscriptionViewSetDestroy:
    """Test DELETE /api/v1/azure/subscriptions/{id}/ - Soft delete subscription."""

    def test_delete_subscription_soft_delete(
        self, authenticated_api_client, azure_subscription
    ):
        """Test deleting subscription performs soft delete."""
        response = authenticated_api_client.delete(
            f'/api/v1/azure/subscriptions/{azure_subscription.id}/'
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify subscription still exists but is inactive
        azure_subscription.refresh_from_db()
        assert azure_subscription.is_active is False

    def test_delete_subscription_not_owner(
        self, authenticated_api_client, other_user_subscription
    ):
        """Test cannot delete other user's subscription."""
        response = authenticated_api_client.delete(
            f'/api/v1/azure/subscriptions/{other_user_subscription.id}/'
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Verify subscription unchanged
        other_user_subscription.refresh_from_db()
        assert other_user_subscription.is_active is True


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestAzureSubscriptionViewSetTestConnection:
    """Test POST /api/v1/azure/subscriptions/{id}/test-connection/ - Test Azure connection."""

    @patch('apps.azure_integration.tasks.test_azure_connection.delay')
    def test_connection_success(
        self, mock_task, authenticated_api_client, azure_subscription
    ):
        """Test successful connection test."""
        # Mock successful task result
        mock_result = MagicMock()
        mock_result.id = 'test-task-id'
        mock_result.get.return_value = {
            'success': True,
            'subscription_id': azure_subscription.subscription_id,
            'subscription_name': 'Production Account',
            'error_message': None,
        }
        mock_task.return_value = mock_result

        response = authenticated_api_client.post(
            f'/api/v1/azure/subscriptions/{azure_subscription.id}/test-connection/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        assert response.data['message'] == 'Connection test completed'
        assert 'task_id' in response.data
        assert 'test_result' in response.data
        assert response.data['test_result']['success'] is True

    @patch('apps.azure_integration.tasks.test_azure_connection.delay')
    def test_connection_failure(
        self, mock_task, authenticated_api_client, azure_subscription
    ):
        """Test failed connection test."""
        # Mock failed task result
        mock_result = MagicMock()
        mock_result.id = 'test-task-id'
        mock_result.get.return_value = {
            'success': False,
            'error_message': 'Invalid credentials',
        }
        mock_task.return_value = mock_result

        response = authenticated_api_client.post(
            f'/api/v1/azure/subscriptions/{azure_subscription.id}/test-connection/'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == 'error'
        assert 'Invalid credentials' in response.data['message']

    def test_connection_not_owner(
        self, authenticated_api_client, other_user_subscription
    ):
        """Test cannot test connection for other user's subscription."""
        response = authenticated_api_client.post(
            f'/api/v1/azure/subscriptions/{other_user_subscription.id}/test-connection/'
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestAzureSubscriptionViewSetStatistics:
    """Test GET /api/v1/azure/subscriptions/{id}/statistics/ - Get Azure statistics."""

    @patch('apps.azure_integration.tasks.sync_azure_statistics.delay')
    def test_statistics_success(
        self, mock_task, authenticated_api_client, azure_subscription
    ):
        """Test successful statistics fetch."""
        # Mock successful task result
        mock_result = MagicMock()
        mock_result.get.return_value = {
            'success': True,
            'total_recommendations': 42,
            'by_category': {
                'Cost': 15,
                'Security': 10,
                'Performance': 8,
                'HighAvailability': 5,
                'OperationalExcellence': 4,
            },
            'by_impact': {
                'High': 12,
                'Medium': 20,
                'Low': 10,
            },
            'total_potential_savings': 15000.50,
            'currency': 'USD',
        }
        mock_task.return_value = mock_result

        response = authenticated_api_client.get(
            f'/api/v1/azure/subscriptions/{azure_subscription.id}/statistics/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        assert 'statistics' in response.data
        assert response.data['statistics']['total_recommendations'] == 42
        assert response.data['statistics']['total_potential_savings'] == 15000.50

    @patch('apps.azure_integration.tasks.sync_azure_statistics.delay')
    def test_statistics_failure(
        self, mock_task, authenticated_api_client, azure_subscription
    ):
        """Test failed statistics fetch."""
        # Mock failed task result
        mock_result = MagicMock()
        mock_result.get.return_value = {
            'success': False,
            'error_message': 'Azure API error',
        }
        mock_task.return_value = mock_result

        response = authenticated_api_client.get(
            f'/api/v1/azure/subscriptions/{azure_subscription.id}/statistics/'
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] == 'error'


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestAzureSubscriptionViewSetSyncNow:
    """Test POST /api/v1/azure/subscriptions/{id}/sync-now/ - Force sync."""

    @patch('apps.azure_integration.tasks.sync_azure_statistics.delay')
    @patch('django.core.cache.cache.delete')
    def test_sync_now_success(
        self, mock_cache_delete, mock_task, authenticated_api_client, azure_subscription
    ):
        """Test force sync clears cache and triggers task."""
        mock_result = MagicMock()
        mock_result.id = 'sync-task-id'
        mock_task.return_value = mock_result

        response = authenticated_api_client.post(
            f'/api/v1/azure/subscriptions/{azure_subscription.id}/sync-now/'
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['status'] == 'success'
        assert response.data['message'] == 'Sync initiated'
        assert 'task_id' in response.data

        # Verify cache was cleared
        mock_cache_delete.assert_called_once()
        # Verify task was triggered
        mock_task.assert_called_once_with(str(azure_subscription.id))


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestAzureSubscriptionViewSetReports:
    """Test GET /api/v1/azure/subscriptions/{id}/reports/ - List subscription reports."""

    def test_list_reports_success(
        self, authenticated_api_client, azure_subscription, test_client
    ):
        """Test listing reports for a subscription."""
        from apps.reports.models import Report

        # Create some reports using this subscription
        report1 = Report.objects.create(
            client=test_client,
            created_by=azure_subscription.created_by,
            report_type='detailed',
            data_source='azure_api',
            azure_subscription=azure_subscription,
            status='completed',
        )
        report2 = Report.objects.create(
            client=test_client,
            created_by=azure_subscription.created_by,
            report_type='cost',
            data_source='azure_api',
            azure_subscription=azure_subscription,
            status='processing',
        )

        response = authenticated_api_client.get(
            f'/api/v1/azure/subscriptions/{azure_subscription.id}/reports/'
        )

        assert response.status_code == status.HTTP_200_OK
        # Check if paginated
        if 'results' in response.data:
            assert len(response.data['results']) == 2
            report_ids = [r['id'] for r in response.data['results']]
        else:
            assert len(response.data) == 2
            report_ids = [r['id'] for r in response.data]

        assert str(report1.id) in report_ids
        assert str(report2.id) in report_ids

    def test_list_reports_empty(self, authenticated_api_client, azure_subscription):
        """Test listing reports when none exist."""
        response = authenticated_api_client.get(
            f'/api/v1/azure/subscriptions/{azure_subscription.id}/reports/'
        )

        assert response.status_code == status.HTTP_200_OK
        if 'results' in response.data:
            assert len(response.data['results']) == 0
        else:
            assert len(response.data) == 0
