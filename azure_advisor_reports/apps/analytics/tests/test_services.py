"""
Unit tests for analytics services.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model

from apps.clients.models import Client
from apps.reports.models import Report, Recommendation
from apps.analytics.services import AnalyticsService

User = get_user_model()


class AnalyticsServiceTestCase(TestCase):
    """Test cases for AnalyticsService."""

    def setUp(self):
        """Set up test data."""
        # Clear cache before each test
        cache.clear()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )

        # Create test clients
        self.client1 = Client.objects.create(
            company_name='Test Client 1',
            status='active',
            contact_email='client1@example.com'
        )

        self.client2 = Client.objects.create(
            company_name='Test Client 2',
            status='active',
            contact_email='client2@example.com'
        )

        self.client3 = Client.objects.create(
            company_name='Inactive Client',
            status='inactive',
            contact_email='client3@example.com'
        )

        # Create test reports
        self.report1 = Report.objects.create(
            client=self.client1,
            created_by=self.user,
            report_type='detailed',
            status='completed',
            processing_started_at=timezone.now() - timedelta(minutes=10),
            processing_completed_at=timezone.now() - timedelta(minutes=5)
        )

        self.report2 = Report.objects.create(
            client=self.client2,
            created_by=self.user,
            report_type='executive',
            status='completed',
            processing_started_at=timezone.now() - timedelta(minutes=8),
            processing_completed_at=timezone.now() - timedelta(minutes=3)
        )

        self.report3 = Report.objects.create(
            client=self.client1,
            created_by=self.user,
            report_type='cost',
            status='pending'
        )

        # Create test recommendations
        self.recommendation1 = Recommendation.objects.create(
            report=self.report1,
            category='cost',
            business_impact='High',
            recommendation='Reduce VM size',
            potential_savings=Decimal('500.00')
        )

        self.recommendation2 = Recommendation.objects.create(
            report=self.report1,
            category='security',
            business_impact='High',
            recommendation='Enable MFA',
            potential_savings=Decimal('0.00')
        )

        self.recommendation3 = Recommendation.objects.create(
            report=self.report2,
            category='cost',
            business_impact='Medium',
            recommendation='Use reserved instances',
            potential_savings=Decimal('1500.00')
        )

        self.recommendation4 = Recommendation.objects.create(
            report=self.report2,
            category='reliability',
            business_impact='High',
            recommendation='Enable backup',
            potential_savings=Decimal('0.00')
        )

    def test_get_dashboard_metrics(self):
        """Test getting dashboard metrics."""
        metrics = AnalyticsService.get_dashboard_metrics()

        # Check structure
        self.assertIn('totalRecommendations', metrics)
        self.assertIn('totalPotentialSavings', metrics)
        self.assertIn('activeClients', metrics)
        self.assertIn('reportsGeneratedThisMonth', metrics)
        self.assertIn('trends', metrics)

        # Check values
        self.assertEqual(metrics['totalRecommendations'], 4)
        self.assertEqual(metrics['totalPotentialSavings'], 2000.0)
        self.assertEqual(metrics['activeClients'], 2)  # Only active clients
        self.assertEqual(metrics['reportsGeneratedThisMonth'], 3)

        # Check trends structure
        self.assertIn('recommendations', metrics['trends'])
        self.assertIn('savings', metrics['trends'])
        self.assertIn('clients', metrics['trends'])
        self.assertIn('reports', metrics['trends'])

    def test_dashboard_metrics_caching(self):
        """Test that dashboard metrics are cached."""
        # First call - should hit database
        metrics1 = AnalyticsService.get_dashboard_metrics()

        # Create new data
        Recommendation.objects.create(
            report=self.report1,
            category='performance',
            business_impact='Low',
            recommendation='Test',
            potential_savings=Decimal('100.00')
        )

        # Second call - should return cached data (not include new recommendation)
        metrics2 = AnalyticsService.get_dashboard_metrics()
        self.assertEqual(metrics1['totalRecommendations'], metrics2['totalRecommendations'])

        # Clear cache and try again
        cache.clear()
        metrics3 = AnalyticsService.get_dashboard_metrics()
        self.assertEqual(metrics3['totalRecommendations'], 5)  # Now includes new recommendation

    def test_calculate_percentage_change(self):
        """Test percentage change calculation."""
        # Test increase
        change = AnalyticsService._calculate_percentage_change(150, 100)
        self.assertEqual(change, 50.0)

        # Test decrease
        change = AnalyticsService._calculate_percentage_change(75, 100)
        self.assertEqual(change, -25.0)

        # Test zero previous value
        change = AnalyticsService._calculate_percentage_change(100, 0)
        self.assertEqual(change, 100.0)

        # Test both zero
        change = AnalyticsService._calculate_percentage_change(0, 0)
        self.assertEqual(change, 0.0)

    def test_get_category_distribution(self):
        """Test getting category distribution."""
        distribution = AnalyticsService.get_category_distribution()

        # Check structure
        self.assertIn('categories', distribution)
        self.assertIn('total', distribution)

        # Check total
        self.assertEqual(distribution['total'], 4)

        # Check categories
        categories = distribution['categories']
        self.assertTrue(len(categories) > 0)

        # Find cost category
        cost_category = next((c for c in categories if c['name'] == 'Cost'), None)
        self.assertIsNotNone(cost_category)
        self.assertEqual(cost_category['value'], 2)
        self.assertEqual(cost_category['percentage'], 50.0)

        # Check category structure
        for category in categories:
            self.assertIn('name', category)
            self.assertIn('value', category)
            self.assertIn('percentage', category)
            self.assertIn('color', category)

    def test_get_trend_data_30_days(self):
        """Test getting 30-day trend data."""
        trend_data = AnalyticsService.get_trend_data(days=30)

        # Check structure
        self.assertIn('data', trend_data)
        self.assertIn('summary', trend_data)

        # Check data points
        data = trend_data['data']
        self.assertEqual(len(data), 31)  # 30 days + today

        # Check data point structure
        for point in data:
            self.assertIn('date', point)
            self.assertIn('value', point)
            self.assertIn('label', point)

        # Check summary
        summary = trend_data['summary']
        self.assertIn('total', summary)
        self.assertIn('average', summary)
        self.assertIn('peak', summary)

        # Today should have 3 reports
        today_data = data[-1]
        self.assertEqual(today_data['value'], 3)

    def test_get_trend_data_7_days(self):
        """Test getting 7-day trend data."""
        trend_data = AnalyticsService.get_trend_data(days=7)

        data = trend_data['data']
        self.assertEqual(len(data), 8)  # 7 days + today

    def test_get_trend_data_90_days(self):
        """Test getting 90-day trend data."""
        trend_data = AnalyticsService.get_trend_data(days=90)

        data = trend_data['data']
        self.assertEqual(len(data), 91)  # 90 days + today

    def test_get_recent_activity(self):
        """Test getting recent activity."""
        activity = AnalyticsService.get_recent_activity(limit=10)

        # Check we got activities
        self.assertEqual(len(activity), 3)  # We have 3 reports

        # Check activity structure
        for item in activity:
            self.assertIn('id', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('description', item)
            self.assertIn('timestamp', item)
            self.assertIn('clientName', item)
            self.assertIn('reportType', item)
            self.assertIn('reportId', item)
            self.assertIn('status', item)

        # Check first activity (most recent)
        first_activity = activity[0]
        self.assertEqual(first_activity['status'], 'pending')

    def test_get_recent_activity_limit(self):
        """Test activity limit parameter."""
        activity = AnalyticsService.get_recent_activity(limit=2)
        self.assertEqual(len(activity), 2)

    def test_get_client_performance_specific_client(self):
        """Test getting performance for a specific client."""
        performance = AnalyticsService.get_client_performance(client_id=str(self.client1.id))

        # Check structure
        self.assertIn('totalReports', performance)
        self.assertIn('completedReports', performance)
        self.assertIn('failedReports', performance)
        self.assertIn('successRate', performance)
        self.assertIn('avgProcessingTimeSeconds', performance)
        self.assertIn('totalRecommendations', performance)
        self.assertIn('totalPotentialSavings', performance)
        self.assertIn('categoryBreakdown', performance)

        # Check values for client1 (2 reports, 2 recommendations)
        self.assertEqual(performance['totalReports'], 2)
        self.assertEqual(performance['completedReports'], 1)
        self.assertEqual(performance['totalRecommendations'], 2)
        self.assertEqual(performance['totalPotentialSavings'], 500.0)

    def test_get_client_performance_all_clients(self):
        """Test getting performance for all clients."""
        performance = AnalyticsService.get_client_performance(client_id=None)

        # Check values for all clients (3 reports, 4 recommendations)
        self.assertEqual(performance['totalReports'], 3)
        self.assertEqual(performance['completedReports'], 2)
        self.assertEqual(performance['totalRecommendations'], 4)
        self.assertEqual(performance['totalPotentialSavings'], 2000.0)

    def test_get_business_impact_distribution(self):
        """Test getting business impact distribution."""
        distribution = AnalyticsService.get_business_impact_distribution()

        # Check structure
        self.assertIn('distribution', distribution)
        self.assertIn('total', distribution)

        # Check total
        self.assertEqual(distribution['total'], 4)

        # Check distribution items
        for item in distribution['distribution']:
            self.assertIn('impact', item)
            self.assertIn('count', item)
            self.assertIn('percentage', item)

        # Find High impact
        high_impact = next((i for i in distribution['distribution'] if i['impact'] == 'High'), None)
        self.assertIsNotNone(high_impact)
        self.assertEqual(high_impact['count'], 3)

    def test_invalidate_cache(self):
        """Test cache invalidation."""
        # Populate cache
        AnalyticsService.get_dashboard_metrics()
        AnalyticsService.get_category_distribution()
        AnalyticsService.get_trend_data(days=30)

        # Verify cache exists
        self.assertIsNotNone(cache.get('dashboard_metrics'))

        # Invalidate cache
        AnalyticsService.invalidate_cache()

        # Verify cache is cleared
        self.assertIsNone(cache.get('dashboard_metrics'))
        self.assertIsNone(cache.get('category_distribution'))
        self.assertIsNone(cache.get('trend_data_30'))

    def test_success_rate_calculation(self):
        """Test success rate calculation in client performance."""
        performance = AnalyticsService.get_client_performance(client_id=str(self.client1.id))

        # Client1 has 2 reports: 1 completed, 1 pending
        # Success rate = (1 / 2) * 100 = 50%
        self.assertEqual(performance['successRate'], 50.0)

    def test_avg_processing_time_calculation(self):
        """Test average processing time calculation."""
        performance = AnalyticsService.get_client_performance()

        # Should calculate average for completed reports only
        self.assertGreater(performance['avgProcessingTimeSeconds'], 0)

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
