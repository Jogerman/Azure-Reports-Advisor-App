"""
Management command to clean up old notifications

Usage:
    python manage.py cleanup_notifications --days 90
    python manage.py cleanup_notifications --days 30 --dry-run
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.notifications.models import (
    EmailNotification,
    WebhookDelivery,
    InAppNotification
)


class Command(BaseCommand):
    help = 'Clean up old notification records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Delete records older than this many days (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--emails',
            action='store_true',
            help='Only clean up email notifications'
        )
        parser.add_argument(
            '--webhook-deliveries',
            action='store_true',
            help='Only clean up webhook deliveries'
        )
        parser.add_argument(
            '--inapp',
            action='store_true',
            help='Only clean up read in-app notifications'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff_date = timezone.now() - timedelta(days=days)

        self.stdout.write(
            self.style.WARNING(f'\nCleaning up notifications older than {days} days')
        )
        self.stdout.write(f'Cutoff date: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}')

        if dry_run:
            self.stdout.write(self.style.NOTICE('\n--- DRY RUN MODE ---\n'))

        total_deleted = 0

        # Clean up email notifications
        if not options['webhook_deliveries'] and not options['inapp']:
            email_count = self._cleanup_emails(cutoff_date, dry_run)
            total_deleted += email_count

        # Clean up webhook deliveries
        if not options['emails'] and not options['inapp']:
            webhook_count = self._cleanup_webhooks(cutoff_date, dry_run)
            total_deleted += webhook_count

        # Clean up in-app notifications
        if not options['emails'] and not options['webhook_deliveries']:
            inapp_count = self._cleanup_inapp(cutoff_date, dry_run)
            total_deleted += inapp_count

        # Summary
        self.stdout.write('\n' + '=' * 50)
        if dry_run:
            self.stdout.write(
                self.style.NOTICE(f'Would delete {total_deleted} total records')
            )
            self.stdout.write(
                self.style.NOTICE('Run without --dry-run to actually delete')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {total_deleted} total records')
            )

    def _cleanup_emails(self, cutoff_date, dry_run):
        """Clean up old email notifications"""
        queryset = EmailNotification.objects.filter(
            created_at__lt=cutoff_date,
            sent=True  # Only delete sent emails
        )

        count = queryset.count()

        if count > 0:
            self.stdout.write(f'\nEmail Notifications:')
            self.stdout.write(f'  Found: {count}')

            if not dry_run:
                deleted = queryset.delete()[0]
                self.stdout.write(
                    self.style.SUCCESS(f'  Deleted: {deleted}')
                )
                return deleted
            else:
                self.stdout.write(
                    self.style.NOTICE(f'  Would delete: {count}')
                )

        return count if dry_run else 0

    def _cleanup_webhooks(self, cutoff_date, dry_run):
        """Clean up old webhook deliveries"""
        queryset = WebhookDelivery.objects.filter(
            created_at__lt=cutoff_date
        )

        count = queryset.count()

        if count > 0:
            self.stdout.write(f'\nWebhook Deliveries:')
            self.stdout.write(f'  Found: {count}')

            if not dry_run:
                deleted = queryset.delete()[0]
                self.stdout.write(
                    self.style.SUCCESS(f'  Deleted: {deleted}')
                )
                return deleted
            else:
                self.stdout.write(
                    self.style.NOTICE(f'  Would delete: {count}')
                )

        return count if dry_run else 0

    def _cleanup_inapp(self, cutoff_date, dry_run):
        """Clean up old read in-app notifications"""
        queryset = InAppNotification.objects.filter(
            created_at__lt=cutoff_date,
            read=True  # Only delete read notifications
        )

        count = queryset.count()

        if count > 0:
            self.stdout.write(f'\nIn-App Notifications (read):')
            self.stdout.write(f'  Found: {count}')

            if not dry_run:
                deleted = queryset.delete()[0]
                self.stdout.write(
                    self.style.SUCCESS(f'  Deleted: {deleted}')
                )
                return deleted
            else:
                self.stdout.write(
                    self.style.NOTICE(f'  Would delete: {count}')
                )

        return count if dry_run else 0
