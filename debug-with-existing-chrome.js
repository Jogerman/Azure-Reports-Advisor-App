const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  console.log('========================================');
  console.log('DEBUGGING WITH YOUR EXISTING CHROME SESSION');
  console.log('========================================\n');

  // Connect to existing Chrome instance
  // First, you need to start Chrome with remote debugging:
  // chrome.exe --remote-debugging-port=9222

  let browser;
  try {
    console.log('Attempting to connect to existing Chrome on port 9222...');
    browser = await chromium.connectOverCDP('http://localhost:9222');
    console.log('✓ Connected to existing Chrome!\n');
  } catch (error) {
    console.log('Could not connect to existing Chrome.');
    console.log('Please start Chrome with: chrome.exe --remote-debugging-port=9222');
    console.log('\nOr I can launch a new Chrome with your profile data...\n');

    // Use the default Chrome profile location
    const userDataDir = process.env.LOCALAPPDATA + '\\Google\\Chrome\\User Data';
    console.log(`Using Chrome profile: ${userDataDir}`);

    browser = await chromium.launchPersistentContext(userDataDir, {
      headless: false,
      channel: 'chrome',
      args: ['--start-maximized']
    });
    console.log('✓ Launched Chrome with your profile!\n');
  }

  const pages = browser.contexts()[0].pages();
  let page;

  // Find or create a page with localhost:3000
  const existingPage = pages.find(p => p.url().includes('localhost:3000'));
  if (existingPage) {
    console.log('✓ Found existing tab with localhost:3000');
    page = existingPage;
  } else {
    console.log('Creating new tab for localhost:3000');
    page = await browser.contexts()[0].newPage();
  }

  const consoleMessages = [];
  const errors = [];
  const failedRequests = [];

  // Capture console messages
  page.on('console', msg => {
    const text = `[${msg.type().toUpperCase()}] ${msg.text()}`;
    consoleMessages.push({ type: msg.type(), text: msg.text() });
    if (msg.type() === 'error' || msg.type() === 'warning') {
      console.log(text);
    }
  });

  // Capture errors
  page.on('pageerror', error => {
    errors.push({ message: error.message, stack: error.stack });
    console.log(`[PAGE ERROR] ${error.message}`);
  });

  // Capture failed requests
  page.on('requestfailed', request => {
    failedRequests.push({ url: request.url(), error: request.failure()?.errorText });
    console.log(`[FAILED REQUEST] ${request.url()}`);
  });

  try {
    console.log('\nStep 1: Navigating to Reports page...');
    await page.goto('http://localhost:3000/reports', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(3000);

    await page.screenshot({ path: 'screenshots/chrome-01-reports-page.png', fullPage: true });
    console.log('✓ Screenshot: chrome-01-reports-page.png');

    console.log('\nStep 2: Analyzing page content...');

    // Get authentication state
    const authState = await page.evaluate(() => {
      const accounts = JSON.parse(localStorage.getItem('msal.accounts') || '{}');
      const hasAccounts = Object.keys(accounts).length > 0;
      return {
        hasAccounts,
        accountCount: Object.keys(accounts).length,
        hasToken: !!localStorage.getItem('auth_token')
      };
    });
    console.log('Auth State:', authState);

    // Count reports and buttons
    const reportElements = await page.locator('[class*="report-card"], [class*="ReportCard"]').count();
    console.log(`Report cards found: ${reportElements}`);

    const pdfButtons = await page.locator('button:has-text("PDF"), button:has-text("pdf")').count();
    const htmlButtons = await page.locator('button:has-text("HTML"), button:has-text("html")').count();
    console.log(`PDF buttons: ${pdfButtons}`);
    console.log(`HTML buttons: ${htmlButtons}`);

    // Get all visible text
    const pageText = await page.locator('body').innerText();

    // Check for empty states
    if (pageText.toLowerCase().includes('no reports')) {
      console.log('⚠️  Found "No reports" message');
    }

    // Check for Autozama
    if (pageText.includes('Autozama')) {
      console.log('✓ Found Autozama on page');
    } else {
      console.log('✗ Autozama not found on page');
    }

    // Look for "View All Reports" button
    const viewAllButton = page.locator('button:has-text("View All Reports")');
    if (await viewAllButton.count() > 0) {
      console.log('\n✓ Found "View All Reports" button');
      console.log('Step 3: Clicking "View All Reports"...');
      await viewAllButton.click();
      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'screenshots/chrome-02-after-view-all.png', fullPage: true });
      console.log('✓ Screenshot: chrome-02-after-view-all.png');

      // Count again
      const pdfButtons2 = await page.locator('button:has-text("PDF")').count();
      const htmlButtons2 = await page.locator('button:has-text("HTML")').count();
      console.log(`After View All - PDF buttons: ${pdfButtons2}, HTML buttons: ${htmlButtons2}`);
    }

    // Get all buttons text
    console.log('\nStep 4: Getting all button texts...');
    const buttons = await page.locator('button').all();
    const buttonTexts = [];
    for (const button of buttons.slice(0, 30)) {
      try {
        const text = await button.innerText();
        if (text && text.trim()) {
          buttonTexts.push(text.trim());
        }
      } catch (e) {}
    }
    console.log('Buttons found:', buttonTexts);

    // Try direct API call
    console.log('\nStep 5: Testing API directly...');
    const apiResponse = await page.evaluate(async () => {
      try {
        // Get token from context
        const getToken = async () => {
          const accounts = JSON.parse(localStorage.getItem('msal.accounts') || '{}');
          return localStorage.getItem('auth_token') || null;
        };

        const token = await getToken();
        console.log('Token exists:', !!token);

        const response = await fetch('http://localhost:8000/api/v1/reports/', {
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Content-Type': 'application/json'
          }
        });

        const data = await response.json();
        return {
          status: response.status,
          ok: response.ok,
          hasResults: !!data.results,
          count: data.results ? data.results.length : 0,
          data: data
        };
      } catch (error) {
        return { error: error.message };
      }
    });

    console.log('API Response:', JSON.stringify(apiResponse, null, 2));

    // If we have reports, look for the specific one
    if (apiResponse.count > 0) {
      console.log(`\n✓ Found ${apiResponse.count} reports in API`);
      const reports = apiResponse.data.results;

      reports.forEach((report, index) => {
        console.log(`\nReport ${index + 1}:`);
        console.log(`  ID: ${report.id}`);
        console.log(`  Client: ${report.client_name || report.client}`);
        console.log(`  Type: ${report.report_type}`);
        console.log(`  Status: ${report.status}`);
        console.log(`  HTML File: ${report.html_file || 'N/A'}`);
        console.log(`  PDF File: ${report.pdf_file || 'N/A'}`);
      });

      // Check if buttons are visible for completed reports with files
      const completedWithFiles = reports.filter(r =>
        r.status === 'completed' && (r.html_file || r.pdf_file)
      );
      console.log(`\nReports with files ready: ${completedWithFiles.length}`);

      if (completedWithFiles.length > 0 && (pdfButtons === 0 && htmlButtons === 0)) {
        console.log('\n⚠️  ISSUE: Reports have files but buttons are not visible!');
        console.log('This suggests a frontend rendering issue.');
      }
    } else {
      console.log('\n⚠️  No reports found in API response');
    }

    // Final screenshot
    await page.screenshot({ path: 'screenshots/chrome-03-final.png', fullPage: true });
    console.log('\n✓ Screenshot: chrome-03-final.png');

    // Check React DevTools
    console.log('\nStep 6: Checking React component state...');
    const reactState = await page.evaluate(() => {
      // Try to access React Fiber
      const rootElement = document.querySelector('#root');
      if (rootElement && rootElement._reactRootContainer) {
        return { hasReact: true };
      }
      return { hasReact: false };
    });
    console.log('React state:', reactState);

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    await page.screenshot({ path: 'screenshots/chrome-error.png', fullPage: true });
  }

  // Summary
  console.log('\n========================================');
  console.log('SUMMARY');
  console.log('========================================');
  console.log(`Console Errors: ${consoleMessages.filter(m => m.type === 'error').length}`);
  console.log(`Page Errors: ${errors.length}`);
  console.log(`Failed Requests: ${failedRequests.length}`);

  if (errors.length > 0) {
    console.log('\n=== ERRORS ===');
    errors.forEach(err => console.log(err.message));
  }

  // Save report
  const report = {
    timestamp: new Date().toISOString(),
    consoleMessages,
    errors,
    failedRequests
  };

  fs.writeFileSync('screenshots/chrome-debug-report.json', JSON.stringify(report, null, 2));
  console.log('\n✓ Report saved: screenshots/chrome-debug-report.json');

  console.log('\n=== Debug complete ===');
  console.log('Screenshots are in screenshots/ folder');
  console.log('Press Ctrl+C to close\n');

  // Keep browser open
  await new Promise(() => {});

})();
