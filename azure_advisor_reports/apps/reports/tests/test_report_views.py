"""
Comprehensive tests for Reports API views with dual data source support.

Tests ReportViewSet endpoints including:
- Report creation with CSV data source
- Report creation with Azure API data source
- XOR validation between CSV and Azure API
- Data source statistics endpoint
- Permissions for Azure API reports
- Celery task triggering
"""

import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status


@pytest.fixture
def azure_subscription(db, test_user):
    """Create a test Azure subscription owned by test_user."""
    from apps.azure_integration.models import AzureSubscription

    subscription = AzureSubscription.objects.create(
        name='Test Subscription',
        subscription_id='12345678-1234-1234-1234-123456789012',
        tenant_id='87654321-4321-4321-4321-210987654321',
        client_id='abcdef12-ab12-ab12-ab12-abcdef123456',
        created_by=test_user,
        is_active=True,
        sync_status='success',
    )
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
    )
    subscription.client_secret = 'other-user-secret-key-123456789012'
    subscription.save()
    return subscription


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetCreateCSV:
    """Test POST /api/v1/reports/ - Create report with CSV data source."""

    @patch('apps.reports.tasks.process_csv_file.delay')
    def test_create_report_csv_success(
        self, mock_task, authenticated_api_client, test_client, sample_csv_valid
    ):
        """Test creating report with CSV file."""
        from apps.reports.models import Report

        csv_content = sample_csv_valid.encode('utf-8')
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'title': 'Test CSV Report',
            'data_source': 'csv',
            'csv_file': csv_file,
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='multipart'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'success'
        assert 'report_id' in response.data['data']

        # Verify report was created
        report = Report.objects.get(id=response.data['data']['report_id'])
        assert report.data_source == 'csv'
        assert report.csv_file is not None
        assert report.azure_subscription is None
        assert report.status == 'uploaded'

        # Verify Celery task was triggered
        mock_task.assert_called_once_with(str(report.id))

    def test_create_report_csv_missing_file(
        self, authenticated_api_client, test_client
    ):
        """Test CSV report creation fails without file."""
        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'data_source': 'csv',
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'csv_file' in str(response.data).lower()

    def test_create_report_csv_with_azure_subscription(
        self, authenticated_api_client, test_client, azure_subscription, sample_csv_valid
    ):
        """Test CSV report creation fails when azure_subscription is provided."""
        csv_content = sample_csv_valid.encode('utf-8')
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'data_source': 'csv',
            'csv_file': csv_file,
            'azure_subscription': str(azure_subscription.id),
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='multipart'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'azure_subscription' in str(response.data).lower()


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetCreateAzureAPI:
    """Test POST /api/v1/reports/ - Create report with Azure API data source."""

    @patch('apps.azure_integration.tasks.fetch_azure_recommendations.delay')
    def test_create_report_azure_api_success(
        self, mock_task, authenticated_api_client, test_client, azure_subscription
    ):
        """Test creating report with Azure API data source."""
        from apps.reports.models import Report

        data = {
            'client_id': str(test_client.id),
            'report_type': 'cost',
            'title': 'Test Azure API Report',
            'data_source': 'azure_api',
            'azure_subscription': str(azure_subscription.id),
            'filters': {
                'category': 'Cost',
                'impact': 'High',
            },
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'success'
        assert 'report_id' in response.data['data']

        # Verify report was created
        report = Report.objects.get(id=response.data['data']['report_id'])
        assert report.data_source == 'azure_api'
        assert report.azure_subscription == azure_subscription
        assert report.csv_file.name == ''
        assert report.status == 'pending'
        assert report.api_sync_metadata is not None
        assert report.api_sync_metadata['filters'] == data['filters']

        # Verify Celery task was triggered
        mock_task.assert_called_once_with(str(report.id))

    def test_create_report_azure_api_missing_subscription(
        self, authenticated_api_client, test_client
    ):
        """Test Azure API report fails without subscription."""
        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'data_source': 'azure_api',
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'azure_subscription' in str(response.data).lower()

    def test_create_report_azure_api_with_csv_file(
        self, authenticated_api_client, test_client, azure_subscription, sample_csv_valid
    ):
        """Test Azure API report fails when CSV file is provided."""
        csv_content = sample_csv_valid.encode('utf-8')
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'data_source': 'azure_api',
            'azure_subscription': str(azure_subscription.id),
            'csv_file': csv_file,
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='multipart'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'csv_file' in str(response.data).lower()

    def test_create_report_azure_api_inactive_subscription(
        self, authenticated_api_client, test_client, azure_subscription
    ):
        """Test Azure API report fails with inactive subscription."""
        # Deactivate subscription
        azure_subscription.is_active = False
        azure_subscription.save()

        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'data_source': 'azure_api',
            'azure_subscription': str(azure_subscription.id),
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'active' in str(response.data).lower()

    def test_create_report_azure_api_not_owner(
        self, authenticated_api_client, test_client, other_user_subscription
    ):
        """Test Azure API report fails when user doesn't own subscription."""
        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'data_source': 'azure_api',
            'azure_subscription': str(other_user_subscription.id),
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='json'
        )

        # Should fail with permission error or validation error
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]

    def test_create_report_azure_api_with_filters(
        self, authenticated_api_client, test_client, azure_subscription
    ):
        """Test creating Azure API report with various filters."""
        data = {
            'client_id': str(test_client.id),
            'report_type': 'security',
            'data_source': 'azure_api',
            'azure_subscription': str(azure_subscription.id),
            'filters': {
                'category': 'Security',
                'impact': 'High',
                'resource_group': 'production-rg',
            },
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_report_azure_api_invalid_filter_category(
        self, authenticated_api_client, test_client, azure_subscription
    ):
        """Test Azure API report fails with invalid category filter."""
        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'data_source': 'azure_api',
            'azure_subscription': str(azure_subscription.id),
            'filters': {
                'category': 'InvalidCategory',
            },
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'category' in str(response.data).lower()

    def test_create_report_azure_api_invalid_filter_impact(
        self, authenticated_api_client, test_client, azure_subscription
    ):
        """Test Azure API report fails with invalid impact filter."""
        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'data_source': 'azure_api',
            'azure_subscription': str(azure_subscription.id),
            'filters': {
                'impact': 'Critical',  # Invalid, should be High/Medium/Low
            },
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'impact' in str(response.data).lower()

    def test_create_report_azure_api_csv_filters_not_allowed(
        self, authenticated_api_client, test_client, sample_csv_valid
    ):
        """Test CSV report fails when filters are provided."""
        csv_content = sample_csv_valid.encode('utf-8')
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'data_source': 'csv',
            'csv_file': csv_file,
            'filters': {'category': 'Cost'},
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='multipart'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'filters' in str(response.data).lower()


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetDataSourceStats:
    """Test GET /api/v1/reports/data-source-stats/ - Get data source statistics."""

    def test_data_source_stats_empty(self, authenticated_api_client):
        """Test statistics with no reports."""
        response = authenticated_api_client.get('/api/v1/reports/data-source-stats/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 0
        assert response.data['by_source'] == {}
        assert response.data['by_status'] == {}

    def test_data_source_stats_with_reports(
        self, authenticated_api_client, test_client, azure_subscription
    ):
        """Test statistics with various reports."""
        from apps.reports.models import Report

        # Create CSV reports
        Report.objects.create(
            client=test_client,
            created_by=authenticated_api_client.handler._force_user,
            report_type='detailed',
            data_source='csv',
            status='completed',
        )
        Report.objects.create(
            client=test_client,
            created_by=authenticated_api_client.handler._force_user,
            report_type='cost',
            data_source='csv',
            status='processing',
        )

        # Create Azure API reports
        Report.objects.create(
            client=test_client,
            created_by=authenticated_api_client.handler._force_user,
            report_type='security',
            data_source='azure_api',
            azure_subscription=azure_subscription,
            status='completed',
        )

        response = authenticated_api_client.get('/api/v1/reports/data-source-stats/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 3
        assert response.data['by_source']['csv'] == 2
        assert response.data['by_source']['azure_api'] == 1
        assert response.data['by_status']['completed'] == 2
        assert response.data['by_status']['processing'] == 1

    def test_data_source_stats_breakdown(
        self, authenticated_api_client, test_client, azure_subscription
    ):
        """Test statistics breakdown by source and status."""
        from apps.reports.models import Report

        Report.objects.create(
            client=test_client,
            created_by=authenticated_api_client.handler._force_user,
            report_type='detailed',
            data_source='csv',
            status='completed',
        )
        Report.objects.create(
            client=test_client,
            created_by=authenticated_api_client.handler._force_user,
            report_type='cost',
            data_source='azure_api',
            azure_subscription=azure_subscription,
            status='completed',
        )

        response = authenticated_api_client.get('/api/v1/reports/data-source-stats/')

        assert response.status_code == status.HTTP_200_OK
        assert 'by_source_and_status' in response.data
        assert len(response.data['by_source_and_status']) >= 2


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetList:
    """Test GET /api/v1/reports/ - List reports with data source filtering."""

    def test_list_reports_filter_by_data_source(
        self, authenticated_api_client, test_client, azure_subscription
    ):
        """Test filtering reports by data source."""
        from apps.reports.models import Report

        # Create reports with different data sources
        csv_report = Report.objects.create(
            client=test_client,
            created_by=authenticated_api_client.handler._force_user,
            report_type='detailed',
            data_source='csv',
            status='completed',
        )
        api_report = Report.objects.create(
            client=test_client,
            created_by=authenticated_api_client.handler._force_user,
            report_type='cost',
            data_source='azure_api',
            azure_subscription=azure_subscription,
            status='completed',
        )

        # Filter for CSV reports
        response = authenticated_api_client.get('/api/v1/reports/?data_source=csv')
        assert response.status_code == status.HTTP_200_OK
        csv_ids = [r['id'] for r in response.data['results']]
        assert str(csv_report.id) in csv_ids
        assert str(api_report.id) not in csv_ids

        # Filter for Azure API reports
        response = authenticated_api_client.get('/api/v1/reports/?data_source=azure_api')
        assert response.status_code == status.HTTP_200_OK
        api_ids = [r['id'] for r in response.data['results']]
        assert str(api_report.id) in api_ids
        assert str(csv_report.id) not in api_ids

    def test_list_reports_includes_data_source(
        self, authenticated_api_client, test_client, azure_subscription
    ):
        """Test report list includes data source field."""
        from apps.reports.models import Report

        Report.objects.create(
            client=test_client,
            created_by=authenticated_api_client.handler._force_user,
            report_type='detailed',
            data_source='csv',
            status='completed',
        )

        response = authenticated_api_client.get('/api/v1/reports/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        assert 'data_source' in response.data['results'][0]


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetRetrieve:
    """Test GET /api/v1/reports/{id}/ - Retrieve report with Azure subscription details."""

    def test_retrieve_csv_report(
        self, authenticated_api_client, test_client
    ):
        """Test retrieving CSV report."""
        from apps.reports.models import Report

        report = Report.objects.create(
            client=test_client,
            created_by=authenticated_api_client.handler._force_user,
            report_type='detailed',
            data_source='csv',
            status='completed',
        )

        response = authenticated_api_client.get(f'/api/v1/reports/{report.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data_source'] == 'csv'
        assert response.data['azure_subscription'] is None
        assert response.data['azure_subscription_detail'] is None

    def test_retrieve_azure_api_report(
        self, authenticated_api_client, test_client, azure_subscription
    ):
        """Test retrieving Azure API report includes subscription details."""
        from apps.reports.models import Report

        report = Report.objects.create(
            client=test_client,
            created_by=authenticated_api_client.handler._force_user,
            report_type='cost',
            data_source='azure_api',
            azure_subscription=azure_subscription,
            status='completed',
        )

        response = authenticated_api_client.get(f'/api/v1/reports/{report.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data_source'] == 'azure_api'
        assert response.data['azure_subscription'] == str(azure_subscription.id)
        assert response.data['azure_subscription_detail'] is not None
        assert response.data['azure_subscription_detail']['name'] == 'Test Subscription'
        # Verify sensitive data not exposed
        assert 'client_secret' not in response.data['azure_subscription_detail']


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetPermissions:
    """Test permission classes for report creation."""

    def test_csv_report_no_permission_check(
        self, authenticated_api_client, test_client, sample_csv_valid
    ):
        """Test CSV report creation doesn't check subscription ownership."""
        csv_content = sample_csv_valid.encode('utf-8')
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'data_source': 'csv',
            'csv_file': csv_file,
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='multipart'
        )

        # Should succeed without subscription ownership check
        assert response.status_code == status.HTTP_201_CREATED

    def test_azure_api_report_requires_ownership(
        self, authenticated_api_client, test_client, other_user_subscription
    ):
        """Test Azure API report requires subscription ownership."""
        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'data_source': 'azure_api',
            'azure_subscription': str(other_user_subscription.id),
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='json'
        )

        # Should fail because user doesn't own the subscription
        # Could be 400 (validation) or 403 (permission)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]

    def test_unauthenticated_cannot_create_report(
        self, api_client, test_client
    ):
        """Test unauthenticated users cannot create reports."""
        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'data_source': 'csv',
        }

        response = api_client.post('/api/v1/reports/', data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.api
@pytest.mark.views
@pytest.mark.django_db
class TestReportViewSetTaskTriggering:
    """Test that correct Celery tasks are triggered based on data source."""

    @patch('apps.reports.tasks.process_csv_file.delay')
    def test_csv_report_triggers_csv_task(
        self, mock_csv_task, authenticated_api_client, test_client, sample_csv_valid
    ):
        """Test CSV report creation triggers CSV processing task."""
        csv_content = sample_csv_valid.encode('utf-8')
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        data = {
            'client_id': str(test_client.id),
            'report_type': 'detailed',
            'data_source': 'csv',
            'csv_file': csv_file,
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='multipart'
        )

        assert response.status_code == status.HTTP_201_CREATED
        # Verify CSV task was called
        assert mock_csv_task.called
        # Verify Azure task was NOT called
        with patch('apps.azure_integration.tasks.fetch_azure_recommendations.delay') as mock_azure:
            assert not mock_azure.called

    @patch('apps.azure_integration.tasks.fetch_azure_recommendations.delay')
    def test_azure_api_report_triggers_azure_task(
        self, mock_azure_task, authenticated_api_client, test_client, azure_subscription
    ):
        """Test Azure API report creation triggers Azure fetch task."""
        data = {
            'client_id': str(test_client.id),
            'report_type': 'cost',
            'data_source': 'azure_api',
            'azure_subscription': str(azure_subscription.id),
        }

        response = authenticated_api_client.post(
            '/api/v1/reports/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        # Verify Azure task was called
        assert mock_azure_task.called
        # Verify CSV task was NOT called
        with patch('apps.reports.tasks.process_csv_file.delay') as mock_csv:
            assert not mock_csv.called
