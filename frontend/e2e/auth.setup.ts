import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

/**
 * Setup authentication for E2E tests
 * This will run once before all tests and save the authentication state
 */
setup('authenticate', async ({ page }) => {
  // Navigate to the login page
  await page.goto('/login');

  // Wait for the page to load
  await expect(page).toHaveTitle(/Azure Advisor Reports/i);

  // For Azure AD authentication, we'll need to handle the OAuth flow
  // This is a mock setup - adjust based on your actual authentication flow

  // In a real scenario with Azure AD, you might:
  // 1. Fill in credentials
  // 2. Handle MFA if required
  // 3. Wait for redirect back to the app

  // For testing purposes, you might want to:
  // - Use a test user account
  // - Mock the authentication response
  // - Or use Playwright's built-in authentication storage

  // Example for form-based auth (adjust for your Azure AD implementation):
  // await page.fill('[name="email"]', process.env.TEST_USER_EMAIL || 'test@example.com');
  // await page.fill('[name="password"]', process.env.TEST_USER_PASSWORD || 'testpass');
  // await page.click('button[type="submit"]');

  // Wait for successful authentication
  // await page.waitForURL('/dashboard');

  // Verify we're logged in
  // await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();

  // Save the authentication state to a file
  // await page.context().storageState({ path: authFile });

  console.log('Authentication setup completed');
});
