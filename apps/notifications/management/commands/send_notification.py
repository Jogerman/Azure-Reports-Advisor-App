"""
Management command to send notifications

Usage:
    python manage.py send_notification --user-id <uuid> --title "Title" --message "Message"
    python manage.py send_notification --all-admins --title "System Alert" --message "Database backup completed"
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from apps.notifications.services import NotificationService
from apps.notifications.models import NotificationType, NotificationPriority
from apps.security.permissions import UserRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Send notifications to users'

    def add_arguments(self, parser):
        # User selection
        parser.add_argument(
            '--user-id',
            type=str,
            help='User ID to send notification to'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username to send notification to'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email to send notification to'
        )
        parser.add_argument(
            '--all-admins',
            action='store_true',
            help='Send to all admin users'
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Send to all active users'
        )

        # Notification content
        parser.add_argument(
            '--title',
            type=str,
            required=True,
            help='Notification title'
        )
        parser.add_argument(
            '--message',
            type=str,
            required=True,
            help='Notification message'
        )
        parser.add_argument(
            '--type',
            type=str,
            default='custom',
            choices=[choice[0] for choice in NotificationType.choices],
            help='Notification type'
        )
        parser.add_argument(
            '--priority',
            type=str,
            default='normal',
            choices=[choice[0] for choice in NotificationPriority.choices],
            help='Notification priority'
        )

        # Channels
        parser.add_argument(
            '--email',
            dest='send_email',
            action='store_true',
            default=True,
            help='Send email notification (default: True)'
        )
        parser.add_argument(
            '--no-email',
            dest='send_email',
            action='store_false',
            help='Do not send email notification'
        )
        parser.add_argument(
            '--inapp',
            dest='create_inapp',
            action='store_true',
            default=True,
            help='Create in-app notification (default: True)'
        )
        parser.add_argument(
            '--no-inapp',
            dest='create_inapp',
            action='store_false',
            help='Do not create in-app notification'
        )
        parser.add_argument(
            '--webhooks',
            dest='trigger_webhooks',
            action='store_true',
            default=True,
            help='Trigger webhooks (default: True)'
        )
        parser.add_argument(
            '--no-webhooks',
            dest='trigger_webhooks',
            action='store_false',
            help='Do not trigger webhooks'
        )

        # Optional fields
        parser.add_argument(
            '--action-url',
            type=str,
            default='',
            help='Action URL for in-app notification'
        )
        parser.add_argument(
            '--action-label',
            type=str,
            default='',
            help='Action button label'
        )

    def handle(self, *args, **options):
        # Get users to send notifications to
        users = self._get_users(options)

        if not users:
            raise CommandError('No users found matching criteria')

        # Send notifications
        success_count = 0
        error_count = 0

        for user in users:
            try:
                NotificationService.notify(
                    user=user,
                    title=options['title'],
                    message=options['message'],
                    notification_type=options['type'],
                    priority=options['priority'],
                    send_email=options['send_email'],
                    create_inapp=options['create_inapp'],
                    trigger_webhooks=options['trigger_webhooks'],
                    action_url=options['action_url'],
                    action_label=options['action_label']
                )
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Notification sent to {user.username}')
                )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to send to {user.username}: {str(e)}')
                )

        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS(f'Successfully sent: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {error_count}'))

    def _get_users(self, options):
        """Get users based on command options"""
        users = []

        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
                users.append(user)
            except User.DoesNotExist:
                raise CommandError(f'User with ID {options["user_id"]} not found')

        elif options['username']:
            try:
                user = User.objects.get(username=options['username'])
                users.append(user)
            except User.DoesNotExist:
                raise CommandError(f'User with username {options["username"]} not found')

        elif options.get('email'):
            try:
                user = User.objects.get(email=options['email'])
                users.append(user)
            except User.DoesNotExist:
                raise CommandError(f'User with email {options["email"]} not found')

        elif options['all_admins']:
            users = list(User.objects.filter(
                role=UserRole.ADMIN,
                is_active=True
            ))

        elif options['all_users']:
            users = list(User.objects.filter(is_active=True))

        else:
            raise CommandError(
                'Must specify --user-id, --username, --email, '
                '--all-admins, or --all-users'
            )

        return users
