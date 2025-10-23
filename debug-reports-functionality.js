const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  console.log('========================================');
  console.log('REPORTS PDF/HTML FUNCTIONALITY DEBUG');
  console.log('========================================\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 500  // Slow down so we can see what's happening
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  const consoleMessages = [];
  const errors = [];
  const networkRequests = [];
  const failedRequests = [];

  // Capture all console messages
  page.on('console', msg => {
    const text = `[${msg.type().toUpperCase()}] ${msg.text()}`;
    consoleMessages.push({ type: msg.type(), text: msg.text(), timestamp: new Date().toISOString() });
    console.log(`[CONSOLE ${msg.type()}] ${msg.text()}`);
  });

  // Capture page errors
  page.on('pageerror', error => {
    const errorText = `${error.message}\n${error.stack}`;
    errors.push({ message: error.message, stack: error.stack, timestamp: new Date().toISOString() });
    console.log(`[PAGE ERROR] ${error.message}`);
  });

  // Capture network requests
  page.on('request', request => {
    if (request.url().includes('/api/')) {
      networkRequests.push({
        url: request.url(),
        method: request.method(),
        timestamp: new Date().toISOString()
      });
      console.log(`[REQUEST] ${request.method()} ${request.url()}`);
    }
  });

  // Capture failed requests
  page.on('requestfailed', request => {
    const failText = `${request.url()} - ${request.failure()?.errorText || 'Unknown'}`;
    failedRequests.push({ url: request.url(), error: request.failure()?.errorText, timestamp: new Date().toISOString() });
    console.log(`[FAILED REQUEST] ${failText}`);
  });

  // Capture responses
  page.on('response', async response => {
    if (response.url().includes('/api/')) {
      const status = response.status();
      console.log(`[RESPONSE] ${status} ${response.url()}`);

      if (status >= 400) {
        try {
          const body = await response.text();
          console.log(`[ERROR RESPONSE BODY] ${body.substring(0, 500)}`);
        } catch (e) {
          console.log(`[ERROR] Could not read response body`);
        }
      }
    }
  });

  try {
    console.log('\nStep 1: Navigating to login page...');
    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle' });
    await page.screenshot({ path: 'screenshots/debug-01-login-page.png', fullPage: true });
    console.log('✓ Screenshot: debug-01-login-page.png');

    console.log('\n=== WAITING 15 SECONDS FOR YOU TO LOGIN ===');
    console.log('Please click "Sign in with Microsoft" and complete the login...\n');

    // Wait 15 seconds for manual login
    await page.waitForTimeout(15000);

    console.log('\nStep 2: Checking authentication state...');
    await page.screenshot({ path: 'screenshots/debug-02-after-login.png', fullPage: true });
    console.log('✓ Screenshot: debug-02-after-login.png');

    // Wait a bit more for any redirects
    await page.waitForTimeout(3000);

    console.log('\nStep 3: Navigating to Reports page...');
    await page.goto('http://localhost:3000/reports', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(5000); // Wait for data to load

    await page.screenshot({ path: 'screenshots/debug-03-reports-page.png', fullPage: true });
    console.log('✓ Screenshot: debug-03-reports-page.png');

    console.log('\nStep 4: Looking for report cards and buttons...');

    // Check for reports
    const reportCards = await page.locator('[class*="report"]').count().catch(() => 0);
    console.log(`Found ${reportCards} elements with 'report' in class name`);

    // Look for PDF button
    const pdfButtons = await page.locator('button:has-text("PDF")').count().catch(() => 0);
    console.log(`Found ${pdfButtons} PDF buttons`);

    // Look for HTML button
    const htmlButtons = await page.locator('button:has-text("HTML")').count().catch(() => 0);
    console.log(`Found ${htmlButtons} HTML buttons`);

    // Look for any buttons
    const allButtons = await page.locator('button').count().catch(() => 0);
    console.log(`Total buttons on page: ${allButtons}`);

    // Get all button texts
    console.log('\nAll button texts on page:');
    const buttons = await page.locator('button').all();
    for (let i = 0; i < Math.min(buttons.length, 20); i++) {
      try {
        const text = await buttons[i].innerText();
        if (text) console.log(`  - "${text}"`);
      } catch (e) {
        // Skip if can't get text
      }
    }

    // Check for "No reports" or empty state messages
    const pageText = await page.locator('body').innerText();
    if (pageText.includes('No reports') || pageText.includes('no reports') || pageText.includes('empty')) {
      console.log('\n⚠️ Found empty state message on page');
    }

    // Try to find the "View All Reports" button and click it
    console.log('\nStep 5: Looking for "View All Reports" button...');
    const viewAllButton = page.locator('button:has-text("View All Reports")');
    const viewAllExists = await viewAllButton.count() > 0;

    if (viewAllExists) {
      console.log('✓ Found "View All Reports" button, clicking it...');
      await viewAllButton.click();
      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'screenshots/debug-04-after-view-all.png', fullPage: true });
      console.log('✓ Screenshot: debug-04-after-view-all.png');

      // Check again for buttons
      const pdfButtons2 = await page.locator('button:has-text("PDF")').count().catch(() => 0);
      const htmlButtons2 = await page.locator('button:has-text("HTML")').count().catch(() => 0);
      console.log(`After clicking View All - PDF buttons: ${pdfButtons2}, HTML buttons: ${htmlButtons2}`);
    } else {
      console.log('✗ "View All Reports" button not found');
    }

    // Check if we can find the report by client name
    console.log('\nStep 6: Looking for Autozama report...');
    const autozamaText = await page.locator('text=Autozama').count().catch(() => 0);
    console.log(`Found ${autozamaText} instances of "Autozama" on page`);

    if (autozamaText > 0) {
      console.log('✓ Found Autozama client on page');
      await page.screenshot({ path: 'screenshots/debug-05-autozama-found.png', fullPage: true });
      console.log('✓ Screenshot: debug-05-autozama-found.png');
    }

    // Try to directly access the report detail if we have the ID
    console.log('\nStep 7: Attempting direct API call to get reports...');
    const reportsResponse = await page.evaluate(async () => {
      try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch('http://localhost:8000/api/v1/reports/', {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        const data = await response.json();
        return { status: response.status, data: data };
      } catch (error) {
        return { error: error.message };
      }
    });

    console.log('API Response:', JSON.stringify(reportsResponse, null, 2));

    // Final screenshot
    await page.screenshot({ path: 'screenshots/debug-06-final-state.png', fullPage: true });
    console.log('✓ Screenshot: debug-06-final-state.png');

    console.log('\nStep 8: Waiting 5 more seconds for any async updates...');
    await page.waitForTimeout(5000);

  } catch (error) {
    console.error('\n❌ Error during debug:', error.message);
    await page.screenshot({ path: 'screenshots/debug-error.png', fullPage: true });
  }

  // Generate report
  console.log('\n========================================');
  console.log('DEBUG SUMMARY');
  console.log('========================================\n');

  console.log(`Console Messages: ${consoleMessages.length}`);
  console.log(`Page Errors: ${errors.length}`);
  console.log(`Network Requests: ${networkRequests.length}`);
  console.log(`Failed Requests: ${failedRequests.length}`);

  if (errors.length > 0) {
    console.log('\n=== PAGE ERRORS ===');
    errors.forEach(err => {
      console.log(`[${err.timestamp}] ${err.message}`);
    });
  }

  if (failedRequests.length > 0) {
    console.log('\n=== FAILED REQUESTS ===');
    failedRequests.forEach(req => {
      console.log(`[${req.timestamp}] ${req.url} - ${req.error}`);
    });
  }

  // Save detailed report
  const report = {
    timestamp: new Date().toISOString(),
    consoleMessages,
    errors,
    networkRequests,
    failedRequests
  };

  fs.writeFileSync(
    'screenshots/debug-detailed-report.json',
    JSON.stringify(report, null, 2)
  );
  console.log('\n✓ Detailed report saved: screenshots/debug-detailed-report.json');

  console.log('\n=== Debug session complete ===');
  console.log('Please review the screenshots in the screenshots/ folder\n');

  await browser.close();
})();
