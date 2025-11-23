const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function testReportsPage() {
  console.log('Starting Playwright test for Reports functionality...');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // Create screenshots directory
  const screenshotsDir = path.join(__dirname, 'screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir);
  }

  try {
    // Navigate to the application
    console.log('1. Navigating to http://localhost:3000...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    await page.screenshot({ path: path.join(screenshotsDir, '01-homepage.png'), fullPage: true });
    console.log('Screenshot saved: 01-homepage.png');

    // Check if we're on the login page or already authenticated
    const currentUrl = page.url();
    console.log('Current URL:', currentUrl);

    if (currentUrl.includes('login') || await page.locator('input[type="email"], input[type="text"][name*="user"]').count() > 0) {
      console.log('2. Login page detected...');
      await page.screenshot({ path: path.join(screenshotsDir, '02-login-page.png'), fullPage: true });
      console.log('Screenshot saved: 02-login-page.png');

      // Try to find and click Azure AD login button or regular login
      const azureLoginButton = page.locator('button:has-text("Sign in with Microsoft"), button:has-text("Login with Azure AD")');
      const regularLoginButton = page.locator('button[type="submit"]:has-text("Login"), button[type="submit"]:has-text("Sign In")');

      if (await azureLoginButton.count() > 0) {
        console.log('Found Azure AD login button');
      } else if (await regularLoginButton.count() > 0) {
        console.log('Found regular login button');
        // For testing purposes, we'll note that login is required
        console.log('NOTE: Manual login required - cannot proceed with automated testing');
      }
    } else {
      console.log('2. Already authenticated or on dashboard');
    }

    // Wait a moment for any redirects
    await page.waitForTimeout(2000);

    // Try to navigate to reports page
    console.log('3. Looking for Reports navigation...');

    // Look for navigation links
    const reportsLink = page.locator('a:has-text("Reports"), nav a[href*="reports"]');

    if (await reportsLink.count() > 0) {
      console.log('Found Reports navigation link');
      await reportsLink.first().click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: path.join(screenshotsDir, '03-reports-page.png'), fullPage: true });
      console.log('Screenshot saved: 03-reports-page.png');
    } else {
      console.log('Trying to navigate directly to /reports...');
      await page.goto('http://localhost:3000/reports', { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);
      await page.screenshot({ path: path.join(screenshotsDir, '03-reports-page-direct.png'), fullPage: true });
      console.log('Screenshot saved: 03-reports-page-direct.png');
    }

    // Look for report items and action buttons
    console.log('4. Looking for report items...');

    // Check for loading states
    const loadingSpinner = page.locator('[class*="spinner"], [class*="loading"]');
    if (await loadingSpinner.count() > 0) {
      console.log('Loading spinner detected, waiting...');
      await page.waitForTimeout(3000);
    }

    // Look for report cards or table rows
    const reportItems = page.locator('[class*="report"], tr:has(td), [data-testid*="report"]');
    const reportCount = await reportItems.count();
    console.log(`Found ${reportCount} potential report items`);

    // Look for View HTML and Download PDF buttons
    const viewHtmlButtons = page.locator('button:has-text("View HTML"), button:has-text("View Report"), a:has-text("View HTML")');
    const downloadPdfButtons = page.locator('button:has-text("Download PDF"), button:has-text("PDF"), a:has-text("Download PDF")');

    console.log(`Found ${await viewHtmlButtons.count()} View HTML buttons`);
    console.log(`Found ${await downloadPdfButtons.count()} Download PDF buttons`);

    await page.screenshot({ path: path.join(screenshotsDir, '04-reports-overview.png'), fullPage: true });
    console.log('Screenshot saved: 04-reports-overview.png');

    // Test View HTML button if available
    if (await viewHtmlButtons.count() > 0) {
      console.log('5. Testing View HTML button...');

      // Listen for console messages and errors
      page.on('console', msg => console.log('Browser console:', msg.type(), msg.text()));
      page.on('pageerror', err => console.log('Browser error:', err.message));

      // Listen for network requests
      page.on('response', response => {
        if (response.url().includes('html') || response.url().includes('report')) {
          console.log(`Network response: ${response.status()} ${response.url()}`);
        }
      });

      await viewHtmlButtons.first().click();
      await page.waitForTimeout(3000);

      await page.screenshot({ path: path.join(screenshotsDir, '05-after-view-html-click.png'), fullPage: true });
      console.log('Screenshot saved: 05-after-view-html-click.png');

      // Check if a new tab opened or modal appeared
      const pages = context.pages();
      console.log(`Total pages open: ${pages.length}`);

      if (pages.length > 1) {
        console.log('New tab detected, checking content...');
        const newPage = pages[pages.length - 1];
        await newPage.waitForTimeout(2000);
        await newPage.screenshot({ path: path.join(screenshotsDir, '05b-html-view-new-tab.png'), fullPage: true });
        console.log('Screenshot saved: 05b-html-view-new-tab.png');
        console.log('New tab URL:', newPage.url());
      }

      // Check for modals or overlays
      const modal = page.locator('[role="dialog"], [class*="modal"]');
      if (await modal.count() > 0) {
        console.log('Modal detected');
        await page.screenshot({ path: path.join(screenshotsDir, '05c-html-view-modal.png'), fullPage: true });
        console.log('Screenshot saved: 05c-html-view-modal.png');
      }
    } else {
      console.log('5. No View HTML buttons found');
    }

    // Navigate back to reports page if needed
    if (page.url().includes('reports')) {
      console.log('Still on reports page');
    } else {
      console.log('Navigating back to reports page...');
      await page.goto('http://localhost:3000/reports', { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);
    }

    // Test Download PDF button if available
    if (await downloadPdfButtons.count() > 0) {
      console.log('6. Testing Download PDF button...');

      // Set up download listener
      const downloadPromise = page.waitForEvent('download', { timeout: 10000 }).catch(() => null);

      await downloadPdfButtons.first().click();
      await page.waitForTimeout(2000);

      const download = await downloadPromise;
      if (download) {
        console.log('Download started:', download.suggestedFilename());
        await page.screenshot({ path: path.join(screenshotsDir, '06-pdf-download-success.png'), fullPage: true });
        console.log('Screenshot saved: 06-pdf-download-success.png');
      } else {
        console.log('No download detected');
        await page.screenshot({ path: path.join(screenshotsDir, '06-pdf-download-failed.png'), fullPage: true });
        console.log('Screenshot saved: 06-pdf-download-failed.png');
      }
    } else {
      console.log('6. No Download PDF buttons found');
    }

    // Get page content for debugging
    const pageText = await page.textContent('body');
    console.log('\nPage contains reports-related text:', pageText.toLowerCase().includes('report'));

    // Check for error messages
    const errorMessages = page.locator('[class*="error"], [role="alert"]');
    if (await errorMessages.count() > 0) {
      console.log('\nError messages found on page:');
      const errors = await errorMessages.allTextContents();
      errors.forEach(err => console.log('  -', err));
    }

    console.log('\nTest completed successfully!');

  } catch (error) {
    console.error('Error during test:', error);
    await page.screenshot({ path: path.join(screenshotsDir, 'error-state.png'), fullPage: true });
    console.log('Error screenshot saved: error-state.png');
  } finally {
    await page.waitForTimeout(2000);
    await browser.close();
    console.log('\nBrowser closed. Check the screenshots directory for results.');
  }
}

testReportsPage().catch(console.error);
