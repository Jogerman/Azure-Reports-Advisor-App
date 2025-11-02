"""
Tests for reports app endpoints.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.clients.models import Client
from .models import Report, Recommendation
import json

User = get_user_model()


class HistoryStatisticsEndpointTests(TestCase):
    """Tests for GET /api/v1/reports/history/statistics/ endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client_api = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Authenticate
        self.client_api.force_authenticate(user=self.user)

        # Create test client
        self.test_client = Client.objects.create(
            company_name='Test Company',
            industry='Technology',
            contact_email='contact@testcompany.com'
        )

        # Create reports with different dates
        self.create_test_reports()

    def create_test_reports(self):
        """Create test reports for various scenarios."""
        now = timezone.now()

        # Reports this month (current)
        for i in range(5):
            Report.objects.create(
                client=self.test_client,
                created_by=self.user,
                report_type='cost',
                status='completed',
                created_at=now - timedelta(days=i)
            )

        # Reports previous month
        for i in range(3):
            Report.objects.create(
                client=self.test_client,
                created_by=self.user,
                report_type='security',
                status='completed',
                created_at=now - timedelta(days=35 + i)
            )

    def test_statistics_no_filters(self):
        """Test statistics endpoint without filters."""
        response = self.client_api.get('/api/v1/reports/history/statistics/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_reports', response.data)
        self.assertIn('reports_this_month', response.data)
        self.assertIn('total_size', response.data)
        self.assertIn('breakdown', response.data)
        self.assertEqual(response.data['total_reports'], 8)
        self.assertEqual(response.data['reports_this_month'], 5)

    def test_statistics_with_date_range(self):
        """Test statistics with date range filter."""
        now = timezone.now()
        date_from = (now - timedelta(days=10)).strftime('%Y-%m-%d')
        date_to = now.strftime('%Y-%m-%d')

        response = self.client_api.get(
            f'/api/v1/reports/history/statistics/?date_from={date_from}&date_to={date_to}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have reports from last 10 days (5 reports)
        self.assertGreater(response.data['total_reports'], 0)

    def test_statistics_with_invalid_date(self):
        """Test statistics with invalid date format."""
        response = self.client_api.get(
            '/api/v1/reports/history/statistics/?date_from=invalid-date'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_statistics_with_report_type_filter(self):
        """Test statistics filtered by report type."""
        response = self.client_api.get(
            '/api/v1/reports/history/statistics/?report_type=cost'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('breakdown', response.data)
        self.assertIn('cost', response.data['breakdown'])

    def test_statistics_breakdown(self):
        """Test that breakdown includes all report types."""
        response = self.client_api.get('/api/v1/reports/history/statistics/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        breakdown = response.data['breakdown']
        self.assertIsInstance(breakdown, dict)
        # Should have cost and security types
        self.assertIn('cost', breakdown)
        self.assertEqual(breakdown['cost'], 5)
        self.assertIn('security', breakdown)
        self.assertEqual(breakdown['security'], 3)

    def test_statistics_unauthenticated(self):
        """Test that unauthenticated requests are rejected."""
        self.client_api.force_authenticate(user=None)
        response = self.client_api.get('/api/v1/reports/history/statistics/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class HistoryTrendsEndpointTests(TestCase):
    """Tests for GET /api/v1/reports/history/trends/ endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client_api = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )

        self.client_api.force_authenticate(user=self.user)

        # Create test client
        self.test_client = Client.objects.create(
            company_name='Test Company',
            industry='Technology',
            contact_email='contact@testcompany.com'
        )

        # Create reports over multiple days
        self.create_trend_reports()

    def create_trend_reports(self):
        """Create reports across multiple days for trend testing."""
        base_date = timezone.now() - timedelta(days=7)

        for day in range(7):
            for i in range(2):  # 2 reports per day
                Report.objects.create(
                    client=self.test_client,
                    created_by=self.user,
                    report_type='cost' if i == 0 else 'security',
                    status='completed',
                    created_at=base_date + timedelta(days=day)
                )

    def test_trends_without_dates(self):
        """Test that trends requires date parameters."""
        response = self.client_api.get('/api/v1/reports/history/trends/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)

    def test_trends_with_valid_dates(self):
        """Test trends with valid date range."""
        date_from = (timezone.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        date_to = timezone.now().strftime('%Y-%m-%d')

        response = self.client_api.get(
            f'/api/v1/reports/history/trends/?date_from={date_from}&date_to={date_to}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIsInstance(response.data['data'], list)
        self.assertGreater(len(response.data['data']), 0)

        # Check data point structure
        if len(response.data['data']) > 0:
            data_point = response.data['data'][0]
            self.assertIn('date', data_point)
            self.assertIn('total', data_point)
            self.assertIn('by_type', data_point)

    def test_trends_with_granularity_day(self):
        """Test trends with daily granularity."""
        date_from = (timezone.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        date_to = timezone.now().strftime('%Y-%m-%d')

        response = self.client_api.get(
            f'/api/v1/reports/history/trends/?date_from={date_from}&date_to={date_to}&granularity=day'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['data']), 0)

    def test_trends_with_granularity_week(self):
        """Test trends with weekly granularity."""
        date_from = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        date_to = timezone.now().strftime('%Y-%m-%d')

        response = self.client_api.get(
            f'/api/v1/reports/history/trends/?date_from={date_from}&date_to={date_to}&granularity=week'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_trends_with_invalid_granularity(self):
        """Test trends with invalid granularity."""
        date_from = (timezone.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        date_to = timezone.now().strftime('%Y-%m-%d')

        response = self.client_api.get(
            f'/api/v1/reports/history/trends/?date_from={date_from}&date_to={date_to}&granularity=invalid'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_trends_with_invalid_date_range(self):
        """Test trends with date_from > date_to."""
        date_from = timezone.now().strftime('%Y-%m-%d')
        date_to = (timezone.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        response = self.client_api.get(
            f'/api/v1/reports/history/trends/?date_from={date_from}&date_to={date_to}'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UsersListEndpointTests(TestCase):
    """Tests for GET /api/v1/reports/users/ endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client_api = APIClient()

        # Create test users
        self.user1 = User.objects.create_user(
            username='user1@example.com',
            email='user1@example.com',
            password='testpass123',
            first_name='User',
            last_name='One'
        )

        self.user2 = User.objects.create_user(
            username='user2@example.com',
            email='user2@example.com',
            password='testpass123',
            first_name='User',
            last_name='Two'
        )

        self.user_no_reports = User.objects.create_user(
            username='user3@example.com',
            email='user3@example.com',
            password='testpass123'
        )

        self.client_api.force_authenticate(user=self.user1)

        # Create test client
        self.test_client = Client.objects.create(
            company_name='Test Company',
            industry='Technology',
            contact_email='contact@testcompany.com'
        )

        # Create reports for users
        for i in range(5):
            Report.objects.create(
                client=self.test_client,
                created_by=self.user1,
                report_type='cost',
                status='completed'
            )

        for i in range(3):
            Report.objects.create(
                client=self.test_client,
                created_by=self.user2,
                report_type='security',
                status='completed'
            )

    def test_users_list(self):
        """Test that users list returns users with reports."""
        response = self.client_api.get('/api/v1/reports/users/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('users', response.data)
        self.assertEqual(len(response.data['users']), 2)  # Only users with reports

    def test_users_list_structure(self):
        """Test that user data has correct structure."""
        response = self.client_api.get('/api/v1/reports/users/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = response.data['users'][0]
        self.assertIn('id', user_data)
        self.assertIn('username', user_data)
        self.assertIn('full_name', user_data)
        self.assertIn('report_count', user_data)

    def test_users_list_ordering(self):
        """Test that users are ordered by report count descending."""
        response = self.client_api.get('/api/v1/reports/users/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        users = response.data['users']
        self.assertEqual(users[0]['report_count'], 5)  # user1 has most reports
        self.assertEqual(users[1]['report_count'], 3)  # user2 has fewer

    def test_users_list_excludes_users_without_reports(self):
        """Test that users without reports are not included."""
        response = self.client_api.get('/api/v1/reports/users/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = [u['username'] for u in response.data['users']]
        self.assertNotIn('user3@example.com', usernames)


class CSVExportEndpointTests(TestCase):
    """Tests for POST /api/v1/reports/export-csv/ endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client_api = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.client_api.force_authenticate(user=self.user)

        # Create test client
        self.test_client = Client.objects.create(
            company_name='Test Company',
            industry='Technology',
            contact_email='contact@testcompany.com'
        )

        # Create test reports
        for i in range(5):
            Report.objects.create(
                client=self.test_client,
                created_by=self.user,
                report_type='cost',
                status='completed',
                title=f'Test Report {i}'
            )

    def test_export_csv_without_filters(self):
        """Test CSV export without filters."""
        response = self.client_api.post(
            '/api/v1/reports/export-csv/',
            data={},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('Content-Disposition', response)
        self.assertIn('reports_export', response['Content-Disposition'])

    def test_export_csv_with_date_range(self):
        """Test CSV export with date range filter."""
        now = timezone.now()
        date_from = (now - timedelta(days=7)).strftime('%Y-%m-%d')
        date_to = now.strftime('%Y-%m-%d')

        response = self.client_api.post(
            '/api/v1/reports/export-csv/',
            data={
                'date_from': date_from,
                'date_to': date_to
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')

    def test_export_csv_with_filters(self):
        """Test CSV export with multiple filters."""
        response = self.client_api.post(
            '/api/v1/reports/export-csv/',
            data={
                'report_type': ['cost'],
                'status': ['completed'],
                'client_id': str(self.test_client.id)
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_export_csv_invalid_date_range(self):
        """Test CSV export with invalid date range."""
        response = self.client_api.post(
            '/api/v1/reports/export-csv/',
            data={
                'date_from': '2025-02-01',
                'date_to': '2025-01-01'  # Earlier than date_from
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_export_csv_content(self):
        """Test that CSV export contains correct headers and data."""
        response = self.client_api.post(
            '/api/v1/reports/export-csv/',
            data={},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decode content
        content = response.content.decode('utf-8')
        lines = content.split('\r\n')

        # Check header
        header = lines[0]
        self.assertIn('ID', header)
        self.assertIn('Title', header)
        self.assertIn('Report Type', header)
        self.assertIn('Client', header)
        self.assertIn('Created By', header)

        # Check that we have data rows
        self.assertGreater(len(lines), 1)


class ReportFilterTests(TestCase):
    """Tests for advanced filtering in reports list endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client_api = APIClient()

        # Create test users
        self.user1 = User.objects.create_user(
            username='user1@example.com',
            email='user1@example.com',
            password='testpass123'
        )

        self.user2 = User.objects.create_user(
            username='user2@example.com',
            email='user2@example.com',
            password='testpass123'
        )

        self.client_api.force_authenticate(user=self.user1)

        # Create test client
        self.test_client = Client.objects.create(
            company_name='Azure Solutions Inc',
            industry='Technology',
            contact_email='contact@azure.com'
        )

        # Create diverse reports
        Report.objects.create(
            client=self.test_client,
            created_by=self.user1,
            report_type='cost',
            status='completed',
            title='Azure Cost Analysis'
        )

        Report.objects.create(
            client=self.test_client,
            created_by=self.user2,
            report_type='security',
            status='failed',
            title='Security Audit'
        )

        Report.objects.create(
            client=self.test_client,
            created_by=self.user1,
            report_type='operations',
            status='completed',
            title='Operations Review'
        )

    def test_filter_by_multiple_report_types(self):
        """Test filtering by multiple report types."""
        response = self.client_api.get(
            '/api/v1/reports/?report_type=cost,security'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_multiple_statuses(self):
        """Test filtering by multiple statuses."""
        response = self.client_api.get(
            '/api/v1/reports/?status=completed,failed'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_filter_by_search(self):
        """Test search filter."""
        response = self.client_api.get(
            '/api/v1/reports/?search=Azure'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['count'], 0)

    def test_filter_by_date_range(self):
        """Test date range filter."""
        now = timezone.now()
        date_from = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        date_to = (now + timedelta(days=1)).strftime('%Y-%m-%d')

        response = self.client_api.get(
            f'/api/v1/reports/?date_from={date_from}&date_to={date_to}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_filter_by_created_by(self):
        """Test filtering by creator."""
        response = self.client_api.get(
            f'/api/v1/reports/?created_by={str(self.user1.id)}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_combined_filters(self):
        """Test combining multiple filters."""
        response = self.client_api.get(
            f'/api/v1/reports/?report_type=cost,operations&status=completed&created_by={str(self.user1.id)}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_ordering_by_created_at(self):
        """Test ordering by created_at."""
        response = self.client_api.get(
            '/api/v1/reports/?ordering=-created_at'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Most recent should be first (operations review)
        self.assertEqual(response.data['results'][0]['title'], 'Operations Review')

    def test_ordering_by_client_name(self):
        """Test ordering by client name."""
        response = self.client_api.get(
            '/api/v1/reports/?ordering=client__company_name'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
