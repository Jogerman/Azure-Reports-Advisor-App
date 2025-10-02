"""
Clients application configuration.
"""

from django.apps import AppConfig


class ClientsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.clients'
    verbose_name = 'Client Management'

    def ready(self):
        # Import signal handlers if any
        pass