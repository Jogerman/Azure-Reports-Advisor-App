# Test Coverage Improvement Plan

**Document Type:** Testing Strategy & Action Plan
**Created:** October 6, 2025
**Current Coverage:** 63.16%
**Target Coverage:** 85%
**Priority:** HIGH - Production Launch Dependency

---

## Executive Summary

### Current State
- **Overall Coverage:** 63.16% (1,766/2,796 lines covered)
- **Total Test Count:** 689 tests
- **Pass Rate:** 58% (400 passed, 163 failed, 126 errors)
- **Files with <50% Coverage:** 12 critical files
- **Gap to Target:** 21.84 percentage points

### Key Findings
1. **Critical Gaps Identified:**
   - Reports app views: 29.6% coverage (171 missing lines)
   - Report generators: 13.9-33.3% coverage (avg 24%)
   - Celery tasks: 9.9% coverage (137 missing lines)
   - Authentication views: 35.2% coverage (81 missing lines)

2. **Strengths:**
   - Models: 100% coverage across all apps
   - Serializers: 100% coverage (analytics)
   - Cache utilities: 98.1% coverage
   - Validators: 95.35% coverage (recently improved)

3. **Test Failures:**
   - 163 failed tests (primarily in views and integration tests)
   - 126 errors (mostly in authentication middleware/permissions)
   - Root cause: Missing test fixtures and database migrations

---

## Coverage Analysis by Application

### Analytics App - 69.4% Coverage ✅
**Status:** GOOD - Above 60%

| File | Coverage | Lines | Priority |
|------|----------|-------|----------|
| serializers.py | 100% | 65/65 | ✅ Complete |
| services.py | Good | 308/444 | Low |
| views.py | 30.0% | 30/100 | **HIGH** |
| models.py | 68.8% | 86/125 | Medium |

**Action Items:**
- [ ] Add view tests for dashboard metrics endpoint
- [ ] Test error handling in analytics services
- [ ] Add permission tests for analytics views

---

### Authentication App - 71.0% Coverage ✅
**Status:** GOOD - Above 70%

| File | Coverage | Lines | Priority |
|------|----------|-------|----------|
| models.py | 100% | 32/32 | ✅ Complete |
| views.py | 35.2% | 44/125 | **HIGH** |
| services.py | 65.2% | 103/158 | Medium |
| permissions.py | 64.6% | 42/65 | Medium |

**Action Items:**
- [ ] Fix 126 authentication test errors
- [ ] Add integration tests for Azure AD login flow
- [ ] Test JWT token refresh and expiration
- [ ] Add permission hierarchy tests
- [ ] Test middleware chain execution

---

### Clients App - 75.5% Coverage ✅
**Status:** EXCELLENT - Above 75%

| File | Coverage | Lines | Priority |
|------|----------|-------|----------|
| models.py | 100% | 79/79 | ✅ Complete |
| views.py | 48.4% | 62/128 | Medium |
| services.py | 74.0% | 91/123 | Low |

**Action Items:**
- [ ] Add client CRUD view tests
- [ ] Test search and filter functionality
- [ ] Add bulk operations tests

---

### Core App - 30.1% Coverage ❌
**Status:** CRITICAL - Needs Immediate Attention

| File | Coverage | Lines | Priority |
|------|----------|-------|----------|
| views.py | 16.8% | 17/101 | **CRITICAL** |
| exceptions.py | 59.0% | 23/39 | Medium |

**Action Items:**
- [ ] **CRITICAL:** Add health check endpoint tests
- [ ] Test custom exception handlers
- [ ] Add API root endpoint tests
- [ ] Test error response formatting

---

### Reports App - 56.6% Coverage ⚠️
**Status:** NEEDS IMPROVEMENT - Below Target

| File | Coverage | Lines | Priority |
|------|----------|-------|----------|
| tasks.py | 9.9% | 15/152 | **CRITICAL** |
| views.py | 29.6% | 72/243 | **CRITICAL** |
| generators/base.py | 21.6% | 21/97 | **HIGH** |
| generators/operations.py | 13.9% | 5/36 | **HIGH** |
| generators/security.py | 18.5% | 5/27 | **HIGH** |
| generators/cost.py | 25.0% | 5/20 | **HIGH** |
| generators/executive.py | 28.6% | 4/14 | **HIGH** |
| generators/detailed.py | 33.3% | 4/12 | **HIGH** |
| models.py | 100% | 126/126 | ✅ Complete |
| validators.py | 95.4% | - | ✅ Complete |
| cache.py | 98.1% | 102/104 | ✅ Complete |

**Action Items:**
- [ ] **CRITICAL:** Add Celery task tests (mocked)
- [ ] **CRITICAL:** Add report generation view tests
- [ ] Test CSV upload flow (end-to-end)
- [ ] Test all 5 report generator templates
- [ ] Add PDF generation tests
- [ ] Test async processing flow
- [ ] Add error recovery tests

---

## Priority Test Implementation Plan

### Phase 1: Critical Fixes (Week 1) - Target: 70% Coverage

**Priority 1A: Fix Failing Tests**
- [ ] Fix 126 authentication errors (middleware, permissions)
- [ ] Fix 163 failed view tests
- [ ] Resolve database migration issues
- [ ] Fix test fixture problems
- **Estimated Impact:** +5% coverage
- **Time:** 2-3 days

**Priority 1B: Core Infrastructure**
- [ ] Add core.views tests (health check, API root)
- [ ] Add reports.tasks tests (mocked Celery)
- [ ] Add basic report generation flow tests
- **Estimated Impact:** +7% coverage
- **Time:** 2 days

---

### Phase 2: Report Generation (Week 2) - Target: 78% Coverage

**Priority 2A: Report Generators**
- [ ] Test detailed report generation
- [ ] Test executive summary generation
- [ ] Test cost optimization report
- [ ] Test security assessment report
- [ ] Test operational excellence report
- **Estimated Impact:** +5% coverage
- **Time:** 3 days

**Priority 2B: Report Views & APIs**
- [ ] Test CSV upload endpoint
- [ ] Test report processing endpoint
- [ ] Test report download endpoint
- [ ] Test report statistics endpoint
- **Estimated Impact:** +3% coverage
- **Time:** 2 days

---

### Phase 3: Integration & Edge Cases (Week 3) - Target: 85%+

**Priority 3A: Integration Tests**
- [ ] Complete CSV upload → Processing → Report generation flow
- [ ] Test Azure AD authentication flow (mocked)
- [ ] Test concurrent report generation
- [ ] Test large CSV file processing
- **Estimated Impact:** +4% coverage
- **Time:** 2-3 days

**Priority 3B: Edge Cases & Error Handling**
- [ ] Test file upload validation edge cases
- [ ] Test network failure recovery
- [ ] Test database transaction rollbacks
- [ ] Test rate limiting
- [ ] Test permission boundaries
- **Estimated Impact:** +3% coverage
- **Time:** 2 days

---

## Detailed Test Requirements

### 1. Reports App - Celery Tasks (tasks.py - 9.9%)

**Missing Test Coverage (137 lines):**

```python
# Tests needed:
1. test_process_csv_task_success
   - Mock file upload
   - Verify CSV parsing
   - Check recommendation creation
   - Verify task completion

2. test_process_csv_task_invalid_file
   - Test with corrupt CSV
   - Verify error handling
   - Check status update

3. test_generate_report_task_success
   - Mock recommendation data
   - Test HTML generation
   - Test PDF generation
   - Verify file storage

4. test_generate_report_task_failure
   - Test with missing data
   - Verify retry logic
   - Check error logging

5. test_send_report_email_task
   - Mock email service
   - Test attachment handling
   - Verify recipient list

6. test_task_retry_mechanism
   - Simulate network failure
   - Verify exponential backoff
   - Test max retries

7. test_task_timeout_handling
   - Simulate long-running task
   - Verify timeout
   - Check cleanup

**Implementation Example:**
```python
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.reports.tasks import process_csv_task

class TestProcessCSVTask(TestCase):
    @patch('apps.reports.tasks.pandas.read_csv')
    @patch('apps.reports.tasks.Report.objects.get')
    def test_process_csv_task_success(self, mock_report, mock_read_csv):
        # Setup mocks
        mock_read_csv.return_value = pd.DataFrame({
            'Category': ['Cost'],
            'Business Impact': ['High'],
            'Recommendation': ['Test']
        })

        # Execute task
        result = process_csv_task.apply(args=['report-id-123'])

        # Assertions
        self.assertTrue(result.successful())
        mock_report.assert_called_once()
```

---

### 2. Reports App - Views (views.py - 29.6%)

**Missing Test Coverage (171 lines):**

```python
# Tests needed:
1. test_upload_csv_endpoint
   - Test successful upload
   - Test file size validation
   - Test file type validation
   - Test authentication required

2. test_process_csv_endpoint
   - Test triggers Celery task
   - Test status validation
   - Test error responses

3. test_download_report_endpoint
   - Test HTML download
   - Test PDF download
   - Test file not found
   - Test permission check

4. test_report_statistics_endpoint
   - Test metrics calculation
   - Test filtering
   - Test caching

5. test_report_recommendations_endpoint
   - Test pagination
   - Test filtering by category
   - Test filtering by impact
   - Test sorting

6. test_report_sharing_endpoint
   - Test share link creation
   - Test permission levels
   - Test expiration handling
```

---

### 3. Report Generators (13.9% - 33.3%)

**All Generators Need:**

```python
# Common test cases for each generator:
1. test_generate_with_valid_data
   - Test with sample recommendations
   - Verify HTML output structure
   - Check styling and formatting

2. test_generate_with_empty_data
   - Test graceful handling
   - Verify default messaging

3. test_generate_with_large_dataset
   - Test with 500+ recommendations
   - Verify performance
   - Check memory usage

4. test_generate_pdf
   - Test PDF conversion
   - Verify file size
   - Check readability

5. test_report_specific_logic
   - Detailed: Test all sections
   - Executive: Test summary calculations
   - Cost: Test savings totals
   - Security: Test risk categorization
   - Operations: Test reliability metrics

**Generator-Specific Tests:**

# Detailed Report
- Test resource grouping by subscription
- Test sorting by impact
- Test full recommendation details

# Executive Summary
- Test executive metrics calculation
- Test high-level statistics
- Test chart data generation

# Cost Optimization
- Test savings aggregation
- Test ROI calculations
- Test cost breakdown charts

# Security Assessment
- Test risk score calculation
- Test vulnerability prioritization
- Test compliance checks

# Operational Excellence
- Test reliability metrics
- Test availability scoring
- Test operational recommendations
```

---

### 4. Authentication Views (views.py - 35.2%)

**Missing Test Coverage (81 lines):**

```python
# Tests needed:
1. test_azure_ad_login_new_user
   - Mock Azure AD response
   - Verify user creation
   - Check JWT generation

2. test_azure_ad_login_existing_user
   - Mock Azure AD
   - Verify user update
   - Check last_login update

3. test_token_refresh
   - Test valid refresh token
   - Test expired token
   - Test invalid token

4. test_logout
   - Test token blacklisting
   - Test session cleanup

5. test_user_profile_update
   - Test partial update
   - Test validation
   - Test permission check

6. test_user_management_endpoints
   - Test list users (admin only)
   - Test user activation/deactivation
   - Test role changes
```

---

### 5. Analytics Views (views.py - 30.0%)

**Missing Test Coverage (70 lines):**

```python
# Tests needed:
1. test_dashboard_metrics_endpoint
   - Test metrics calculation
   - Test caching
   - Test date range filtering

2. test_trend_data_endpoint
   - Test 30-day trends
   - Test 90-day trends
   - Test data aggregation

3. test_category_distribution
   - Test percentage calculation
   - Test filtering

4. test_client_performance
   - Test per-client metrics
   - Test success rate calculation

5. test_recent_activity
   - Test activity feed
   - Test pagination
   - Test filtering by user

6. test_analytics_permissions
   - Test role-based access
   - Test data filtering by user
```

---

### 6. Integration Tests

**CSV Upload → Processing → Report Generation Flow:**

```python
class TestCompleteReportWorkflow(APITestCase):
    def test_end_to_end_report_generation(self):
        # 1. Create client
        client = Client.objects.create(company_name='Test Corp')

        # 2. Upload CSV
        with open('test_data/sample_advisor.csv', 'rb') as f:
            response = self.client.post('/api/reports/upload/', {
                'csv_file': f,
                'client_id': client.id,
                'report_type': 'detailed'
            })
        self.assertEqual(response.status_code, 201)
        report_id = response.data['id']

        # 3. Process CSV (mock Celery)
        with patch('apps.reports.tasks.process_csv_task.delay') as mock_task:
            response = self.client.post(f'/api/reports/{report_id}/process/')
            self.assertEqual(response.status_code, 202)
            mock_task.assert_called_once()

        # 4. Simulate task completion
        report = Report.objects.get(id=report_id)
        report.status = 'completed'
        report.save()

        # 5. Generate report
        response = self.client.post(f'/api/reports/{report_id}/generate/', {
            'formats': ['html', 'pdf']
        })
        self.assertEqual(response.status_code, 200)

        # 6. Download report
        response = self.client.get(f'/api/reports/{report_id}/download/html/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html')
```

---

## Testing Best Practices

### 1. Test Organization
```
apps/
  app_name/
    tests/
      __init__.py
      conftest.py           # Shared fixtures
      factories.py          # Factory Boy factories
      test_models.py        # Model tests
      test_serializers.py   # Serializer tests
      test_views.py         # View/API tests
      test_services.py      # Business logic tests
      test_tasks.py         # Celery task tests
      test_integration.py   # Integration tests
```

### 2. Fixture Management
```python
# Use Factory Boy for test data
import factory
from apps.clients.models import Client

class ClientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Client

    company_name = factory.Faker('company')
    contact_email = factory.Faker('email')
    status = 'active'

# Usage in tests
def test_something(self):
    client = ClientFactory()
    assert client.company_name is not None
```

### 3. Mocking External Services
```python
# Mock Azure AD calls
@patch('apps.authentication.services.AzureADService.validate_token')
def test_azure_login(self, mock_validate):
    mock_validate.return_value = {
        'sub': 'user-id-123',
        'email': 'test@example.com',
        'name': 'Test User'
    }
    # Test code here
```

### 4. Database Isolation
```python
# Use TransactionTestCase for Celery tests
from django.test import TransactionTestCase

class TestCeleryTasks(TransactionTestCase):
    def test_task_with_db_access(self):
        # Celery tasks run in separate transactions
        # Use TransactionTestCase for proper isolation
        pass
```

### 5. Performance Testing
```python
import time
from django.test import TestCase

class TestPerformance(TestCase):
    def test_large_csv_processing(self):
        start = time.time()
        # Process large CSV
        duration = time.time() - start
        self.assertLess(duration, 30.0, "Processing took too long")
```

---

## Success Metrics

### Coverage Targets by Phase

| Phase | Target Coverage | Estimated Date | Status |
|-------|----------------|----------------|--------|
| Phase 1: Critical Fixes | 70% | Week 1 | Pending |
| Phase 2: Report Generation | 78% | Week 2 | Pending |
| Phase 3: Integration | 85% | Week 3 | Pending |
| **Production Ready** | **85%+** | **Week 3** | **Pending** |

### Quality Metrics

- **Pass Rate:** 100% (all tests passing)
- **Code Coverage:** 85%+ overall
- **Critical Path Coverage:** 95%+ (CSV upload → Report generation)
- **Error Rate:** <1% false positives
- **Test Execution Time:** <5 minutes for full suite

---

## Risk Assessment

### High Risk Areas (Require Immediate Attention)

1. **Celery Tasks (9.9% coverage)**
   - **Risk:** Production failures in async processing
   - **Impact:** Critical - Reports won't generate
   - **Mitigation:** Priority 1A implementation

2. **Report Views (29.6% coverage)**
   - **Risk:** API endpoint failures
   - **Impact:** High - Users can't upload/download
   - **Mitigation:** Priority 1B and 2B

3. **Authentication Errors (126 errors)**
   - **Risk:** Security vulnerabilities
   - **Impact:** Critical - App unusable
   - **Mitigation:** Immediate fix required

### Medium Risk Areas

1. **Report Generators (13-33% coverage)**
   - **Risk:** Incorrect report output
   - **Impact:** Medium - Manual verification possible
   - **Mitigation:** Phase 2A implementation

2. **Analytics Views (30% coverage)**
   - **Risk:** Incorrect metrics
   - **Impact:** Medium - Not mission-critical
   - **Mitigation:** Phase 3B implementation

### Low Risk Areas

- Models (100% coverage) ✅
- Serializers (100% coverage) ✅
- Validators (95.4% coverage) ✅
- Cache utilities (98.1% coverage) ✅

---

## Resource Requirements

### Time Allocation
- **Phase 1:** 4-5 days (40 hours)
- **Phase 2:** 5 days (40 hours)
- **Phase 3:** 4-5 days (40 hours)
- **Total:** 2.5-3 weeks (120 hours)

### Team Requirements
- **QA Engineer:** 1 FTE (test writing, execution)
- **Backend Developer:** 0.5 FTE (fix failing tests, code review)
- **DevOps:** 0.25 FTE (CI/CD pipeline optimization)

### Tools & Infrastructure
- pytest + pytest-cov
- pytest-django
- Factory Boy (test fixtures)
- Faker (test data generation)
- pytest-mock (mocking)
- coverage.py (coverage reporting)
- GitHub Actions (CI/CD)

---

## Next Steps

### Immediate Actions (This Week)
1. [ ] Fix 126 authentication test errors
2. [ ] Fix 163 failed view tests
3. [ ] Add core.views health check tests
4. [ ] Add reports.tasks basic tests (mocked)
5. [ ] Generate updated coverage report

### Week 2 Actions
1. [ ] Implement all report generator tests
2. [ ] Add report view API tests
3. [ ] Create integration test suite
4. [ ] Target: 78% coverage

### Week 3 Actions
1. [ ] Complete integration tests
2. [ ] Add edge case tests
3. [ ] Performance testing
4. [ ] Final coverage: 85%+
5. [ ] **READY FOR PRODUCTION**

---

## Appendix A: Test Command Reference

```powershell
# Run all tests with coverage
pytest --cov=apps --cov-report=html --cov-report=term-missing

# Run specific app tests
pytest apps/reports/tests/ -v

# Run specific test file
pytest apps/reports/tests/test_tasks.py -v

# Run tests matching pattern
pytest -k "test_upload" -v

# Run failed tests only
pytest --lf

# Generate coverage report
coverage report -m
coverage html

# Run with profiling
pytest --durations=10

# Parallel execution (faster)
pytest -n auto
```

---

## Appendix B: Sample Test Data

Location: `D:\Code\Azure Reports\azure_advisor_reports\test_data\`

Required test CSV files:
- `sample_advisor_small.csv` (10 recommendations)
- `sample_advisor_medium.csv` (100 recommendations)
- `sample_advisor_large.csv` (500+ recommendations)
- `sample_advisor_invalid.csv` (malformed data)
- `sample_advisor_empty.csv` (no recommendations)

---

**Document Status:** DRAFT
**Next Review:** After Phase 1 completion
**Owner:** QA Team
**Last Updated:** October 6, 2025
