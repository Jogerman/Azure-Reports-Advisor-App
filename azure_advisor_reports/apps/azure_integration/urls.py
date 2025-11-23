"""
URL configuration for Azure Integration app.

Provides REST API endpoints for managing Azure subscriptions and integrations.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.azure_integration.views import AzureSubscriptionViewSet

app_name = 'azure_integration'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'subscriptions', AzureSubscriptionViewSet, basename='azure-subscription')

urlpatterns = [
    path('', include(router.urls)),
]
