"""
Notification System Serializers

Serializers for REST API endpoints
"""

from rest_framework import serializers
from .models import (
    EmailNotification,
    Webhook,
    WebhookDelivery,
    InAppNotification,
    NotificationType,
    NotificationPriority
)


class EmailNotificationSerializer(serializers.ModelSerializer):
    """Serializer for email notifications"""

    class Meta:
        model = EmailNotification
        fields = [
            'id',
            'to_email',
            'cc_emails',
            'bcc_emails',
            'subject',
            'message',
            'html_message',
            'notification_type',
            'priority',
            'user',
            'context_data',
            'sent',
            'sent_at',
            'failed',
            'error_message',
            'retry_count',
            'opened',
            'opened_at',
            'clicked',
            'clicked_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'sent',
            'sent_at',
            'failed',
            'error_message',
            'retry_count',
            'opened',
            'opened_at',
            'clicked',
            'clicked_at',
            'created_at',
            'updated_at',
        ]


class EmailNotificationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for email notification list"""

    class Meta:
        model = EmailNotification
        fields = [
            'id',
            'to_email',
            'subject',
            'notification_type',
            'priority',
            'sent',
            'sent_at',
            'failed',
            'created_at',
        ]


class WebhookSerializer(serializers.ModelSerializer):
    """Serializer for webhook configuration"""

    delivery_success_rate = serializers.SerializerMethodField()

    class Meta:
        model = Webhook
        fields = [
            'id',
            'name',
            'url',
            'secret',
            'events',
            'method',
            'headers',
            'timeout',
            'active',
            'verified',
            'last_triggered_at',
            'failure_count',
            'max_failures',
            'delivery_success_rate',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'verified',
            'last_triggered_at',
            'failure_count',
            'delivery_success_rate',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'secret': {'write_only': True}
        }

    def get_delivery_success_rate(self, obj) -> float:
        """Calculate delivery success rate"""
        total = obj.deliveries.count()
        if total == 0:
            return 0.0

        successful = obj.deliveries.filter(success=True).count()
        return round((successful / total) * 100, 2)


class WebhookListSerializer(serializers.ModelSerializer):
    """Simplified serializer for webhook list"""

    class Meta:
        model = Webhook
        fields = [
            'id',
            'name',
            'url',
            'events',
            'active',
            'last_triggered_at',
            'failure_count',
            'created_at',
        ]


class WebhookDeliverySerializer(serializers.ModelSerializer):
    """Serializer for webhook delivery logs"""

    webhook_name = serializers.CharField(source='webhook.name', read_only=True)
    webhook_url = serializers.CharField(source='webhook.url', read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = [
            'id',
            'webhook',
            'webhook_name',
            'webhook_url',
            'event_type',
            'payload',
            'status_code',
            'response_body',
            'response_headers',
            'success',
            'error_message',
            'duration_ms',
            'retry_count',
            'next_retry_at',
            'created_at',
        ]
        read_only_fields = '__all__'


class WebhookDeliveryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for webhook delivery list"""

    webhook_name = serializers.CharField(source='webhook.name', read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = [
            'id',
            'webhook_name',
            'event_type',
            'success',
            'status_code',
            'duration_ms',
            'created_at',
        ]


class InAppNotificationSerializer(serializers.ModelSerializer):
    """Serializer for in-app notifications"""

    class Meta:
        model = InAppNotification
        fields = [
            'id',
            'user',
            'title',
            'message',
            'notification_type',
            'priority',
            'action_url',
            'action_label',
            'read',
            'read_at',
            'context_data',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'read_at',
            'created_at',
        ]


class InAppNotificationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for notification list"""

    class Meta:
        model = InAppNotification
        fields = [
            'id',
            'title',
            'message',
            'notification_type',
            'priority',
            'action_url',
            'action_label',
            'read',
            'created_at',
        ]


class MarkNotificationsReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""

    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text='List of notification IDs to mark as read. If empty, marks all as read.'
    )


class SendNotificationSerializer(serializers.Serializer):
    """Serializer for sending notifications via API"""

    user_id = serializers.UUIDField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    message = serializers.CharField(required=True)
    notification_type = serializers.ChoiceField(
        choices=NotificationType.choices,
        default=NotificationType.CUSTOM
    )
    priority = serializers.ChoiceField(
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL
    )
    send_email = serializers.BooleanField(default=True)
    create_inapp = serializers.BooleanField(default=True)
    trigger_webhooks = serializers.BooleanField(default=True)
    action_url = serializers.CharField(max_length=500, required=False, allow_blank=True)
    action_label = serializers.CharField(max_length=100, required=False, allow_blank=True)
    email_template = serializers.CharField(required=False, allow_blank=True)
    email_context = serializers.JSONField(required=False, default=dict)


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""

    total_emails = serializers.IntegerField()
    emails_sent = serializers.IntegerField()
    emails_failed = serializers.IntegerField()
    emails_opened = serializers.IntegerField()
    emails_clicked = serializers.IntegerField()

    total_webhooks = serializers.IntegerField()
    active_webhooks = serializers.IntegerField()
    webhook_deliveries = serializers.IntegerField()
    successful_deliveries = serializers.IntegerField()
    failed_deliveries = serializers.IntegerField()

    total_inapp_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    read_notifications = serializers.IntegerField()

    avg_email_open_rate = serializers.FloatField()
    avg_webhook_success_rate = serializers.FloatField()


class WebhookTestSerializer(serializers.Serializer):
    """Serializer for testing webhooks"""

    webhook_id = serializers.UUIDField(required=True)
    event_type = serializers.CharField(required=False, default='test.event')
    payload = serializers.JSONField(required=False, default=dict)
