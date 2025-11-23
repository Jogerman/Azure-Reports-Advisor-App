"""
Management command to clean up test/development report data.
Preserves users, clients, configurations while removing outdated reports.

Usage:
    python manage.py cleanup_test_data --dry-run  # Test first
    python manage.py cleanup_test_data            # Execute cleanup
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.reports.models import Report, Recommendation
from apps.clients.models import Client
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Clean up test/development reports and recommendations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate cleanup without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        # Get current counts
        report_count = Report.objects.count()
        recommendation_count = Recommendation.objects.count()
        client_count = Client.objects.count()
        user_count = User.objects.count()

        self.stdout.write(self.style.WARNING('\n' + '=' * 60))
        self.stdout.write(self.style.WARNING('DATA CLEANUP SUMMARY'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write('')
        self.stdout.write(self.style.ERROR(f'Reports to DELETE: {report_count:,}'))
        self.stdout.write(self.style.ERROR(f'Recommendations to DELETE: {recommendation_count:,}'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Clients to PRESERVE: {client_count:,}'))
        self.stdout.write(self.style.SUCCESS(f'Users to PRESERVE: {user_count:,}'))
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.NOTICE('[DRY RUN MODE] No changes will be made'))
            self.stdout.write('')
            self.stdout.write('What would be deleted:')
            self.stdout.write(f'  - {report_count:,} reports (including CSV, HTML, PDF files)')
            self.stdout.write(f'  - {recommendation_count:,} recommendations')
            self.stdout.write('')
            self.stdout.write('What would be preserved:')
            self.stdout.write(f'  - {client_count:,} clients')
            self.stdout.write(f'  - {user_count:,} users')
            self.stdout.write(f'  - All Azure subscriptions')
            self.stdout.write(f'  - All configurations')
            self.stdout.write('')
            return

        # Confirmation prompt
        if not force:
            self.stdout.write(self.style.WARNING('⚠️  This action cannot be undone!'))
            self.stdout.write('')
            confirm = input('Type "DELETE ALL REPORTS" to proceed: ')
            if confirm != 'DELETE ALL REPORTS':
                self.stdout.write(self.style.ERROR('\n✗ Cleanup cancelled'))
                return

        # Execute cleanup in transaction
        try:
            with transaction.atomic():
                self.stdout.write('')
                self.stdout.write('Deleting reports and recommendations...')
                self.stdout.write('')

                # Delete all reports (CASCADE deletes recommendations automatically)
                deleted = Report.objects.all().delete()

                self.stdout.write(self.style.SUCCESS('✓ Deletion Summary:'))
                self.stdout.write('')
                for model, count in deleted[1].items():
                    self.stdout.write(f'  - {model}: {count:,}')
                self.stdout.write('')

                # Verify cleanup
                remaining_reports = Report.objects.count()
                remaining_recs = Recommendation.objects.count()

                if remaining_reports == 0 and remaining_recs == 0:
                    self.stdout.write('=' * 60)
                    self.stdout.write(self.style.SUCCESS('✓ CLEANUP COMPLETED SUCCESSFULLY'))
                    self.stdout.write('=' * 60)
                    self.stdout.write('')
                    self.stdout.write('Next steps:')
                    self.stdout.write('  1. Upload a new CSV file')
                    self.stdout.write('  2. Generate a new report')
                    self.stdout.write('  3. Verify Savings/Reservations sections appear')
                    self.stdout.write('')
                else:
                    raise Exception(
                        f'Cleanup incomplete: {remaining_reports} reports, '
                        f'{remaining_recs} recommendations remain'
                    )

        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'✗ Cleanup failed: {str(e)}'))
            self.stdout.write('')
            raise
