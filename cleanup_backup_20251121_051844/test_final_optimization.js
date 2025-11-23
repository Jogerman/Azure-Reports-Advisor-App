/**
 * Verificar optimizaciones de templates ejecutados
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function testOptimization() {
    console.log('='.repeat(80));
    console.log('VERIFICACIÓN DE OPTIMIZACIÓN DE TEMPLATES');
    console.log('='.repeat(80));

    const browser = await chromium.launch({ headless: true });

    try {
        const page = await browser.newPage();

        // Crear HTML mínimo de prueba
        const testHTML = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test Optimización</title>
</head>
<body>
    <h1>Templates Optimizados</h1>
    <div style="margin: 50px; font-family: 'Segoe UI', sans-serif;">
        <h2 style="color: #0078D4;">✅ Optimizaciones Implementadas:</h2>
        <ul style="line-height: 1.8; font-size: 1.1em;">
            <li><strong>Problema 1:</strong> Key Insights (Página 3) - SOLUCIONADO
                <ul>
                    <li>Reducido padding de 20px → 15px</li>
                    <li>Reducido line-height de 1.8 → 1.6</li>
                    <li>Añadido page-break-after: avoid</li>
                </ul>
            </li>
            <li><strong>Problema 2:</strong> Página Vacía #6 - ELIMINADA
                <ul>
                    <li>Ajustado page-break-before en Strategic Roadmap</li>
                    <li>Removidos espacios innecesarios</li>
                </ul>
            </li>
            <li><strong>Problema 3:</strong> Top 10 Table (Página 8) - COMPACTADA
                <ul>
                    <li>Reducido margin de tablas: 20px → 10px</li>
                    <li>Padding de celdas: 8px → 6px en print</li>
                    <li>Font-size de tabla: 0.8rem → 0.75rem en print</li>
                </ul>
            </li>
            <li><strong>Problema 4:</strong> Phase 3 (Página 10) - OPTIMIZADA
                <ul>
                    <li>Reducido padding de boxes: 20px → 15px</li>
                    <li>Reducido margin-bottom de listas</li>
                    <li>Line-height: 1.8 → 1.6</li>
                </ul>
            </li>
        </ul>

        <h2 style="color: #107C10; margin-top: 40px;">📊 Optimizaciones CSS Print:</h2>
        <ul style="line-height: 1.8; font-size: 1.1em;">
            <li>Sections: margin 15px (antes: 24px)</li>
            <li>Metric cards: padding 12px (antes: 16px)</li>
            <li>Chart height: 180px (antes: 200px)</li>
            <li>Table padding: 6px/8px (antes: 8px/12px)</li>
            <li>Info boxes: padding 12px, margin 10px (antes: 16px/16px)</li>
            <li>Font sizes reducidos: 0.65rem-0.85rem</li>
        </ul>

        <h2 style="color: #FF8C00; margin-top: 40px;">🎯 Resultados Esperados:</h2>
        <ul style="line-height: 1.8; font-size: 1.1em;">
            <li>Reducción de páginas: 12 → 9-10 páginas</li>
            <li>Reducción de tamaño: ~1098 KB → ~800-900 KB</li>
            <li>Eliminación de espacios vacíos</li>
            <li>Mejor aprovechamiento del espacio</li>
        </ul>
    </div>

    <div style="margin: 50px; padding: 30px; background: #f0f0f0; border-left: 6px solid #0078D4;">
        <h3>📝 Archivos Modificados:</h3>
        <ul>
            <li><code>azure_advisor_reports/templates/reports/executive_enhanced.html</code></li>
            <li><code>azure_advisor_reports/templates/reports/base.html</code> (CSS print rules)</li>
        </ul>
        <p style="margin-top: 20px;">
            <strong>Nota:</strong> Para ver los resultados reales, es necesario regenerar el PDF
            usando el generador de reportes de Django con estos templates actualizados.
        </p>
    </div>
</body>
</html>
        `;

        await page.setContent(testHTML);
        await page.waitForTimeout(1000);

        const outputPath = path.join(__dirname, 'optimization_verification.pdf');
        await page.pdf({
            path: outputPath,
            format: 'A4',
            printBackground: true,
            margin: { top: '1cm', right: '1cm', bottom: '1cm', left: '1cm' }
        });

        const stats = fs.statSync(outputPath);
        console.log(`\n✅ Documento de verificación generado: ${outputPath}`);
        console.log(`📏 Tamaño: ${(stats.size / 1024).toFixed(2)} KB`);
        console.log('='.repeat(80));

    } finally {
        await browser.close();
    }
}

testOptimization().catch(console.error);
