"""
Database Optimization Tools

Provides tools for analyzing and optimizing database queries, including:
- Slow query detection
- Missing index identification
- Query plan analysis
- N+1 query detection
"""

import time
import logging
from typing import List, Dict, Any, Optional
from django.db import connection, reset_queries
from django.conf import settings
from django.core.cache import cache
from functools import wraps

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """
    Analyze database queries for performance issues
    """

    @staticmethod
    def get_slow_queries(threshold_ms: float = 100) -> List[Dict[str, Any]]:
        """
        Get queries that took longer than threshold

        Args:
            threshold_ms: Threshold in milliseconds

        Returns:
            List of slow queries with timing information
        """
        if not settings.DEBUG:
            logger.warning('Query logging only available in DEBUG mode')
            return []

        slow_queries = []
        for query in connection.queries:
            time_ms = float(query['time']) * 1000
            if time_ms > threshold_ms:
                slow_queries.append({
                    'sql': query['sql'],
                    'time_ms': time_ms,
                })

        return sorted(slow_queries, key=lambda x: x['time_ms'], reverse=True)

    @staticmethod
    def analyze_query_patterns() -> Dict[str, Any]:
        """
        Analyze query patterns to detect N+1 queries and other issues
        """
        if not settings.DEBUG:
            return {'error': 'Query analysis only available in DEBUG mode'}

        queries = connection.queries
        total_queries = len(queries)
        total_time = sum(float(q['time']) for q in queries)

        # Group by SQL statement (ignoring parameters)
        query_counts = {}
        for query in queries:
            sql = query['sql'].split('WHERE')[0]  # Simplified grouping
            if sql not in query_counts:
                query_counts[sql] = 0
            query_counts[sql] += 1

        # Detect potential N+1 queries (same query executed many times)
        potential_n_plus_1 = {
            sql: count
            for sql, count in query_counts.items()
            if count > 10
        }

        return {
            'total_queries': total_queries,
            'total_time_ms': total_time * 1000,
            'unique_queries': len(query_counts),
            'potential_n_plus_1_queries': potential_n_plus_1,
            'duplicate_query_percentage': (
                100 * (1 - len(query_counts) / total_queries)
                if total_queries > 0 else 0
            ),
        }

    @staticmethod
    def get_table_stats() -> List[Dict[str, Any]]:
        """
        Get statistics about database tables
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
            """)

            columns = [col[0] for col in cursor.description]
            results = []

            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results

    @staticmethod
    def get_index_usage() -> List[Dict[str, Any]]:
        """
        Get index usage statistics to identify unused indexes
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan as index_scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM pg_stat_user_indexes
                ORDER BY idx_scan ASC, pg_relation_size(indexrelid) DESC
            """)

            columns = [col[0] for col in cursor.description]
            results = []

            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results

    @staticmethod
    def get_missing_indexes() -> List[Dict[str, Any]]:
        """
        Identify potential missing indexes based on sequential scans
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    seq_scan as sequential_scans,
                    seq_tup_read as tuples_read,
                    idx_scan as index_scans,
                    n_live_tup as live_tuples,
                    CASE
                        WHEN seq_scan > 0 THEN ROUND((100.0 * idx_scan / (seq_scan + idx_scan))::numeric, 2)
                        ELSE 100
                    END as index_usage_percentage
                FROM pg_stat_user_tables
                WHERE n_live_tup > 1000
                AND seq_scan > idx_scan
                ORDER BY seq_scan DESC, n_live_tup DESC
            """)

            columns = [col[0] for col in cursor.description]
            results = []

            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results


def track_query_performance(func):
    """
    Decorator to track query performance

    Usage:
        @track_query_performance
        def get_reports():
            return Report.objects.all()
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            return func(*args, **kwargs)

        reset_queries()
        start_time = time.time()

        result = func(*args, **kwargs)

        duration = time.time() - start_time
        query_count = len(connection.queries)

        if query_count > 50:
            logger.warning(
                f'{func.__name__} executed {query_count} queries in {duration:.2f}s. '
                'Potential N+1 query problem.'
            )

        if duration > 1.0:
            logger.warning(
                f'{func.__name__} took {duration:.2f}s with {query_count} queries. '
                'Consider optimization.'
            )

        return result

    return wrapper


class QueryCache:
    """
    Simple query result caching
    """

    @staticmethod
    def cached_query(cache_key: str, timeout: int = 300):
        """
        Decorator to cache query results

        Args:
            cache_key: Cache key (can use format strings with args)
            timeout: Cache timeout in seconds

        Usage:
            @QueryCache.cached_query('reports_for_client_{client_id}', timeout=600)
            def get_client_reports(client_id):
                return Report.objects.filter(client_id=client_id)
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Format cache key with args/kwargs
                formatted_key = cache_key.format(**kwargs) if kwargs else cache_key

                # Try to get from cache
                cached_result = cache.get(formatted_key)
                if cached_result is not None:
                    logger.debug(f'Cache hit for {formatted_key}')
                    return cached_result

                # Execute query
                result = func(*args, **kwargs)

                # Cache result
                cache.set(formatted_key, result, timeout)
                logger.debug(f'Cached result for {formatted_key}')

                return result

            return wrapper
        return decorator

    @staticmethod
    def invalidate(cache_key: str):
        """
        Invalidate a cache key
        """
        cache.delete(cache_key)

    @staticmethod
    def invalidate_pattern(pattern: str):
        """
        Invalidate all keys matching pattern
        Note: Requires Redis cache backend with pattern support
        """
        try:
            cache.delete_pattern(pattern)
        except AttributeError:
            logger.warning('Cache backend does not support pattern deletion')


# =============================================================================
# Recommended Indexes for Common Queries
# =============================================================================

RECOMMENDED_INDEXES = """
-- Reports Model Indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_client_status
    ON reports_report (client_id, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_created_status
    ON reports_report (created_at DESC, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_type_status
    ON reports_report (report_type, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_created_by
    ON reports_report (created_by_id, created_at DESC);

-- Clients Model Indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clients_status
    ON clients_client (status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clients_company_name
    ON clients_client (company_name);

-- Recommendations Model Indexes (if applicable)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recommendations_report
    ON recommendations_recommendation (report_id, category);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recommendations_category_impact
    ON recommendations_recommendation (category, impact);

-- User Model Indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role_active
    ON authentication_user (role, is_active);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email
    ON authentication_user (email);

-- Composite indexes for common filter combinations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_client_type_status
    ON reports_report (client_id, report_type, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_created_range
    ON reports_report (created_at DESC)
    WHERE status IN ('completed', 'failed');
"""


def apply_recommended_indexes():
    """
    Apply recommended indexes to database

    WARNING: Run this during maintenance window as it may take time
    """
    with connection.cursor() as cursor:
        for statement in RECOMMENDED_INDEXES.split(';'):
            statement = statement.strip()
            if statement:
                try:
                    logger.info(f'Executing: {statement[:100]}...')
                    cursor.execute(statement)
                    logger.info('✓ Index created successfully')
                except Exception as e:
                    logger.error(f'Failed to create index: {str(e)}')


# =============================================================================
# Query Optimization Tips
# =============================================================================

OPTIMIZATION_TIPS = """
Database Query Optimization Guide
==================================

1. Use select_related() for Foreign Keys
   ----------------------------------------
   Bad:  reports = Report.objects.all()
         for report in reports:
             print(report.client.name)  # N+1 query!

   Good: reports = Report.objects.select_related('client', 'created_by').all()
         for report in reports:
             print(report.client.name)  # Single query

2. Use prefetch_related() for Many-to-Many and Reverse FK
   --------------------------------------------------------
   Bad:  clients = Client.objects.all()
         for client in clients:
             reports = client.reports.all()  # N+1 query!

   Good: clients = Client.objects.prefetch_related('reports').all()
         for client in clients:
             reports = client.reports.all()  # Prefetched

3. Use only() and defer() to Limit Fields
   -----------------------------------------
   # Only fetch needed fields
   Report.objects.only('id', 'title', 'status')

   # Defer large fields
   Report.objects.defer('analysis_data', 'error_message')

4. Use values() and values_list() for Simple Data
   ------------------------------------------------
   # Don't load full model instances if you only need a few fields
   Report.objects.filter(status='completed').values('id', 'title')

5. Use exists() Instead of count() for Existence Checks
   -------------------------------------------------------
   Bad:  if Report.objects.filter(client=client).count() > 0:
   Good: if Report.objects.filter(client=client).exists():

6. Use Indexes for Filtered Fields
   ----------------------------------
   # Add indexes to fields used in WHERE, ORDER BY, JOIN
   class Meta:
       indexes = [
           models.Index(fields=['status', 'created_at']),
       ]

7. Batch Operations
   -------------------
   # Use bulk_create, bulk_update instead of individual saves
   Report.objects.bulk_create(reports_list, batch_size=1000)

8. Use Database Functions
   --------------------------
   from django.db.models import Count, Avg, Max
   Client.objects.annotate(report_count=Count('reports'))

9. Cache Expensive Queries
   --------------------------
   from django.core.cache import cache

   result = cache.get('expensive_query')
   if result is None:
       result = expensive_query()
       cache.set('expensive_query', result, 300)

10. Use Raw SQL for Complex Queries
    ----------------------------------
    # Sometimes raw SQL is more efficient than ORM
    Report.objects.raw('SELECT * FROM reports WHERE ...')
"""


def print_optimization_tips():
    """Print database optimization tips"""
    print(OPTIMIZATION_TIPS)
