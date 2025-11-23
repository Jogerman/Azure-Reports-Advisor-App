#!/usr/bin/env python
"""
Diagnostic script to connect to production Azure database and analyze state.
Run this locally to investigate Savings/Reservations sections issue.

Usage:
    python diagnose_database.py
"""

import os
import sys

# Add the project to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'azure_advisor_reports'))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings.production')

import django
django.setup()

from apps.reports.models import Report, Recommendation
from django.db.models import Count, Q, Sum
from django.db import connection

print("=" * 80)
print("AZURE ADVISOR REPORTS - DATABASE DIAGNOSTIC")
print("=" * 80)
print()

# Connection info
print(f"📡 DATABASE CONNECTION:")
print(f"   Host: {connection.settings_dict['HOST']}")
print(f"   Database: {connection.settings_dict['NAME']}")
print(f"   User: {connection.settings_dict['USER']}")
print()

# 1. Total counts
print("=" * 80)
print("📊 TOTAL COUNTS")
print("=" * 80)

total_reports = Report.objects.count()
total_recommendations = Recommendation.objects.count()

print(f"   Reports: {total_recommendations:,}")
print(f"   Recommendations: {total_recommendations:,}")
print()

if total_recommendations == 0:
    print("⚠️  WARNING: No recommendations found in database!")
    print("   This means either:")
    print("     1. Cleanup was executed and database is empty")
    print("     2. No CSV has been uploaded yet")
    print()
    print("   NEXT STEPS:")
    print("     1. Upload a CSV file via the UI")
    print("     2. Generate a new report")
    print("     3. Run this script again")
    print()
    sys.exit(0)

# 2. Categorization breakdown
print("=" * 80)
print("🏷️  CATEGORIZATION BREAKDOWN")
print("=" * 80)

categories = Recommendation.objects.values('commitment_category').annotate(
    count=Count('id'),
    total_savings=Sum('estimated_monthly_savings')
).order_by('-count')

print(f"   {'Category':<35} {'Count':>10} {'Monthly Savings':>20}")
print(f"   {'-'*35} {'-'*10} {'-'*20}")

for cat in categories:
    category = cat['commitment_category'] or 'None/NULL'
    count = cat['count']
    savings = cat['total_savings'] or 0
    percentage = (count / total_recommendations * 100) if total_recommendations > 0 else 0
    print(f"   {category:<35} {count:>10,} ({percentage:>5.1f}%)   ${savings:>15,.2f}")

print()

# 3. Check for problematic states
print("=" * 80)
print("⚠️  PROBLEMATIC DATA CHECK")
print("=" * 80)

uncategorized_count = Recommendation.objects.filter(
    Q(commitment_category='uncategorized') | Q(commitment_category__isnull=True)
).count()

if uncategorized_count > 0:
    percentage = (uncategorized_count / total_recommendations * 100)
    print(f"   ❌ Found {uncategorized_count:,} UNCATEGORIZED recommendations ({percentage:.1f}%)")
    print()
    print("   ISSUE: These recommendations won't appear in Savings/Reservations sections")
    print()
    print("   CAUSE: Likely created before ReservationAnalyzer integration or")
    print("          CSV was uploaded with older version before v2.0.19")
    print()
    print("   FIX OPTIONS:")
    print("      Option 1 (Recommended): Run backfill command")
    print("         python manage.py backfill_reservations")
    print()
    print("      Option 2: Delete and re-upload CSV")
    print("         python manage.py cleanup_test_data --force")
    print("         Then upload new CSV via UI")
    print()
else:
    print("   ✅ All recommendations are categorized!")
    print()

# 4. Check if we have categorized data for sections
print("=" * 80)
print("✅ SECTION DATA AVAILABILITY")
print("=" * 80)

has_pure_reservations = Recommendation.objects.filter(
    Q(commitment_category='pure_reservation_1y') |
    Q(commitment_category='pure_reservation_3y')
).exists()

pure_res_count = Recommendation.objects.filter(
    Q(commitment_category='pure_reservation_1y') |
    Q(commitment_category='pure_reservation_3y')
).count()

has_savings_plans = Recommendation.objects.filter(
    commitment_category='pure_savings_plan'
).exists()

sp_count = Recommendation.objects.filter(
    commitment_category='pure_savings_plan'
).count()

has_combined = Recommendation.objects.filter(
    Q(commitment_category='combined_sp_1y') |
    Q(commitment_category='combined_sp_3y')
).exists()

combined_count = Recommendation.objects.filter(
    Q(commitment_category='combined_sp_1y') |
    Q(commitment_category='combined_sp_3y')
).count()

print(f"   Pure Reservations (1Y/3Y):  {'YES ✓' if has_pure_reservations else 'NO ✗':>10}  ({pure_res_count:,} recs)")
print(f"   Savings Plans:              {'YES ✓' if has_savings_plans else 'NO ✗':>10}  ({sp_count:,} recs)")
print(f"   Combined Commitments:       {'YES ✓' if has_combined else 'NO ✗':>10}  ({combined_count:,} recs)")
print()

# 5. Recent reports check
print("=" * 80)
print("📋 RECENT REPORTS (Last 5)")
print("=" * 80)

recent_reports = Report.objects.order_by('-created_at')[:5]

if recent_reports.exists():
    print(f"   {'Report Name':<45} {'Status':<12} {'Recs':>6} {'Categorized':>12}")
    print(f"   {'-'*45} {'-'*12} {'-'*6} {'-'*12}")

    for report in recent_reports:
        rec_count = report.recommendations.count()
        categorized = report.recommendations.exclude(
            Q(commitment_category='uncategorized') | Q(commitment_category__isnull=True)
        ).count()

        name = report.report_name[:43] + '..' if len(report.report_name) > 45 else report.report_name
        print(f"   {name:<45} {report.status:<12} {rec_count:>6,} {categorized:>12,}")

    print()

    # Detailed analysis of latest report
    latest = recent_reports.first()
    print(f"🔍 LATEST REPORT DETAIL: {latest.report_name}")
    print(f"   Created: {latest.created_at}")
    print(f"   Status: {latest.status}")
    print(f"   Type: {latest.report_type}")
    print()

    report_cats = latest.recommendations.values('commitment_category').annotate(
        count=Count('id')
    ).order_by('-count')

    if report_cats:
        print("   Categories in this report:")
        for cat in report_cats:
            category = cat['commitment_category'] or 'None/NULL'
            count = cat['count']
            print(f"      - {category:<35}: {count:>4,} recommendations")
    else:
        print("   ⚠️  No recommendations in this report")

    print()
else:
    print("   No reports found")
    print()

# 6. Final summary
print("=" * 80)
print("📝 SUMMARY & RECOMMENDATIONS")
print("=" * 80)

if uncategorized_count > 0:
    print("❌ PROBLEM IDENTIFIED:")
    print(f"   {uncategorized_count:,} uncategorized recommendations found")
    print()
    print("🔧 SOLUTION:")
    print("   Run: python manage.py backfill_reservations")
    print("   This will analyze and categorize all existing recommendations")
    print()
elif not (has_pure_reservations or has_savings_plans or has_combined):
    print("⚠️  WARNING:")
    print("   Database has recommendations but NONE are categorized for")
    print("   Savings/Reservations sections")
    print()
    print("🔧 POSSIBLE CAUSES:")
    print("   1. CSV doesn't contain reservation/savings plan recommendations")
    print("   2. ReservationAnalyzer isn't detecting them (check keywords)")
    print()
    print("💡 NEXT STEPS:")
    print("   1. Check a sample recommendation text:")
    sample = Recommendation.objects.first()
    if sample:
        print(f"      Recommendation: {sample.recommendation[:100]}...")
        print(f"      Benefits: {sample.potential_benefits[:100] if sample.potential_benefits else 'None'}...")
    print()
    print("   2. Verify it contains keywords like:")
    print("      - 'reserved instance', 'reserved vm', 'reservation'")
    print("      - 'savings plan', 'compute savings plan'")
    print("      - '1 year', '3 year', 'commitment'")
    print()
else:
    print("✅ DATABASE LOOKS GOOD!")
    print()
    print(f"   - {pure_res_count:,} Pure Reservation recommendations")
    print(f"   - {sp_count:,} Savings Plan recommendations")
    print(f"   - {combined_count:,} Combined recommendations")
    print()
    print("📊 Savings/Reservations sections SHOULD appear in cost reports")
    print()
    print("If sections still don't show:")
    print("   1. Make sure you're viewing a COST OPTIMIZATION report")
    print("   2. Try regenerating the report (old reports won't update)")
    print("   3. Clear browser cache and reload")
    print("   4. Check backend logs for errors during report generation")
    print()

print("=" * 80)
print("Script completed successfully!")
print("=" * 80)
