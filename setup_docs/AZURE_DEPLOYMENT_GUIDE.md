# Azure Deployment Guide
**Azure Advisor Reports Platform - Infrastructure Deployment**

**Version:** 1.0
**Last Updated:** October 2, 2025
**Target Environment:** Windows PowerShell
**Prerequisites:** Azure CLI, Bicep, Azure Subscription

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure AD App Registration](#azure-ad-app-registration)
3. [Infrastructure Deployment](#infrastructure-deployment)
4. [Post-Deployment Configuration](#post-deployment-configuration)
5. [GitHub Secrets Configuration](#github-secrets-configuration)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

1. **Azure CLI** (v2.50+)
   ```powershell
   # Install Azure CLI
   winget install Microsoft.AzureCLI

   # Verify installation
   az --version

   # Login to Azure
   az login
   ```

2. **Bicep** (Installed automatically with Azure CLI 2.20+)
   ```powershell
   # Verify Bicep installation
   az bicep version

   # Update Bicep to latest version
   az bicep upgrade
   ```

3. **Azure Subscription**
   ```powershell
   # List your subscriptions
   az account list --output table

   # Set active subscription
   az account set --subscription "<subscription-id>"

   # Verify current subscription
   az account show
   ```

### Required Permissions

You need the following Azure RBAC roles:
- **Contributor** or **Owner** on the subscription
- **User Access Administrator** (for RBAC role assignments)
- **Application Administrator** in Azure AD (for app registration)

### Verify Permissions

```powershell
# Check your role assignments
az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) --output table
```

---

## Azure AD App Registration

Before deploying infrastructure, you must register an Azure AD application for authentication.

### Step 1: Create App Registration

```powershell
# Set variables
$appName = "Azure Advisor Reports - Production"
$environment = "prod"  # or "dev", "staging"

# Create the app registration
$app = az ad app create `
  --display-name $appName `
  --sign-in-audience "AzureADMyOrg" `
  --web-redirect-uris "https://your-domain.com" "http://localhost:3000" `
  --enable-id-token-issuance true `
  --query "{appId: appId, objectId: id}" `
  -o json | ConvertFrom-Json

# Save the App ID (Client ID)
$clientId = $app.appId
Write-Host "Client ID: $clientId" -ForegroundColor Green

# Create a client secret
$secret = az ad app credential reset `
  --id $app.appId `
  --append `
  --display-name "Production Secret" `
  --years 2 `
  --query password -o tsv

Write-Host "Client Secret: $secret" -ForegroundColor Yellow
Write-Host "IMPORTANT: Save this secret now! It won't be shown again." -ForegroundColor Red

# Get Tenant ID
$tenantId = az account show --query tenantId -o tsv
Write-Host "Tenant ID: $tenantId" -ForegroundColor Green
```

### Step 2: Configure API Permissions

```powershell
# Add Microsoft Graph permissions
az ad app permission add `
  --id $app.appId `
  --api 00000003-0000-0000-c000-000000000000 `
  --api-permissions e1fe6dd8-ba31-4d61-89e7-88639da4683d=Scope  # User.Read

# Grant admin consent
az ad app permission admin-consent --id $app.appId
```

### Step 3: Update Redirect URIs (After Infrastructure Deployment)

After deploying infrastructure and getting your production URL:

```powershell
# Get the Front Door endpoint from deployment
$frontDoorEndpoint = "https://your-frontdoor-endpoint.azurefd.net"

# Update redirect URIs
az ad app update `
  --id $app.appId `
  --web-redirect-uris $frontDoorEndpoint "http://localhost:3000"
```

### Save These Values

Create a secure note with the following:
```
AZURE_AD_CLIENT_ID: <client-id>
AZURE_AD_CLIENT_SECRET: <client-secret>
AZURE_AD_TENANT_ID: <tenant-id>
```

---

## Infrastructure Deployment

### Step 1: Prepare Deployment Parameters

Create a parameters file for your environment:

```powershell
# Navigate to Bicep directory
cd "D:\Code\Azure Reports\scripts\azure\bicep"

# Create parameters file
$paramsFile = "main.parameters.$environment.json"
```

**Example: `main.parameters.prod.json`**

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environment": {
      "value": "prod"
    },
    "location": {
      "value": "eastus2"
    },
    "resourceGroupPrefix": {
      "value": "rg-azure-advisor"
    },
    "appNamePrefix": {
      "value": "azure-advisor"
    },
    "azureAdClientId": {
      "value": "YOUR_CLIENT_ID"
    },
    "azureAdTenantId": {
      "value": "YOUR_TENANT_ID"
    },
    "azureAdClientSecret": {
      "value": "YOUR_CLIENT_SECRET"
    },
    "customDomain": {
      "value": ""
    },
    "enableAppInsights": {
      "value": true
    },
    "enableFrontDoor": {
      "value": true
    }
  }
}
```

### Step 2: Validate Deployment

```powershell
# Set environment
$environment = "prod"
$location = "eastus2"

# Validate the deployment (dry-run)
az deployment sub validate `
  --name "azure-advisor-$environment-$(Get-Date -Format 'yyyyMMdd-HHmmss')" `
  --location $location `
  --template-file main.bicep `
  --parameters main.parameters.$environment.json
```

### Step 3: Deploy Infrastructure

```powershell
# Deploy to Azure
$deploymentName = "azure-advisor-$environment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

az deployment sub create `
  --name $deploymentName `
  --location $location `
  --template-file main.bicep `
  --parameters main.parameters.$environment.json `
  --verbose

# This will take 15-20 minutes
```

### Step 4: Capture Deployment Outputs

```powershell
# Get deployment outputs
$outputs = az deployment sub show `
  --name $deploymentName `
  --query properties.outputs `
  -o json | ConvertFrom-Json

# Display key outputs
Write-Host "`n=== DEPLOYMENT OUTPUTS ===" -ForegroundColor Cyan
Write-Host "Resource Group: $($outputs.resourceGroupName.value)" -ForegroundColor Green
Write-Host "Backend URL: $($outputs.appServiceBackendUrl.value)" -ForegroundColor Green
Write-Host "Frontend URL: $($outputs.appServiceFrontendUrl.value)" -ForegroundColor Green
Write-Host "Key Vault: $($outputs.keyVaultName.value)" -ForegroundColor Green
Write-Host "Front Door: $($outputs.frontDoorEndpoint.value)" -ForegroundColor Green

# Save outputs to file
$outputs | ConvertTo-Json -Depth 10 | Out-File "deployment-outputs-$environment.json"
Write-Host "`nOutputs saved to: deployment-outputs-$environment.json" -ForegroundColor Yellow
```

---

## Post-Deployment Configuration

### Step 1: Configure Key Vault Secrets

The deployment creates placeholder secrets. You must update them with actual values.

```powershell
# Set variables from deployment outputs
$resourceGroup = $outputs.resourceGroupName.value
$keyVaultName = $outputs.keyVaultName.value
$dbConnectionString = $outputs.postgreSqlConnectionString.value
$redisConnectionString = $outputs.redisConnectionString.value
$storageConnectionString = $outputs.storageAccountConnectionString.value

# Update Database URL secret
az keyvault secret set `
  --vault-name $keyVaultName `
  --name "DATABASE-URL" `
  --value $dbConnectionString

# Update Redis URL secret
az keyvault secret set `
  --vault-name $keyVaultName `
  --name "REDIS-URL" `
  --value $redisConnectionString

# Update Storage Connection String secret
az keyvault secret set `
  --vault-name $keyVaultName `
  --name "AZURE-STORAGE-CONNECTION-STRING" `
  --value $storageConnectionString

# Generate and set Django Secret Key
$djangoSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 50 | ForEach-Object {[char]$_})
az keyvault secret set `
  --vault-name $keyVaultName `
  --name "DJANGO-SECRET-KEY" `
  --value $djangoSecret

# Azure AD secrets should already be set, but verify
az keyvault secret show --vault-name $keyVaultName --name "AZURE-AD-CLIENT-ID" --query value -o tsv
az keyvault secret show --vault-name $keyVaultName --name "AZURE-AD-TENANT-ID" --query value -o tsv

Write-Host "`nKey Vault secrets configured successfully!" -ForegroundColor Green
```

### Step 2: Configure App Service Settings

Update App Service to use Key Vault references:

```powershell
$backendAppName = $outputs.appServiceBackendName.value

# Get Key Vault URI
$keyVaultUri = $outputs.keyVaultUri.value

# Configure App Service to use Key Vault references
az webapp config appsettings set `
  --name $backendAppName `
  --resource-group $resourceGroup `
  --settings `
    "DATABASE_URL=@Microsoft.KeyVault(VaultName=$keyVaultName;SecretName=DATABASE-URL)" `
    "REDIS_URL=@Microsoft.KeyVault(VaultName=$keyVaultName;SecretName=REDIS-URL)" `
    "CELERY_BROKER_URL=@Microsoft.KeyVault(VaultName=$keyVaultName;SecretName=REDIS-URL)" `
    "CELERY_RESULT_BACKEND=@Microsoft.KeyVault(VaultName=$keyVaultName;SecretName=REDIS-URL)" `
    "AZURE_STORAGE_CONNECTION_STRING=@Microsoft.KeyVault(VaultName=$keyVaultName;SecretName=AZURE-STORAGE-CONNECTION-STRING)" `
    "SECRET_KEY=@Microsoft.KeyVault(VaultName=$keyVaultName;SecretName=DJANGO-SECRET-KEY)" `
    "AZURE_CLIENT_ID=@Microsoft.KeyVault(VaultName=$keyVaultName;SecretName=AZURE-AD-CLIENT-ID)" `
    "AZURE_CLIENT_SECRET=@Microsoft.KeyVault(VaultName=$keyVaultName;SecretName=AZURE-AD-CLIENT-SECRET)" `
    "AZURE_TENANT_ID=@Microsoft.KeyVault(VaultName=$keyVaultName;SecretName=AZURE-AD-TENANT-ID)" `
    "DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production" `
    "DEBUG=False" `
    "ALLOWED_HOSTS=$($outputs.appServiceBackendUrl.value),$($outputs.frontDoorEndpoint.value)"

Write-Host "App Service settings configured!" -ForegroundColor Green
```

### Step 3: Run Database Migrations

```powershell
# SSH into backend App Service
az webapp ssh --name $backendAppName --resource-group $resourceGroup

# Once connected, run migrations
python manage.py migrate --no-input
python manage.py collectstatic --no-input
python manage.py createsuperuser

# Exit SSH
exit
```

### Step 4: Restart App Services

```powershell
# Restart backend
az webapp restart --name $backendAppName --resource-group $resourceGroup

# Restart frontend
$frontendAppName = $outputs.appServiceFrontendName.value
az webapp restart --name $frontendAppName --resource-group $resourceGroup

Write-Host "App Services restarted!" -ForegroundColor Green
```

---

## GitHub Secrets Configuration

See **GITHUB_SECRETS_GUIDE.md** for detailed instructions.

Quick setup:

```powershell
# Required secrets for GitHub Actions
gh secret set AZURE_CREDENTIALS_PROD --body @azure-credentials-prod.json
gh secret set DJANGO_SECRET_KEY_PROD --body $djangoSecret
gh secret set AZURE_CLIENT_ID_PROD --body $clientId
gh secret set AZURE_CLIENT_SECRET_PROD --body $secret
gh secret set AZURE_TENANT_ID_PROD --body $tenantId
gh secret set DATABASE_URL_PROD --body $dbConnectionString
gh secret set REDIS_URL_PROD --body $redisConnectionString
gh secret set AZURE_STORAGE_CONNECTION_STRING_PROD --body $storageConnectionString
```

---

## Verification

### Step 1: Health Check

```powershell
# Check backend health
$backendUrl = $outputs.appServiceBackendUrl.value
Invoke-RestMethod -Uri "$backendUrl/api/health/" -Method Get

# Expected output:
# {
#   "status": "healthy",
#   "database": "connected",
#   "redis": "connected",
#   "timestamp": "2025-10-02T12:00:00Z"
# }
```

### Step 2: Verify Front Door

```powershell
# Test Front Door endpoint
$frontDoorUrl = "https://$($outputs.frontDoorEndpoint.value)"
Invoke-WebRequest -Uri $frontDoorUrl -UseBasicParsing | Select-Object StatusCode

# Expected: StatusCode: 200
```

### Step 3: Verify Key Vault Access

```powershell
# Test if App Service can access Key Vault
az webapp log tail --name $backendAppName --resource-group $resourceGroup

# Look for successful Key Vault secret retrieval in logs
```

### Step 4: Verify WAF

```powershell
# Check WAF policy status
az network front-door waf-policy show `
  --name $($outputs.wafPolicyName.value) `
  --resource-group $resourceGroup `
  --query "policySettings.{Mode:mode,State:enabledState}" -o table
```

---

## Troubleshooting

### Issue: Deployment Fails with "Role Assignment Failed"

**Solution:**
```powershell
# Ensure you have User Access Administrator role
az role assignment create `
  --assignee $(az ad signed-in-user show --query id -o tsv) `
  --role "User Access Administrator" `
  --scope "/subscriptions/$(az account show --query id -o tsv)"
```

### Issue: Key Vault Access Denied

**Solution:**
```powershell
# Assign yourself Key Vault Administrator role
az role assignment create `
  --assignee $(az ad signed-in-user show --query id -o tsv) `
  --role "Key Vault Administrator" `
  --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$resourceGroup/providers/Microsoft.KeyVault/vaults/$keyVaultName"
```

### Issue: App Service Can't Access Key Vault

**Solution:**
```powershell
# Verify Managed Identity is enabled
az webapp identity show --name $backendAppName --resource-group $resourceGroup

# Verify role assignment
az role assignment list --assignee $(az webapp identity show --name $backendAppName --resource-group $resourceGroup --query principalId -o tsv) --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$resourceGroup/providers/Microsoft.KeyVault/vaults/$keyVaultName"
```

### Issue: Database Connection Fails

**Solution:**
```powershell
# Check PostgreSQL firewall rules
az postgres flexible-server firewall-rule list `
  --resource-group $resourceGroup `
  --name $($outputs.postgreSqlServerName.value)

# Add firewall rule for your IP if needed
az postgres flexible-server firewall-rule create `
  --resource-group $resourceGroup `
  --name $($outputs.postgreSqlServerName.value) `
  --rule-name "AllowMyIP" `
  --start-ip-address "YOUR_IP" `
  --end-ip-address "YOUR_IP"
```

### Issue: Front Door Not Routing Traffic

**Solution:**
```powershell
# Check origin health
az afd endpoint show `
  --profile-name $($outputs.frontDoorName.value) `
  --endpoint-name "endpoint" `
  --resource-group $resourceGroup

# Purge Front Door cache
az afd endpoint purge `
  --profile-name $($outputs.frontDoorName.value) `
  --endpoint-name "endpoint" `
  --resource-group $resourceGroup `
  --content-paths "/*"
```

### Enable Diagnostic Logging

```powershell
# Create Log Analytics workspace (if not exists)
$workspaceName = "law-azure-advisor-$environment"
az monitor log-analytics workspace create `
  --resource-group $resourceGroup `
  --workspace-name $workspaceName `
  --location $location

# Enable diagnostics for App Service
az monitor diagnostic-settings create `
  --name "AppServiceDiagnostics" `
  --resource $(az webapp show --name $backendAppName --resource-group $resourceGroup --query id -o tsv) `
  --workspace $workspaceName `
  --logs '[{"category":"AppServiceHTTPLogs","enabled":true},{"category":"AppServiceConsoleLogs","enabled":true},{"category":"AppServiceAppLogs","enabled":true}]' `
  --metrics '[{"category":"AllMetrics","enabled":true}]'
```

---

## Cost Estimation

Expected monthly costs for each environment:

### Development Environment
- App Service Plan (B1): ~$13/month
- PostgreSQL (Standard_B2s): ~$30/month
- Redis (Basic C0): ~$16/month
- Storage: ~$5/month
- **Total: ~$64/month**

### Staging Environment
- App Service Plan (S2): ~$149/month
- PostgreSQL (GP D2s v3): ~$120/month
- Redis (Standard C1): ~$75/month
- Storage: ~$10/month
- Front Door (Standard): ~$35/month
- **Total: ~$389/month**

### Production Environment
- App Service Plan (P2v3 x2): ~$440/month
- PostgreSQL (GP D4s v3 with HA): ~$350/month
- Redis (Premium P1): ~$300/month
- Storage: ~$20/month
- Front Door (Premium): ~$110/month
- Application Insights: ~$50/month
- **Total: ~$1,270/month**

---

## Next Steps

1. **Configure Custom Domain** (if applicable)
2. **Setup SSL Certificates**
3. **Configure Monitoring Dashboards**
4. **Setup Alerting Rules**
5. **Deploy Application Code via GitHub Actions**
6. **Run User Acceptance Testing**
7. **Create Backup and Disaster Recovery Plan**

---

## Support

For issues:
1. Check Azure Portal for resource status
2. Review Application Insights logs
3. Check App Service logs: `az webapp log tail`
4. Consult **TROUBLESHOOTING.md**
5. Contact Azure Support if infrastructure issues persist

---

**Document Version:** 1.0
**Last Updated:** October 2, 2025
**Maintained By:** DevOps Team
