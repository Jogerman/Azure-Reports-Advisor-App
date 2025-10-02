"""
Celery configuration for azure_advisor_reports project.

Windows Compatibility Notes:
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
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings.development')

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
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,

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
    """Configure workers on initialization."""
    pass

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