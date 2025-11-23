"""
Notification System Admin Interface
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import (
    EmailNotification,
    Webhook,
    WebhookDelivery,
    InAppNotification
)


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    """Admin interface for email notifications"""

    list_display = [
        'id',
        'to_email',
        'subject',
        'notification_type',
        'priority',
        'status_badge',
        'opened',
        'clicked',
        'created_at'
    ]
    list_filter = [
        'notification_type',
        'priority',
        'sent',
        'failed',
        'opened',
        'clicked',
        'created_at'
    ]
    search_fields = [
        'to_email',
        'subject',
        'message',
        'id'
    ]
    readonly_fields = [
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
        'updated_at'
    ]
    fieldsets = (
        ('Recipients', {
            'fields': ('to_email', 'cc_emails', 'bcc_emails')
        }),
        ('Content', {
            'fields': ('subject', 'message', 'html_message')
        }),
        ('Classification', {
            'fields': ('notification_type', 'priority', 'user')
        }),
        ('Status', {
            'fields': (
                'sent',
                'sent_at',
                'failed',
                'error_message',
                'retry_count'
            )
        }),
        ('Tracking', {
            'fields': (
                'opened',
                'opened_at',
                'clicked',
                'clicked_at'
            )
        }),
        ('Metadata', {
            'fields': ('context_data', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def status_badge(self, obj):
        """Display status with color badge"""
        if obj.failed:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 7px; border-radius: 3px;">Failed</span>'
            )
        elif obj.sent:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 7px; border-radius: 3px;">Sent</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 7px; border-radius: 3px;">Pending</span>'
            )

    status_badge.short_description = 'Status'

    def has_add_permission(self, request):
        """Prevent manual creation through admin"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only admins can delete"""
        return request.user.is_superuser


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    """Admin interface for webhooks"""

    list_display = [
        'name',
        'url',
        'method',
        'active_badge',
        'verified_badge',
        'failure_count',
        'last_triggered_at',
        'created_at'
    ]
    list_filter = [
        'active',
        'verified',
        'method',
        'created_at'
    ]
    search_fields = [
        'name',
        'url',
        'id'
    ]
    readonly_fields = [
        'id',
        'verified',
        'last_triggered_at',
        'failure_count',
        'created_at',
        'updated_at',
        'view_deliveries_link'
    ]
    fieldsets = (
        ('Configuration', {
            'fields': ('name', 'url', 'secret', 'events')
        }),
        ('Request Settings', {
            'fields': ('method', 'headers', 'timeout')
        }),
        ('Status', {
            'fields': (
                'active',
                'verified',
                'last_triggered_at',
                'failure_count',
                'max_failures'
            )
        }),
        ('Ownership', {
            'fields': ('created_by',)
        }),
        ('Deliveries', {
            'fields': ('view_deliveries_link',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    filter_horizontal = []

    def active_badge(self, obj):
        """Display active status with badge"""
        if obj.active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 7px; border-radius: 3px;">Active</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 7px; border-radius: 3px;">Inactive</span>'
            )

    active_badge.short_description = 'Active'

    def verified_badge(self, obj):
        """Display verified status with badge"""
        if obj.verified:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 3px 7px; border-radius: 3px;">Verified</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 7px; border-radius: 3px;">Unverified</span>'
            )

    verified_badge.short_description = 'Verified'

    def view_deliveries_link(self, obj):
        """Link to view webhook deliveries"""
        if obj.pk:
            url = reverse('admin:notifications_webhookdelivery_changelist')
            return format_html(
                '<a href="{}?webhook__id__exact={}" target="_blank">View Deliveries</a>',
                url,
                obj.id
            )
        return '-'

    view_deliveries_link.short_description = 'Deliveries'


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    """Admin interface for webhook deliveries"""

    list_display = [
        'id',
        'webhook_link',
        'event_type',
        'status_badge',
        'status_code',
        'duration_ms',
        'retry_count',
        'created_at'
    ]
    list_filter = [
        'success',
        'event_type',
        'created_at'
    ]
    search_fields = [
        'webhook__name',
        'event_type',
        'id'
    ]
    readonly_fields = [
        'id',
        'webhook',
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
        'created_at'
    ]
    fieldsets = (
        ('Webhook', {
            'fields': ('webhook', 'event_type')
        }),
        ('Request', {
            'fields': ('payload',)
        }),
        ('Response', {
            'fields': (
                'status_code',
                'response_body',
                'response_headers',
                'success',
                'error_message',
                'duration_ms'
            )
        }),
        ('Retry', {
            'fields': ('retry_count', 'next_retry_at')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def webhook_link(self, obj):
        """Link to webhook"""
        url = reverse('admin:notifications_webhook_change', args=[obj.webhook.id])
        return format_html('<a href="{}">{}</a>', url, obj.webhook.name)

    webhook_link.short_description = 'Webhook'

    def status_badge(self, obj):
        """Display status with badge"""
        if obj.success:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 7px; border-radius: 3px;">Success</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 7px; border-radius: 3px;">Failed</span>'
            )

    status_badge.short_description = 'Status'

    def has_add_permission(self, request):
        """Prevent manual creation"""
        return False

    def has_change_permission(self, request, obj=None):
        """Read-only"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only admins can delete"""
        return request.user.is_superuser


@admin.register(InAppNotification)
class InAppNotificationAdmin(admin.ModelAdmin):
    """Admin interface for in-app notifications"""

    list_display = [
        'id',
        'user',
        'title',
        'notification_type',
        'priority',
        'read_badge',
        'action_url',
        'created_at'
    ]
    list_filter = [
        'notification_type',
        'priority',
        'read',
        'created_at'
    ]
    search_fields = [
        'user__username',
        'user__email',
        'title',
        'message',
        'id'
    ]
    readonly_fields = [
        'id',
        'read_at',
        'created_at'
    ]
    fieldsets = (
        ('Recipient', {
            'fields': ('user',)
        }),
        ('Content', {
            'fields': ('title', 'message', 'notification_type', 'priority')
        }),
        ('Action', {
            'fields': ('action_url', 'action_label')
        }),
        ('Status', {
            'fields': ('read', 'read_at')
        }),
        ('Metadata', {
            'fields': ('context_data', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def read_badge(self, obj):
        """Display read status with badge"""
        if obj.read:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 7px; border-radius: 3px;">Read</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #007bff; color: white; padding: 3px 7px; border-radius: 3px;">Unread</span>'
            )

    read_badge.short_description = 'Status'

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        """Bulk action to mark notifications as read"""
        count = queryset.filter(read=False).update(
            read=True,
            read_at=timezone.now()
        )
        self.message_user(request, f'{count} notifications marked as read')

    mark_as_read.short_description = 'Mark selected as read'

    def mark_as_unread(self, request, queryset):
        """Bulk action to mark notifications as unread"""
        count = queryset.filter(read=True).update(
            read=False,
            read_at=None
        )
        self.message_user(request, f'{count} notifications marked as unread')

    mark_as_unread.short_description = 'Mark selected as unread'
