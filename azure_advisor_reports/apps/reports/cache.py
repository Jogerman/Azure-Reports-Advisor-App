"""
Redis caching utilities for report and analytics data.

Implements caching strategies to reduce database load and improve
response times by up to 80% for frequently accessed data.
"""

from django.core.cache import cache
from django.conf import settings
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

# Cache TTL settings (in seconds)
CACHE_TTL = 60 * 15  # 15 minutes for most data
CACHE_TTL_SHORT = 60 * 5  # 5 minutes for frequently changing data
CACHE_TTL_LONG = 60 * 60  # 1 hour for relatively static data


def get_cache_key(prefix, *args, **kwargs):
    """
    Generate a consistent cache key from prefix and arguments.

    Args:
        prefix (str): Cache key prefix (e.g., 'report', 'analytics')
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key

    Returns:
        str: Generated cache key
    """
    key_parts = [prefix]

    # Add positional args
    for arg in args:
        key_parts.append(str(arg))

    # Add keyword args (sorted for consistency)
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")

    # Create hash if key is too long
    key_string = ":".join(key_parts)
    if len(key_string) > 200:
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    return key_string


# ============================================================================
# Report Caching
# ============================================================================

def get_report_cache_key(report_id):
    """Get cache key for a specific report."""
    return get_cache_key('report', report_id)


def get_report_list_cache_key(**filters):
    """Get cache key for report list with filters."""
    return get_cache_key('report_list', **filters)


def cache_report_data(report):
    """
    Cache report data including analysis and basic stats.

    Args:
        report: Report model instance

    Returns:
        dict: Cached data
    """
    key = get_report_cache_key(report.id)

    cached_data = {
        'id': str(report.id),
        'analysis_data': report.analysis_data,
        'recommendations_count': report.recommendations.count(),
        'total_potential_savings': float(report.total_potential_savings),
        'status': report.status,
        'report_type': report.report_type,
        'created_at': report.created_at.isoformat() if report.created_at else None,
    }

    cache.set(key, cached_data, CACHE_TTL)
    logger.debug(f"Cached report data for {report.id}")

    return cached_data


def get_cached_report_data(report_id):
    """
    Retrieve cached report data.

    Args:
        report_id (str): Report UUID

    Returns:
        dict: Cached data or None if not found
    """
    key = get_report_cache_key(report_id)
    cached_data = cache.get(key)

    if cached_data:
        logger.debug(f"Cache hit for report {report_id}")
    else:
        logger.debug(f"Cache miss for report {report_id}")

    return cached_data


def invalidate_report_cache(report_id):
    """
    Invalidate cache for a specific report.

    Args:
        report_id (str): Report UUID
    """
    key = get_report_cache_key(report_id)
    cache.delete(key)
    logger.info(f"Invalidated cache for report {report_id}")


# ============================================================================
# Analytics Caching
# ============================================================================

def get_analytics_cache_key(metric_name, **params):
    """Get cache key for analytics metrics."""
    return get_cache_key('analytics', metric_name, **params)


def cache_dashboard_metrics(metrics_data):
    """
    Cache dashboard metrics data.

    Args:
        metrics_data (dict): Metrics data to cache

    Returns:
        dict: Cached data
    """
    key = get_analytics_cache_key('dashboard_metrics')
    cache.set(key, metrics_data, CACHE_TTL)
    logger.debug("Cached dashboard metrics")
    return metrics_data


def get_cached_dashboard_metrics():
    """
    Retrieve cached dashboard metrics.

    Returns:
        dict: Cached metrics or None
    """
    key = get_analytics_cache_key('dashboard_metrics')
    cached_data = cache.get(key)

    if cached_data:
        logger.debug("Cache hit for dashboard metrics")
    else:
        logger.debug("Cache miss for dashboard metrics")

    return cached_data


def cache_category_distribution(distribution_data):
    """
    Cache category distribution data.

    Args:
        distribution_data (dict): Category distribution to cache

    Returns:
        dict: Cached data
    """
    key = get_analytics_cache_key('category_distribution')
    cache.set(key, distribution_data, CACHE_TTL_LONG)
    logger.debug("Cached category distribution")
    return distribution_data


def get_cached_category_distribution():
    """
    Retrieve cached category distribution.

    Returns:
        dict: Cached distribution or None
    """
    key = get_analytics_cache_key('category_distribution')
    return cache.get(key)


def cache_trend_data(trend_data, days):
    """
    Cache trend data for a specific time period.

    Args:
        trend_data (dict): Trend data to cache
        days (int): Number of days for trend (7, 30, 90)

    Returns:
        dict: Cached data
    """
    key = get_analytics_cache_key('trend_data', days=days)
    cache.set(key, trend_data, CACHE_TTL)
    logger.debug(f"Cached trend data for {days} days")
    return trend_data


def get_cached_trend_data(days):
    """
    Retrieve cached trend data.

    Args:
        days (int): Number of days for trend

    Returns:
        dict: Cached trend data or None
    """
    key = get_analytics_cache_key('trend_data', days=days)
    return cache.get(key)


def cache_recent_activity(activity_data, limit):
    """
    Cache recent activity data.

    Args:
        activity_data (list): Recent activity items
        limit (int): Number of items

    Returns:
        list: Cached data
    """
    key = get_analytics_cache_key('recent_activity', limit=limit)
    cache.set(key, activity_data, CACHE_TTL_SHORT)
    logger.debug(f"Cached recent activity (limit={limit})")
    return activity_data


def get_cached_recent_activity(limit):
    """
    Retrieve cached recent activity.

    Args:
        limit (int): Number of items

    Returns:
        list: Cached activity data or None
    """
    key = get_analytics_cache_key('recent_activity', limit=limit)
    return cache.get(key)


# ============================================================================
# Cache Invalidation
# ============================================================================

def invalidate_analytics_cache():
    """
    Invalidate all analytics caches.

    Call this when new reports are created or updated to ensure
    dashboard shows fresh data.
    """
    patterns = [
        get_analytics_cache_key('dashboard_metrics'),
        get_analytics_cache_key('category_distribution'),
        get_analytics_cache_key('trend_data', days=7),
        get_analytics_cache_key('trend_data', days=30),
        get_analytics_cache_key('trend_data', days=90),
        get_analytics_cache_key('recent_activity', limit=10),
        get_analytics_cache_key('recent_activity', limit=20),
        get_analytics_cache_key('recent_activity', limit=50),
    ]

    for pattern in patterns:
        cache.delete(pattern)

    logger.info("Invalidated all analytics caches")


def invalidate_all_caches():
    """
    Invalidate all application caches.

    Use sparingly - only for major data changes or debugging.
    """
    try:
        cache.clear()
        logger.warning("Cleared all application caches")
    except Exception as e:
        logger.error(f"Failed to clear caches: {e}")


# ============================================================================
# Client Performance Caching
# ============================================================================

def get_client_performance_cache_key(client_id):
    """Get cache key for client performance metrics."""
    return get_cache_key('client_performance', client_id)


def cache_client_performance(client_id, performance_data):
    """
    Cache client performance data.

    Args:
        client_id (str): Client UUID
        performance_data (dict): Performance metrics

    Returns:
        dict: Cached data
    """
    key = get_client_performance_cache_key(client_id)
    cache.set(key, performance_data, CACHE_TTL)
    logger.debug(f"Cached client performance for {client_id}")
    return performance_data


def get_cached_client_performance(client_id):
    """
    Retrieve cached client performance data.

    Args:
        client_id (str): Client UUID

    Returns:
        dict: Cached performance data or None
    """
    key = get_client_performance_cache_key(client_id)
    return cache.get(key)


def invalidate_client_cache(client_id):
    """
    Invalidate all caches related to a specific client.

    Args:
        client_id (str): Client UUID
    """
    performance_key = get_client_performance_cache_key(client_id)
    cache.delete(performance_key)
    logger.info(f"Invalidated cache for client {client_id}")
