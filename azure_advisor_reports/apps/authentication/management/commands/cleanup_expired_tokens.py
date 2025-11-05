"""
Django management command to clean up expired JWT tokens from the blacklist.

This command removes tokens that have already expired from the database,
helping to maintain optimal database performance and reduce storage costs.

Usage:
    python manage.py cleanup_expired_tokens

    Options:
        --dry-run    : Show what would be deleted without actually deleting
        --verbose    : Show detailed output

Schedule this command to run periodically (daily recommended):
    - Via cron job
    - Via Celery Beat (see tasks.py)
    - Via system scheduler (Windows Task Scheduler, systemd timer, etc.)
"""

import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.authentication.models import TokenBlacklist

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up expired JWT tokens from the blacklist database'

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output including token information',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        dry_run = options['dry_run']
        verbose = options['verbose']

        self.stdout.write(self.style.MIGRATE_HEADING('JWT Token Cleanup'))
        self.stdout.write('')

        # Get current time
        now = timezone.now()
        self.stdout.write(f'Current time: {now.strftime("%Y-%m-%d %H:%M:%S %Z")}')
        self.stdout.write('')

        # Count expired tokens
        expired_tokens = TokenBlacklist.objects.filter(expires_at__lt=now)
        total_count = expired_tokens.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No expired tokens found. Database is clean!'))
            return

        # Show statistics
        self.stdout.write(f'Found {total_count} expired tokens:')

        # Count by token type
        access_count = expired_tokens.filter(token_type='access').count()
        refresh_count = expired_tokens.filter(token_type='refresh').count()

        self.stdout.write(f'  - Access tokens:  {access_count}')
        self.stdout.write(f'  - Refresh tokens: {refresh_count}')
        self.stdout.write('')

        # Count revoked vs non-revoked
        revoked_count = expired_tokens.filter(is_revoked=True).count()
        non_revoked_count = expired_tokens.filter(is_revoked=False).count()

        self.stdout.write(f'  - Revoked:     {revoked_count}')
        self.stdout.write(f'  - Non-revoked: {non_revoked_count}')
        self.stdout.write('')

        # Show verbose details if requested
        if verbose:
            self.stdout.write(self.style.MIGRATE_LABEL('Expired Token Details:'))
            for token in expired_tokens[:20]:  # Show first 20
                status = 'REVOKED' if token.is_revoked else 'EXPIRED'
                expired_delta = now - token.expires_at
                self.stdout.write(
                    f'  [{status}] {token.jti[:12]}... | '
                    f'{token.token_type:7s} | '
                    f'{token.user.email:30s} | '
                    f'expired {expired_delta.days}d {expired_delta.seconds // 3600}h ago'
                )

            if total_count > 20:
                self.stdout.write(f'  ... and {total_count - 20} more')
            self.stdout.write('')

        # Perform deletion
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN: No tokens were deleted'))
            self.stdout.write(f'Would delete {total_count} expired tokens')
        else:
            self.stdout.write('Deleting expired tokens...')

            try:
                deleted_count = TokenBlacklist.cleanup_expired()

                self.stdout.write('')
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully deleted {deleted_count} expired tokens'
                    )
                )

                # Log to application logger
                logger.info(
                    f'Cleaned up {deleted_count} expired JWT tokens from blacklist'
                )

            except Exception as e:
                self.stdout.write('')
                self.stdout.write(
                    self.style.ERROR(f'Error during cleanup: {str(e)}')
                )
                logger.error(f'Error cleaning up expired tokens: {str(e)}')
                raise

        # Show remaining token statistics
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Remaining Token Statistics:'))

        remaining_total = TokenBlacklist.objects.count()
        remaining_active = TokenBlacklist.objects.filter(
            is_revoked=False,
            expires_at__gte=now
        ).count()
        remaining_revoked = TokenBlacklist.objects.filter(is_revoked=True).count()

        self.stdout.write(f'Total tokens in database:     {remaining_total}')
        self.stdout.write(f'  - Active (valid):           {remaining_active}')
        self.stdout.write(f'  - Revoked (blacklisted):    {remaining_revoked}')

        # Calculate oldest token age
        oldest_token = TokenBlacklist.objects.order_by('created_at').first()
        if oldest_token:
            age = now - oldest_token.created_at
            self.stdout.write(f'  - Oldest token age:         {age.days} days')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Cleanup completed successfully!'))
