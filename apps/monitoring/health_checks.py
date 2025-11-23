"""
Health Check Endpoints for Monitoring

Provides endpoints for checking application health, readiness, and liveness.
"""

import time
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from .telemetry import track_availability


def health_check(request):
    """
    Basic health check endpoint
    Returns 200 if application is running
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': getattr(settings, 'VERSION', '1.0.0'),
    })


def readiness_check(request):
    """
    Readiness check - verifies that application is ready to serve traffic
    Checks: Database, Cache, and other critical dependencies
    """
    start_time = time.time()
    checks = {}
    overall_status = 'ready'

    # Check Database
    db_status, db_duration = check_database()
    checks['database'] = {
        'status': db_status,
        'duration_ms': db_duration
    }
    if db_status != 'healthy':
        overall_status = 'not_ready'

    # Check Cache
    cache_status, cache_duration = check_cache()
    checks['cache'] = {
        'status': cache_status,
        'duration_ms': cache_duration
    }
    if cache_status != 'healthy':
        overall_status = 'degraded'  # Cache failure is not critical

    # Check Celery (if configured)
    celery_status, celery_duration = check_celery()
    checks['celery'] = {
        'status': celery_status,
        'duration_ms': celery_duration
    }

    total_duration = int((time.time() - start_time) * 1000)

    # Track availability
    track_availability(
        'ReadinessCheck',
        success=overall_status == 'ready',
        duration_ms=total_duration,
        message=f'Status: {overall_status}',
        properties={
            'database': db_status,
            'cache': cache_status,
            'celery': celery_status,
        }
    )

    status_code = 200 if overall_status == 'ready' else 503

    return JsonResponse({
        'status': overall_status,
        'checks': checks,
        'duration_ms': total_duration,
        'timestamp': timezone.now().isoformat(),
    }, status=status_code)


def liveness_check(request):
    """
    Liveness check - verifies that application is running and not deadlocked
    This should be lightweight and always succeed if the process is running
    """
    return JsonResponse({
        'status': 'alive',
        'timestamp': timezone.now().isoformat(),
    })


def check_database():
    """
    Check database connectivity
    Returns: (status, duration_ms)
    """
    start_time = time.time()
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        duration_ms = int((time.time() - start_time) * 1000)
        return 'healthy', duration_ms
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return f'unhealthy: {str(e)[:50]}', duration_ms


def check_cache():
    """
    Check cache connectivity
    Returns: (status, duration_ms)
    """
    start_time = time.time()
    try:
        test_key = '__health_check__'
        test_value = 'ok'

        cache.set(test_key, test_value, 10)
        cached_value = cache.get(test_key)

        if cached_value == test_value:
            duration_ms = int((time.time() - start_time) * 1000)
            cache.delete(test_key)
            return 'healthy', duration_ms
        else:
            duration_ms = int((time.time() - start_time) * 1000)
            return 'unhealthy: cache read/write mismatch', duration_ms
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return f'unhealthy: {str(e)[:50]}', duration_ms


def check_celery():
    """
    Check Celery worker availability
    Returns: (status, duration_ms)
    """
    start_time = time.time()
    try:
        from django_celery_results.models import TaskResult

        # Check if we can query task results
        TaskResult.objects.first()

        duration_ms = int((time.time() - start_time) * 1000)
        return 'healthy', duration_ms
    except ImportError:
        duration_ms = int((time.time() - start_time) * 1000)
        return 'not_configured', duration_ms
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return f'unhealthy: {str(e)[:50]}', duration_ms


def metrics_endpoint(request):
    """
    Prometheus-style metrics endpoint (optional)
    """
    from django.db import connection

    metrics = []

    # Database metrics
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes
                FROM pg_stat_user_tables
                ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()

            for row in rows:
                schema, table, inserts, updates, deletes = row
                metrics.append(f'db_operations_total{{table="{table}",operation="insert"}} {inserts}')
                metrics.append(f'db_operations_total{{table="{table}",operation="update"}} {updates}')
                metrics.append(f'db_operations_total{{table="{table}",operation="delete"}} {deletes}')
    except:
        pass

    # Application info
    metrics.append(f'app_info{{version="{getattr(settings, "VERSION", "1.0.0")}"}} 1')

    return JsonResponse({
        'metrics': '\n'.join(metrics)
    })
