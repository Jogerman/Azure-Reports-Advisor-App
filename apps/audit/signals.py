"""
Django signals for automatic audit logging of model changes

These signals automatically create audit log entries when models are created,
updated, or deleted, providing comprehensive tracking without manual logging.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.cache import cache
from typing import Optional
import threading

from .models import AuditLog, AuditAction, AuditSeverity
from .utils import calculate_object_changes

User = get_user_model()

# Thread-local storage for request context
_thread_locals = threading.local()


def set_current_request(request):
    """
    Store current request in thread-local storage for use in signals
    Call this from middleware or view
    """
    _thread_locals.request = request


def get_current_request():
    """
    Retrieve current request from thread-local storage
    """
    return getattr(_thread_locals, 'request', None)


# =============================================================================
# User Management Signals
# =============================================================================

@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """
    Log user creation and updates
    """
    request = get_current_request()

    if created:
        action = AuditAction.USER_CREATED
        changes = {}
        description = f'User {instance.username} was created'
    else:
        action = AuditAction.USER_UPDATED
        # Get old instance from cache if available
        old_instance = cache.get(f'user_pre_save_{instance.id}')
        if old_instance:
            changes = calculate_object_changes(
                old_instance,
                instance,
                fields=['username', 'email', 'is_active', 'is_staff', 'role']
            )
        else:
            changes = {}
        description = f'User {instance.username} was updated'

    AuditLog.log_action(
        action=action,
        user=getattr(request, 'user', None) if request else None,
        resource_type='User',
        resource_id=str(instance.id),
        resource_name=instance.username,
        action_description=description,
        changes=changes,
        severity=AuditSeverity.MEDIUM,
        ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR') if request else None,
    )


@receiver(pre_save, sender=User)
def cache_user_pre_save(sender, instance, **kwargs):
    """
    Cache the old user state before saving for change tracking
    """
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            cache.set(f'user_pre_save_{instance.id}', old_instance, timeout=60)
        except User.DoesNotExist:
            pass


@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """
    Log user deletion
    """
    request = get_current_request()

    AuditLog.log_action(
        action=AuditAction.USER_DELETED,
        user=getattr(request, 'user', None) if request else None,
        resource_type='User',
        resource_id=str(instance.id),
        resource_name=instance.username,
        action_description=f'User {instance.username} was deleted',
        severity=AuditSeverity.HIGH,
        metadata={
            'deleted_user_email': instance.email,
            'deleted_user_role': getattr(instance, 'role', ''),
        },
        ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR') if request else None,
    )


# =============================================================================
# Client Management Signals
# =============================================================================

def setup_client_signals():
    """
    Setup signals for Client model (imported to avoid circular imports)
    """
    try:
        from apps.clients.models import Client

        @receiver(post_save, sender=Client)
        def log_client_changes(sender, instance, created, **kwargs):
            request = get_current_request()

            if created:
                action = AuditAction.CLIENT_CREATED
                changes = {}
                description = f'Client {instance.company_name} was created'
            else:
                action = AuditAction.CLIENT_UPDATED
                old_instance = cache.get(f'client_pre_save_{instance.id}')
                if old_instance:
                    changes = calculate_object_changes(
                        old_instance,
                        instance,
                        fields=['company_name', 'status', 'contact_email']
                    )
                else:
                    changes = {}
                description = f'Client {instance.company_name} was updated'

            AuditLog.log_action(
                action=action,
                user=getattr(request, 'user', None) if request else None,
                resource_type='Client',
                resource_id=str(instance.id),
                resource_name=instance.company_name,
                action_description=description,
                changes=changes,
                severity=AuditSeverity.MEDIUM,
                ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR') if request else None,
            )

        @receiver(pre_save, sender=Client)
        def cache_client_pre_save(sender, instance, **kwargs):
            if instance.pk:
                try:
                    old_instance = Client.objects.get(pk=instance.pk)
                    cache.set(f'client_pre_save_{instance.id}', old_instance, timeout=60)
                except Client.DoesNotExist:
                    pass

        @receiver(post_delete, sender=Client)
        def log_client_deletion(sender, instance, **kwargs):
            request = get_current_request()

            AuditLog.log_action(
                action=AuditAction.CLIENT_DELETED,
                user=getattr(request, 'user', None) if request else None,
                resource_type='Client',
                resource_id=str(instance.id),
                resource_name=instance.company_name,
                action_description=f'Client {instance.company_name} was deleted',
                severity=AuditSeverity.HIGH,
                ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR') if request else None,
            )

    except ImportError:
        pass


# =============================================================================
# Report Management Signals
# =============================================================================

def setup_report_signals():
    """
    Setup signals for Report model (imported to avoid circular imports)
    """
    try:
        from apps.reports.models import Report

        @receiver(post_save, sender=Report)
        def log_report_changes(sender, instance, created, **kwargs):
            request = get_current_request()

            if created:
                action = AuditAction.REPORT_CREATED
                changes = {}
                description = f'Report for client {instance.client.company_name} was created'
                severity = AuditSeverity.MEDIUM
            else:
                action = AuditAction.REPORT_UPDATED
                old_instance = cache.get(f'report_pre_save_{instance.id}')
                if old_instance:
                    changes = calculate_object_changes(
                        old_instance,
                        instance,
                        fields=['status', 'report_type']
                    )
                else:
                    changes = {}
                description = f'Report {instance.id} was updated'
                # Higher severity if status changed to failed
                severity = AuditSeverity.HIGH if instance.status == 'failed' else AuditSeverity.LOW

            AuditLog.log_action(
                action=action,
                user=getattr(request, 'user', None) if request else None,
                resource_type='Report',
                resource_id=str(instance.id),
                resource_name=f'Report for {instance.client.company_name}',
                action_description=description,
                changes=changes,
                severity=severity,
                metadata={
                    'client_id': str(instance.client_id),
                    'report_type': instance.report_type,
                    'status': instance.status,
                },
                ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR') if request else None,
            )

        @receiver(pre_save, sender=Report)
        def cache_report_pre_save(sender, instance, **kwargs):
            if instance.pk:
                try:
                    old_instance = Report.objects.get(pk=instance.pk)
                    cache.set(f'report_pre_save_{instance.id}', old_instance, timeout=60)
                except Report.DoesNotExist:
                    pass

        @receiver(post_delete, sender=Report)
        def log_report_deletion(sender, instance, **kwargs):
            request = get_current_request()

            AuditLog.log_action(
                action=AuditAction.REPORT_DELETED,
                user=getattr(request, 'user', None) if request else None,
                resource_type='Report',
                resource_id=str(instance.id),
                resource_name=f'Report for {instance.client.company_name}',
                action_description=f'Report {instance.id} was deleted',
                severity=AuditSeverity.HIGH,
                metadata={
                    'client_id': str(instance.client_id),
                    'report_type': instance.report_type,
                    'had_csv': bool(instance.csv_file),
                    'had_pdf': bool(instance.pdf_file),
                },
                ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR') if request else None,
            )

    except ImportError:
        pass


# Initialize all signal handlers
setup_client_signals()
setup_report_signals()
