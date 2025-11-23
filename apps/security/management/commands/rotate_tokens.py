"""
Management command for token rotation tasks

Usage:
    python manage.py rotate_tokens --cleanup
    python manage.py rotate_tokens --check-expiring
    python manage.py rotate_tokens --notify-expiring
"""

from django.core.management.base import BaseCommand

from apps.security.token_rotation import (
    cleanup_expired_tokens,
    send_expiry_notifications,
    APIKeyRotation
)


class Command(BaseCommand):
    help = 'Manage token rotation tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up expired tokens and API keys'
        )
        parser.add_argument(
            '--check-expiring',
            action='store_true',
            help='Check for expiring API keys'
        )
        parser.add_argument(
            '--notify-expiring',
            action='store_true',
            help='Send notifications for expiring API keys'
        )
        parser.add_argument(
            '--warning-days',
            type=int,
            default=7,
            help='Days before expiry to warn (default: 7)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all rotation tasks'
        )

    def handle(self, *args, **options):
        run_all = options['all']

        if options['cleanup'] or run_all:
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(self.style.WARNING('Cleaning up expired tokens...'))
            count = cleanup_expired_tokens()
            self.stdout.write(
                self.style.SUCCESS(f'✓ Deactivated {count} expired API keys')
            )

        if options['check_expiring'] or run_all:
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(self.style.WARNING('Checking for expiring API keys...'))
            warning_days = options['warning_days']
            expiring_keys = APIKeyRotation.check_expiring_keys(warning_days=warning_days)

            if expiring_keys:
                self.stdout.write(
                    self.style.WARNING(f'Found {len(expiring_keys)} API keys expiring soon:')
                )
                for key in expiring_keys:
                    days = key.days_until_expiry
                    self.stdout.write(
                        f'  • {key.name} ({key.user.username}) - expires in {days} days'
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS('✓ No API keys expiring soon')
                )

        if options['notify_expiring'] or run_all:
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(self.style.WARNING('Sending expiry notifications...'))
            count = send_expiry_notifications()
            self.stdout.write(
                self.style.SUCCESS(f'✓ Sent notifications for {count} API keys')
            )

        if not any([options['cleanup'], options['check_expiring'], options['notify_expiring'], run_all]):
            self.stdout.write(
                self.style.ERROR('Please specify an action: --cleanup, --check-expiring, --notify-expiring, or --all')
            )
