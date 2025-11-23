#!/usr/bin/env python
"""
Test script to verify PDF render timing improvements.
This script generates a test PDF and monitors the timing of each step.
"""

import os
import sys
import django
import logging
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'azure_advisor_reports'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
django.setup()

from apps.reports.models import Report
from apps.reports.services.pdf_service import SyncPlaywrightPDFGenerator

# Configure logging to see all the timing details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_pdf_generation():
    """Test PDF generation with a real report and monitor timing."""

    # Find the most recent report
    report = Report.objects.filter(
        status='completed',
        html_file__isnull=False
    ).order_by('-created_at').first()

    if not report:
        logger.error("❌ No completed reports found with HTML files")
        return False

    logger.info(f"📄 Testing PDF generation for Report ID: {report.id}")
    logger.info(f"   Report Type: {report.report_type}")
    logger.info(f"   Client: {report.client.name}")
    logger.info(f"   Recommendations: {report.recommendations.count()}")

    # Read the HTML content
    try:
        with report.html_file.open('r') as f:
            html_content = f.read()
        logger.info(f"✅ HTML content loaded ({len(html_content)} bytes)")
    except Exception as e:
        logger.error(f"❌ Failed to read HTML file: {e}")
        return False

    # Generate temporary PDF path
    temp_pdf_path = os.path.join(
        os.path.dirname(__file__),
        f'test_render_timing_{report.id}.pdf'
    )

    logger.info(f"🚀 Starting PDF generation...")
    logger.info(f"   Output path: {temp_pdf_path}")
    start_time = datetime.now()

    try:
        # Initialize generator
        generator = SyncPlaywrightPDFGenerator(
            headless=True,
            timeout=60000  # 60 seconds
        )

        # Generate PDF with all wait options enabled
        # Note: wait_for_images and wait_for_elements_visible are called automatically
        pdf_path = generator.generate_pdf_from_html(
            html_content=html_content,
            output_path=temp_pdf_path,
            wait_for_charts=True,
            wait_for_fonts=True,
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"✅ PDF generated successfully!")
        logger.info(f"   Path: {pdf_path}")
        logger.info(f"   Duration: {duration:.2f} seconds")

        # Check file size
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
            logger.info(f"   File size: {file_size:.2f} MB")

            logger.info("")
            logger.info("📊 RESULTS:")
            logger.info(f"   ✅ PDF generation completed in {duration:.2f}s")
            logger.info(f"   ✅ File size: {file_size:.2f} MB")
            logger.info("")
            logger.info("🔍 NEXT STEPS:")
            logger.info(f"   1. Open the PDF: {pdf_path}")
            logger.info("   2. Check for any blank spaces in the PDF")
            logger.info("   3. Verify all charts are rendered correctly")
            logger.info("   4. Verify all images are loaded")
            logger.info("   5. Check that all tables and text are visible")
            logger.info("")
            logger.info("⏱️  EXPECTED TIMING:")
            logger.info("   - Network idle: ~10s")
            logger.info("   - DOM load: ~2s")
            logger.info("   - Fonts loading: ~1s")
            logger.info("   - Lazy content: ~2s")
            logger.info("   - Chart rendering: ~5-15s")
            logger.info("   - Image loading: ~2-5s")
            logger.info("   - Elements visibility: ~1-5s")
            logger.info("   - Final wait: ~4s")
            logger.info("   - Total expected: ~27-42s")
            logger.info("")

            if duration < 20:
                logger.warning("⚠️  PDF generated faster than expected!")
                logger.warning("    This might indicate that some wait steps were skipped.")
                logger.warning("    Please verify the PDF carefully for blank spaces.")
            elif duration > 50:
                logger.warning("⚠️  PDF generation took longer than expected!")
                logger.warning("    This might indicate timeout issues or slow rendering.")
                logger.warning("    Check the logs above for any timeout warnings.")
            else:
                logger.info("✅ Generation time is within expected range!")

            return True
        else:
            logger.error("❌ PDF file was not created")
            return False

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"❌ PDF generation failed after {duration:.2f}s")
        logger.error(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("PDF RENDER TIMING TEST")
    logger.info("=" * 80)
    logger.info("")

    success = test_pdf_generation()

    logger.info("")
    logger.info("=" * 80)
    if success:
        logger.info("✅ TEST PASSED")
    else:
        logger.info("❌ TEST FAILED")
    logger.info("=" * 80)

    sys.exit(0 if success else 1)
