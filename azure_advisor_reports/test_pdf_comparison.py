"""
Test script to compare PDF generation: WeasyPrint vs Playwright
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
django.setup()

from apps.reports.models import Report
from apps.reports.generators.executive import ExecutiveReportGenerator
from apps.reports.generators.cost import CostOptimizationReportGenerator
from django.conf import settings

def test_pdf_generation():
    """Generate PDFs with both engines and compare."""

    # Get the most recent report
    try:
        report = Report.objects.latest('created_at')
        print(f"\n✅ Found report: {report.title}")
        print(f"   Client: {report.client.name}")
        print(f"   Recommendations: {report.recommendations.count()}")
    except Report.DoesNotExist:
        print("❌ No reports found in database. Please create a report first.")
        return

    # Test Executive Report with both engines
    print("\n" + "="*80)
    print("TESTING EXECUTIVE REPORT")
    print("="*80)

    generator = ExecutiveReportGenerator(report)

    # 1. Generate with WeasyPrint
    print("\n📄 Generating with WeasyPrint...")
    original_engine = settings.PDF_ENGINE
    settings.PDF_ENGINE = 'weasyprint'

    try:
        weasyprint_path = generator.generate_pdf()
        weasyprint_size = Path(weasyprint_path).stat().st_size
        print(f"   ✅ WeasyPrint PDF: {weasyprint_path}")
        print(f"   📦 Size: {weasyprint_size / 1024:.2f} KB")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        weasyprint_path = None

    # 2. Generate with Playwright
    print("\n🎭 Generating with Playwright...")
    settings.PDF_ENGINE = 'playwright'

    try:
        playwright_path = generator.generate_pdf()
        playwright_size = Path(playwright_path).stat().st_size
        print(f"   ✅ Playwright PDF: {playwright_path}")
        print(f"   📦 Size: {playwright_size / 1024:.2f} KB")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        playwright_path = None

    # Restore original engine
    settings.PDF_ENGINE = original_engine

    # Test Cost Report with both engines
    print("\n" + "="*80)
    print("TESTING COST OPTIMIZATION REPORT")
    print("="*80)

    generator = CostOptimizationReportGenerator(report)

    # 1. Generate with WeasyPrint
    print("\n📄 Generating with WeasyPrint...")
    settings.PDF_ENGINE = 'weasyprint'

    try:
        weasyprint_cost_path = generator.generate_pdf()
        weasyprint_cost_size = Path(weasyprint_cost_path).stat().st_size
        print(f"   ✅ WeasyPrint PDF: {weasyprint_cost_path}")
        print(f"   📦 Size: {weasyprint_cost_size / 1024:.2f} KB")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        weasyprint_cost_path = None

    # 2. Generate with Playwright
    print("\n🎭 Generating with Playwright...")
    settings.PDF_ENGINE = 'playwright'

    try:
        playwright_cost_path = generator.generate_pdf()
        playwright_cost_size = Path(playwright_cost_path).stat().st_size
        print(f"   ✅ Playwright PDF: {playwright_cost_path}")
        print(f"   📦 Size: {playwright_cost_size / 1024:.2f} KB")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        playwright_cost_path = None

    # Restore original engine
    settings.PDF_ENGINE = original_engine

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    if weasyprint_path and playwright_path:
        size_diff = ((playwright_size - weasyprint_size) / weasyprint_size) * 100
        print(f"\n📊 Executive Report:")
        print(f"   WeasyPrint:  {weasyprint_size / 1024:.2f} KB")
        print(f"   Playwright:  {playwright_size / 1024:.2f} KB")
        print(f"   Difference:  {size_diff:+.1f}%")

    if weasyprint_cost_path and playwright_cost_path:
        cost_size_diff = ((playwright_cost_size - weasyprint_cost_size) / weasyprint_cost_size) * 100
        print(f"\n📊 Cost Report:")
        print(f"   WeasyPrint:  {weasyprint_cost_size / 1024:.2f} KB")
        print(f"   Playwright:  {playwright_cost_size / 1024:.2f} KB")
        print(f"   Difference:  {cost_size_diff:+.1f}%")

    print("\n✅ PDF comparison complete!")
    print("\n💡 Next steps:")
    print("   1. Open both PDFs to compare visual quality")
    print("   2. Check if Chart.js visualizations render in Playwright PDF")
    print("   3. Verify professional styling and layout")

if __name__ == '__main__':
    test_pdf_generation()
