"""
Django app configuration for azure_integration.
"""

from django.apps import AppConfig


class AzureIntegrationConfig(AppConfig):
    """Configuration for Azure Integration app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.azure_integration'
    verbose_name = 'Azure Integration'

    def ready(self):
        """
        Import signal handlers when the app is ready.
        """
        # Import signals here when needed
        pass
