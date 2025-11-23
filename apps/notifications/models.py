"""
Notification System Models

Supports email notifications, webhooks, and in-app notifications
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class NotificationType(models.TextChoices):
    """Notification type choices"""
    REPORT_COMPLETED = 'report_completed', 'Report Completed'
    REPORT_FAILED = 'report_failed', 'Report Failed'
    CSV_PROCESSED = 'csv_processed', 'CSV Processed'
    USER_INVITED = 'user_invited', 'User Invited'
    SYSTEM_ALERT = 'system_alert', 'System Alert'
    CUSTOM = 'custom', 'Custom Notification'


class NotificationPriority(models.TextChoices):
    """Notification priority levels"""
    LOW = 'low', 'Low'
    NORMAL = 'normal', 'Normal'
    HIGH = 'high', 'High'
    URGENT = 'urgent', 'Urgent'


class EmailNotification(models.Model):
    """
    Email notification model
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Recipients
    to_email = models.EmailField()
    cc_emails = models.JSONField(default=list, blank=True)
    bcc_emails = models.JSONField(default=list, blank=True)

    # Content
    subject = models.CharField(max_length=255)
    message = models.TextField()
    html_message = models.TextField(blank=True)

    # Metadata
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.CUSTOM
    )
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL
    )

    # Related objects
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_notifications'
    )
    context_data = models.JSONField(default=dict, blank=True)

    # Status
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    failed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)

    # Tracking
    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'email_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sent', 'created_at']),
            models.Index(fields=['notification_type', 'sent']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f'{self.subject} to {self.to_email}'

    def mark_as_sent(self):
        """Mark notification as sent"""
        self.sent = True
        self.sent_at = timezone.now()
        self.save(update_fields=['sent', 'sent_at', 'updated_at'])

    def mark_as_failed(self, error: str):
        """Mark notification as failed"""
        self.failed = True
        self.error_message = error
        self.retry_count += 1
        self.save(update_fields=['failed', 'error_message', 'retry_count', 'updated_at'])


class Webhook(models.Model):
    """
    Webhook configuration model
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Configuration
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    secret = models.CharField(max_length=255, blank=True)

    # Events to trigger
    events = models.JSONField(
        default=list,
        help_text='List of event types that trigger this webhook'
    )

    # Request configuration
    method = models.CharField(
        max_length=10,
        default='POST',
        choices=[
            ('POST', 'POST'),
            ('PUT', 'PUT'),
            ('PATCH', 'PATCH'),
        ]
    )
    headers = models.JSONField(default=dict, blank=True)
    timeout = models.IntegerField(default=30, help_text='Timeout in seconds')

    # Status
    active = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    failure_count = models.IntegerField(default=0)
    max_failures = models.IntegerField(default=10)

    # Ownership
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='webhooks'
    )

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'webhooks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['active', 'created_at']),
            models.Index(fields=['created_by', '-created_at']),
        ]

    def __str__(self):
        return f'{self.name} - {self.url}'

    def should_trigger_for_event(self, event_type: str) -> bool:
        """Check if webhook should trigger for event"""
        return self.active and event_type in self.events


class WebhookDelivery(models.Model):
    """
    Webhook delivery log
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Webhook
    webhook = models.ForeignKey(
        Webhook,
        on_delete=models.CASCADE,
        related_name='deliveries'
    )

    # Event
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()

    # Response
    status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    response_headers = models.JSONField(default=dict, blank=True)

    # Status
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)

    # Retry
    retry_count = models.IntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    # Timestamp
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'webhook_deliveries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['webhook', '-created_at']),
            models.Index(fields=['success', 'created_at']),
            models.Index(fields=['next_retry_at']),
        ]

    def __str__(self):
        return f'{self.webhook.name} - {self.event_type} - {self.created_at}'


class InAppNotification(models.Model):
    """
    In-app notification model
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Recipient
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    # Content
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.CUSTOM
    )
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL
    )

    # Action
    action_url = models.CharField(max_length=500, blank=True)
    action_label = models.CharField(max_length=100, blank=True)

    # Status
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    context_data = models.JSONField(default=dict, blank=True)

    # Timestamp
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'inapp_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read', '-created_at']),
            models.Index(fields=['notification_type', '-created_at']),
        ]

    def __str__(self):
        return f'{self.title} for {self.user.username}'

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save(update_fields=['read', 'read_at'])
