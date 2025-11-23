"""
Notification Services

Handles sending emails, triggering webhooks, and creating in-app notifications
"""

import logging
import requests
import hmac
import hashlib
import time
from typing import Optional, Dict, Any, List
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from .models import (
    EmailNotification,
    Webhook,
    WebhookDelivery,
    InAppNotification,
    NotificationType,
    NotificationPriority
)

logger = logging.getLogger(__name__)


# =============================================================================
# Email Service
# =============================================================================

class EmailService:
    """
    Service for sending email notifications
    """

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        message: str,
        html_message: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        notification_type: str = NotificationType.CUSTOM,
        priority: str = NotificationPriority.NORMAL,
        user=None,
        context_data: Optional[Dict] = None
    ) -> EmailNotification:
        """
        Send an email notification

        Args:
            to_email: Recipient email
            subject: Email subject
            message: Plain text message
            html_message: HTML message (optional)
            cc_emails: CC recipients
            bcc_emails: BCC recipients
            notification_type: Type of notification
            priority: Priority level
            user: Related user
            context_data: Additional context

        Returns:
            EmailNotification instance

        Example:
            EmailService.send_email(
                to_email='user@example.com',
                subject='Report Ready',
                message='Your report is ready',
                html_message='<h1>Your report is ready</h1>',
                notification_type=NotificationType.REPORT_COMPLETED
            )
        """
        # Create notification record
        notification = EmailNotification.objects.create(
            to_email=to_email,
            cc_emails=cc_emails or [],
            bcc_emails=bcc_emails or [],
            subject=subject,
            message=message,
            html_message=html_message or '',
            notification_type=notification_type,
            priority=priority,
            user=user,
            context_data=context_data or {}
        )

        try:
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
                cc=cc_emails,
                bcc=bcc_emails
            )

            # Add HTML version if provided
            if html_message:
                email.attach_alternative(html_message, "text/html")

            # Send email
            email.send(fail_silently=False)

            # Mark as sent
            notification.mark_as_sent()

            logger.info(f'Email sent successfully to {to_email}: {subject}')

        except Exception as e:
            # Mark as failed
            notification.mark_as_failed(str(e))
            logger.error(f'Failed to send email to {to_email}: {str(e)}')

        return notification

    @staticmethod
    def send_template_email(
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        **kwargs
    ) -> EmailNotification:
        """
        Send email using Django template

        Args:
            to_email: Recipient email
            subject: Email subject
            template_name: Template name (without extension)
            context: Template context
            **kwargs: Additional arguments for send_email

        Example:
            EmailService.send_template_email(
                to_email='user@example.com',
                subject='Report Ready',
                template_name='emails/report_completed',
                context={'report': report, 'user': user}
            )
        """
        # Render HTML template
        html_message = render_to_string(f'{template_name}.html', context)

        # Render text template (optional)
        try:
            message = render_to_string(f'{template_name}.txt', context)
        except:
            # Fallback to simple text version
            message = f'{subject}\n\nPlease view this email in an HTML-capable email client.'

        return EmailService.send_email(
            to_email=to_email,
            subject=subject,
            message=message,
            html_message=html_message,
            **kwargs
        )

    @staticmethod
    def send_report_completed_email(report, user):
        """Send notification when report is completed"""
        return EmailService.send_template_email(
            to_email=user.email,
            subject=f'Report for {report.client.company_name} is Ready',
            template_name='emails/report_completed',
            context={
                'report': report,
                'user': user,
                'download_url': f'{settings.FRONTEND_URL}/reports/{report.id}',
            },
            notification_type=NotificationType.REPORT_COMPLETED,
            user=user
        )

    @staticmethod
    def send_report_failed_email(report, user, error_message):
        """Send notification when report fails"""
        return EmailService.send_template_email(
            to_email=user.email,
            subject=f'Report for {report.client.company_name} Failed',
            template_name='emails/report_failed',
            context={
                'report': report,
                'user': user,
                'error_message': error_message,
            },
            notification_type=NotificationType.REPORT_FAILED,
            priority=NotificationPriority.HIGH,
            user=user
        )


# =============================================================================
# Webhook Service
# =============================================================================

class WebhookService:
    """
    Service for triggering webhooks
    """

    @staticmethod
    def trigger_webhook(
        event_type: str,
        payload: Dict[str, Any],
        webhook_id: Optional[str] = None
    ) -> List[WebhookDelivery]:
        """
        Trigger webhooks for an event

        Args:
            event_type: Event type
            payload: Event payload
            webhook_id: Specific webhook ID (optional, otherwise triggers all matching)

        Returns:
            List of WebhookDelivery instances

        Example:
            WebhookService.trigger_webhook(
                event_type='report.completed',
                payload={
                    'report_id': str(report.id),
                    'client_name': report.client.company_name,
                    'timestamp': timezone.now().isoformat()
                }
            )
        """
        deliveries = []

        # Get matching webhooks
        if webhook_id:
            webhooks = Webhook.objects.filter(id=webhook_id, active=True)
        else:
            webhooks = Webhook.objects.filter(active=True)

        for webhook in webhooks:
            if webhook.should_trigger_for_event(event_type):
                delivery = WebhookService._send_webhook(webhook, event_type, payload)
                deliveries.append(delivery)

        return deliveries

    @staticmethod
    def _send_webhook(
        webhook: Webhook,
        event_type: str,
        payload: Dict[str, Any]
    ) -> WebhookDelivery:
        """
        Send a single webhook request

        Args:
            webhook: Webhook instance
            event_type: Event type
            payload: Event payload

        Returns:
            WebhookDelivery instance
        """
        start_time = time.time()

        # Create delivery record
        delivery = WebhookDelivery.objects.create(
            webhook=webhook,
            event_type=event_type,
            payload=payload
        )

        try:
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Azure-Advisor-Reports-Webhook/1.0',
                **webhook.headers
            }

            # Add signature if secret is configured
            if webhook.secret:
                signature = WebhookService._generate_signature(payload, webhook.secret)
                headers['X-Webhook-Signature'] = signature

            # Send request
            response = requests.request(
                method=webhook.method,
                url=webhook.url,
                json=payload,
                headers=headers,
                timeout=webhook.timeout
            )

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Update delivery record
            delivery.status_code = response.status_code
            delivery.response_body = response.text[:5000]  # Limit size
            delivery.response_headers = dict(response.headers)
            delivery.success = 200 <= response.status_code < 300
            delivery.duration_ms = duration_ms
            delivery.save()

            # Update webhook
            if delivery.success:
                webhook.failure_count = 0
                webhook.last_triggered_at = timezone.now()
            else:
                webhook.failure_count += 1

            webhook.save()

            logger.info(
                f'Webhook {webhook.name} triggered: {event_type} - '
                f'Status {response.status_code}'
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            delivery.error_message = str(e)
            delivery.duration_ms = duration_ms
            delivery.save()

            webhook.failure_count += 1
            webhook.save()

            logger.error(f'Webhook {webhook.name} failed: {str(e)}')

        # Check if webhook should be disabled
        if webhook.failure_count >= webhook.max_failures:
            webhook.active = False
            webhook.save()
            logger.warning(
                f'Webhook {webhook.name} disabled after '
                f'{webhook.failure_count} failures'
            )

        return delivery

    @staticmethod
    def _generate_signature(payload: Dict[str, Any], secret: str) -> str:
        """
        Generate HMAC signature for webhook payload

        Args:
            payload: Webhook payload
            secret: Webhook secret

        Returns:
            HMAC signature
        """
        import json

        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        return f'sha256={signature}'

    @staticmethod
    def verify_signature(payload: Dict[str, Any], signature: str, secret: str) -> bool:
        """
        Verify webhook signature

        Args:
            payload: Webhook payload
            signature: Provided signature
            secret: Webhook secret

        Returns:
            True if signature is valid
        """
        expected_signature = WebhookService._generate_signature(payload, secret)
        return hmac.compare_digest(signature, expected_signature)


# =============================================================================
# In-App Notification Service
# =============================================================================

class InAppNotificationService:
    """
    Service for creating in-app notifications
    """

    @staticmethod
    def create_notification(
        user,
        title: str,
        message: str,
        notification_type: str = NotificationType.CUSTOM,
        priority: str = NotificationPriority.NORMAL,
        action_url: str = '',
        action_label: str = '',
        context_data: Optional[Dict] = None
    ) -> InAppNotification:
        """
        Create an in-app notification

        Args:
            user: User to notify
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            action_url: URL for action button
            action_label: Label for action button
            context_data: Additional context

        Returns:
            InAppNotification instance

        Example:
            InAppNotificationService.create_notification(
                user=request.user,
                title='Report Ready',
                message='Your report for Client A is ready',
                notification_type=NotificationType.REPORT_COMPLETED,
                action_url='/reports/123',
                action_label='View Report'
            )
        """
        notification = InAppNotification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            action_url=action_url,
            action_label=action_label,
            context_data=context_data or {}
        )

        logger.info(f'In-app notification created for {user.username}: {title}')

        return notification

    @staticmethod
    def get_unread_count(user) -> int:
        """Get count of unread notifications for user"""
        return InAppNotification.objects.filter(
            user=user,
            read=False
        ).count()

    @staticmethod
    def mark_all_as_read(user):
        """Mark all notifications as read for user"""
        InAppNotification.objects.filter(
            user=user,
            read=False
        ).update(read=True, read_at=timezone.now())


# =============================================================================
# Unified Notification Service
# =============================================================================

class NotificationService:
    """
    Unified service for sending notifications across all channels
    """

    @staticmethod
    def notify(
        user,
        title: str,
        message: str,
        notification_type: str = NotificationType.CUSTOM,
        priority: str = NotificationPriority.NORMAL,
        send_email: bool = True,
        create_inapp: bool = True,
        trigger_webhooks: bool = True,
        email_template: Optional[str] = None,
        webhook_payload: Optional[Dict] = None,
        **kwargs
    ):
        """
        Send notification across multiple channels

        Args:
            user: User to notify
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            send_email: Send email notification
            create_inapp: Create in-app notification
            trigger_webhooks: Trigger webhooks
            email_template: Email template name (optional)
            webhook_payload: Custom webhook payload (optional)
            **kwargs: Additional arguments

        Example:
            NotificationService.notify(
                user=request.user,
                title='Report Ready',
                message='Your report is ready to download',
                notification_type=NotificationType.REPORT_COMPLETED,
                send_email=True,
                create_inapp=True,
                trigger_webhooks=True,
                email_template='emails/report_completed',
                webhook_payload={'report_id': report.id}
            )
        """
        results = {}

        # Send email
        if send_email and user.email:
            if email_template:
                email = EmailService.send_template_email(
                    to_email=user.email,
                    subject=title,
                    template_name=email_template,
                    context=kwargs.get('email_context', {}),
                    notification_type=notification_type,
                    priority=priority,
                    user=user
                )
            else:
                email = EmailService.send_email(
                    to_email=user.email,
                    subject=title,
                    message=message,
                    notification_type=notification_type,
                    priority=priority,
                    user=user
                )
            results['email'] = email

        # Create in-app notification
        if create_inapp:
            inapp = InAppNotificationService.create_notification(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                action_url=kwargs.get('action_url', ''),
                action_label=kwargs.get('action_label', '')
            )
            results['inapp'] = inapp

        # Trigger webhooks
        if trigger_webhooks:
            if webhook_payload is None:
                webhook_payload = {
                    'event': notification_type,
                    'user_id': str(user.id),
                    'title': title,
                    'message': message,
                    'timestamp': timezone.now().isoformat()
                }

            deliveries = WebhookService.trigger_webhook(
                event_type=notification_type,
                payload=webhook_payload
            )
            results['webhooks'] = deliveries

        return results
