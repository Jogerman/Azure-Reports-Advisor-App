# Generated migration to backfill reservation categorization for existing data
from django.db import migrations


def backfill_reservation_categories(apps, schema_editor):
    """
    Re-analyze all existing recommendations to populate reservation categorization fields.

    This migration fixes data from before the reservation enhancement was implemented.
    It re-analyzes recommendation text to properly categorize reservations.
    """
    Recommendation = apps.get_model('reports', 'Recommendation')

    # Import the analyzer (we'll use a simplified version in the migration)
    # to avoid dependencies on services that might change
    import re

    def analyze_recommendation(recommendation_text, benefits_text):
        """Simplified version of ReservationAnalyzer for migration."""
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

    # Get all recommendations
    recommendations = Recommendation.objects.all()
    total = recommendations.count()
    updated = 0
    skipped = 0

    print(f"\n{'='*60}")
    print(f"Backfilling reservation categories for {total} recommendations...")
    print(f"{'='*60}\n")

    for i, rec in enumerate(recommendations, 1):
        # Skip if already categorized correctly (not uncategorized)
        if rec.commitment_category and rec.commitment_category != 'uncategorized':
            skipped += 1
            if i % 100 == 0:
                print(f"Progress: {i}/{total} ({skipped} already categorized)")
            continue

        # Re-analyze
        recommendation_text = rec.recommendation or ''
        benefits_text = rec.potential_benefits or ''

        analysis = analyze_recommendation(recommendation_text, benefits_text)

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

        # Progress update every 100 records
        if i % 100 == 0:
            print(f"Progress: {i}/{total} ({updated} updated, {skipped} skipped)")

    print(f"\n{'='*60}")
    print(f"Backfill complete!")
    print(f"Total recommendations: {total}")
    print(f"Updated: {updated}")
    print(f"Already categorized (skipped): {skipped}")
    print(f"{'='*60}\n")

    # Show categorization breakdown
    categories = {}
    for rec in Recommendation.objects.all():
        cat = rec.commitment_category or 'uncategorized'
        categories[cat] = categories.get(cat, 0) + 1

    print("\nCategorization breakdown:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")
    print()


def reverse_backfill(apps, schema_editor):
    """
    Reverse operation: reset all fields to uncategorized.
    WARNING: This will lose all categorization data!
    """
    Recommendation = apps.get_model('reports', 'Recommendation')

    Recommendation.objects.all().update(
        is_reservation_recommendation=False,
        is_savings_plan=False,
        reservation_type=None,
        commitment_term_years=None,
        commitment_category='uncategorized'
    )

    print("All recommendations reset to uncategorized state.")


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0009_populate_savings_plan_flags'),
    ]

    operations = [
        migrations.RunPython(
            backfill_reservation_categories,
            reverse_code=reverse_backfill
        ),
    ]
