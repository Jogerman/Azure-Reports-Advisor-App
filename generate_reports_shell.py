"""
Generate sample reports using Django shell context
"""
from apps.reports.models import Report
from apps.reports.generators.executive import ExecutiveReportGenerator
from apps.reports.generators.cost import CostOptimizationReportGenerator
from apps.reports.generators.security import SecurityReportGenerator
import os

print("=" * 70)
print("GENERANDO REPORTES DE EJEMPLO CON TEMPLATES MEJORADOS")
print("=" * 70)
print()

# Obtener reportes completados
completed_reports = Report.objects.filter(status='completed').order_by('-created_at')

if not completed_reports.exists():
    print("⚠️  No hay reportes completados en la base de datos.")
    print("   Por favor genera al menos un reporte primero.")
else:
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
        print(f"📅 Cliente: {report.client.company_name if report.client else 'N/A'}")
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
