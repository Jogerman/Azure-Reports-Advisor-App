/**
 * Script para generar PDF optimizado con los templates actualizados
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function generateOptimizedPDF() {
    console.log('='.repeat(80));
    console.log('Generando PDF Optimizado - Templates Actualizados');
    console.log('='.repeat(80));

    const browser = await chromium.launch({
        headless: true,
        args: ['--disable-web-security']
    });

    try {
        const context = await browser.newContext();
        const page = await context.newPage();

        // Cargar el HTML del template
        const htmlPath = path.join(__dirname, 'azure_advisor_reports', 'templates', 'reports', 'executive_enhanced.html');

        // Crear HTML completo con datos de ejemplo
        const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Executive Summary - Azure Advisor Report - Contoso Ltd.</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        ${fs.readFileSync(path.join(__dirname, 'azure_advisor_reports', 'templates', 'reports', 'base_styles.css'), 'utf-8')}
    </style>
</head>
<body>
    <!-- Cover Page -->
    <div class="cover-page">
        <div class="cover-header">
            <div class="cover-logo">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                </svg>
            </div>
            <div class="cover-company">Contoso Ltd.</div>
        </div>

        <div class="cover-main">
            <h1 class="cover-title">Azure Advisor<br>Analysis Report</h1>
            <p class="cover-subtitle">Executive Summary</p>

            <div class="cover-icon-container">
                <div class="cover-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white">
                        <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 1.99 2H18c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
                    </svg>
                </div>
            </div>
        </div>

        <div class="cover-footer">
            <div class="cover-footer-grid">
                <div class="cover-footer-item">
                    <div class="cover-footer-label">Report Date</div>
                    <div class="cover-footer-value">October 26, 2025</div>
                </div>
                <div class="cover-footer-item">
                    <div class="cover-footer-label">Total Findings</div>
                    <div class="cover-footer-value">42</div>
                </div>
                <div class="cover-footer-item">
                    <div class="cover-footer-label">Potential Savings</div>
                    <div class="cover-footer-value">$145,000</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Report Content -->
    <div class="report-container">
        <!-- Report Header -->
        <div class="report-header">
            <div class="report-logo-section">
                <div class="report-logo-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                    </svg>
                </div>
                <div class="report-logo-text">Azure Advisor Reports</div>
            </div>

            <h1>Executive Summary Report</h1>

            <div class="report-meta">
                <div class="meta-item">
                    <span class="meta-label">Client:</span>
                    <span>Contoso Ltd.</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Generated:</span>
                    <span>October 26, 2025</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Report Type:</span>
                    <span>Executive Summary</span>
                </div>
            </div>
        </div>

        <!-- Content continues... -->
        <p style="text-align: center; padding: 50px; color: #666; font-size: 1.2em;">
            ✅ PDF Optimizado Generado con Éxito<br><br>
            Este PDF utiliza los templates ultra-compactos optimizados que eliminan espacios vacíos innecesarios.
        </p>

        <!-- Report Footer -->
        <div class="report-footer">
            <div class="footer-disclaimer">
                <strong>Disclaimer:</strong> This report was automatically generated from Azure Advisor recommendations.
                All data is sourced from Microsoft Azure Advisor as of October 26, 2025.
            </div>

            <div class="footer-credits">
                <div class="footer-logo">
                    <span class="font-semibold text-primary">Azure Advisor Reports Platform</span>
                </div>
                <p>&copy; 2025 Azure Advisor Reports Platform</p>
            </div>
        </div>
    </div>
</body>
</html>
        `;

        // Navegar al HTML
        await page.setContent(htmlContent, { waitUntil: 'networkidle' });

        // Esperar un momento para que se renderice
        await page.waitForTimeout(2000);

        // Generar PDF con configuración optimizada
        const outputPath = path.join(__dirname, 'playwright_final_optimized.pdf');
        await page.pdf({
            path: outputPath,
            format: 'A4',
            printBackground: true,
            margin: {
                top: '1.2cm',
                right: '1cm',
                bottom: '1.2cm',
                left: '1cm'
            },
            preferCSSPageSize: false,
            displayHeaderFooter: false
        });

        // Verificar tamaño del archivo
        const stats = fs.statSync(outputPath);
        const fileSizeKB = stats.size / 1024;

        console.log('\n✅ PDF generado exitosamente!');
        console.log(`📄 Archivo: ${outputPath}`);
        console.log(`📏 Tamaño: ${fileSizeKB.toFixed(2)} KB`);
        console.log('='.repeat(80));

    } catch (error) {
        console.error('❌ Error al generar PDF:', error);
        throw error;
    } finally {
        await browser.close();
    }
}

// Ejecutar
generateOptimizedPDF().catch(console.error);
