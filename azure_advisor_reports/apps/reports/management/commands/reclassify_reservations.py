"""
Management command to reclassify existing recommendations with correct
is_savings_plan and commitment_category values.

This command fixes recommendations that were created before the bug fix in tasks.py,
where the new fields (is_savings_plan and commitment_category) were not being populated.

Usage:
    python manage.py reclassify_reservations --dry-run
    python manage.py reclassify_reservations --report-id <UUID>
    python manage.py reclassify_reservations
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from apps.reports.models import Recommendation, Report
from apps.reports.services.reservation_analyzer import ReservationAnalyzer
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Reclassify existing recommendations with enhanced Savings Plan categorization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--report-id',
            type=str,
            help='Specific report ID to reclassify (optional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without saving to database',
        )
        parser.add_argument(
            '--only-uncategorized',
            action='store_true',
            help='Only process recommendations currently marked as uncategorized',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of recommendations to process in each batch (default: 100)',
        )

    def handle(self, *args, **options):
        report_id = options.get('report_id')
        dry_run = options.get('dry_run')
        only_uncategorized = options.get('only_uncategorized')
        batch_size = options.get('batch_size')

        self.stdout.write(self.style.HTTP_INFO('=' * 80))
        self.stdout.write(self.style.HTTP_INFO('RECLASSIFYING RESERVATION RECOMMENDATIONS'))
        self.stdout.write(self.style.HTTP_INFO('=' * 80))

        # Build query
        queryset = Recommendation.objects.all()

        if report_id:
            try:
                report = Report.objects.get(id=report_id)
                queryset = queryset.filter(report=report)
                self.stdout.write(f'Target: Report {report_id} - {report.title or report.report_type}')
            except Report.DoesNotExist:
                raise CommandError(f'Report with ID {report_id} not found')
        else:
            self.stdout.write('Target: ALL recommendations in database')

        if only_uncategorized:
            queryset = queryset.filter(commitment_category='uncategorized')
            self.stdout.write('Filter: Only uncategorized recommendations')

        total = queryset.count()
        self.stdout.write(f'Total recommendations to process: {total}')

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  DRY RUN MODE - No changes will be saved'))

        self.stdout.write(self.style.HTTP_INFO('-' * 80))

        # Statistics
        stats = {
            'processed': 0,
            'updated': 0,
            'unchanged': 0,
            'errors': 0,
            'categorized': {
                'pure_reservation_1y': 0,
                'pure_reservation_3y': 0,
                'pure_savings_plan': 0,
                'combined_sp_1y': 0,
                'combined_sp_3y': 0,
                'uncategorized': 0,
            }
        }

        # Process in batches
        for offset in range(0, total, batch_size):
            batch = queryset[offset:offset + batch_size]

            with transaction.atomic():
                for rec in batch:
                    stats['processed'] += 1

                    try:
                        # Reanalyze the recommendation
                        analysis = ReservationAnalyzer.analyze_recommendation(
                            rec.recommendation,
                            rec.potential_benefits
                        )

                        # Check if values would change
                        old_category = rec.commitment_category
                        new_category = analysis['commitment_category']
                        old_sp = rec.is_savings_plan
                        new_sp = analysis['is_savings_plan']
                        old_is_res = rec.is_reservation_recommendation
                        new_is_res = analysis['is_reservation']

                        # Determine if update needed
                        needs_update = (
                            old_category != new_category or
                            old_sp != new_sp or
                            old_is_res != new_is_res
                        )

                        if needs_update:
                            # Log the change
                            if old_category != new_category:
                                self.stdout.write(
                                    f'  [{rec.id}] {old_category} → {self.style.SUCCESS(new_category)}'
                                )
                            if old_sp != new_sp:
                                self.stdout.write(
                                    f'    is_savings_plan: {old_sp} → {new_sp}'
                                )

                            if not dry_run:
                                # Update all reservation-related fields
                                rec.is_reservation_recommendation = analysis['is_reservation']
                                rec.reservation_type = analysis['reservation_type']
                                rec.commitment_term_years = analysis['commitment_term_years']
                                rec.is_savings_plan = analysis['is_savings_plan']
                                rec.commitment_category = analysis['commitment_category']
                                rec.save(update_fields=[
                                    'is_reservation_recommendation',
                                    'reservation_type',
                                    'commitment_term_years',
                                    'is_savings_plan',
                                    'commitment_category'
                                ])

                            stats['updated'] += 1
                            stats['categorized'][new_category] += 1
                        else:
                            stats['unchanged'] += 1

                        # Progress indicator
                        if stats['processed'] % 100 == 0:
                            self.stdout.write(
                                f'Progress: {stats["processed"]}/{total} processed, '
                                f'{stats["updated"]} updated...'
                            )

                    except Exception as e:
                        stats['errors'] += 1
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ ERROR processing {rec.id}: {str(e)}')
                        )
                        logger.error(f'Reclassification error for {rec.id}: {str(e)}', exc_info=True)

        # Print summary
        self.stdout.write(self.style.HTTP_INFO('-' * 80))
        self.stdout.write(self.style.HTTP_INFO('SUMMARY'))
        self.stdout.write(self.style.HTTP_INFO('-' * 80))
        self.stdout.write(f'Total processed:     {stats["processed"]}')
        self.stdout.write(f'Updated:             {stats["updated"]}')
        self.stdout.write(f'Unchanged:           {stats["unchanged"]}')
        self.stdout.write(f'Errors:              {stats["errors"]}')

        if stats['updated'] > 0:
            self.stdout.write('\nNew Categorization Distribution:')
            for category, count in stats['categorized'].items():
                if count > 0:
                    self.stdout.write(f'  {category:25s}: {count}')

        self.stdout.write(self.style.HTTP_INFO('-' * 80))

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'✓ DRY RUN COMPLETE: Would have updated {stats["updated"]} recommendations'
            ))
            self.stdout.write('Run without --dry-run to apply changes')
        else:
            self.stdout.write(self.style.SUCCESS(
                f'✓ RECLASSIFICATION COMPLETE: {stats["updated"]} recommendations updated'
            ))

            if stats['errors'] > 0:
                self.stdout.write(self.style.WARNING(
                    f'⚠️  {stats["errors"]} errors occurred - check logs for details'
                ))

        self.stdout.write(self.style.HTTP_INFO('=' * 80))
