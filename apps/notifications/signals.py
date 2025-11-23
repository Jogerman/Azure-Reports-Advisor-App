"""
Notification System Signals

Automatic notification triggers based on model events
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .services import NotificationService, WebhookService
from .models import NotificationType, NotificationPriority


# =============================================================================
# Report Notifications
# =============================================================================

@receiver(post_save, sender='reports.Report')
def report_status_changed(sender, instance, created, **kwargs):
    """
    Trigger notifications when report status changes

    Sends notifications when:
    - Report is completed
    - Report fails
    """
    if created:
        return  # Don't send notifications for newly created reports

    report = instance

    # Report completed
    if report.status == 'completed' and report.generated_at:
        NotificationService.notify(
            user=report.created_by,
            title=f'Report Ready: {report.client.company_name}',
            message=f'Your Azure Advisor report for {report.client.company_name} is ready to download.',
            notification_type=NotificationType.REPORT_COMPLETED,
            priority=NotificationPriority.NORMAL,
            send_email=True,
            create_inapp=True,
            trigger_webhooks=True,
            action_url=f'/reports/{report.id}',
            action_label='View Report',
            email_template='emails/report_completed',
            email_context={
                'report': report,
                'user': report.created_by,
                'download_url': f'{settings.FRONTEND_URL}/reports/{report.id}',
            },
            webhook_payload={
                'event': 'report.completed',
                'report_id': str(report.id),
                'client_name': report.client.company_name,
                'created_by': report.created_by.username,
                'created_at': report.created_at.isoformat(),
                'generated_at': report.generated_at.isoformat(),
            }
        )

    # Report failed
    elif report.status == 'failed':
        error_message = getattr(report, 'error_message', 'Unknown error occurred')

        NotificationService.notify(
            user=report.created_by,
            title=f'Report Failed: {report.client.company_name}',
            message=f'Your Azure Advisor report for {report.client.company_name} failed to generate. Error: {error_message}',
            notification_type=NotificationType.REPORT_FAILED,
            priority=NotificationPriority.HIGH,
            send_email=True,
            create_inapp=True,
            trigger_webhooks=True,
            action_url=f'/reports/{report.id}',
            action_label='View Details',
            email_template='emails/report_failed',
            email_context={
                'report': report,
                'user': report.created_by,
                'error_message': error_message,
            },
            webhook_payload={
                'event': 'report.failed',
                'report_id': str(report.id),
                'client_name': report.client.company_name,
                'created_by': report.created_by.username,
                'error_message': error_message,
            }
        )


# =============================================================================
# CSV Processing Notifications
# =============================================================================

@receiver(post_save, sender='clients.CSVUpload')
def csv_processed(sender, instance, created, **kwargs):
    """
    Notify when CSV processing completes
    """
    if created:
        return

    csv_upload = instance

    # CSV processed successfully
    if csv_upload.status == 'completed' and csv_upload.processed_at:
        NotificationService.notify(
            user=csv_upload.uploaded_by,
            title='CSV Processing Complete',
            message=f'CSV file "{csv_upload.file_name}" has been processed successfully. {csv_upload.clients_created} clients created.',
            notification_type=NotificationType.CSV_PROCESSED,
            priority=NotificationPriority.NORMAL,
            send_email=False,  # Don't send email for CSV processing
            create_inapp=True,
            trigger_webhooks=True,
            action_url='/clients',
            action_label='View Clients',
            webhook_payload={
                'event': 'csv.processed',
                'upload_id': str(csv_upload.id),
                'file_name': csv_upload.file_name,
                'clients_created': csv_upload.clients_created,
                'uploaded_by': csv_upload.uploaded_by.username,
            }
        )

    # CSV processing failed
    elif csv_upload.status == 'failed':
        error_message = getattr(csv_upload, 'error_message', 'Unknown error')

        NotificationService.notify(
            user=csv_upload.uploaded_by,
            title='CSV Processing Failed',
            message=f'Failed to process CSV file "{csv_upload.file_name}". Error: {error_message}',
            notification_type=NotificationType.CSV_PROCESSED,
            priority=NotificationPriority.HIGH,
            send_email=False,
            create_inapp=True,
            trigger_webhooks=True,
            webhook_payload={
                'event': 'csv.failed',
                'upload_id': str(csv_upload.id),
                'file_name': csv_upload.file_name,
                'error_message': error_message,
            }
        )


# =============================================================================
# User Management Notifications
# =============================================================================

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def user_created(sender, instance, created, **kwargs):
    """
    Notify when a new user is created/invited
    """
    if not created:
        return

    user = instance

    # Send welcome notification
    NotificationService.notify(
        user=user,
        title='Welcome to Azure Advisor Reports',
        message='Your account has been created successfully. You can now start generating Azure Advisor reports.',
        notification_type=NotificationType.USER_INVITED,
        priority=NotificationPriority.NORMAL,
        send_email=True,
        create_inapp=True,
        trigger_webhooks=False,  # Don't trigger webhooks for user creation
        action_url='/dashboard',
        action_label='Go to Dashboard',
        email_template='emails/welcome',
        email_context={
            'user': user,
            'dashboard_url': f'{settings.FRONTEND_URL}/dashboard',
        }
    )


# =============================================================================
# System Alert Notifications
# =============================================================================

def send_system_alert(title: str, message: str, priority: str = NotificationPriority.HIGH):
    """
    Send system alert to all admins

    Usage:
        from apps.notifications.signals import send_system_alert
        send_system_alert(
            title='Database Connection Lost',
            message='Database connection was lost at 10:30 AM',
            priority=NotificationPriority.URGENT
        )
    """
    from django.contrib.auth import get_user_model
    from apps.security.permissions import UserRole

    User = get_user_model()

    # Get all admin users
    admins = User.objects.filter(role=UserRole.ADMIN, is_active=True)

    for admin in admins:
        NotificationService.notify(
            user=admin,
            title=title,
            message=message,
            notification_type=NotificationType.SYSTEM_ALERT,
            priority=priority,
            send_email=True,
            create_inapp=True,
            trigger_webhooks=True,
            webhook_payload={
                'event': 'system.alert',
                'title': title,
                'message': message,
                'priority': priority,
            }
        )
