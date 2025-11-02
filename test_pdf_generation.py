"""
Test PDF generation with new PDF-optimized templates
"""
from apps.reports.models import Report
from apps.reports.generators.executive import ExecutiveReportGenerator
from apps.reports.generators.cost import CostOptimizationReportGenerator
from apps.reports.generators.security import SecurityReportGenerator

print("=" * 70)
print("TESTING PDF GENERATION WITH OPTIMIZED TEMPLATES")
print("=" * 70)
print()

# Get a completed report of each type
completed_reports = Report.objects.filter(status='completed').order_by('-created_at')

if not completed_reports.exists():
    print("⚠️  No hay reportes completados en la base de datos.")
else:
    print(f"📊 Encontrados {completed_reports.count()} reportes completados")
    print()

    for report_type in ['executive', 'cost', 'security']:
        report = completed_reports.filter(report_type=report_type).first()

        if not report:
            print(f"⏭️  No hay reportes de tipo '{report_type}', saltando...")
            continue

        print(f"\n{'='*70}")
        print(f"Testing {report_type.upper()} PDF Generation")
        print(f"{'='*70}")
        print(f"📄 Report ID: {report.id}")
        print(f"📅 Cliente: {report.client.company_name if report.client else 'N/A'}")
        print()

        try:
            # Select appropriate generator
            if report_type == 'executive':
                generator = ExecutiveReportGenerator(report)
            elif report_type == 'cost':
                generator = CostOptimizationReportGenerator(report)
            elif report_type == 'security':
                generator = SecurityReportGenerator(report)

            # Generate PDF with new template
            print("  🔨 Generating PDF with optimized template...")
            pdf_path = generator.generate_pdf()
            print(f"  ✅ PDF generated successfully: {pdf_path}")

            # Check file size
            import os
            from django.conf import settings
            full_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
            if os.path.exists(full_path):
                size_kb = os.path.getsize(full_path) / 1024
                print(f"  📏 File size: {size_kb:.2f} KB")

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

print()
print("=" * 70)
print("✅ TESTING COMPLETED")
print("=" * 70)
