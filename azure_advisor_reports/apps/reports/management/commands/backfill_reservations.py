"""
Management command to backfill reservation categorization for existing recommendations.

This command executes the same logic as migration 0010_backfill_reservation_categories
but as a standalone management command that can be run manually without blocking
the application startup.

Usage:
    python manage.py backfill_reservations
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.reports.models import Recommendation


class Command(BaseCommand):
    help = 'Backfill reservation categorization for existing recommendations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch (default: 100)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-categorization of all records (even already categorized ones)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        force = options['force']

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS('Starting Reservation Backfill Process'))
        self.stdout.write("=" * 60)
        self.stdout.write("")

        # Get all recommendations
        recommendations = Recommendation.objects.all()
        total = recommendations.count()
        updated = 0
        skipped = 0
        batch_num = 0

        self.stdout.write(f"Total recommendations to process: {total:,}")
        self.stdout.write("")

        # Process in batches
        for i in range(0, total, batch_size):
            batch_num += 1
            batch = recommendations[i:i + batch_size]

            with transaction.atomic():
                for rec in batch:
                    # Skip if already categorized correctly (not uncategorized) and not forcing
                    if not force and rec.commitment_category and rec.commitment_category != 'uncategorized':
                        skipped += 1
                        continue

                    # Re-analyze
                    recommendation_text = rec.recommendation or ''
                    benefits_text = rec.potential_benefits or ''

                    analysis = self.analyze_recommendation(recommendation_text, benefits_text)

                    # Update fields
                    rec.is_reservation_recommendation = analysis['is_reservation']
                    rec.is_savings_plan = analysis['is_savings_plan']
                    rec.reservation_type = analysis['reservation_type']
                    rec.commitment_term_years = analysis['commitment_term_years']
                    rec.commitment_category = analysis['commitment_category']

                    rec.save(update_fields=[
                        'is_reservation_recommendation',
                        'is_savings_plan',
                        'reservation_type',
                        'commitment_term_years',
                        'commitment_category'
                    ])

                    updated += 1

            # Progress update after each batch
            current_position = min(i + batch_size, total)
            progress_pct = (current_position / total) * 100
            self.stdout.write(
                f"Batch {batch_num}: Processed {current_position:,}/{total:,} "
                f"({progress_pct:.1f}%) - Updated: {updated:,}, Skipped: {skipped:,}"
            )

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS('Backfill Complete!'))
        self.stdout.write("=" * 60)
        self.stdout.write(f"Total recommendations: {total:,}")
        self.stdout.write(f"Updated: {updated:,}")
        self.stdout.write(f"Already categorized (skipped): {skipped:,}")
        self.stdout.write("")

        # Show categorization breakdown
        self.stdout.write(self.style.SUCCESS("Categorization Breakdown:"))
        categories = {}
        for rec in Recommendation.objects.all():
            cat = rec.commitment_category or 'uncategorized'
            categories[cat] = categories.get(cat, 0) + 1

        for cat, count in sorted(categories.items()):
            self.stdout.write(f"  {cat}: {count:,}")
        self.stdout.write("")

    def analyze_recommendation(self, recommendation_text, benefits_text):
        """Simplified version of ReservationAnalyzer for backfill."""
        combined_text = f"{recommendation_text} {benefits_text}".lower()

        # Check if it's a reservation
        reservation_keywords = [
            'reserved instance', 'reserved vm', 'reserved capacity',
            'reservation', 'reserve capacity', 'ri recommendation',
            'commit to', 'commitment'
        ]
        is_reservation = any(keyword in combined_text for keyword in reservation_keywords)

        # Check if it's a savings plan
        savings_plan_keywords = [
            'savings plan', 'compute savings plan', 'saving plan',
            'savings plans'
        ]
        is_savings_plan = any(keyword in combined_text for keyword in savings_plan_keywords)

        # Determine commitment term
        commitment_term_years = None
        if 'three year' in combined_text or '3 year' in combined_text or '3-year' in combined_text:
            commitment_term_years = 3
        elif 'one year' in combined_text or '1 year' in combined_text or '1-year' in combined_text:
            commitment_term_years = 1

        # Determine reservation type
        reservation_type = None
        if is_reservation and not is_savings_plan:
            if 'vm' in combined_text or 'virtual machine' in combined_text:
                reservation_type = 'reserved_instance'
            else:
                reservation_type = 'reserved_capacity'
        elif is_savings_plan:
            reservation_type = 'savings_plan'

        # Determine commitment category
        commitment_category = 'uncategorized'

        if is_savings_plan and not is_reservation:
            commitment_category = 'pure_savings_plan'
        elif is_reservation and not is_savings_plan:
            if commitment_term_years == 3:
                commitment_category = 'pure_reservation_3y'
            elif commitment_term_years == 1:
                commitment_category = 'pure_reservation_1y'
            else:
                commitment_category = 'pure_reservation_unknown'
        elif is_savings_plan and is_reservation:
            # Combined strategy
            if commitment_term_years == 3:
                commitment_category = 'combined_sp_3y'
            elif commitment_term_years == 1:
                commitment_category = 'combined_sp_1y'
            else:
                commitment_category = 'combined_sp_unknown'

        return {
            'is_reservation': is_reservation,
            'is_savings_plan': is_savings_plan,
            'reservation_type': reservation_type,
            'commitment_term_years': commitment_term_years,
            'commitment_category': commitment_category
        }
