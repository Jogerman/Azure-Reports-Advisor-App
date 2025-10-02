"""
Core views for health checks and utilities.
"""

import time
import logging
from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Comprehensive health check endpoint for monitoring.

    Returns detailed status of all critical services:
    - PostgreSQL database
    - Redis cache
    - Celery workers

    Response includes:
    - Overall health status
    - Individual service status
    - Response times for each service
    - Service details
    """
    start_time = time.time()
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {},
        'performance': {}
    }

    # Check database connection
    db_start = time.time()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            db_version = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            migration_count = cursor.fetchone()[0]

        db_time = time.time() - db_start
        health_status['services']['database'] = {
            'status': 'healthy',
            'response_time_ms': round(db_time * 1000, 2),
            'details': {
                'engine': 'PostgreSQL',
                'migrations_applied': migration_count,
                'version': db_version.split()[0] if db_version else 'unknown'
            }
        }
        health_status['performance']['database_response_ms'] = round(db_time * 1000, 2)
    except Exception as e:
        db_time = time.time() - db_start
        health_status['services']['database'] = {
            'status': 'unhealthy',
            'response_time_ms': round(db_time * 1000, 2),
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
        logger.error(f"Database health check failed: {str(e)}")

    # Check Redis connection
    redis_start = time.time()
    try:
        test_key = f'health_check_{int(time.time())}'
        cache.set(test_key, 'test', 10)
        retrieved_value = cache.get(test_key)
        cache.delete(test_key)

        redis_time = time.time() - redis_start

        # Get Redis info
        redis_info = {}
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            info = redis_conn.info()
            redis_info = {
                'version': info.get('redis_version', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'unknown'),
                'uptime_days': info.get('uptime_in_days', 0)
            }
        except:
            redis_info = {'note': 'Redis info not available'}

        health_status['services']['redis'] = {
            'status': 'healthy',
            'response_time_ms': round(redis_time * 1000, 2),
            'details': redis_info
        }
        health_status['performance']['redis_response_ms'] = round(redis_time * 1000, 2)
    except Exception as e:
        redis_time = time.time() - redis_start
        health_status['services']['redis'] = {
            'status': 'unhealthy',
            'response_time_ms': round(redis_time * 1000, 2),
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
        logger.error(f"Redis health check failed: {str(e)}")

    # Check Celery workers
    celery_start = time.time()
    try:
        from azure_advisor_reports.celery import app as celery_app

        broker_url = celery_app.conf.broker_url
        celery_details = {
            'broker_url': broker_url.split('@')[-1] if '@' in broker_url else broker_url,
            'task_serializer': celery_app.conf.task_serializer,
            'result_backend': celery_app.conf.result_backend.split('@')[-1] if '@' in celery_app.conf.result_backend else celery_app.conf.result_backend
        }

        # Try to check for active workers
        try:
            inspect = celery_app.control.inspect(timeout=2.0)
            stats = inspect.stats()
            active_tasks = inspect.active()

            celery_time = time.time() - celery_start

            if stats:
                worker_count = len(stats)
                total_active_tasks = sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0

                health_status['services']['celery'] = {
                    'status': 'healthy',
                    'response_time_ms': round(celery_time * 1000, 2),
                    'details': {
                        **celery_details,
                        'workers_count': worker_count,
                        'active_tasks': total_active_tasks,
                        'workers': list(stats.keys())
                    }
                }
            else:
                health_status['services']['celery'] = {
                    'status': 'degraded',
                    'response_time_ms': round(celery_time * 1000, 2),
                    'details': {
                        **celery_details,
                        'workers_count': 0,
                        'message': 'No workers available'
                    }
                }
                if health_status['status'] == 'healthy':
                    health_status['status'] = 'degraded'

        except Exception as worker_error:
            celery_time = time.time() - celery_start
            health_status['services']['celery'] = {
                'status': 'degraded',
                'response_time_ms': round(celery_time * 1000, 2),
                'details': {
                    **celery_details,
                    'message': 'Configured but no workers responding',
                    'error': str(worker_error)
                }
            }
            if health_status['status'] == 'healthy':
                health_status['status'] = 'degraded'

        health_status['performance']['celery_response_ms'] = round(celery_time * 1000, 2)

    except Exception as e:
        celery_time = time.time() - celery_start
        health_status['services']['celery'] = {
            'status': 'unhealthy',
            'response_time_ms': round(celery_time * 1000, 2),
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
        logger.error(f"Celery health check failed: {str(e)}")

    # Calculate total response time
    total_time = time.time() - start_time
    health_status['performance']['total_response_ms'] = round(total_time * 1000, 2)

    # Determine HTTP status code
    if health_status['status'] == 'healthy':
        response_status = status.HTTP_200_OK
    elif health_status['status'] == 'degraded':
        response_status = status.HTTP_200_OK  # Still operational
    else:
        response_status = status.HTTP_503_SERVICE_UNAVAILABLE

    return Response(health_status, status=response_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def monitoring_dashboard(request):
    """
    Monitoring dashboard endpoint providing system metrics and statistics.

    Returns:
    - Service health summary
    - Application statistics
    - System information
    """
    try:
        from apps.authentication.models import User
        from apps.clients.models import Client
        from apps.reports.models import Report

        dashboard_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'statistics': {
                'users': {
                    'total': User.objects.count(),
                    'active': User.objects.filter(is_active=True).count()
                },
                'clients': {
                    'total': Client.objects.count(),
                    'active': Client.objects.filter(status='active').count()
                },
                'reports': {
                    'total': Report.objects.count(),
                    'pending': Report.objects.filter(status='pending').count(),
                    'processing': Report.objects.filter(status='processing').count(),
                    'completed': Report.objects.filter(status='completed').count(),
                    'failed': Report.objects.filter(status='failed').count()
                }
            },
            'environment': {
                'debug_mode': settings.DEBUG,
                'django_version': settings.DJANGO_VERSION if hasattr(settings, 'DJANGO_VERSION') else 'unknown',
                'python_version': settings.PYTHON_VERSION if hasattr(settings, 'PYTHON_VERSION') else 'unknown'
            }
        }

        return Response(dashboard_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Monitoring dashboard error: {str(e)}")
        return Response(
            {
                'error': 'Failed to retrieve monitoring data',
                'detail': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )