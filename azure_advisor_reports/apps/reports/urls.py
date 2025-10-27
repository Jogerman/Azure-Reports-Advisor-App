"""
URL configuration for Reports app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportViewSet,
    RecommendationViewSet,
    ReportTemplateViewSet,
    ReportShareViewSet,
)

app_name = 'reports'

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'recommendations', RecommendationViewSet, basename='recommendation')
router.register(r'templates', ReportTemplateViewSet, basename='template')
router.register(r'shares', ReportShareViewSet, basename='share')

urlpatterns = [
    path('', include(router.urls)),
]
