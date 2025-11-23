#!/usr/bin/env python
"""
Database Diagnostic Script for Azure Advisor Reports v2.0.19

This script connects to the production PostgreSQL database and provides
comprehensive diagnostics for:
1. Savings/Reservations categorization status
2. Recommendation distribution
3. Database schema verification
4. Recent reports analysis

Usage:
    python manage.py shell < scripts/diagnose_database_state.py

Or run directly from Django shell:
    python scripts/diagnose_database_state.py
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings.production')
django.setup()

from django.db import connection
from django.db.models import Count, Sum, Q
from apps.reports.models import Report, Recommendation

# ANSI Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print formatted section header."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")


def print_subheader(text):
    """Print formatted subsection header."""
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}{text}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-'*len(text)}{Colors.ENDC}")


def print_success(text):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(label, value, indent=0):
    """Print formatted info line."""
    spaces = "  " * indent
    print(f"{spaces}{Colors.OKBLUE}{label}:{Colors.ENDC} {value}")


def check_database_connection():
    """Verify database connection."""
    print_header("DATABASE CONNECTION CHECK")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
        print_success(f"Connected to PostgreSQL")
        print_info("Version", version)
        print_info("Database", connection.settings_dict['NAME'])
        print_info("Host", connection.settings_dict['HOST'])
        return True
    except Exception as e:
        print_error(f"Database connection failed: {str(e)}")
        return False


def analyze_overall_statistics():
    """Analyze overall report and recommendation statistics."""
    print_header("OVERALL STATISTICS")

    # Total counts
    total_reports = Report.objects.count()
    total_recommendations = Recommendation.objects.count()
    completed_reports = Report.objects.filter(status='completed').count()

    print_subheader("Report Counts")
    print_info("Total Reports", f"{total_reports:,}")
    print_info("Completed Reports", f"{completed_reports:,}")
    print_info("Total Recommendations", f"{total_recommendations:,}")

    if total_recommendations > 0:
        avg_per_report = total_recommendations / total_reports if total_reports > 0 else 0
        print_info("Average Recommendations per Report", f"{avg_per_report:.1f}")

    # Recent activity
    print_subheader("Recent Activity (Last 7 Days)")
    last_week = datetime.now() - timedelta(days=7)
    recent_reports = Report.objects.filter(created_at__gte=last_week).count()
    recent_recommendations = Recommendation.objects.filter(created_at__gte=last_week).count()

    print_info("Reports Created", f"{recent_reports:,}")
    print_info("Recommendations Created", f"{recent_recommendations:,}")


def analyze_commitment_categorization():
    """Analyze commitment_category field distribution."""
    print_header("COMMITMENT CATEGORIZATION ANALYSIS (v2.0.19 FEATURE)")

    # Overall categorization status
    total_recommendations = Recommendation.objects.count()

    if total_recommendations == 0:
        print_warning("No recommendations found in database!")
        return

    # Get categorization breakdown
    categorization = Recommendation.objects.values('commitment_category').annotate(
        count=Count('id'),
        total_savings=Sum('potential_savings')
    ).order_by('-count')

    print_subheader("Commitment Category Distribution")

    for item in categorization:
        category = item['commitment_category']
        count = item['count']
        total_savings = item['total_savings'] or Decimal('0')
        percentage = (count / total_recommendations) * 100

        # Color code based on category
        if category == 'uncategorized':
            color = Colors.WARNING
            symbol = "⚠"
        elif 'pure_reservation' in category:
            color = Colors.OKGREEN
            symbol = "✓"
        elif 'savings_plan' in category:
            color = Colors.OKCYAN
            symbol = "✓"
        else:
            color = Colors.ENDC
            symbol = " "

        print(f"{color}{symbol} {category:30s} {count:>6,} ({percentage:5.1f}%)  ${total_savings:>12,.2f}{Colors.ENDC}")

    # Check for categorization issues
    uncategorized = Recommendation.objects.filter(commitment_category='uncategorized').count()
    if uncategorized > 0:
        uncategorized_pct = (uncategorized / total_recommendations) * 100
        print_warning(f"{uncategorized:,} recommendations ({uncategorized_pct:.1f}%) are UNCATEGORIZED")
        print_warning("This may indicate:")
        print_warning("  - Old data from before v2.0.19 deployment")
        print_warning("  - CSV processing not calling ReservationAnalyzer")
        print_warning("  - ReservationAnalyzer pattern matching issues")
    else:
        print_success("All recommendations are properly categorized!")


def analyze_reservation_recommendations():
    """Analyze reservation-specific fields."""
    print_header("RESERVATION/SAVINGS PLAN DETAILED ANALYSIS")

    # Pure Reservations
    print_subheader("Pure Reservations (Traditional RI)")

    pure_1y = Recommendation.objects.filter(commitment_category='pure_reservation_1y')
    pure_3y = Recommendation.objects.filter(commitment_category='pure_reservation_3y')

    pure_1y_stats = pure_1y.aggregate(
        count=Count('id'),
        total_savings=Sum('potential_savings')
    )
    pure_3y_stats = pure_3y.aggregate(
        count=Count('id'),
        total_savings=Sum('potential_savings')
    )

    print_info("1-Year Reservations", f"{pure_1y_stats['count'] or 0:,}")
    print_info("  Total Annual Savings", f"${pure_1y_stats['total_savings'] or Decimal('0'):,.2f}", indent=1)

    print_info("3-Year Reservations", f"{pure_3y_stats['count'] or 0:,}")
    print_info("  Total Annual Savings", f"${pure_3y_stats['total_savings'] or Decimal('0'):,.2f}", indent=1)
    print_info("  Total 3-Year Commitment Savings", f"${(pure_3y_stats['total_savings'] or Decimal('0')) * 3:,.2f}", indent=1)

    # Savings Plans
    print_subheader("Pure Savings Plans")

    savings_plans = Recommendation.objects.filter(commitment_category='pure_savings_plan')
    sp_stats = savings_plans.aggregate(
        count=Count('id'),
        total_savings=Sum('potential_savings')
    )

    print_info("Count", f"{sp_stats['count'] or 0:,}")
    print_info("Total Annual Savings", f"${sp_stats['total_savings'] or Decimal('0'):,.2f}")

    # Combined Commitments
    print_subheader("Combined Commitments (Savings Plan + Reservations)")

    combined_1y = Recommendation.objects.filter(commitment_category='combined_sp_1y')
    combined_3y = Recommendation.objects.filter(commitment_category='combined_sp_3y')

    combined_1y_stats = combined_1y.aggregate(count=Count('id'), total_savings=Sum('potential_savings'))
    combined_3y_stats = combined_3y.aggregate(count=Count('id'), total_savings=Sum('potential_savings'))

    print_info("SP + 1Y Reservations", f"{combined_1y_stats['count'] or 0:,}")
    print_info("  Total Annual Savings", f"${combined_1y_stats['total_savings'] or Decimal('0'):,.2f}", indent=1)

    print_info("SP + 3Y Reservations", f"{combined_3y_stats['count'] or 0:,}")
    print_info("  Total Annual Savings", f"${combined_3y_stats['total_savings'] or Decimal('0'):,.2f}", indent=1)


def show_sample_recommendations():
    """Show sample recommendations for each commitment category."""
    print_header("SAMPLE RECOMMENDATIONS BY CATEGORY")

    categories = [
        'pure_reservation_1y',
        'pure_reservation_3y',
        'pure_savings_plan',
        'combined_sp_1y',
        'combined_sp_3y',
        'uncategorized'
    ]

    for category in categories:
        recs = Recommendation.objects.filter(commitment_category=category).order_by('-potential_savings')[:3]

        if recs.exists():
            print_subheader(f"{category.upper()} (Top 3 by Savings)")
            for i, rec in enumerate(recs, 1):
                print(f"  {i}. ${rec.potential_savings:,.2f}/yr - {rec.recommendation[:80]}...")
                if rec.commitment_term_years:
                    print(f"     Term: {rec.commitment_term_years} year(s)")
                if rec.reservation_type:
                    print(f"     Type: {rec.reservation_type}")
                print()


def analyze_recent_reports():
    """Analyze recent completed reports."""
    print_header("RECENT COMPLETED REPORTS ANALYSIS")

    recent_reports = Report.objects.filter(
        status='completed'
    ).order_by('-created_at')[:5]

    if not recent_reports.exists():
        print_warning("No completed reports found!")
        return

    for report in recent_reports:
        print_subheader(f"Report: {report.client.company_name} - {report.get_report_type_display()}")
        print_info("Created", report.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        print_info("Status", report.status)

        # Recommendation counts
        total_recs = report.recommendations.count()
        print_info("Total Recommendations", f"{total_recs:,}")

        if total_recs > 0:
            # Categorization breakdown
            cat_breakdown = report.recommendations.values('commitment_category').annotate(
                count=Count('id')
            ).order_by('-count')

            print_info("Categorization Breakdown", "")
            for item in cat_breakdown:
                pct = (item['count'] / total_recs) * 100
                print(f"    - {item['commitment_category']:30s}: {item['count']:>5,} ({pct:5.1f}%)")

            # Check if sections would appear
            has_pure_1y = report.recommendations.filter(commitment_category='pure_reservation_1y').exists()
            has_pure_3y = report.recommendations.filter(commitment_category='pure_reservation_3y').exists()
            has_combined = report.recommendations.filter(
                Q(commitment_category='combined_sp_1y') | Q(commitment_category='combined_sp_3y')
            ).exists()

            print_info("Template Sections Visible", "")
            print(f"    - Pure 1Y Section: {'YES ✓' if has_pure_1y else 'NO ✗'}")
            print(f"    - Pure 3Y Section: {'YES ✓' if has_pure_3y else 'NO ✗'}")
            print(f"    - Combined Section: {'YES ✓' if has_combined else 'NO ✗'}")


def check_schema_integrity():
    """Verify database schema has required fields."""
    print_header("SCHEMA INTEGRITY CHECK")

    # Check for new v2.0 fields
    print_subheader("Checking v2.0.19 Schema Fields")

    with connection.cursor() as cursor:
        # Check commitment_category field
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'recommendations'
              AND column_name IN ('commitment_category', 'is_savings_plan', 'commitment_term_years')
            ORDER BY column_name;
        """)

        fields = cursor.fetchall()

        if len(fields) == 3:
            print_success("All v2.0.19 schema fields present")
            for field_name, data_type, is_nullable in fields:
                print_info(f"  {field_name}", f"{data_type} (nullable: {is_nullable})")
        else:
            print_error(f"Missing schema fields! Found {len(fields)}/3 expected fields")

        # Check for default value
        cursor.execute("""
            SELECT column_default
            FROM information_schema.columns
            WHERE table_name = 'recommendations'
              AND column_name = 'commitment_category';
        """)
        default_value = cursor.fetchone()
        if default_value:
            print_info("  commitment_category default", default_value[0] or "NULL")


def generate_recommendations():
    """Generate actionable recommendations based on findings."""
    print_header("ACTIONABLE RECOMMENDATIONS")

    # Check uncategorized count
    uncategorized = Recommendation.objects.filter(commitment_category='uncategorized').count()
    total = Recommendation.objects.count()

    if uncategorized > 0:
        print_warning("ISSUE: Uncategorized Recommendations Detected")
        print()
        print("Possible causes:")
        print("  1. Old recommendations created before v2.0.19 deployment")
        print("  2. CSV processing not calling ReservationAnalyzer.analyze_recommendation()")
        print("  3. ReservationAnalyzer pattern matching needs improvement")
        print()
        print("Recommended actions:")
        print("  1. Check when these recommendations were created:")
        print("     python manage.py shell")
        print('     >>> from apps.reports.models import Recommendation')
        print('     >>> Recommendation.objects.filter(commitment_category="uncategorized").values("created_at").distinct()')
        print()
        print("  2. If old data: Re-run categorization with:")
        print("     python manage.py recategorize_reservations --all")
        print()
        print("  3. If new data: Check CSV processing logs for errors:")
        print("     docker logs azure-advisor-celery -f | grep -i 'reservation'")
    else:
        print_success("All recommendations properly categorized!")

    # Check if any cost reports exist
    cost_reports = Report.objects.filter(report_type='cost', status='completed').count()

    if cost_reports == 0:
        print_warning("No completed cost reports found - cannot verify template rendering")
    else:
        print_success(f"Found {cost_reports:,} completed cost reports")
        print()
        print("To verify template rendering:")
        print("  1. Download a recent cost report PDF")
        print("  2. Check for these sections:")
        print("     - 'Pure Reserved Instances - 3 Year Commitment'")
        print("     - 'Pure Reserved Instances - 1 Year Commitment'")
        print("     - 'Estrategia Combinada: Savings Plans + Reservas'")


def main():
    """Main diagnostic function."""
    print(f"{Colors.BOLD}")
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   Azure Advisor Reports v2.0.19 - Database Diagnostic Tool       ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    print(f"{Colors.ENDC}")

    # Run all diagnostic checks
    if not check_database_connection():
        return

    analyze_overall_statistics()
    check_schema_integrity()
    analyze_commitment_categorization()
    analyze_reservation_recommendations()
    show_sample_recommendations()
    analyze_recent_reports()
    generate_recommendations()

    print_header("DIAGNOSTIC COMPLETE")
    print()


if __name__ == '__main__':
    main()
