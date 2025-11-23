"""
Comprehensive test suite for Azure Integration Celery tasks.

This module tests all Celery tasks in apps.azure_integration.tasks:
- fetch_azure_recommendations
- generate_azure_report
- test_azure_connection
- sync_azure_statistics
- Helper function: _save_recommendations_to_db

Target coverage: 85%+
"""

import pytest
from unittest.mock import patch, MagicMock, Mock, PropertyMock
from decimal import Decimal
from datetime import datetime, timedelta

from celery.exceptions import Ignore, SoftTimeLimitExceeded, Retry
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.azure_integration.tasks import (
    fetch_azure_recommendations,
    generate_azure_report,
    test_azure_connection,
    sync_azure_statistics,
    _save_recommendations_to_db,
)
from apps.azure_integration.models import AzureSubscription
from apps.azure_integration.exceptions import (
    AzureAuthenticationError,
    AzureAPIError,
    AzureConnectionError,
)
from apps.reports.models import Report, Recommendation
from apps.clients.models import Client

User = get_user_model()


# ============================================================================
# Fixtures
# ============================================================================

# Note: Using fixtures from root conftest.py:
# - test_user (user)
# - test_client_obj (client)


@pytest.fixture
def azure_subscription(db, test_user):
    """Create test Azure subscription."""
    subscription = AzureSubscription(
        name='Test Subscription',
        subscription_id='12345678-1234-1234-1234-123456789012',
        tenant_id='87654321-4321-4321-4321-210987654321',
        client_id='11111111-1111-1111-1111-111111111111',
        created_by=test_user,
        is_active=True,
    )
    # Set encrypted secret
    subscription.client_secret = 'test-secret-key-123'
    subscription.save()
    return subscription


@pytest.fixture
def report_azure_api(db, test_client_obj, azure_subscription, test_user):
    """Create test report for Azure API data source."""
    return Report.objects.create(
        client=test_client_obj,
        created_by=test_user,
        report_type='cost',
        data_source='azure_api',
        azure_subscription=azure_subscription,
        status='pending',
        api_sync_metadata={'filters': {'category': 'Cost'}},
    )


@pytest.fixture
def report_csv(db, test_client_obj, test_user):
    """Create test report for CSV data source."""
    return Report.objects.create(
        client=test_client_obj,
        created_by=test_user,
        report_type='cost',
        data_source='csv',
        status='pending',
    )


@pytest.fixture
def sample_azure_recommendations():
    """Sample recommendations from Azure API."""
    return [
        {
            'id': '/subscriptions/abc/recommendations/rec-1',
            'category': 'Cost',
            'impact': 'High',
            'risk': 'Error',
            'impacted_resource': 'vm-prod-001',
            'resource_type': 'Microsoft.Compute/virtualMachines',
            'resource_group': 'rg-production',
            'recommendation': 'Shutdown unused VM to save costs',
            'description': 'This VM has been idle for 30 days',
            'potential_savings': 1200.50,
            'currency': 'USD',
            'last_updated': '2024-01-15T10:00:00Z',
            'metadata': {
                'recommendation_type_id': 'cost-vm-shutdown',
                'extended_properties': {
                    'subscriptionId': '12345678-1234-1234-1234-123456789012',
                    'subscriptionName': 'Production Subscription',
                },
            },
        },
        {
            'id': '/subscriptions/abc/recommendations/rec-2',
            'category': 'Security',
            'impact': 'Medium',
            'risk': 'Warning',
            'impacted_resource': 'storage-account-1',
            'resource_type': 'Microsoft.Storage/storageAccounts',
            'resource_group': 'rg-production',
            'recommendation': 'Enable HTTPS only access',
            'description': 'Storage account allows HTTP traffic',
            'potential_savings': None,
            'currency': None,
            'last_updated': '2024-01-15T11:00:00Z',
            'metadata': {},
        },
    ]


@pytest.fixture
def mock_azure_service():
    """Mock AzureAdvisorService."""
    with patch('apps.azure_integration.tasks.AzureAdvisorService') as mock:
        service_instance = MagicMock()
        mock.return_value = service_instance
        yield service_instance


# ============================================================================
# Test Helper Function: _save_recommendations_to_db
# ============================================================================

class TestSaveRecommendationsToDb:
    """Test suite for _save_recommendations_to_db helper function."""

    def test_save_recommendations_success(
        self, db, report_azure_api, sample_azure_recommendations
    ):
        """Test successful saving of recommendations to database."""
        # Execute
        count = _save_recommendations_to_db(report_azure_api, sample_azure_recommendations)

        # Assert
        assert count == 2
        assert Recommendation.objects.filter(report=report_azure_api).count() == 2

        # Verify first recommendation
        rec1 = Recommendation.objects.get(resource_name='vm-prod-001')
        assert rec1.category == 'cost'
        assert rec1.business_impact == 'high'
        assert rec1.recommendation == 'Shutdown unused VM to save costs'
        assert rec1.potential_savings == Decimal('1200.50')
        assert rec1.currency == 'USD'
        assert rec1.resource_group == 'rg-production'

        # Verify second recommendation
        rec2 = Recommendation.objects.get(resource_name='storage-account-1')
        assert rec2.category == 'security'
        assert rec2.business_impact == 'medium'
        assert rec2.potential_savings == Decimal('0')

    def test_save_empty_recommendations(self, db, report_azure_api):
        """Test saving empty list of recommendations."""
        count = _save_recommendations_to_db(report_azure_api, [])

        assert count == 0
        assert Recommendation.objects.filter(report=report_azure_api).count() == 0

    def test_save_recommendations_category_mapping(self, db, report_azure_api):
        """Test category mapping from Azure to internal format."""
        recommendations = [
            {
                'category': 'HighAvailability',
                'impact': 'High',
                'impacted_resource': 'test-resource',
                'resource_type': 'test-type',
                'resource_group': 'test-rg',
                'recommendation': 'Test recommendation',
                'description': 'Test description',
                'metadata': {},
            },
        ]

        count = _save_recommendations_to_db(report_azure_api, recommendations)

        assert count == 1
        rec = Recommendation.objects.first()
        assert rec.category == 'reliability'  # Mapped from HighAvailability

    def test_save_recommendations_bulk_create(
        self, db, report_azure_api, sample_azure_recommendations
    ):
        """Test that bulk_create is used for performance."""
        # Create many recommendations
        many_recommendations = sample_azure_recommendations * 50  # 100 total

        with patch('apps.azure_integration.tasks.Recommendation.objects.bulk_create') as mock_bulk:
            mock_bulk.return_value = []
            count = _save_recommendations_to_db(report_azure_api, many_recommendations)

            # Verify bulk_create was called with batch_size
            mock_bulk.assert_called_once()
            call_args = mock_bulk.call_args
            assert call_args[1]['batch_size'] == 1000

    def test_save_recommendations_transaction_rollback(self, db, report_azure_api):
        """Test that transaction rolls back on error."""
        recommendations = [
            {
                'category': 'Cost',
                'impact': 'High',
                'impacted_resource': 'test',
                'resource_type': 'test',
                'resource_group': 'test',
                'recommendation': 'test',
                'description': 'test',
                'metadata': {},
            },
        ]

        # Mock bulk_create to raise an error
        with patch('apps.azure_integration.tasks.Recommendation.objects.bulk_create') as mock_bulk:
            mock_bulk.side_effect = Exception('Database error')

            # Should raise exception
            with pytest.raises(Exception, match='Database error'):
                _save_recommendations_to_db(report_azure_api, recommendations)

        # Verify no recommendations were saved (transaction rolled back)
        assert Recommendation.objects.filter(report=report_azure_api).count() == 0


# ============================================================================
# Test Task: fetch_azure_recommendations
# ============================================================================

class TestFetchAzureRecommendations:
    """Test suite for fetch_azure_recommendations Celery task."""

    def test_successful_fetch(
        self, db, report_azure_api, sample_azure_recommendations, mock_azure_service
    ):
        """Test successful fetch and save of recommendations."""
        # Setup mock
        mock_azure_service.fetch_recommendations.return_value = sample_azure_recommendations

        # Execute task
        result = fetch_azure_recommendations(str(report_azure_api.id))

        # Assert result
        assert result['status'] == 'success'
        assert result['recommendations_count'] == 2
        assert 'fetch_duration_seconds' in result

        # Verify report was updated
        report_azure_api.refresh_from_db()
        assert report_azure_api.status == 'completed'
        assert report_azure_api.api_sync_metadata['recommendations_count'] == 2
        assert 'fetched_at' in report_azure_api.api_sync_metadata

        # Verify recommendations were saved
        assert Recommendation.objects.filter(report=report_azure_api).count() == 2

    def test_fetch_with_filters(
        self, db, report_azure_api, sample_azure_recommendations, mock_azure_service
    ):
        """Test fetch with filters from api_sync_metadata."""
        # Set specific filters
        report_azure_api.api_sync_metadata = {
            'filters': {'category': 'Cost', 'impact': 'High'}
        }
        report_azure_api.save()

        mock_azure_service.fetch_recommendations.return_value = sample_azure_recommendations

        # Execute
        result = fetch_azure_recommendations(str(report_azure_api.id))

        # Verify filters were passed to service
        mock_azure_service.fetch_recommendations.assert_called_once_with(
            filters={'category': 'Cost', 'impact': 'High'}
        )

        assert result['status'] == 'success'

    def test_report_not_found(self, db):
        """Test handling of non-existent report (should Ignore)."""
        fake_id = '12345678-1234-1234-1234-123456789012'

        # Should raise Ignore
        with pytest.raises(Ignore):
            fetch_azure_recommendations(fake_id)

    def test_wrong_data_source(self, db, report_csv):
        """Test handling of report with wrong data source."""
        # report_csv has data_source='csv', not 'azure_api'

        with pytest.raises(Ignore):
            fetch_azure_recommendations(str(report_csv.id))

        # Verify report was marked as failed
        report_csv.refresh_from_db()
        assert report_csv.status == 'failed'
        assert 'not configured for Azure API' in report_csv.error_message

    def test_no_azure_subscription(self, db, test_client_obj, test_user):
        """Test handling of report without Azure subscription."""
        report = Report.objects.create(
            client=test_client_obj,
            created_by=test_user,
            report_type='cost',
            data_source='azure_api',
            status='pending',
        )

        with pytest.raises(Ignore):
            fetch_azure_recommendations(str(report.id))

        # Verify report was marked as failed
        report.refresh_from_db()
        assert report.status == 'failed'
        assert 'no Azure subscription' in report.error_message

    def test_authentication_error(
        self, db, report_azure_api, mock_azure_service
    ):
        """Test handling of Azure authentication errors."""
        # Setup mock to raise authentication error
        mock_azure_service.fetch_recommendations.side_effect = AzureAuthenticationError(
            'Invalid credentials'
        )

        # Should raise Ignore (no retry for auth errors)
        with pytest.raises(Ignore):
            fetch_azure_recommendations(str(report_azure_api.id))

        # Verify report status
        report_azure_api.refresh_from_db()
        assert report_azure_api.status == 'failed'
        assert 'authentication failed' in report_azure_api.error_message.lower()

        # Verify subscription status
        subscription = report_azure_api.azure_subscription
        subscription.refresh_from_db()
        assert subscription.sync_status == 'failed'

    def test_api_error_with_retry(
        self, db, report_azure_api, mock_azure_service
    ):
        """Test API error triggers retry."""
        # Setup mock to raise API error
        mock_azure_service.fetch_recommendations.side_effect = AzureAPIError(
            'Rate limit exceeded'
        )

        # The task will raise Retry exception to trigger retry
        # Celery wraps the original exception in Retry's __cause__
        with pytest.raises((Retry, AzureAPIError)):
            fetch_azure_recommendations(str(report_azure_api.id))

        # Verify report status was updated to failed
        report_azure_api.refresh_from_db()
        assert report_azure_api.status == 'failed'
        assert 'Rate limit exceeded' in report_azure_api.error_message

    def test_connection_error_with_retry(
        self, db, report_azure_api, mock_azure_service
    ):
        """Test connection error triggers retry."""
        mock_azure_service.fetch_recommendations.side_effect = AzureConnectionError(
            'Connection timeout'
        )

        # The task will raise Retry exception
        with pytest.raises((Retry, AzureConnectionError)):
            fetch_azure_recommendations(str(report_azure_api.id))

        # Verify report status was updated to failed
        report_azure_api.refresh_from_db()
        assert report_azure_api.status == 'failed'

    def test_soft_time_limit_exceeded(
        self, db, report_azure_api, mock_azure_service
    ):
        """Test handling of task timeout."""
        # Setup mock to raise timeout
        mock_azure_service.fetch_recommendations.side_effect = SoftTimeLimitExceeded()

        # Should raise Ignore
        with pytest.raises(Ignore):
            fetch_azure_recommendations(str(report_azure_api.id))

        # Verify report status
        report_azure_api.refresh_from_db()
        assert report_azure_api.status == 'failed'
        assert 'timed out' in report_azure_api.error_message.lower()

    def test_database_save_error(
        self, db, report_azure_api, sample_azure_recommendations, mock_azure_service
    ):
        """Test handling of database save errors."""
        mock_azure_service.fetch_recommendations.return_value = sample_azure_recommendations

        # Mock bulk_create to fail
        with patch('apps.azure_integration.tasks.Recommendation.objects.bulk_create') as mock_bulk:
            mock_bulk.side_effect = Exception('Database error')

            with pytest.raises(Ignore):
                fetch_azure_recommendations(str(report_azure_api.id))

            # Verify report marked as failed
            report_azure_api.refresh_from_db()
            assert report_azure_api.status == 'failed'
            assert 'Failed to save recommendations' in report_azure_api.error_message

    def test_metadata_storage(
        self, db, report_azure_api, sample_azure_recommendations, mock_azure_service
    ):
        """Test that sync metadata is properly stored."""
        mock_azure_service.fetch_recommendations.return_value = sample_azure_recommendations

        result = fetch_azure_recommendations(str(report_azure_api.id))

        report_azure_api.refresh_from_db()
        metadata = report_azure_api.api_sync_metadata

        # Verify all required metadata fields
        assert 'filters' in metadata
        assert 'requested_at' in metadata
        assert 'fetched_at' in metadata
        assert metadata['recommendations_count'] == 2
        assert 'fetch_duration_seconds' in metadata
        assert metadata['azure_api_calls'] == 1

    @patch('apps.azure_integration.tasks.generate_azure_report')
    def test_chains_to_report_generation(
        self, mock_generate, db, report_azure_api, sample_azure_recommendations, mock_azure_service
    ):
        """Test that task chains to generate_azure_report on success."""
        mock_azure_service.fetch_recommendations.return_value = sample_azure_recommendations

        result = fetch_azure_recommendations(str(report_azure_api.id))

        # Verify generate_azure_report was called
        mock_generate.delay.assert_called_once_with(
            str(report_azure_api.id), format_type='both'
        )


# ============================================================================
# Test Task: generate_azure_report
# ============================================================================

class TestGenerateAzureReport:
    """Test suite for generate_azure_report Celery task."""

    @pytest.fixture
    def completed_report(self, db, report_azure_api, sample_azure_recommendations):
        """Create a completed report with recommendations."""
        report_azure_api.status = 'completed'
        report_azure_api.save()

        # Add recommendations
        _save_recommendations_to_db(report_azure_api, sample_azure_recommendations)

        return report_azure_api

    def test_successful_pdf_generation(self, db, completed_report):
        """Test successful PDF report generation."""
        # Mock the generator - patch from reports.generators
        with patch('apps.reports.generators.get_generator_for_report') as mock_get_gen:
            mock_generator = MagicMock()
            mock_generator.generate_pdf.return_value = 'reports/pdf/test.pdf'
            mock_get_gen.return_value = mock_generator

            # Execute
            result = generate_azure_report(str(completed_report.id), format_type='pdf')

            # Assert
            assert result['status'] == 'success'
            assert 'PDF' in result['files_generated']
            assert result['file_paths']['pdf'] == 'reports/pdf/test.pdf'

            # Verify generator was called
            mock_generator.generate_pdf.assert_called_once()

    def test_successful_html_generation(self, db, completed_report):
        """Test successful HTML report generation."""
        with patch('apps.reports.generators.get_generator_for_report') as mock_get_gen:
            mock_generator = MagicMock()
            mock_generator.generate_html.return_value = 'reports/html/test.html'
            mock_get_gen.return_value = mock_generator

            result = generate_azure_report(str(completed_report.id), format_type='html')

            assert result['status'] == 'success'
            assert 'HTML' in result['files_generated']
            assert result['file_paths']['html'] == 'reports/html/test.html'

    def test_successful_both_formats(self, db, completed_report):
        """Test generation of both HTML and PDF."""
        with patch('apps.reports.generators.get_generator_for_report') as mock_get_gen:
            mock_generator = MagicMock()
            mock_generator.generate_html.return_value = 'reports/html/test.html'
            mock_generator.generate_pdf.return_value = 'reports/pdf/test.pdf'
            mock_get_gen.return_value = mock_generator

            result = generate_azure_report(str(completed_report.id), format_type='both')

            assert result['status'] == 'success'
            assert 'HTML' in result['files_generated']
            assert 'PDF' in result['files_generated']

    def test_report_not_found(self, db):
        """Test handling of non-existent report."""
        fake_id = '12345678-1234-1234-1234-123456789012'

        with pytest.raises(Ignore):
            generate_azure_report(fake_id)

    def test_report_not_completed(self, db, report_azure_api):
        """Test handling of report that's not completed."""
        report_azure_api.status = 'processing'
        report_azure_api.save()

        result = generate_azure_report(str(report_azure_api.id))

        assert result['status'] == 'error'
        assert 'must be completed' in result['error'].lower()

    def test_no_recommendations(self, db, report_azure_api):
        """Test handling of report with no recommendations."""
        report_azure_api.status = 'completed'
        report_azure_api.save()

        result = generate_azure_report(str(report_azure_api.id))

        assert result['status'] == 'error'
        assert 'no recommendations' in result['error'].lower()

    def test_invalid_format_type(self, db, completed_report):
        """Test handling of invalid format type."""
        result = generate_azure_report(str(completed_report.id), format_type='invalid')

        assert result['status'] == 'error'
        assert 'Invalid format type' in result['error']

    def test_generation_error_with_retry(self, db, completed_report):
        """Test that generation errors trigger retry."""
        with patch('apps.reports.generators.get_generator_for_report') as mock_get_gen:
            mock_generator = MagicMock()
            mock_generator.generate_pdf.side_effect = Exception('PDF generation failed')
            mock_get_gen.return_value = mock_generator

            # The task will raise Retry exception (or the original exception)
            with pytest.raises((Retry, Exception)):
                generate_azure_report(str(completed_report.id), format_type='pdf')

            # Verify report status was set back to completed
            completed_report.refresh_from_db()
            assert completed_report.status == 'completed'


# ============================================================================
# Test Task: test_azure_connection
# ============================================================================

class TestTestAzureConnection:
    """Test suite for test_azure_connection Celery task."""

    def test_successful_connection(self, db, azure_subscription, mock_azure_service):
        """Test successful connection test."""
        # Setup mock
        mock_azure_service.test_connection.return_value = {
            'success': True,
            'subscription_id': azure_subscription.subscription_id,
            'subscription_name': azure_subscription.name,
            'error_message': None,
        }

        # Execute
        result = test_azure_connection(str(azure_subscription.id))

        # Assert
        assert result['success'] is True
        assert result['subscription_id'] == azure_subscription.subscription_id

        # Verify sync status updated
        azure_subscription.refresh_from_db()
        assert azure_subscription.sync_status == 'success'

    def test_failed_connection(self, db, azure_subscription, mock_azure_service):
        """Test failed connection test."""
        mock_azure_service.test_connection.return_value = {
            'success': False,
            'subscription_id': azure_subscription.subscription_id,
            'subscription_name': azure_subscription.name,
            'error_message': 'Connection timeout',
        }

        result = test_azure_connection(str(azure_subscription.id))

        assert result['success'] is False
        assert 'Connection timeout' in result['error_message']

        # Verify sync status updated
        azure_subscription.refresh_from_db()
        assert azure_subscription.sync_status == 'failed'

    def test_subscription_not_found(self, db):
        """Test handling of non-existent subscription."""
        fake_id = '12345678-1234-1234-1234-123456789012'

        with pytest.raises(Ignore):
            test_azure_connection(fake_id)

    def test_authentication_error(self, db, azure_subscription):
        """Test handling of authentication errors."""
        with patch('apps.azure_integration.tasks.AzureAdvisorService') as mock_service:
            mock_service.side_effect = AzureAuthenticationError('Invalid credentials')

            result = test_azure_connection(str(azure_subscription.id))

            assert result['success'] is False
            assert 'Invalid credentials' in result['error_message']

            # Verify sync status
            azure_subscription.refresh_from_db()
            assert azure_subscription.sync_status == 'failed'


# ============================================================================
# Test Task: sync_azure_statistics
# ============================================================================

class TestSyncAzureStatistics:
    """Test suite for sync_azure_statistics Celery task."""

    def test_successful_sync(self, db, azure_subscription, mock_azure_service):
        """Test successful statistics sync."""
        # Setup mock
        mock_stats = {
            'total_recommendations': 10,
            'by_category': {'Cost': 5, 'Security': 3, 'Performance': 2},
            'by_impact': {'High': 4, 'Medium': 3, 'Low': 3},
            'total_potential_savings': 5000.00,
            'currency': 'USD',
        }
        mock_azure_service.get_statistics.return_value = mock_stats

        # Execute
        result = sync_azure_statistics(str(azure_subscription.id))

        # Assert
        assert result['success'] is True
        assert result['total_recommendations'] == 10
        assert result['by_category']['Cost'] == 5
        assert result['total_potential_savings'] == 5000.00

        # Verify sync status
        azure_subscription.refresh_from_db()
        assert azure_subscription.sync_status == 'success'

    def test_subscription_not_found(self, db):
        """Test handling of non-existent subscription."""
        fake_id = '12345678-1234-1234-1234-123456789012'

        with pytest.raises(Ignore):
            sync_azure_statistics(fake_id)

    def test_api_error(self, db, azure_subscription, mock_azure_service):
        """Test handling of API errors."""
        mock_azure_service.get_statistics.side_effect = AzureAPIError('API error')

        result = sync_azure_statistics(str(azure_subscription.id))

        assert result['success'] is False
        assert 'API error' in result['error_message']
        assert result['total_recommendations'] == 0

        # Verify sync status
        azure_subscription.refresh_from_db()
        assert azure_subscription.sync_status == 'failed'

    def test_authentication_error(self, db, azure_subscription, mock_azure_service):
        """Test handling of authentication errors."""
        mock_azure_service.get_statistics.side_effect = AzureAuthenticationError(
            'Auth failed'
        )

        result = sync_azure_statistics(str(azure_subscription.id))

        assert result['success'] is False
        assert 'Auth failed' in result['error_message']
