"""
Django Admin configuration for Audit models
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import AuditLog, SecurityEvent, DataAccessLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for viewing audit logs (read-only)
    """
    list_display = [
        'timestamp',
        'colored_severity',
        'action_display',
        'user_link',
        'resource_display',
        'colored_success',
        'duration_display',
        'ip_address',
    ]
    list_filter = [
        'action',
        'severity',
        'success',
        'timestamp',
        'resource_type',
    ]
    search_fields = [
        'username',
        'user_email',
        'resource_name',
        'resource_id',
        'ip_address',
        'action_description',
    ]
    readonly_fields = [
        'id',
        'timestamp',
        'user',
        'username',
        'user_email',
        'user_role',
        'action',
        'action_description',
        'severity',
        'resource_type',
        'resource_id',
        'resource_name',
        'formatted_changes',
        'formatted_metadata',
        'ip_address',
        'user_agent',
        'request_path',
        'request_method',
        'session_id',
        'success',
        'error_message',
        'status_code',
        'duration_ms',
        'retention_date',
        'tags',
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    list_per_page = 50

    fieldsets = (
        ('When', {
            'fields': ('id', 'timestamp', 'retention_date')
        }),
        ('Who', {
            'fields': ('user', 'username', 'user_email', 'user_role')
        }),
        ('What', {
            'fields': ('action', 'action_description', 'severity', 'tags')
        }),
        ('Resource', {
            'fields': ('resource_type', 'resource_id', 'resource_name')
        }),
        ('Changes', {
            'fields': ('formatted_changes', 'formatted_metadata'),
            'classes': ('collapse',)
        }),
        ('Request Context', {
            'fields': (
                'ip_address',
                'user_agent',
                'request_path',
                'request_method',
                'session_id'
            ),
            'classes': ('collapse',)
        }),
        ('Outcome', {
            'fields': ('success', 'error_message', 'status_code', 'duration_ms')
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of audit logs"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs"""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent modification of audit logs"""
        return False

    def colored_severity(self, obj):
        """Display severity with color coding"""
        colors = {
            'low': '#10B981',
            'medium': '#F59E0B',
            'high': '#EF4444',
            'critical': '#DC2626',
        }
        color = colors.get(obj.severity, '#6B7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_severity_display()
        )
    colored_severity.short_description = 'Severity'

    def action_display(self, obj):
        """Display action with icon"""
        return format_html(
            '<span title="{}">{}</span>',
            obj.action_description or '',
            obj.get_action_display()
        )
    action_display.short_description = 'Action'

    def user_link(self, obj):
        """Display user with link to user admin"""
        if obj.user:
            url = reverse('admin:authentication_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.username)
        return obj.username or 'System'
    user_link.short_description = 'User'

    def resource_display(self, obj):
        """Display resource information"""
        if obj.resource_type and obj.resource_name:
            return format_html(
                '<strong>{}</strong><br/><small>{}</small>',
                obj.resource_name,
                obj.resource_type
            )
        return '-'
    resource_display.short_description = 'Resource'

    def colored_success(self, obj):
        """Display success status with color"""
        if obj.success:
            return format_html(
                '<span style="color: #10B981;">✓ Success</span>'
            )
        else:
            return format_html(
                '<span style="color: #EF4444;">✗ Failed</span>'
            )
    colored_success.short_description = 'Status'

    def duration_display(self, obj):
        """Display duration in human-readable format"""
        if obj.duration_ms is None:
            return '-'

        if obj.duration_ms < 1000:
            return f'{obj.duration_ms}ms'
        else:
            return f'{obj.duration_ms / 1000:.2f}s'
    duration_display.short_description = 'Duration'

    def formatted_changes(self, obj):
        """Display changes in formatted JSON"""
        if not obj.changes:
            return 'No changes'

        json_str = json.dumps(obj.changes, indent=2)
        return format_html('<pre style="max-height: 400px; overflow: auto;">{}</pre>', json_str)
    formatted_changes.short_description = 'Changes'

    def formatted_metadata(self, obj):
        """Display metadata in formatted JSON"""
        if not obj.metadata:
            return 'No metadata'

        json_str = json.dumps(obj.metadata, indent=2)
        return format_html('<pre style="max-height: 400px; overflow: auto;">{}</pre>', json_str)
    formatted_metadata.short_description = 'Metadata'


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """
    Admin interface for security events
    """
    list_display = [
        'timestamp',
        'colored_severity',
        'event_type',
        'user_attempted',
        'ip_address',
        'resolved_status',
        'alert_status',
    ]
    list_filter = [
        'event_type',
        'severity',
        'resolved',
        'alert_sent',
        'timestamp',
    ]
    search_fields = [
        'event_type',
        'username_attempted',
        'ip_address',
        'description',
    ]
    readonly_fields = [
        'id',
        'timestamp',
        'event_type',
        'severity',
        'user',
        'username_attempted',
        'ip_address',
        'user_agent',
        'description',
        'formatted_details',
        'alert_sent',
        'alert_sent_at',
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

    fields = [
        'id',
        'timestamp',
        'event_type',
        'colored_severity',
        'user',
        'username_attempted',
        'ip_address',
        'user_agent',
        'description',
        'formatted_details',
        'resolved',
        'resolved_at',
        'resolved_by',
        'resolution_notes',
        'alert_sent',
        'alert_sent_at',
    ]

    def colored_severity(self, obj):
        """Display severity with color coding"""
        colors = {
            'low': '#10B981',
            'medium': '#F59E0B',
            'high': '#EF4444',
            'critical': '#DC2626',
        }
        color = colors.get(obj.severity, '#6B7280')
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 14px;">{}</span>',
            color,
            obj.get_severity_display().upper()
        )
    colored_severity.short_description = 'Severity'

    def user_attempted(self, obj):
        """Display attempted username"""
        if obj.user:
            return format_html('<strong>{}</strong>', obj.user.username)
        return obj.username_attempted or 'Unknown'
    user_attempted.short_description = 'User'

    def resolved_status(self, obj):
        """Display resolution status"""
        if obj.resolved:
            return format_html(
                '<span style="color: #10B981;">✓ Resolved</span><br/>'
                '<small>{}</small>',
                obj.resolved_at.strftime('%Y-%m-%d %H:%M') if obj.resolved_at else ''
            )
        return format_html('<span style="color: #EF4444;">⚠ Unresolved</span>')
    resolved_status.short_description = 'Resolution'

    def alert_status(self, obj):
        """Display alert status"""
        if obj.alert_sent:
            return format_html(
                '<span style="color: #10B981;">✓ Sent</span><br/>'
                '<small>{}</small>',
                obj.alert_sent_at.strftime('%Y-%m-%d %H:%M') if obj.alert_sent_at else ''
            )
        return format_html('<span style="color: #F59E0B;">⚠ Pending</span>')
    alert_status.short_description = 'Alert'

    def formatted_details(self, obj):
        """Display details in formatted JSON"""
        if not obj.details:
            return 'No details'

        json_str = json.dumps(obj.details, indent=2)
        return format_html('<pre style="max-height: 400px; overflow: auto;">{}</pre>', json_str)
    formatted_details.short_description = 'Details'

    def has_add_permission(self, request):
        """Only allow creation through code"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of security events"""
        return request.user.is_superuser


@admin.register(DataAccessLog)
class DataAccessLogAdmin(admin.ModelAdmin):
    """
    Admin interface for data access logs
    """
    list_display = [
        'timestamp',
        'username',
        'access_type',
        'data_type',
        'data_description',
        'ip_address',
    ]
    list_filter = [
        'access_type',
        'data_type',
        'timestamp',
    ]
    search_fields = [
        'username',
        'data_type',
        'data_id',
        'data_description',
        'purpose',
    ]
    readonly_fields = [
        'id',
        'timestamp',
        'user',
        'username',
        'data_type',
        'data_id',
        'data_description',
        'access_type',
        'ip_address',
        'purpose',
        'retention_date',
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

    def has_add_permission(self, request):
        """Only allow creation through code"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of data access logs"""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent modification of data access logs"""
        return False
