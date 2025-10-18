# Production Deployment Guide
## Azure Advisor Reports Platform

**Document Version:** 1.0
**Last Updated:** October 4, 2025
**Platform:** Windows PowerShell
**Target Environment:** Microsoft Azure

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Setup](#pre-deployment-setup)
3. [Azure Infrastructure Deployment](#azure-infrastructure-deployment)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Health Checks & Verification](#health-checks--verification)
8. [Rollback Procedures](#rollback-procedures)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software (Windows)

```powershell
# Verify installations
python --version      # Should be 3.11+
node --version        # Should be 18+
docker --version      # Docker Desktop for Windows
az --version          # Azure CLI 2.50+
git --version         # Git for Windows 2.40+

# If missing, install:
# Python: https://www.python.org/downloads/
# Node.js: https://nodejs.org/
# Docker Desktop: https://www.docker.com/products/docker-desktop/
# Azure CLI: https://aka.ms/installazurecliwindows
# Git: https://git-scm.com/download/win
```

### Required Access & Permissions

- [ ] Azure subscription with Owner or Contributor role
- [ ] Azure AD permissions to create App Registrations
- [ ] GitHub repository access (for CI/CD)
- [ ] Production environment variables documented
- [ ] On-call team notified of deployment window

### Required Documents

- [ ] `.env.production.template` filled with actual values → `.env.production`
- [ ] `SECURITY_CHECKLIST.md` reviewed and signed off
- [ ] All Azure resource names documented
- [ ] Disaster recovery plan documented

---

## Pre-Deployment Setup

### Step 1: Azure CLI Login

```powershell
# Login to Azure
az login

# Verify correct subscription
az account show

# Set subscription (if you have multiple)
az account set --subscription "<subscription-id>"

# Verify
az account list --output table
```

### Step 2: Create Azure Resource Group

```powershell
# Define variables
$resourceGroup = "rg-azure-advisor-reports-prod"
$location = "eastus2"

# Create resource group
az group create `
    --name $resourceGroup `
    --location $location `
    --tags Environment=Production Project=AzureAdvisorReports

# Verify
az group show --name $resourceGroup --output table
```

### Step 3: Generate Strong SECRET_KEY

```powershell
# Generate Django SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Save this in .env.production under SECRET_KEY=
# Example output: django-insecure-abc123xyz456...
```

---

## Azure Infrastructure Deployment

### Option A: Deploy with Bicep (Recommended)

```powershell
# Navigate to Bicep templates directory
cd scripts\azure\bicep

# Validate Bicep template
az bicep build --file main.bicep

# Create parameter file (use provided templates in AZURE_DEPLOYMENT_GUIDE.md)
# Edit parameters.prod.json with your values

# Preview changes (What-If analysis)
az deployment sub create `
    --location eastus2 `
    --template-file main.bicep `
    --parameters parameters.prod.json `
    --what-if

# Deploy infrastructure
az deployment sub create `
    --location eastus2 `
    --template-file main.bicep `
    --parameters parameters.prod.json `
    --name "azure-advisor-reports-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# Monitor deployment
az deployment sub show `
    --name "azure-advisor-reports-<timestamp>" `
    --query "properties.provisioningState"

# Deployment takes approximately 15-20 minutes
```

### Option B: Manual Azure Resource Creation

<details>
<summary><strong>Click to expand manual deployment steps</strong></summary>

#### PostgreSQL Database

```powershell
$postgresServer = "psql-advisor-prod"
$dbName = "azure_advisor_reports_prod"
$dbUser = "appuser"
$dbPassword = "<generate-strong-password>"  # Use a password manager

# Create PostgreSQL server
az postgres flexible-server create `
    --resource-group $resourceGroup `
    --name $postgresServer `
    --location $location `
    --admin-user $dbUser `
    --admin-password $dbPassword `
    --sku-name Standard_D2s_v3 `
    --tier GeneralPurpose `
    --storage-size 128 `
    --version 15 `
    --public-access 0.0.0.0 `
    --high-availability Disabled `
    --backup-retention 14

# Create database
az postgres flexible-server db create `
    --resource-group $resourceGroup `
    --server-name $postgresServer `
    --database-name $dbName

# Configure firewall (allow Azure services)
az postgres flexible-server firewall-rule create `
    --resource-group $resourceGroup `
    --name $postgresServer `
    --rule-name AllowAzureServices `
    --start-ip-address 0.0.0.0 `
    --end-ip-address 0.0.0.0

# Get connection string
$dbHost = "$postgresServer.postgres.database.azure.com"
Write-Host "Database Connection String:"
Write-Host "DB_HOST=$dbHost"
Write-Host "DB_USER=$dbUser"
Write-Host "DB_NAME=$dbName"
```

#### Redis Cache

```powershell
$redisName = "redis-advisor-prod"

# Create Redis cache
az redis create `
    --resource-group $resourceGroup `
    --name $redisName `
    --location $location `
    --sku Standard `
    --vm-size C2 `
    --enable-non-ssl-port false

# Get Redis connection details
$redisKey = az redis list-keys --resource-group $resourceGroup --name $redisName --query primaryKey -o tsv
$redisHost = az redis show --resource-group $resourceGroup --name $redisName --query hostName -o tsv

Write-Host "Redis Connection:"
Write-Host "REDIS_URL=rediss://:$redisKey@${redisHost}:6380"
```

#### Storage Account

```powershell
$storageName = "stadvisorprod"  # Must be globally unique

# Create storage account
az storage account create `
    --resource-group $resourceGroup `
    --name $storageName `
    --location $location `
    --sku Standard_LRS `
    --kind StorageV2 `
    --access-tier Hot `
    --https-only true `
    --min-tls-version TLS1_2

# Get storage account key
$storageKey = az storage account keys list `
    --resource-group $resourceGroup `
    --account-name $storageName `
    --query "[0].value" -o tsv

# Create blob containers
$containers = @("static", "csv-uploads", "reports-html", "reports-pdf")
foreach ($container in $containers) {
    az storage container create `
        --name $container `
        --account-name $storageName `
        --account-key $storageKey `
        --public-access off
}

Write-Host "Storage Account:"
Write-Host "AZURE_STORAGE_ACCOUNT_NAME=$storageName"
Write-Host "AZURE_STORAGE_ACCOUNT_KEY=$storageKey"
```

#### App Service Plans

```powershell
# Backend App Service Plan (P2v3)
az appservice plan create `
    --resource-group $resourceGroup `
    --name "asp-advisor-backend-prod" `
    --location $location `
    --is-linux `
    --sku P2V3 `
    --number-of-workers 2

# Frontend App Service Plan (P1v3)
az appservice plan create `
    --resource-group $resourceGroup `
    --name "asp-advisor-frontend-prod" `
    --location $location `
    --is-linux `
    --sku P1V3 `
    --number-of-workers 1
```

#### Application Insights

```powershell
$appInsightsName = "appi-advisor-prod"

# Create Log Analytics Workspace first
az monitor log-analytics workspace create `
    --resource-group $resourceGroup `
    --workspace-name "law-advisor-prod" `
    --location $location

$workspaceId = az monitor log-analytics workspace show `
    --resource-group $resourceGroup `
    --workspace-name "law-advisor-prod" `
    --query id -o tsv

# Create Application Insights
az monitor app-insights component create `
    --resource-group $resourceGroup `
    --app $appInsightsName `
    --location $location `
    --kind web `
    --application-type web `
    --workspace $workspaceId

# Get connection string
$appInsightsConnString = az monitor app-insights component show `
    --resource-group $resourceGroup `
    --app $appInsightsName `
    --query connectionString -o tsv

Write-Host "Application Insights:"
Write-Host "APPLICATIONINSIGHTS_CONNECTION_STRING=$appInsightsConnString"
```

</details>

---

## Backend Deployment

### Step 1: Build Docker Image

```powershell
# Navigate to project root
cd D:\Code\Azure Reports

# Build production Docker image
docker build -f Dockerfile.prod -t azure-advisor-backend:prod .

# Verify image
docker images | Select-String "azure-advisor-backend"
```

### Step 2: Create Azure Container Registry (ACR)

```powershell
$acrName = "acradvisorprod"  # Must be globally unique

# Create ACR
az acr create `
    --resource-group $resourceGroup `
    --name $acrName `
    --sku Standard `
    --admin-enabled true `
    --location $location

# Get ACR credentials
$acrUsername = az acr credential show `
    --name $acrName `
    --query username -o tsv

$acrPassword = az acr credential show `
    --name $acrName `
    --query "passwords[0].value" -o tsv

Write-Host "ACR Credentials:"
Write-Host "Registry: ${acrName}.azurecr.io"
Write-Host "Username: $acrUsername"
```

### Step 3: Push Docker Image to ACR

```powershell
# Login to ACR
az acr login --name $acrName

# Tag image
docker tag azure-advisor-backend:prod ${acrName}.azurecr.io/azure-advisor-backend:latest
docker tag azure-advisor-backend:prod ${acrName}.azurecr.io/azure-advisor-backend:v1.0.0

# Push image
docker push ${acrName}.azurecr.io/azure-advisor-backend:latest
docker push ${acrName}.azurecr.io/azure-advisor-backend:v1.0.0

# Verify
az acr repository list --name $acrName --output table
```

### Step 4: Create Backend App Service

```powershell
$backendAppName = "app-advisor-backend-prod"

# Create Web App with Docker container
az webapp create `
    --resource-group $resourceGroup `
    --plan "asp-advisor-backend-prod" `
    --name $backendAppName `
    --deployment-container-image-name "${acrName}.azurecr.io/azure-advisor-backend:latest"

# Configure ACR credentials
az webapp config container set `
    --resource-group $resourceGroup `
    --name $backendAppName `
    --docker-custom-image-name "${acrName}.azurecr.io/azure-advisor-backend:latest" `
    --docker-registry-server-url "https://${acrName}.azurecr.io" `
    --docker-registry-server-user $acrUsername `
    --docker-registry-server-password $acrPassword

# Enable container logging
az webapp log config `
    --resource-group $resourceGroup `
    --name $backendAppName `
    --docker-container-logging filesystem

Write-Host "Backend URL: https://${backendAppName}.azurewebsites.net"
```

### Step 5: Configure Environment Variables

```powershell
# IMPORTANT: Set all environment variables from .env.production

# Critical settings
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $backendAppName `
    --settings `
        DJANGO_ENVIRONMENT=production `
        DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production `
        DEBUG=False `
        SECRET_KEY="<your-secret-key>" `
        ALLOWED_HOSTS="${backendAppName}.azurewebsites.net" `
        CORS_ALLOWED_ORIGINS="https://app-advisor-frontend-prod.azurewebsites.net"

# Database configuration
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $backendAppName `
    --settings `
        DB_NAME="$dbName" `
        DB_USER="$dbUser" `
        DB_PASSWORD="$dbPassword" `
        DB_HOST="$dbHost" `
        DB_PORT="5432"

# Redis configuration
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $backendAppName `
    --settings `
        REDIS_URL="rediss://:$redisKey@${redisHost}:6380" `
        REDIS_PASSWORD="$redisKey"

# Azure Storage configuration
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $backendAppName `
    --settings `
        AZURE_STORAGE_ACCOUNT_NAME="$storageName" `
        AZURE_STORAGE_ACCOUNT_KEY="$storageKey" `
        AZURE_STORAGE_CONTAINER="static"

# Application Insights
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $backendAppName `
    --settings `
        APPLICATIONINSIGHTS_CONNECTION_STRING="$appInsightsConnString"

# Azure AD (you need to set these after creating App Registration)
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $backendAppName `
    --settings `
        AZURE_CLIENT_ID="<your-client-id>" `
        AZURE_CLIENT_SECRET="<your-client-secret>" `
        AZURE_TENANT_ID="<your-tenant-id>" `
        AZURE_REDIRECT_URI="https://app-advisor-frontend-prod.azurewebsites.net"

# Gunicorn configuration
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $backendAppName `
    --settings `
        GUNICORN_WORKERS="4" `
        GUNICORN_THREADS="2" `
        GUNICORN_TIMEOUT="120"
```

### Step 6: Run Database Migrations

```powershell
# SSH into the container
az webapp ssh --resource-group $resourceGroup --name $backendAppName

# Inside the container:
python manage.py migrate
python manage.py collectstatic --no-input
python manage.py createsuperuser  # Create admin user

# Exit
exit
```

---

## Frontend Deployment

### Step 1: Configure Production Environment

```powershell
# Navigate to frontend directory
cd frontend

# Create .env.production file
@"
REACT_APP_API_URL=https://${backendAppName}.azurewebsites.net
REACT_APP_AZURE_CLIENT_ID=<your-client-id>
REACT_APP_AZURE_TENANT_ID=<your-tenant-id>
REACT_APP_AZURE_REDIRECT_URI=https://app-advisor-frontend-prod.azurewebsites.net
REACT_APP_ENVIRONMENT=production
"@ | Out-File -FilePath .env.production -Encoding utf8
```

### Step 2: Build Frontend

```powershell
# Install dependencies
npm ci

# Build for production
npm run build

# Verify build
Test-Path build\index.html  # Should return True
```

### Step 3: Deploy to Azure App Service

```powershell
$frontendAppName = "app-advisor-frontend-prod"

# Create Web App (Node.js runtime)
az webapp create `
    --resource-group $resourceGroup `
    --plan "asp-advisor-frontend-prod" `
    --name $frontendAppName `
    --runtime "NODE:18-lts"

# Deploy build folder
cd build
Compress-Archive -Path * -DestinationPath ..\build.zip -Force
cd ..

az webapp deployment source config-zip `
    --resource-group $resourceGroup `
    --name $frontendAppName `
    --src build.zip

# Configure startup command (serve static files)
az webapp config set `
    --resource-group $resourceGroup `
    --name $frontendAppName `
    --startup-file "npx serve -s . -l 8080"

# Enable HTTPS only
az webapp update `
    --resource-group $resourceGroup `
    --name $frontendAppName `
    --https-only true

Write-Host "Frontend URL: https://${frontendAppName}.azurewebsites.net"
```

---

## Post-Deployment Configuration

### Step 1: Configure Custom Domains (Optional)

```powershell
# Add custom domain
az webapp config hostname add `
    --resource-group $resourceGroup `
    --webapp-name $backendAppName `
    --hostname api.yourdomain.com

# Bind SSL certificate (using App Service Managed Certificate)
az webapp config ssl bind `
    --resource-group $resourceGroup `
    --name $backendAppName `
    --certificate-thumbprint auto `
    --ssl-type SNI

# Repeat for frontend
az webapp config hostname add `
    --resource-group $resourceGroup `
    --webapp-name $frontendAppName `
    --hostname www.yourdomain.com
```

### Step 2: Configure Auto-Scaling

```powershell
# Backend auto-scaling (2-10 instances)
az monitor autoscale create `
    --resource-group $resourceGroup `
    --resource "/subscriptions/<subscription-id>/resourceGroups/$resourceGroup/providers/Microsoft.Web/serverFarms/asp-advisor-backend-prod" `
    --name "backend-autoscale" `
    --min-count 2 `
    --max-count 10 `
    --count 2

az monitor autoscale rule create `
    --resource-group $resourceGroup `
    --autoscale-name "backend-autoscale" `
    --condition "Percentage CPU > 70 avg 5m" `
    --scale out 1

az monitor autoscale rule create `
    --resource-group $resourceGroup `
    --autoscale-name "backend-autoscale" `
    --condition "Percentage CPU < 30 avg 5m" `
    --scale in 1
```

### Step 3: Configure Alerts

```powershell
# Create action group for notifications
az monitor action-group create `
    --resource-group $resourceGroup `
    --name "ag-advisor-alerts" `
    --short-name "advisoralert" `
    --email-receiver name="DevTeam" email="devteam@yourdomain.com"

# Alert on high error rate
az monitor metrics alert create `
    --resource-group $resourceGroup `
    --name "backend-high-errors" `
    --scopes "/subscriptions/<subscription-id>/resourceGroups/$resourceGroup/providers/Microsoft.Web/sites/$backendAppName" `
    --condition "avg Http5xx > 10" `
    --window-size 5m `
    --evaluation-frequency 1m `
    --action "ag-advisor-alerts"
```

---

## Health Checks & Verification

### Step 1: Verify Backend Health

```powershell
# Test health check endpoint
$backendUrl = "https://${backendAppName}.azurewebsites.net"
Invoke-RestMethod -Uri "$backendUrl/api/health/" -Method Get

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "redis": "connected",
#   "timestamp": "2025-10-04T12:00:00Z"
# }
```

### Step 2: Smoke Test Critical Flows

```powershell
# 1. Test API is responding
Invoke-RestMethod -Uri "$backendUrl/api/" -Method Get

# 2. Test authentication endpoint (should return 401 unauthorized)
try {
    Invoke-RestMethod -Uri "$backendUrl/api/clients/" -Method Get
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "✅ Authentication working (expected 401)"
    }
}

# 3. Test frontend loads
$frontendUrl = "https://${frontendAppName}.azurewebsites.net"
$response = Invoke-WebRequest -Uri $frontendUrl -UseBasicParsing
if ($response.StatusCode -eq 200) {
    Write-Host "✅ Frontend loaded successfully"
}
```

### Step 3: Monitor Application Insights

```powershell
# Open Application Insights in browser
Start-Process "https://portal.azure.com/#@/resource/subscriptions/<subscription-id>/resourceGroups/$resourceGroup/providers/Microsoft.Insights/components/$appInsightsName/overview"

# Monitor for:
# - No 5xx errors in last 10 minutes
# - Response times < 2 seconds
# - Successful requests > 95%
```

---

## Rollback Procedures

### Emergency Rollback to Previous Version

```powershell
# Option 1: Rollback Docker image to previous tag
az webapp config container set `
    --resource-group $resourceGroup `
    --name $backendAppName `
    --docker-custom-image-name "${acrName}.azurecr.io/azure-advisor-backend:v0.9.0"

# Option 2: Use App Service deployment slots (if configured)
az webapp deployment slot swap `
    --resource-group $resourceGroup `
    --name $backendAppName `
    --slot staging `
    --target-slot production

# Verify rollback
Invoke-RestMethod -Uri "$backendUrl/api/health/"

# Monitor Application Insights for 15 minutes
```

### Database Rollback (if needed)

```powershell
# Restore database from backup
$backupTime = "2025-10-03T23:00:00Z"  # Use appropriate timestamp

az postgres flexible-server restore `
    --resource-group $resourceGroup `
    --name "$postgresServer-restored" `
    --source-server $postgresServer `
    --restore-time $backupTime

# Point application to restored database (requires app restart)
```

---

## Troubleshooting

### Issue: Container won't start

```powershell
# Check container logs
az webapp log tail --resource-group $resourceGroup --name $backendAppName

# Common issues:
# 1. Missing environment variables
# 2. Database connection failure
# 3. Redis connection failure

# Verify environment variables
az webapp config appsettings list --resource-group $resourceGroup --name $backendAppName --output table
```

### Issue: Database connection errors

```powershell
# Test database connectivity
az postgres flexible-server show `
    --resource-group $resourceGroup `
    --name $postgresServer

# Check firewall rules
az postgres flexible-server firewall-rule list `
    --resource-group $resourceGroup `
    --name $postgresServer

# Add App Service outbound IPs to firewall
$outboundIps = az webapp show `
    --resource-group $resourceGroup `
    --name $backendAppName `
    --query "outboundIpAddresses" -o tsv

# Split and add each IP
$outboundIps -split ',' | ForEach-Object {
    $ip = $_.Trim()
    az postgres flexible-server firewall-rule create `
        --resource-group $resourceGroup `
        --name $postgresServer `
        --rule-name "AppService-$ip" `
        --start-ip-address $ip `
        --end-ip-address $ip
}
```

### Issue: 502 Bad Gateway

```powershell
# Check if container is running
az webapp show --resource-group $resourceGroup --name $backendAppName --query "state"

# Restart app
az webapp restart --resource-group $resourceGroup --name $backendAppName

# Check logs
az webapp log tail --resource-group $resourceGroup --name $backendAppName
```

### Issue: Frontend not loading

```powershell
# Check deployment status
az webapp deployment list-publishing-profiles `
    --resource-group $resourceGroup `
    --name $frontendAppName

# Redeploy
az webapp deployment source config-zip `
    --resource-group $resourceGroup `
    --name $frontendAppName `
    --src build.zip
```

---

## Post-Deployment Checklist

- [ ] Backend health check endpoint returns 200 OK
- [ ] Frontend loads without errors
- [ ] Database migrations completed successfully
- [ ] Static files served correctly
- [ ] Authentication flow working (Azure AD login)
- [ ] API endpoints responding correctly
- [ ] File upload working (CSV upload test)
- [ ] Report generation working (end-to-end test)
- [ ] Application Insights receiving telemetry
- [ ] Error alerts configured and tested
- [ ] Auto-scaling rules configured
- [ ] Backup and restore tested
- [ ] Security checklist completed
- [ ] On-call team notified of successful deployment
- [ ] Documentation updated with production URLs
- [ ] Monitoring dashboard created

---

## Success Criteria

Deployment is considered successful when:

1. ✅ All health checks pass
2. ✅ Zero 5xx errors in first 30 minutes
3. ✅ Response times < 2 seconds
4. ✅ End-to-end user flow works (login → upload CSV → generate report → download)
5. ✅ All Azure resources in "Succeeded" state
6. ✅ Application Insights showing telemetry
7. ✅ Security checklist 100% complete

---

## Next Steps After Deployment

1. Monitor Application Insights for 24 hours
2. Schedule user training sessions
3. Create operational runbook
4. Document any issues encountered
5. Plan first maintenance window
6. Schedule security audit
7. Set up regular backups verification

---

## Support Contacts

- **On-Call Engineer:** [Contact info]
- **DevOps Lead:** [Contact info]
- **Database Admin:** [Contact info]
- **Security Team:** [Contact info]

---

**End of Production Deployment Guide**

*For additional help, see TROUBLESHOOTING.md and ADMIN_GUIDE.md*
