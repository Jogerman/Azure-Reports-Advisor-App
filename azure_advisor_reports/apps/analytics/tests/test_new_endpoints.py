"""
Tests for new analytics endpoints: user-activity, activity-summary, system-health
"""

import uuid
from datetime import datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.authentication.models import User
from apps.clients.models import Client
from apps.reports.models import Report
from apps.analytics.models import UserActivity


class UserActivityEndpointTestCase(TestCase):
    """Test cases for user-activity endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            role='admin',
            is_staff=True
        )

        self.regular_user = User.objects.create_user(
            username='user@test.com',
            email='user@test.com',
            password='testpass123',
            role='analyst'
        )

        # Create test client
        self.test_client = Client.objects.create(
            company_name='Test Company',
            industry='Technology',
            contact_email='test@company.com',
            status='active'
        )

        # Create test activities
        now = timezone.now()
        for i in range(30):
            UserActivity.objects.create(
                user=self.admin_user if i % 2 == 0 else self.regular_user,
                action='generate_report' if i % 3 == 0 else 'upload_csv',
                description=f'Test activity {i}',
                client=self.test_client,
                ip_address='127.0.0.1',
                user_agent='Test Agent',
                metadata={'test': i},
                created_at=now - timedelta(hours=i)
            )

    def test_user_activity_unauthorized(self):
        """Test that unauthenticated users cannot access endpoint."""
        url = reverse('analytics:user-activity')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_activity_basic(self):
        """Test basic user activity retrieval."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:user-activity')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn('activities', data)
        self.assertIn('total_count', data)
        self.assertIn('limit', data)
        self.assertIn('offset', data)
        self.assertEqual(data['total_count'], 30)
        self.assertEqual(len(data['activities']), 25)  # Default limit

    def test_user_activity_with_filters(self):
        """Test user activity with filters."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:user-activity')

        # Filter by user
        response = self.client.get(url, {'user_id': str(self.admin_user.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_count'], 15)  # Half of 30

        # Filter by activity type
        response = self.client.get(url, {'activity_type': 'generate_report'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_count'], 10)  # Every 3rd

    def test_user_activity_pagination(self):
        """Test pagination."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:user-activity')

        # First page
        response = self.client.get(url, {'limit': 10, 'offset': 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['activities']), 10)
        self.assertTrue(data['has_next'])
        self.assertFalse(data['has_previous'])

        # Second page
        response = self.client.get(url, {'limit': 10, 'offset': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['activities']), 10)
        self.assertTrue(data['has_next'])
        self.assertTrue(data['has_previous'])

    def test_user_activity_date_filtering(self):
        """Test date range filtering."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:user-activity')

        # Filter by date range
        date_from = (timezone.now() - timedelta(hours=10)).isoformat()
        date_to = timezone.now().isoformat()

        response = self.client.get(url, {
            'date_from': date_from,
            'date_to': date_to
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertLessEqual(data['total_count'], 11)  # Activities from last 10 hours

    def test_user_activity_regular_user_permission(self):
        """Test that regular users can only see their own activity."""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('analytics:user-activity')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        # Should only see their own activities (15 out of 30)
        self.assertEqual(data['total_count'], 15)

        # Verify all activities belong to regular_user
        for activity in data['activities']:
            self.assertEqual(activity['user']['id'], str(self.regular_user.id))

    def test_user_activity_invalid_date_format(self):
        """Test invalid date format handling."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:user-activity')

        response = self.client.get(url, {'date_from': 'invalid-date'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ActivitySummaryEndpointTestCase(TestCase):
    """Test cases for activity-summary endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        self.admin_user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )

        # Create diverse activities
        now = timezone.now()
        actions = ['generate_report', 'upload_csv', 'download_report', 'create_client']

        for i in range(40):
            UserActivity.objects.create(
                user=self.admin_user,
                action=actions[i % len(actions)],
                description=f'Test activity {i}',
                ip_address='127.0.0.1',
                created_at=now - timedelta(days=i % 7)
            )

    def test_activity_summary_unauthorized(self):
        """Test unauthorized access."""
        url = reverse('analytics:activity-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_activity_summary_by_type(self):
        """Test activity summary grouped by activity type."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:activity-summary')

        response = self.client.get(url, {'group_by': 'activity_type'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn('summary', data)
        self.assertIn('total_activities', data)
        self.assertIn('date_range', data)
        self.assertEqual(data['total_activities'], 40)
        self.assertEqual(len(data['summary']), 4)  # 4 different action types

        # Verify percentages sum to ~100
        total_percentage = sum(item['percentage'] for item in data['summary'])
        self.assertAlmostEqual(total_percentage, 100.0, places=0)

    def test_activity_summary_by_user(self):
        """Test activity summary grouped by user."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:activity-summary')

        response = self.client.get(url, {'group_by': 'user'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn('summary', data)
        self.assertEqual(len(data['summary']), 1)  # Only one user in test data

    def test_activity_summary_by_day(self):
        """Test activity summary grouped by day."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:activity-summary')

        response = self.client.get(url, {'group_by': 'day'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn('summary', data)
        # Should have up to 7 days
        self.assertLessEqual(len(data['summary']), 7)

    def test_activity_summary_invalid_group_by(self):
        """Test invalid group_by parameter."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:activity-summary')

        response = self.client.get(url, {'group_by': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activity_summary_with_date_range(self):
        """Test activity summary with date filtering."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:activity-summary')

        date_from = (timezone.now() - timedelta(days=3)).isoformat()
        date_to = timezone.now().isoformat()

        response = self.client.get(url, {
            'date_from': date_from,
            'date_to': date_to
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        # Should have fewer activities within 3-day range
        self.assertLess(data['total_activities'], 40)


class SystemHealthEndpointTestCase(TestCase):
    """Test cases for system-health endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create users with different roles
        self.admin_user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            role='admin',
            is_staff=True
        )

        self.manager_user = User.objects.create_user(
            username='manager@test.com',
            email='manager@test.com',
            password='testpass123',
            role='manager'
        )

        self.analyst_user = User.objects.create_user(
            username='analyst@test.com',
            email='analyst@test.com',
            password='testpass123',
            role='analyst'
        )

        # Create test client and report
        self.test_client = Client.objects.create(
            company_name='Test Company',
            industry='Technology',
            contact_email='test@company.com',
            status='active'
        )

        # Create some test data for metrics
        now = timezone.now()
        UserActivity.objects.create(
            user=self.admin_user,
            action='generate_report',
            description='Test activity',
            ip_address='127.0.0.1',
            created_at=now
        )

    def test_system_health_unauthorized(self):
        """Test unauthorized access."""
        url = reverse('analytics:system-health')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_system_health_admin_access(self):
        """Test admin can access system health."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:system-health')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        # Verify all expected fields are present
        expected_fields = [
            'database_size',
            'database_size_formatted',
            'total_reports',
            'active_users_today',
            'active_users_this_week',
            'avg_report_generation_time',
            'error_rate',
            'storage_used',
            'storage_used_formatted',
            'uptime',
            'last_calculated'
        ]

        for field in expected_fields:
            self.assertIn(field, data)

    def test_system_health_manager_access(self):
        """Test manager can access system health."""
        self.client.force_authenticate(user=self.manager_user)
        url = reverse('analytics:system-health')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_system_health_analyst_forbidden(self):
        """Test analyst cannot access system health."""
        self.client.force_authenticate(user=self.analyst_user)
        url = reverse('analytics:system-health')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_system_health_metrics_validity(self):
        """Test that returned metrics have valid values."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:system-health')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        # Verify numeric fields are non-negative
        self.assertGreaterEqual(data['database_size'], 0)
        self.assertGreaterEqual(data['total_reports'], 0)
        self.assertGreaterEqual(data['active_users_today'], 0)
        self.assertGreaterEqual(data['active_users_this_week'], 0)
        self.assertGreaterEqual(data['avg_report_generation_time'], 0)
        self.assertGreaterEqual(data['error_rate'], 0)
        self.assertLessEqual(data['error_rate'], 100)  # Percentage

        # Verify formatted strings are not empty
        self.assertIsNotNone(data['database_size_formatted'])
        self.assertIsNotNone(data['uptime'])
