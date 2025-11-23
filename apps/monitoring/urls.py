"""
URL Configuration for Monitoring Endpoints
"""

from django.urls import path
from . import health_checks

app_name = 'monitoring'

urlpatterns = [
    # Health check endpoints
    path('health/', health_checks.health_check, name='health'),
    path('health/ready/', health_checks.readiness_check, name='readiness'),
    path('health/live/', health_checks.liveness_check, name='liveness'),
    path('metrics/', health_checks.metrics_endpoint, name='metrics'),
]
