# QA Testing Strategy - Azure Advisor Reports Platform

**Document Type:** Quality Assurance & Testing Strategy
**Last Updated:** October 1, 2025
**Status:** Milestone 2 - In Progress
**Test Coverage Target:** Backend 85% | Frontend 70%

---

## Executive Summary

This document outlines the comprehensive testing strategy for the Azure Advisor Reports Platform. Based on the current implementation status (Milestone 2: 91% complete), this strategy identifies testing gaps, provides actionable recommendations, and establishes quality standards for the project.

### Current Testing Status

**Backend Testing:**
- Total Test Files: 10
- Total Test Cases: 292 collected
- Current Status: 148 errors, 119 failures, 25 passing
- Estimated Coverage: ~30-40% (needs fixing)
- Target Coverage: 85%

**Frontend Testing:**
- Total Test Files: 1 (App.test.tsx only)
- Test Coverage: 0% (no tests executing)
- Target Coverage: 70%

**Critical Gap:** Both backend and frontend testing infrastructure needs immediate attention.

---

## Table of Contents

1. [Testing Infrastructure](#testing-infrastructure)
2. [Backend Testing Strategy](#backend-testing-strategy)
3. [Frontend Testing Strategy](#frontend-testing-strategy)
4. [Integration Testing](#integration-testing)
5. [Test Coverage Gaps](#test-coverage-gaps)
6. [Testing Procedures](#testing-procedures)
7. [Quality Metrics](#quality-metrics)
8. [Recommendations](#recommendations)

---

## 1. Testing Infrastructure

### Backend (pytest + Django)

**Current Configuration:**
```ini
# pytest.ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = azure_advisor_reports.settings.testing
addopts = --cov=apps --cov-report=html --cov-fail-under=40
testpaths = apps/ tests/
```

**Installed Testing Tools:**
- pytest 8.4.2
- pytest-django 4.11.1
- pytest-cov 7.0.0
- pytest-Faker 37.8.0
- factory-boy (for test data factories)

**Test Markers:**
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.slow` - Performance tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.celery` - Celery task tests
- `@pytest.mark.azure` - Azure integration tests

### Frontend (Jest + React Testing Library)

**Current Configuration:**
```json
{
  "jest": {
    "collectCoverageFrom": [
      "src/**/*.{js,jsx,ts,tsx}",
      "!src/**/*.d.ts"
    ]
  }
}
```

**Installed Testing Tools:**
- Jest 29.7.0
- @testing-library/react 16.1.0
- @testing-library/jest-dom 6.6.3
- @testing-library/user-event 14.5.2

**Test File Pattern:** `*.test.{ts,tsx,js,jsx}`

### Test Fixtures & Factories

**Comprehensive Factory Support:**
```python
# Available Factories
- UserFactory (with role variations)
- AdminUserFactory
- ClientFactory
- ReportFactory (with status variations)
- RecommendationFactory
- ClientContactFactory
- ClientNoteFactory

# Specialized Factories
- PendingReportFactory
- ProcessingReportFactory
- CompletedReportFactory
- FailedReportFactory
- CostRecommendationFactory
- SecurityRecommendationFactory
```

---

## 2. Backend Testing Strategy

### 2.1 Current Test Coverage by Module

**Authentication Module** (`apps/authentication/`)
- ✅ Models: test_models.py (23 tests) - PASSING
- ✅ Permissions: test_permissions.py (20+ tests) - ERRORS
- ✅ Serializers: test_serializers.py (15+ tests) - ERRORS
- ✅ Services: test_services.py (20+ tests) - ERRORS
- ✅ Views: test_views.py (30+ tests) - ERRORS

**Status:** Infrastructure exists but tests are failing due to:
- Missing Azure AD mock implementations
- JWT token generation issues
- Serializer validation errors

**Clients Module** (`apps/clients/`)
- ✅ Models: test_models.py (42 tests) - PASSING
- ✅ Serializers: test_serializers.py (15+ tests) - ERRORS
- ✅ Services: test_services.py (25+ tests) - ERRORS
- ✅ Views: test_views.py (25+ tests) - ERRORS

**Status:** Comprehensive test coverage planned, but execution failing.

**Reports Module** (`apps/reports/`)
- ✅ Models: test_models.py (basic tests) - NEEDS EXPANSION
- ❌ Serializers: NOT IMPLEMENTED
- ❌ Services: NOT IMPLEMENTED
- ❌ Views: NOT IMPLEMENTED
- ❌ Tasks: NOT IMPLEMENTED (Celery)
- ❌ CSV Processing: NOT IMPLEMENTED
- ❌ Report Generation: NOT IMPLEMENTED

**Analytics Module** (`apps/analytics/`)
- ❌ No tests implemented
- ❌ Not yet in scope (Milestone 3)

### 2.2 Critical Test Gaps - Backend

**High Priority (Immediate Action Required):**

1. **Fix Authentication Tests (148 errors)**
   - Mock Azure AD service properly
   - Fix JWT token generation in tests
   - Update serializer tests with correct data
   - Verify permission tests execute correctly

2. **Reports Module Testing (0% coverage)**
   - Test Report model lifecycle
   - Test CSV file upload validation
   - Test file storage integration
   - Test report status transitions

3. **CSV Processing Tests (NOT IMPLEMENTED)**
   - Valid CSV parsing
   - Invalid CSV handling
   - Large file processing (performance)
   - Encoding issues (UTF-8, UTF-8-BOM)
   - Malformed data handling

4. **Celery Task Tests (NOT IMPLEMENTED)**
   - CSV processing task
   - Report generation task
   - Task failure handling
   - Task retry logic
   - Task status tracking

**Medium Priority:**

5. **API Integration Tests**
   - End-to-end report generation flow
   - Client creation → CSV upload → Report generation
   - Authentication flow with real JWT tokens
   - File upload to storage

6. **Security Tests**
   - SQL injection prevention (ORM validation)
   - XSS prevention in report output
   - CSRF protection
   - File upload security
   - Authentication bypass attempts

**Low Priority:**

7. **Performance Tests**
   - Large CSV file processing (1000+ rows)
   - Concurrent report generation
   - Database query optimization
   - API response times

### 2.3 Backend Test Plan

#### Phase 1: Fix Existing Tests (Week 1)

```bash
Priority 1: Fix Authentication Module
- Update Azure AD mocks in conftest.py
- Fix JWT token fixtures
- Resolve serializer validation issues
- Run: pytest apps/authentication/tests/ -v

Priority 2: Fix Clients Module
- Verify factory data matches model changes
- Update serializer test data
- Fix permission-related test failures
- Run: pytest apps/clients/tests/ -v
```

#### Phase 2: Reports Module Tests (Week 1-2)

```python
# Test Structure for Reports Module

# test_models.py
class TestReportModel:
    def test_report_creation(self):
        """Test basic report creation"""

    def test_report_status_transitions(self):
        """Test pending → processing → completed"""

    def test_report_with_recommendations(self):
        """Test report with associated recommendations"""

    def test_report_file_fields(self):
        """Test CSV, HTML, PDF file storage"""

# test_serializers.py
class TestReportSerializer:
    def test_report_list_serialization(self):
        """Test list view serialization"""

    def test_report_detail_serialization(self):
        """Test detail view with nested data"""

# test_services.py
class TestCSVProcessingService:
    def test_parse_valid_csv(self):
        """Test parsing valid Azure Advisor CSV"""

    def test_parse_invalid_csv(self):
        """Test error handling for invalid CSV"""

    def test_large_csv_processing(self):
        """Test performance with 1000+ rows"""

# test_tasks.py
class TestReportGenerationTask:
    def test_process_csv_task(self):
        """Test async CSV processing"""

    def test_generate_report_task(self):
        """Test report generation task"""

    def test_task_failure_handling(self):
        """Test task retry logic"""

# test_views.py
class TestReportAPIEndpoints:
    def test_upload_csv(self):
        """Test CSV upload endpoint"""

    def test_generate_report(self):
        """Test report generation trigger"""

    def test_download_report(self):
        """Test report download"""
```

#### Phase 3: Integration Tests (Week 2)

```python
# tests/integration/test_report_workflow.py

@pytest.mark.integration
class TestReportGenerationWorkflow:
    """End-to-end report generation tests"""

    def test_complete_report_generation_flow(
        self, authenticated_client, client_model, sample_csv_file
    ):
        """
        Test complete flow:
        1. Upload CSV
        2. Process CSV (create recommendations)
        3. Generate report
        4. Download report
        """
        # Step 1: Upload CSV
        response = authenticated_client.post(
            '/api/reports/upload/',
            {'client': client_model.id, 'csv_file': sample_csv_file},
            format='multipart'
        )
        assert response.status_code == 201
        report_id = response.data['id']

        # Step 2: Wait for processing (or mock Celery)
        report = Report.objects.get(id=report_id)
        assert report.status == 'completed'

        # Step 3: Generate report
        response = authenticated_client.post(
            f'/api/reports/{report_id}/generate/',
            {'report_type': 'detailed'}
        )
        assert response.status_code == 200

        # Step 4: Download report
        response = authenticated_client.get(
            f'/api/reports/{report_id}/download/?format=pdf'
        )
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
```

---

## 3. Frontend Testing Strategy

### 3.1 Current Frontend Test Coverage

**Critical Gap:** Only 1 test file exists (App.test.tsx) and it's failing.

**Coverage: 0% across all components**

### 3.2 Frontend Test Plan

#### Phase 1: Setup Testing Infrastructure (Week 1)

```bash
# Fix existing test setup
1. Fix App.test.tsx configuration
2. Update jest.config.js for TypeScript
3. Add test utilities and helpers
4. Create test setup file with mocks
```

#### Phase 2: Component Tests (Week 2-3)

**Authentication Components:**
```typescript
// src/components/auth/__tests__/LoginPage.test.tsx
describe('LoginPage', () => {
  it('renders login button', () => {
    render(<LoginPage />);
    expect(screen.getByText(/sign in with microsoft/i)).toBeInTheDocument();
  });

  it('initiates Azure AD login on button click', async () => {
    const mockLogin = jest.fn();
    render(<LoginPage />);

    const loginButton = screen.getByText(/sign in with microsoft/i);
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled();
    });
  });
});

// src/components/auth/__tests__/ProtectedRoute.test.tsx
describe('ProtectedRoute', () => {
  it('redirects to login when not authenticated', () => {
    // Mock unauthenticated state
    render(<ProtectedRoute><div>Protected</div></ProtectedRoute>);
    expect(screen.queryByText('Protected')).not.toBeInTheDocument();
  });

  it('renders children when authenticated', () => {
    // Mock authenticated state
    render(<ProtectedRoute><div>Protected</div></ProtectedRoute>);
    expect(screen.getByText('Protected')).toBeInTheDocument();
  });
});
```

**Client Management Components:**
```typescript
// src/components/clients/__tests__/ClientForm.test.tsx
describe('ClientForm', () => {
  it('renders form fields correctly', () => {
    render(<ClientForm onSubmit={jest.fn()} />);

    expect(screen.getByLabelText(/company name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/industry/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contact email/i)).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    const onSubmit = jest.fn();
    render(<ClientForm onSubmit={onSubmit} />);

    fireEvent.click(screen.getByText(/submit/i));

    await waitFor(() => {
      expect(screen.getByText(/company name is required/i)).toBeInTheDocument();
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    const onSubmit = jest.fn();
    render(<ClientForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText(/company name/i), {
      target: { value: 'Test Company' }
    });
    fireEvent.change(screen.getByLabelText(/contact email/i), {
      target: { value: 'test@example.com' }
    });

    fireEvent.click(screen.getByText(/submit/i));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          company_name: 'Test Company',
          contact_email: 'test@example.com'
        })
      );
    });
  });
});

// src/pages/__tests__/ClientsPage.test.tsx
describe('ClientsPage', () => {
  it('displays loading state initially', () => {
    render(<ClientsPage />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('displays clients after loading', async () => {
    const mockClients = [
      { id: '1', company_name: 'Client 1' },
      { id: '2', company_name: 'Client 2' }
    ];

    // Mock API response
    jest.spyOn(clientService, 'getClients').mockResolvedValue({
      results: mockClients,
      count: 2
    });

    render(<ClientsPage />);

    await waitFor(() => {
      expect(screen.getByText('Client 1')).toBeInTheDocument();
      expect(screen.getByText('Client 2')).toBeInTheDocument();
    });
  });

  it('handles search functionality', async () => {
    render(<ClientsPage />);

    const searchInput = screen.getByPlaceholderText(/search/i);
    fireEvent.change(searchInput, { target: { value: 'Test' } });

    await waitFor(() => {
      expect(clientService.getClients).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'Test' })
      );
    });
  });
});
```

**Service Layer Tests:**
```typescript
// src/services/__tests__/clientService.test.ts
describe('clientService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getClients', () => {
    it('fetches clients successfully', async () => {
      const mockData = { results: [], count: 0 };
      mockAxios.get.mockResolvedValue({ data: mockData });

      const result = await clientService.getClients();

      expect(mockAxios.get).toHaveBeenCalledWith('/api/clients/');
      expect(result).toEqual(mockData);
    });

    it('handles API errors', async () => {
      mockAxios.get.mockRejectedValue(new Error('Network error'));

      await expect(clientService.getClients()).rejects.toThrow();
    });
  });

  describe('createClient', () => {
    it('creates client with valid data', async () => {
      const clientData = {
        company_name: 'Test Co',
        contact_email: 'test@example.com'
      };

      mockAxios.post.mockResolvedValue({ data: { id: '1', ...clientData } });

      const result = await clientService.createClient(clientData);

      expect(mockAxios.post).toHaveBeenCalledWith('/api/clients/', clientData);
      expect(result.id).toBe('1');
    });
  });
});
```

#### Phase 3: Integration & E2E Tests (Week 3)

```typescript
// src/__tests__/integration/reportGeneration.test.tsx
describe('Report Generation Flow', () => {
  it('completes full report generation workflow', async () => {
    // 1. Login
    const { user } = renderWithAuth(<App />);

    // 2. Navigate to clients
    fireEvent.click(screen.getByText(/clients/i));

    // 3. Create new client
    fireEvent.click(screen.getByText(/add client/i));
    // ... fill form

    // 4. Upload CSV
    fireEvent.click(screen.getByText(/upload csv/i));
    // ... upload file

    // 5. Generate report
    fireEvent.click(screen.getByText(/generate report/i));

    // 6. Verify report appears
    await waitFor(() => {
      expect(screen.getByText(/report generated/i)).toBeInTheDocument();
    });
  });
});
```

---

## 4. Integration Testing

### 4.1 Integration Test Scenarios

**Critical User Journeys:**

1. **Authentication Flow**
   - Azure AD login → Token exchange → Access protected resources

2. **Client Management Flow**
   - Create client → View client → Update client → Delete client

3. **Report Generation Flow**
   - Upload CSV → Process CSV → Generate report → Download report

4. **Dashboard Analytics Flow**
   - Load dashboard → Fetch metrics → Display charts

### 4.2 Integration Test Infrastructure

```python
# tests/integration/conftest.py

@pytest.fixture
def integration_setup(db):
    """Setup complete test environment for integration tests"""
    # Create test users
    admin = UserFactory(role='admin')
    analyst = UserFactory(role='analyst')

    # Create test clients
    clients = ClientFactory.create_batch(3)

    # Create test reports
    for client in clients:
        report = ReportFactory(client=client, created_by=analyst)
        RecommendationFactory.create_batch(10, report=report)

    return {
        'admin': admin,
        'analyst': analyst,
        'clients': clients
    }

@pytest.mark.integration
class TestCompleteReportWorkflow:
    """Test complete report generation workflow"""

    def test_csv_to_pdf_workflow(self, integration_setup, api_client):
        """Test CSV upload → Processing → PDF generation"""
        # Test implementation
        pass
```

---

## 5. Test Coverage Gaps

### 5.1 Backend Coverage Gaps

| Module | Current Coverage | Target | Gap | Priority |
|--------|-----------------|--------|-----|----------|
| Authentication | ~40% (errors) | 85% | 45% | Critical |
| Clients | ~50% (errors) | 85% | 35% | High |
| Reports | ~10% | 85% | 75% | Critical |
| Analytics | 0% | 85% | 85% | Medium |
| Core/Utils | 0% | 70% | 70% | Low |

### 5.2 Frontend Coverage Gaps

| Component Type | Current Coverage | Target | Gap | Priority |
|---------------|-----------------|--------|-----|----------|
| Pages | 0% | 70% | 70% | Critical |
| Components | 0% | 70% | 70% | Critical |
| Services | 0% | 80% | 80% | Critical |
| Hooks | 0% | 75% | 75% | High |
| Utils | 0% | 85% | 85% | Medium |

### 5.3 Missing Test Categories

**Backend:**
- ❌ CSV processing edge cases
- ❌ Celery task tests
- ❌ File storage integration
- ❌ PDF generation tests
- ❌ Security vulnerability tests
- ❌ Performance benchmarks
- ❌ Azure service mocks

**Frontend:**
- ❌ Component unit tests
- ❌ Hook tests
- ❌ Service layer tests
- ❌ Integration tests
- ❌ Accessibility tests
- ❌ Visual regression tests
- ❌ E2E tests

---

## 6. Testing Procedures

### 6.1 Running Tests

**Backend Tests:**
```bash
# Run all tests
cd azure_advisor_reports
pytest

# Run specific module
pytest apps/authentication/tests/

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test markers
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests
pytest -m "not slow"        # Skip slow tests
pytest -m security          # Security tests

# Run with verbose output
pytest -v -s

# Run failed tests only
pytest --lf  # last failed
pytest --ff  # failed first
```

**Frontend Tests:**
```bash
# Run all tests
cd frontend
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- ClientForm.test.tsx

# Watch mode
npm test -- --watch

# Update snapshots
npm test -- -u
```

### 6.2 Pre-Commit Testing Checklist

```bash
# Before committing code:

1. Run linting
   - Backend: flake8 apps/
   - Frontend: npm run lint

2. Run tests
   - Backend: pytest apps/
   - Frontend: npm test

3. Check coverage
   - Backend: pytest --cov=apps --cov-fail-under=40
   - Frontend: npm test -- --coverage

4. Run type checking (frontend)
   - npm run type-check

5. Run security checks
   - pip install bandit && bandit -r apps/
   - npm audit
```

### 6.3 CI/CD Testing Pipeline

```yaml
# .github/workflows/tests.yml

name: Tests
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest --cov=apps --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test -- --coverage
```

---

## 7. Quality Metrics

### 7.1 Test Coverage Targets

**Backend (Django/Python):**
- Overall coverage: ≥ 85%
- Models: ≥ 90%
- Views/APIs: ≥ 85%
- Services: ≥ 80%
- Utils: ≥ 85%

**Frontend (React/TypeScript):**
- Overall coverage: ≥ 70%
- Components: ≥ 70%
- Hooks: ≥ 75%
- Services: ≥ 80%
- Utils: ≥ 85%

### 7.2 Test Quality Metrics

**Test Effectiveness:**
- Test execution time: < 2 minutes (unit tests)
- Test execution time: < 10 minutes (integration tests)
- Test flakiness: < 1% (tests should be deterministic)
- Code coverage increase: +10% per sprint minimum

**Test Maintenance:**
- Test-to-code ratio: 1:1 to 1:3
- Average test complexity: Keep tests simple and focused
- Test duplication: Minimize with fixtures and utilities

---

## 8. Recommendations

### 8.1 Immediate Actions (Week 1)

**Priority 1: Fix Existing Backend Tests**
```bash
1. Fix authentication test errors
   - Update Azure AD mocks in conftest.py
   - Fix JWT token generation
   - Resolve serializer validation issues

2. Fix client test errors
   - Verify factory data
   - Update test data to match current models
   - Fix permission-related failures

3. Achieve basic passing test suite
   - Target: All 292 tests passing
   - Current: 25 passing, 267 failing/errors
```

**Priority 2: Implement Reports Module Tests**
```bash
1. Create test files:
   - test_serializers.py
   - test_services.py
   - test_views.py
   - test_tasks.py (Celery)

2. Implement core tests:
   - CSV upload validation
   - CSV processing logic
   - Report generation
   - File storage
```

**Priority 3: Bootstrap Frontend Testing**
```bash
1. Fix App.test.tsx
2. Create test utilities and mocks
3. Implement first component tests:
   - LoginPage.test.tsx
   - ClientForm.test.tsx
   - ClientsPage.test.tsx
```

### 8.2 Short-term Actions (Week 2-3)

**Backend:**
- Implement integration tests for report workflow
- Add security tests (SQL injection, XSS, CSRF)
- Create performance benchmarks
- Document test patterns and best practices

**Frontend:**
- Complete component test coverage (70% target)
- Implement service layer tests
- Add integration tests
- Set up visual regression testing

### 8.3 Long-term Actions (Milestone 3)

**Advanced Testing:**
- E2E tests with Playwright/Cypress
- Load testing with Locust
- Security penetration testing
- Accessibility testing (WCAG 2.1)
- Visual regression testing
- Contract testing for APIs

**Automation:**
- Automated test generation
- Code coverage enforcement in CI/CD
- Automated security scanning
- Performance regression detection

### 8.4 Tools & Resources

**Recommended Additional Tools:**

**Backend:**
- `pytest-xdist` - Parallel test execution
- `pytest-benchmark` - Performance benchmarking
- `hypothesis` - Property-based testing
- `locust` - Load testing
- `bandit` - Security linting

**Frontend:**
- `@testing-library/user-event` - User interaction simulation
- `msw` (Mock Service Worker) - API mocking
- `jest-axe` - Accessibility testing
- `Playwright` or `Cypress` - E2E testing
- `Storybook` - Component development & testing

**Code Quality:**
- `SonarQube` - Code quality analysis
- `Codecov` - Coverage tracking
- `Snyk` - Security vulnerability scanning
- `Lighthouse CI` - Performance tracking

---

## 9. Test Documentation Standards

### 9.1 Test Naming Convention

```python
# Backend (pytest)
def test_<feature>_<scenario>_<expected_result>():
    """
    Clear docstring explaining:
    - What is being tested
    - Test scenario
    - Expected outcome
    """
    # Arrange
    # Act
    # Assert

# Example:
def test_csv_upload_with_invalid_format_returns_400():
    """Test that uploading a non-CSV file returns 400 Bad Request"""
    # Test implementation
```

```typescript
// Frontend (Jest)
describe('ComponentName', () => {
  describe('when condition', () => {
    it('should expected behavior', () => {
      // Test implementation
    });
  });
});

// Example:
describe('ClientForm', () => {
  describe('when submitting with invalid data', () => {
    it('should display validation errors', () => {
      // Test implementation
    });
  });
});
```

### 9.2 Test Structure (AAA Pattern)

```python
def test_example():
    # Arrange - Setup test data and mocks
    user = UserFactory()
    client_data = {'company_name': 'Test Co'}

    # Act - Execute the function being tested
    result = create_client(client_data, user)

    # Assert - Verify expected outcome
    assert result.company_name == 'Test Co'
    assert result.created_by == user
```

---

## 10. Next Steps for QA Team

### Week 1 Tasks (Priority Order)

1. **Day 1-2: Fix Authentication Tests**
   - Debug and fix 148 authentication test errors
   - Update mocks and fixtures
   - Document authentication test patterns

2. **Day 3: Fix Client Tests**
   - Resolve client module test failures
   - Verify all 107 client tests pass

3. **Day 4-5: Reports Module Testing**
   - Create reports test files
   - Implement core report tests
   - Achieve 40%+ coverage on reports module

### Week 2 Tasks

4. **Day 1-3: Integration Testing**
   - Create integration test suite
   - Test complete report generation flow
   - Test authentication integration

5. **Day 4-5: Frontend Testing Bootstrap**
   - Fix App.test.tsx
   - Create test utilities
   - Implement first 3 component tests

### Week 3 Tasks

6. **Frontend Test Coverage**
   - Complete component tests
   - Implement service layer tests
   - Reach 50%+ frontend coverage

7. **Documentation**
   - Document all test patterns
   - Create testing best practices guide
   - Update CLAUDE.md with testing info

---

## Appendix A: Test File Templates

### Backend Test Template

```python
# apps/module/tests/test_feature.py

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.module.models import Model
from tests.factories import ModelFactory

User = get_user_model()

@pytest.mark.unit
class TestModelName:
    """Unit tests for ModelName"""

    def test_model_creation(self, db):
        """Test basic model creation"""
        instance = ModelFactory()
        assert instance is not None
        assert str(instance)  # Test __str__

    def test_model_validation(self, db):
        """Test model validation"""
        # Test implementation

@pytest.mark.api
class TestAPIEndpoint:
    """API tests for endpoint"""

    def test_list_endpoint(self, authenticated_client):
        """Test GET /api/endpoint/"""
        response = authenticated_client.get('/api/endpoint/')
        assert response.status_code == 200

    def test_create_endpoint(self, authenticated_client):
        """Test POST /api/endpoint/"""
        data = {'field': 'value'}
        response = authenticated_client.post('/api/endpoint/', data)
        assert response.status_code == 201
```

### Frontend Test Template

```typescript
// src/components/__tests__/Component.test.tsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ComponentName } from '../ComponentName';

describe('ComponentName', () => {
  it('renders correctly', () => {
    render(<ComponentName />);
    expect(screen.getByText(/expected text/i)).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    const onAction = jest.fn();
    render(<ComponentName onAction={onAction} />);

    const button = screen.getByRole('button');
    fireEvent.click(button);

    await waitFor(() => {
      expect(onAction).toHaveBeenCalled();
    });
  });

  it('displays error state', () => {
    render(<ComponentName error="Error message" />);
    expect(screen.getByText(/error message/i)).toBeInTheDocument();
  });
});
```

---

## Appendix B: Common Test Patterns

### Testing Async Operations

```python
# Backend - Celery tasks
@pytest.mark.celery
def test_async_task(mocker):
    mock_task = mocker.patch('apps.reports.tasks.process_csv')
    mock_task.delay.return_value.id = 'task-123'

    result = trigger_csv_processing(report_id)

    assert mock_task.delay.called
    assert result.task_id == 'task-123'
```

```typescript
// Frontend - API calls
it('handles async data loading', async () => {
  const mockData = [{ id: '1', name: 'Test' }];
  jest.spyOn(api, 'getData').mockResolvedValue(mockData);

  render(<DataComponent />);

  expect(screen.getByTestId('loading')).toBeInTheDocument();

  await waitFor(() => {
    expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});
```

### Testing Error Handling

```python
def test_error_handling(api_client):
    """Test API error response"""
    response = api_client.post('/api/endpoint/', {})

    assert response.status_code == 400
    assert 'error' in response.data
    assert 'field is required' in str(response.data)
```

```typescript
it('displays error message on API failure', async () => {
  jest.spyOn(api, 'getData').mockRejectedValue(new Error('Network error'));

  render(<Component />);

  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument();
  });
});
```

---

**Document End**

*For questions or clarifications on testing strategy, contact the QA team or refer to CLAUDE.md for development guidelines.*
