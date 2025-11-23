from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.monitoring'
    verbose_name = 'Monitoring & Observability'

    def ready(self):
        # Import signal handlers and monitoring setup
        from . import telemetry
        telemetry.setup_telemetry()
