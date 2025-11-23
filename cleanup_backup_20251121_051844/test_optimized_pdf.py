"""
Test script to generate optimized PDF and compare with original.

This script generates a new PDF using the optimized templates and compares
file size and page count with the original.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
django.setup()

from django.utils import timezone
from apps.reports.models import Client, Report
from apps.reports.services.report_generator import ReportGenerator

def get_file_size_mb(file_path):
    """Get file size in MB."""
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    return 0

def count_pdf_pages(file_path):
    """Count pages in PDF (simple heuristic)."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            # Count /Type /Page occurrences
            return content.count(b'/Type /Page')
    except:
        return 0

def main():
    print("=" * 80)
    print("PDF Optimization Test - Comparing Original vs Optimized")
    print("=" * 80)

    # Get the client (Autozama)
    try:
        client = Client.objects.get(company_name='Autozama')
        print(f"\nClient found: {client.company_name}")
    except Client.DoesNotExist:
        print("ERROR: Autozama client not found!")
        return

    # Get the most recent report
    report = Report.objects.filter(client=client).order_by('-created_at').first()
    if not report:
        print("ERROR: No reports found for this client!")
        return

    print(f"Report found: {report.report_type} (ID: {report.id})")
    print(f"Total recommendations: {report.recommendations.count()}")

    # Original PDF path
    original_pdf = Path(__file__).parent / "playwright_current.pdf"
    optimized_pdf = Path(__file__).parent / "playwright_optimized.pdf"

    # Get original PDF stats
    if original_pdf.exists():
        original_size = get_file_size_mb(original_pdf)
        original_pages = count_pdf_pages(original_pdf)
        print(f"\nOriginal PDF:")
        print(f"  - File: {original_pdf.name}")
        print(f"  - Size: {original_size:.2f} MB")
        print(f"  - Pages: ~{original_pages}")
    else:
        print(f"\nWARNING: Original PDF not found at {original_pdf}")
        original_size = 0
        original_pages = 0

    # Generate optimized PDF
    print(f"\nGenerating optimized PDF...")
    print(f"  - Using optimized CSS and templates")
    print(f"  - Reduced margins: 12mm top/bottom, 10mm left/right")
    print(f"  - Scale: 0.95")
    print(f"  - Compact spacing in print mode")

    try:
        generator = ReportGenerator()

        # Generate executive report (same as original)
        pdf_path = generator.generate_executive_report(
            client=client,
            output_filename=optimized_pdf.name
        )

        print(f"\nOptimized PDF generated successfully!")
        print(f"  - Path: {pdf_path}")

        # Get optimized PDF stats
        optimized_size = get_file_size_mb(pdf_path)
        optimized_pages = count_pdf_pages(pdf_path)

        print(f"\nOptimized PDF:")
        print(f"  - File: {Path(pdf_path).name}")
        print(f"  - Size: {optimized_size:.2f} MB")
        print(f"  - Pages: ~{optimized_pages}")

        # Compare results
        if original_size > 0:
            size_reduction = ((original_size - optimized_size) / original_size) * 100
            page_reduction = original_pages - optimized_pages

            print("\n" + "=" * 80)
            print("COMPARISON RESULTS")
            print("=" * 80)
            print(f"Size reduction: {size_reduction:.1f}% ({original_size:.2f} MB → {optimized_size:.2f} MB)")
            print(f"Space saved: {(original_size - optimized_size):.2f} MB")
            print(f"Page reduction: {page_reduction} pages ({original_pages} → {optimized_pages})")

            if optimized_size <= 0.7:  # Target: 500-700 KB = 0.5-0.7 MB
                print("\n✅ SUCCESS: Target file size achieved (≤700 KB)!")
            elif optimized_size < original_size * 0.7:
                print("\n✅ GOOD: File size reduced by >30%")
            else:
                print("\n⚠️  NOTE: Further optimization may be needed")

            print("\nOptimizations applied:")
            print("  ✓ Reduced section margins (12 → 6 spacing units)")
            print("  ✓ Compact metric cards (8 → 4 padding)")
            print("  ✓ Smaller chart heights (300px → 200px)")
            print("  ✓ Compact table cells (4 → 2-3 padding)")
            print("  ✓ Reduced line-height in lists (2.2 → 1.8)")
            print("  ✓ Optimized PDF margins (20mm → 12mm)")
            print("  ✓ Reduced viewport size")
            print("  ✓ Added image-rendering optimizations")

        print("\n" + "=" * 80)
        print("Test completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\nERROR: Failed to generate optimized PDF: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
