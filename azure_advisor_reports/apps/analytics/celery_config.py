"""
Celery Beat schedule configuration for analytics tasks.

This file defines the periodic task schedules for the analytics module.
Add this configuration to your main celery.py or settings.py file.
"""

from celery.schedules import crontab

# Celery Beat Schedule for Analytics Tasks
ANALYTICS_CELERY_BEAT_SCHEDULE = {
    # Calculate and cache all analytics metrics daily at 2:00 AM
    'calculate-daily-metrics': {
        'task': 'analytics.calculate_daily_metrics',
        'schedule': crontab(hour=2, minute=0),
        'options': {
            'expires': 3600,  # Task expires after 1 hour
        }
    },

    # Cleanup old user activities weekly on Sunday at 3:00 AM
    'cleanup-old-activities': {
        'task': 'analytics.cleanup_old_activities',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday
        'kwargs': {'days': 90},  # Delete activities older than 90 days
        'options': {
            'expires': 7200,  # Task expires after 2 hours
        }
    },

    # Calculate dashboard metrics for different periods daily at 1:00 AM
    'calculate-dashboard-metrics-periodic': {
        'task': 'analytics.calculate_dashboard_metrics_periodic',
        'schedule': crontab(hour=1, minute=0),
        'options': {
            'expires': 3600,
        }
    },

    # Cleanup old system health metrics weekly on Sunday at 4:00 AM
    'cleanup-old-system-metrics': {
        'task': 'analytics.cleanup_old_system_metrics',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),
        'kwargs': {'days': 30},  # Keep only last 30 days
        'options': {
            'expires': 3600,
        }
    },

    # Update hourly report usage statistics
    'update-report-usage-stats': {
        'task': 'analytics.update_report_usage_stats',
        'schedule': crontab(minute=5),  # Run at 5 minutes past every hour
        'options': {
            'expires': 1800,  # Task expires after 30 minutes
        }
    },

    # Generate weekly analytics report every Monday at 9:00 AM
    'generate-weekly-report': {
        'task': 'analytics.generate_weekly_report',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Monday
        'options': {
            'expires': 3600,
        }
    },
}


# Example of how to integrate into settings.py:
"""
# In your azure_advisor_reports/settings.py file:

from apps.analytics.celery_config import ANALYTICS_CELERY_BEAT_SCHEDULE

# Merge with existing CELERY_BEAT_SCHEDULE
CELERY_BEAT_SCHEDULE = {
    **CELERY_BEAT_SCHEDULE,  # Existing schedules
    **ANALYTICS_CELERY_BEAT_SCHEDULE,  # Analytics schedules
}
"""

# Alternative: Direct configuration example
EXAMPLE_CELERY_BEAT_CONFIG = {
    'broker_url': 'redis://localhost:6379/0',
    'result_backend': 'redis://localhost:6379/0',
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    'beat_schedule': ANALYTICS_CELERY_BEAT_SCHEDULE,
}
