"""
Management command to fix absolute file paths in Report model.

This command fixes reports that have absolute paths stored in html_file and pdf_file
fields by converting them to relative paths that Django FileField expects.

Usage:
    python manage.py fix_report_paths
    python manage.py fix_report_paths --dry-run
"""

from django.core.management.base import BaseCommand
from apps.reports.models import Report
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix absolute file paths in Report model to relative paths'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Get all reports with file paths
        reports = Report.objects.exclude(html_file='').exclude(pdf_file='') | \
                  Report.objects.exclude(html_file__isnull=True).exclude(pdf_file__isnull=True)

        fixed_count = 0
        skipped_count = 0

        self.stdout.write(f'Found {reports.count()} reports with files')

        for report in reports:
            updated = False
            original_html = str(report.html_file) if report.html_file else None
            original_pdf = str(report.pdf_file) if report.pdf_file else None

            # Fix HTML file path
            if report.html_file:
                html_path = str(report.html_file)

                # Check if it has absolute path prefixes
                if '/app/media/' in html_path or html_path.startswith('/'):
                    # Remove absolute path prefixes
                    fixed_html = html_path.replace('/app/media/', '').replace('/media/', '')

                    # Remove leading slash if present
                    if fixed_html.startswith('/'):
                        fixed_html = fixed_html.lstrip('/')

                    self.stdout.write(
                        self.style.WARNING(f'\nReport {report.id}:')
                    )
                    self.stdout.write(f'  HTML: {html_path} -> {fixed_html}')

                    if not dry_run:
                        report.html_file = fixed_html
                        updated = True

            # Fix PDF file path
            if report.pdf_file:
                pdf_path = str(report.pdf_file)

                # Check if it has absolute path prefixes
                if '/app/media/' in pdf_path or pdf_path.startswith('/'):
                    # Remove absolute path prefixes
                    fixed_pdf = pdf_path.replace('/app/media/', '').replace('/media/', '')

                    # Remove leading slash if present
                    if fixed_pdf.startswith('/'):
                        fixed_pdf = fixed_pdf.lstrip('/')

                    if not original_html or '/app/media/' not in original_html:
                        self.stdout.write(
                            self.style.WARNING(f'\nReport {report.id}:')
                        )
                    self.stdout.write(f'  PDF: {pdf_path} -> {fixed_pdf}')

                    if not dry_run:
                        report.pdf_file = fixed_pdf
                        updated = True

            # Save if updated
            if updated:
                if not dry_run:
                    report.save(update_fields=['html_file', 'pdf_file'])
                    self.stdout.write(self.style.SUCCESS('  ✓ Fixed'))
                fixed_count += 1
            else:
                skipped_count += 1

        # Summary
        self.stdout.write('\n' + '=' * 60)
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'\nDRY RUN COMPLETE:'))
            self.stdout.write(f'  Would fix: {fixed_count} reports')
            self.stdout.write(f'  Would skip: {skipped_count} reports')
            self.stdout.write('\nRun without --dry-run to apply changes')
        else:
            self.stdout.write(self.style.SUCCESS(f'\nCOMPLETE:'))
            self.stdout.write(self.style.SUCCESS(f'  Fixed: {fixed_count} reports'))
            self.stdout.write(f'  Skipped: {skipped_count} reports (already correct)')
