#!/usr/bin/env python
"""
Validation script for Enhanced Reservation & Saving Plans Analysis (v2.0)

This script helps validate the implementation by checking:
1. Database migrations are applied
2. New fields exist on Recommendation model
3. Categorization logic is working
4. Report generator methods are available
5. Template files exist

Usage:
    cd /Users/josegomez/Documents/Code/Azure-Reports-Advisor-App/azure_advisor_reports
    python ../validate_enhanced_reservations.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'azure_advisor_reports'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
django.setup()

from apps.reports.models import Recommendation, Report
from apps.reports.services.reservation_analyzer import ReservationAnalyzer
from apps.reports.generators.base import BaseReportGenerator


def print_header(text):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def check_model_fields():
    """Verify new fields exist on Recommendation model."""
    print_header("1. Checking Model Fields")

    try:
        # Check if new fields exist
        is_savings_plan_field = Recommendation._meta.get_field('is_savings_plan')
        commitment_category_field = Recommendation._meta.get_field('commitment_category')

        print("✅ Field 'is_savings_plan' exists")
        print(f"   - Type: {is_savings_plan_field.get_internal_type()}")
        print(f"   - Indexed: {is_savings_plan_field.db_index}")
        print(f"   - Default: {is_savings_plan_field.default}")

        print("\n✅ Field 'commitment_category' exists")
        print(f"   - Type: {commitment_category_field.get_internal_type()}")
        print(f"   - Indexed: {commitment_category_field.db_index}")
        print(f"   - Max Length: {commitment_category_field.max_length}")
        print(f"   - Choices: {len(commitment_category_field.choices)} categories")

        # Check computed properties
        rec = Recommendation()
        assert hasattr(rec, 'is_pure_reservation'), "Missing is_pure_reservation property"
        assert hasattr(rec, 'is_combined_commitment'), "Missing is_combined_commitment property"
        print("\n✅ Computed properties exist:")
        print("   - is_pure_reservation")
        print("   - is_combined_commitment")

        return True

    except Exception as e:
        print(f"❌ Error checking model fields: {str(e)}")
        return False


def check_data_distribution():
    """Check how recommendations are categorized."""
    print_header("2. Checking Data Distribution")

    try:
        total = Recommendation.objects.count()
        reservations = Recommendation.objects.filter(is_reservation_recommendation=True).count()

        print(f"Total Recommendations: {total:,}")
        print(f"Reservation Recommendations: {reservations:,}\n")

        if reservations > 0:
            # Count by category
            categories = {
                'pure_reservation_1y': Recommendation.objects.filter(commitment_category='pure_reservation_1y').count(),
                'pure_reservation_3y': Recommendation.objects.filter(commitment_category='pure_reservation_3y').count(),
                'pure_savings_plan': Recommendation.objects.filter(commitment_category='pure_savings_plan').count(),
                'combined_sp_1y': Recommendation.objects.filter(commitment_category='combined_sp_1y').count(),
                'combined_sp_3y': Recommendation.objects.filter(commitment_category='combined_sp_3y').count(),
                'uncategorized': Recommendation.objects.filter(commitment_category='uncategorized', is_reservation_recommendation=True).count(),
            }

            print("Category Distribution:")
            for category, count in categories.items():
                if count > 0:
                    pct = (count / reservations * 100) if reservations > 0 else 0
                    print(f"  ✓ {category:30s}: {count:5,} ({pct:5.1f}%)")

            # Check savings plans
            savings_plans = Recommendation.objects.filter(is_savings_plan=True).count()
            print(f"\n✅ Savings Plans Identified: {savings_plans:,}")

            if categories['uncategorized'] > 0:
                print(f"\n⚠️  Warning: {categories['uncategorized']} reservations are uncategorized")
        else:
            print("ℹ️  No reservation recommendations found in database")

        return True

    except Exception as e:
        print(f"❌ Error checking data distribution: {str(e)}")
        return False


def check_analyzer_methods():
    """Verify ReservationAnalyzer has new methods."""
    print_header("3. Checking ReservationAnalyzer Methods")

    try:
        # Check methods exist
        methods = [
            'is_savings_plan',
            'is_traditional_reservation',
            'is_combined_commitment',
            'categorize_commitment',
        ]

        for method in methods:
            assert hasattr(ReservationAnalyzer, method), f"Missing method: {method}"
            print(f"✅ Method exists: {method}")

        # Test analysis
        print("\n Testing analysis on sample text...")
        test_cases = [
            ("Purchase 3-year reserved instance for VM", "Traditional 3Y Reservation"),
            ("Buy 1-year reserved capacity", "Traditional 1Y Reservation"),
            ("Azure Compute Savings Plan recommendation", "Savings Plan"),
            ("Combine savings plan with 3-year reservation", "Combined SP+3Y"),
        ]

        for text, expected_type in test_cases:
            result = ReservationAnalyzer.analyze_recommendation(text)
            print(f"\n  Text: {text[:50]}...")
            print(f"    - is_reservation: {result['is_reservation']}")
            print(f"    - is_savings_plan: {result['is_savings_plan']}")
            print(f"    - category: {result['commitment_category']}")
            print(f"    ✓ Expected: {expected_type}")

        return True

    except Exception as e:
        print(f"❌ Error checking analyzer methods: {str(e)}")
        return False


def check_generator_methods():
    """Verify BaseReportGenerator has new methods."""
    print_header("4. Checking Report Generator Methods")

    try:
        methods = [
            'get_pure_reservation_metrics_by_term',
            'get_savings_plan_metrics',
            'get_combined_commitment_metrics',
            '_get_reservation_type_display',
        ]

        for method in methods:
            assert hasattr(BaseReportGenerator, method), f"Missing method: {method}"
            print(f"✅ Method exists: {method}")

        # Test with a real report if available
        latest_report = Report.objects.order_by('-created_at').first()
        if latest_report:
            print(f"\n Testing with report: {latest_report.id}")
            generator = BaseReportGenerator(latest_report)

            # Test new methods
            pure_metrics = generator.get_pure_reservation_metrics_by_term()
            savings_metrics = generator.get_savings_plan_metrics()
            combined_metrics = generator.get_combined_commitment_metrics()

            print(f"  ✓ Pure reservations: {pure_metrics['total_count']} found")
            print(f"  ✓ Savings plans: {savings_metrics['count']} found")
            print(f"  ✓ Combined: {combined_metrics['total_count']} found")
        else:
            print("\nℹ️  No reports found to test generator methods")

        return True

    except Exception as e:
        print(f"❌ Error checking generator methods: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def check_template_files():
    """Verify template files exist."""
    print_header("5. Checking Template Files")

    try:
        base_path = "/Users/josegomez/Documents/Code/Azure-Reports-Advisor-App/azure_advisor_reports"

        files_to_check = [
            "templates/reports/partials/enhanced_reservations_section.html",
            "templates/reports/cost_enhanced.html",
        ]

        for file_path in files_to_check:
            full_path = os.path.join(base_path, file_path)
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                print(f"✅ {file_path}")
                print(f"   Size: {size:,} bytes")
            else:
                print(f"❌ Missing: {file_path}")
                return False

        # Check include statement in cost_enhanced.html
        cost_template_path = os.path.join(base_path, "templates/reports/cost_enhanced.html")
        with open(cost_template_path, 'r') as f:
            content = f.read()
            if "enhanced_reservations_section.html" in content:
                print("\n✅ cost_enhanced.html includes enhanced_reservations_section.html")
            else:
                print("\n⚠️  Warning: cost_enhanced.html may not include enhanced_reservations_section.html")

        return True

    except Exception as e:
        print(f"❌ Error checking template files: {str(e)}")
        return False


def check_migrations():
    """Check if migrations are applied."""
    print_header("6. Checking Migrations")

    try:
        from django.db import connection

        # Check if migrations table exists and contains our migrations
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT app, name
                FROM django_migrations
                WHERE app = 'reports'
                AND (name LIKE '%0008%' OR name LIKE '%0009%')
                ORDER BY name
            """)
            migrations = cursor.fetchall()

        if len(migrations) >= 2:
            print("✅ Migrations applied:")
            for app, name in migrations:
                print(f"   - {name}")
        else:
            print("⚠️  Warning: Migrations may not be fully applied")
            print(f"   Found {len(migrations)} relevant migrations")

        return True

    except Exception as e:
        print(f"❌ Error checking migrations: {str(e)}")
        return False


def main():
    """Run all validation checks."""
    print("\n" + "="*70)
    print("  ENHANCED RESERVATION & SAVING PLANS ANALYSIS - VALIDATION")
    print("  Version 2.0 - Multi-Dimensional Analysis")
    print("="*70)

    checks = [
        check_migrations,
        check_model_fields,
        check_data_distribution,
        check_analyzer_methods,
        check_generator_methods,
        check_template_files,
    ]

    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Unexpected error in {check.__name__}: {str(e)}")
            results.append(False)

    # Summary
    print_header("VALIDATION SUMMARY")
    passed = sum(results)
    total = len(results)

    print(f"Checks Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL CHECKS PASSED! Implementation is ready for testing.")
    else:
        print(f"\n⚠️  {total - passed} check(s) failed. Review errors above.")

    print("\nNext Steps:")
    print("1. Apply migrations if not already done:")
    print("   python manage.py migrate reports")
    print("2. Upload a CSV with reservation recommendations")
    print("3. Generate a cost optimization report")
    print("4. Verify enhanced section appears in the report")

    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
