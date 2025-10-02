"""
Authentication application configuration.
"""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'
    verbose_name = 'Authentication & User Management'

    def ready(self):
        # Import signal handlers if any
        pass