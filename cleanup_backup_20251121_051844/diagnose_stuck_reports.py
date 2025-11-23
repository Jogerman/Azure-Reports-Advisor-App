"""
Diagnostic script to check for stuck reports in production.

This script connects to the production database and checks:
1. Reports stuck in 'processing' or 'generating' status
2. Reports that are completed but missing HTML/PDF files
3. Reports by type (executive, cost, security) that failed generation
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings.production')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'azure_advisor_reports'))
django.setup()

from apps.reports.models import Report
from django.utils import timezone

def print_separator(char="=", length=80):
    print(char * length)

def diagnose_stuck_reports():
    print_separator()
    print("DIAGNOSING STUCK REPORTS IN PRODUCTION")
    print_separator()
    print(f"Current time: {timezone.now()}")
    print()

    # 1. Check for reports stuck in 'processing' status
    print_separator("-")
    print("1. REPORTS STUCK IN 'PROCESSING' STATUS")
    print_separator("-")

    processing_reports = Report.objects.filter(status='processing').order_by('-processing_started_at')
    print(f"\nFound {processing_reports.count()} reports in 'processing' status:\n")

    for report in processing_reports:
        time_stuck = timezone.now() - report.processing_started_at if report.processing_started_at else None
        print(f"ID: {report.id}")
        print(f"  Client: {report.client.company_name}")
        print(f"  Report Type: {report.get_report_type_display()}")
        print(f"  Started Processing: {report.processing_started_at}")
        print(f"  Time Stuck: {time_stuck}")
        print(f"  CSV File: {report.csv_file.name if report.csv_file else 'None'}")
        print(f"  Recommendations: {report.recommendations.count()}")
        print(f"  Error Message: {report.error_message or 'None'}")
        print()

    # 2. Check for reports stuck in 'generating' status
    print_separator("-")
    print("2. REPORTS STUCK IN 'GENERATING' STATUS")
    print_separator("-")

    generating_reports = Report.objects.filter(status='generating').order_by('-updated_at')
    print(f"\nFound {generating_reports.count()} reports in 'generating' status:\n")

    for report in generating_reports:
        time_stuck = timezone.now() - report.updated_at
        print(f"ID: {report.id}")
        print(f"  Client: {report.client.company_name}")
        print(f"  Report Type: {report.get_report_type_display()}")
        print(f"  Last Updated: {report.updated_at}")
        print(f"  Time Stuck: {time_stuck}")
        print(f"  Recommendations: {report.recommendations.count()}")
        print(f"  HTML File: {report.html_file.name if report.html_file else 'None'}")
        print(f"  PDF File: {report.pdf_file.name if report.pdf_file else 'None'}")
        print()

    # 3. Check completed reports without generated files (last 24 hours)
    print_separator("-")
    print("3. COMPLETED REPORTS WITHOUT GENERATED FILES (LAST 24 HOURS)")
    print_separator("-")

    cutoff_time = timezone.now() - timedelta(hours=24)
    incomplete_files = Report.objects.filter(
        status='completed',
        processing_completed_at__gte=cutoff_time
    ).exclude(
        html_file__isnull=False,
        pdf_file__isnull=False
    ).order_by('-processing_completed_at')

    print(f"\nFound {incomplete_files.count()} completed reports without files:\n")

    for report in incomplete_files:
        print(f"ID: {report.id}")
        print(f"  Client: {report.client.company_name}")
        print(f"  Report Type: {report.get_report_type_display()}")
        print(f"  Completed: {report.processing_completed_at}")
        print(f"  Recommendations: {report.recommendations.count()}")
        print(f"  HTML File: {'Yes' if report.html_file else 'NO'}")
        print(f"  PDF File: {'Yes' if report.pdf_file else 'NO'}")
        print()

    # 4. Check reports by type for executive, cost, security (last 7 days)
    print_separator("-")
    print("4. REPORT GENERATION STATUS BY TYPE (LAST 7 DAYS)")
    print_separator("-")

    cutoff_time_week = timezone.now() - timedelta(days=7)
    report_types = ['executive', 'cost', 'security']

    for report_type in report_types:
        print(f"\n{report_type.upper()} Reports:")

        reports = Report.objects.filter(
            report_type=report_type,
            created_at__gte=cutoff_time_week
        ).order_by('-created_at')

        print(f"  Total: {reports.count()}")
        print(f"  Completed: {reports.filter(status='completed').count()}")
        print(f"  With HTML: {reports.filter(html_file__isnull=False).exclude(html_file='').count()}")
        print(f"  With PDF: {reports.filter(pdf_file__isnull=False).exclude(pdf_file='').count()}")
        print(f"  Processing: {reports.filter(status='processing').count()}")
        print(f"  Generating: {reports.filter(status='generating').count()}")
        print(f"  Failed: {reports.filter(status='failed').count()}")

        # Show details of reports without files
        incomplete = reports.filter(
            status='completed'
        ).exclude(
            html_file__isnull=False,
            pdf_file__isnull=False
        ).exclude(html_file='').exclude(pdf_file='')

        if incomplete.count() > 0:
            print(f"\n  Completed but missing files:")
            for report in incomplete[:5]:  # Show up to 5
                print(f"    - {report.id} | {report.client.company_name} | "
                      f"HTML: {'Yes' if report.html_file else 'NO'} | "
                      f"PDF: {'Yes' if report.pdf_file else 'NO'}")

    # 5. Recent failed reports
    print_separator("-")
    print("5. RECENT FAILED REPORTS (LAST 24 HOURS)")
    print_separator("-")

    failed_reports = Report.objects.filter(
        status='failed',
        updated_at__gte=cutoff_time
    ).order_by('-updated_at')

    print(f"\nFound {failed_reports.count()} failed reports:\n")

    for report in failed_reports[:10]:  # Show up to 10
        print(f"ID: {report.id}")
        print(f"  Client: {report.client.company_name}")
        print(f"  Report Type: {report.get_report_type_display()}")
        print(f"  Failed At: {report.updated_at}")
        print(f"  Error: {report.error_message}")
        print(f"  Retry Count: {report.retry_count}")
        print()

    print_separator()
    print("DIAGNOSIS COMPLETE")
    print_separator()

if __name__ == '__main__':
    try:
        diagnose_stuck_reports()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
