"""
Script para generar reportes de ejemplo con los nuevos templates mejorados
Azure Advisor Reports Platform
"""

import os
import sys
import django

# Setup Django
# The script is already in /app, and manage.py is in /app/azure_advisor_reports
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/azure_advisor_reports')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
django.setup()

from apps.reports.models import Report
from apps.reports.generators.executive import ExecutiveReportGenerator
from apps.reports.generators.cost import CostOptimizationReportGenerator
from apps.reports.generators.security import SecurityReportGenerator

def generate_sample_reports():
    """Generar reportes de ejemplo con los templates mejorados"""

    print("=" * 70)
    print("GENERANDO REPORTES DE EJEMPLO CON TEMPLATES MEJORADOS")
    print("=" * 70)
    print()

    # Obtener reportes completados
    completed_reports = Report.objects.filter(status='completed').order_by('-created_at')

    if not completed_reports.exists():
        print("⚠️  No hay reportes completados en la base de datos.")
        print("   Por favor genera al menos un reporte primero.")
        return

    print(f"📊 Encontrados {completed_reports.count()} reportes completados")
    print()

    # Directorio para guardar los reportes
    output_dir = '/app/sample_reports'
    os.makedirs(output_dir, exist_ok=True)

    # Generar reportes de diferentes tipos
    generated_count = 0

    for report_type in ['executive', 'cost', 'security']:
        # Buscar un reporte de este tipo
        report = completed_reports.filter(report_type=report_type).first()

        if not report:
            print(f"⏭️  No hay reportes de tipo '{report_type}', saltando...")
            continue

        print(f"\n{'='*70}")
        print(f"Generando {report_type.upper()} REPORT")
        print(f"{'='*70}")
        print(f"📄 Report ID: {report.id}")
        print(f"📅 Cliente: {report.client_name}")
        print(f"📆 Creado: {report.created_at.strftime('%Y-%m-%d %H:%M')}")
        print()

        try:
            # Seleccionar el generador apropiado
            if report_type == 'executive':
                generator = ExecutiveReportGenerator(report)
            elif report_type == 'cost':
                generator = CostOptimizationReportGenerator(report)
            elif report_type == 'security':
                generator = SecurityReportGenerator(report)

            # Generar HTML
            print("  🔨 Generando HTML...")
            html_path = generator.generate_html()
            print(f"  ✅ HTML generado: {html_path}")

            # Copiar al directorio de salida
            output_html = f"{output_dir}/{report_type}_report_enhanced.html"
            os.system(f"cp {html_path} {output_html}")
            print(f"  📁 Copiado a: {output_html}")

            # Generar PDF
            print("  🔨 Generando PDF...")
            pdf_path = generator.generate_pdf()
            print(f"  ✅ PDF generado: {pdf_path}")

            # Copiar al directorio de salida
            output_pdf = f"{output_dir}/{report_type}_report_enhanced.pdf"
            os.system(f"cp {pdf_path} {output_pdf}")
            print(f"  📁 Copiado a: {output_pdf}")

            generated_count += 1

        except Exception as e:
            print(f"  ❌ Error generando reporte: {str(e)}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 70)
    print(f"✅ PROCESO COMPLETADO")
    print("=" * 70)
    print(f"📊 Reportes generados: {generated_count}")
    print(f"📁 Ubicación: {output_dir}")
    print()
    print("Los reportes han sido generados con los NUEVOS TEMPLATES MEJORADOS:")
    print("  - Visualizaciones con Chart.js")
    print("  - Diseño profesional Azure-branded")
    print("  - Datos 100% reales de Azure Advisor")
    print("  - KPIs, roadmaps y análisis detallados")
    print()
    print("Para copiarlos al host (Windows):")
    print(f"  docker cp azure-advisor-backend:{output_dir} \"D:\\Code\\Azure Reports\\sample_reports\"")
    print()

if __name__ == '__main__':
    generate_sample_reports()
