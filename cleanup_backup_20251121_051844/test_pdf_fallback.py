"""
Test script to verify PDF generation with Playwright primary and WeasyPrint fallback.

This script simulates different scenarios:
1. Successful Playwright generation
2. Playwright failure triggering WeasyPrint fallback
3. Both engines failing
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent / 'azure_advisor_reports'
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
django.setup()

from django.conf import settings
from apps.reports.models import Report
from apps.clients.models import Client
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_normal_pdf_generation():
    """Test normal PDF generation (should use Playwright)."""
    logger.info("=" * 80)
    logger.info("TEST 1: Normal PDF Generation (Playwright should be used)")
    logger.info("=" * 80)

    try:
        # Get the most recent report
        report = Report.objects.filter(status='completed').order_by('-created_at').first()

        if not report:
            logger.error("No completed reports found. Please generate a report first.")
            return False

        logger.info(f"Using report: {report.id} ({report.report_type})")

        # Force regenerate PDF
        from apps.reports.generators import get_generator
        generator = get_generator(report)

        logger.info("Starting PDF generation...")
        pdf_path = generator.generate_pdf()

        logger.info(f"✓ PDF generated successfully: {pdf_path}")
        logger.info(f"✓ Check logs above to confirm Playwright was used")
        return True

    except Exception as e:
        logger.error(f"✗ PDF generation failed: {str(e)}")
        return False


def test_playwright_failure_fallback():
    """Test fallback to WeasyPrint when Playwright fails."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Playwright Failure Fallback (WeasyPrint should be used)")
    logger.info("=" * 80)

    try:
        # Get a report
        report = Report.objects.filter(status='completed').order_by('-created_at').first()

        if not report:
            logger.error("No completed reports found.")
            return False

        logger.info(f"Using report: {report.id} ({report.report_type})")

        # Temporarily break Playwright by monkeypatching
        from apps.reports.generators import base
        original_playwright_method = base.BaseReportGenerator.generate_pdf_with_playwright

        def mock_playwright_failure(self):
            logger.info("Simulating Playwright failure...")
            raise Exception("Simulated Playwright failure for testing")

        # Replace method temporarily
        base.BaseReportGenerator.generate_pdf_with_playwright = mock_playwright_failure

        try:
            from apps.reports.generators import get_generator
            generator = get_generator(report)

            logger.info("Starting PDF generation (Playwright will fail)...")
            pdf_path = generator.generate_pdf()

            logger.info(f"✓ PDF generated successfully using fallback: {pdf_path}")
            logger.info(f"✓ Check logs above to confirm WeasyPrint fallback was triggered")
            return True

        finally:
            # Restore original method
            base.BaseReportGenerator.generate_pdf_with_playwright = original_playwright_method

    except Exception as e:
        logger.error(f"✗ Fallback test failed: {str(e)}")
        return False


def test_both_engines_failure():
    """Test behavior when both engines fail."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Both Engines Failure (should raise exception)")
    logger.info("=" * 80)

    try:
        # Get a report
        report = Report.objects.filter(status='completed').order_by('-created_at').first()

        if not report:
            logger.error("No completed reports found.")
            return False

        logger.info(f"Using report: {report.id} ({report.report_type})")

        # Temporarily break both engines
        from apps.reports.generators import base
        original_playwright = base.BaseReportGenerator.generate_pdf_with_playwright
        original_weasyprint = base.BaseReportGenerator.generate_pdf_with_weasyprint

        def mock_playwright_failure(self):
            logger.info("Simulating Playwright failure...")
            raise Exception("Simulated Playwright failure")

        def mock_weasyprint_failure(self):
            logger.info("Simulating WeasyPrint failure...")
            raise Exception("Simulated WeasyPrint failure")

        # Replace both methods
        base.BaseReportGenerator.generate_pdf_with_playwright = mock_playwright_failure
        base.BaseReportGenerator.generate_pdf_with_weasyprint = mock_weasyprint_failure

        try:
            from apps.reports.generators import get_generator
            generator = get_generator(report)

            logger.info("Starting PDF generation (both engines will fail)...")
            pdf_path = generator.generate_pdf()

            logger.error(f"✗ Test failed: Expected exception but PDF was generated")
            return False

        except Exception as e:
            if "both engines failed" in str(e).lower():
                logger.info(f"✓ Test passed: Both engines failed as expected")
                logger.info(f"✓ Error message: {str(e)}")
                return True
            else:
                logger.error(f"✗ Test failed: Unexpected error: {str(e)}")
                return False

        finally:
            # Restore original methods
            base.BaseReportGenerator.generate_pdf_with_playwright = original_playwright
            base.BaseReportGenerator.generate_pdf_with_weasyprint = original_weasyprint

    except Exception as e:
        logger.error(f"✗ Both engines failure test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    logger.info("Starting PDF Fallback Tests")
    logger.info(f"Django Settings Module: {settings.SETTINGS_MODULE}")

    results = {
        'Normal Generation (Playwright)': test_normal_pdf_generation(),
        'Playwright Failure Fallback': test_playwright_failure_fallback(),
        'Both Engines Failure': test_both_engines_failure(),
    }

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{status}: {test_name}")

    total = len(results)
    passed = sum(results.values())
    logger.info(f"\nTotal: {passed}/{total} tests passed")

    return all(results.values())


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
