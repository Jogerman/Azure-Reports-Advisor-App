"""
Notification System Views

REST API endpoints for notifications, webhooks, and email tracking
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from apps.security.permissions import (
    IsAdmin,
    IsManager,
    ResourcePermission,
    has_permission
)

from .models import (
    EmailNotification,
    Webhook,
    WebhookDelivery,
    InAppNotification,
    NotificationType
)
from .serializers import (
    EmailNotificationSerializer,
    EmailNotificationListSerializer,
    WebhookSerializer,
    WebhookListSerializer,
    WebhookDeliverySerializer,
    WebhookDeliveryListSerializer,
    InAppNotificationSerializer,
    InAppNotificationListSerializer,
    MarkNotificationsReadSerializer,
    SendNotificationSerializer,
    NotificationStatsSerializer,
    WebhookTestSerializer
)
from .services import (
    EmailService,
    WebhookService,
    InAppNotificationService,
    NotificationService
)

User = get_user_model()


# =============================================================================
# Email Notifications ViewSet
# =============================================================================

class EmailNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing email notifications

    Only admins and managers can view all email notifications
    Users can view their own notifications
    """
    queryset = EmailNotification.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'priority', 'sent', 'failed']
    search_fields = ['to_email', 'subject', 'message']
    ordering_fields = ['created_at', 'sent_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return EmailNotificationListSerializer
        return EmailNotificationSerializer

    def get_queryset(self):
        """Filter notifications based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user

        # Admins and managers see all
        if has_permission(user, ResourcePermission.VIEW_AUDIT_LOG):
            return queryset

        # Regular users see only their own
        return queryset.filter(user=user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def retry(self, request, pk=None):
        """
        Retry sending a failed email notification

        POST /api/notifications/emails/{id}/retry/
        """
        notification = self.get_object()

        if not notification.failed:
            return Response(
                {'error': 'This notification did not fail'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retry sending
        try:
            result = EmailService.send_email(
                to_email=notification.to_email,
                subject=notification.subject,
                message=notification.message,
                html_message=notification.html_message,
                cc_emails=notification.cc_emails,
                bcc_emails=notification.bcc_emails,
                notification_type=notification.notification_type,
                priority=notification.priority,
                user=notification.user
            )

            return Response(
                EmailNotificationSerializer(result).data,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =============================================================================
# Webhooks ViewSet
# =============================================================================

class WebhookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing webhooks

    Users can create and manage their own webhooks
    Admins can view and manage all webhooks
    """
    queryset = Webhook.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['active', 'verified']
    search_fields = ['name', 'url']
    ordering_fields = ['created_at', 'last_triggered_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return WebhookListSerializer
        return WebhookSerializer

    def get_queryset(self):
        """Filter webhooks based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user

        # Admins see all webhooks
        if has_permission(user, ResourcePermission.MANAGE_SETTINGS):
            return queryset

        # Regular users see only their own webhooks
        return queryset.filter(created_by=user)

    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Test a webhook by sending a test event

        POST /api/notifications/webhooks/{id}/test/
        Body: {
            "event_type": "test.event",
            "payload": {"test": true}
        }
        """
        webhook = self.get_object()
        serializer = WebhookTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event_type = serializer.validated_data.get('event_type', 'test.event')
        payload = serializer.validated_data.get('payload', {
            'test': True,
            'timestamp': timezone.now().isoformat(),
            'user': request.user.username
        })

        # Send test webhook
        delivery = WebhookService._send_webhook(webhook, event_type, payload)

        return Response(
            WebhookDeliverySerializer(delivery).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a webhook

        POST /api/notifications/webhooks/{id}/activate/
        """
        webhook = self.get_object()
        webhook.active = True
        webhook.failure_count = 0
        webhook.save()

        return Response(
            WebhookSerializer(webhook).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a webhook

        POST /api/notifications/webhooks/{id}/deactivate/
        """
        webhook = self.get_object()
        webhook.active = False
        webhook.save()

        return Response(
            WebhookSerializer(webhook).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def deliveries(self, request, pk=None):
        """
        Get delivery history for a webhook

        GET /api/notifications/webhooks/{id}/deliveries/
        """
        webhook = self.get_object()
        deliveries = webhook.deliveries.all()[:100]  # Last 100 deliveries

        serializer = WebhookDeliverySerializer(deliveries, many=True)
        return Response(serializer.data)


# =============================================================================
# Webhook Deliveries ViewSet
# =============================================================================

class WebhookDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing webhook delivery logs
    """
    queryset = WebhookDelivery.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['webhook', 'event_type', 'success']
    ordering_fields = ['created_at', 'duration_ms']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return WebhookDeliveryListSerializer
        return WebhookDeliverySerializer

    def get_queryset(self):
        """Filter deliveries based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user

        # Admins see all deliveries
        if has_permission(user, ResourcePermission.MANAGE_SETTINGS):
            return queryset

        # Regular users see only their webhook deliveries
        return queryset.filter(webhook__created_by=user)


# =============================================================================
# In-App Notifications ViewSet
# =============================================================================

class InAppNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for in-app notifications

    Users can only view their own notifications
    """
    queryset = InAppNotification.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'priority', 'read']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return InAppNotificationListSerializer
        return InAppNotificationSerializer

    def get_queryset(self):
        """Users see only their own notifications"""
        return super().get_queryset().filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Get count of unread notifications

        GET /api/notifications/inapp/unread_count/
        """
        count = InAppNotificationService.get_unread_count(request.user)
        return Response({'unread_count': count})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark a notification as read

        POST /api/notifications/inapp/{id}/mark_read/
        """
        notification = self.get_object()
        notification.mark_as_read()

        return Response(
            InAppNotificationSerializer(notification).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        Mark all notifications as read

        POST /api/notifications/inapp/mark_all_read/
        Body: {
            "notification_ids": ["uuid1", "uuid2"]  # Optional
        }
        """
        serializer = MarkNotificationsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data.get('notification_ids', [])

        if notification_ids:
            # Mark specific notifications as read
            InAppNotification.objects.filter(
                id__in=notification_ids,
                user=request.user,
                read=False
            ).update(read=True, read_at=timezone.now())
            count = len(notification_ids)
        else:
            # Mark all as read
            InAppNotificationService.mark_all_as_read(request.user)
            count = InAppNotification.objects.filter(
                user=request.user,
                read=True
            ).count()

        return Response({
            'message': f'{count} notifications marked as read',
            'count': count
        })

    @action(detail=False, methods=['delete'])
    def clear_read(self, request):
        """
        Delete all read notifications

        DELETE /api/notifications/inapp/clear_read/
        """
        count = InAppNotification.objects.filter(
            user=request.user,
            read=True
        ).delete()[0]

        return Response({
            'message': f'{count} read notifications deleted',
            'count': count
        })


# =============================================================================
# Unified Notification API
# =============================================================================

class NotificationViewSet(viewsets.ViewSet):
    """
    Unified notification API for sending notifications across all channels
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], permission_classes=[IsManager])
    def send(self, request):
        """
        Send notification across multiple channels

        POST /api/notifications/send/
        Body: {
            "user_id": "uuid",
            "title": "Notification Title",
            "message": "Notification message",
            "notification_type": "custom",
            "priority": "normal",
            "send_email": true,
            "create_inapp": true,
            "trigger_webhooks": true,
            "action_url": "/path/to/action",
            "action_label": "View Details",
            "email_template": "emails/custom",
            "email_context": {}
        }
        """
        serializer = SendNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get user
        try:
            user = User.objects.get(id=serializer.validated_data['user_id'])
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Send notification
        results = NotificationService.notify(
            user=user,
            title=serializer.validated_data['title'],
            message=serializer.validated_data['message'],
            notification_type=serializer.validated_data['notification_type'],
            priority=serializer.validated_data['priority'],
            send_email=serializer.validated_data['send_email'],
            create_inapp=serializer.validated_data['create_inapp'],
            trigger_webhooks=serializer.validated_data['trigger_webhooks'],
            email_template=serializer.validated_data.get('email_template'),
            action_url=serializer.validated_data.get('action_url', ''),
            action_label=serializer.validated_data.get('action_label', ''),
            email_context=serializer.validated_data.get('email_context', {})
        )

        return Response({
            'message': 'Notification sent successfully',
            'email_sent': 'email' in results,
            'inapp_created': 'inapp' in results,
            'webhooks_triggered': len(results.get('webhooks', []))
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def stats(self, request):
        """
        Get notification statistics

        GET /api/notifications/stats/
        """
        # Email stats
        total_emails = EmailNotification.objects.count()
        emails_sent = EmailNotification.objects.filter(sent=True).count()
        emails_failed = EmailNotification.objects.filter(failed=True).count()
        emails_opened = EmailNotification.objects.filter(opened=True).count()
        emails_clicked = EmailNotification.objects.filter(clicked=True).count()

        # Webhook stats
        total_webhooks = Webhook.objects.count()
        active_webhooks = Webhook.objects.filter(active=True).count()
        webhook_deliveries = WebhookDelivery.objects.count()
        successful_deliveries = WebhookDelivery.objects.filter(success=True).count()
        failed_deliveries = WebhookDelivery.objects.filter(success=False).count()

        # In-app notification stats
        total_inapp = InAppNotification.objects.count()
        unread_notifications = InAppNotification.objects.filter(read=False).count()
        read_notifications = InAppNotification.objects.filter(read=True).count()

        # Calculate rates
        avg_email_open_rate = (emails_opened / emails_sent * 100) if emails_sent > 0 else 0
        avg_webhook_success_rate = (successful_deliveries / webhook_deliveries * 100) if webhook_deliveries > 0 else 0

        stats_data = {
            'total_emails': total_emails,
            'emails_sent': emails_sent,
            'emails_failed': emails_failed,
            'emails_opened': emails_opened,
            'emails_clicked': emails_clicked,
            'total_webhooks': total_webhooks,
            'active_webhooks': active_webhooks,
            'webhook_deliveries': webhook_deliveries,
            'successful_deliveries': successful_deliveries,
            'failed_deliveries': failed_deliveries,
            'total_inapp_notifications': total_inapp,
            'unread_notifications': unread_notifications,
            'read_notifications': read_notifications,
            'avg_email_open_rate': round(avg_email_open_rate, 2),
            'avg_webhook_success_rate': round(avg_webhook_success_rate, 2),
        }

        serializer = NotificationStatsSerializer(stats_data)
        return Response(serializer.data)
