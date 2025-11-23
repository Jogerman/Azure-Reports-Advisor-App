"""
Test PDF generation with inlined Chart.js to verify production fix.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'azure_advisor_reports'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
django.setup()

from django.template.loader import render_to_string
from apps.reports.services.pdf_service import generate_pdf

def test_chart_rendering():
    """Test if charts render correctly in PDF with inlined Chart.js."""

    # Create a simple test HTML with Chart.js
    test_context = {
        'client': {
            'company_name': 'Test Company',
        },
        'category_distribution': [
            {'category_display': 'Cost', 'count': 25},
            {'category_display': 'Security', 'count': 15},
            {'category_display': 'Reliability', 'count': 10},
        ],
        'high_impact_count': 12,
        'medium_impact_count': 18,
        'low_impact_count': 10,
        'category_stats': [
            {'category': 'Cost', 'total_savings': 15000},
            {'category': 'Security', 'total_savings': 8000},
            {'category': 'Reliability', 'total_savings': 5000},
        ],
        'recommendations_by_category': {},
        'total_potential_savings': 28000,
        'total_recommendations': 40,
    }

    # Render the detailed template (which uses base_redesigned.html)
    html_content = render_to_string('reports/detailed.html', test_context)

    # Generate PDF
    output_path = os.path.join(os.path.dirname(__file__), 'test_chart_rendering.pdf')

    print(f"Generating test PDF with inlined Chart.js...")
    print(f"Output path: {output_path}")

    try:
        pdf_path = generate_pdf(
            html_content=html_content,
            output_path=output_path,
            wait_for_charts=True,
            wait_for_fonts=True,
        )

        print(f"✓ PDF generated successfully: {pdf_path}")
        print(f"✓ File size: {os.path.getsize(pdf_path) / 1024:.2f} KB")
        print("\nPlease open the PDF and verify that charts are visible.")

    except Exception as e:
        print(f"✗ Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == '__main__':
    success = test_chart_rendering()
    sys.exit(0 if success else 1)
