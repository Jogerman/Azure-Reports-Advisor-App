"""
Management command to fix reports stuck in processing status.

This command identifies reports that have been stuck in 'processing' or 'generating'
status for too long and marks them as 'failed' with an appropriate error message.

This situation can occur when:
- A Celery worker crashes during processing
- A report is deleted while being processed
- The processing task times out

Usage:
    python manage.py fix_stuck_reports
    python manage.py fix_stuck_reports --dry-run
    python manage.py fix_stuck_reports --hours 2
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.reports.models import Report
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix reports stuck in processing or generating status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=1,
            help='Number of hours after which a report is considered stuck (default: 1)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        hours = options['hours']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Calculate the cutoff time
        cutoff_time = timezone.now() - timedelta(hours=hours)

        # Find stuck reports
        stuck_reports = Report.objects.filter(
            status__in=['processing', 'generating'],
            updated_at__lt=cutoff_time
        ).order_by('updated_at')

        total_count = stuck_reports.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS(
                f'\nNo stuck reports found (checked for reports older than {hours} hour(s))'
            ))
            return

        self.stdout.write(
            self.style.WARNING(
                f'\nFound {total_count} stuck report(s) older than {hours} hour(s):\n'
            )
        )

        # Process each stuck report
        fixed_count = 0
        for report in stuck_reports:
            time_stuck = timezone.now() - report.updated_at
            hours_stuck = time_stuck.total_seconds() / 3600

            self.stdout.write(
                f'\n  Report: {report.name} ({report.id})'
            )
            self.stdout.write(
                f'    Status: {report.status}'
            )
            self.stdout.write(
                f'    Client: {report.client.name if report.client else "N/A"}'
            )
            self.stdout.write(
                f'    Created: {report.created_at.strftime("%Y-%m-%d %H:%M:%S")}'
            )
            self.stdout.write(
                f'    Last Updated: {report.updated_at.strftime("%Y-%m-%d %H:%M:%S")}'
            )
            self.stdout.write(
                self.style.ERROR(
                    f'    Time Stuck: {hours_stuck:.1f} hours'
                )
            )

            if not dry_run:
                # Update the report status
                original_status = report.status
                report.status = 'failed'
                report.error_message = (
                    f'Report was stuck in "{original_status}" status for {hours_stuck:.1f} hours. '
                    f'Processing was automatically cancelled due to timeout. '
                    f'Please try uploading the CSV file again.'
                )
                report.save(update_fields=['status', 'error_message', 'updated_at'])

                self.stdout.write(
                    self.style.SUCCESS('    ✓ Marked as failed')
                )
                fixed_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING('    → Would mark as failed')
                )

        # Summary
        self.stdout.write('\n' + '=' * 70)
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN COMPLETE:'))
            self.stdout.write(f'  Would fix: {total_count} stuck report(s)')
            self.stdout.write('\nRun without --dry-run to apply changes')
        else:
            self.stdout.write(self.style.SUCCESS('\nCOMPLETE:'))
            self.stdout.write(self.style.SUCCESS(f'  Fixed: {fixed_count} stuck report(s)'))
            self.stdout.write(
                '\nUsers can now retry uploading their CSV files for these reports.'
            )
        self.stdout.write('=' * 70 + '\n')
