"""
Unit tests for analytics API views.
"""

from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache

from apps.clients.models import Client
from apps.reports.models import Report, Recommendation

User = get_user_model()


class AnalyticsAPITestCase(TestCase):
    """Test cases for Analytics API endpoints."""

    def setUp(self):
        """Set up test data."""
        cache.clear()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            role='analyst'
        )

        # Create admin user
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            role='admin',
            is_staff=True
        )

        # Create API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create test data
        self.test_client = Client.objects.create(
            company_name='Test Client',
            status='active',
            contact_email='client@example.com'
        )

        self.report = Report.objects.create(
            client=self.test_client,
            created_by=self.user,
            report_type='detailed',
            status='completed',
            processing_started_at=timezone.now() - timedelta(minutes=10),
            processing_completed_at=timezone.now() - timedelta(minutes=5)
        )

        self.recommendation = Recommendation.objects.create(
            report=self.report,
            category='cost',
            business_impact='High',
            recommendation='Test recommendation',
            potential_savings=Decimal('500.00')
        )

    def test_dashboard_analytics_endpoint(self):
        """Test GET /api/analytics/dashboard/"""
        url = reverse('analytics:dashboard-analytics')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response structure
        self.assertIn('metrics', response.data)
        self.assertIn('categoryDistribution', response.data)
        self.assertIn('trendData', response.data)
        self.assertIn('recentActivity', response.data)

        # Check metrics structure
        metrics = response.data['metrics']
        self.assertIn('totalRecommendations', metrics)
        self.assertIn('totalPotentialSavings', metrics)
        self.assertIn('activeClients', metrics)
        self.assertIn('reportsGeneratedThisMonth', metrics)
        self.assertIn('trends', metrics)

    def test_dashboard_analytics_unauthorized(self):
        """Test dashboard analytics requires authentication."""
        self.client.force_authenticate(user=None)
        url = reverse('analytics:dashboard-analytics')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_metrics_endpoint(self):
        """Test GET /api/analytics/metrics/"""
        url = reverse('analytics:dashboard-metrics')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response has metrics
        self.assertIn('totalRecommendations', response.data)
        self.assertIn('totalPotentialSavings', response.data)
        self.assertIn('activeClients', response.data)
        self.assertIn('trends', response.data)

    def test_trend_data_endpoint_default(self):
        """Test GET /api/analytics/trends/ with default parameters."""
        url = reverse('analytics:trend-data')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response structure
        self.assertIn('data', response.data)
        self.assertIn('summary', response.data)

        # Default is 30 days, so should have 31 data points
        self.assertEqual(len(response.data['data']), 31)

    def test_trend_data_endpoint_7_days(self):
        """Test GET /api/analytics/trends/?days=7"""
        url = reverse('analytics:trend-data')
        response = self.client.get(url, {'days': 7})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 8)  # 7 days + today

    def test_trend_data_endpoint_90_days(self):
        """Test GET /api/analytics/trends/?days=90"""
        url = reverse('analytics:trend-data')
        response = self.client.get(url, {'days': 90})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 91)  # 90 days + today

    def test_trend_data_invalid_days(self):
        """Test trend data with invalid days parameter."""
        url = reverse('analytics:trend-data')

        # Invalid number - should default to 30
        response = self.client.get(url, {'days': 45})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 31)

        # Invalid string - should default to 30
        response = self.client.get(url, {'days': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 31)

    def test_category_distribution_endpoint(self):
        """Test GET /api/analytics/categories/"""
        url = reverse('analytics:category-distribution')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response structure
        self.assertIn('categories', response.data)
        self.assertIn('total', response.data)

        # Check we have categories
        self.assertGreater(len(response.data['categories']), 0)

        # Check category structure
        category = response.data['categories'][0]
        self.assertIn('name', category)
        self.assertIn('value', category)
        self.assertIn('percentage', category)
        self.assertIn('color', category)

    def test_recent_activity_endpoint_default(self):
        """Test GET /api/analytics/recent-activity/ with default limit."""
        url = reverse('analytics:recent-activity')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

        # Check activity structure
        if len(response.data) > 0:
            activity = response.data[0]
            self.assertIn('id', activity)
            self.assertIn('type', activity)
            self.assertIn('title', activity)
            self.assertIn('description', activity)
            self.assertIn('timestamp', activity)
            self.assertIn('clientName', activity)
            self.assertIn('status', activity)

    def test_recent_activity_endpoint_with_limit(self):
        """Test GET /api/analytics/recent-activity/?limit=5"""
        # Create more reports
        for i in range(10):
            Report.objects.create(
                client=self.test_client,
                created_by=self.user,
                report_type='detailed',
                status='completed'
            )

        url = reverse('analytics:recent-activity')
        response = self.client.get(url, {'limit': 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_recent_activity_limit_validation(self):
        """Test recent activity limit validation."""
        url = reverse('analytics:recent-activity')

        # Negative limit - should default to 10
        response = self.client.get(url, {'limit': -5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Limit too high - should cap at 100
        response = self.client.get(url, {'limit': 200})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_client_performance_endpoint_all_clients(self):
        """Test GET /api/analytics/client-performance/ without client_id."""
        url = reverse('analytics:client-performance')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response structure
        self.assertIn('totalReports', response.data)
        self.assertIn('completedReports', response.data)
        self.assertIn('failedReports', response.data)
        self.assertIn('successRate', response.data)
        self.assertIn('avgProcessingTimeSeconds', response.data)
        self.assertIn('totalRecommendations', response.data)
        self.assertIn('totalPotentialSavings', response.data)
        self.assertIn('categoryBreakdown', response.data)

    def test_client_performance_endpoint_specific_client(self):
        """Test GET /api/analytics/client-performance/?client_id=<uuid>"""
        url = reverse('analytics:client-performance')
        response = self.client.get(url, {'client_id': str(self.test_client.id)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('totalReports', response.data)

    def test_business_impact_distribution_endpoint(self):
        """Test GET /api/analytics/business-impact/"""
        url = reverse('analytics:business-impact')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response structure
        self.assertIn('distribution', response.data)
        self.assertIn('total', response.data)

        # Check distribution items
        if len(response.data['distribution']) > 0:
            item = response.data['distribution'][0]
            self.assertIn('impact', item)
            self.assertIn('count', item)
            self.assertIn('percentage', item)

    def test_cache_invalidation_endpoint_admin(self):
        """Test POST /api/analytics/cache/invalidate/ as admin."""
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin_user)

        url = reverse('analytics:cache-invalidate')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_cache_invalidation_endpoint_non_admin(self):
        """Test cache invalidation requires admin permissions."""
        # Regular user should be forbidden
        url = reverse('analytics:cache-invalidate')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)

    def test_analytics_response_format(self):
        """Test that all endpoints return properly formatted responses."""
        endpoints = [
            'analytics:dashboard-analytics',
            'analytics:dashboard-metrics',
            'analytics:trend-data',
            'analytics:category-distribution',
            'analytics:recent-activity',
            'analytics:client-performance',
            'analytics:business-impact',
        ]

        for endpoint_name in endpoints:
            url = reverse(endpoint_name)
            response = self.client.get(url)

            # All endpoints should return 200 for authenticated users
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                f"Endpoint {endpoint_name} failed with {response.status_code}"
            )

            # Response should be JSON
            self.assertEqual(response['Content-Type'], 'application/json')

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()


class AnalyticsCachingTestCase(TestCase):
    """Test cases for analytics caching behavior."""

    def setUp(self):
        """Set up test data."""
        cache.clear()

        self.user = User.objects.create_user(
            username='cachetest',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create test data
        test_client = Client.objects.create(
            company_name='Test Client',
            status='active'
        )

        Report.objects.create(
            client=test_client,
            created_by=self.user,
            report_type='detailed',
            status='completed'
        )

    def test_dashboard_metrics_uses_cache(self):
        """Test that dashboard metrics endpoint uses caching."""
        url = reverse('analytics:dashboard-metrics')

        # First request - hits database
        response1 = self.client.get(url)
        initial_count = response1.data['totalRecommendations']

        # Create new data
        report = Report.objects.first()
        Recommendation.objects.create(
            report=report,
            category='cost',
            business_impact='High',
            recommendation='New recommendation',
            potential_savings=Decimal('100.00')
        )

        # Second request - should return cached data (not include new recommendation)
        response2 = self.client.get(url)
        self.assertEqual(response2.data['totalRecommendations'], initial_count)

    def test_cache_invalidation_works(self):
        """Test that cache invalidation actually clears the cache."""
        # Create admin user
        admin = User.objects.create_user(
            username='admintest',
            email='admin@example.com',
            first_name='Admin',
            last_name='Test',
            role='admin',
            is_staff=True
        )

        # Populate cache
        self.client.get(reverse('analytics:dashboard-metrics'))

        # Invalidate cache as admin
        self.client.force_authenticate(user=admin)
        invalidate_url = reverse('analytics:cache-invalidate')
        self.client.post(invalidate_url)

        # Verify cache is cleared
        self.assertIsNone(cache.get('dashboard_metrics'))

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
