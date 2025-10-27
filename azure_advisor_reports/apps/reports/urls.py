"""
URL configuration for reports app.
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

# Create router and register viewsets
router = DefaultRouter()
router.register(r'', ReportViewSet, basename='report')  # Empty prefix since /reports/ is already in main urls.py
router.register(r'recommendations', RecommendationViewSet, basename='recommendation')
router.register(r'templates', ReportTemplateViewSet, basename='template')
router.register(r'shares', ReportShareViewSet, basename='share')

urlpatterns = [
    path('', include(router.urls)),
]