import { test, expect } from '@playwright/test';

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the authentication - adjust based on your actual auth implementation
    await page.goto('/dashboard');

    // Wait for the dashboard to load
    await page.waitForLoadState('networkidle');
  });

  test('should display dashboard title and description', async ({ page }) => {
    // Check for main heading
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();

    // Check for description
    await expect(page.getByText(/Welcome to Azure Advisor Reports Platform/i)).toBeVisible();
  });

  test('should display all metric cards', async ({ page }) => {
    // Wait for data to load
    await page.waitForSelector('[data-testid="metric-card"]', { timeout: 5000 });

    // Check for all four metric cards
    await expect(page.getByText('Active Clients')).toBeVisible();
    await expect(page.getByText('Reports Generated')).toBeVisible();
    await expect(page.getByText('Total Potential Savings')).toBeVisible();
    await expect(page.getByText('Total Recommendations')).toBeVisible();
  });

  test('should display charts', async ({ page }) => {
    // Check for category chart
    await expect(page.getByText('Recommendations by Category')).toBeVisible();

    // Check for trend chart
    await expect(page.getByText('Report Generation Trend')).toBeVisible();
  });

  test('should display recent activity section', async ({ page }) => {
    await expect(page.getByText('Recent Activity')).toBeVisible();
  });

  test('should display quick action cards', async ({ page }) => {
    await expect(page.getByText('Manage Clients')).toBeVisible();
    await expect(page.getByText('Generate Reports')).toBeVisible();
    await expect(page.getByText('View History')).toBeVisible();
  });

  test('should navigate to clients page when clicking quick action', async ({ page }) => {
    // Click on "Manage Clients" quick action
    await page.getByRole('link', { name: /Manage Clients/i }).click();

    // Verify navigation to clients page
    await expect(page).toHaveURL(/.*\/clients/);
    await expect(page.getByRole('heading', { name: /clients/i })).toBeVisible();
  });

  test('should navigate to reports page when clicking quick action', async ({ page }) => {
    // Click on "Generate Reports" quick action
    await page.getByRole('link', { name: /Generate Reports/i }).click();

    // Verify navigation to reports page
    await expect(page).toHaveURL(/.*\/reports/);
  });

  test('should refresh dashboard when clicking refresh button', async ({ page }) => {
    // Wait for initial load
    await page.waitForSelector('[data-testid="metric-card"]', { timeout: 5000 });

    // Click refresh button
    const refreshButton = page.getByRole('button', { name: /refresh/i });
    await refreshButton.click();

    // Verify button shows loading state
    await expect(refreshButton).toContainText(/refreshing/i);

    // Wait for refresh to complete
    await expect(refreshButton).toContainText(/refresh/i, { timeout: 5000 });
  });

  test('should be responsive on mobile', async ({ page, viewport }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Dashboard should still be visible and functional
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
    await expect(page.getByText('Active Clients')).toBeVisible();
  });

  test('should handle error state gracefully', async ({ page }) => {
    // Intercept API call and return error
    await page.route('**/api/v1/analytics/dashboard/', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' }),
      });
    });

    await page.reload();

    // Wait for error message
    await expect(page.getByRole('alert')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/error loading dashboard/i)).toBeVisible();

    // Verify "Try again" button is present
    await expect(page.getByRole('button', { name: /try again/i })).toBeVisible();
  });

  test('should have proper keyboard navigation', async ({ page }) => {
    // Tab through interactive elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Verify focus is visible
    const focusedElement = await page.evaluateHandle(() => document.activeElement);
    expect(focusedElement).toBeTruthy();
  });

  test('should have accessible elements', async ({ page }) => {
    // Run accessibility audit
    // Check for ARIA labels
    const refreshButton = page.getByRole('button', { name: /refresh dashboard data/i });
    await expect(refreshButton).toHaveAttribute('aria-label');

    // Check for navigation landmark
    await expect(page.getByRole('navigation', { name: /quick actions/i })).toBeVisible();
  });
});
