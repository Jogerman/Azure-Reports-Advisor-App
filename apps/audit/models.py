"""
Audit Trail Models for Azure Advisor Reports Platform

This module provides comprehensive audit logging for all user actions,
system events, and data modifications. Supports compliance requirements
for SOC 2, HIPAA, GDPR, and other regulatory frameworks.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from typing import Any, Dict, Optional

User = get_user_model()


class AuditAction(models.TextChoices):
    """
    Predefined audit action types for categorization and filtering
    """
    # Authentication & Authorization
    LOGIN = 'login', 'User Login'
    LOGOUT = 'logout', 'User Logout'
    LOGIN_FAILED = 'login_failed', 'Failed Login Attempt'
    PASSWORD_CHANGE = 'password_change', 'Password Changed'
    PASSWORD_RESET = 'password_reset', 'Password Reset'
    MFA_ENABLED = 'mfa_enabled', 'MFA Enabled'
    MFA_DISABLED = 'mfa_disabled', 'MFA Disabled'

    # User Management
    USER_CREATED = 'user_created', 'User Created'
    USER_UPDATED = 'user_updated', 'User Updated'
    USER_DELETED = 'user_deleted', 'User Deleted'
    USER_DEACTIVATED = 'user_deactivated', 'User Deactivated'
    USER_REACTIVATED = 'user_reactivated', 'User Reactivated'
    ROLE_CHANGED = 'role_changed', 'User Role Changed'
    PERMISSIONS_CHANGED = 'permissions_changed', 'User Permissions Changed'

    # Client Management
    CLIENT_CREATED = 'client_created', 'Client Created'
    CLIENT_UPDATED = 'client_updated', 'Client Updated'
    CLIENT_DELETED = 'client_deleted', 'Client Deleted'
    CLIENT_VIEWED = 'client_viewed', 'Client Viewed'

    # Report Management
    REPORT_CREATED = 'report_created', 'Report Created'
    REPORT_UPDATED = 'report_updated', 'Report Updated'
    REPORT_DELETED = 'report_deleted', 'Report Deleted'
    REPORT_DOWNLOADED = 'report_downloaded', 'Report Downloaded'
    REPORT_VIEWED = 'report_viewed', 'Report Viewed'
    REPORT_SHARED = 'report_shared', 'Report Shared'

    # CSV Processing
    CSV_UPLOADED = 'csv_uploaded', 'CSV File Uploaded'
    CSV_PROCESSED = 'csv_processed', 'CSV File Processed'
    CSV_PROCESSING_FAILED = 'csv_processing_failed', 'CSV Processing Failed'
    CSV_VALIDATION_FAILED = 'csv_validation_failed', 'CSV Validation Failed'

    # Data Access
    DATA_EXPORTED = 'data_exported', 'Data Exported'
    DATA_IMPORTED = 'data_imported', 'Data Imported'
    BULK_DELETE = 'bulk_delete', 'Bulk Delete Operation'

    # Security Events
    ACCESS_DENIED = 'access_denied', 'Access Denied'
    RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded', 'Rate Limit Exceeded'
    SUSPICIOUS_ACTIVITY = 'suspicious_activity', 'Suspicious Activity Detected'
    TOKEN_EXPIRED = 'token_expired', 'Auth Token Expired'
    TOKEN_REVOKED = 'token_revoked', 'Auth Token Revoked'

    # System Events
    SYSTEM_CONFIG_CHANGED = 'system_config_changed', 'System Configuration Changed'
    MAINTENANCE_MODE = 'maintenance_mode', 'Maintenance Mode Toggled'
    BACKUP_CREATED = 'backup_created', 'Backup Created'
    BACKUP_RESTORED = 'backup_restored', 'Backup Restored'

    # API Activity
    API_CALL = 'api_call', 'API Call'
    API_ERROR = 'api_error', 'API Error'
    WEBHOOK_TRIGGERED = 'webhook_triggered', 'Webhook Triggered'

    # Other
    OTHER = 'other', 'Other Action'


class AuditSeverity(models.TextChoices):
    """
    Severity levels for audit events
    """
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    CRITICAL = 'critical', 'Critical'


class AuditLog(models.Model):
    """
    Main audit log model for tracking all system activities

    Tracks who did what, when, where, and why with complete context.
    Immutable after creation to maintain audit integrity.
    """

    # Primary identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    # Actor information (who)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='User who performed the action. Null for system actions.'
    )
    username = models.CharField(
        max_length=255,
        blank=True,
        help_text='Username at time of action (preserved even if user deleted)'
    )
    user_email = models.EmailField(
        blank=True,
        help_text='User email at time of action'
    )
    user_role = models.CharField(
        max_length=50,
        blank=True,
        help_text='User role at time of action'
    )

    # Action information (what)
    action = models.CharField(
        max_length=50,
        choices=AuditAction.choices,
        db_index=True,
        help_text='Type of action performed'
    )
    action_description = models.TextField(
        blank=True,
        help_text='Human-readable description of the action'
    )
    severity = models.CharField(
        max_length=20,
        choices=AuditSeverity.choices,
        default=AuditSeverity.LOW,
        db_index=True
    )

    # Resource information (on what)
    resource_type = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text='Type of resource affected (e.g., Report, Client, User)'
    )
    resource_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text='ID of the affected resource'
    )
    resource_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Name/title of the affected resource'
    )

    # Change tracking
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text='Before/after values for updates. Format: {"field": {"old": value, "new": value}}'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional context and metadata about the action'
    )

    # Request context (where/how)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the client'
    )
    user_agent = models.TextField(
        blank=True,
        help_text='User agent string from the request'
    )
    request_path = models.CharField(
        max_length=512,
        blank=True,
        help_text='API endpoint or URL path'
    )
    request_method = models.CharField(
        max_length=10,
        blank=True,
        help_text='HTTP method (GET, POST, PUT, DELETE, etc.)'
    )
    session_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text='Session ID for grouping related actions'
    )

    # Outcome
    success = models.BooleanField(
        default=True,
        help_text='Whether the action completed successfully'
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error message if action failed'
    )
    status_code = models.IntegerField(
        null=True,
        blank=True,
        help_text='HTTP status code'
    )

    # Performance metrics
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text='Action duration in milliseconds'
    )

    # Compliance & retention
    retention_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date when this log can be purged'
    )
    tags = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text='Tags for categorization and filtering'
    )

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'user']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['severity', '-timestamp']),
            models.Index(fields=['success', '-timestamp']),
            models.Index(fields=['session_id', '-timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

        # Prevent modifications to audit logs
        permissions = [
            ('view_auditlog', 'Can view audit logs'),
            ('export_auditlog', 'Can export audit logs'),
        ]

    def __str__(self):
        user_str = self.username or 'System'
        return f'{user_str} - {self.get_action_display()} - {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}'

    def save(self, *args, **kwargs):
        """
        Override save to make logs immutable after creation
        and auto-populate user information
        """
        if self.pk is not None:
            raise ValueError('Audit logs cannot be modified after creation')

        # Auto-populate user information if user is provided
        if self.user:
            self.username = self.user.username
            self.user_email = self.user.email
            self.user_role = getattr(self.user, 'role', '')

        # Set default retention date (7 years for compliance)
        if not self.retention_date:
            self.retention_date = timezone.now() + timezone.timedelta(days=7*365)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Prevent deletion of audit logs
        """
        raise ValueError('Audit logs cannot be deleted')

    @classmethod
    def log_action(
        cls,
        action: str,
        user: Optional[User] = None,
        resource_type: str = '',
        resource_id: str = '',
        resource_name: str = '',
        changes: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: str = '',
        request_path: str = '',
        request_method: str = '',
        session_id: str = '',
        success: bool = True,
        error_message: str = '',
        status_code: Optional[int] = None,
        severity: str = AuditSeverity.LOW,
        tags: Optional[list] = None,
        duration_ms: Optional[int] = None,
    ) -> 'AuditLog':
        """
        Convenience method to create audit log entries

        Example:
            AuditLog.log_action(
                action=AuditAction.REPORT_CREATED,
                user=request.user,
                resource_type='Report',
                resource_id=str(report.id),
                resource_name=report.title,
                ip_address=get_client_ip(request),
                metadata={'client_id': str(report.client_id)},
                severity=AuditSeverity.MEDIUM
            )
        """
        return cls.objects.create(
            action=action,
            user=user,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            changes=changes or {},
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path,
            request_method=request_method,
            session_id=session_id,
            success=success,
            error_message=error_message,
            status_code=status_code,
            severity=severity,
            tags=tags or [],
            duration_ms=duration_ms,
        )


class SecurityEvent(models.Model):
    """
    Specialized model for security-related events requiring immediate attention
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    # Event details
    event_type = models.CharField(max_length=100, db_index=True)
    severity = models.CharField(
        max_length=20,
        choices=AuditSeverity.choices,
        default=AuditSeverity.HIGH
    )

    # Actor (may be anonymous for failed login attempts)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    username_attempted = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)

    # Details
    description = models.TextField()
    details = models.JSONField(default=dict)

    # Response
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_security_events'
    )
    resolution_notes = models.TextField(blank=True)

    # Alerting
    alert_sent = models.BooleanField(default=False)
    alert_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'security_events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'severity']),
            models.Index(fields=['resolved', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
        ]

    def __str__(self):
        return f'{self.event_type} - {self.severity} - {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}'


class DataAccessLog(models.Model):
    """
    Specialized logging for sensitive data access (PII, financial data, etc.)
    Required for GDPR, HIPAA, and other privacy compliance
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    # Who accessed the data
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    username = models.CharField(max_length=255)

    # What data was accessed
    data_type = models.CharField(max_length=100, db_index=True)
    data_id = models.CharField(max_length=255, db_index=True)
    data_description = models.CharField(max_length=255)

    # How it was accessed
    access_type = models.CharField(
        max_length=50,
        choices=[
            ('read', 'Read'),
            ('create', 'Create'),
            ('update', 'Update'),
            ('delete', 'Delete'),
            ('export', 'Export'),
        ]
    )

    # Context
    ip_address = models.GenericIPAddressField()
    purpose = models.TextField(help_text='Business justification for access')

    # Compliance
    retention_date = models.DateTimeField()

    class Meta:
        db_table = 'data_access_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['data_type', 'data_id']),
        ]

    def __str__(self):
        return f'{self.username} accessed {self.data_type} {self.data_id}'
