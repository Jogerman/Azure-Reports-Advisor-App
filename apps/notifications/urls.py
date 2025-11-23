"""
Notification System URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EmailNotificationViewSet,
    WebhookViewSet,
    WebhookDeliveryViewSet,
    InAppNotificationViewSet,
    NotificationViewSet
)

app_name = 'notifications'

router = DefaultRouter()
router.register(r'emails', EmailNotificationViewSet, basename='email-notification')
router.register(r'webhooks', WebhookViewSet, basename='webhook')
router.register(r'webhook-deliveries', WebhookDeliveryViewSet, basename='webhook-delivery')
router.register(r'inapp', InAppNotificationViewSet, basename='inapp-notification')
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
