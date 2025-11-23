"""
Comprehensive tests for Report serializers with dual data source support.

Tests cover:
- ReportCreateSerializer with CSV and Azure API data sources
- XOR validation between CSV and Azure API
- Filter validation
- Integration with existing serializers
"""

import io
import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError

from apps.reports.models import Report
from apps.reports.serializers import (
    ReportSerializer,
    ReportListSerializer,
    ReportCreateSerializer,
)
from apps.clients.models import Client
from apps.azure_integration.models import AzureSubscription

User = get_user_model()


class ReportSerializerTestCase(TestCase):
    """Tests for ReportSerializer with dual data source fields."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.client = Client.objects.create(
            company_name='Test Company',
            contact_name='John Doe',
            contact_email='john@testcompany.com'
        )

        self.subscription = AzureSubscription.objects.create(
            name='Test Subscription',
            subscription_id='550e8400-e29b-41d4-a716-446655440000',
            tenant_id='660e8400-e29b-41d4-a716-446655440000',
            client_id='770e8400-e29b-41d4-a716-446655440000',
            created_by=self.user,
        )

    def test_serialization_includes_data_source(self):
        """Test that data_source field is included in serialization."""
        report = Report.objects.create(
            client=self.client,
            created_by=self.user,
            report_type='detailed',
            data_source='csv',
        )

        serializer = ReportSerializer(report)
        data = serializer.data

        self.assertIn('data_source', data)
        self.assertEqual(data['data_source'], 'csv')

    def test_serialization_with_azure_subscription(self):
        """Test serialization includes Azure subscription details."""
        report = Report.objects.create(
            client=self.client,
            created_by=self.user,
            report_type='detailed',
            data_source='azure_api',
            azure_subscription=self.subscription,
        )

        serializer = ReportSerializer(report)
        data = serializer.data

        self.assertIn('azure_subscription', data)
        self.assertIn('azure_subscription_detail', data)
        self.assertIsNotNone(data['azure_subscription_detail'])
        self.assertEqual(data['azure_subscription_detail']['name'], 'Test Subscription')
        self.assertEqual(
            data['azure_subscription_detail']['subscription_id'],
            '550e8400-e29b-41d4-a716-446655440000'
        )

    def test_serialization_includes_api_sync_metadata(self):
        """Test that api_sync_metadata is included."""
        report = Report.objects.create(
            client=self.client,
            created_by=self.user,
            report_type='detailed',
            data_source='azure_api',
            azure_subscription=self.subscription,
            api_sync_metadata={'filters': {'category': 'Cost'}}
        )

        serializer = ReportSerializer(report)
        data = serializer.data

        self.assertIn('api_sync_metadata', data)
        self.assertEqual(data['api_sync_metadata']['filters']['category'], 'Cost')


class ReportListSerializerTestCase(TestCase):
    """Tests for ReportListSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.client = Client.objects.create(
            company_name='Test Company',
            contact_name='John Doe',
            contact_email='john@testcompany.com'
        )

    def test_list_serialization_includes_data_source(self):
        """Test that data_source is included in list view."""
        report = Report.objects.create(
            client=self.client,
            created_by=self.user,
            report_type='detailed',
            data_source='azure_api',
        )

        serializer = ReportListSerializer(report)
        data = serializer.data

        self.assertIn('data_source', data)
        self.assertEqual(data['data_source'], 'azure_api')


class ReportCreateSerializerTestCase(TestCase):
    """Tests for ReportCreateSerializer with dual data source support."""

    def setUp(self):
        """Set up test data and CSV file."""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.client = Client.objects.create(
            company_name='Test Company',
            contact_name='John Doe',
            contact_email='john@testcompany.com'
        )

        self.subscription = AzureSubscription.objects.create(
            name='Test Subscription',
            subscription_id='550e8400-e29b-41d4-a716-446655440000',
            tenant_id='660e8400-e29b-41d4-a716-446655440000',
            client_id='770e8400-e29b-41d4-a716-446655440000',
            is_active=True,
            created_by=self.user,
        )

        # Create valid CSV file
        csv_content = """Category,Recommendation,Impact,Subscription ID,Resource Group,Resource Name
Cost,Resize VM,High,sub-123,rg-prod,vm-prod-01
Security,Enable MFA,High,sub-123,rg-prod,ad-prod"""

        self.csv_file = SimpleUploadedFile(
            'test.csv',
            csv_content.encode('utf-8'),
            content_type='text/csv'
        )

    def test_csv_creation_success(self):
        """Test successful report creation with CSV data source."""
        data = {
            'client_id': str(self.client.id),
            'report_type': 'detailed',
            'data_source': 'csv',
            'csv_file': self.csv_file,
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        report = serializer.save()

        self.assertEqual(report.data_source, 'csv')
        self.assertIsNotNone(report.csv_file)
        self.assertIsNone(report.azure_subscription)
        self.assertEqual(report.status, 'uploaded')

    def test_azure_api_creation_success(self):
        """Test successful report creation with Azure API data source."""
        data = {
            'client_id': str(self.client.id),
            'report_type': 'detailed',
            'data_source': 'azure_api',
            'azure_subscription': str(self.subscription.id),
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        report = serializer.save()

        self.assertEqual(report.data_source, 'azure_api')
        self.assertIsNone(report.csv_file.name if report.csv_file else None)
        self.assertEqual(report.azure_subscription, self.subscription)
        self.assertEqual(report.status, 'pending')

    def test_xor_validation_fails_with_both_sources(self):
        """Test XOR validation fails when both CSV and subscription provided."""
        data = {
            'client_id': str(self.client.id),
            'data_source': 'csv',
            'csv_file': self.csv_file,
            'azure_subscription': str(self.subscription.id),
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('azure_subscription', serializer.errors)

    def test_xor_validation_fails_with_neither_source(self):
        """Test XOR validation fails when neither CSV nor subscription provided."""
        data = {
            'client_id': str(self.client.id),
            'data_source': 'csv',
            # No csv_file or azure_subscription
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('csv_file', serializer.errors)

    def test_csv_creation_without_file_fails(self):
        """Test CSV creation fails without file."""
        data = {
            'client_id': str(self.client.id),
            'data_source': 'csv',
            # Missing csv_file
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('csv_file', serializer.errors)

    def test_azure_api_creation_without_subscription_fails(self):
        """Test Azure API creation fails without subscription."""
        data = {
            'client_id': str(self.client.id),
            'data_source': 'azure_api',
            # Missing azure_subscription
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('azure_subscription', serializer.errors)

    def test_azure_api_creation_with_inactive_subscription_fails(self):
        """Test Azure API creation fails with inactive subscription."""
        # Create inactive subscription
        inactive_sub = AzureSubscription.objects.create(
            name='Inactive Subscription',
            subscription_id='660e8400-e29b-41d4-a716-446655440000',
            tenant_id='770e8400-e29b-41d4-a716-446655440000',
            client_id='880e8400-e29b-41d4-a716-446655440000',
            is_active=False,
            created_by=self.user,
        )

        data = {
            'client_id': str(self.client.id),
            'data_source': 'azure_api',
            'azure_subscription': str(inactive_sub.id),
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('azure_subscription', serializer.errors)

    def test_filters_validation_with_valid_filters(self):
        """Test filters validation with valid filter values."""
        data = {
            'client_id': str(self.client.id),
            'data_source': 'azure_api',
            'azure_subscription': str(self.subscription.id),
            'filters': {
                'category': 'Cost',
                'impact': 'High',
                'resource_group': 'rg-production'
            }
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        report = serializer.save()
        self.assertIn('filters', report.api_sync_metadata)
        self.assertEqual(report.api_sync_metadata['filters']['category'], 'Cost')

    def test_filters_validation_with_invalid_category(self):
        """Test filters validation fails with invalid category."""
        data = {
            'client_id': str(self.client.id),
            'data_source': 'azure_api',
            'azure_subscription': str(self.subscription.id),
            'filters': {
                'category': 'InvalidCategory'
            }
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('filters', serializer.errors)

    def test_filters_validation_with_invalid_impact(self):
        """Test filters validation fails with invalid impact."""
        data = {
            'client_id': str(self.client.id),
            'data_source': 'azure_api',
            'azure_subscription': str(self.subscription.id),
            'filters': {
                'impact': 'Critical'  # Invalid, should be High/Medium/Low
            }
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('filters', serializer.errors)

    def test_filters_validation_with_invalid_keys(self):
        """Test filters validation fails with invalid filter keys."""
        data = {
            'client_id': str(self.client.id),
            'data_source': 'azure_api',
            'azure_subscription': str(self.subscription.id),
            'filters': {
                'invalid_key': 'value',
                'another_invalid': 'value2'
            }
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('filters', serializer.errors)

    def test_api_sync_metadata_set_correctly_with_filters(self):
        """Test api_sync_metadata is set correctly with filters and timestamp."""
        data = {
            'client_id': str(self.client.id),
            'data_source': 'azure_api',
            'azure_subscription': str(self.subscription.id),
            'filters': {
                'category': 'Cost',
                'impact': 'High'
            }
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())

        report = serializer.save()

        self.assertIsNotNone(report.api_sync_metadata)
        self.assertIn('filters', report.api_sync_metadata)
        self.assertIn('requested_at', report.api_sync_metadata)
        self.assertEqual(report.api_sync_metadata['filters']['category'], 'Cost')
        self.assertEqual(report.api_sync_metadata['filters']['impact'], 'High')

    def test_default_data_source_is_csv(self):
        """Test data_source defaults to 'csv' if not specified."""
        data = {
            'client_id': str(self.client.id),
            'csv_file': self.csv_file,
            # data_source not specified
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        report = serializer.save()
        self.assertEqual(report.data_source, 'csv')

    def test_csv_with_filters_fails(self):
        """Test CSV data source cannot have filters."""
        data = {
            'client_id': str(self.client.id),
            'data_source': 'csv',
            'csv_file': self.csv_file,
            'filters': {'category': 'Cost'}
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('filters', serializer.errors)

    def test_invalid_client_id_fails(self):
        """Test creation fails with non-existent client_id."""
        data = {
            'client_id': str(uuid.uuid4()),  # Non-existent client
            'data_source': 'csv',
            'csv_file': self.csv_file,
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('client_id', serializer.errors)

    def test_title_is_optional(self):
        """Test title field is optional."""
        data = {
            'client_id': str(self.client.id),
            'data_source': 'csv',
            'csv_file': self.csv_file,
            # title not provided
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        report = serializer.save()
        self.assertEqual(report.title, '')

    def test_custom_title_is_saved(self):
        """Test custom title is saved correctly."""
        data = {
            'client_id': str(self.client.id),
            'data_source': 'csv',
            'csv_file': self.csv_file,
            'title': 'My Custom Report Title'
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())

        report = serializer.save()
        self.assertEqual(report.title, 'My Custom Report Title')

    def test_report_type_defaults_to_detailed(self):
        """Test report_type defaults to 'detailed'."""
        data = {
            'client_id': str(self.client.id),
            'data_source': 'csv',
            'csv_file': self.csv_file,
            # report_type not specified
        }

        request = self.factory.post('/api/reports/')
        request.user = self.user

        serializer = ReportCreateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())

        report = serializer.save()
        self.assertEqual(report.report_type, 'detailed')

    def test_different_report_types(self):
        """Test different report types can be specified."""
        for report_type, _ in Report.REPORT_TYPES:
            data = {
                'client_id': str(self.client.id),
                'data_source': 'csv',
                'csv_file': self.csv_file,
                'report_type': report_type
            }

            request = self.factory.post('/api/reports/')
            request.user = self.user

            serializer = ReportCreateSerializer(data=data, context={'request': request})
            self.assertTrue(serializer.is_valid(), f"Failed for {report_type}")

            report = serializer.save()
            self.assertEqual(report.report_type, report_type)

            # Clean up for next iteration
            report.delete()

            # Reset CSV file
            csv_content = """Category,Recommendation,Impact,Subscription ID,Resource Group,Resource Name
Cost,Resize VM,High,sub-123,rg-prod,vm-prod-01"""
            self.csv_file = SimpleUploadedFile(
                'test.csv',
                csv_content.encode('utf-8'),
                content_type='text/csv'
            )
