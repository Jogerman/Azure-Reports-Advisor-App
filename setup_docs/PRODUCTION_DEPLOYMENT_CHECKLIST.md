# PRODUCTION DEPLOYMENT CHECKLIST
## Azure Advisor Reports Platform

**Version:** 1.0
**Date Created:** October 2, 2025
**Last Updated:** October 2, 2025
**Owner:** DevOps Team

---

## 📋 OVERVIEW

This checklist provides a comprehensive, step-by-step guide for deploying the Azure Advisor Reports Platform to production. Follow all sections in order, marking items as complete only after verification.

### Deployment Strategy
- **Method:** Blue-Green Deployment (Zero Downtime)
- **Automation:** GitHub Actions
- **Monitoring:** Real-time with Application Insights
- **Rollback:** Automated slot swap reversal

### Estimated Timeline
- **Pre-Deployment Preparation:** 2-3 days
- **Infrastructure Deployment:** 4-6 hours
- **Application Deployment:** 2-3 hours
- **Post-Deployment Validation:** 24 hours intensive, 1 week monitoring

---

## 🔧 PRE-DEPLOYMENT PREPARATION

### Week 1: Critical Infrastructure Completion

#### Infrastructure Code Completion (Priority P0)

**networking.bicep Module:**
- [ ] Create `D:\Code\Azure Reports\scripts\azure\bicep\modules\networking.bicep`
- [ ] Implement Azure Front Door Premium configuration
- [ ] Define WAF policy rules (OWASP Top 10, bot protection)
- [ ] Configure custom domain (if applicable)
- [ ] Setup SSL/TLS certificate (App Service Managed or Let's Encrypt)
- [ ] Define CDN caching rules (static assets: 7 days, HTML: 1 hour)
- [ ] Add routing rules (backend: api.*, frontend: www.*)
- [ ] Configure health probe endpoints
- [ ] Add outputs for Front Door hostname and endpoint
- [ ] Test Bicep validation: `az bicep build --file modules/networking.bicep`
- [ ] Estimated Time: 6-8 hours
- [ ] Owner: DevOps Engineer

**Report Templates Verification:**
- [ ] Check if templates exist at `azure_advisor_reports/templates/reports/`
- [ ] Verify `base.html` (common styling, header, footer)
- [ ] Verify `detailed.html` (full recommendation list, grouped by category)
- [ ] Verify `executive.html` (high-level summary, charts, top 10)
- [ ] Verify `cost.html` (cost optimization focus, savings calculations, ROI)
- [ ] Verify `security.html` (security recommendations, risk levels, compliance)
- [ ] Verify `operations.html` (operational excellence, reliability, best practices)
- [ ] If templates missing: Create all 6 templates
- [ ] Implement PDF generation service (`apps/reports/services/pdf_generator.py`)
- [ ] Install WeasyPrint: `pip install weasyprint`
- [ ] Test HTML template rendering with sample data
- [ ] Test PDF generation with sample data
- [ ] Verify PDF quality (formatting, charts, page breaks)
- [ ] Estimated Time: 0-12 hours (if templates missing)
- [ ] Owner: Backend Developer

**Bicep Template Testing:**
- [ ] Deploy to dev environment:
  ```powershell
  az deployment sub create `
    --location eastus2 `
    --template-file scripts/azure/bicep/main.bicep `
    --parameters environment=dev `
      azureAdClientId="dev-client-id" `
      azureAdClientSecret="dev-secret" `
      azureAdTenantId="tenant-id"
  ```
- [ ] Verify all resources created successfully
- [ ] Check resource dependencies and outputs
- [ ] Validate networking configuration
- [ ] Test security (Key Vault, managed identities)
- [ ] Delete dev resources after testing
- [ ] Fix any Bicep deployment issues
- [ ] Estimated Time: 4 hours
- [ ] Owner: DevOps Engineer

#### Azure Configuration (Priority P0)

**Azure AD Application Registration:**
- [ ] Login to Azure Portal: https://portal.azure.com
- [ ] Navigate to Azure Active Directory > App registrations
- [ ] Click "New registration"
- [ ] Name: "Azure Advisor Reports - Production"
- [ ] Supported account types: "Single tenant"
- [ ] Redirect URIs:
  - [ ] Web: `https://<production-domain>/auth/callback`
  - [ ] Web: `https://<production-domain>`
  - [ ] SPA: `https://<production-domain>`
- [ ] Click "Register"
- [ ] Note Application (client) ID: __________________
- [ ] Note Directory (tenant) ID: __________________
- [ ] Navigate to "Certificates & secrets"
- [ ] Click "New client secret"
- [ ] Description: "Production Secret - Oct 2025"
- [ ] Expires: 24 months
- [ ] Click "Add"
- [ ] **IMMEDIATELY** copy secret value: __________________ (will not be shown again)
- [ ] Navigate to "API permissions"
- [ ] Click "Add a permission" > Microsoft Graph
- [ ] Select "Delegated permissions"
- [ ] Add permissions:
  - [ ] User.Read
  - [ ] openid
  - [ ] profile
  - [ ] email
- [ ] Click "Grant admin consent for [tenant]" (if admin)
- [ ] Navigate to "Authentication"
- [ ] Enable "ID tokens" (for MSAL)
- [ ] Set Logout URL: `https://<production-domain>/logout`
- [ ] Save all changes
- [ ] Test authentication with staging environment first
- [ ] Estimated Time: 2 hours
- [ ] Owner: Security Admin / DevOps Engineer

**Azure Resources Creation:**
- [ ] Subscription ID verified: __________________
- [ ] Resource group location decided: East US 2 (or other)
- [ ] Resource naming convention confirmed
- [ ] Service principal created for GitHub Actions:
  ```powershell
  az ad sp create-for-rbac `
    --name "github-actions-azure-advisor-prod" `
    --role contributor `
    --scopes /subscriptions/{subscription-id} `
    --sdk-auth
  ```
- [ ] Note service principal JSON output for AZURE_CREDENTIALS_PROD
- [ ] Verify service principal has Contributor role
- [ ] Estimated Time: 1 hour
- [ ] Owner: DevOps Engineer

**GitHub Secrets Configuration:**
- [ ] Navigate to GitHub repository > Settings > Secrets and variables > Actions
- [ ] Add production secrets:

**Production Secrets (Required):**
- [ ] `AZURE_CREDENTIALS_PROD`:
  ```json
  {
    "clientId": "<service-principal-client-id>",
    "clientSecret": "<service-principal-secret>",
    "subscriptionId": "<azure-subscription-id>",
    "tenantId": "<azure-tenant-id>"
  }
  ```
- [ ] `DJANGO_SECRET_KEY_PROD`:
  ```powershell
  # Generate:
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- [ ] `DATABASE_URL_PROD`: (will be populated after infrastructure deployment)
  ```
  postgresql://<username>:<password>@<server>:5432/<database>
  ```
- [ ] `REDIS_URL_PROD`: (will be populated after infrastructure deployment)
  ```
  rediss://:<password>@<hostname>:6380/0
  ```
- [ ] `AZURE_CLIENT_ID_PROD`: (from Azure AD app registration above)
- [ ] `AZURE_CLIENT_SECRET_PROD`: (from Azure AD app registration above)
- [ ] `AZURE_TENANT_ID`: (from Azure AD app registration above)
- [ ] `AZURE_STORAGE_CONNECTION_STRING_PROD`: (will be populated after infrastructure deployment)
- [ ] `SQL_ADMIN_USER`: (choose strong username, not 'admin' or 'root')
- [ ] `SQL_ADMIN_PASSWORD`: (generate strong 20+ char password)
  ```powershell
  # Generate strong password:
  -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 24 | % {[char]$_})
  ```
- [ ] `BACKUP_STORAGE_KEY`: (will be populated after infrastructure deployment)

**Staging Secrets (Required):**
- [ ] `AZURE_CREDENTIALS_STAGING`
- [ ] `DJANGO_SECRET_KEY_STAGING`
- [ ] `DATABASE_URL_STAGING`
- [ ] `REDIS_URL_STAGING`
- [ ] `AZURE_CLIENT_ID_STAGING`
- [ ] `AZURE_CLIENT_SECRET_STAGING`
- [ ] `AZURE_STORAGE_CONNECTION_STRING_STAGING`

**Optional Secrets:**
- [ ] `SENTRY_DSN_PROD`: (if using Sentry for error tracking)
- [ ] `SENDGRID_API_KEY`: (if using SendGrid for email)
- [ ] `SLACK_WEBHOOK_URL`: (for deployment notifications)

- [ ] Verify all secrets are set (no placeholders)
- [ ] Test secret access in workflow dry-run
- [ ] Document secret rotation schedule (every 6 months)
- [ ] Estimated Time: 3 hours
- [ ] Owner: DevOps Engineer

#### Testing Completion (Priority P0)

**Pytest Configuration Fix:**
- [ ] Open `D:\Code\Azure Reports\azure_advisor_reports\conftest.py`
- [ ] Add pytest_configure hook if not present:
  ```python
  import django
  from django.conf import settings

  def pytest_configure():
      if not settings.configured:
          settings.configure(
              DJANGO_SETTINGS_MODULE='azure_advisor_reports.settings'
          )
          django.setup()
  ```
- [ ] Run test to verify configuration:
  ```powershell
  cd "D:\Code\Azure Reports\azure_advisor_reports"
  python -m pytest apps/reports/tests/test_serializers.py -v
  ```
- [ ] Verify tests run without Django configuration errors
- [ ] Estimated Time: 10 minutes
- [ ] Owner: QA Engineer

**Reports Views Tests Completion:**
- [ ] Create or update `apps/reports/tests/test_views.py`
- [ ] Test CSV upload endpoint (valid file, invalid file, size limits)
- [ ] Test report generation endpoint (all 5 types)
- [ ] Test report status endpoint
- [ ] Test report download endpoint (HTML and PDF)
- [ ] Test report list endpoint (filtering, pagination, search)
- [ ] Test report detail endpoint
- [ ] Test report delete endpoint
- [ ] Test permission-based access (role restrictions)
- [ ] Test error responses (400, 401, 403, 404, 500)
- [ ] Aim for 80%+ views coverage
- [ ] Run tests:
  ```powershell
  python -m pytest apps/reports/tests/test_views.py -v --cov=apps/reports/views
  ```
- [ ] Estimated Time: 4 hours
- [ ] Owner: QA Engineer

**Full Test Suite Execution:**
- [ ] Run all backend tests:
  ```powershell
  cd "D:\Code\Azure Reports\azure_advisor_reports"
  python -m pytest -v --cov=apps --cov-report=html --cov-report=term
  ```
- [ ] Review coverage report:
  ```powershell
  start htmlcov/index.html
  ```
- [ ] Verify coverage meets targets:
  - [ ] Overall: 85%+ (Target achieved: ___%)
  - [ ] Authentication: 90%+ (Actual: ___%)
  - [ ] Clients: 85%+ (Actual: ___%)
  - [ ] Reports: 85%+ (Actual: ___%)
  - [ ] Analytics: 85%+ (Actual: ___%)
- [ ] Fix any failing tests
- [ ] Address critical coverage gaps
- [ ] Generate final coverage report JSON:
  ```powershell
  python -m pytest --cov=apps --cov-report=json
  ```
- [ ] Commit coverage report to repository
- [ ] Estimated Time: 1 hour
- [ ] Owner: QA Engineer

**Integration Testing:**
- [ ] Test complete CSV upload → report generation flow:
  - [ ] Upload valid Azure Advisor CSV
  - [ ] Verify CSV processing completes
  - [ ] Trigger report generation (all 5 types)
  - [ ] Verify reports complete successfully
  - [ ] Download HTML and PDF
  - [ ] Verify report content accuracy
- [ ] Test authentication flow:
  - [ ] Azure AD login (if possible with test account)
  - [ ] JWT token generation
  - [ ] Token refresh
  - [ ] Logout
- [ ] Test error recovery:
  - [ ] Invalid CSV upload
  - [ ] Large file upload (>50MB)
  - [ ] Report generation with corrupted data
  - [ ] Database connection failure (simulate)
  - [ ] Redis connection failure (simulate)
- [ ] Test concurrent operations:
  - [ ] Multiple CSV uploads simultaneously
  - [ ] Multiple report generations simultaneously
- [ ] Document integration test results
- [ ] Estimated Time: 8 hours
- [ ] Owner: QA Engineer + Backend Developer

---

## 🏗️ INFRASTRUCTURE DEPLOYMENT

### Staging Environment Deployment

**Infrastructure Deployment to Staging:**
- [ ] Verify all Bicep modules complete (infrastructure, security, networking)
- [ ] Deploy staging infrastructure:
  ```powershell
  az deployment sub create `
    --location eastus2 `
    --template-file "D:\Code\Azure Reports\scripts\azure\bicep\main.bicep" `
    --parameters environment=staging `
      azureAdClientId=$env:AZURE_CLIENT_ID_STAGING `
      azureAdClientSecret=$env:AZURE_CLIENT_SECRET_STAGING `
      azureAdTenantId=$env:AZURE_TENANT_ID
  ```
- [ ] Monitor deployment progress (expect 15-25 minutes)
- [ ] Verify all resources created:
  - [ ] Resource Group: rg-azure-advisor-staging
  - [ ] PostgreSQL Flexible Server
  - [ ] Redis Cache
  - [ ] Storage Account (with 4 containers)
  - [ ] App Service Plans (backend + frontend)
  - [ ] App Services (backend + frontend)
  - [ ] Application Insights
  - [ ] Log Analytics Workspace
  - [ ] Key Vault
  - [ ] Front Door (if networking module complete)
- [ ] Note resource outputs:
  - [ ] DATABASE_URL: __________________
  - [ ] REDIS_URL: __________________
  - [ ] STORAGE_CONNECTION_STRING: __________________
  - [ ] FRONTEND_URL: __________________
  - [ ] BACKEND_URL: __________________
- [ ] Update GitHub staging secrets with connection strings
- [ ] Estimated Time: 2 hours
- [ ] Owner: DevOps Engineer

**Database Initialization (Staging):**
- [ ] Connect to staging database:
  ```powershell
  az postgres flexible-server connect `
    --name <postgres-server-name> `
    --admin-user <admin-username> `
    --admin-password <admin-password> `
    --database postgres
  ```
- [ ] Create application database:
  ```sql
  CREATE DATABASE azure_advisor_reports_staging;
  ```
- [ ] Verify database connectivity from local machine
- [ ] Test database backups are configured
- [ ] Estimated Time: 30 minutes
- [ ] Owner: DevOps Engineer

**Application Deployment to Staging:**
- [ ] Create deployment tag:
  ```powershell
  cd "D:\Code\Azure Reports"
  git tag -a staging-v1.0 -m "Staging deployment - October 2025"
  git push origin staging-v1.0
  ```
- [ ] Trigger staging deployment workflow:
  - [ ] Navigate to GitHub Actions
  - [ ] Select "Deploy to Staging" workflow
  - [ ] Click "Run workflow"
  - [ ] Select branch: main
  - [ ] Click "Run workflow"
- [ ] Monitor deployment progress (expect 10-15 minutes):
  - [ ] Backend tests pass
  - [ ] Frontend tests pass
  - [ ] Docker images built
  - [ ] Backend deployed
  - [ ] Frontend deployed
  - [ ] Health checks pass
- [ ] Deployment completes successfully
- [ ] Verify deployment logs for errors
- [ ] Estimated Time: 1 hour
- [ ] Owner: DevOps Engineer

**Database Migration (Staging):**
- [ ] SSH into staging backend app service:
  ```powershell
  az webapp ssh --name <backend-app-name> --resource-group rg-azure-advisor-staging
  ```
- [ ] Navigate to application directory:
  ```bash
  cd /home/site/wwwroot
  ```
- [ ] Run migrations:
  ```bash
  python manage.py migrate --no-input
  ```
- [ ] Verify migrations applied successfully
- [ ] Create superuser:
  ```bash
  python manage.py createsuperuser
  ```
- [ ] Test admin access: `https://<backend-url>/admin`
- [ ] Estimated Time: 30 minutes
- [ ] Owner: Backend Developer

**Staging Smoke Tests:**
- [ ] **Authentication:**
  - [ ] Navigate to staging frontend URL
  - [ ] Click "Sign in with Microsoft"
  - [ ] Verify Azure AD login works
  - [ ] Verify dashboard loads
  - [ ] Verify user profile shown
  - [ ] Logout works
- [ ] **Client Management:**
  - [ ] Create new client via UI
  - [ ] Edit client details
  - [ ] View client detail page
  - [ ] Delete client
- [ ] **CSV Upload:**
  - [ ] Upload sample Azure Advisor CSV
  - [ ] Verify file upload success
  - [ ] Check CSV processing status
- [ ] **Report Generation:**
  - [ ] Trigger report generation (detailed type)
  - [ ] Monitor processing status
  - [ ] Verify report completes
  - [ ] Download HTML report
  - [ ] Download PDF report
  - [ ] Verify report content
- [ ] **Dashboard:**
  - [ ] Verify metrics load correctly
  - [ ] Verify charts render
  - [ ] Verify recent activity shows
  - [ ] Test time range selector (7/30/90 days)
- [ ] **API Health Check:**
  - [ ] Test: `https://<backend-url>/api/health/`
  - [ ] Verify JSON response with database and Redis status
- [ ] Document any issues found
- [ ] Fix critical issues before proceeding
- [ ] Estimated Time: 2 hours
- [ ] Owner: QA Engineer + Full Team

### Production Environment Deployment

**Infrastructure Deployment to Production:**
- [ ] **Pre-deployment backup** (if upgrading existing production):
  - [ ] Backup production database (if exists)
  - [ ] Backup critical configuration files
  - [ ] Document current state
- [ ] **Final verification checklist:**
  - [ ] All staging tests passed
  - [ ] Stakeholder sign-off received
  - [ ] Team on standby for deployment
  - [ ] Rollback plan reviewed and ready
- [ ] Deploy production infrastructure:
  ```powershell
  az deployment sub create `
    --location eastus2 `
    --template-file "D:\Code\Azure Reports\scripts\azure\bicep\main.bicep" `
    --parameters environment=prod `
      azureAdClientId=$env:AZURE_CLIENT_ID_PROD `
      azureAdClientSecret=$env:AZURE_CLIENT_SECRET_PROD `
      azureAdTenantId=$env:AZURE_TENANT_ID
  ```
- [ ] Monitor deployment (expect 20-30 minutes for production tier)
- [ ] Verify all resources created:
  - [ ] Resource Group: rg-azure-advisor-prod
  - [ ] PostgreSQL Flexible Server (GeneralPurpose_D4s_v3, zone-redundant)
  - [ ] Redis Cache (Premium P1)
  - [ ] Storage Account
  - [ ] App Service Plans (P2v3 backend, P1v3 frontend)
  - [ ] App Services (both with staging slots)
  - [ ] Application Insights
  - [ ] Log Analytics Workspace
  - [ ] Key Vault (Premium tier)
  - [ ] Front Door Premium with WAF
- [ ] Note production outputs:
  - [ ] DATABASE_URL_PROD: __________________
  - [ ] REDIS_URL_PROD: __________________
  - [ ] STORAGE_CONNECTION_STRING_PROD: __________________
  - [ ] FRONTEND_URL: __________________
  - [ ] BACKEND_URL: __________________
  - [ ] FRONT_DOOR_URL: __________________
- [ ] Update GitHub production secrets
- [ ] Verify resource tags are correct (environment, project, cost-center)
- [ ] Estimated Time: 3 hours
- [ ] Owner: DevOps Engineer

**Database Initialization (Production):**
- [ ] Connect to production database
- [ ] Create application database: `azure_advisor_reports_prod`
- [ ] Verify SSL/TLS connection
- [ ] Test database connectivity
- [ ] Configure automated backups:
  - [ ] Backup retention: 14 days
  - [ ] Geo-redundant backup: Enabled
  - [ ] Point-in-time restore: Enabled
- [ ] Test backup restoration (on separate test database)
- [ ] Document backup restoration procedure
- [ ] Estimated Time: 1 hour
- [ ] Owner: DevOps Engineer

**Application Deployment to Production (Blue-Green Strategy):**
- [ ] **Phase 1: Deploy to Staging Slot**
  - [ ] Create production deployment tag:
    ```powershell
    git tag -a prod-v1.0.0 -m "Production release 1.0.0 - October 2025"
    git push origin prod-v1.0.0
    ```
  - [ ] Trigger production deployment workflow:
    - [ ] GitHub Actions > "Deploy to Production"
    - [ ] Select tag: prod-v1.0.0
    - [ ] Workflow creates deployment to staging slot first
  - [ ] Monitor staging slot deployment
  - [ ] Verify deployment to staging slot successful

- [ ] **Phase 2: Database Migration on Production**
  - [ ] SSH into production backend staging slot
  - [ ] Run migrations:
    ```bash
    python manage.py migrate --no-input
    ```
  - [ ] Verify migrations successful
  - [ ] Create superuser for production
  - [ ] Test admin access

- [ ] **Phase 3: Staging Slot Smoke Tests**
  - [ ] Test staging slot URL: `https://<app-name>-staging.azurewebsites.net`
  - [ ] Run all smoke tests (authentication, clients, upload, reports, dashboard)
  - [ ] Verify performance (response times <2 seconds)
  - [ ] Check error logs (should be minimal)
  - [ ] Load test staging slot (optional but recommended)
  - [ ] Get team sign-off for slot swap

- [ ] **Phase 4: Blue-Green Slot Swap**
  - [ ] Initiate slot swap via GitHub Actions workflow
  - [ ] Monitor slot swap progress (expect 2-5 minutes)
  - [ ] Verify swap completed successfully
  - [ ] Verify production slot now serves new version

- [ ] **Phase 5: Post-Swap Verification**
  - [ ] Test production URL immediately
  - [ ] Run critical smoke tests:
    - [ ] Health check: /api/health/
    - [ ] Authentication flow
    - [ ] Dashboard loads
    - [ ] API endpoints respond
  - [ ] Monitor Application Insights for errors
  - [ ] Monitor response times
  - [ ] Monitor resource utilization (CPU, memory, database connections)
  - [ ] Check error rate (<1%)

- [ ] **Deployment Complete**
  - [ ] Announce deployment success to team
  - [ ] Update status page (if applicable)
  - [ ] Document deployment timestamp
  - [ ] Begin 24-hour intensive monitoring

- [ ] Estimated Time: 2-3 hours
- [ ] Owner: DevOps Engineer + Team on Standby

---

## 🔍 POST-DEPLOYMENT VALIDATION

### Immediate Verification (First Hour)

**Health Checks:**
- [ ] Backend health endpoint responds: `https://<backend-url>/api/health/`
- [ ] Frontend loads correctly: `https://<frontend-url>`
- [ ] API endpoints respond:
  - [ ] GET /api/clients/
  - [ ] GET /api/reports/
  - [ ] GET /api/analytics/dashboard/
- [ ] Database connectivity confirmed
- [ ] Redis connectivity confirmed
- [ ] Blob storage accessible
- [ ] Application Insights receiving telemetry

**Functional Tests:**
- [ ] **User Authentication:**
  - [ ] Login with Azure AD works
  - [ ] Token generation successful
  - [ ] User profile loads
  - [ ] RBAC permissions enforced
  - [ ] Logout works
- [ ] **Client Management:**
  - [ ] Create client works
  - [ ] List clients works
  - [ ] View client detail works
  - [ ] Edit client works
  - [ ] Delete client works (test with test data only)
- [ ] **CSV Upload:**
  - [ ] Upload CSV works
  - [ ] File validation works (reject invalid files)
  - [ ] File stored in blob storage
  - [ ] Processing status tracked
- [ ] **Report Generation:**
  - [ ] Generate detailed report works
  - [ ] Generate executive report works
  - [ ] Generate cost report works
  - [ ] Report status updates correctly
  - [ ] HTML download works
  - [ ] PDF download works
  - [ ] Report content is accurate
- [ ] **Dashboard:**
  - [ ] Metrics load correctly
  - [ ] Charts render
  - [ ] Trends work (7/30/90 days)
  - [ ] Recent activity shows
  - [ ] Refresh button works

**Performance Verification:**
- [ ] Page load times <3 seconds (first load)
- [ ] Page load times <1 second (cached)
- [ ] API response times <500ms (simple queries)
- [ ] API response times <2 seconds (complex queries)
- [ ] Report generation <60 seconds (target <45 seconds)
- [ ] Dashboard loads <2 seconds

**Security Verification:**
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] Security headers present:
  - [ ] Strict-Transport-Security
  - [ ] X-Frame-Options
  - [ ] X-Content-Type-Options
  - [ ] Content-Security-Policy
- [ ] Authentication required for protected routes
- [ ] RBAC enforced (test with different roles)
- [ ] No sensitive data in error messages
- [ ] CORS configured correctly

**Error Monitoring:**
- [ ] Application Insights dashboard shows data
- [ ] Error rate <1%
- [ ] No critical errors in logs
- [ ] Exceptions tracked and categorized
- [ ] Failed requests tracked

### First 24 Hours Monitoring

**Continuous Monitoring Tasks:**
- [ ] Monitor Application Insights Live Metrics:
  - [ ] Request rate
  - [ ] Response time
  - [ ] Failed requests
  - [ ] Server exceptions
- [ ] Monitor resource utilization:
  - [ ] App Service CPU (<50% average)
  - [ ] App Service Memory (<70%)
  - [ ] PostgreSQL connections (<80% of max)
  - [ ] PostgreSQL CPU (<60%)
  - [ ] Redis memory (<80%)
- [ ] Monitor error logs:
  - [ ] Check for recurring errors
  - [ ] Investigate any 500 errors
  - [ ] Review warning messages
- [ ] Monitor performance:
  - [ ] P95 response time <2 seconds
  - [ ] P99 response time <5 seconds
  - [ ] Dashboard load time <2 seconds
- [ ] Monitor business metrics:
  - [ ] Number of reports generated
  - [ ] CSV uploads successful
  - [ ] User logins successful

**Alerting Verification:**
- [ ] Test critical alerts:
  - [ ] Simulate high response time (if possible)
  - [ ] Verify alert triggers
  - [ ] Verify notification delivery (email, Slack, etc.)
- [ ] Verify alert rules active:
  - [ ] Response time >5 seconds (Critical)
  - [ ] Error rate >10% (Critical)
  - [ ] CPU >80% (High)
  - [ ] Memory >85% (High)
  - [ ] Failed deployment (Critical)
- [ ] Document alert response procedures

**Issue Resolution:**
- [ ] Log any issues discovered
- [ ] Triage by severity (P0, P1, P2)
- [ ] Fix critical issues immediately
- [ ] Schedule fixes for high-priority issues (within 24 hours)
- [ ] Document workarounds for known issues

### First Week Validation

**Daily Checks:**
- [ ] **Day 2:**
  - [ ] Review previous 24 hours metrics
  - [ ] Check for any overnight errors
  - [ ] Verify backups completed successfully
  - [ ] Test report generation with real customer data (if available)
  - [ ] Monitor user adoption (login count)

- [ ] **Day 3:**
  - [ ] Performance trending review
  - [ ] Cost monitoring review (actual vs. estimated)
  - [ ] User feedback collection (if users onboarded)
  - [ ] Security scan (optional: run OWASP ZAP)

- [ ] **Day 4:**
  - [ ] Database performance review
  - [ ] Query optimization if needed
  - [ ] Cache hit rate review (Redis)
  - [ ] Blob storage usage review

- [ ] **Day 5:**
  - [ ] Weekly metrics summary
  - [ ] Stakeholder report (uptime, performance, usage)
  - [ ] Team retrospective (what went well, what to improve)
  - [ ] Plan next week improvements

**Comprehensive Testing:**
- [ ] **Load Testing (Optional but Recommended):**
  - [ ] Setup load testing tool (Azure Load Testing, k6, or Locust)
  - [ ] Simulate 50 concurrent users
  - [ ] Simulate 100 concurrent users (target capacity)
  - [ ] Monitor response times under load
  - [ ] Verify auto-scaling triggers correctly
  - [ ] Document load test results

- [ ] **User Acceptance Testing:**
  - [ ] Invite beta users (3-5 initial users)
  - [ ] Provide training/onboarding
  - [ ] Collect feedback via survey
  - [ ] Log feature requests
  - [ ] Address critical usability issues

- [ ] **Documentation Validation:**
  - [ ] User manual accurate (test all steps)
  - [ ] API documentation matches implementation
  - [ ] Deployment runbook tested
  - [ ] Troubleshooting guide helpful

### First Month Optimization

**Performance Optimization:**
- [ ] Review slow API endpoints (>2 seconds)
- [ ] Optimize database queries (use EXPLAIN ANALYZE)
- [ ] Implement additional caching where beneficial
- [ ] Frontend bundle size optimization
- [ ] Image optimization
- [ ] Implement code splitting (lazy loading)

**Cost Optimization:**
- [ ] Review actual resource usage vs. provisioned
- [ ] Identify underutilized resources
- [ ] Evaluate tier downgrades for dev/staging
- [ ] Purchase reserved instances (30-40% savings)
- [ ] Configure auto-shutdown for dev environment
- [ ] Implement storage lifecycle policies (cool tier for old reports)
- [ ] Set up cost alerts and budgets

**Feature Enhancements (Based on Feedback):**
- [ ] Collect user feedback
- [ ] Prioritize feature requests
- [ ] Plan sprint for top 3-5 enhancements
- [ ] Update product roadmap

**Security Review:**
- [ ] Review access logs for suspicious activity
- [ ] Verify no unauthorized access attempts
- [ ] Test backup restoration procedure
- [ ] Review and rotate secrets (if needed)
- [ ] Security audit (internal or external)
- [ ] Penetration testing (if budget allows)

---

## 🚨 ROLLBACK PROCEDURES

### When to Rollback

**Immediate Rollback (P0 Issues):**
- Application not loading (500 errors, blank pages)
- Authentication completely broken
- Data corruption or data loss
- Security breach or vulnerability exploited
- Critical functionality not working (reports not generating)
- Error rate >20%
- Performance degradation >50% (response times)

**Scheduled Rollback (P1 Issues):**
- Non-critical features broken
- Error rate 10-20%
- Performance degradation 25-50%
- Multiple P2 issues impacting user experience
- Stakeholder decision to revert

### Rollback Execution

**Blue-Green Slot Swap Reversal:**
- [ ] Navigate to Azure Portal
- [ ] Go to App Service (backend)
- [ ] Select "Deployment slots"
- [ ] Click "Swap"
- [ ] Swap production <-> staging slots
- [ ] Monitor swap progress (2-5 minutes)
- [ ] Verify rollback successful
- [ ] Repeat for frontend App Service

**Database Rollback (If Needed):**
- [ ] **Option 1: Point-in-Time Restore**
  - [ ] Navigate to PostgreSQL server > Backup and restore
  - [ ] Select restore point (timestamp before deployment)
  - [ ] Restore to new server (don't overwrite production)
  - [ ] Test restored database
  - [ ] Update connection string to restored database
  - [ ] Verify application works with restored database

- [ ] **Option 2: Migration Reversal**
  - [ ] SSH into backend app service
  - [ ] Run migration reversal:
    ```bash
    python manage.py migrate <app_name> <previous_migration_number>
    ```
  - [ ] Verify database schema reverted

**Post-Rollback Verification:**
- [ ] Application functional
- [ ] All smoke tests pass
- [ ] Error rate back to normal
- [ ] Performance restored
- [ ] Users can access system
- [ ] Communicate rollback to stakeholders

**Incident Documentation:**
- [ ] Log incident details (what went wrong, when, impact)
- [ ] Document rollback actions taken
- [ ] Root cause analysis (RCA)
- [ ] Create post-mortem document
- [ ] Plan fixes to prevent recurrence
- [ ] Schedule re-deployment after fixes

---

## 📊 SUCCESS CRITERIA

### Deployment Success Metrics

**Infrastructure:**
- [ ] All resources deployed successfully (0 errors)
- [ ] Infrastructure deployment time <30 minutes
- [ ] All health checks passing
- [ ] Monitoring active and receiving data

**Application:**
- [ ] Zero-downtime deployment achieved
- [ ] All smoke tests passing (100%)
- [ ] Error rate <1%
- [ ] Response times <2 seconds (P95)
- [ ] Report generation <45 seconds (P95)

**Security:**
- [ ] All secrets in Key Vault
- [ ] HTTPS enforced
- [ ] WAF active with OWASP rule set
- [ ] Security headers present
- [ ] Authentication working
- [ ] RBAC enforced

**Performance:**
- [ ] Page load <3 seconds (first load)
- [ ] API response <500ms (simple queries)
- [ ] API response <2 seconds (complex queries)
- [ ] Auto-scaling configured and tested

**Monitoring:**
- [ ] All dashboards created and accessible
- [ ] Alert rules configured and tested
- [ ] Logs centralized in Log Analytics
- [ ] On-call rotation established

### Business Success Metrics (First Month)

- [ ] 10+ active clients onboarded
- [ ] 100+ reports generated successfully
- [ ] User satisfaction >4/5 (survey)
- [ ] 99.9% uptime achieved
- [ ] <3 production incidents
- [ ] Average report generation <45 seconds
- [ ] <2% error rate

---

## 📝 COMMUNICATION PLAN

### Pre-Deployment Communication

**Internal Team:**
- [ ] Send deployment schedule 1 week in advance
- [ ] Hold deployment readiness meeting
- [ ] Confirm team availability during deployment window
- [ ] Share deployment runbook with team
- [ ] Assign roles and responsibilities

**Stakeholders:**
- [ ] Notify stakeholders of deployment date
- [ ] Share expected downtime (if any - should be zero)
- [ ] Provide status page link (if applicable)

**Beta Users (If Applicable):**
- [ ] Send notification of upcoming launch
- [ ] Share user guide/documentation
- [ ] Schedule onboarding sessions
- [ ] Provide support contact information

### During Deployment Communication

**Team Communication:**
- [ ] Use dedicated Slack channel or Teams channel
- [ ] Real-time updates every 30 minutes
- [ ] Immediate notification of any issues
- [ ] Clear go/no-go decisions

**Stakeholder Updates:**
- [ ] Send update when deployment starts
- [ ] Send update when deployment completes
- [ ] Send update if any issues encountered

### Post-Deployment Communication

**Success Announcement:**
- [ ] Send deployment success email to team
- [ ] Send launch announcement to stakeholders
- [ ] Share public announcement (if applicable)
- [ ] Update status page to "Operational"

**Daily Updates (First Week):**
- [ ] Send daily summary email:
  - Uptime %
  - Error rate
  - Performance metrics
  - User count
  - Issues encountered and resolved

**Weekly Report (First Month):**
- [ ] Send weekly summary:
  - Metrics dashboard summary
  - User adoption progress
  - Feature usage statistics
  - Issues and resolutions
  - Next week plan

---

## ✅ FINAL SIGN-OFF

### Pre-Deployment Sign-Off

**Technical Lead:**
- [ ] Name: __________________
- [ ] Date: __________________
- [ ] Signature: __________________
- [ ] Notes: __________________

**DevOps Engineer:**
- [ ] Name: __________________
- [ ] Date: __________________
- [ ] Signature: __________________
- [ ] Notes: __________________

**QA Lead:**
- [ ] Name: __________________
- [ ] Date: __________________
- [ ] Signature: __________________
- [ ] Notes: __________________

**Product Manager:**
- [ ] Name: __________________
- [ ] Date: __________________
- [ ] Signature: __________________
- [ ] Notes: __________________

### Post-Deployment Sign-Off

**Deployment Successful:**
- [ ] Date/Time Deployed: __________________
- [ ] Deployment Tag: __________________
- [ ] Deployed By: __________________

**24-Hour Validation Complete:**
- [ ] All smoke tests passed
- [ ] Error rate <1%
- [ ] Performance metrics met
- [ ] No critical issues
- [ ] Validated By: __________________
- [ ] Date: __________________

**Production Launch Approved:**
- [ ] Approved By: __________________
- [ ] Title: __________________
- [ ] Date: __________________

---

## 📞 SUPPORT CONTACTS

### On-Call Rotation

**Week 1 (Deployment Week):**
- [ ] Primary: __________________
- [ ] Secondary: __________________
- [ ] Escalation: __________________

**Week 2:**
- [ ] Primary: __________________
- [ ] Secondary: __________________

### Emergency Contacts

**DevOps Team:**
- [ ] Lead: __________________ (Phone: ______________)
- [ ] Engineer 1: __________________ (Phone: ______________)
- [ ] Engineer 2: __________________ (Phone: ______________)

**Development Team:**
- [ ] Backend Lead: __________________ (Phone: ______________)
- [ ] Frontend Lead: __________________ (Phone: ______________)

**Management:**
- [ ] Product Manager: __________________ (Phone: ______________)
- [ ] Technical Director: __________________ (Phone: ______________)

**Azure Support:**
- [ ] Support Plan: __________________ (Professional/Premier)
- [ ] Support Phone: __________________
- [ ] Support Portal: https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade

---

## 📚 APPENDIX

### A. Useful Commands

**Azure CLI:**
```powershell
# Login
az login

# Set subscription
az account set --subscription "<subscription-id>"

# Deploy Bicep
az deployment sub create --location eastus2 --template-file main.bicep --parameters environment=prod

# SSH to App Service
az webapp ssh --name <app-name> --resource-group <rg-name>

# View logs
az webapp log tail --name <app-name> --resource-group <rg-name>

# Restart App Service
az webapp restart --name <app-name> --resource-group <rg-name>

# Swap slots
az webapp deployment slot swap --name <app-name> --resource-group <rg-name> --slot staging --target-slot production
```

**Database:**
```powershell
# Connect to PostgreSQL
az postgres flexible-server connect --name <server-name> --admin-user <username> --admin-password <password>

# Backup database
az postgres flexible-server backup create --name <server-name> --resource-group <rg-name>

# Restore database
az postgres flexible-server restore --source-server <server-name> --resource-group <rg-name> --name <new-server-name> --restore-time "2025-10-02T10:00:00Z"
```

**Application:**
```bash
# SSH into App Service backend
cd /home/site/wwwroot

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --no-input

# Django shell
python manage.py shell
```

### B. Troubleshooting Common Issues

**Issue: Application not starting**
- Check App Service logs: `az webapp log tail`
- Verify environment variables configured
- Check startup command correct
- Verify Docker image pulled successfully

**Issue: Database connection fails**
- Verify DATABASE_URL correct
- Check firewall rules allow App Service IP
- Test connection from local machine
- Verify SSL/TLS settings

**Issue: Azure AD authentication fails**
- Verify redirect URIs match exactly
- Check client ID and secret correct
- Verify tenant ID correct
- Check API permissions granted
- Review MSAL configuration

**Issue: Reports not generating**
- Check Celery worker running
- Verify Redis connection
- Check blob storage connection
- Review task logs in Application Insights
- Verify templates exist

**Issue: Performance slow**
- Check database query performance
- Review Application Insights performance dashboard
- Verify cache hit rate (Redis)
- Check resource utilization (CPU, memory)
- Consider scaling up or out

### C. Monitoring Dashboards

**Application Overview:**
- Request rate
- Response time (average, P95, P99)
- Failed requests
- Server exceptions
- Dependency calls

**Performance:**
- API endpoint response times
- Database query duration
- Cache hit rate
- Report generation duration

**Business Metrics:**
- Reports generated (hourly, daily)
- Active users
- CSV uploads
- Client count

**Infrastructure:**
- CPU utilization
- Memory utilization
- Database connections
- Redis operations
- Storage usage

### D. Deployment Runbook Links

- **CLAUDE.md:** Project architecture and conventions
- **PLANNING.md:** Technical planning and architecture
- **DEPLOYMENT_READINESS_REPORT.md:** Infrastructure assessment
- **FINAL_PROJECT_STATUS_REPORT.md:** Overall project status

---

**Checklist Version:** 1.0
**Last Updated:** October 2, 2025
**Maintained By:** DevOps Team
**Review Frequency:** After each deployment

---

**END OF PRODUCTION DEPLOYMENT CHECKLIST**

*Print this checklist and mark items physically during deployment for accountability*
