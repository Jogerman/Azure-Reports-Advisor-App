"""
Script to fix stuck reports in production by triggering report generation.

This script will:
1. Find all completed reports without HTML/PDF files
2. Trigger report generation for each one
3. Monitor the generation status
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
from apps.reports.tasks import generate_report
from django.utils import timezone

def print_separator(char="=", length=80):
    print(char * length)

def fix_stuck_reports():
    print_separator()
    print("FIXING STUCK REPORTS - TRIGGERING REPORT GENERATION")
    print_separator()
    print(f"Current time: {timezone.now()}")
    print()

    # Find completed reports without HTML/PDF files (last 7 days)
    cutoff_time = timezone.now() - timedelta(days=7)
    stuck_reports = Report.objects.filter(
        status='completed',
        processing_completed_at__gte=cutoff_time
    ).filter(
        html_file=''
    ).order_by('-processing_completed_at')

    print(f"Found {stuck_reports.count()} completed reports without files:\n")

    if stuck_reports.count() == 0:
        print("✅ No stuck reports found. All reports have files generated.")
        return

    generated_count = 0
    failed_count = 0

    for report in stuck_reports:
        print(f"Processing Report: {report.id}")
        print(f"  Client: {report.client.company_name}")
        print(f"  Report Type: {report.get_report_type_display()}")
        print(f"  Recommendations: {report.recommendations.count()}")
        print(f"  Completed: {report.processing_completed_at}")

        # Check if report has recommendations
        if report.recommendations.count() == 0:
            print(f"  ⚠️  SKIPPED: No recommendations to generate report from")
            failed_count += 1
            print()
            continue

        # Trigger report generation
        try:
            task = generate_report.delay(str(report.id), format_type='both')
            print(f"  ✅ Report generation task dispatched: {task.id}")
            generated_count += 1
        except Exception as e:
            print(f"  ❌ Failed to trigger generation: {str(e)}")
            failed_count += 1

        print()

    print_separator()
    print("SUMMARY")
    print_separator()
    print(f"Total stuck reports found: {stuck_reports.count()}")
    print(f"Generation tasks dispatched: {generated_count}")
    print(f"Failed/Skipped: {failed_count}")
    print()
    print("✅ Report generation tasks have been dispatched.")
    print("   Monitor worker logs to see the generation progress:")
    print("   az containerapp logs show --name advisor-reports-worker \\")
    print("     --resource-group rg-azure-advisor-app --follow --tail 100")
    print_separator()

if __name__ == '__main__':
    try:
        fix_stuck_reports()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
