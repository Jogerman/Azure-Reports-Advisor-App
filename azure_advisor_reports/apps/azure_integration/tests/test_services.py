"""
Comprehensive tests for Azure Advisor Service.

This module provides extensive test coverage for AzureAdvisorService including:
- Initialization and authentication
- Fetching recommendations with various filters
- Pagination handling
- Data transformation
- Retry logic
- Caching behavior
- Connection testing
- Statistics calculation
- Error handling
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from django.core.cache import cache
from django.test import TestCase

from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ServiceRequestError,
    ResourceNotFoundError,
)

from apps.azure_integration.models import AzureSubscription
from apps.azure_integration.services.azure_advisor_service import AzureAdvisorService
from apps.azure_integration.exceptions import (
    AzureAuthenticationError,
    AzureAPIError,
    AzureConnectionError,
)


class MockRecommendation:
    """Mock Azure Advisor Recommendation object."""

    def __init__(
        self,
        rec_id='rec-001',
        category='Cost',
        impact='High',
        impacted_field='Microsoft.Compute/virtualMachines',
        impacted_value='vm-001',
        short_description=None,
        extended_properties=None,
        resource_metadata=None,
        last_updated=None,
    ):
        self.id = rec_id
        self.category = category
        self.impact = impact
        self.impacted_field = impacted_field
        self.impacted_value = impacted_value
        self.short_description = short_description or {'problem': 'Test recommendation'}
        self.extended_properties = extended_properties or {}
        self.resource_metadata = resource_metadata or {
            'resourceId': f'/subscriptions/sub-123/resourceGroups/rg-test/providers/{impacted_field}/{impacted_value}'
        }
        self.last_updated = last_updated or datetime(2024, 1, 15, 10, 30, 0)
        self.recommendation_type_id = 'test-type-001'
        self.suppression_ids = []


class AzureAdvisorServiceInitializationTests(TestCase):
    """Tests for service initialization and authentication."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = self._create_test_user()
        self.subscription = self._create_test_subscription()

    def _create_test_user(self):
        """Create a test user."""
        from apps.authentication.models import User
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def _create_test_subscription(self):
        """Create a test Azure subscription."""
        subscription = AzureSubscription.objects.create(
            name='Test Subscription',
            subscription_id='12345678-1234-1234-1234-123456789abc',
            tenant_id='87654321-4321-4321-4321-cba987654321',
            client_id='11111111-1111-1111-1111-111111111111',
            created_by=self.user
        )
        subscription.client_secret = 'test-secret-key'
        subscription.save()
        return subscription

    @patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient')
    @patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential')
    def test_initialization_success(self, mock_credential, mock_client):
        """Test successful service initialization."""
        # Arrange
        mock_credential.return_value = Mock()
        mock_client.return_value = Mock()

        # Act
        service = AzureAdvisorService(self.subscription)

        # Assert
        self.assertIsNotNone(service)
        self.assertEqual(service.azure_subscription, self.subscription)
        mock_credential.assert_called_once()
        mock_client.assert_called_once()

    @patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient')
    @patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential')
    def test_initialization_with_authentication_error(self, mock_credential, mock_client):
        """Test initialization with authentication failure."""
        # Arrange
        mock_credential.side_effect = ClientAuthenticationError('Invalid credentials')

        # Act & Assert
        with self.assertRaises(AzureAuthenticationError) as context:
            AzureAdvisorService(self.subscription)

        self.assertIn('Authentication failed', str(context.exception))

    @patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient')
    @patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential')
    def test_initialization_with_generic_error(self, mock_credential, mock_client):
        """Test initialization with generic error."""
        # Arrange
        mock_credential.side_effect = Exception('Network error')

        # Act & Assert
        with self.assertRaises(AzureConnectionError) as context:
            AzureAdvisorService(self.subscription)

        self.assertIn('Failed to initialize', str(context.exception))


class AzureAdvisorServiceFetchTests(TestCase):
    """Tests for fetching recommendations."""

    def setUp(self):
        """Set up test fixtures."""
        cache.clear()
        self.user = self._create_test_user()
        self.subscription = self._create_test_subscription()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def _create_test_user(self):
        """Create a test user."""
        from apps.authentication.models import User
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def _create_test_subscription(self):
        """Create a test Azure subscription."""
        subscription = AzureSubscription.objects.create(
            name='Test Subscription',
            subscription_id='12345678-1234-1234-1234-123456789abc',
            tenant_id='87654321-4321-4321-4321-cba987654321',
            client_id='11111111-1111-1111-1111-111111111111',
            created_by=self.user
        )
        subscription.client_secret = 'test-secret-key'
        subscription.save()
        return subscription

    def _create_mock_service(self):
        """Create a mock AzureAdvisorService."""
        with patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient'), \
             patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential'):
            return AzureAdvisorService(self.subscription)

    def test_fetch_recommendations_no_filters(self):
        """Test fetching recommendations without filters."""
        # Arrange
        service = self._create_mock_service()
        mock_recommendations = [
            MockRecommendation(rec_id='rec-001', category='Cost', impact='High'),
            MockRecommendation(rec_id='rec-002', category='Security', impact='Medium'),
            MockRecommendation(rec_id='rec-003', category='Performance', impact='Low'),
        ]

        with patch.object(service, '_fetch_recommendations_from_api', return_value=mock_recommendations):
            # Act
            results = service.fetch_recommendations()

            # Assert
            self.assertEqual(len(results), 3)
            self.assertEqual(results[0]['id'], 'rec-001')
            self.assertEqual(results[0]['category'], 'Cost')
            self.assertEqual(results[1]['category'], 'Security')

    def test_fetch_recommendations_with_category_filter(self):
        """Test fetching recommendations with category filter."""
        # Arrange
        service = self._create_mock_service()
        mock_recommendations = [
            MockRecommendation(rec_id='rec-001', category='Cost', impact='High'),
            MockRecommendation(rec_id='rec-002', category='Security', impact='Medium'),
            MockRecommendation(rec_id='rec-003', category='Cost', impact='Low'),
        ]

        with patch.object(service, '_fetch_recommendations_from_api', return_value=mock_recommendations):
            # Act
            results = service.fetch_recommendations(filters={'category': 'Cost'})

            # Assert
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]['category'], 'Cost')
            self.assertEqual(results[1]['category'], 'Cost')

    def test_fetch_recommendations_with_impact_filter(self):
        """Test fetching recommendations with impact filter."""
        # Arrange
        service = self._create_mock_service()
        mock_recommendations = [
            MockRecommendation(rec_id='rec-001', category='Cost', impact='High'),
            MockRecommendation(rec_id='rec-002', category='Security', impact='Medium'),
            MockRecommendation(rec_id='rec-003', category='Performance', impact='High'),
        ]

        with patch.object(service, '_fetch_recommendations_from_api', return_value=mock_recommendations):
            # Act
            results = service.fetch_recommendations(filters={'impact': 'High'})

            # Assert
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]['impact'], 'High')
            self.assertEqual(results[1]['impact'], 'High')

    def test_fetch_recommendations_with_multiple_filters(self):
        """Test fetching recommendations with multiple filters."""
        # Arrange
        service = self._create_mock_service()
        mock_recommendations = [
            MockRecommendation(rec_id='rec-001', category='Cost', impact='High'),
            MockRecommendation(rec_id='rec-002', category='Security', impact='High'),
            MockRecommendation(rec_id='rec-003', category='Cost', impact='Low'),
        ]

        with patch.object(service, '_fetch_recommendations_from_api', return_value=mock_recommendations):
            # Act
            results = service.fetch_recommendations(filters={
                'category': 'Cost',
                'impact': 'High'
            })

            # Assert
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['category'], 'Cost')
            self.assertEqual(results[0]['impact'], 'High')

    def test_fetch_recommendations_with_resource_group_filter(self):
        """Test fetching recommendations with resource group filter."""
        # Arrange
        service = self._create_mock_service()
        mock_recommendations = [
            MockRecommendation(
                rec_id='rec-001',
                category='Cost',
                resource_metadata={
                    'resourceId': '/subscriptions/sub-123/resourceGroups/rg-prod/providers/Microsoft.Compute/virtualMachines/vm-001'
                }
            ),
            MockRecommendation(
                rec_id='rec-002',
                category='Security',
                resource_metadata={
                    'resourceId': '/subscriptions/sub-123/resourceGroups/rg-dev/providers/Microsoft.Storage/storageAccounts/storage-001'
                }
            ),
        ]

        with patch.object(service, '_fetch_recommendations_from_api', return_value=mock_recommendations):
            # Act
            results = service.fetch_recommendations(filters={'resource_group': 'rg-prod'})

            # Assert
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['resource_group'], 'rg-prod')

    def test_fetch_recommendations_invalid_category_filter(self):
        """Test fetching recommendations with invalid category filter."""
        # Arrange
        service = self._create_mock_service()

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            service.fetch_recommendations(filters={'category': 'InvalidCategory'})

        self.assertIn('Invalid category', str(context.exception))

    def test_fetch_recommendations_invalid_impact_filter(self):
        """Test fetching recommendations with invalid impact filter."""
        # Arrange
        service = self._create_mock_service()

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            service.fetch_recommendations(filters={'impact': 'Critical'})

        self.assertIn('Invalid impact', str(context.exception))


class AzureAdvisorServiceCachingTests(TestCase):
    """Tests for caching behavior."""

    def setUp(self):
        """Set up test fixtures."""
        cache.clear()
        self.user = self._create_test_user()
        self.subscription = self._create_test_subscription()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def _create_test_user(self):
        """Create a test user."""
        from apps.authentication.models import User
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def _create_test_subscription(self):
        """Create a test Azure subscription."""
        subscription = AzureSubscription.objects.create(
            name='Test Subscription',
            subscription_id='12345678-1234-1234-1234-123456789abc',
            tenant_id='87654321-4321-4321-4321-cba987654321',
            client_id='11111111-1111-1111-1111-111111111111',
            created_by=self.user
        )
        subscription.client_secret = 'test-secret-key'
        subscription.save()
        return subscription

    def _create_mock_service(self):
        """Create a mock AzureAdvisorService."""
        with patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient'), \
             patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential'):
            return AzureAdvisorService(self.subscription)

    def test_caching_first_call_fetches_from_api(self):
        """Test that first call fetches from API."""
        # Arrange
        service = self._create_mock_service()
        mock_recommendations = [MockRecommendation(rec_id='rec-001')]

        with patch.object(service, '_fetch_recommendations_from_api', return_value=mock_recommendations) as mock_fetch:
            # Act
            results = service.fetch_recommendations()

            # Assert
            self.assertEqual(len(results), 1)
            mock_fetch.assert_called_once()

    def test_caching_second_call_uses_cache(self):
        """Test that second call uses cache."""
        # Arrange
        service = self._create_mock_service()
        mock_recommendations = [MockRecommendation(rec_id='rec-001')]

        with patch.object(service, '_fetch_recommendations_from_api', return_value=mock_recommendations) as mock_fetch:
            # Act
            results1 = service.fetch_recommendations()
            results2 = service.fetch_recommendations()

            # Assert
            self.assertEqual(len(results1), 1)
            self.assertEqual(len(results2), 1)
            # Should only call API once
            mock_fetch.assert_called_once()

    def test_caching_different_filters_different_cache(self):
        """Test that different filters create different cache entries."""
        # Arrange
        service = self._create_mock_service()
        mock_recommendations = [
            MockRecommendation(rec_id='rec-001', category='Cost'),
            MockRecommendation(rec_id='rec-002', category='Security'),
        ]

        with patch.object(service, '_fetch_recommendations_from_api', return_value=mock_recommendations) as mock_fetch:
            # Act
            results1 = service.fetch_recommendations(filters={'category': 'Cost'})
            results2 = service.fetch_recommendations(filters={'category': 'Security'})

            # Assert
            self.assertEqual(len(results1), 1)
            self.assertEqual(len(results2), 1)
            # Should call API twice (different cache keys)
            self.assertEqual(mock_fetch.call_count, 2)


class AzureAdvisorServicePaginationTests(TestCase):
    """Tests for pagination handling."""

    def setUp(self):
        """Set up test fixtures."""
        cache.clear()
        self.user = self._create_test_user()
        self.subscription = self._create_test_subscription()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def _create_test_user(self):
        """Create a test user."""
        from apps.authentication.models import User
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def _create_test_subscription(self):
        """Create a test Azure subscription."""
        subscription = AzureSubscription.objects.create(
            name='Test Subscription',
            subscription_id='12345678-1234-1234-1234-123456789abc',
            tenant_id='87654321-4321-4321-4321-cba987654321',
            client_id='11111111-1111-1111-1111-111111111111',
            created_by=self.user
        )
        subscription.client_secret = 'test-secret-key'
        subscription.save()
        return subscription

    def test_pagination_handles_multiple_pages(self):
        """Test that pagination correctly fetches all pages."""
        # Arrange
        with patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient'), \
             patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential'):
            service = AzureAdvisorService(self.subscription)

        # Create mock paged results (simulating multiple pages)
        page1_recs = [
            MockRecommendation(rec_id=f'rec-{i:03d}', category='Cost')
            for i in range(1, 51)  # 50 items
        ]
        page2_recs = [
            MockRecommendation(rec_id=f'rec-{i:03d}', category='Security')
            for i in range(51, 101)  # 50 items
        ]

        all_recommendations = page1_recs + page2_recs
        mock_paged_results = iter(all_recommendations)

        mock_client = Mock()
        mock_client.recommendations.list.return_value = mock_paged_results
        service.client = mock_client

        # Act
        results = service.fetch_recommendations()

        # Assert
        self.assertEqual(len(results), 100)
        self.assertEqual(results[0]['id'], 'rec-001')
        self.assertEqual(results[99]['id'], 'rec-100')

    def test_pagination_handles_empty_results(self):
        """Test that pagination handles empty results correctly."""
        # Arrange
        with patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient'), \
             patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential'):
            service = AzureAdvisorService(self.subscription)

        mock_client = Mock()
        mock_client.recommendations.list.return_value = iter([])
        service.client = mock_client

        # Act
        results = service.fetch_recommendations()

        # Assert
        self.assertEqual(len(results), 0)


class AzureAdvisorServiceDataTransformationTests(TestCase):
    """Tests for data transformation from Azure format to internal format."""

    def setUp(self):
        """Set up test fixtures."""
        cache.clear()
        self.user = self._create_test_user()
        self.subscription = self._create_test_subscription()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def _create_test_user(self):
        """Create a test user."""
        from apps.authentication.models import User
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def _create_test_subscription(self):
        """Create a test Azure subscription."""
        subscription = AzureSubscription.objects.create(
            name='Test Subscription',
            subscription_id='12345678-1234-1234-1234-123456789abc',
            tenant_id='87654321-4321-4321-4321-cba987654321',
            client_id='11111111-1111-1111-1111-111111111111',
            created_by=self.user
        )
        subscription.client_secret = 'test-secret-key'
        subscription.save()
        return subscription

    def _create_mock_service(self):
        """Create a mock AzureAdvisorService."""
        with patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient'), \
             patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential'):
            return AzureAdvisorService(self.subscription)

    def test_transform_recommendation_basic_fields(self):
        """Test basic field transformation."""
        # Arrange
        service = self._create_mock_service()
        mock_rec = MockRecommendation(
            rec_id='rec-001',
            category='Cost',
            impact='High',
            impacted_field='Microsoft.Compute/virtualMachines',
            impacted_value='vm-001'
        )

        # Act
        result = service._transform_recommendation(mock_rec)

        # Assert
        self.assertEqual(result['id'], 'rec-001')
        self.assertEqual(result['category'], 'Cost')
        self.assertEqual(result['impact'], 'High')
        self.assertEqual(result['risk'], 'Error')  # High impact maps to Error
        self.assertEqual(result['resource_type'], 'Microsoft.Compute/virtualMachines')

    def test_transform_recommendation_cost_savings(self):
        """Test cost savings transformation."""
        # Arrange
        service = self._create_mock_service()
        mock_rec = MockRecommendation(
            rec_id='rec-001',
            category='Cost',
            extended_properties={
                'savingsAmount': '150.50',
                'savingsCurrency': 'USD'
            }
        )

        # Act
        result = service._transform_recommendation(mock_rec)

        # Assert
        self.assertEqual(result['potential_savings'], 150.50)
        self.assertEqual(result['currency'], 'USD')

    def test_transform_recommendation_cost_savings_numeric(self):
        """Test cost savings transformation with numeric value."""
        # Arrange
        service = self._create_mock_service()
        mock_rec = MockRecommendation(
            rec_id='rec-001',
            category='Cost',
            extended_properties={
                'savingsAmount': 200.75,
                'savingsCurrency': 'EUR'
            }
        )

        # Act
        result = service._transform_recommendation(mock_rec)

        # Assert
        self.assertEqual(result['potential_savings'], 200.75)
        self.assertEqual(result['currency'], 'EUR')

    def test_transform_recommendation_resource_group_extraction(self):
        """Test resource group extraction from resource ID."""
        # Arrange
        service = self._create_mock_service()
        mock_rec = MockRecommendation(
            rec_id='rec-001',
            resource_metadata={
                'resourceId': '/subscriptions/sub-123/resourceGroups/rg-production/providers/Microsoft.Compute/virtualMachines/vm-001'
            }
        )

        # Act
        result = service._transform_recommendation(mock_rec)

        # Assert
        self.assertEqual(result['resource_group'], 'rg-production')
        self.assertEqual(result['impacted_resource'], 'vm-001')

    def test_transform_recommendation_risk_mapping(self):
        """Test risk level mapping from impact."""
        # Arrange
        service = self._create_mock_service()

        test_cases = [
            ('High', 'Error'),
            ('Medium', 'Warning'),
            ('Low', 'None'),
        ]

        for impact, expected_risk in test_cases:
            mock_rec = MockRecommendation(rec_id='rec-001', impact=impact)

            # Act
            result = service._transform_recommendation(mock_rec)

            # Assert
            self.assertEqual(result['risk'], expected_risk)


class AzureAdvisorServiceRetryLogicTests(TestCase):
    """Tests for retry logic."""

    def setUp(self):
        """Set up test fixtures."""
        cache.clear()
        self.user = self._create_test_user()
        self.subscription = self._create_test_subscription()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def _create_test_user(self):
        """Create a test user."""
        from apps.authentication.models import User
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def _create_test_subscription(self):
        """Create a test Azure subscription."""
        subscription = AzureSubscription.objects.create(
            name='Test Subscription',
            subscription_id='12345678-1234-1234-1234-123456789abc',
            tenant_id='87654321-4321-4321-4321-cba987654321',
            client_id='11111111-1111-1111-1111-111111111111',
            created_by=self.user
        )
        subscription.client_secret = 'test-secret-key'
        subscription.save()
        return subscription

    def test_retry_on_service_request_error_then_success(self):
        """Test retry logic on ServiceRequestError followed by success.

        ServiceRequestError (network errors) should trigger retries.
        This test verifies the retry decorator works correctly.
        """
        # Arrange
        with patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient'), \
             patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential'):
            service = AzureAdvisorService(self.subscription)

        # Track call count at the client level
        call_count = {'count': 0}

        def mock_list_side_effect():
            call_count['count'] += 1
            if call_count['count'] < 2:
                # First call fails with network error (retriable)
                raise ServiceRequestError('Network timeout')
            # Second call succeeds
            return iter([MockRecommendation(rec_id='rec-001')])

        mock_client = Mock()
        mock_client.recommendations.list = Mock(side_effect=mock_list_side_effect)
        service.client = mock_client

        # Act
        results = service.fetch_recommendations()

        # Assert
        self.assertEqual(len(results), 1)
        # Retry decorator should have retried once, so we get 2 calls total
        self.assertEqual(call_count['count'], 2)


class AzureAdvisorServiceConnectionTestTests(TestCase):
    """Tests for connection testing."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = self._create_test_user()
        self.subscription = self._create_test_subscription()

    def _create_test_user(self):
        """Create a test user."""
        from apps.authentication.models import User
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def _create_test_subscription(self):
        """Create a test Azure subscription."""
        subscription = AzureSubscription.objects.create(
            name='Test Subscription',
            subscription_id='12345678-1234-1234-1234-123456789abc',
            tenant_id='87654321-4321-4321-4321-cba987654321',
            client_id='11111111-1111-1111-1111-111111111111',
            created_by=self.user
        )
        subscription.client_secret = 'test-secret-key'
        subscription.save()
        return subscription

    def _create_mock_service(self):
        """Create a mock AzureAdvisorService."""
        with patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient'), \
             patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential'):
            return AzureAdvisorService(self.subscription)

    def test_connection_test_success(self):
        """Test successful connection test."""
        # Arrange
        service = self._create_mock_service()
        mock_client = Mock()
        mock_client.recommendations.list.return_value = iter([MockRecommendation()])
        service.client = mock_client

        # Act
        result = service.test_connection()

        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['subscription_id'], self.subscription.subscription_id)
        self.assertEqual(result['subscription_name'], self.subscription.name)
        self.assertIsNone(result['error_message'])

    def test_connection_test_success_with_empty_results(self):
        """Test successful connection test with empty results."""
        # Arrange
        service = self._create_mock_service()
        mock_client = Mock()
        mock_client.recommendations.list.return_value = iter([])
        service.client = mock_client

        # Act
        result = service.test_connection()

        # Assert
        self.assertTrue(result['success'])

    def test_connection_test_authentication_failure(self):
        """Test connection test with authentication failure."""
        # Arrange
        service = self._create_mock_service()
        mock_client = Mock()
        mock_client.recommendations.list.side_effect = ClientAuthenticationError('Invalid credentials')
        service.client = mock_client

        # Act
        result = service.test_connection()

        # Assert
        self.assertFalse(result['success'])
        self.assertIsNotNone(result['error_message'])
        self.assertIn('Authentication failed', result['error_message'])

    def test_connection_test_api_error(self):
        """Test connection test with API error."""
        # Arrange
        service = self._create_mock_service()
        mock_client = Mock()
        mock_client.recommendations.list.side_effect = HttpResponseError('API error')
        service.client = mock_client

        # Act
        result = service.test_connection()

        # Assert
        self.assertFalse(result['success'])
        self.assertIsNotNone(result['error_message'])
        self.assertIn('API error', result['error_message'])

    def test_connection_test_network_error(self):
        """Test connection test with network error."""
        # Arrange
        service = self._create_mock_service()
        mock_client = Mock()
        mock_client.recommendations.list.side_effect = ServiceRequestError('Network timeout')
        service.client = mock_client

        # Act
        result = service.test_connection()

        # Assert
        self.assertFalse(result['success'])
        self.assertIsNotNone(result['error_message'])
        self.assertIn('Network error', result['error_message'])


class AzureAdvisorServiceStatisticsTests(TestCase):
    """Tests for statistics calculation."""

    def setUp(self):
        """Set up test fixtures."""
        cache.clear()
        self.user = self._create_test_user()
        self.subscription = self._create_test_subscription()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def _create_test_user(self):
        """Create a test user."""
        from apps.authentication.models import User
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def _create_test_subscription(self):
        """Create a test Azure subscription."""
        subscription = AzureSubscription.objects.create(
            name='Test Subscription',
            subscription_id='12345678-1234-1234-1234-123456789abc',
            tenant_id='87654321-4321-4321-4321-cba987654321',
            client_id='11111111-1111-1111-1111-111111111111',
            created_by=self.user
        )
        subscription.client_secret = 'test-secret-key'
        subscription.save()
        return subscription

    def _create_mock_service(self):
        """Create a mock AzureAdvisorService."""
        with patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient'), \
             patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential'):
            return AzureAdvisorService(self.subscription)

    def test_statistics_calculation(self):
        """Test statistics calculation."""
        # Arrange
        service = self._create_mock_service()
        mock_recommendations = [
            MockRecommendation(rec_id='rec-001', category='Cost', impact='High',
                             extended_properties={'savingsAmount': 100.0, 'savingsCurrency': 'USD'}),
            MockRecommendation(rec_id='rec-002', category='Security', impact='High'),
            MockRecommendation(rec_id='rec-003', category='Cost', impact='Medium',
                             extended_properties={'savingsAmount': 50.0, 'savingsCurrency': 'USD'}),
            MockRecommendation(rec_id='rec-004', category='Performance', impact='Low'),
        ]

        with patch.object(service, '_fetch_recommendations_from_api', return_value=mock_recommendations):
            # Act
            stats = service.get_statistics()

            # Assert
            self.assertEqual(stats['total_recommendations'], 4)
            self.assertEqual(stats['by_category']['Cost'], 2)
            self.assertEqual(stats['by_category']['Security'], 1)
            self.assertEqual(stats['by_category']['Performance'], 1)
            self.assertEqual(stats['by_impact']['High'], 2)
            self.assertEqual(stats['by_impact']['Medium'], 1)
            self.assertEqual(stats['by_impact']['Low'], 1)
            self.assertEqual(stats['total_potential_savings'], 150.0)
            self.assertEqual(stats['currency'], 'USD')

    def test_statistics_with_no_savings(self):
        """Test statistics when no cost savings available."""
        # Arrange
        service = self._create_mock_service()
        mock_recommendations = [
            MockRecommendation(rec_id='rec-001', category='Security', impact='High'),
            MockRecommendation(rec_id='rec-002', category='Performance', impact='Medium'),
        ]

        with patch.object(service, '_fetch_recommendations_from_api', return_value=mock_recommendations):
            # Act
            stats = service.get_statistics()

            # Assert
            self.assertEqual(stats['total_recommendations'], 2)
            self.assertIsNone(stats['total_potential_savings'])
            self.assertIsNone(stats['currency'])

    def test_statistics_caching(self):
        """Test that statistics are cached."""
        # Arrange
        service = self._create_mock_service()
        mock_recommendations = [MockRecommendation(rec_id='rec-001')]

        with patch.object(service, '_fetch_recommendations_from_api', return_value=mock_recommendations) as mock_fetch:
            # Act
            stats1 = service.get_statistics()
            stats2 = service.get_statistics()

            # Assert
            self.assertEqual(stats1['total_recommendations'], 1)
            self.assertEqual(stats2['total_recommendations'], 1)
            # Should only call fetch once (second call uses cache)
            mock_fetch.assert_called_once()


class AzureAdvisorServiceErrorHandlingTests(TestCase):
    """Tests for error handling."""

    def setUp(self):
        """Set up test fixtures."""
        cache.clear()
        self.user = self._create_test_user()
        self.subscription = self._create_test_subscription()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def _create_test_user(self):
        """Create a test user."""
        from apps.authentication.models import User
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def _create_test_subscription(self):
        """Create a test Azure subscription."""
        subscription = AzureSubscription.objects.create(
            name='Test Subscription',
            subscription_id='12345678-1234-1234-1234-123456789abc',
            tenant_id='87654321-4321-4321-4321-cba987654321',
            client_id='11111111-1111-1111-1111-111111111111',
            created_by=self.user
        )
        subscription.client_secret = 'test-secret-key'
        subscription.save()
        return subscription

    def test_authentication_error_handling(self):
        """Test authentication error handling."""
        # Arrange
        with patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient'), \
             patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential'):
            service = AzureAdvisorService(self.subscription)

        mock_client = Mock()
        mock_client.recommendations.list.side_effect = ClientAuthenticationError('Invalid credentials')
        service.client = mock_client

        # Act & Assert
        with self.assertRaises(AzureAuthenticationError):
            service.fetch_recommendations()

    def test_api_error_handling(self):
        """Test API error handling."""
        # Arrange
        with patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient'), \
             patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential'):
            service = AzureAdvisorService(self.subscription)

        mock_client = Mock()
        mock_client.recommendations.list.side_effect = HttpResponseError('API error')
        service.client = mock_client

        # Act & Assert
        with self.assertRaises(AzureAPIError):
            service.fetch_recommendations()

    def test_connection_error_handling(self):
        """Test connection error handling."""
        # Arrange
        with patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient'), \
             patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential'):
            service = AzureAdvisorService(self.subscription)

        mock_client = Mock()
        mock_client.recommendations.list.side_effect = ServiceRequestError('Network error')
        service.client = mock_client

        # Act & Assert
        with self.assertRaises(AzureConnectionError):
            service.fetch_recommendations()

    def test_resource_not_found_error_handling(self):
        """Test resource not found error handling."""
        # Arrange
        with patch('apps.azure_integration.services.azure_advisor_service.AdvisorManagementClient'), \
             patch('apps.azure_integration.services.azure_advisor_service.ClientSecretCredential'):
            service = AzureAdvisorService(self.subscription)

        mock_client = Mock()
        mock_client.recommendations.list.side_effect = ResourceNotFoundError('Subscription not found')
        service.client = mock_client

        # Act & Assert
        with self.assertRaises(AzureAPIError):
            service.fetch_recommendations()
