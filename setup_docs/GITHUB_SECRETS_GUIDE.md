# GitHub Secrets Configuration Guide
**Azure Advisor Reports Platform - CI/CD Secrets Setup**

**Version:** 1.0
**Last Updated:** October 2, 2025
**Target:** GitHub Actions Workflows

---

## Table of Contents

1. [Overview](#overview)
2. [Azure Credentials](#azure-credentials)
3. [Application Secrets](#application-secrets)
4. [Database Secrets](#database-secrets)
5. [Azure AD Secrets](#azure-ad-secrets)
6. [Storage Secrets](#storage-secrets)
7. [Configuration by Environment](#configuration-by-environment)
8. [Setup Instructions](#setup-instructions)
9. [Verification](#verification)
10. [Security Best Practices](#security-best-practices)

---

## Overview

GitHub Actions workflows require secrets for deploying to Azure and configuring the application. This guide documents all required secrets and how to obtain them.

### Secret Categories

1. **Azure Infrastructure Secrets** - For Azure CLI authentication
2. **Application Configuration** - Django/React settings
3. **Database Credentials** - PostgreSQL connection
4. **Caching** - Redis connection
5. **Azure AD Authentication** - OAuth 2.0 credentials
6. **Storage** - Azure Blob Storage

### Naming Convention

All secrets follow this pattern:
```
<SECRET_NAME>_<ENVIRONMENT>
```

Environments: `DEV`, `STAGING`, `PROD`

---

## Azure Credentials

### AZURE_CREDENTIALS_{ENV}

**Purpose:** Authenticate GitHub Actions to Azure for resource deployment

**How to Obtain:**

```powershell
# Create a service principal for GitHub Actions
$appName = "GitHub-Actions-AzureAdvisorReports-Prod"
$subscriptionId = az account show --query id -o tsv

# Create service principal with Contributor role
$sp = az ad sp create-for-rbac `
  --name $appName `
  --role Contributor `
  --scopes "/subscriptions/$subscriptionId" `
  --sdk-auth `
  -o json

# The output is the JSON you need for the secret
$sp | Out-File "azure-credentials-prod.json"

# Display the JSON (copy this value)
$sp
```

**Format:**
```json
{
  "clientId": "<GUID>",
  "clientSecret": "<SECRET>",
  "subscriptionId": "<GUID>",
  "tenantId": "<GUID>",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

**Usage in Workflow:**
```yaml
- name: Azure Login
  uses: azure/login@v1
  with:
    creds: ${{ secrets.AZURE_CREDENTIALS_PROD }}
```

**Required For:**
- `deploy-staging.yml`
- `deploy-production.yml`

---

## Application Secrets

### DJANGO_SECRET_KEY_{ENV}

**Purpose:** Django cryptographic signing key

**How to Obtain:**

```powershell
# Generate a secure random key
$djangoSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 50 | ForEach-Object {[char]$_})
Write-Host "DJANGO_SECRET_KEY: $djangoSecret"

# Or use Python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Format:** 50+ character random string

**Example:**
```
jR8nK3mP9vL2qW5tY7uI1oP4aS6dF8gH0jK2lZ4xC3vB5nM7
```

**Usage in Workflow:**
```yaml
env:
  SECRET_KEY: ${{ secrets.DJANGO_SECRET_KEY_PROD }}
```

**Required For:**
- Backend deployment
- Django settings configuration

---

## Database Secrets

### DATABASE_URL_{ENV}

**Purpose:** PostgreSQL connection string

**How to Obtain:**

After Bicep deployment:

```powershell
# Get deployment outputs
$outputs = az deployment sub show --name <deployment-name> --query properties.outputs -o json | ConvertFrom-Json
$dbConnectionString = $outputs.postgreSqlConnectionString.value

Write-Host "DATABASE_URL: $dbConnectionString"
```

**Format:**
```
postgresql://<username>:<password>@<server>.postgres.database.azure.com:5432/<database>?sslmode=require
```

**Example:**
```
postgresql://postgres:MyP@ssw0rd@azure-advisor-psql-prod.postgres.database.azure.com:5432/azure_advisor_reports?sslmode=require
```

**Usage in Workflow:**
```yaml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL_PROD }}
```

**Required For:**
- Backend deployment
- Database migrations
- Application runtime

---

## Caching Secrets

### REDIS_URL_{ENV}

**Purpose:** Redis cache and Celery broker connection

**How to Obtain:**

After Bicep deployment:

```powershell
# Get Redis connection string from deployment
$redisConnectionString = $outputs.redisConnectionString.value

Write-Host "REDIS_URL: $redisConnectionString"
```

**Format:**
```
rediss://:<access-key>@<cache-name>.redis.cache.windows.net:6380/0?ssl_cert_reqs=required
```

**Example:**
```
rediss://:dQgY+wVxK3mP9vL2qW5tY7uI1oP4aS6dF8gH==@azure-advisor-redis-prod.redis.cache.windows.net:6380/0?ssl_cert_reqs=required
```

**Usage in Workflow:**
```yaml
env:
  REDIS_URL: ${{ secrets.REDIS_URL_PROD }}
  CELERY_BROKER_URL: ${{ secrets.REDIS_URL_PROD }}
  CELERY_RESULT_BACKEND: ${{ secrets.REDIS_URL_PROD }}
```

**Required For:**
- Backend deployment
- Celery workers
- Application caching

---

## Azure AD Secrets

### AZURE_CLIENT_ID_{ENV}

**Purpose:** Azure AD application (client) ID for OAuth authentication

**How to Obtain:**

```powershell
# From Azure AD app registration
$clientId = az ad app list --display-name "Azure Advisor Reports - Production" --query "[0].appId" -o tsv

Write-Host "AZURE_CLIENT_ID: $clientId"
```

**Format:** GUID

**Example:**
```
12345678-1234-1234-1234-123456789012
```

**Usage in Workflow:**
```yaml
env:
  AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID_PROD }}
  REACT_APP_AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID_PROD }}
```

**Required For:**
- Backend authentication
- Frontend authentication
- Both deployments

---

### AZURE_CLIENT_SECRET_{ENV}

**Purpose:** Azure AD application client secret

**How to Obtain:**

```powershell
# Create a new client secret
$app = az ad app list --display-name "Azure Advisor Reports - Production" --query "[0]" -o json | ConvertFrom-Json

$secret = az ad app credential reset `
  --id $app.appId `
  --append `
  --display-name "GitHub Actions Secret" `
  --years 2 `
  --query password -o tsv

Write-Host "AZURE_CLIENT_SECRET: $secret" -ForegroundColor Yellow
Write-Host "SAVE THIS NOW! It won't be shown again." -ForegroundColor Red
```

**Format:** Random string (Base64-like)

**Example:**
```
3mP~9vL2.qW5tY7uI1oP4aS6dF8gH0jK2lZ4x
```

**Security Note:** This is highly sensitive. Store securely and rotate regularly.

**Usage in Workflow:**
```yaml
env:
  AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET_PROD }}
```

**Required For:**
- Backend authentication

---

### AZURE_TENANT_ID_{ENV}

**Purpose:** Azure AD tenant (directory) ID

**How to Obtain:**

```powershell
# Get tenant ID
$tenantId = az account show --query tenantId -o tsv

Write-Host "AZURE_TENANT_ID: $tenantId"
```

**Format:** GUID

**Example:**
```
87654321-4321-4321-4321-210987654321
```

**Usage in Workflow:**
```yaml
env:
  AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID_PROD }}
  REACT_APP_AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID_PROD }}
```

**Required For:**
- Backend authentication
- Frontend authentication

---

## Storage Secrets

### AZURE_STORAGE_CONNECTION_STRING_{ENV}

**Purpose:** Azure Blob Storage for CSV uploads and generated reports

**How to Obtain:**

After Bicep deployment:

```powershell
# Get storage connection string
$storageConnectionString = $outputs.storageAccountConnectionString.value

Write-Host "AZURE_STORAGE_CONNECTION_STRING: $storageConnectionString"
```

**Format:**
```
DefaultEndpointsProtocol=https;AccountName=<name>;AccountKey=<key>;EndpointSuffix=core.windows.net
```

**Example:**
```
DefaultEndpointsProtocol=https;AccountName=azureadvisorstor;AccountKey=wVxK3mP9vL2qW5tY7uI1oP4aS6dF8gH0jK2lZ4xC3vB5nM7==;EndpointSuffix=core.windows.net
```

**Usage in Workflow:**
```yaml
env:
  AZURE_STORAGE_CONNECTION_STRING: ${{ secrets.AZURE_STORAGE_CONNECTION_STRING_PROD }}
```

**Required For:**
- Backend deployment
- File upload functionality
- Report generation

---

## Configuration by Environment

### Development Environment

**Required Secrets:**
```
AZURE_CREDENTIALS_DEV
DJANGO_SECRET_KEY_DEV
DATABASE_URL_DEV
REDIS_URL_DEV
AZURE_CLIENT_ID_DEV
AZURE_CLIENT_SECRET_DEV
AZURE_TENANT_ID_DEV
AZURE_STORAGE_CONNECTION_STRING_DEV
```

**Optional:**
- Can use local PostgreSQL/Redis
- Can use Docker Compose instead of Azure resources

---

### Staging Environment

**Required Secrets:**
```
AZURE_CREDENTIALS_STAGING
DJANGO_SECRET_KEY_STAGING
DATABASE_URL_STAGING
REDIS_URL_STAGING
AZURE_CLIENT_ID_STAGING
AZURE_CLIENT_SECRET_STAGING
AZURE_TENANT_ID_STAGING
AZURE_STORAGE_CONNECTION_STRING_STAGING
```

**Additional:**
```
AZURE_WEBAPP_NAME_BACKEND_STAGING
AZURE_WEBAPP_NAME_FRONTEND_STAGING
AZURE_RESOURCE_GROUP_STAGING
```

---

### Production Environment

**Required Secrets:**
```
AZURE_CREDENTIALS_PROD
DJANGO_SECRET_KEY_PROD
DATABASE_URL_PROD
REDIS_URL_PROD
AZURE_CLIENT_ID_PROD
AZURE_CLIENT_SECRET_PROD
AZURE_TENANT_ID_PROD
AZURE_STORAGE_CONNECTION_STRING_PROD
```

**Additional:**
```
AZURE_WEBAPP_NAME_BACKEND_PROD
AZURE_WEBAPP_NAME_FRONTEND_PROD
AZURE_RESOURCE_GROUP_PROD
SENTRY_DSN_PROD (optional - for error tracking)
```

---

## Setup Instructions

### Using GitHub CLI

```powershell
# Install GitHub CLI
winget install GitHub.cli

# Login
gh auth login

# Navigate to repository
cd "D:\Code\Azure Reports"

# Set secrets (Production example)
gh secret set AZURE_CREDENTIALS_PROD --body @azure-credentials-prod.json
gh secret set DJANGO_SECRET_KEY_PROD --body "<your-django-secret>"
gh secret set DATABASE_URL_PROD --body "<your-db-url>"
gh secret set REDIS_URL_PROD --body "<your-redis-url>"
gh secret set AZURE_CLIENT_ID_PROD --body "<your-client-id>"
gh secret set AZURE_CLIENT_SECRET_PROD --body "<your-client-secret>"
gh secret set AZURE_TENANT_ID_PROD --body "<your-tenant-id>"
gh secret set AZURE_STORAGE_CONNECTION_STRING_PROD --body "<your-storage-connection>"

# Additional configuration secrets
gh secret set AZURE_WEBAPP_NAME_BACKEND_PROD --body "azure-advisor-backend-prod"
gh secret set AZURE_WEBAPP_NAME_FRONTEND_PROD --body "azure-advisor-frontend-prod"
gh secret set AZURE_RESOURCE_GROUP_PROD --body "rg-azure-advisor-prod"
```

### Using GitHub Web UI

1. Go to: `https://github.com/YOUR_ORG/YOUR_REPO/settings/secrets/actions`
2. Click "New repository secret"
3. Enter secret name (e.g., `AZURE_CREDENTIALS_PROD`)
4. Paste secret value
5. Click "Add secret"
6. Repeat for all secrets

### Bulk Setup Script

Create `scripts/setup-github-secrets.ps1`:

```powershell
# Load deployment outputs
$outputs = Get-Content "deployment-outputs-prod.json" | ConvertFrom-Json

# Set all secrets
gh secret set AZURE_CREDENTIALS_PROD --body @azure-credentials-prod.json
gh secret set DJANGO_SECRET_KEY_PROD --body (Read-Host -Prompt "Django Secret Key" -AsSecureString | ConvertFrom-SecureString)
gh secret set DATABASE_URL_PROD --body $outputs.postgreSqlConnectionString.value
gh secret set REDIS_URL_PROD --body $outputs.redisConnectionString.value
gh secret set AZURE_CLIENT_ID_PROD --body (Read-Host -Prompt "Azure Client ID")
gh secret set AZURE_CLIENT_SECRET_PROD --body (Read-Host -Prompt "Azure Client Secret" -AsSecureString | ConvertFrom-SecureString)
gh secret set AZURE_TENANT_ID_PROD --body (az account show --query tenantId -o tsv)
gh secret set AZURE_STORAGE_CONNECTION_STRING_PROD --body $outputs.storageAccountConnectionString.value
gh secret set AZURE_WEBAPP_NAME_BACKEND_PROD --body $outputs.appServiceBackendName.value
gh secret set AZURE_WEBAPP_NAME_FRONTEND_PROD --body $outputs.appServiceFrontendName.value
gh secret set AZURE_RESOURCE_GROUP_PROD --body $outputs.resourceGroupName.value

Write-Host "All secrets configured successfully!" -ForegroundColor Green
```

---

## Verification

### List All Secrets

```powershell
# Using GitHub CLI
gh secret list

# Expected output shows all secret names (values are hidden)
```

### Test Secrets in Workflow

Create `.github/workflows/test-secrets.yml`:

```yaml
name: Test Secrets Configuration

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Check Secrets
        run: |
          echo "Testing secret availability..."
          if [ -z "${{ secrets.AZURE_CREDENTIALS_PROD }}" ]; then
            echo "❌ AZURE_CREDENTIALS_PROD not set"
            exit 1
          fi
          echo "✅ AZURE_CREDENTIALS_PROD is set"

          if [ -z "${{ secrets.DJANGO_SECRET_KEY_PROD }}" ]; then
            echo "❌ DJANGO_SECRET_KEY_PROD not set"
            exit 1
          fi
          echo "✅ DJANGO_SECRET_KEY_PROD is set"

          echo "All required secrets are configured!"
```

Run manually to test:
```powershell
gh workflow run test-secrets.yml
gh run list --workflow=test-secrets.yml
```

---

## Security Best Practices

### 1. Secret Rotation

Rotate secrets regularly:
- **Azure AD Client Secrets:** Every 6-12 months
- **Django Secret Key:** Annually (requires app restart)
- **Database Passwords:** Annually during maintenance window
- **Service Principal Credentials:** Every 12 months

### 2. Access Control

- Limit who can view/edit GitHub Actions secrets
- Use repository-level secrets, not organization-level
- Enable branch protection rules
- Require approvals for production deployments

### 3. Audit Trail

```powershell
# Check secret usage in workflows
gh api repos/:owner/:repo/actions/secrets/:secret_name/logs

# Monitor for unauthorized access
az monitor activity-log list --max-events 100 | Where-Object {$_.operationName.value -like "*Secret*"}
```

### 4. Emergency Procedures

**If a secret is compromised:**

1. **Immediately rotate the credential:**
   ```powershell
   # For Azure AD client secret
   az ad app credential reset --id <app-id> --years 1

   # Update GitHub secret
   gh secret set AZURE_CLIENT_SECRET_PROD --body "<new-secret>"
   ```

2. **Revoke old credential:**
   ```powershell
   az ad app credential delete --id <app-id> --key-id <old-key-id>
   ```

3. **Review access logs:**
   ```powershell
   az monitor activity-log list --start-time 2025-10-01 --end-time 2025-10-02
   ```

4. **Redeploy applications with new secrets**

### 5. Key Vault Integration

For production, consider using Azure Key Vault instead of GitHub Secrets:

```yaml
- name: Get secrets from Key Vault
  uses: Azure/get-keyvault-secrets@v1
  with:
    keyvault: "azure-advisor-kv-prod"
    secrets: 'DATABASE-URL,REDIS-URL,DJANGO-SECRET-KEY'
  id: keyvault
```

This provides:
- Centralized secret management
- Audit logging
- Automatic rotation
- RBAC integration

---

## Troubleshooting

### Issue: "Secret not found" in workflow

**Solution:**
```powershell
# Verify secret exists
gh secret list | Select-String "AZURE_CREDENTIALS_PROD"

# If not found, set it
gh secret set AZURE_CREDENTIALS_PROD --body @azure-credentials-prod.json
```

### Issue: Invalid Azure credentials

**Solution:**
```powershell
# Test the service principal
$creds = Get-Content azure-credentials-prod.json | ConvertFrom-Json

az login --service-principal `
  --username $creds.clientId `
  --password $creds.clientSecret `
  --tenant $creds.tenantId

# If it fails, recreate the service principal
az ad sp delete --id $creds.clientId
# Then create new one (see Azure Credentials section)
```

### Issue: Database connection fails

**Solution:**
```powershell
# Test connection string
$dbUrl = "YOUR_DATABASE_URL"

# Use psql or test with Python
python -c "import psycopg2; conn = psycopg2.connect('$dbUrl'); print('Connection successful')"
```

---

## Quick Reference

| Secret Name | Format | Sensitivity | Rotation Frequency |
|------------|--------|-------------|-------------------|
| AZURE_CREDENTIALS | JSON | High | 12 months |
| DJANGO_SECRET_KEY | String | High | 12 months |
| DATABASE_URL | Connection String | Critical | 12 months |
| REDIS_URL | Connection String | High | 12 months |
| AZURE_CLIENT_ID | GUID | Medium | N/A (immutable) |
| AZURE_CLIENT_SECRET | String | Critical | 6 months |
| AZURE_TENANT_ID | GUID | Low | N/A (immutable) |
| AZURE_STORAGE_CONNECTION_STRING | Connection String | High | 12 months |

---

## Next Steps

After configuring all secrets:

1. ✅ Run secret verification workflow
2. ✅ Test staging deployment
3. ✅ Run smoke tests
4. ✅ Deploy to production
5. ✅ Monitor Application Insights for errors
6. ✅ Schedule secret rotation reminders

---

**Document Version:** 1.0
**Last Updated:** October 2, 2025
**Maintained By:** DevOps Team
