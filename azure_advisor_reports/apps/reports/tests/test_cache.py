"""
Tests for Redis caching utilities.

This module tests the caching functions used throughout the reports app
to ensure cache keys are generated correctly, data is cached and retrieved properly,
and cache invalidation works as expected.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from django.core.cache import cache
from django.utils import timezone
import uuid

from apps.reports.cache import (
    get_cache_key,
    get_report_cache_key,
    get_report_list_cache_key,
    cache_report_data,
    get_cached_report_data,
    invalidate_report_cache,
    get_analytics_cache_key,
    cache_dashboard_metrics,
    get_cached_dashboard_metrics,
    cache_category_distribution,
    get_cached_category_distribution,
    cache_trend_data,
    get_cached_trend_data,
    cache_recent_activity,
    get_cached_recent_activity,
    invalidate_analytics_cache,
    invalidate_all_caches,
    get_client_performance_cache_key,
    cache_client_performance,
    get_cached_client_performance,
    invalidate_client_cache,
    CACHE_TTL,
    CACHE_TTL_SHORT,
    CACHE_TTL_LONG,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before and after each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestCacheKeyGeneration:
    """Test cache key generation utilities."""

    def test_get_cache_key_with_prefix_only(self):
        """Test cache key generation with only prefix."""
        key = get_cache_key('test')
        assert key == 'test'

    def test_get_cache_key_with_args(self):
        """Test cache key generation with positional arguments."""
        key = get_cache_key('test', 'arg1', 'arg2', '123')
        assert key == 'test:arg1:arg2:123'

    def test_get_cache_key_with_kwargs(self):
        """Test cache key generation with keyword arguments."""
        key = get_cache_key('test', filter1='value1', filter2='value2')
        # kwargs should be sorted
        assert 'test' in key
        assert 'filter1:value1' in key
        assert 'filter2:value2' in key

    def test_get_cache_key_with_args_and_kwargs(self):
        """Test cache key generation with both args and kwargs."""
        key = get_cache_key('test', 'arg1', filter='value')
        assert 'test' in key
        assert 'arg1' in key
        assert 'filter:value' in key

    def test_get_cache_key_long_key_uses_hash(self):
        """Test that long cache keys are hashed."""
        # Create a very long key
        long_value = 'x' * 200
        key = get_cache_key('test', long_value)

        # Should be hashed and shorter
        assert len(key) < 50
        assert key.startswith('test:')

    def test_get_cache_key_kwargs_sorted(self):
        """Test that kwargs are sorted for consistency."""
        key1 = get_cache_key('test', a='1', b='2', c='3')
        key2 = get_cache_key('test', c='3', a='1', b='2')  # Different order

        # Should produce same key
        assert key1 == key2

    def test_get_report_cache_key(self):
        """Test report-specific cache key generation."""
        report_id = uuid.uuid4()
        key = get_report_cache_key(report_id)

        assert 'report' in key
        assert str(report_id) in key

    def test_get_report_list_cache_key(self):
        """Test report list cache key generation with filters."""
        key = get_report_list_cache_key(client_id='123', status='completed')

        assert 'report_list' in key
        assert 'client_id:123' in key or '123' in key
        assert 'status:completed' in key or 'completed' in key

    def test_get_analytics_cache_key(self):
        """Test analytics cache key generation."""
        key = get_analytics_cache_key('metrics', days=30)

        assert 'metrics' in key
        assert 'days:30' in key or '30' in key


@pytest.mark.django_db
class TestReportCaching:
    """Test report data caching functions."""

    def create_mock_report(self, report_id=None):
        """Helper to create a mock report."""
        if report_id is None:
            report_id = uuid.uuid4()

        report = Mock()
        report.id = report_id
        report.analysis_data = {'total': 100, 'categories': {}}
        report.recommendations = Mock()
        report.recommendations.count = Mock(return_value=50)
        report.total_potential_savings = 1000.50
        report.status = 'completed'
        report.report_type = 'detailed'
        report.created_at = timezone.now()

        return report

    def test_cache_report_data(self):
        """Test caching report data."""
        report = self.create_mock_report()

        result = cache_report_data(report)

        # Check returned data
        assert result['id'] == str(report.id)
        assert result['status'] == 'completed'
        assert result['recommendations_count'] == 50
        assert result['total_potential_savings'] == 1000.50

        # Check data is cached
        key = get_report_cache_key(report.id)
        cached = cache.get(key)
        assert cached is not None
        assert cached['id'] == str(report.id)

    def test_get_cached_report_data_exists(self):
        """Test retrieving cached report data when it exists."""
        report = self.create_mock_report()
        cache_report_data(report)

        # Retrieve cached data
        cached_data = get_cached_report_data(report.id)

        assert cached_data is not None
        assert cached_data['id'] == str(report.id)
        assert cached_data['status'] == 'completed'

    def test_get_cached_report_data_not_exists(self):
        """Test retrieving cached report data when it doesn't exist."""
        report_id = uuid.uuid4()

        # Should return None if not cached
        cached_data = get_cached_report_data(report_id)

        assert cached_data is None

    def test_invalidate_report_cache(self):
        """Test invalidating report cache."""
        report = self.create_mock_report()
        cache_report_data(report)

        # Verify cached
        assert get_cached_report_data(report.id) is not None

        # Invalidate
        invalidate_report_cache(report.id)

        # Should be gone
        assert get_cached_report_data(report.id) is None

    def test_cache_report_data_with_none_created_at(self):
        """Test caching report with None created_at."""
        report = self.create_mock_report()
        report.created_at = None

        result = cache_report_data(report)

        assert result['created_at'] is None


@pytest.mark.django_db
class TestAnalyticsCaching:
    """Test analytics data caching functions."""

    def test_cache_dashboard_metrics(self):
        """Test caching dashboard metrics."""
        metrics_data = {
            'total_reports': 100,
            'total_savings': 50000,
            'active_clients': 25
        }

        cache_dashboard_metrics(metrics_data)

        # Check data is cached
        cached = get_cached_dashboard_metrics()
        assert cached is not None
        assert cached['total_reports'] == 100
        assert cached['total_savings'] == 50000

    def test_get_cached_dashboard_metrics_not_exists(self):
        """Test retrieving dashboard metrics when not cached."""
        result = get_cached_dashboard_metrics()

        assert result is None

    def test_cache_category_distribution(self):
        """Test caching category distribution data."""
        distribution_data = {
            'cost': 50,
            'security': 30,
            'reliability': 20
        }

        cache_category_distribution(distribution_data)

        # Retrieve cached data
        cached = get_cached_category_distribution()
        assert cached is not None
        assert cached['cost'] == 50
        assert cached['security'] == 30

    def test_cache_trend_data(self):
        """Test caching trend data with different day ranges."""
        trend_data_7 = [{'date': '2025-01-01', 'count': 10}]
        trend_data_30 = [{'date': '2025-01-01', 'count': 100}]

        cache_trend_data(trend_data_7, days=7)
        cache_trend_data(trend_data_30, days=30)

        # Should be cached separately for different day ranges
        cached_7 = get_cached_trend_data(days=7)
        cached_30 = get_cached_trend_data(days=30)

        assert cached_7 is not None
        assert cached_30 is not None
        assert cached_7[0]['count'] == 10
        assert cached_30[0]['count'] == 100

    def test_get_cached_trend_data_not_exists(self):
        """Test retrieving trend data when not cached."""
        result = get_cached_trend_data(days=7)

        assert result is None

    def test_cache_recent_activity(self):
        """Test caching recent activity data."""
        activity_data = [
            {'id': '1', 'action': 'report_generated'},
            {'id': '2', 'action': 'client_created'}
        ]

        cache_recent_activity(activity_data, limit=10)

        # Retrieve cached data
        cached = get_cached_recent_activity(limit=10)
        assert cached is not None
        assert len(cached) == 2
        assert cached[0]['action'] == 'report_generated'

    def test_cache_recent_activity_different_limits(self):
        """Test caching recent activity with different limits."""
        activity_short = [{'id': '1'}]
        activity_long = [{'id': '1'}, {'id': '2'}, {'id': '3'}]

        cache_recent_activity(activity_short, limit=5)
        cache_recent_activity(activity_long, limit=20)

        # Should be cached separately
        cached_5 = get_cached_recent_activity(limit=5)
        cached_20 = get_cached_recent_activity(limit=20)

        assert len(cached_5) == 1
        assert len(cached_20) == 3

    def test_invalidate_analytics_cache(self):
        """Test invalidating all analytics caches."""
        # Cache various analytics data
        cache_dashboard_metrics({'total': 100})
        cache_category_distribution({'cost': 50})
        cache_trend_data([{'count': 10}], days=7)

        # Verify cached
        assert get_cached_dashboard_metrics() is not None
        assert get_cached_category_distribution() is not None
        assert get_cached_trend_data(days=7) is not None

        # Invalidate all
        invalidate_analytics_cache()

        # All should be gone
        assert get_cached_dashboard_metrics() is None
        assert get_cached_category_distribution() is None
        assert get_cached_trend_data(days=7) is None


@pytest.mark.django_db
class TestClientCaching:
    """Test client performance caching functions."""

    def test_get_client_performance_cache_key(self):
        """Test client performance cache key generation."""
        client_id = uuid.uuid4()
        key = get_client_performance_cache_key(client_id)

        assert 'client_performance' in key
        assert str(client_id) in key

    def test_cache_client_performance(self):
        """Test caching client performance data."""
        client_id = uuid.uuid4()
        performance_data = {
            'total_reports': 25,
            'total_savings': 15000,
            'avg_score': 85.5
        }

        cache_client_performance(client_id, performance_data)

        # Retrieve cached data
        cached = get_cached_client_performance(client_id)
        assert cached is not None
        assert cached['total_reports'] == 25
        assert cached['avg_score'] == 85.5

    def test_get_cached_client_performance_not_exists(self):
        """Test retrieving client performance when not cached."""
        client_id = uuid.uuid4()

        result = get_cached_client_performance(client_id)

        assert result is None

    def test_invalidate_client_cache(self):
        """Test invalidating client cache."""
        client_id = uuid.uuid4()
        performance_data = {'total_reports': 25}

        cache_client_performance(client_id, performance_data)

        # Verify cached
        assert get_cached_client_performance(client_id) is not None

        # Invalidate
        invalidate_client_cache(client_id)

        # Should be gone
        assert get_cached_client_performance(client_id) is None


@pytest.mark.django_db
class TestCacheTTL:
    """Test cache Time-To-Live settings."""

    @patch('apps.reports.cache.cache')
    def test_report_cache_uses_default_ttl(self, mock_cache):
        """Test that report caching uses default TTL."""
        from apps.reports import cache as cache_module

        report = Mock()
        report.id = uuid.uuid4()
        report.analysis_data = {}
        report.recommendations = Mock()
        report.recommendations.count = Mock(return_value=0)
        report.total_potential_savings = 0
        report.status = 'completed'
        report.report_type = 'detailed'
        report.created_at = timezone.now()

        cache_module.cache_report_data(report)

        # Check that cache.set was called with CACHE_TTL
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert call_args[0][2] == CACHE_TTL

    @patch('apps.reports.cache.cache')
    def test_dashboard_metrics_use_default_ttl(self, mock_cache):
        """Test that dashboard metrics use default TTL."""
        from apps.reports import cache as cache_module

        metrics = {'total': 100}
        cache_module.cache_dashboard_metrics(metrics)

        # Should use default TTL
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert call_args[0][2] == CACHE_TTL

    @patch('apps.reports.cache.cache')
    def test_category_distribution_uses_long_ttl(self, mock_cache):
        """Test that category distribution uses long TTL."""
        from apps.reports import cache as cache_module

        distribution = {'cost': 50}
        cache_module.cache_category_distribution(distribution)

        # Should use long TTL (1 hour)
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert call_args[0][2] == CACHE_TTL_LONG

    @patch('apps.reports.cache.cache')
    def test_recent_activity_uses_short_ttl(self, mock_cache):
        """Test that recent activity uses short TTL."""
        from apps.reports import cache as cache_module

        activity = [{'id': '1'}]
        cache_module.cache_recent_activity(activity, limit=10)

        # Should use short TTL (5 minutes)
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert call_args[0][2] == CACHE_TTL_SHORT


@pytest.mark.django_db
class TestCacheInvalidation:
    """Test cache invalidation functions."""

    def test_invalidate_all_caches(self):
        """Test invalidating all caches."""
        # Cache various types of data
        report_id = uuid.uuid4()
        client_id = uuid.uuid4()

        report = Mock()
        report.id = report_id
        report.analysis_data = {}
        report.recommendations = Mock()
        report.recommendations.count = Mock(return_value=0)
        report.total_potential_savings = 0
        report.status = 'completed'
        report.report_type = 'detailed'
        report.created_at = timezone.now()

        cache_report_data(report)
        cache_dashboard_metrics({'total': 100})
        cache_client_performance(client_id, {'total_reports': 10})

        # Verify all are cached
        assert get_cached_report_data(report_id) is not None
        assert get_cached_dashboard_metrics() is not None
        assert get_cached_client_performance(client_id) is not None

        # Invalidate everything
        invalidate_all_caches()

        # All should be gone
        assert get_cached_report_data(report_id) is None
        assert get_cached_dashboard_metrics() is None
        assert get_cached_client_performance(client_id) is None

    @patch('apps.reports.cache.cache')
    def test_invalidate_all_caches_calls_clear(self, mock_cache):
        """Test that invalidate_all_caches calls cache.clear()."""
        from apps.reports import cache as cache_module

        cache_module.invalidate_all_caches()

        # Should call cache.clear()
        mock_cache.clear.assert_called_once()


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_cache_with_empty_data(self):
        """Test caching empty data structures."""
        cache_dashboard_metrics({})
        cache_category_distribution({})
        cache_trend_data([], days=7)
        cache_recent_activity([], limit=10)

        # Should cache empty data
        assert get_cached_dashboard_metrics() == {}
        assert get_cached_category_distribution() == {}
        assert get_cached_trend_data(days=7) == []
        assert get_cached_recent_activity(limit=10) == []

    def test_cache_with_none_values(self):
        """Test caching data with None values."""
        data_with_none = {
            'value1': None,
            'value2': 'test',
            'value3': None
        }

        cache_dashboard_metrics(data_with_none)

        cached = get_cached_dashboard_metrics()
        assert cached is not None
        assert cached['value1'] is None
        assert cached['value2'] == 'test'

    def test_cache_key_with_special_characters(self):
        """Test cache key generation with special characters."""
        key = get_cache_key('test', 'arg/with/slash', filter='value:with:colon')

        # Should handle special characters
        assert isinstance(key, str)
        assert 'test' in key

    def test_cache_key_with_unicode(self):
        """Test cache key generation with unicode characters."""
        key = get_cache_key('test', 'café', filter='日本語')

        # Should handle unicode
        assert isinstance(key, str)

    def test_multiple_invalidations(self):
        """Test multiple invalidations don't cause errors."""
        report_id = uuid.uuid4()

        # Invalidate non-existent cache (should not error)
        invalidate_report_cache(report_id)
        invalidate_client_cache(report_id)
        invalidate_analytics_cache()

        # Should complete without errors
        assert True
