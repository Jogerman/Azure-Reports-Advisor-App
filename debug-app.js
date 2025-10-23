const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 100 // Slow down actions slightly for visibility
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  const consoleMessages = [];
  const errors = [];
  const failedRequests = [];
  const networkRequests = [];

  // Capture console messages
  page.on('console', msg => {
    const timestamp = new Date().toISOString();
    const text = `[${timestamp}] [${msg.type().toUpperCase()}] ${msg.text()}`;
    consoleMessages.push(text);
    console.log(text);
  });

  // Capture page errors
  page.on('pageerror', error => {
    const timestamp = new Date().toISOString();
    const errorText = `[${timestamp}] [PAGE ERROR] ${error.message}\n${error.stack}`;
    errors.push(errorText);
    console.log(errorText);
  });

  // Capture failed requests
  page.on('requestfailed', request => {
    const timestamp = new Date().toISOString();
    const failText = `[${timestamp}] [FAILED REQUEST] ${request.method()} ${request.url()} - ${request.failure()?.errorText || 'Unknown'}`;
    failedRequests.push(failText);
    console.log(failText);
  });

  // Capture all network requests
  page.on('response', async response => {
    const timestamp = new Date().toISOString();
    const request = response.request();
    const status = response.status();
    const url = response.url();

    const networkLog = {
      timestamp,
      method: request.method(),
      url,
      status,
      statusText: response.statusText(),
      headers: await response.allHeaders().catch(() => ({}))
    };

    networkRequests.push(networkLog);

    // Log non-2xx responses
    if (status >= 400) {
      const errorText = `[${timestamp}] [HTTP ${status}] ${request.method()} ${url}`;
      console.log(errorText);

      // Try to get response body for error responses
      try {
        const body = await response.text();
        console.log(`  Response body: ${body.substring(0, 500)}`);
      } catch (e) {
        // Ignore if we can't read the body
      }
    }
  });

  console.log('\n========================================');
  console.log('AZURE ADVISOR REPORTS - DEBUG SESSION');
  console.log('========================================\n');

  // Navigate to app
  console.log('Step 1: Navigating to http://localhost:3000...');
  try {
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle', timeout: 30000 });
    console.log('Navigation successful');
  } catch (e) {
    console.log(`Navigation error: ${e.message}`);
  }

  // Wait a moment for initial render
  await page.waitForTimeout(2000);

  // Take initial screenshot
  await page.screenshot({ path: 'screenshots/01-initial-state.png', fullPage: true });
  console.log('✓ Screenshot: 01-initial-state.png');

  // Check if we're on login page
  const isLoginPage = await page.locator('text=Sign in with Microsoft').isVisible().catch(() => false);

  if (isLoginPage) {
    console.log('\n========================================');
    console.log('LOGIN PAGE DETECTED');
    console.log('========================================');
    console.log('');
    console.log('⏳ WAITING 15 SECONDS FOR USER TO LOGIN');
    console.log('');
    console.log('👉 Please click "Sign in with Microsoft"');
    console.log('👉 Complete the Azure AD login flow');
    console.log('👉 The script will continue automatically');
    console.log('');

    await page.screenshot({ path: 'screenshots/02-login-page-ready.png', fullPage: true });
    console.log('✓ Screenshot: 02-login-page-ready.png');

    // Wait 15 seconds for manual login
    for (let i = 15; i > 0; i--) {
      process.stdout.write(`\rTime remaining: ${i} seconds... `);
      await page.waitForTimeout(1000);
    }
    console.log('\n');

    console.log('Login wait period completed.');
  } else {
    console.log('Login page not detected, may already be authenticated');
  }

  // Wait for any post-login navigation
  console.log('\nStep 2: Waiting for post-login state...');
  await page.waitForTimeout(5000);

  // Take screenshot of current state after login
  await page.screenshot({ path: 'screenshots/03-after-login-state.png', fullPage: true });
  console.log('✓ Screenshot: 03-after-login-state.png');

  // Check what page we're on
  const currentURL = page.url();
  console.log(`Current URL: ${currentURL}`);

  // Try to navigate to dashboard
  console.log('\nStep 3: Navigating to dashboard...');
  try {
    await page.goto('http://localhost:3000/', { waitUntil: 'networkidle', timeout: 10000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/04-dashboard-page.png', fullPage: true });
    console.log('✓ Screenshot: 04-dashboard-page.png');
  } catch (e) {
    console.log(`Could not navigate to dashboard: ${e.message}`);
  }

  // Try to navigate to reports page
  console.log('\nStep 4: Navigating to reports page...');
  try {
    await page.goto('http://localhost:3000/reports', { waitUntil: 'networkidle', timeout: 10000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/05-reports-page.png', fullPage: true });
    console.log('✓ Screenshot: 05-reports-page.png');
  } catch (e) {
    console.log(`Could not navigate to reports: ${e.message}`);
  }

  // Try to navigate to clients page
  console.log('\nStep 5: Navigating to clients page...');
  try {
    await page.goto('http://localhost:3000/clients', { waitUntil: 'networkidle', timeout: 10000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/06-clients-page.png', fullPage: true });
    console.log('✓ Screenshot: 06-clients-page.png');
  } catch (e) {
    console.log(`Could not navigate to clients: ${e.message}`);
  }

  // Capture final state and wait for any async errors
  console.log('\nStep 6: Waiting 10 seconds to capture any delayed errors...');
  for (let i = 10; i > 0; i--) {
    process.stdout.write(`\rCapturing errors: ${i} seconds remaining... `);
    await page.waitForTimeout(1000);
  }
  console.log('\n');

  // Final screenshot
  await page.screenshot({ path: 'screenshots/07-final-state.png', fullPage: true });
  console.log('✓ Screenshot: 07-final-state.png');

  // Generate detailed report
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      totalConsoleMessages: consoleMessages.length,
      totalErrors: errors.length,
      totalFailedRequests: failedRequests.length,
      totalNetworkRequests: networkRequests.length
    },
    consoleMessages,
    errors,
    failedRequests,
    networkRequests: networkRequests.filter(req => req.status >= 400)
  };

  // Save detailed JSON report
  fs.writeFileSync('screenshots/debug-report.json', JSON.stringify(report, null, 2));
  console.log('\n✓ Saved detailed report: screenshots/debug-report.json');

  // Print summary to console
  console.log('\n========================================');
  console.log('DEBUG SUMMARY');
  console.log('========================================\n');

  console.log(`Total Console Messages: ${consoleMessages.length}`);
  console.log(`Total Page Errors: ${errors.length}`);
  console.log(`Total Failed Requests: ${failedRequests.length}`);
  console.log(`Total HTTP Errors (4xx/5xx): ${networkRequests.filter(req => req.status >= 400).length}`);

  if (consoleMessages.length > 0) {
    console.log('\n--- CONSOLE MESSAGES ---');
    consoleMessages.forEach(msg => console.log(msg));
  }

  if (errors.length > 0) {
    console.log('\n--- PAGE ERRORS ---');
    errors.forEach(err => console.log(err));
  }

  if (failedRequests.length > 0) {
    console.log('\n--- FAILED REQUESTS ---');
    failedRequests.forEach(req => console.log(req));
  }

  const httpErrors = networkRequests.filter(req => req.status >= 400);
  if (httpErrors.length > 0) {
    console.log('\n--- HTTP ERROR RESPONSES ---');
    httpErrors.forEach(req => {
      console.log(`[${req.status}] ${req.method} ${req.url}`);
    });
  }

  console.log('\n========================================');
  console.log('Press Ctrl+C to close the browser');
  console.log('========================================\n');

  // Keep browser open for manual inspection
  await page.waitForTimeout(300000); // 5 minutes

  await browser.close();
})();
