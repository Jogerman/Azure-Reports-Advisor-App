const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  console.log('🔍 Starting comprehensive debugging session...\n');

  const browser = await chromium.launch({
    headless: false,
    args: ['--disable-web-security'] // Help identify CORS issues
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: 'D:\\Code\\Azure Reports\\debug-videos',
      size: { width: 1920, height: 1080 }
    }
  });

  const page = await context.newPage();

  // Storage for captured data
  const debugData = {
    consoleMessages: [],
    pageErrors: [],
    networkRequests: [],
    failedRequests: [],
    responseErrors: [],
    timestamp: new Date().toISOString()
  };

  // Capture all console messages
  page.on('console', msg => {
    const logEntry = {
      type: msg.type(),
      text: msg.text(),
      location: msg.location(),
      timestamp: new Date().toISOString()
    };
    debugData.consoleMessages.push(logEntry);
    console.log(`📋 CONSOLE [${msg.type().toUpperCase()}]: ${msg.text()}`);
  });

  // Capture page errors (uncaught exceptions)
  page.on('pageerror', error => {
    const errorEntry = {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    };
    debugData.pageErrors.push(errorEntry);
    console.log(`❌ PAGE ERROR: ${error.message}`);
    console.log(`   Stack: ${error.stack}`);
  });

  // Capture all requests
  page.on('request', request => {
    const requestEntry = {
      url: request.url(),
      method: request.method(),
      headers: request.headers(),
      postData: request.postData(),
      timestamp: new Date().toISOString()
    };
    debugData.networkRequests.push(requestEntry);

    if (request.url().includes('/api/')) {
      console.log(`🌐 REQUEST: ${request.method()} ${request.url()}`);
    }
  });

  // Capture failed requests
  page.on('requestfailed', request => {
    const failureEntry = {
      url: request.url(),
      method: request.method(),
      errorText: request.failure()?.errorText,
      timestamp: new Date().toISOString()
    };
    debugData.failedRequests.push(failureEntry);
    console.log(`🔴 FAILED REQUEST: ${request.method()} ${request.url()}`);
    console.log(`   Error: ${request.failure()?.errorText}`);
  });

  // Capture responses with errors
  page.on('response', async response => {
    if (!response.ok() && response.url().includes('/api/')) {
      let responseBody = null;
      try {
        responseBody = await response.text();
      } catch (e) {
        responseBody = 'Could not read response body';
      }

      const responseEntry = {
        url: response.url(),
        status: response.status(),
        statusText: response.statusText(),
        headers: response.headers(),
        body: responseBody,
        timestamp: new Date().toISOString()
      };
      debugData.responseErrors.push(responseEntry);
      console.log(`⚠️  RESPONSE ERROR: ${response.status()} ${response.url()}`);
      console.log(`   Status: ${response.status()} ${response.statusText()}`);
      console.log(`   Body: ${responseBody?.substring(0, 200)}...`);
    }
  });

  try {
    console.log('\n📱 Navigating to http://localhost:3000...\n');
    await page.goto('http://localhost:3000', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    // Wait for initial render
    await page.waitForTimeout(2000);

    // Take screenshot of initial state
    console.log('\n📸 Taking screenshot of initial state...');
    await page.screenshot({
      path: 'D:\\Code\\Azure Reports\\debug-1-initial-state.png',
      fullPage: true
    });

    // Check if we're on login page or dashboard
    const currentUrl = page.url();
    console.log(`\n🔗 Current URL: ${currentUrl}`);

    // Try to capture localStorage and sessionStorage
    const storageData = await page.evaluate(() => {
      return {
        localStorage: { ...localStorage },
        sessionStorage: { ...sessionStorage },
        cookies: document.cookie
      };
    });
    debugData.storageData = storageData;
    console.log('\n💾 Storage Data:', JSON.stringify(storageData, null, 2));

    // Wait a bit more to catch any delayed errors
    await page.waitForTimeout(3000);

    // Check for visible error messages on the page
    const errorMessages = await page.evaluate(() => {
      const errors = [];

      // Look for common error indicators
      const errorElements = document.querySelectorAll('[class*="error" i], [class*="alert" i], [role="alert"]');
      errorElements.forEach(el => {
        errors.push({
          text: el.textContent?.trim(),
          className: el.className,
          tagName: el.tagName
        });
      });

      return errors;
    });

    if (errorMessages.length > 0) {
      console.log('\n🚨 Visible Error Messages on Page:');
      errorMessages.forEach(err => {
        console.log(`   - ${err.text}`);
      });
      debugData.visibleErrors = errorMessages;
    }

    // Try to navigate to reports page if not already there
    if (!currentUrl.includes('/reports')) {
      console.log('\n🔄 Attempting to navigate to Reports page...');

      // Look for Reports link in sidebar
      try {
        await page.click('a[href="/reports"]', { timeout: 5000 });
        await page.waitForTimeout(2000);

        console.log('📸 Taking screenshot of Reports page...');
        await page.screenshot({
          path: 'D:\\Code\\Azure Reports\\debug-2-reports-page.png',
          fullPage: true
        });
      } catch (e) {
        console.log('⚠️  Could not navigate to Reports page:', e.message);
      }
    }

    // Try to find and click on any report to trigger the error
    console.log('\n🔍 Looking for reports to interact with...');
    try {
      const reportButtons = await page.$$('button:has-text("View"), button:has-text("Download")');
      console.log(`   Found ${reportButtons.length} report action buttons`);

      if (reportButtons.length > 0) {
        console.log('\n🖱️  Clicking first View/Download button...');
        await reportButtons[0].click();
        await page.waitForTimeout(3000);

        console.log('📸 Taking screenshot after clicking report action...');
        await page.screenshot({
          path: 'D:\\Code\\Azure Reports\\debug-3-after-action.png',
          fullPage: true
        });
      }
    } catch (e) {
      console.log('⚠️  Error interacting with reports:', e.message);
    }

    // Wait a bit more to capture any final errors
    await page.waitForTimeout(2000);

  } catch (error) {
    console.error('\n💥 Error during debugging:', error.message);
    debugData.scriptError = {
      message: error.message,
      stack: error.stack
    };
  }

  // Save all captured data to JSON file
  const reportPath = 'D:\\Code\\Azure Reports\\DEBUG_REPORT.json';
  fs.writeFileSync(reportPath, JSON.stringify(debugData, null, 2));
  console.log(`\n💾 Debug report saved to: ${reportPath}`);

  // Generate summary
  console.log('\n' + '='.repeat(80));
  console.log('📊 DEBUG SUMMARY');
  console.log('='.repeat(80));
  console.log(`Console Messages: ${debugData.consoleMessages.length}`);
  console.log(`Page Errors: ${debugData.pageErrors.length}`);
  console.log(`Total Network Requests: ${debugData.networkRequests.length}`);
  console.log(`Failed Requests: ${debugData.failedRequests.length}`);
  console.log(`Response Errors (4xx/5xx): ${debugData.responseErrors.length}`);

  if (debugData.pageErrors.length > 0) {
    console.log('\n❌ PAGE ERRORS FOUND:');
    debugData.pageErrors.forEach((err, i) => {
      console.log(`\n${i + 1}. ${err.message}`);
      console.log(`   ${err.stack?.split('\n')[1]?.trim()}`);
    });
  }

  if (debugData.responseErrors.length > 0) {
    console.log('\n⚠️  API ERRORS FOUND:');
    debugData.responseErrors.forEach((err, i) => {
      console.log(`\n${i + 1}. ${err.status} ${err.url}`);
      console.log(`   ${err.body?.substring(0, 100)}...`);
    });
  }

  if (debugData.failedRequests.length > 0) {
    console.log('\n🔴 FAILED REQUESTS:');
    debugData.failedRequests.forEach((req, i) => {
      console.log(`\n${i + 1}. ${req.method} ${req.url}`);
      console.log(`   ${req.errorText}`);
    });
  }

  console.log('\n' + '='.repeat(80));
  console.log('✅ Debugging session complete!');
  console.log('='.repeat(80));
  console.log('\nGenerated files:');
  console.log('  - debug-1-initial-state.png');
  console.log('  - debug-2-reports-page.png (if navigated)');
  console.log('  - debug-3-after-action.png (if action triggered)');
  console.log('  - DEBUG_REPORT.json (full details)');
  console.log('\n');

  await browser.close();
})();
