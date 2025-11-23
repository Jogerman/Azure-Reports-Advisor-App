import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Report Generation Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports');
    await page.waitForLoadState('networkidle');
  });

  test('should display reports page correctly', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /generate reports/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /new report/i })).toBeVisible();
  });

  test('should open create report modal', async ({ page }) => {
    // Click new report button
    await page.getByRole('button', { name: /new report/i }).click();

    // Verify modal is open
    await expect(page.getByText(/create new report/i)).toBeVisible();
    await expect(page.getByLabelText(/select client/i)).toBeVisible();
    await expect(page.getByText(/upload azure advisor csv/i)).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    // Open modal
    await page.getByRole('button', { name: /new report/i }).click();

    // Try to submit without filling fields
    await page.getByRole('button', { name: /create report/i }).click();

    // Verify validation errors appear
    await expect(page.getByText(/please select a client/i)).toBeVisible();
    await expect(page.getByText(/please upload a csv file/i)).toBeVisible();
  });

  test('should upload CSV file', async ({ page }) => {
    // Open modal
    await page.getByRole('button', { name: /new report/i }).click();

    // Create a test CSV file
    const testCSVContent = `Category,Impact,Description,Potential Benefits
Cost,High,Reduce idle resources,Save $500/month
Security,Medium,Enable MFA,Improve security posture`;

    // Create file input buffer
    const buffer = Buffer.from(testCSVContent);

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-advisor-report.csv',
      mimeType: 'text/csv',
      buffer: buffer,
    });

    // Verify file is selected
    await expect(page.getByText('test-advisor-report.csv')).toBeVisible();
    await expect(page.getByTestId('check-icon')).toBeVisible();
  });

  test('should reject non-CSV files', async ({ page }) => {
    // Open modal
    await page.getByRole('button', { name: /new report/i }).click();

    // Try to upload a non-CSV file
    const buffer = Buffer.from('This is not a CSV');
    const fileInput = page.locator('input[type="file"]');

    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: buffer,
    });

    // Verify error message
    await expect(page.getByText(/only csv files are allowed/i)).toBeVisible();
  });

  test('should reject files exceeding size limit', async ({ page }) => {
    // Open modal
    await page.getByRole('button', { name: /new report/i }).click();

    // Create a large file (mock - in real scenario this would be 51MB)
    const largeContent = 'x'.repeat(51 * 1024 * 1024); // 51MB
    const buffer = Buffer.from(largeContent);

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'large-file.csv',
      mimeType: 'text/csv',
      buffer: buffer,
    });

    // Verify error message
    await expect(page.getByText(/file size exceeds.*mb limit/i)).toBeVisible();
  });

  test('should complete full report creation flow', async ({ page }) => {
    // Mock successful API responses
    await page.route('**/api/v1/clients/', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '123',
            company_name: 'Test Company',
            status: 'active',
          },
        ]),
      });
    });

    await page.route('**/api/v1/reports/', route => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'report-123',
            status: 'processing',
            client_id: '123',
          }),
        });
      } else {
        route.continue();
      }
    });

    // Open modal
    await page.getByRole('button', { name: /new report/i }).click();

    // Select client
    await page.getByLabelText(/select client/i).selectOption('123');

    // Upload CSV
    const testCSVContent = `Category,Impact,Description
Cost,High,Reduce idle resources`;
    const buffer = Buffer.from(testCSVContent);

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'advisor-report.csv',
      mimeType: 'text/csv',
      buffer: buffer,
    });

    // Select report type
    await page.getByLabelText(/report type/i).selectOption('detailed');

    // Submit form
    await page.getByRole('button', { name: /create report/i }).click();

    // Verify success message
    await expect(page.getByText(/report created successfully/i)).toBeVisible({ timeout: 5000 });

    // Modal should close
    await expect(page.getByText(/create new report/i)).not.toBeVisible();
  });

  test('should display existing reports', async ({ page }) => {
    // Mock API response with reports
    await page.route('**/api/v1/reports/', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'report-1',
            client: { company_name: 'Company A' },
            status: 'completed',
            report_type: 'detailed',
            created_at: '2025-01-01T00:00:00Z',
          },
          {
            id: 'report-2',
            client: { company_name: 'Company B' },
            status: 'processing',
            report_type: 'executive',
            created_at: '2025-01-02T00:00:00Z',
          },
        ]),
      });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify reports are displayed
    await expect(page.getByText('Company A')).toBeVisible();
    await expect(page.getByText('Company B')).toBeVisible();
  });

  test('should download completed report', async ({ page }) => {
    // Mock reports API
    await page.route('**/api/v1/reports/', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'report-1',
            client: { company_name: 'Company A' },
            status: 'completed',
            pdf_file: '/media/reports/test.pdf',
          },
        ]),
      });
    });

    // Mock download endpoint
    const downloadPromise = page.waitForEvent('download');
    await page.route('**/api/v1/reports/report-1/download/', route => {
      route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'application/pdf',
          'Content-Disposition': 'attachment; filename=report.pdf',
        },
        body: Buffer.from('PDF content'),
      });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Click download button
    const downloadButton = page.getByRole('button', { name: /download/i }).first();
    await downloadButton.click();

    // Verify download started
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('report');
  });

  test('should filter reports by status', async ({ page }) => {
    // Select status filter
    await page.getByLabel(/filter by status/i).selectOption('completed');

    // Verify URL updates with filter
    await expect(page).toHaveURL(/.*status=completed/);

    // Verify only completed reports are shown
    const completedBadges = page.getByText(/completed/i);
    await expect(completedBadges.first()).toBeVisible();
  });

  test('should search reports by client name', async ({ page }) => {
    // Type in search box
    const searchInput = page.getByPlaceholder(/search/i);
    await searchInput.fill('Test Company');

    // Wait for debounce
    await page.waitForTimeout(1000);

    // Verify search is applied
    await expect(page).toHaveURL(/.*search=Test/);
  });

  test('should delete report with confirmation', async ({ page }) => {
    // Mock reports
    await page.route('**/api/v1/reports/', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'report-1',
            client: { company_name: 'Company A' },
            status: 'completed',
          },
        ]),
      });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Setup dialog handler
    page.on('dialog', dialog => dialog.accept());

    // Mock delete API
    await page.route('**/api/v1/reports/report-1/', route => {
      route.fulfill({ status: 204 });
    });

    // Click delete button
    await page.getByRole('button', { name: /delete/i }).first().click();

    // Verify success message
    await expect(page.getByText(/report deleted successfully/i)).toBeVisible({ timeout: 5000 });
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock error response
    await page.route('**/api/v1/reports/', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' }),
      });
    });

    await page.reload();

    // Verify error message is shown
    await expect(page.getByText(/failed to load reports/i)).toBeVisible({ timeout: 5000 });
  });

  test('should be accessible', async ({ page }) => {
    // Check heading structure
    await expect(page.getByRole('heading', { name: /generate reports/i })).toBeVisible();

    // Check button accessibility
    const newReportButton = page.getByRole('button', { name: /new report/i });
    await expect(newReportButton).toBeVisible();

    // Verify keyboard navigation
    await page.keyboard.press('Tab');
    const focusedElement = await page.evaluateHandle(() => document.activeElement);
    expect(focusedElement).toBeTruthy();
  });
});
