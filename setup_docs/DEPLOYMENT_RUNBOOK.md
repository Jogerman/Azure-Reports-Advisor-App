# DEPLOYMENT RUNBOOK
## Azure Advisor Reports Platform - Step-by-Step Deployment Guide

**Document Version:** 1.0
**Last Updated:** October 3, 2025
**Platform:** Windows (PowerShell)
**Target:** Production Deployment

---

## 📋 OVERVIEW

This runbook provides **step-by-step instructions** for deploying the Azure Advisor Reports Platform to production. It assumes you have completed all development and testing, and are ready to deploy to Azure.

### Prerequisites Checklist

Before starting deployment, ensure you have:

- [ ] Azure subscription with Owner or Contributor role
- [ ] Azure CLI installed (`az --version` should show 2.50+)
- [ ] PowerShell 7+ installed
- [ ] Bicep CLI installed (`az bicep version`)
- [ ] GitHub repository access with Secrets management permission
- [ ] Domain name (optional, for custom domain)
- [ ] SSL certificate (optional, Azure can manage for you)

---

## PHASE 1: PRE-DEPLOYMENT PREPARATION

**Estimated Time:** 2 hours
**Owner:** DevOps Engineer + Security Admin

### Step 1.1: Azure CLI Setup (10 minutes)

```powershell
# Verify Azure CLI installation
az --version

# If not installed, install Azure CLI
# Download from: https://aka.ms/installazurecliwindows

# Login to Azure
az login

# Set your subscription (if you have multiple)
az account list --output table
az account set --subscription "<your-subscription-id>"

# Verify selected subscription
az account show
```

**Validation:**
- Azure CLI version: 2.50 or higher
- Successfully logged in
- Correct subscription selected

### Step 1.2: Install Bicep CLI (5 minutes)

```powershell
# Install Bicep CLI
az bicep install

# Verify installation
az bicep version

# Update to latest version
az bicep upgrade
```

**Validation:**
- Bicep CLI installed successfully
- Version 0.20+ recommended

### Step 1.3: Clone Repository (5 minutes)

```powershell
# Clone the repository
cd C:\Projects
git clone <repository-url> azure-advisor-reports
cd azure-advisor-reports

# Checkout production branch (or main)
git checkout main
git pull origin main

# Verify Bicep files exist
ls scripts\azure\bicep\
```

**Validation:**
- Repository cloned successfully
- Bicep files present in `scripts/azure/bicep/`
  - `main.bicep`
  - `modules/infrastructure.bicep`
  - `modules/security.bicep`
  - `modules/networking.bicep`

### Step 1.4: Prepare Parameters (30 minutes)

```powershell
# Navigate to Bicep directory
cd scripts\azure\bicep

# Copy example parameters file
Copy-Item main.parameters.example.json main.parameters.prod.json

# Edit parameters file
notepad main.parameters.prod.json
```

**Edit the parameters file** with your production values:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environment": {
      "value": "prod"
    },
    "location": {
      "value": "eastus"
    },
    "projectName": {
      "value": "azure-advisor-reports"
    },
    "databaseAdminUsername": {
      "value": "azureadmin"
    },
    "databaseAdminPassword": {
      "value": "CHANGE_THIS_SECURE_PASSWORD_123!"
    },
    "customDomainName": {
      "value": "reports.yourcompany.com"
    },
    "enableCustomDomain": {
      "value": true
    },
    "keyVaultSku": {
      "value": "Standard"
    },
    "frontDoorSku": {
      "value": "Standard_AzureFrontDoor"
    }
  }
}
```

**⚠️ IMPORTANT: Change These Values:**
- `databaseAdminPassword`: Use a strong, random password (min 12 chars)
- `customDomainName`: Your actual domain (or set `enableCustomDomain` to false)
- `location`: Choose Azure region closest to your users

**Store Sensitive Values Securely:**
```powershell
# Save database password to secure file
$dbPassword = Read-Host -AsSecureString "Enter database admin password"
$dbPassword | ConvertFrom-SecureString | Out-File ".\db-password-encrypted.txt"
```

**Validation:**
- Parameters file created: `main.parameters.prod.json`
- All required parameters filled
- Sensitive values stored securely

### Step 1.5: Validate Bicep Templates (15 minutes)

```powershell
# Validate main template
az bicep build --file main.bicep

# Validate each module
az bicep build --file modules\infrastructure.bicep
az bicep build --file modules\security.bicep
az bicep build --file modules\networking.bicep

# Perform deployment validation (dry-run)
az deployment sub create `
  --location eastus `
  --template-file main.bicep `
  --parameters main.parameters.prod.json `
  --what-if
```

**What to Check:**
- All Bicep files compile without errors
- No circular dependencies
- `--what-if` shows expected resources to be created
- No destructive changes listed (first deployment)

**Validation:**
- ✅ All templates compile successfully
- ✅ What-if output shows ~15 resources to be created
- ✅ No errors or warnings

---

## PHASE 2: AZURE AD CONFIGURATION

**Estimated Time:** 30 minutes
**Owner:** Security Admin or Azure AD Administrator

### Step 2.1: Register Production Azure AD Application (20 minutes)

```powershell
# Open Azure Portal
Start-Process "https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"

# Or use Azure CLI to register
$appName = "Azure Advisor Reports - Production"
$redirectUri = "https://reports.yourcompany.com"  # Change to your domain

# Create the app registration
$app = az ad app create `
  --display-name $appName `
  --sign-in-audience "AzureADMyOrg" `
  --web-redirect-uris $redirectUri `
  --query "appId" `
  --output tsv

Write-Host "Application ID: $app" -ForegroundColor Green

# Note the Application (Client) ID
$clientId = $app
```

**Or via Azure Portal (Recommended for first-time):**

1. Navigate to **Azure Active Directory** > **App registrations** > **New registration**
2. **Name:** Azure Advisor Reports - Production
3. **Supported account types:** Accounts in this organizational directory only
4. **Redirect URI:**
   - Platform: Web
   - URL: `https://reports.yourcompany.com` (your production domain)
5. Click **Register**

6. **Copy Application (Client) ID** - You'll need this!
7. **Copy Directory (Tenant) ID** - You'll need this!

**Validation:**
- Application registered successfully
- Client ID copied and saved
- Tenant ID copied and saved

### Step 2.2: Create Client Secret (5 minutes)

```powershell
# Via Azure CLI
$secretName = "prod-secret-$(Get-Date -Format 'yyyy-MM')"
$secretEndDate = (Get-Date).AddMonths(24)  # 24-month expiry

$secret = az ad app credential reset `
  --id $clientId `
  --append `
  --display-name $secretName `
  --end-date $secretEndDate.ToString("yyyy-MM-ddTHH:mm:ssZ") `
  --query "password" `
  --output tsv

Write-Host "Client Secret: $secret" -ForegroundColor Yellow
Write-Host "⚠️ SAVE THIS NOW! You won't see it again!" -ForegroundColor Red

# Save to secure file
$secret | ConvertTo-SecureString -AsPlainText -Force | ConvertFrom-SecureString | Out-File ".\client-secret-encrypted.txt"
```

**Or via Azure Portal:**

1. Go to your app registration > **Certificates & secrets**
2. Click **New client secret**
3. **Description:** prod-secret-2025-10
4. **Expires:** 24 months (recommended)
5. Click **Add**
6. **⚠️ COPY THE SECRET VALUE IMMEDIATELY** - You can't see it again!

**Store the secret securely:**
- Password manager (1Password, LastPass, Azure Key Vault)
- Encrypted file on secure drive
- **Never commit to Git!**

**Validation:**
- Client secret created
- Secret value copied and stored securely
- Expiry date noted (set calendar reminder for 6 months before)

### Step 2.3: Configure API Permissions (5 minutes)

**Via Azure Portal:**

1. Go to your app registration > **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Select **Delegated permissions**
5. Search and check:
   - `User.Read`
   - `openid`
   - `profile`
   - `email`
6. Click **Add permissions**
7. Click **Grant admin consent for [Your Organization]**
8. Confirm by clicking **Yes**

```powershell
# Via Azure CLI
az ad app permission add `
  --id $clientId `
  --api 00000003-0000-0000-c000-000000000000 `
  --api-permissions `
    e1fe6dd8-ba31-4d61-89e7-88639da4683d=Scope `  # User.Read
    37f7f235-527c-4136-accd-4a02d197296e=Scope `  # openid
    14dad69e-099b-42c9-810b-d002981feec1=Scope `  # profile
    64a6cdd6-aab1-4aaf-94b8-3cc8405e90d0=Scope    # email

# Grant admin consent
az ad app permission admin-consent --id $clientId
```

**Validation:**
- 4 permissions added (User.Read, openid, profile, email)
- Admin consent granted (green checkmark)
- Status shows "Granted for [Your Organization]"

### Step 2.4: Save Azure AD Credentials (5 minutes)

Create a secure credentials file:

```powershell
# Create credentials object
$credentials = @{
    ClientId = $clientId
    TenantId = (az account show --query tenantId -o tsv)
    ClientSecret = $secret
    RedirectUri = "https://reports.yourcompany.com"
} | ConvertTo-Json

# Save to encrypted file
$credentials | Out-File ".\azuread-credentials.json"

Write-Host "Credentials saved to azuread-credentials.json" -ForegroundColor Green
Write-Host "⚠️ KEEP THIS FILE SECURE! Add to .gitignore!" -ForegroundColor Yellow
```

**Validation:**
- Credentials file created
- File added to `.gitignore`
- File backed up to secure location

---

## PHASE 3: INFRASTRUCTURE DEPLOYMENT

**Estimated Time:** 30 minutes
**Owner:** DevOps Engineer

### Step 3.1: Create Resource Group (Optional, 2 minutes)

```powershell
# Resource group is created by main.bicep, but you can pre-create it
$resourceGroup = "rg-azure-advisor-reports-prod"
$location = "eastus"

az group create `
  --name $resourceGroup `
  --location $location `
  --tags `
    Environment=Production `
    Project=AzureAdvisorReports `
    ManagedBy=Bicep `
    CostCenter=IT `
    CreatedDate=$(Get-Date -Format "yyyy-MM-dd")

Write-Host "Resource group created: $resourceGroup" -ForegroundColor Green
```

**Validation:**
- Resource group created successfully
- Tags applied correctly

### Step 3.2: Deploy Infrastructure via Bicep (20 minutes)

```powershell
# Navigate to Bicep directory
cd scripts\azure\bicep

# Deploy to Azure (subscription-level deployment)
Write-Host "Starting deployment... This will take 15-20 minutes" -ForegroundColor Yellow

$deploymentName = "azure-advisor-reports-prod-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

az deployment sub create `
  --name $deploymentName `
  --location $location `
  --template-file main.bicep `
  --parameters main.parameters.prod.json `
  --parameters `
    databaseAdminUsername=azureadmin `
    databaseAdminPassword="$(Get-Content .\db-password-encrypted.txt | ConvertTo-SecureString | ConvertFrom-SecureString -AsPlainText)" `
  --verbose

# Check deployment status
az deployment sub show `
  --name $deploymentName `
  --query "properties.provisioningState" `
  --output tsv
```

**Monitor the deployment:**
- Watch the output for each resource being created
- Deployment takes **15-20 minutes** typically
- PostgreSQL and Front Door take the longest

**Common Issues:**
- **Quota exceeded:** Request quota increase for your subscription
- **Name already taken:** Change `projectName` in parameters
- **SKU not available:** Choose a different region or SKU

**Validation:**
- Deployment completed successfully (provisioningState: Succeeded)
- All 15+ resources created
- No errors in deployment output

### Step 3.3: Retrieve Deployment Outputs (5 minutes)

```powershell
# Get all deployment outputs
$outputs = az deployment sub show `
  --name $deploymentName `
  --query "properties.outputs" `
  --output json | ConvertFrom-Json

# Save outputs to file
$outputs | ConvertTo-Json -Depth 10 | Out-File ".\deployment-outputs.json"

# Display key outputs
Write-Host "=== Deployment Outputs ===" -ForegroundColor Cyan
Write-Host "Resource Group: $($outputs.resourceGroupName.value)" -ForegroundColor Green
Write-Host "Backend URL: $($outputs.backendUrl.value)" -ForegroundColor Green
Write-Host "Frontend URL: $($outputs.frontendUrl.value)" -ForegroundColor Green
Write-Host "Key Vault Name: $($outputs.keyVaultName.value)" -ForegroundColor Green
Write-Host "Database Server: $($outputs.databaseServer.value)" -ForegroundColor Green
Write-Host "Storage Account: $($outputs.storageAccountName.value)" -ForegroundColor Green
Write-Host "Application Insights: $($outputs.appInsightsName.value)" -ForegroundColor Green
```

**Save these values - you'll need them for configuration!**

**Validation:**
- All outputs retrieved successfully
- Output file created: `deployment-outputs.json`
- URLs are accessible (may show default page initially)

### Step 3.4: Verify Resource Creation (5 minutes)

```powershell
# List all resources in the resource group
az resource list `
  --resource-group $outputs.resourceGroupName.value `
  --output table

# Verify specific resources
Write-Host "`n=== Resource Verification ===" -ForegroundColor Cyan

# PostgreSQL
az postgres flexible-server show `
  --resource-group $outputs.resourceGroupName.value `
  --name $outputs.databaseServer.value `
  --query "{Name:name, State:state, Version:version}" `
  --output table

# Redis
az redis show `
  --resource-group $outputs.resourceGroupName.value `
  --name $($outputs.redisName.value) `
  --query "{Name:name, ProvisioningState:provisioningState, SKU:sku.name}" `
  --output table

# App Services
az webapp list `
  --resource-group $outputs.resourceGroupName.value `
  --query "[].{Name:name, State:state, DefaultHostName:defaultHostName}" `
  --output table

# Key Vault
az keyvault show `
  --name $outputs.keyVaultName.value `
  --query "{Name:name, Location:location, SKU:properties.sku.name}" `
  --output table
```

**Check for:**
- All resources showing "Succeeded" or "Running" state
- PostgreSQL version: 15
- Redis SKU matches your parameters
- App Services are running

**Validation:**
- ✅ All 15+ resources created successfully
- ✅ All resources in "Succeeded" or "Running" state
- ✅ No resources in "Failed" state

---

## PHASE 4: SECRETS CONFIGURATION

**Estimated Time:** 45 minutes
**Owner:** DevOps Engineer

### Step 4.1: Add Secrets to Azure Key Vault (20 minutes)

```powershell
$keyVaultName = $outputs.keyVaultName.value

# 1. Django Secret Key (generate a random one)
$djangoSecretKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 50 | ForEach-Object {[char]$_})
az keyvault secret set `
  --vault-name $keyVaultName `
  --name "DJANGO-SECRET-KEY" `
  --value $djangoSecretKey

# 2. Database URL
$dbUser = "azureadmin"
$dbPassword = Get-Content .\db-password-encrypted.txt | ConvertTo-SecureString | ConvertFrom-SecureString -AsPlainText
$dbHost = "$($outputs.databaseServer.value).postgres.database.azure.com"
$dbName = "azure_advisor_reports_prod"
$databaseUrl = "postgresql://${dbUser}:${dbPassword}@${dbHost}:5432/${dbName}?sslmode=require"

az keyvault secret set `
  --vault-name $keyVaultName `
  --name "DATABASE-URL" `
  --value $databaseUrl

# 3. Redis URL
$redisHost = "$($outputs.redisName.value).redis.cache.windows.net"
$redisKey = (az redis list-keys `
  --resource-group $outputs.resourceGroupName.value `
  --name $outputs.redisName.value `
  --query "primaryKey" `
  --output tsv)
$redisUrl = "rediss://:${redisKey}@${redisHost}:6380/0"

az keyvault secret set `
  --vault-name $keyVaultName `
  --name "REDIS-URL" `
  --value $redisUrl

# 4. Azure Storage Connection String
$storageConnectionString = (az storage account show-connection-string `
  --resource-group $outputs.resourceGroupName.value `
  --name $outputs.storageAccountName.value `
  --query "connectionString" `
  --output tsv)

az keyvault secret set `
  --vault-name $keyVaultName `
  --name "AZURE-STORAGE-CONNECTION-STRING" `
  --value $storageConnectionString

# 5. Azure AD Client Secret (from earlier)
az keyvault secret set `
  --vault-name $keyVaultName `
  --name "AZURE-CLIENT-SECRET" `
  --value $secret

# 6. JWT Secret Key (generate a random one)
$jwtSecretKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
az keyvault secret set `
  --vault-name $keyVaultName `
  --name "JWT-SECRET-KEY" `
  --value $jwtSecretKey

# 7. Celery Broker URL (same as Redis)
az keyvault secret set `
  --vault-name $keyVaultName `
  --name "CELERY-BROKER-URL" `
  --value $redisUrl

Write-Host "All secrets added to Key Vault: $keyVaultName" -ForegroundColor Green
```

**Validation:**
- All 7 secrets added to Key Vault
- Secrets accessible via Azure Portal
- No plain-text secrets in Git or local files

### Step 4.2: Configure GitHub Secrets (25 minutes)

**Via GitHub CLI (if installed):**

```powershell
# Install GitHub CLI if not present
# Download from: https://cli.github.com/

# Login to GitHub
gh auth login

# Navigate to repository
cd D:\Code\Azure Reports

# Add production secrets
gh secret set AZURE_CREDENTIALS_PROD --body (Get-Content .\azure-credentials.json)
gh secret set DJANGO_SECRET_KEY_PROD --body $djangoSecretKey
gh secret set DATABASE_URL_PROD --body $databaseUrl
gh secret set REDIS_URL_PROD --body $redisUrl
gh secret set AZURE_CLIENT_ID_PROD --body $clientId
gh secret set AZURE_CLIENT_SECRET_PROD --body $secret
gh secret set AZURE_TENANT_ID_PROD --body (az account show --query tenantId -o tsv)
gh secret set AZURE_STORAGE_CONNECTION_STRING_PROD --body $storageConnectionString
gh secret set AZURE_SUBSCRIPTION_ID_PROD --body (az account show --query id -o tsv)
gh secret set AZURE_RESOURCE_GROUP_PROD --body $outputs.resourceGroupName.value
gh secret set AZURE_WEBAPP_NAME_BACKEND_PROD --body $outputs.backendAppName.value
gh secret set AZURE_WEBAPP_NAME_FRONTEND_PROD --body $outputs.frontendAppName.value

Write-Host "All GitHub secrets configured!" -ForegroundColor Green
```

**Or via GitHub Web UI (Manual):**

1. Go to your repository on GitHub
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret** for each:

**Production Secrets (12 secrets):**

| Secret Name | Value Source | Example |
|-------------|--------------|---------|
| `AZURE_CREDENTIALS_PROD` | Azure service principal JSON | `{"clientId":"...","clientSecret":"...","subscriptionId":"...","tenantId":"..."}` |
| `DJANGO_SECRET_KEY_PROD` | Generated random string | `y7kF9mN2p...` |
| `DATABASE_URL_PROD` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL_PROD` | Redis connection string | `rediss://:key@host:6380/0` |
| `AZURE_CLIENT_ID_PROD` | Azure AD Application ID | `abc123-def456-...` |
| `AZURE_CLIENT_SECRET_PROD` | Azure AD Client Secret | `xyz789...` |
| `AZURE_TENANT_ID_PROD` | Azure AD Tenant ID | `tenant-id-123...` |
| `AZURE_STORAGE_CONNECTION_STRING_PROD` | Storage account connection | `DefaultEndpointsProtocol=https;...` |
| `AZURE_SUBSCRIPTION_ID_PROD` | Azure subscription ID | `sub-id-123...` |
| `AZURE_RESOURCE_GROUP_PROD` | Resource group name | `rg-azure-advisor-reports-prod` |
| `AZURE_WEBAPP_NAME_BACKEND_PROD` | Backend App Service name | `app-azure-advisor-reports-backend-prod` |
| `AZURE_WEBAPP_NAME_FRONTEND_PROD` | Frontend App Service name | `app-azure-advisor-reports-frontend-prod` |

**To create Azure service principal for deployments:**

```powershell
# Create service principal with Contributor role on subscription
$sp = az ad sp create-for-rbac `
  --name "github-actions-azure-advisor-reports" `
  --role Contributor `
  --scopes "/subscriptions/$(az account show --query id -o tsv)" `
  --sdk-auth

# Output is the JSON for AZURE_CREDENTIALS_PROD secret
Write-Host $sp -ForegroundColor Cyan
```

**Validation:**
- All 12 production secrets configured in GitHub
- Secrets are encrypted and not visible
- Workflows have access to secrets

---

## PHASE 5: DATABASE INITIALIZATION

**Estimated Time:** 20 minutes
**Owner:** Backend Developer / DevOps Engineer

### Step 5.1: Configure Database Firewall (5 minutes)

```powershell
$dbServerName = $outputs.databaseServer.value
$resourceGroup = $outputs.resourceGroupName.value

# Add your current IP to firewall (for initial setup)
$myIp = (Invoke-WebRequest -Uri "https://api.ipify.org").Content
az postgres flexible-server firewall-rule create `
  --resource-group $resourceGroup `
  --name $dbServerName `
  --rule-name "AllowMyIP" `
  --start-ip-address $myIp `
  --end-ip-address $myIp

# Add Azure services (for App Service access)
az postgres flexible-server firewall-rule create `
  --resource-group $resourceGroup `
  --name $dbServerName `
  --rule-name "AllowAzureServices" `
  --start-ip-address 0.0.0.0 `
  --end-ip-address 0.0.0.0

Write-Host "Database firewall configured" -ForegroundColor Green
```

**Validation:**
- Firewall rules created successfully
- Your IP can connect to database
- Azure services can connect

### Step 5.2: Create Production Database (5 minutes)

```powershell
# Connect to PostgreSQL and create database
$dbHost = "$dbServerName.postgres.database.azure.com"
$dbUser = "azureadmin"

# Install psql if not available (via PostgreSQL client tools)
# Download from: https://www.postgresql.org/download/windows/

# Create database
$env:PGPASSWORD = $dbPassword
psql -h $dbHost -U $dbUser -d postgres -c "CREATE DATABASE azure_advisor_reports_prod;"
psql -h $dbHost -U $dbUser -d postgres -c "CREATE DATABASE azure_advisor_reports_prod_test;"

# Verify databases
psql -h $dbHost -U $dbUser -d postgres -c "\l"

Remove-Item Env:\PGPASSWORD  # Clear password from environment
```

**Or via Azure Portal:**
1. Navigate to your PostgreSQL server
2. Go to **Databases** > **Add**
3. Database name: `azure_advisor_reports_prod`
4. Click **Save**

**Validation:**
- Production database created: `azure_advisor_reports_prod`
- Test database created: `azure_advisor_reports_prod_test`
- Databases visible in Azure Portal

### Step 5.3: Deploy Backend Application (10 minutes)

**Option A: Deploy via GitHub Actions (Recommended)**

```powershell
# Push code to trigger deployment
cd D:\Code\Azure Reports
git checkout main
git pull origin main
git push origin main

# Monitor deployment in GitHub Actions
Start-Process "https://github.com/<your-org>/<your-repo>/actions"
```

**Option B: Deploy via Azure CLI (Manual)**

```powershell
# Build Docker image locally
cd D:\Code\Azure Reports\azure_advisor_reports
docker build -t azure-advisor-backend:prod .

# Push to Azure Container Registry (if using ACR)
# Or deploy directly to App Service

# Deploy to App Service
az webapp deployment source config-zip `
  --resource-group $resourceGroup `
  --name $outputs.backendAppName.value `
  --src backend-deployment.zip
```

**Monitor deployment:**
```powershell
az webapp log tail `
  --resource-group $resourceGroup `
  --name $outputs.backendAppName.value
```

**Validation:**
- Backend deployed successfully
- App Service is running
- No errors in logs

### Step 5.4: Run Database Migrations (5 minutes)

```powershell
# SSH into App Service
az webapp ssh `
  --resource-group $resourceGroup `
  --name $outputs.backendAppName.value

# Inside App Service SSH:
# cd /home/site/wwwroot
# python manage.py migrate --no-input
# python manage.py collectstatic --no-input --clear
# exit

# Or run via App Service console (Azure Portal)
# Navigate to: App Service > Development Tools > SSH
```

**Or run migrations remotely:**

```powershell
# Execute command via App Service
az webapp ssh `
  --resource-group $resourceGroup `
  --name $outputs.backendAppName.value `
  --command "cd /home/site/wwwroot && python manage.py migrate --no-input"
```

**Validation:**
- All migrations applied successfully
- Database schema created
- No migration errors

### Step 5.5: Create Superuser (5 minutes)

```powershell
# SSH into App Service
az webapp ssh `
  --resource-group $resourceGroup `
  --name $outputs.backendAppName.value

# Inside SSH:
# python manage.py createsuperuser
# Username: admin
# Email: admin@yourcompany.com
# Password: (create a strong password)
```

**Or create via Django shell:**

```python
# In App Service SSH
python manage.py shell

from apps.authentication.models import User
User.objects.create_superuser(
    username='admin',
    email='admin@yourcompany.com',
    password='YourStrongPassword123!',
    role='admin'
)
exit()
```

**Validation:**
- Superuser created successfully
- Can login to Django admin: `https://<backend-url>/admin/`

---

## PHASE 6: FRONTEND DEPLOYMENT

**Estimated Time:** 15 minutes
**Owner:** Frontend Developer / DevOps Engineer

### Step 6.1: Configure Frontend Environment (5 minutes)

```powershell
cd D:\Code\Azure Reports\frontend

# Create production environment file
@"
REACT_APP_API_URL=$($outputs.backendUrl.value)
REACT_APP_AZURE_CLIENT_ID=$clientId
REACT_APP_AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)
REACT_APP_AZURE_REDIRECT_URI=$($outputs.frontendUrl.value)
"@ | Out-File .env.production

# Verify file
Get-Content .env.production
```

**Validation:**
- `.env.production` file created
- All environment variables set correctly
- Backend URL points to production

### Step 6.2: Build Frontend (5 minutes)

```powershell
# Install dependencies
npm install

# Build for production
npm run build

# Verify build
ls build\
```

**Build output should show:**
- `build/static/js/*.js` files
- `build/static/css/*.css` files
- `build/index.html`
- Total size < 2MB (gzipped < 500KB)

**Validation:**
- Build completed successfully
- No build errors
- `build/` directory created

### Step 6.3: Deploy Frontend to App Service (5 minutes)

**Option A: Deploy via GitHub Actions (Recommended)**

```powershell
# Commit and push (GitHub Actions will build and deploy)
git add .env.production
git commit -m "Configure production environment"
git push origin main
```

**Option B: Deploy manually via ZIP**

```powershell
# Create deployment ZIP
Compress-Archive -Path build\* -DestinationPath frontend-deployment.zip -Force

# Deploy to App Service
az webapp deployment source config-zip `
  --resource-group $resourceGroup `
  --name $outputs.frontendAppName.value `
  --src frontend-deployment.zip

# Restart App Service
az webapp restart `
  --resource-group $resourceGroup `
  --name $outputs.frontendAppName.value
```

**Validation:**
- Frontend deployed successfully
- App Service is running
- Frontend accessible at production URL

---

## PHASE 7: CELERY WORKERS SETUP

**Estimated Time:** 15 minutes
**Owner:** Backend Developer / DevOps Engineer

### Step 7.1: Configure Celery App Service (10 minutes)

```powershell
# Create App Service for Celery worker
$workerAppName = "app-azure-advisor-reports-worker-prod"

az webapp create `
  --resource-group $resourceGroup `
  --plan $(az appservice plan list --resource-group $resourceGroup --query "[0].name" -o tsv) `
  --name $workerAppName `
  --runtime "PYTHON|3.11" `
  --deployment-container-image-name "azure-advisor-backend:prod"

# Configure app settings (same as backend)
az webapp config appsettings set `
  --resource-group $resourceGroup `
  --name $workerAppName `
  --settings `
    DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production `
    WEBSITE_HTTPLOGGING_RETENTION_DAYS=7 `
    SCM_DO_BUILD_DURING_DEPLOYMENT=true

# Set startup command for Celery worker
az webapp config set `
  --resource-group $resourceGroup `
  --name $workerAppName `
  --startup-file "celery -A azure_advisor_reports worker -l info --pool=solo"

Write-Host "Celery worker configured" -ForegroundColor Green
```

**Validation:**
- Celery worker App Service created
- Startup command set correctly
- App is running

### Step 7.2: Configure Celery Beat (5 minutes)

```powershell
# Create App Service for Celery beat (optional, for scheduled tasks)
$beatAppName = "app-azure-advisor-reports-beat-prod"

az webapp create `
  --resource-group $resourceGroup `
  --plan $(az appservice plan list --resource-group $resourceGroup --query "[0].name" -o tsv) `
  --name $beatAppName `
  --runtime "PYTHON|3.11"

# Set startup command for Celery beat
az webapp config set `
  --resource-group $resourceGroup `
  --name $beatAppName `
  --startup-file "celery -A azure_advisor_reports beat -l info"
```

**Validation:**
- Celery beat configured (if needed)
- Both worker and beat are running

---

## PHASE 8: MONITORING SETUP

**Estimated Time:** 30 minutes
**Owner:** DevOps Engineer

### Step 8.1: Configure Application Insights (10 minutes)

```powershell
$appInsightsName = $outputs.appInsightsName.value
$instrumentationKey = (az monitor app-insights component show `
  --app $appInsightsName `
  --resource-group $resourceGroup `
  --query "instrumentationKey" `
  --output tsv)

# Add instrumentation key to backend app settings
az webapp config appsettings set `
  --resource-group $resourceGroup `
  --name $outputs.backendAppName.value `
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$instrumentationKey

# Restart backend to apply
az webapp restart `
  --resource-group $resourceGroup `
  --name $outputs.backendAppName.value
```

**Validation:**
- Application Insights instrumentation key configured
- Telemetry data flowing to Application Insights

### Step 8.2: Create Dashboards (15 minutes)

**Create dashboards via Azure Portal:**

1. Navigate to **Application Insights** > **Overview**
2. Click **Dashboard** > **New dashboard**

**Create 5 dashboards:**

**Dashboard 1: Application Overview**
- Requests per minute
- Response time (avg, p95, p99)
- Failed requests
- Active users
- Top 10 slowest requests

**Dashboard 2: Performance Metrics**
- Server response time trend
- Database query time
- Redis cache hit rate
- Celery task duration
- Report generation time

**Dashboard 3: Error Tracking**
- Exception count by type
- Failed requests by endpoint
- Error rate trend
- Top 10 errors
- Error details log

**Dashboard 4: Business Metrics**
- Reports generated per day
- Active clients
- Total recommendations processed
- Potential savings calculated
- User login activity

**Dashboard 5: Infrastructure Health**
- CPU usage (backend, frontend, worker)
- Memory usage
- Database connections
- Redis connections
- Disk usage

**Validation:**
- All 5 dashboards created
- Dashboards showing live data
- Team has access to dashboards

### Step 8.3: Configure Alerts (10 minutes)

```powershell
# Create action group for notifications
$actionGroupName = "ag-azure-advisor-reports-prod"
az monitor action-group create `
  --resource-group $resourceGroup `
  --name $actionGroupName `
  --short-name "AAR-Alerts" `
  --email admin email@yourcompany.com `
  --email-name "Admin Team"

# Critical Alert 1: High Response Time
az monitor metrics alert create `
  --name "alert-high-response-time" `
  --resource-group $resourceGroup `
  --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$resourceGroup/providers/Microsoft.Web/sites/$($outputs.backendAppName.value)" `
  --condition "avg requests/duration > 5" `
  --window-size 5m `
  --evaluation-frequency 1m `
  --action $actionGroupName `
  --description "Alert when average response time exceeds 5 seconds"

# Critical Alert 2: High Error Rate
az monitor metrics alert create `
  --name "alert-high-error-rate" `
  --resource-group $resourceGroup `
  --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$resourceGroup/providers/Microsoft.Web/sites/$($outputs.backendAppName.value)" `
  --condition "avg requests/failed > 5" `
  --window-size 5m `
  --evaluation-frequency 1m `
  --action $actionGroupName `
  --description "Alert when error rate exceeds 5% over 5 minutes"

# Add more alerts as needed...
```

**Create additional alerts via Azure Portal:**

**Critical Alerts (5):**
1. Response time > 5 seconds (5-minute window)
2. Error rate > 5% (5-minute window)
3. Service downtime (any App Service unavailable)
4. Database connection failure
5. Redis connection failure

**High Priority Alerts (5):**
1. Memory usage > 80% (15-minute window)
2. CPU usage > 80% (15-minute window)
3. Disk usage > 85%
4. Failed reports > 10 in 1 hour
5. Celery queue depth > 100

**Medium Priority Alerts (3):**
1. Daily cost exceeds budget by 20%
2. Auto-scaling triggered (for awareness)
3. SSL certificate expiring in 30 days

**Validation:**
- All 13 alerts configured
- Action group configured with email notifications
- Test alerts triggered successfully

---

## PHASE 9: VALIDATION & TESTING

**Estimated Time:** 45 minutes
**Owner:** QA Engineer + Full Team

### Step 9.1: Health Check Validation (5 minutes)

```powershell
# Backend health check
$backendHealthUrl = "$($outputs.backendUrl.value)/api/health/"
$backendHealth = Invoke-RestMethod -Uri $backendHealthUrl
Write-Host "Backend Health: $($backendHealth | ConvertTo-Json)" -ForegroundColor Green

# Frontend health check
$frontendHealthUrl = $outputs.frontendUrl.value
$frontendResponse = Invoke-WebRequest -Uri $frontendHealthUrl
Write-Host "Frontend Status: $($frontendResponse.StatusCode)" -ForegroundColor Green
```

**Expected Results:**
- Backend: `{"status": "healthy", "database": "connected", "redis": "connected"}`
- Frontend: HTTP 200 OK

**Validation:**
- Both health checks passing
- All services reporting healthy

### Step 9.2: Smoke Tests (20 minutes)

**Test 1: Authentication Flow**
1. Navigate to frontend URL
2. Click "Sign in with Microsoft"
3. Login with Azure AD credentials
4. Verify redirect back to dashboard
5. Verify user profile displayed
6. Logout

**Test 2: Client Management**
1. Navigate to Clients page
2. Click "Add Client"
3. Fill in client details
4. Save client
5. Verify client appears in list
6. Edit client
7. Delete client

**Test 3: Report Generation (Most Critical)**
1. Upload sample Azure Advisor CSV file
2. Select client
3. Select report type (try all 5 types)
4. Wait for generation (should complete in <45 seconds)
5. Download HTML report
6. Download PDF report
7. Verify report content is correct

**Test 4: Dashboard**
1. Navigate to Dashboard
2. Verify metrics display correctly
3. Verify charts render
4. Verify recent activity shows reports
5. Wait 30 seconds for auto-refresh
6. Verify data updates

**Test 5: Analytics API**
```powershell
# Test analytics endpoint
$analyticsUrl = "$($outputs.backendUrl.value)/api/analytics/dashboard/"
$token = "YOUR_AUTH_TOKEN"  # Get from browser after login

$headers = @{
    "Authorization" = "Bearer $token"
}

$analytics = Invoke-RestMethod -Uri $analyticsUrl -Headers $headers
Write-Host ($analytics | ConvertTo-Json -Depth 5)
```

**Validation:**
- All smoke tests pass
- No errors or crashes
- Features work as expected

### Step 9.3: Performance Spot Checks (10 minutes)

```powershell
# Measure API response times
$endpoints = @(
    "$($outputs.backendUrl.value)/api/health/",
    "$($outputs.backendUrl.value)/api/clients/",
    "$($outputs.backendUrl.value)/api/analytics/dashboard/"
)

foreach ($endpoint in $endpoints) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    Invoke-RestMethod -Uri $endpoint -ErrorAction SilentlyContinue
    $sw.Stop()
    Write-Host "$endpoint - Response Time: $($sw.ElapsedMilliseconds)ms" -ForegroundColor Cyan
}
```

**Expected Response Times:**
- Health check: < 200ms
- Clients list: < 500ms
- Dashboard analytics: < 1000ms (first load), < 200ms (cached)

**Validation:**
- All response times within acceptable range
- No timeouts
- Caching working correctly

### Step 9.4: Security Validation (10 minutes)

**Check 1: HTTPS Enforcement**
```powershell
# Test HTTP redirect to HTTPS
$httpUrl = $outputs.frontendUrl.value -replace "https://", "http://"
Invoke-WebRequest -Uri $httpUrl -MaximumRedirection 0

# Should return 301/302 redirect to HTTPS
```

**Check 2: Security Headers**
```powershell
$response = Invoke-WebRequest -Uri $outputs.frontendUrl.value
$headers = $response.Headers

Write-Host "=== Security Headers ===" -ForegroundColor Cyan
Write-Host "Strict-Transport-Security: $($headers['Strict-Transport-Security'])"
Write-Host "X-Content-Type-Options: $($headers['X-Content-Type-Options'])"
Write-Host "X-Frame-Options: $($headers['X-Frame-Options'])"
Write-Host "Content-Security-Policy: $($headers['Content-Security-Policy'])"
```

**Expected Headers:**
- `Strict-Transport-Security`: max-age=31536000
- `X-Content-Type-Options`: nosniff
- `X-Frame-Options`: DENY or SAMEORIGIN
- `Content-Security-Policy`: (should exist)

**Check 3: Authentication Required**
```powershell
# Try accessing protected endpoint without token
try {
    Invoke-RestMethod -Uri "$($outputs.backendUrl.value)/api/clients/"
} catch {
    Write-Host "✅ Protected endpoint requires authentication: $_" -ForegroundColor Green
}
```

**Validation:**
- HTTPS enforced
- Security headers present
- Authentication required for protected endpoints
- No sensitive data exposed in errors

---

## PHASE 10: GO-LIVE & MONITORING

**Estimated Time:** 24 hours (intensive monitoring)
**Owner:** Full Team on Rotation

### Step 10.1: Final Go/No-Go Decision (30 minutes)

**Checklist before going live:**

- [ ] All infrastructure deployed successfully
- [ ] All secrets configured correctly
- [ ] Database migrated with no errors
- [ ] Backend application running
- [ ] Frontend application running
- [ ] Celery workers running
- [ ] All smoke tests passing
- [ ] Performance within acceptable range
- [ ] Security validations passing
- [ ] Monitoring and alerts configured
- [ ] Team trained and ready
- [ ] Rollback plan documented
- [ ] Stakeholders notified

**If any item is NOT checked:**
- **DO NOT proceed to production**
- Fix the issue first
- Re-run validation tests
- Get approval before proceeding

**If all items checked:**
- Proceed to go-live! 🚀

### Step 10.2: Production Go-Live (1 hour)

**10 AM (or your chosen time):**

```powershell
# Final smoke test
Write-Host "Running final pre-launch smoke test..." -ForegroundColor Yellow
# Run smoke tests from Step 9.2

# Enable production traffic
Write-Host "Enabling production traffic..." -ForegroundColor Green

# If using Azure Front Door with custom domain:
# Update DNS CNAME to point to Front Door endpoint

# Monitor initial traffic
Write-Host "Monitoring initial production traffic..." -ForegroundColor Cyan
az monitor app-insights events show `
  --app $appInsightsName `
  --resource-group $resourceGroup `
  --event-types requests `
  --start-time $(Get-Date).AddMinutes(-5).ToString("yyyy-MM-ddTHH:mm:ss") `
  --end-time $(Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
```

**First Hour Actions:**
- Monitor error logs continuously
- Watch Application Insights live metrics
- Check resource usage (CPU, memory)
- Verify alerts are working
- Monitor first user logins
- Watch for any anomalies

**Communication:**
- Announce go-live to stakeholders
- Notify support team
- Update status page (if applicable)

### Step 10.3: 24-Hour Intensive Monitoring

**Monitoring Schedule (Team Rotation):**

**Hours 0-4 (DevOps + Backend Lead):**
- Watch error logs every 15 minutes
- Monitor Application Insights dashboard
- Check resource utilization
- Respond to any alerts
- Document any issues

**Hours 4-8 (Frontend Lead + QA):**
- Continue monitoring
- Test user journeys
- Monitor performance metrics
- Check dashboard analytics
- Document user feedback

**Hours 8-16 (Full Team):**
- Business hours monitoring
- User onboarding support
- Performance optimization
- Bug triage and fixes
- Stakeholder updates

**Hours 16-24 (DevOps + On-Call):**
- Evening/night monitoring
- Alert response
- Performance checks
- Prepare 24-hour report

**Monitoring Checklist (Every Hour):**

```powershell
# Automated monitoring script
while ($true) {
    Clear-Host
    Write-Host "=== Production Monitoring - $(Get-Date) ===" -ForegroundColor Cyan

    # 1. Health Check
    try {
        $health = Invoke-RestMethod -Uri "$($outputs.backendUrl.value)/api/health/"
        Write-Host "✅ Health: $($health.status)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Health Check Failed: $_" -ForegroundColor Red
    }

    # 2. Error Count (last hour)
    $errors = az monitor app-insights metrics show `
        --app $appInsightsName `
        --resource-group $resourceGroup `
        --metric "exceptions/count" `
        --start-time $(Get-Date).AddHours(-1).ToString("yyyy-MM-ddTHH:mm:ss") `
        --end-time $(Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") `
        --aggregation count `
        --query "value.timeseries[0].data[0].count" `
        --output tsv

    Write-Host "Errors (last hour): $errors" -ForegroundColor $(if ($errors -gt 5) { "Red" } else { "Green" })

    # 3. Request Count
    $requests = az monitor app-insights metrics show `
        --app $appInsightsName `
        --resource-group $resourceGroup `
        --metric "requests/count" `
        --start-time $(Get-Date).AddHours(-1).ToString("yyyy-MM-ddTHH:mm:ss") `
        --end-time $(Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") `
        --aggregation count `
        --query "value.timeseries[0].data[0].count" `
        --output tsv

    Write-Host "Requests (last hour): $requests" -ForegroundColor Green

    # 4. Average Response Time
    $responseTime = az monitor app-insights metrics show `
        --app $appInsightsName `
        --resource-group $resourceGroup `
        --metric "requests/duration" `
        --start-time $(Get-Date).AddHours(-1).ToString("yyyy-MM-ddTHH:mm:ss") `
        --end-time $(Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") `
        --aggregation avg `
        --query "value.timeseries[0].data[0].average" `
        --output tsv

    Write-Host "Avg Response Time: $([math]::Round($responseTime))ms" -ForegroundColor $(if ($responseTime -gt 2000) { "Yellow" } else { "Green" })

    # 5. Resource Usage
    $cpuUsage = az monitor metrics list `
        --resource "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$resourceGroup/providers/Microsoft.Web/sites/$($outputs.backendAppName.value)" `
        --metric "CpuPercentage" `
        --start-time $(Get-Date).AddHours(-1).ToString("yyyy-MM-ddTHH:mm:ss") `
        --end-time $(Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") `
        --aggregation Average `
        --query "value[0].timeseries[0].data[0].average" `
        --output tsv

    Write-Host "CPU Usage: $([math]::Round($cpuUsage))%" -ForegroundColor $(if ($cpuUsage -gt 80) { "Red" } elseif ($cpuUsage -gt 60) { "Yellow" } else { "Green" })

    Write-Host "`nNext check in 60 seconds... (Ctrl+C to stop)" -ForegroundColor Gray
    Start-Sleep -Seconds 60
}
```

**Incident Response:**
- If errors > 10 in 1 hour: Investigate immediately
- If response time > 5 seconds: Check database and Redis
- If CPU > 85%: Consider scaling up
- If any critical alert: Follow incident response plan

### Step 10.4: 24-Hour Report (End of Day 1)

**Generate deployment report:**

```powershell
# Create 24-hour report
$report = @"
# 24-Hour Production Report
**Date:** $(Get-Date -Format "yyyy-MM-dd")
**Environment:** Production
**Report Period:** $(Get-Date -Format "yyyy-MM-dd HH:mm") - $(Get-Date).AddHours(-24) to $(Get-Date)

## Summary
- Deployment Status: Success
- Uptime: XX.XX%
- Total Requests: XXXX
- Total Errors: XX
- Average Response Time: XXXms
- Peak Concurrent Users: XX

## Metrics
- Reports Generated: XX
- Active Clients: XX
- Total Recommendations Processed: XXXX
- Potential Savings Calculated: \$XXX,XXX

## Issues Encountered
1. [Issue description]
2. [Issue description]

## Resolutions
1. [Resolution description]
2. [Resolution description]

## Recommendations
1. [Recommendation]
2. [Recommendation]

## Next Steps
1. Continue monitoring for 7 days
2. Performance optimization as needed
3. User onboarding support
"@

$report | Out-File ".\production-24hour-report.md"
Write-Host "24-hour report saved: production-24hour-report.md" -ForegroundColor Green
```

---

## 🚨 EMERGENCY PROCEDURES

### Rollback Procedure (If Needed)

**If critical issues arise and you need to rollback:**

```powershell
# 1. Stop accepting new traffic
Write-Host "Initiating emergency rollback..." -ForegroundColor Red

# 2. Swap back to staging slot (if using blue-green)
az webapp deployment slot swap `
  --resource-group $resourceGroup `
  --name $outputs.backendAppName.value `
  --slot staging `
  --action swap

# 3. Restore database from backup (if needed)
$backupFile = "database-backup-YYYYMMDD.sql"  # Change to your backup
az postgres flexible-server restore `
  --resource-group $resourceGroup `
  --name $dbServerName `
  --source-server $dbServerName `
  --restore-point-in-time "2025-10-03T10:00:00Z"  # Change to pre-deployment time

# 4. Notify team
Write-Host "Rollback complete. Investigating issues..." -ForegroundColor Yellow

# 5. Create incident report
# Document what went wrong and how to prevent it
```

**Rollback Decision Criteria:**
- Error rate > 20%
- Complete service outage > 5 minutes
- Data corruption detected
- Security vulnerability discovered
- Critical functionality broken

**After Rollback:**
1. Investigate root cause
2. Fix the issue in development
3. Re-test thoroughly
4. Schedule new deployment

---

## ✅ POST-DEPLOYMENT CHECKLIST

### Day 1-7: Daily Checks

- [ ] **Day 1:** Run smoke tests, monitor errors, verify alerts
- [ ] **Day 2:** Check performance metrics, review user feedback
- [ ] **Day 3:** Analyze usage patterns, optimize if needed
- [ ] **Day 4:** Review costs, adjust resources if needed
- [ ] **Day 5:** Security audit, check firewall rules
- [ ] **Day 6:** Backup verification, test restore procedure
- [ ] **Day 7:** Weekly report, plan optimizations

### Week 2-4: Weekly Checks

- [ ] **Week 2:** Performance optimization, user training
- [ ] **Week 3:** Cost optimization, reserved instances
- [ ] **Week 4:** Feature feedback, plan next iteration

---

## 📞 SUPPORT & CONTACTS

### Escalation Matrix

**Level 1: Application Issues**
- Team: DevOps Engineer, Backend Developer
- Response Time: 1 hour
- Contact: devops@yourcompany.com

**Level 2: Infrastructure Issues**
- Team: Cloud Architect, Azure Support
- Response Time: 2 hours
- Contact: cloud-team@yourcompany.com

**Level 3: Critical Outage**
- Team: CTO, Product Manager, Full Engineering Team
- Response Time: 15 minutes
- Contact: emergency@yourcompany.com

### Useful Links

- **Azure Portal:** https://portal.azure.com
- **GitHub Repository:** https://github.com/<your-org>/azure-advisor-reports
- **Application Insights:** https://portal.azure.com/#@<tenant>/resource/subscriptions/<sub-id>/resourceGroups/<rg>/providers/microsoft.insights/components/<app-insights-name>/overview
- **Production Frontend:** https://reports.yourcompany.com
- **Production Backend:** https://api-reports.yourcompany.com
- **Documentation:** D:\Code\Azure Reports\CLAUDE.md

---

## 📝 FINAL NOTES

### Success Criteria

**Deployment is considered successful when:**
- ✅ All infrastructure deployed without errors
- ✅ Application accessible and functional
- ✅ All smoke tests passing
- ✅ Monitoring and alerts working
- ✅ No critical issues in first 24 hours
- ✅ Performance within acceptable range
- ✅ Security validations passing

### Lessons Learned

**After deployment, document:**
- What went well
- What could be improved
- Time estimates vs actuals
- Issues encountered and resolutions
- Process improvements for next time

### Next Steps

**After successful deployment:**
1. User onboarding and training
2. Monitor for 7 days with daily checks
3. Performance optimization based on real usage
4. Cost optimization (reserved instances, auto-shutdown)
5. Plan next feature iteration
6. Collect user feedback
7. Continuous improvement

---

**Document Version:** 1.0
**Last Updated:** October 3, 2025
**Prepared By:** Project Orchestrator (Claude Code)
**Status:** Ready for Production Deployment

**GOOD LUCK WITH YOUR DEPLOYMENT! 🚀**

---

**END OF DEPLOYMENT RUNBOOK**
