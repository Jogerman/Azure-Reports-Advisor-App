"""
Celery configuration for azure_advisor_reports project.

Production Configuration:
- Uses gevent pool for better concurrency with I/O-bound tasks
- 4 concurrent greenlets per worker (configurable via worker_concurrency)
- Auto-scaling: 2-5 worker replicas in Azure Container Apps
- Effective concurrency: 8-20 tasks simultaneously (2-5 workers × 4 greenlets)

Windows Development Notes:
- On Windows, use 'solo' pool: celery -A azure_advisor_reports worker -l info -P solo
- Or use gevent pool: celery -A azure_advisor_reports worker -l info -P gevent
- Default pool (prefork) doesn't work on Windows
"""

import os
import sys
from celery import Celery
from celery.signals import worker_process_init
from kombu import Exchange, Queue

# Set the default Django settings module for the 'celery' program.
# Use environment variable to determine settings module, with intelligent defaults
environment = os.environ.get('DJANGO_ENVIRONMENT', 'development').lower()
if environment == 'production':
    settings_module = 'azure_advisor_reports.settings.production'
elif environment == 'staging':
    settings_module = 'azure_advisor_reports.settings.staging'
else:
    settings_module = 'azure_advisor_reports.settings.development'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

# Create Celery app
app = Celery('azure_advisor_reports')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure task queues
app.conf.task_queues = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('reports', Exchange('reports'), routing_key='reports.#'),
    Queue('priority', Exchange('priority'), routing_key='priority.#', priority=10),
)

# Configure task routes
app.conf.task_routes = {
    'apps.reports.tasks.*': {'queue': 'reports'},
    'apps.reports.tasks.process_csv_file': {'queue': 'priority', 'priority': 9},
    'apps.reports.tasks.generate_report': {'queue': 'reports', 'priority': 8},
}

# Celery configuration
app.conf.update(
    # Task configuration
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes hard limit
    task_soft_time_limit=1500,  # 25 minutes soft limit
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Result backend
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },

    # Worker configuration
    worker_prefetch_multiplier=4,  # Increased for gevent pool (4 concurrent tasks per worker)
    worker_max_tasks_per_child=1000,
    worker_pool='gevent',  # Use gevent pool for better concurrency with I/O-bound tasks
    worker_concurrency=4,  # Number of concurrent greenlets per worker

    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    # Windows-specific settings
    # Note: These are automatically adjusted when running on Windows
    worker_pool_restarts=True,
)

# Signal handlers
@worker_process_init.connect
def configure_workers(sender=None, conf=None, **kwargs):
    """
    Configure workers on initialization.

    This runs when each worker process starts, ensuring Django settings
    are properly loaded and database connection is available.
    """
    import logging
    from django.conf import settings
    from django.db import connection

    logger = logging.getLogger('celery.worker')

    # Log the settings module being used
    settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'UNKNOWN')
    logger.info(f"Worker initialized with settings module: {settings_module}")

    # Verify database configuration is loaded
    try:
        db_config = settings.DATABASES['default']
        db_engine = db_config.get('ENGINE', 'UNKNOWN')
        db_name = db_config.get('NAME', 'UNKNOWN')
        logger.info(f"Database engine: {db_engine}")
        logger.info(f"Database name: {db_name}")

        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        logger.info("Database connection successful")

    except Exception as e:
        logger.error(f"Database configuration error: {e}")
        logger.error(f"DATABASES setting: {getattr(settings, 'DATABASES', 'NOT SET')}")
        # Don't raise - let tasks fail individually so we can see better error messages

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')
    return 'Debug task completed'

@app.task(bind=True)
def health_check_task(self):
    """Health check task to verify Celery is working."""
    import datetime
    return {
        'status': 'healthy',
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'worker': self.request.hostname,
    }