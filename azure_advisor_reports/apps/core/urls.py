"""
Core URLs for health checks and utilities.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.health_check, name='health_check'),
    path('monitoring/', views.monitoring_dashboard, name='monitoring_dashboard'),
]