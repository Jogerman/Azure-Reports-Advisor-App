# Data migration to backfill is_savings_plan and commitment_category for existing recommendations

from django.db import migrations


def populate_savings_plan_flags(apps, schema_editor):
    """
    Backfill is_savings_plan and commitment_category for existing recommendations.

    This migration analyzes existing recommendations and categorizes them based on:
    - reservation_type field
    - commitment_term_years field
    - is_reservation_recommendation flag
    """
    Recommendation = apps.get_model('reports', 'Recommendation')

    # Mark all 'savings_plan' reservation_type as Savings Plans
    updated_sp = Recommendation.objects.filter(
        reservation_type='savings_plan'
    ).update(is_savings_plan=True)

    print(f"Marked {updated_sp} recommendations as savings plans")

    # Categorize pure reservations - 1 Year
    updated_1y = Recommendation.objects.filter(
        is_reservation_recommendation=True,
        reservation_type__in=['reserved_instance', 'reserved_capacity'],
        commitment_term_years=1
    ).update(
        commitment_category='pure_reservation_1y',
        is_savings_plan=False
    )

    print(f"Categorized {updated_1y} recommendations as pure_reservation_1y")

    # Categorize pure reservations - 3 Years
    updated_3y = Recommendation.objects.filter(
        is_reservation_recommendation=True,
        reservation_type__in=['reserved_instance', 'reserved_capacity'],
        commitment_term_years=3
    ).update(
        commitment_category='pure_reservation_3y',
        is_savings_plan=False
    )

    print(f"Categorized {updated_3y} recommendations as pure_reservation_3y")

    # Categorize pure savings plans
    updated_pure_sp = Recommendation.objects.filter(
        is_savings_plan=True,
        reservation_type='savings_plan'
    ).update(commitment_category='pure_savings_plan')

    print(f"Categorized {updated_pure_sp} recommendations as pure_savings_plan")

    # Log any uncategorized reservations for manual review
    uncategorized = Recommendation.objects.filter(
        is_reservation_recommendation=True,
        commitment_category='uncategorized'
    ).count()

    if uncategorized > 0:
        print(f"WARNING: {uncategorized} reservation recommendations remain uncategorized")


def reverse_populate(apps, schema_editor):
    """Reverse migration - reset to defaults."""
    Recommendation = apps.get_model('reports', 'Recommendation')
    Recommendation.objects.all().update(
        is_savings_plan=False,
        commitment_category='uncategorized'
    )
    print("Reset all recommendations to default values")


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0008_enhance_reservation_categorization'),
    ]

    operations = [
        migrations.RunPython(populate_savings_plan_flags, reverse_populate),
    ]
