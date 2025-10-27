"""
Reports application configuration.
"""

from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reports'
    verbose_name = 'Report Management'

    def ready(self):
        # Import signal handlers if any
        pass