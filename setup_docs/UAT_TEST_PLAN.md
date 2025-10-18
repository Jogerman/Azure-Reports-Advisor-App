# User Acceptance Testing (UAT) Plan
## Azure Advisor Reports Platform

**Document Type:** User Acceptance Testing Strategy & Test Cases
**Version:** 1.0
**Created:** October 6, 2025
**Test Environment:** Staging (staging.azureadvisorreports.com)
**Target Go-Live Date:** October 20, 2025

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [UAT Objectives](#uat-objectives)
3. [Scope](#scope)
4. [Test Environment](#test-environment)
5. [Test Participants](#test-participants)
6. [Test Scenarios](#test-scenarios)
7. [Test Data](#test-data)
8. [Entry & Exit Criteria](#entry--exit-criteria)
9. [Defect Management](#defect-management)
10. [Sign-Off](#sign-off)

---

## Executive Summary

This UAT plan defines the approach, test scenarios, and success criteria for validating the Azure Advisor Reports Platform before production launch. The platform automates Azure Advisor report generation, reducing manual effort from 8 hours to 45 minutes per report.

### UAT Timeline

| Phase | Duration | Dates | Participants |
|-------|----------|-------|--------------|
| UAT Preparation | 2 days | Oct 8-9 | QA Team |
| UAT Execution | 5 days | Oct 10-16 | Business Users + QA |
| Defect Resolution | 2 days | Oct 17-18 | Dev Team |
| Regression Testing | 1 day | Oct 19 | QA Team |
| Sign-Off | 1 day | Oct 20 | Stakeholders |

### Success Metrics

- **Test Coverage:** 100% of critical user journeys tested
- **Pass Rate:** ≥95% of test cases pass
- **Defect Rate:** ≤5 critical/high defects
- **User Satisfaction:** ≥4.5/5.0 rating from UAT participants
- **Performance:** Report generation <45 seconds for 100-recommendation CSV

---

## UAT Objectives

### Primary Objectives

1. **Validate Business Requirements:** Confirm all features meet documented requirements
2. **Verify User Experience:** Ensure intuitive, user-friendly interface
3. **Test Real-World Scenarios:** Validate with actual Azure Advisor CSV exports
4. **Confirm Report Quality:** Verify generated reports meet quality standards
5. **Assess Performance:** Validate response times and system stability

### Secondary Objectives

1. Test error handling and recovery
2. Validate accessibility compliance (WCAG 2.1 AA)
3. Confirm cross-browser compatibility
4. Test mobile responsiveness
5. Verify email notifications (if implemented)

---

## Scope

### In Scope

#### Core Features
- ✅ Azure AD authentication and authorization
- ✅ Client management (CRUD operations)
- ✅ CSV file upload and validation
- ✅ Report generation (all 5 types)
- ✅ Report download (HTML and PDF)
- ✅ Dashboard analytics and metrics
- ✅ User profile management
- ✅ Report history and search

#### Report Types
1. Detailed Report (full recommendations)
2. Executive Summary (high-level overview)
3. Cost Optimization Report (savings focus)
4. Security Assessment Report (security focus)
5. Operational Excellence Report (reliability focus)

#### User Roles
- Admin
- Manager
- Analyst
- Viewer

### Out of Scope

- Infrastructure deployment (handled by DevOps)
- API-only integrations (future release)
- Mobile native apps (web only)
- Multi-language support (English only in v1.0)
- Custom report templates (future release)

---

## Test Environment

### Staging Environment Details

```
Frontend URL: https://staging-frontend.azureadvisorreports.com
Backend API: https://staging-api.azureadvisorreports.com/api
Admin Panel: https://staging-api.azureadvisorreports.com/admin

Azure AD Tenant: testing.onmicrosoft.com
Test Subscription: Azure-Test-Subscription-001
```

### Environment Configuration

| Component | Configuration | Status |
|-----------|---------------|--------|
| Frontend | React 18 on Azure App Service | ✅ Ready |
| Backend | Django 4.2 on Azure App Service | ✅ Ready |
| Database | PostgreSQL 15 (Azure Database) | ✅ Ready |
| Cache | Redis 7 (Azure Cache) | ✅ Ready |
| Storage | Azure Blob Storage | ✅ Ready |
| Monitoring | Application Insights | ✅ Ready |

### Test Data Requirements

- 5 test client organizations
- 20 sample CSV files (varying sizes: 10, 50, 100, 500, 1000 rows)
- 10 test user accounts (various roles)
- Sample Azure Advisor CSV exports from real subscriptions

---

## Test Participants

### UAT Team Structure

| Role | Name | Responsibilities | Time Commitment |
|------|------|------------------|----------------|
| **UAT Lead** | [TBD] | Overall coordination, sign-off | 100% (2 weeks) |
| **Business Analyst** | [TBD] | Requirements validation | 50% (1 week) |
| **Cloud Engineer** | [TBD] | Technical validation | 75% (1.5 weeks) |
| **Service Delivery Manager** | [TBD] | Process validation | 50% (1 week) |
| **End User (Analyst)** | [TBD] | Day-to-day usage testing | 50% (1 week) |
| **End User (Manager)** | [TBD] | Reporting & analytics testing | 25% (0.5 weeks) |
| **QA Engineer** | [TBD] | Test execution support | 100% (2 weeks) |

### Training Requirements

- **Pre-UAT Training Session:** 2 hours (Oct 7, 2025)
  - Platform overview
  - Test case walkthrough
  - Defect reporting process
  - Q&A session

---

## Test Scenarios

### TS-001: User Authentication & Authorization

**Priority:** CRITICAL
**User Role:** All
**Estimated Time:** 30 minutes

#### Test Cases

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-001-TC-001 | Azure AD Login - New User | 1. Click "Login with Microsoft"<br>2. Enter Azure AD credentials<br>3. Complete MFA (if required)<br>4. Grant permissions | User logged in successfully<br>Profile created<br>Redirected to dashboard | ⏳ |
| TS-001-TC-002 | Azure AD Login - Existing User | 1. Click "Login with Microsoft"<br>2. Enter credentials | User logged in<br>Last login updated<br>Dashboard displays | ⏳ |
| TS-001-TC-003 | Invalid Credentials | 1. Attempt login with wrong password | Login fails<br>Error message displayed | ⏳ |
| TS-001-TC-004 | Session Timeout | 1. Login<br>2. Wait 60 minutes idle<br>3. Attempt action | Session expired<br>Prompted to re-login | ⏳ |
| TS-001-TC-005 | Logout | 1. Click Logout | User logged out<br>Redirected to login page<br>Cannot access protected pages | ⏳ |
| TS-001-TC-006 | Role-Based Access - Viewer | 1. Login as Viewer<br>2. Attempt to create client | 403 Forbidden or button disabled | ⏳ |
| TS-001-TC-007 | Role-Based Access - Manager | 1. Login as Manager<br>2. Create client<br>3. Generate report | Client created<br>Report generated successfully | ⏳ |

**Acceptance Criteria:**
- ✅ All users can login with Azure AD
- ✅ Roles enforced correctly
- ✅ Session management works as expected

---

### TS-002: Client Management

**Priority:** HIGH
**User Role:** Manager, Admin
**Estimated Time:** 45 minutes

#### Test Cases

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-002-TC-001 | Create New Client | 1. Navigate to Clients<br>2. Click "Add Client"<br>3. Fill form (Company Name, Industry, Email)<br>4. Click Save | Client created<br>Appears in client list<br>Success message shown | ⏳ |
| TS-002-TC-002 | View Client Details | 1. Click on client name | Client details displayed<br>Associated reports shown | ⏳ |
| TS-002-TC-003 | Edit Client | 1. Open client<br>2. Click Edit<br>3. Modify fields<br>4. Save | Changes saved<br>Updated in list | ⏳ |
| TS-002-TC-004 | Search Clients | 1. Enter search term in search box | Filtered results displayed<br>Matches company name | ⏳ |
| TS-002-TC-005 | Filter Clients by Status | 1. Select "Active" filter | Only active clients shown | ⏳ |
| TS-002-TC-006 | Delete Client (No Reports) | 1. Select client without reports<br>2. Click Delete<br>3. Confirm | Client deleted<br>Removed from list | ⏳ |
| TS-002-TC-007 | Delete Client (With Reports) | 1. Select client with reports<br>2. Click Delete | Warning shown about associated reports<br>Option to proceed or cancel | ⏳ |
| TS-002-TC-008 | Validation - Required Fields | 1. Click "Add Client"<br>2. Leave Company Name blank<br>3. Click Save | Validation error shown<br>Form not submitted | ⏳ |
| TS-002-TC-009 | Validation - Invalid Email | 1. Enter invalid email format<br>2. Click Save | Email validation error<br>Form not submitted | ⏳ |

**Acceptance Criteria:**
- ✅ Full CRUD operations work
- ✅ Search and filter functional
- ✅ Validation prevents invalid data

---

### TS-003: CSV Upload & Validation

**Priority:** CRITICAL
**User Role:** Analyst, Manager, Admin
**Estimated Time:** 60 minutes

#### Test Cases

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-003-TC-001 | Upload Valid CSV - Small (10 rows) | 1. Select client<br>2. Click "Upload CSV"<br>3. Select 10-row CSV<br>4. Choose report type<br>5. Upload | File uploaded successfully<br>Processing status shown<br>Preview available | ⏳ |
| TS-003-TC-002 | Upload Valid CSV - Medium (100 rows) | Same as above with 100-row CSV | File uploaded<br>Processing completes in <10s | ⏳ |
| TS-003-TC-003 | Upload Valid CSV - Large (500 rows) | Same as above with 500-row CSV | File uploaded<br>Processing completes in <30s | ⏳ |
| TS-003-TC-004 | Upload Invalid File Type (.xlsx) | 1. Attempt to upload Excel file | File rejected<br>Error: "Only CSV files accepted" | ⏳ |
| TS-003-TC-005 | Upload Oversized File (>50MB) | 1. Upload file >50MB | File rejected<br>Error: "File too large" | ⏳ |
| TS-003-TC-006 | Upload Malformed CSV | 1. Upload CSV with missing columns | File rejected<br>Error: "Invalid CSV format" | ⏳ |
| TS-003-TC-007 | Upload CSV with Special Characters | 1. Upload CSV with Unicode characters | File processed successfully<br>Characters displayed correctly | ⏳ |
| TS-003-TC-008 | Upload CSV with Empty Rows | 1. Upload CSV with blank rows | Empty rows ignored<br>Valid rows processed | ⏳ |
| TS-003-TC-009 | Cancel Upload | 1. Start upload<br>2. Click Cancel during upload | Upload canceled<br>No partial data saved | ⏳ |
| TS-003-TC-010 | Re-upload After Error | 1. Upload invalid file<br>2. Upload valid file | Second upload succeeds<br>Error cleared | ⏳ |

**Test Data Required:**
- sample_advisor_10rows.csv
- sample_advisor_100rows.csv
- sample_advisor_500rows.csv
- sample_advisor_invalid.csv (missing columns)
- sample_advisor_unicode.csv (special characters)
- large_file_60mb.csv (size test)
- sample_report.xlsx (wrong type)

**Acceptance Criteria:**
- ✅ Valid CSV files upload successfully
- ✅ Invalid files rejected with clear error messages
- ✅ Large files process within performance SLA
- ✅ File validation prevents malicious uploads

---

### TS-004: Report Generation

**Priority:** CRITICAL
**User Role:** Analyst, Manager, Admin
**Estimated Time:** 90 minutes

#### Test Cases - Detailed Report

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-004-TC-001 | Generate Detailed Report | 1. Upload CSV with 100 rows<br>2. Wait for processing<br>3. Click "Generate Report"<br>4. Select "Detailed Report"<br>5. Select HTML format<br>6. Generate | Report generated in <30s<br>All recommendations included<br>Proper formatting<br>Client branding visible | ⏳ |
| TS-004-TC-002 | Detailed Report - Content Validation | 1. Review generated report | All sections present:<br>- Executive Summary<br>- Recommendation Details<br>- Resource Breakdown<br>- Cost Analysis<br>- Charts/graphs | ⏳ |
| TS-004-TC-003 | Detailed Report - PDF Format | 1. Generate as PDF | PDF downloads<br>Readable content<br>Professional formatting<br>Charts render correctly | ⏳ |

#### Test Cases - Executive Summary

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-004-TC-004 | Generate Executive Summary | 1. Select "Executive Summary" type<br>2. Generate | Report generated<br>High-level metrics only<br>1-2 pages maximum | ⏳ |
| TS-004-TC-005 | Executive Summary - Metrics | Review report content | Contains:<br>- Total recommendations<br>- Potential savings (total)<br>- Business impact distribution<br>- Top 5 recommendations | ⏳ |

#### Test Cases - Cost Optimization Report

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-004-TC-006 | Generate Cost Report | 1. Select "Cost Optimization"<br>2. Generate | Report focuses on cost items<br>Savings calculations accurate<br>ROI metrics included | ⏳ |
| TS-004-TC-007 | Cost Report - Savings Calculation | Verify calculations | Total savings matches sum<br>Currency displayed (USD)<br>High-savings items highlighted | ⏳ |

#### Test Cases - Security Assessment

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-004-TC-008 | Generate Security Report | 1. Select "Security Assessment"<br>2. Generate | Security recommendations only<br>Risk levels categorized<br>Compliance notes included | ⏳ |

#### Test Cases - Operational Excellence

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-004-TC-009 | Generate Operations Report | 1. Select "Operational Excellence"<br>2. Generate | Operations/reliability focus<br>Availability recommendations<br>Best practices included | ⏳ |

#### Cross-Report Test Cases

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-004-TC-010 | Generate All Report Types | 1. Generate all 5 types for same client | All reports generate successfully<br>Each has appropriate content<br>No errors | ⏳ |
| TS-004-TC-011 | Concurrent Report Generation | 1. Generate 3 reports simultaneously | All complete successfully<br>No performance degradation | ⏳ |
| TS-004-TC-012 | Report with No Recommendations | 1. Process empty CSV<br>2. Generate report | Report shows "No recommendations"<br>Graceful handling | ⏳ |
| TS-004-TC-013 | Report Regeneration | 1. Generate report<br>2. Delete generated files<br>3. Regenerate | New report created successfully<br>Identical to original | ⏳ |

**Acceptance Criteria:**
- ✅ All 5 report types generate correctly
- ✅ Reports complete within 45 seconds
- ✅ HTML and PDF formats both functional
- ✅ Report content accurate and complete
- ✅ Professional formatting and branding

---

### TS-005: Report Download & Viewing

**Priority:** HIGH
**User Role:** All
**Estimated Time:** 30 minutes

#### Test Cases

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-005-TC-001 | Download HTML Report | 1. Click "Download HTML" | File downloads<br>Opens in browser<br>Readable content | ⏳ |
| TS-005-TC-002 | Download PDF Report | 1. Click "Download PDF" | File downloads<br>Opens in PDF reader<br>Formatted correctly | ⏳ |
| TS-005-TC-003 | Preview Report in Browser | 1. Click "Preview" | Report opens in new tab<br>All content visible<br>Charts/images load | ⏳ |
| TS-005-TC-004 | Download Report - Not Owner | 1. Login as different user<br>2. Access report URL | Report accessible (if permissions allow)<br>Or 403 Forbidden | ⏳ |
| TS-005-TC-005 | Download Large PDF (500 recs) | 1. Download PDF with 500 recommendations | File downloads successfully<br>All pages render<br>File size reasonable (<10MB) | ⏳ |
| TS-005-TC-006 | Print Report | 1. Open report in browser<br>2. Print | Print preview looks professional<br>Page breaks appropriate | ⏳ |

**Acceptance Criteria:**
- ✅ Download links work reliably
- ✅ Reports viewable in browser and PDF reader
- ✅ File permissions enforced

---

### TS-006: Dashboard & Analytics

**Priority:** MEDIUM
**User Role:** Manager, Admin
**Estimated Time:** 45 minutes

#### Test Cases

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-006-TC-001 | View Dashboard Metrics | 1. Navigate to Dashboard | Metrics displayed:<br>- Total clients<br>- Total reports<br>- Avg processing time<br>- Total savings | ⏳ |
| TS-006-TC-002 | View Trend Charts | Scroll to charts | 30-day trend chart visible<br>Report generation over time<br>Interactive tooltips | ⏳ |
| TS-006-TC-003 | Category Distribution | Review pie chart | Recommendation breakdown by category<br>Percentages shown<br>Color-coded | ⏳ |
| TS-006-TC-004 | Client Performance | View client list on dashboard | Top clients by report count<br>Success rate shown<br>Sortable | ⏳ |
| TS-006-TC-005 | Recent Activity Feed | Check activity section | Recent report generations listed<br>Timestamps accurate<br>User attribution correct | ⏳ |
| TS-006-TC-006 | Filter Dashboard by Date | 1. Select date range (last 7 days) | Metrics recalculate<br>Charts update<br>Filters persist | ⏳ |
| TS-006-TC-007 | Export Dashboard Data | 1. Click "Export" (if available) | Data exports to CSV/Excel<br>All metrics included | ⏳ |
| TS-006-TC-008 | Dashboard Performance | 1. Refresh dashboard with 100+ reports | Loads in <3 seconds<br>No lag when scrolling | ⏳ |

**Acceptance Criteria:**
- ✅ All metrics calculate correctly
- ✅ Charts render properly
- ✅ Dashboard loads quickly
- ✅ Data filters work

---

### TS-007: User Profile Management

**Priority:** LOW
**User Role:** All
**Estimated Time:** 20 minutes

#### Test Cases

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-007-TC-001 | View Profile | 1. Click profile icon<br>2. Select "Profile" | Profile page displays<br>Shows name, email, role, last login | ⏳ |
| TS-007-TC-002 | Update Profile | 1. Click Edit<br>2. Change display name<br>3. Save | Changes saved<br>Name updated throughout app | ⏳ |
| TS-007-TC-003 | Update Profile Photo | 1. Upload photo<br>2. Save | Photo updated<br>Displayed in header | ⏳ |
| TS-007-TC-004 | Change Notification Preferences | 1. Toggle email notifications<br>2. Save | Preferences saved<br>Notifications respect settings | ⏳ |

**Acceptance Criteria:**
- ✅ Profile edits save correctly
- ✅ Changes reflect immediately

---

### TS-008: Search & Filter

**Priority:** MEDIUM
**User Role:** All
**Estimated Time:** 30 minutes

#### Test Cases

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-008-TC-001 | Search Reports by Name | 1. Enter report name in search | Matching reports shown<br>Non-matching hidden | ⏳ |
| TS-008-TC-002 | Filter Reports by Client | 1. Select client from dropdown | Only that client's reports shown | ⏳ |
| TS-008-TC-003 | Filter Reports by Status | 1. Select "Completed" status | Only completed reports shown | ⏳ |
| TS-008-TC-004 | Filter Reports by Type | 1. Select "Cost Optimization" | Only cost reports shown | ⏳ |
| TS-008-TC-005 | Filter Reports by Date Range | 1. Set date range (last 30 days) | Reports within range shown | ⏳ |
| TS-008-TC-006 | Combined Filters | 1. Apply multiple filters | Results match all filter criteria (AND logic) | ⏳ |
| TS-008-TC-007 | Clear Filters | 1. Click "Clear Filters" | All filters removed<br>All reports shown | ⏳ |
| TS-008-TC-008 | No Results Found | 1. Search for non-existent term | "No results" message shown<br>Option to clear search | ⏳ |

**Acceptance Criteria:**
- ✅ Search is fast (<1 second)
- ✅ Filters work independently and combined
- ✅ Clear UX for no results

---

### TS-009: Error Handling & Recovery

**Priority:** HIGH
**User Role:** All
**Estimated Time:** 45 minutes

#### Test Cases

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-009-TC-001 | Handle Network Timeout | 1. Disconnect network during upload<br>2. Wait for timeout | Error message displayed<br>Option to retry<br>Partial data not saved | ⏳ |
| TS-009-TC-002 | Handle Server Error (500) | 1. Trigger server error (via test endpoint) | Generic error message<br>No stack trace exposed<br>Error logged | ⏳ |
| TS-009-TC-003 | Handle Invalid CSV | 1. Upload corrupted CSV | Clear error message<br>Instructions to fix<br>Option to upload new file | ⏳ |
| TS-009-TC-004 | Handle Permission Denied | 1. Attempt unauthorized action | 403 error with explanation<br>Redirect to appropriate page | ⏳ |
| TS-009-TC-005 | Handle Page Not Found | 1. Navigate to invalid URL | 404 page displayed<br>Link back to home | ⏳ |
| TS-009-TC-006 | Recover from Failed Report Gen | 1. Upload CSV<br>2. Simulate processing failure<br>3. Retry | Retry succeeds<br>No duplicate data<br>Status updates correctly | ⏳ |

**Acceptance Criteria:**
- ✅ All errors display user-friendly messages
- ✅ No sensitive information leaked
- ✅ Recovery options provided where appropriate

---

### TS-010: Performance & Usability

**Priority:** HIGH
**User Role:** All
**Estimated Time:** 45 minutes

#### Test Cases

| ID | Test Case | Steps | Expected Result | Status |
|----|-----------|-------|----------------|--------|
| TS-010-TC-001 | Page Load Time | 1. Navigate to various pages | All pages load in <2 seconds | ⏳ |
| TS-010-TC-002 | CSV Upload (100 rows) | 1. Upload 100-row CSV | Upload completes in <5 seconds | ⏳ |
| TS-010-TC-003 | CSV Processing (100 rows) | 1. Process 100-row CSV | Processing completes in <10 seconds | ⏳ |
| TS-010-TC-004 | Report Generation (100 recs) | 1. Generate detailed report | Completes in <30 seconds | ⏳ |
| TS-010-TC-005 | Report Generation (500 recs) | 1. Generate detailed report | Completes in <45 seconds | ⏳ |
| TS-010-TC-006 | Dashboard Load with 100+ Reports | 1. Load dashboard | Displays in <3 seconds | ⏳ |
| TS-010-TC-007 | Search Performance | 1. Search in 100+ reports | Results in <1 second | ⏳ |
| TS-010-TC-008 | Concurrent Users (10) | 1. Simulate 10 users simultaneously | No performance degradation<br>All operations complete | ⏳ |
| TS-010-TC-009 | Mobile Responsiveness | 1. Access on mobile device | UI adapts to screen size<br>All functions accessible | ⏳ |
| TS-010-TC-010 | Browser Compatibility - Chrome | Test all features in Chrome | All features work | ⏳ |
| TS-010-TC-011 | Browser Compatibility - Firefox | Test all features in Firefox | All features work | ⏳ |
| TS-010-TC-012 | Browser Compatibility - Edge | Test all features in Edge | All features work | ⏳ |
| TS-010-TC-013 | Accessibility - Keyboard Navigation | 1. Navigate using only keyboard | All interactive elements accessible<br>Tab order logical | ⏳ |
| TS-010-TC-014 | Accessibility - Screen Reader | 1. Use screen reader (NVDA/JAWS) | All content announced<br>Proper ARIA labels | ⏳ |

**Performance Benchmarks:**
- Page load: <2 seconds
- CSV upload (100 rows): <5 seconds
- CSV processing (100 rows): <10 seconds
- Report generation (100 recs): <30 seconds
- Report generation (500 recs): <45 seconds
- Dashboard load: <3 seconds
- Search results: <1 second

**Acceptance Criteria:**
- ✅ 90% of operations meet performance benchmarks
- ✅ Mobile experience is usable
- ✅ Works in Chrome, Firefox, Edge (latest versions)
- ✅ Keyboard navigation functional
- ✅ Basic screen reader support

---

## Test Data

### Test Users

| Username | Email | Role | Password | Notes |
|----------|-------|------|----------|-------|
| admin@test.com | admin@test.com | Admin | [Provided separately] | Full access |
| manager@test.com | manager@test.com | Manager | [Provided separately] | Can manage clients, generate reports |
| analyst@test.com | analyst@test.com | Analyst | [Provided separately] | Can create/view reports |
| viewer@test.com | viewer@test.com | Viewer | [Provided separately] | Read-only access |

### Test Clients

| Company Name | Industry | Contact Email | Status |
|--------------|----------|---------------|--------|
| Acme Corp | Technology | contact@acme.example.com | Active |
| Globex Inc | Manufacturing | info@globex.example.com | Active |
| Initech LLC | Financial Services | support@initech.example.com | Active |
| Umbrella Corp | Healthcare | admin@umbrella.example.com | Inactive |
| Stark Industries | Technology | contact@stark.example.com | Active |

### Test CSV Files

Location: `D:\Code\Azure Reports\test_data\`

| Filename | Rows | Size | Purpose |
|----------|------|------|---------|
| sample_advisor_10.csv | 10 | 2 KB | Quick test |
| sample_advisor_100.csv | 100 | 15 KB | Standard test |
| sample_advisor_500.csv | 500 | 75 KB | Large test |
| sample_advisor_1000.csv | 1000 | 150 KB | Performance test |
| sample_advisor_invalid.csv | - | - | Error handling |
| sample_advisor_unicode.csv | 50 | 10 KB | Special characters |

---

## Entry & Exit Criteria

### Entry Criteria (All must be met to start UAT)

- [ ] All development complete (features implemented)
- [ ] Unit tests passing (≥85% coverage)
- [ ] Integration tests passing
- [ ] System testing complete
- [ ] Staging environment deployed and stable
- [ ] Test data prepared
- [ ] UAT participants trained
- [ ] Defect tracking system ready

### Exit Criteria (All must be met to launch)

- [ ] All critical test scenarios executed
- [ ] ≥95% of test cases pass
- [ ] Zero critical defects open
- [ ] ≤2 high-priority defects open (with workarounds)
- [ ] Performance benchmarks met
- [ ] Security testing complete
- [ ] Accessibility compliance verified (WCAG 2.1 AA)
- [ ] User satisfaction ≥4.5/5.0
- [ ] Stakeholder sign-off obtained

---

## Defect Management

### Defect Severity Definitions

| Severity | Definition | Example | Response Time |
|----------|------------|---------|---------------|
| **Critical** | System unusable, data loss, security issue | Cannot login, data corruption | 4 hours |
| **High** | Major feature broken, no workaround | Report generation fails | 1 day |
| **Medium** | Feature partially broken, workaround exists | Filter not working, can search manually | 3 days |
| **Low** | Minor UI issue, cosmetic | Typo, alignment issue | 1 week |

### Defect Reporting Process

1. **Discovery:** Tester identifies issue during UAT
2. **Documentation:** Create defect in tracking system with:
   - Clear title
   - Steps to reproduce
   - Expected vs. actual result
   - Screenshots/videos
   - Environment details
   - Severity assessment
3. **Triage:** Dev team reviews and assigns priority
4. **Resolution:** Developer fixes issue
5. **Verification:** Tester retests and verifies fix
6. **Closure:** Defect marked as closed

### Defect Tracking Template

```
Defect ID: DEF-001
Title: [Brief description]
Severity: [Critical/High/Medium/Low]
Priority: [P1/P2/P3/P4]
Reported By: [Name]
Date Reported: [Date]
Test Case: [TS-XXX-TC-XXX]

Steps to Reproduce:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Expected Result:
[What should happen]

Actual Result:
[What actually happened]

Screenshots/Evidence:
[Attach files]

Environment:
- Browser: [Chrome/Firefox/Edge]
- OS: [Windows/Mac/Linux]
- URL: [Staging URL]

Status: [Open/In Progress/Resolved/Closed]
Resolution Notes: [Developer comments]
Verified By: [Tester name]
Verification Date: [Date]
```

---

## Test Execution Tracking

### Overall Progress

| Test Scenario | Total TCs | Executed | Passed | Failed | Blocked | % Complete |
|---------------|-----------|----------|--------|--------|---------|------------|
| TS-001: Authentication | 7 | 0 | 0 | 0 | 0 | 0% |
| TS-002: Client Management | 9 | 0 | 0 | 0 | 0 | 0% |
| TS-003: CSV Upload | 10 | 0 | 0 | 0 | 0 | 0% |
| TS-004: Report Generation | 14 | 0 | 0 | 0 | 0 | 0% |
| TS-005: Report Download | 6 | 0 | 0 | 0 | 0 | 0% |
| TS-006: Dashboard | 8 | 0 | 0 | 0 | 0 | 0% |
| TS-007: User Profile | 4 | 0 | 0 | 0 | 0 | 0% |
| TS-008: Search & Filter | 8 | 0 | 0 | 0 | 0 | 0% |
| TS-009: Error Handling | 6 | 0 | 0 | 0 | 0 | 0% |
| TS-010: Performance | 14 | 0 | 0 | 0 | 0 | 0% |
| **TOTAL** | **86** | **0** | **0** | **0** | **0** | **0%** |

### Daily Testing Log

**Date: ________**

| Tester | Hours | Test Scenarios Completed | Defects Found | Notes |
|--------|-------|-------------------------|---------------|-------|
| | | | | |
| | | | | |

---

## Sign-Off

### UAT Completion Sign-Off

**Project:** Azure Advisor Reports Platform
**Version:** 1.0
**UAT Completion Date:** ___________

I hereby confirm that User Acceptance Testing has been completed satisfactorily and the system is ready for production deployment.

| Stakeholder | Role | Signature | Date | Comments |
|-------------|------|-----------|------|----------|
| | UAT Lead | | | |
| | Business Owner | | | |
| | IT Manager | | | |
| | Product Manager | | | |
| | QA Manager | | | |

### Approval for Production Release

Based on the successful completion of UAT, I approve this system for production release.

**Name:** _______________________
**Title:** _______________________
**Signature:** _______________________
**Date:** _______________________

---

## Appendices

### Appendix A: Test Environment Setup Guide

See: `DEPLOYMENT_RUNBOOK.md`

### Appendix B: Known Limitations

1. Internet Explorer not supported (Edge Chromium required)
2. File upload limited to 50MB
3. Concurrent processing limited to 10 reports
4. Mobile app not available (web-responsive only)
5. Report retention: 90 days (configurable)

### Appendix C: UAT Feedback Survey

**Post-UAT User Satisfaction Survey:**

1. How easy was it to learn the system? (1-5)
2. How satisfied are you with the report quality? (1-5)
3. How satisfied are you with system performance? (1-5)
4. How likely are you to recommend this tool? (1-10)
5. What did you like most?
6. What needs improvement?
7. Any missing features?

### Appendix D: Contact Information

**UAT Support:**
- UAT Lead: [Name] - [Email]
- QA Engineer: [Name] - [Email]
- Tech Lead: [Name] - [Email]

**Issue Reporting:**
- Defect Tracking: [URL]
- Support Email: uat-support@example.com
- Slack Channel: #uat-azure-reports

---

**Document Status:** READY FOR EXECUTION
**Next Review:** Post-UAT (October 20, 2025)
**Owner:** QA Team
**Last Updated:** October 6, 2025
