# Frontend Testing Guide

This document provides comprehensive information about testing in the Azure Advisor Reports Platform frontend.

## Testing Stack

- **Unit/Integration Tests**: React Testing Library + Jest
- **E2E Tests**: Playwright
- **Coverage**: Jest Coverage Reports

## Test Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ComponentName.tsx
│   │   └── ComponentName.test.tsx
│   ├── pages/
│   │   ├── PageName.tsx
│   │   └── PageName.test.tsx
│   └── utils/
│       └── test-utils.tsx
└── e2e/
    ├── auth.setup.ts
    ├── dashboard.spec.ts
    └── report-generation.spec.ts
```

## Running Tests

### Unit and Integration Tests

```bash
# Run tests in watch mode (development)
npm test

# Run all tests once with coverage
npm run test:ci

# Run tests with coverage report
npm run test:coverage
```

### E2E Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run E2E tests with UI mode (interactive)
npm run test:e2e:ui

# Run E2E tests in headed mode (see browser)
npm run test:e2e:headed

# Debug E2E tests
npm run test:e2e:debug

# Run E2E tests only in Chromium
npm run test:e2e:chromium

# View test report
npm run test:e2e:report

# Run all tests (unit + E2E)
npm run test:all
```

## Writing Tests

### Unit Tests

Unit tests focus on individual components and functions in isolation.

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MyComponent from './MyComponent';

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('should handle user interactions', async () => {
    const user = userEvent.setup();
    render(<MyComponent />);

    await user.click(screen.getByRole('button'));
    expect(screen.getByText('Clicked')).toBeInTheDocument();
  });
});
```

### Integration Tests

Integration tests verify that multiple components work together correctly.

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import DashboardPage from './DashboardPage';
import { analyticsService } from '../services';

jest.mock('../services');

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

describe('DashboardPage', () => {
  it('should fetch and display data', async () => {
    (analyticsService.getDashboardAnalytics as jest.Mock).mockResolvedValue({
      metrics: { activeClients: 25 },
    });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <BrowserRouter>
          <DashboardPage />
        </BrowserRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('25')).toBeInTheDocument();
    });
  });
});
```

### E2E Tests

E2E tests verify complete user workflows from start to finish.

```typescript
import { test, expect } from '@playwright/test';

test.describe('Report Generation Flow', () => {
  test('should create a new report', async ({ page }) => {
    await page.goto('/reports');

    // Click new report button
    await page.getByRole('button', { name: /new report/i }).click();

    // Fill form
    await page.getByLabel(/select client/i).selectOption('client-id');

    // Upload file
    await page.setInputFiles('input[type="file"]', {
      name: 'test.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from('test,data'),
    });

    // Submit
    await page.getByRole('button', { name: /create/i }).click();

    // Verify success
    await expect(page.getByText(/success/i)).toBeVisible();
  });
});
```

## Test Utilities

### Mock Data

Use the pre-defined mock data in `utils/test-utils.tsx`:

```typescript
import { mockUser, mockClient, mockReport, createMockFile } from '../utils/test-utils';

// Use in your tests
render(<Component user={mockUser} />);
```

### Custom Render Function

The `render` function from `test-utils.tsx` provides common wrappers:

```typescript
import { render } from '../utils/test-utils';

render(<MyComponent />, {
  // Custom providers if needed
});
```

## Testing Best Practices

### 1. Test User Behavior, Not Implementation

❌ Bad:
```typescript
expect(component.state.count).toBe(1);
```

✅ Good:
```typescript
expect(screen.getByText('Count: 1')).toBeInTheDocument();
```

### 2. Use Accessible Queries

Prefer queries that reflect how users interact with your app:

```typescript
// Priority order:
screen.getByRole('button', { name: /submit/i })
screen.getByLabelText(/email/i)
screen.getByPlaceholderText(/search/i)
screen.getByText(/welcome/i)
screen.getByTestId('custom-element') // Last resort
```

### 3. Async Testing

Always use `waitFor` for async operations:

```typescript
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
});
```

### 4. Mock External Dependencies

Mock services and API calls:

```typescript
jest.mock('../services', () => ({
  apiService: {
    getData: jest.fn(),
  },
}));
```

### 5. Clean Up After Tests

```typescript
afterEach(() => {
  jest.clearAllMocks();
});
```

## Coverage Requirements

Current coverage targets:
- **Statements**: 80%
- **Branches**: 75%
- **Functions**: 80%
- **Lines**: 80%

### Viewing Coverage

```bash
npm run test:ci
```

Coverage reports are generated in:
- Console output
- `coverage/lcov-report/index.html` (open in browser)

## Accessibility Testing

### Unit Tests

Check for basic accessibility:

```typescript
it('should have proper ARIA labels', () => {
  render(<MyComponent />);

  expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
  expect(screen.getByLabelText(/email/i)).toHaveAttribute('type', 'email');
});
```

### E2E Tests

```typescript
test('should be keyboard navigable', async ({ page }) => {
  await page.goto('/dashboard');

  await page.keyboard.press('Tab');
  const focused = await page.evaluateHandle(() => document.activeElement);

  expect(focused).toBeTruthy();
});
```

## Continuous Integration

Tests run automatically on:
- Pull requests
- Pushes to main branch
- Scheduled nightly builds

### GitHub Actions

```yaml
- name: Run unit tests
  run: npm run test:ci

- name: Run E2E tests
  run: npm run test:e2e
```

## Debugging Tests

### Unit Tests

```bash
# Run specific test file
npm test -- MyComponent.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="should render"

# Update snapshots
npm test -- -u
```

### E2E Tests

```bash
# Debug mode (step through tests)
npm run test:e2e:debug

# Run specific test file
npx playwright test e2e/dashboard.spec.ts

# Run specific test by name
npx playwright test -g "should display dashboard"

# Show trace viewer
npx playwright show-trace trace.zip
```

## Common Issues

### 1. "ResizeObserver is not defined"

Already handled in `setupTests.ts`:

```typescript
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
```

### 2. Framer Motion Warnings

Already mocked in `setupTests.ts`

### 3. E2E Tests Timing Out

Increase timeout in `playwright.config.ts`:

```typescript
use: {
  actionTimeout: 10000,
  navigationTimeout: 30000,
}
```

### 4. Authentication in E2E Tests

Use `auth.setup.ts` to handle authentication:

```typescript
// Run before all tests
test.use({ storageState: 'playwright/.auth/user.json' });
```

## Test Organization

### File Naming

- Unit/Integration tests: `ComponentName.test.tsx`
- E2E tests: `feature-name.spec.ts`
- Test utilities: `test-utils.tsx`
- Mock data: `__mocks__/`

### Test Structure

```typescript
describe('ComponentName', () => {
  describe('Rendering', () => {
    it('should render correctly', () => {});
  });

  describe('User Interactions', () => {
    it('should handle clicks', () => {});
  });

  describe('Error Handling', () => {
    it('should display errors', () => {});
  });

  describe('Accessibility', () => {
    it('should be keyboard accessible', () => {});
  });
});
```

## Resources

- [React Testing Library Documentation](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev)
- [Jest Documentation](https://jestjs.io/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

## Getting Help

If you encounter issues with tests:

1. Check this documentation
2. Review existing test files for examples
3. Check the console output for specific errors
4. Consult the team's testing guidelines
5. Ask in the team's Slack channel

## Maintenance

### Updating Test Dependencies

```bash
npm update @testing-library/react @testing-library/jest-dom
npm update @playwright/test
```

### Running Test Audits

```bash
# Check for outdated test dependencies
npm outdated

# Security audit
npm audit
```

---

**Last Updated**: 2025-01-11
**Maintained By**: Development Team
