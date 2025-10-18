# PRE-DEPLOYMENT CHECKLIST
## Azure Advisor Reports Platform

**Environment:** ___ Development ___ Staging ___ Production
**Date:** ________________
**Deployed By:** ________________
**Deployment Name:** ________________

---

## PHASE 1: PREREQUISITES VALIDATION

### Azure Subscription Setup
- [ ] Active Azure subscription confirmed
- [ ] Contributor role at subscription level verified
- [ ] Subscription ID documented: _______________________
- [ ] Resource providers registered (automatic during deployment)

### Azure AD Configuration
- [ ] **Azure AD App Registration created**
  - [ ] Application (client) ID: _______________________
  - [ ] Directory (tenant) ID: _______________________
  - [ ] Client secret created (expiry date: _________)
  - [ ] Redirect URIs configured:
    - [ ] `https://localhost:3000` (development)
    - [ ] `https://azure-advisor-frontend-staging.azurewebsites.net` (staging)
    - [ ] `https://azure-advisor-frontend.azurewebsites.net` (production)
  - [ ] API permissions granted:
    - [ ] Microsoft Graph → User.Read (Delegated)
    - [ ] Admin consent granted

- [ ] **Service Principal for GitHub Actions**
  - [ ] Service principal created
  - [ ] Contributor role assigned at subscription level
  - [ ] User Access Administrator role assigned (for RBAC)
  - [ ] JSON credentials saved securely
  - [ ] Service principal name: _______________________

### Local Environment
- [ ] Azure CLI installed (version 2.40+)
  - Version: _______________________
- [ ] Bicep CLI installed
  - Version: _______________________
- [ ] PowerShell 7.x installed
  - Version: _______________________
- [ ] Git installed
  - Version: _______________________
- [ ] Logged into Azure CLI: `az login`
  - Logged in as: _______________________
  - Subscription: _______________________

### Parameter Files
- [ ] Parameter file updated: `scripts/azure/bicep/parameters.{environment}.json`
- [ ] Azure AD Client ID updated (not placeholder)
- [ ] Azure AD Tenant ID updated (not placeholder)
- [ ] Azure AD Client Secret updated (not placeholder)
- [ ] Custom domain configured (if applicable): _______________________
- [ ] All parameters validated

---

## PHASE 2: DEPLOYMENT VALIDATION

### Bicep Template Validation
- [ ] Navigate to: `D:\Code\Azure Reports\scripts\azure\bicep`
- [ ] Run: `az bicep build --file main.bicep`
- [ ] Compilation successful (no errors)
- [ ] Warnings reviewed and acceptable (9 expected)
- [ ] All module files present:
  - [ ] `modules/infrastructure.bicep`
  - [ ] `modules/security.bicep`
  - [ ] `modules/networking.bicep`

### Deployment Script Validation
- [ ] Navigate to: `D:\Code\Azure Reports\scripts\azure`
- [ ] Deployment script exists: `deploy.ps1`
- [ ] Script syntax validated (no errors)
- [ ] Environment parameter set: ___ dev ___ staging ___ prod
- [ ] Location parameter confirmed: _______________________

### What-If Analysis
- [ ] Run What-If analysis:
  ```powershell
  .\deploy.ps1 -Environment {env} -WhatIf
  ```
- [ ] Resource changes reviewed
- [ ] No unexpected deletions
- [ ] Resource count expected: ~28 resources (with Front Door)
- [ ] Estimated cost reviewed: $______/month
- [ ] What-If output saved to: _______________________

---

## PHASE 3: DEPLOYMENT EXECUTION

### Pre-Deployment Backup (Staging/Production Only)
- [ ] N/A for first deployment
- [ ] Database backup created (if existing)
- [ ] Configuration backup created
- [ ] Backup location: _______________________

### Resource Group
- [ ] Resource group name: rg-azure-advisor-{environment}
- [ ] Location: eastus2 (or specified location)
- [ ] Tags configured:
  - [ ] Environment: {environment}
  - [ ] Project: AzureAdvisorReports
  - [ ] ManagedBy: Bicep

### Execute Deployment
- [ ] Run deployment command:
  ```powershell
  cd D:\Code\Azure Reports\scripts\azure
  .\deploy.ps1 -Environment {environment}
  ```
- [ ] Pre-deployment validation passed
- [ ] Bicep validation passed
- [ ] Parameters collected/loaded
- [ ] Deployment confirmation accepted
- [ ] Deployment started
  - Start time: _______________________
  - Deployment name: _______________________

### Monitor Deployment
- [ ] Deployment in progress (watch console output)
- [ ] No errors reported
- [ ] Resource provisioning successful
- [ ] Deployment completed successfully
  - End time: _______________________
  - Duration: _______________________
- [ ] Deployment outputs retrieved
- [ ] Outputs saved to: `scripts/azure/outputs/`

---

## PHASE 4: POST-DEPLOYMENT VERIFICATION

### Resource Verification
- [ ] Resource group created: `rg-azure-advisor-{environment}`
- [ ] Resource count: ___ (expected ~28)
- [ ] All resources in "Succeeded" state
- [ ] No failed deployments

**Core Resources:**
- [ ] App Service Plan (Backend): _______________________
- [ ] App Service Plan (Frontend): _______________________
- [ ] App Service (Backend): _______________________
- [ ] App Service (Frontend): _______________________
- [ ] PostgreSQL Flexible Server: _______________________
- [ ] Azure Cache for Redis: _______________________
- [ ] Storage Account: _______________________
- [ ] Application Insights: _______________________
- [ ] Log Analytics Workspace: _______________________
- [ ] Key Vault: _______________________
- [ ] Azure Front Door (if enabled): _______________________
- [ ] WAF Policy (if Front Door enabled): _______________________

### Key Vault Configuration
- [ ] Key Vault accessible
- [ ] 7 secrets created (with placeholders)
- [ ] Update secrets with actual values:
  - [ ] `DATABASE-URL`: Updated
  - [ ] `REDIS-URL`: Updated
  - [ ] `AZURE-STORAGE-CONNECTION-STRING`: Updated
  - [ ] `AZURE-AD-CLIENT-ID`: Updated
  - [ ] `AZURE-AD-CLIENT-SECRET`: Updated
  - [ ] `AZURE-AD-TENANT-ID`: Updated
  - [ ] `DJANGO-SECRET-KEY`: Generated and set
- [ ] Managed Identity RBAC verified:
  - [ ] Backend App Service has "Key Vault Secrets User" role
  - [ ] Frontend App Service has "Key Vault Secrets User" role

### Database Setup
- [ ] PostgreSQL server accessible
- [ ] Database created: `azure_advisor_reports`
- [ ] SSL connection enforced
- [ ] Firewall rules configured (if needed)
- [ ] Connection string tested
- [ ] Admin credentials saved securely

### Storage Account
- [ ] Storage account accessible
- [ ] Blob containers created:
  - [ ] `csv-uploads`
  - [ ] `reports-html`
  - [ ] `reports-pdf`
  - [ ] `static-assets`
- [ ] CORS configured for frontend URL
- [ ] Connection string saved

### Redis Cache
- [ ] Redis cache accessible
- [ ] Connection string saved
- [ ] SSL/TLS enabled
- [ ] Persistence enabled (Premium tier only)

### App Services
- [ ] Backend App Service URL: _______________________
- [ ] Frontend App Service URL: _______________________
- [ ] HTTPS-only enforced
- [ ] Always On enabled
- [ ] Python 3.11 runtime (backend)
- [ ] Node 18 LTS runtime (frontend)

### Networking (if Front Door enabled)
- [ ] Front Door endpoint: _______________________
- [ ] WAF enabled and in Prevention mode (staging/prod)
- [ ] Origins configured (backend + frontend)
- [ ] Routes configured (api + default)
- [ ] Health probes active
- [ ] SSL certificate auto-managed

---

## PHASE 5: APPLICATION CONFIGURATION

### Backend App Service Configuration
- [ ] Navigate to: Azure Portal → App Service (Backend)
- [ ] Configuration → Application settings:
  - [ ] `DATABASE_URL`: Set (from Key Vault reference)
  - [ ] `REDIS_URL`: Set (from Key Vault reference)
  - [ ] `AZURE_STORAGE_CONNECTION_STRING`: Set
  - [ ] `APPLICATIONINSIGHTS_CONNECTION_STRING`: Set
  - [ ] `AZURE_CLIENT_ID`: Set
  - [ ] `AZURE_CLIENT_SECRET`: Set
  - [ ] `AZURE_TENANT_ID`: Set
  - [ ] `SECRET_KEY`: Set (from Key Vault)
  - [ ] `DEBUG`: Set to `False`
  - [ ] `ALLOWED_HOSTS`: Set to backend URL
  - [ ] `CORS_ALLOWED_ORIGINS`: Set to frontend URL
- [ ] General settings:
  - [ ] `PYTHON_VERSION`: 3.11
  - [ ] `SCM_DO_BUILD_DURING_DEPLOYMENT`: true
- [ ] Configuration saved and restarted

### Frontend App Service Configuration
- [ ] Navigate to: Azure Portal → App Service (Frontend)
- [ ] Configuration → Application settings:
  - [ ] `REACT_APP_API_URL`: Set to backend URL
  - [ ] `REACT_APP_AZURE_CLIENT_ID`: Set
  - [ ] `REACT_APP_AZURE_TENANT_ID`: Set
  - [ ] `REACT_APP_AZURE_REDIRECT_URI`: Set to frontend URL
- [ ] General settings:
  - [ ] `NODE_VERSION`: 18
- [ ] Configuration saved and restarted

### Environment File Generation
- [ ] Environment file created: `scripts/azure/outputs/.env.{environment}`
- [ ] File contains all connection strings
- [ ] File secured (not committed to Git)
- [ ] Azure AD credentials added manually
- [ ] Django SECRET_KEY generated and added

---

## PHASE 6: APPLICATION DEPLOYMENT

### Backend Deployment
- [ ] Code deployed to App Service (via GitHub Actions or manual)
- [ ] Deployment method: ___ GitHub Actions ___ Manual ___ Azure DevOps
- [ ] Deployment successful
- [ ] Application logs reviewed (no errors)

### Database Migrations
- [ ] Connect to backend App Service:
  ```powershell
  az webapp ssh --resource-group rg-azure-advisor-{env} `
    --name azure-advisor-backend-{env}
  ```
- [ ] Run migrations:
  ```bash
  python manage.py migrate
  ```
- [ ] Migrations completed successfully
- [ ] No errors reported

### Create Superuser
- [ ] Create Django superuser:
  ```bash
  python manage.py createsuperuser
  ```
- [ ] Username: _______________________
- [ ] Email: _______________________
- [ ] Password: (saved securely)

### Static Files
- [ ] Collect static files:
  ```bash
  python manage.py collectstatic --no-input
  ```
- [ ] Static files uploaded to storage account
- [ ] Static files accessible

### Frontend Deployment
- [ ] Code deployed to App Service (via GitHub Actions or manual)
- [ ] Build process completed
- [ ] Frontend accessible

---

## PHASE 7: SMOKE TESTING

### Backend Health Checks
- [ ] Navigate to: `{backend-url}/api/health/`
- [ ] Health check returns 200 OK
- [ ] Response includes:
  - [ ] Database status: healthy
  - [ ] Redis status: healthy
  - [ ] Storage status: healthy
  - [ ] Overall status: healthy

### Frontend Access
- [ ] Navigate to: `{frontend-url}`
- [ ] Frontend loads successfully
- [ ] No console errors
- [ ] Login page displayed

### Authentication Flow
- [ ] Click "Sign in with Microsoft"
- [ ] Redirected to Azure AD login
- [ ] Login with test account
- [ ] Redirected back to application
- [ ] User authenticated successfully
- [ ] User profile displayed

### API Connectivity
- [ ] Backend API accessible from frontend
- [ ] CORS working correctly
- [ ] API responses received
- [ ] No authentication errors

### Database Connectivity
- [ ] Database connection successful
- [ ] Queries executing properly
- [ ] No connection errors

### Storage Connectivity
- [ ] Storage account accessible
- [ ] File upload working (if tested)
- [ ] Blob containers accessible

### Redis Connectivity
- [ ] Redis connection successful
- [ ] Cache operations working
- [ ] No connection errors

---

## PHASE 8: MONITORING SETUP

### Application Insights
- [ ] Application Insights configured
- [ ] Telemetry data flowing
- [ ] Live Metrics accessible
- [ ] Application Map visible
- [ ] Performance metrics available

### Log Analytics
- [ ] Log Analytics Workspace active
- [ ] Logs being collected
- [ ] Query workspace accessible
- [ ] Retention period confirmed: 30 days

### Alerts Configuration
- [ ] Alert rules created (optional for dev):
  - [ ] Response time > 2 seconds
  - [ ] Error rate > 5%
  - [ ] CPU > 80%
  - [ ] Memory > 80%
- [ ] Alert action group configured
- [ ] Test alert sent and received

### Cost Monitoring
- [ ] Azure Cost Management enabled
- [ ] Budget created: $______ /month
- [ ] Budget alerts configured at:
  - [ ] 80% threshold
  - [ ] 100% threshold
- [ ] Cost analysis reviewed

---

## PHASE 9: SECURITY VALIDATION

### Network Security
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] TLS 1.2 minimum version
- [ ] SSL certificate valid
- [ ] WAF enabled (staging/prod)
- [ ] DDoS protection active (Front Door)

### Access Control
- [ ] Azure AD authentication working
- [ ] Only authenticated users can access
- [ ] Managed identities configured
- [ ] RBAC roles assigned correctly
- [ ] No overly permissive access

### Secret Management
- [ ] All secrets in Key Vault
- [ ] No secrets in application code
- [ ] No secrets in environment variables (using Key Vault references)
- [ ] Key Vault access logs enabled

### Audit Logging
- [ ] Diagnostic settings enabled
- [ ] Logs flowing to Log Analytics
- [ ] Audit logs accessible
- [ ] Log retention configured

---

## PHASE 10: DOCUMENTATION

### Deployment Documentation
- [ ] Deployment outputs saved
- [ ] Connection strings documented (securely)
- [ ] Resource names documented
- [ ] Configuration settings documented

### Credentials Management
- [ ] All credentials saved securely (password manager or Key Vault)
- [ ] Azure AD app credentials saved
- [ ] Service principal credentials saved
- [ ] Database admin credentials saved
- [ ] Superuser credentials saved

### Next Steps Documented
- [ ] Remaining manual configuration steps listed
- [ ] GitHub Secrets configuration documented
- [ ] Production deployment prerequisites documented

---

## PHASE 11: GITHUB ACTIONS SETUP (Optional)

### GitHub Secrets Configuration
- [ ] Navigate to: GitHub → Settings → Secrets and variables → Actions
- [ ] Add repository secrets:
  - [ ] `AZURE_CREDENTIALS_{ENV}`: Service principal JSON
  - [ ] `DJANGO_SECRET_KEY_{ENV}`: Generated secret key
  - [ ] `DATABASE_URL_{ENV}`: PostgreSQL connection string
  - [ ] `REDIS_URL_{ENV}`: Redis connection string
  - [ ] `AZURE_CLIENT_ID_{ENV}`: Azure AD client ID
  - [ ] `AZURE_CLIENT_SECRET_{ENV}`: Azure AD client secret
  - [ ] `AZURE_TENANT_ID`: Azure AD tenant ID
  - [ ] `AZURE_STORAGE_CONNECTION_STRING_{ENV}`: Storage connection string

### Workflow Testing
- [ ] GitHub Actions workflow exists: `.github/workflows/deploy-{environment}.yml`
- [ ] Workflow syntax validated
- [ ] Secrets configured correctly
- [ ] Test deployment triggered (if ready)

---

## PHASE 12: FINAL VALIDATION

### Functionality Testing
- [ ] User registration/login working
- [ ] Client management CRUD operations working
- [ ] CSV upload working
- [ ] Report generation working
- [ ] Report download working
- [ ] Dashboard loading correctly

### Performance Testing
- [ ] Page load time < 3 seconds
- [ ] API response time < 2 seconds
- [ ] No timeouts observed
- [ ] Auto-scaling configured (staging/prod)

### Rollback Preparation
- [ ] Rollback procedure documented
- [ ] Resource group can be deleted if needed
- [ ] Deployment can be reversed
- [ ] Rollback command ready:
  ```powershell
  az group delete --name rg-azure-advisor-{env} --yes --no-wait
  ```

---

## DEPLOYMENT SIGN-OFF

### Deployment Summary
- **Environment:** _______________________
- **Deployment Date:** _______________________
- **Deployment Duration:** _______________________
- **Deployed By:** _______________________
- **Resources Created:** _______________________
- **Estimated Monthly Cost:** $_______________________

### Deployment Status
- [ ] ✅ All prerequisites met
- [ ] ✅ Deployment completed successfully
- [ ] ✅ All resources provisioned
- [ ] ✅ Application configured
- [ ] ✅ Health checks passing
- [ ] ✅ Security validated
- [ ] ✅ Monitoring active
- [ ] ✅ Documentation complete

### Known Issues
_List any issues encountered during deployment:_

1. _______________________
2. _______________________
3. _______________________

### Next Steps
_List remaining tasks or next phase actions:_

1. _______________________
2. _______________________
3. _______________________

### Sign-Off
- **Deployed By:** _______________________ (Signature)
- **Reviewed By:** _______________________ (Signature)
- **Date:** _______________________
- **Status:** ___ Approved ___ Approved with Issues ___ Rejected

---

## TROUBLESHOOTING QUICK REFERENCE

### Common Issues

**Deployment Fails:**
1. Check Azure CLI login: `az account show`
2. Verify subscription permissions
3. Review deployment logs in Azure Portal
4. Check Bicep template syntax
5. Verify parameter file values

**Application Not Loading:**
1. Check App Service logs
2. Verify environment variables
3. Check health endpoint: `/api/health/`
4. Review Application Insights errors
5. Restart App Service

**Database Connection Fails:**
1. Check firewall rules (allow Azure services)
2. Verify connection string
3. Check SSL enforcement
4. Test connection from App Service
5. Review PostgreSQL server logs

**Authentication Fails:**
1. Verify Azure AD app registration
2. Check redirect URIs
3. Verify client ID and secret
4. Check tenant ID
5. Review authentication logs

**Secrets Not Accessible:**
1. Check Key Vault access policies
2. Verify managed identity assignment
3. Check RBAC roles
4. Ensure Key Vault references format correct
5. Restart App Service after configuration changes

---

**Document Version:** 1.0
**Last Updated:** October 4, 2025
**Prepared By:** DevOps & Cloud Infrastructure Specialist

---

**SAVE THIS CHECKLIST WITH DEPLOYMENT DOCUMENTATION**
