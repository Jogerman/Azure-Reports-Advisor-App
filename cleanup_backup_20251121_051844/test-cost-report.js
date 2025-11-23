const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function testCostReport() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  // Navigate to the local HTML file
  const htmlPath = path.join(__dirname, '.playwright-mcp', 'cost-report-autozama.html');
  const url = `file://${htmlPath}`;

  console.log(`Navigating to: ${url}`);

  try {
    // Navigate to the cost report
    const response = await page.goto(url, {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    console.log(`Response status: ${response.status()}`);

    if (response.status() !== 200) {
      console.error(`Error: Received status ${response.status()}`);
      const text = await page.content();
      console.log('Page content:', text.substring(0, 500));
      await browser.close();
      return;
    }

    // Wait for the page to fully load
    console.log('Waiting for page to load...');
    await page.waitForTimeout(3000);

    // Wait for Chart.js to load (if charts exist)
    try {
      await page.waitForSelector('canvas', { timeout: 5000 });
      console.log('Charts detected on page');
      // Wait a bit more for charts to render
      await page.waitForTimeout(2000);
    } catch (e) {
      console.log('No charts found or charts took too long to load');
    }

    // Create output directory
    const outputDir = path.join(__dirname, '.playwright-mcp');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Take full page screenshot
    console.log('Taking full page screenshot...');
    await page.screenshot({
      path: path.join(outputDir, 'cost-report-full-page.png'),
      fullPage: true
    });

    // Try to take screenshots of specific sections
    const sections = [
      { selector: '.metrics-grid', name: 'hero-metrics-grid' },
      { selector: '.metric-card-primary', name: 'primary-metric-card' },
      { selector: '.charts-grid', name: 'charts-grid' },
      { selector: '.chart-container', name: 'chart-container-first' },
      { selector: '#savingsByResourceChart', name: 'savings-by-resource-chart' },
      { selector: '#topCostSaversChart', name: 'top-cost-savers-chart' },
      { selector: '.success-box', name: 'financial-impact-summary' },
      { selector: '.section', name: 'section-first' }
    ];

    for (const section of sections) {
      try {
        const element = await page.$(section.selector);
        if (element) {
          console.log(`Taking screenshot of ${section.name}...`);
          await element.screenshot({
            path: path.join(outputDir, `cost-report-${section.name}.png`)
          });
        } else {
          console.log(`Section ${section.name} (${section.selector}) not found`);
        }
      } catch (e) {
        console.log(`Could not screenshot ${section.name}: ${e.message}`);
      }
    }

    // Generate PDF
    console.log('Generating PDF...');
    const pdfPath = path.join(__dirname, 'context_docs', 'Autozama_cost_report_redesigned.pdf');

    // Create context_docs directory if it doesn't exist
    const contextDocsDir = path.join(__dirname, 'context_docs');
    if (!fs.existsSync(contextDocsDir)) {
      fs.mkdirSync(contextDocsDir, { recursive: true });
    }

    await page.pdf({
      path: pdfPath,
      format: 'A4',
      printBackground: true,
      margin: {
        top: '20px',
        right: '20px',
        bottom: '20px',
        left: '20px'
      }
    });

    console.log(`PDF saved to: ${pdfPath}`);

    // Get page title
    const title = await page.title();
    console.log(`Page title: ${title}`);

    // Check for errors in console
    const logs = [];
    page.on('console', msg => logs.push(`${msg.type()}: ${msg.text()}`));

    // Get some basic page info
    const pageInfo = await page.evaluate(() => {
      return {
        hasChartJs: typeof window.Chart !== 'undefined',
        canvasCount: document.querySelectorAll('canvas').length,
        hasMetricsGrid: !!document.querySelector('.metrics-grid'),
        hasChartsGrid: !!document.querySelector('.charts-grid'),
        hasChartContainers: document.querySelectorAll('.chart-container').length,
        hasSavingsChart: !!document.querySelector('#savingsByResourceChart'),
        hasCostSaversChart: !!document.querySelector('#topCostSaversChart'),
        hasSuccessBox: !!document.querySelector('.success-box'),
        metricCardsCount: document.querySelectorAll('.metric-card').length,
        sectionsCount: document.querySelectorAll('.section').length,
        bodyClasses: document.body.className,
        h1Text: document.querySelector('h1')?.textContent || 'No H1 found',
        pageTitle: document.title
      };
    });

    console.log('\n=== Page Analysis ===');
    console.log(JSON.stringify(pageInfo, null, 2));

    if (logs.length > 0) {
      console.log('\n=== Console Logs ===');
      logs.forEach(log => console.log(log));
    }

  } catch (error) {
    console.error('Error during test:', error.message);

    // Take screenshot on error
    try {
      await page.screenshot({
        path: path.join(__dirname, '.playwright-mcp', 'cost-report-error.png'),
        fullPage: true
      });
    } catch (e) {
      console.error('Could not take error screenshot:', e.message);
    }
  } finally {
    await browser.close();
  }
}

testCostReport().catch(console.error);
