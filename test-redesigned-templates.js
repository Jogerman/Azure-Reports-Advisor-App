const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  console.log('========================================');
  console.log('TESTING REDESIGNED REPORT TEMPLATES');
  console.log('========================================\n');

  // Create screenshots directory
  if (!fs.existsSync('screenshots')) {
    fs.mkdirSync('screenshots');
  }

  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // Capture console messages
  const consoleMessages = [];
  page.on('console', msg => {
    consoleMessages.push({ type: msg.type(), text: msg.text() });
    if (msg.type() === 'error' || msg.type() === 'warning') {
      console.log(`[${msg.type().toUpperCase()}] ${msg.text()}`);
    }
  });

  try {
    console.log('Step 1: Navigating to Reports page...');
    await page.goto('http://localhost:3000/reports', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    console.log('✓ Page loaded');

    // Wait a bit for any dynamic content
    await page.waitForTimeout(3000);

    // Take initial screenshot
    await page.screenshot({
      path: 'screenshots/redesign-01-reports-page.png',
      fullPage: true
    });
    console.log('✓ Screenshot: redesign-01-reports-page.png');

    // Check authentication state
    const isAuthenticated = await page.evaluate(() => {
      return localStorage.getItem('auth_token') !== null;
    });

    console.log(`Authentication: ${isAuthenticated ? 'Authenticated' : 'Not authenticated'}`);

    if (!isAuthenticated) {
      console.log('\n⚠️  Not authenticated. Please login manually.');
      console.log('Waiting 20 seconds for manual login...\n');
      await page.waitForTimeout(20000);

      // Refresh to reports page after login
      await page.goto('http://localhost:3000/reports', { waitUntil: 'networkidle' });
      await page.waitForTimeout(3000);
    }

    // Look for HTML buttons
    console.log('\nStep 2: Looking for report HTML buttons...');
    const htmlButtons = await page.locator('button:has-text("HTML"), a:has-text("View HTML")').count();
    console.log(`Found ${htmlButtons} HTML view buttons`);

    if (htmlButtons > 0) {
      console.log('\nStep 3: Clicking first HTML button to view redesigned report...');

      // Click the first HTML button
      const firstHtmlButton = page.locator('button:has-text("HTML"), a:has-text("View HTML")').first();
      await firstHtmlButton.click();

      // Wait for the report to load
      await page.waitForTimeout(5000);

      // Check if we're on a new page or in a modal
      const currentUrl = page.url();
      console.log(`Current URL: ${currentUrl}`);

      // Take screenshot of the HTML report
      await page.screenshot({
        path: 'screenshots/redesign-02-html-report-desktop.png',
        fullPage: true
      });
      console.log('✓ Screenshot: redesign-02-html-report-desktop.png');

      // Check for design elements
      console.log('\nStep 4: Verifying redesign elements...');

      const designChecks = await page.evaluate(() => {
        const checks = {
          hasAzureBlue: false,
          hasGradients: false,
          hasMetricCards: false,
          hasChartJs: false,
          hasCoverPage: false,
          hasSectionHeaders: false
        };

        // Check for Azure blue color
        const allElements = document.querySelectorAll('*');
        for (const el of allElements) {
          const styles = window.getComputedStyle(el);
          const bg = styles.backgroundColor;
          const color = styles.color;
          const bgImage = styles.backgroundImage;

          // Check for Azure blue (#0078D4)
          if (bg.includes('0, 120, 212') || color.includes('0, 120, 212')) {
            checks.hasAzureBlue = true;
          }

          // Check for gradients
          if (bgImage && bgImage.includes('gradient')) {
            checks.hasGradients = true;
          }
        }

        // Check for metric cards
        checks.hasMetricCards = document.querySelector('.metric-card, [class*="metric"]') !== null;

        // Check for Chart.js
        checks.hasChartJs = typeof window.Chart !== 'undefined';

        // Check for cover page
        checks.hasCoverPage = document.querySelector('.cover-page, [class*="cover"]') !== null;

        // Check for section headers
        checks.hasSectionHeaders = document.querySelector('.section-header, [class*="section"]') !== null;

        return checks;
      });

      console.log('Design Elements Check:');
      console.log('  Azure Blue Color:', designChecks.hasAzureBlue ? '✓' : '✗');
      console.log('  Gradients:', designChecks.hasGradients ? '✓' : '✗');
      console.log('  Metric Cards:', designChecks.hasMetricCards ? '✓' : '✗');
      console.log('  Chart.js Loaded:', designChecks.hasChartJs ? '✓' : '✗');
      console.log('  Cover Page:', designChecks.hasCoverPage ? '✓' : '✗');
      console.log('  Section Headers:', designChecks.hasSectionHeaders ? '✓' : '✗');

      // Test responsive design - Mobile view
      console.log('\nStep 5: Testing responsive design (mobile view)...');
      await page.setViewportSize({ width: 375, height: 812 });
      await page.waitForTimeout(2000);

      await page.screenshot({
        path: 'screenshots/redesign-03-html-report-mobile.png',
        fullPage: true
      });
      console.log('✓ Screenshot: redesign-03-html-report-mobile.png');

      // Test responsive design - Tablet view
      console.log('Testing responsive design (tablet view)...');
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.waitForTimeout(2000);

      await page.screenshot({
        path: 'screenshots/redesign-04-html-report-tablet.png',
        fullPage: true
      });
      console.log('✓ Screenshot: redesign-04-html-report-tablet.png');

      // Return to desktop
      await page.setViewportSize({ width: 1920, height: 1080 });

      // Check for charts on the page
      console.log('\nStep 6: Checking for Chart.js visualizations...');
      const chartCount = await page.locator('canvas').count();
      console.log(`Found ${chartCount} canvas elements (charts)`);

      if (chartCount > 0) {
        console.log('✓ Charts are present in the redesigned template');

        // Try to get chart titles
        const chartTitles = await page.evaluate(() => {
          const titles = [];
          document.querySelectorAll('.chart-title, [class*="chart"] h3, [class*="chart"] h4').forEach(el => {
            titles.push(el.textContent.trim());
          });
          return titles;
        });

        if (chartTitles.length > 0) {
          console.log('Chart titles found:');
          chartTitles.forEach(title => console.log(`  - ${title}`));
        }
      }

    } else {
      console.log('\n⚠️  No HTML buttons found. Reports may not be available.');

      // Check page content
      const pageText = await page.locator('body').innerText();
      if (pageText.includes('No reports') || pageText.includes('no reports')) {
        console.log('✗ Page shows "No reports" message');
      }
    }

    // Go back to reports list
    console.log('\nStep 7: Returning to reports list...');
    await page.goto('http://localhost:3000/reports', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Try to test PDF button (just check if it exists, don't download)
    console.log('\nStep 8: Checking for PDF buttons...');
    const pdfButtons = await page.locator('button:has-text("PDF"), a:has-text("Download PDF")').count();
    console.log(`Found ${pdfButtons} PDF download buttons`);

    if (pdfButtons > 0) {
      console.log('✓ PDF functionality is available');
    }

    // Final screenshot
    await page.screenshot({
      path: 'screenshots/redesign-05-final-state.png',
      fullPage: true
    });
    console.log('✓ Screenshot: redesign-05-final-state.png');

  } catch (error) {
    console.error('\n❌ Error during testing:', error.message);
    await page.screenshot({
      path: 'screenshots/redesign-error.png',
      fullPage: true
    });
    console.log('✓ Error screenshot saved');
  }

  console.log('\n========================================');
  console.log('TESTING SUMMARY');
  console.log('========================================');
  console.log('All screenshots saved to screenshots/ folder');
  console.log('Console errors:', consoleMessages.filter(m => m.type === 'error').length);
  console.log('Console warnings:', consoleMessages.filter(m => m.type === 'warning').length);

  // Save console log
  fs.writeFileSync(
    'screenshots/redesign-console-log.json',
    JSON.stringify({ messages: consoleMessages }, null, 2)
  );
  console.log('✓ Console log saved: screenshots/redesign-console-log.json');

  console.log('\n✓ Testing complete! Review the screenshots to verify the redesign.');
  console.log('Press Ctrl+C to close the browser.\n');

  // Keep browser open for manual inspection
  await new Promise(() => {});

})();
