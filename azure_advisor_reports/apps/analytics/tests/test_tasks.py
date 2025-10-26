"""
Tests for Celery tasks in analytics module
"""

from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock

from apps.authentication.models import User
from apps.clients.models import Client
from apps.analytics.models import UserActivity, DashboardMetrics
from apps.analytics.tasks import (
    calculate_daily_metrics,
    cleanup_old_activities,
    calculate_dashboard_metrics_periodic,
    cleanup_old_system_metrics,
)


class CalculateDailyMetricsTaskTestCase(TestCase):
    """Test cases for calculate_daily_metrics task."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )

    @patch('apps.analytics.tasks.AnalyticsService')
    def test_calculate_daily_metrics_success(self, mock_service):
        """Test successful daily metrics calculation."""
        # Mock all service methods
        mock_service.invalidate_cache.return_value = None
        mock_service.get_dashboard_metrics.return_value = {'totalReports': 100}
        mock_service.get_category_distribution.return_value = {'categories': []}
        mock_service.get_trend_data.return_value = {'data': []}
        mock_service.get_recent_activity.return_value = []
        mock_service.get_business_impact_distribution.return_value = {'distribution': []}
        mock_service.get_activity_summary.return_value = {'total_activities': 0}
        mock_service.get_system_health.return_value = {'uptime': '1 day'}

        # Run task
        result = calculate_daily_metrics()

        # Verify result
        self.assertIn('successfully', result)

        # Verify service methods were called
        mock_service.invalidate_cache.assert_called_once()
        mock_service.get_dashboard_metrics.assert_called_once()
        self.assertEqual(mock_service.get_trend_data.call_count, 3)  # For 7, 30, 90 days

    @patch('apps.analytics.tasks.AnalyticsService')
    def test_calculate_daily_metrics_handles_errors(self, mock_service):
        """Test that task handles errors properly."""
        mock_service.invalidate_cache.side_effect = Exception('Cache error')

        # Should raise exception
        with self.assertRaises(Exception):
            calculate_daily_metrics()


class CleanupOldActivitiesTaskTestCase(TestCase):
    """Test cases for cleanup_old_activities task."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )

        # Create activities with different ages
        now = timezone.now()

        # Recent activities (should not be deleted)
        for i in range(5):
            UserActivity.objects.create(
                user=self.user,
                action='generate_report',
                description='Recent activity',
                ip_address='127.0.0.1',
                created_at=now - timedelta(days=i)
            )

        # Old activities (should be deleted)
        for i in range(5):
            UserActivity.objects.create(
                user=self.user,
                action='upload_csv',
                description='Old activity',
                ip_address='127.0.0.1',
                created_at=now - timedelta(days=100 + i)
            )

    def test_cleanup_old_activities_default_days(self):
        """Test cleanup with default 90 days."""
        initial_count = UserActivity.objects.count()
        self.assertEqual(initial_count, 10)

        # Run cleanup task (default 90 days)
        result = cleanup_old_activities()

        # Verify old activities were deleted
        remaining_count = UserActivity.objects.count()
        self.assertEqual(remaining_count, 5)  # Only recent ones remain

        # Verify result message
        self.assertIn('5 activities', result)

    def test_cleanup_old_activities_custom_days(self):
        """Test cleanup with custom days parameter."""
        # Run cleanup with 2 days retention
        result = cleanup_old_activities(days=2)

        # Should delete most activities (keeping only last 2 days)
        remaining_count = UserActivity.objects.count()
        self.assertLessEqual(remaining_count, 3)

    def test_cleanup_old_activities_no_deletion(self):
        """Test cleanup when no old activities exist."""
        # Delete all old activities first
        UserActivity.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=90)
        ).delete()

        # Run cleanup
        result = cleanup_old_activities()

        # Should report 0 deletions
        self.assertIn('0 activities', result)


class CalculateDashboardMetricsPeriodicTaskTestCase(TestCase):
    """Test cases for calculate_dashboard_metrics_periodic task."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )

        self.client = Client.objects.create(
            company_name='Test Company',
            industry='Technology',
            contact_email='test@company.com',
            status='active'
        )

    @patch('apps.analytics.tasks.DashboardMetrics.calculate_for_date')
    def test_calculate_periodic_metrics(self, mock_calculate):
        """Test periodic dashboard metrics calculation."""
        mock_metrics = MagicMock()
        mock_calculate.return_value = mock_metrics

        # Run task
        result = calculate_dashboard_metrics_periodic()

        # Verify result
        self.assertIn('daily', result)
        self.assertIn('weekly', result)
        self.assertIn('monthly', result)

        # Verify calculate_for_date was called for each period
        self.assertEqual(mock_calculate.call_count, 3)

    @patch('apps.analytics.tasks.DashboardMetrics.calculate_for_date')
    def test_calculate_periodic_metrics_handles_errors(self, mock_calculate):
        """Test error handling in periodic metrics calculation."""
        mock_calculate.side_effect = Exception('Calculation error')

        # Should raise exception
        with self.assertRaises(Exception):
            calculate_dashboard_metrics_periodic()


class CleanupOldSystemMetricsTaskTestCase(TestCase):
    """Test cases for cleanup_old_system_metrics task."""

    def setUp(self):
        """Set up test data."""
        from apps.analytics.models import SystemHealthMetrics

        now = timezone.now()

        # Create recent metrics
        for i in range(5):
            SystemHealthMetrics.objects.create(
                recorded_at=now - timedelta(days=i),
                database_connections=10,
                celery_active_tasks=5
            )

        # Create old metrics
        for i in range(5):
            SystemHealthMetrics.objects.create(
                recorded_at=now - timedelta(days=40 + i),
                database_connections=10,
                celery_active_tasks=5
            )

    def test_cleanup_old_system_metrics_default(self):
        """Test cleanup with default 30 days."""
        from apps.analytics.models import SystemHealthMetrics

        initial_count = SystemHealthMetrics.objects.count()
        self.assertEqual(initial_count, 10)

        # Run cleanup
        result = cleanup_old_system_metrics()

        # Verify old metrics were deleted
        remaining_count = SystemHealthMetrics.objects.count()
        self.assertEqual(remaining_count, 5)

        # Verify result message
        self.assertIn('5 system metrics', result)

    def test_cleanup_old_system_metrics_custom_days(self):
        """Test cleanup with custom retention period."""
        from apps.analytics.models import SystemHealthMetrics

        # Run cleanup with 3 days retention
        result = cleanup_old_system_metrics(days=3)

        # Should delete most metrics
        remaining_count = SystemHealthMetrics.objects.count()
        self.assertLessEqual(remaining_count, 4)


class TaskIntegrationTestCase(TestCase):
    """Integration tests for task workflows."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )

        # Create some activities
        now = timezone.now()
        for i in range(10):
            UserActivity.objects.create(
                user=self.user,
                action='generate_report',
                description=f'Activity {i}',
                ip_address='127.0.0.1',
                created_at=now - timedelta(hours=i)
            )

    @patch('apps.analytics.tasks.logger')
    def test_task_logging(self, mock_logger):
        """Test that tasks log appropriately."""
        # Run cleanup task
        cleanup_old_activities(days=90)

        # Verify logging calls were made
        self.assertTrue(mock_logger.info.called)

    def test_multiple_tasks_sequence(self):
        """Test running multiple tasks in sequence."""
        # This simulates a daily task schedule

        # 1. Calculate metrics
        with patch('apps.analytics.tasks.AnalyticsService') as mock_service:
            mock_service.invalidate_cache.return_value = None
            mock_service.get_dashboard_metrics.return_value = {}
            mock_service.get_category_distribution.return_value = {}
            mock_service.get_trend_data.return_value = {}
            mock_service.get_recent_activity.return_value = []
            mock_service.get_business_impact_distribution.return_value = {}
            mock_service.get_activity_summary.return_value = {}
            mock_service.get_system_health.return_value = {}

            result1 = calculate_daily_metrics()
            self.assertIn('successfully', result1)

        # 2. Cleanup old activities
        result2 = cleanup_old_activities(days=90)
        self.assertIsNotNone(result2)

        # Both tasks should complete without errors
        self.assertTrue(True)
