# Azure Services Setup Guide
## Azure Advisor Reports Platform

**Last Updated:** October 1, 2025
**Version:** 1.0
**Target Audience:** DevOps Engineers, Cloud Administrators

---

## Table of Contents

1. [Overview](#overview)
2. [Azure Active Directory Setup](#azure-active-directory-setup)
3. [Azure Blob Storage Setup](#azure-blob-storage-setup)
4. [Azure Database for PostgreSQL](#azure-database-for-postgresql)
5. [Azure Cache for Redis](#azure-cache-for-redis)
6. [Azure App Service](#azure-app-service)
7. [Application Insights](#application-insights)
8. [Cost Estimation](#cost-estimation)
9. [Security Best Practices](#security-best-practices)
10. [Connection Strings Reference](#connection-strings-reference)

---

## Overview

### Required Azure Services

| Service | Purpose | Tier | Required |
|---------|---------|------|----------|
| **Azure Active Directory** | Authentication | Free/P1 | Yes |
| **Azure Blob Storage** | File storage (CSV, Reports) | Standard | Yes |
| **Azure Database for PostgreSQL** | Primary database | General Purpose | Yes |
| **Azure Cache for Redis** | Caching & Celery broker | Standard | Yes |
| **Azure App Service** | Backend hosting | Premium v3 | Yes |
| **Azure App Service** | Frontend hosting | Premium v3 | Yes |
| **Application Insights** | Monitoring & logging | Pay-as-you-go | Recommended |
| **Azure Front Door** | CDN & WAF | Premium | Optional |

### Prerequisites

Before you begin, ensure you have:
- Azure subscription with Owner or Contributor role
- Azure CLI installed and configured (`az login`)
- PowerShell 7+ or Bash terminal
- Access to create Azure AD app registrations

---

## Azure Active Directory Setup

### Step 1: Create Azure AD App Registration

#### Using Azure Portal

1. **Navigate to Azure Active Directory**
   - Go to [Azure Portal](https://portal.azure.com)
   - Search for "Azure Active Directory"
   - Click on "App registrations" in the left menu

2. **Create New Registration**
   - Click "+ New registration"
   - Fill in the following:
     - **Name**: `Azure Advisor Reports - Production`
     - **Supported account types**: `Accounts in this organizational directory only (Single tenant)`
     - **Redirect URI**:
       - Platform: `Single-page application (SPA)`
       - URI: `https://yourdomain.com` (update with your actual domain)
       - For development: `http://localhost:3000`
   - Click "Register"

3. **Note the Application Details**
   - After registration, note the following:
     - **Application (client) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
     - **Directory (tenant) ID**: `yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy`
   - Save these values for configuration

4. **Configure API Permissions**
   - Click "API permissions" in the left menu
   - Click "+ Add a permission"
   - Select "Microsoft Graph"
   - Select "Delegated permissions"
   - Add the following permissions:
     - `User.Read` - Read user profile
     - `openid` - OpenID Connect sign-in
     - `profile` - View user's basic profile
     - `email` - View user's email address
   - Click "Grant admin consent" (requires admin privileges)

5. **Create Client Secret (for backend API)**
   - Click "Certificates & secrets" in the left menu
   - Click "+ New client secret"
   - Description: `Backend API Secret - Production`
   - Expires: `24 months` (recommended to rotate regularly)
   - Click "Add"
   - **IMPORTANT**: Copy the secret value immediately (you can't view it again)
   - Save as: `AZURE_CLIENT_SECRET`

6. **Configure Authentication**
   - Click "Authentication" in the left menu
   - Under "Implicit grant and hybrid flows":
     - ✅ Check "Access tokens (used for implicit flows)"
     - ✅ Check "ID tokens (used for implicit and hybrid flows)"
   - Under "Advanced settings":
     - Allow public client flows: `No`
   - Click "Save"

7. **Configure Token Configuration (Optional)**
   - Click "Token configuration" in the left menu
   - Add optional claims as needed:
     - `email`, `family_name`, `given_name`, `upn`

#### Using Azure CLI

```powershell
# Login to Azure
az login

# Set subscription (if you have multiple)
az account set --subscription "Your Subscription Name"

# Create Azure AD app registration
az ad app create `
  --display-name "Azure Advisor Reports - Production" `
  --sign-in-audience "AzureADMyOrg" `
  --web-redirect-uris "https://yourdomain.com" "http://localhost:3000" `
  --enable-id-token-issuance true `
  --enable-access-token-issuance true

# Note the appId from output (this is your AZURE_CLIENT_ID)

# Get tenant ID
az account show --query tenantId -o tsv

# Create service principal
az ad sp create --id <APP_ID>

# Add Microsoft Graph permissions
az ad app permission add `
  --id <APP_ID> `
  --api 00000003-0000-0000-c000-000000000000 `
  --api-permissions e1fe6dd8-ba31-4d61-89e7-88639da4683d=Scope

# Grant admin consent (requires Global Admin)
az ad app permission admin-consent --id <APP_ID>

# Create client secret
az ad app credential reset --id <APP_ID> --append
# Note the password from output (this is your AZURE_CLIENT_SECRET)
```

### Step 2: Configure Environment Variables

Add to your `.env` file:

```env
# Azure AD Configuration
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_SECRET=your-client-secret-value
AZURE_TENANT_ID=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
AZURE_REDIRECT_URI=https://yourdomain.com
AZURE_AUTHORITY=https://login.microsoftonline.com/yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
```

### Step 3: Test Authentication

```powershell
# Test with MSAL
python -c "
from msal import ConfidentialClientApplication
import os
from dotenv import load_dotenv

load_dotenv()

app = ConfidentialClientApplication(
    os.getenv('AZURE_CLIENT_ID'),
    authority=os.getenv('AZURE_AUTHORITY'),
    client_credential=os.getenv('AZURE_CLIENT_SECRET')
)

result = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])
print('Success!' if 'access_token' in result else 'Failed!')
print(result)
"
```

---

## Azure Blob Storage Setup

### Step 1: Create Storage Account

#### Using Azure Portal

1. **Navigate to Storage Accounts**
   - Go to [Azure Portal](https://portal.azure.com)
   - Search for "Storage accounts"
   - Click "+ Create"

2. **Configure Basic Settings**
   - **Resource group**: Create new or select existing (e.g., `rg-azure-advisor-reports-prod`)
   - **Storage account name**: `stadvisorprod` (must be globally unique, 3-24 lowercase letters/numbers)
   - **Region**: `East US 2` (or your preferred region)
   - **Performance**: `Standard`
   - **Redundancy**: `Locally-redundant storage (LRS)` (for cost savings) or `Geo-redundant storage (GRS)` (for high availability)

3. **Advanced Settings**
   - **Require secure transfer for REST API operations**: `Enabled`
   - **Enable blob public access**: `Disabled` (for security)
   - **Blob storage access tier**: `Hot`
   - **Enable blob versioning**: `Enabled` (recommended)
   - **Enable soft delete for blobs**: `Enabled` - 7 days retention

4. **Networking**
   - **Network connectivity**: `Public endpoint (all networks)` (or restrict to specific VNets)
   - **Require secure transfer**: `Enabled`

5. **Data Protection**
   - **Enable soft delete for blobs**: `Enabled` - 7 days
   - **Enable soft delete for containers**: `Enabled` - 7 days
   - **Enable versioning for blobs**: `Enabled`

6. **Review + Create**
   - Review settings
   - Click "Create"

#### Using Azure CLI

```powershell
# Set variables
$RESOURCE_GROUP = "rg-azure-advisor-reports-prod"
$LOCATION = "eastus2"
$STORAGE_ACCOUNT = "stadvisorprod"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account
az storage account create `
  --name $STORAGE_ACCOUNT `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --sku Standard_LRS `
  --kind StorageV2 `
  --access-tier Hot `
  --https-only true `
  --allow-blob-public-access false `
  --min-tls-version TLS1_2

# Enable blob versioning
az storage account blob-service-properties update `
  --account-name $STORAGE_ACCOUNT `
  --enable-versioning true

# Enable soft delete
az storage account blob-service-properties update `
  --account-name $STORAGE_ACCOUNT `
  --enable-delete-retention true `
  --delete-retention-days 7
```

### Step 2: Create Blob Containers

#### Using Azure Portal

1. **Navigate to Storage Account**
   - Go to your newly created storage account
   - Click "Containers" in the left menu

2. **Create Containers**
   - Click "+ Container" for each:

     **Container 1: csv-uploads**
     - Name: `csv-uploads`
     - Public access level: `Private (no anonymous access)`

     **Container 2: reports-html**
     - Name: `reports-html`
     - Public access level: `Private (no anonymous access)`

     **Container 3: reports-pdf**
     - Name: `reports-pdf`
     - Public access level: `Private (no anonymous access)`

     **Container 4: static-assets** (optional)
     - Name: `static-assets`
     - Public access level: `Blob (anonymous read access for blobs only)`

#### Using Azure CLI

```powershell
# Get storage account key
$ACCOUNT_KEY = az storage account keys list `
  --account-name $STORAGE_ACCOUNT `
  --resource-group $RESOURCE_GROUP `
  --query "[0].value" -o tsv

# Create containers
az storage container create `
  --name csv-uploads `
  --account-name $STORAGE_ACCOUNT `
  --account-key $ACCOUNT_KEY `
  --public-access off

az storage container create `
  --name reports-html `
  --account-name $STORAGE_ACCOUNT `
  --account-key $ACCOUNT_KEY `
  --public-access off

az storage container create `
  --name reports-pdf `
  --account-name $STORAGE_ACCOUNT `
  --account-key $ACCOUNT_KEY `
  --public-access off

az storage container create `
  --name static-assets `
  --account-name $STORAGE_ACCOUNT `
  --account-key $ACCOUNT_KEY `
  --public-access blob
```

### Step 3: Configure CORS (for frontend access)

#### Using Azure Portal

1. Go to Storage Account → Resource sharing (CORS)
2. Blob service tab
3. Add new CORS rule:
   - **Allowed origins**: `https://yourdomain.com, http://localhost:3000`
   - **Allowed methods**: `GET, POST, PUT, DELETE, OPTIONS`
   - **Allowed headers**: `*`
   - **Exposed headers**: `*`
   - **Max age**: `3600`
4. Click "Save"

#### Using Azure CLI

```powershell
az storage cors add `
  --services b `
  --methods GET POST PUT DELETE OPTIONS `
  --origins "https://yourdomain.com" "http://localhost:3000" `
  --allowed-headers "*" `
  --exposed-headers "*" `
  --max-age 3600 `
  --account-name $STORAGE_ACCOUNT `
  --account-key $ACCOUNT_KEY
```

### Step 4: Get Connection String

#### Using Azure Portal

1. Go to Storage Account → Access keys
2. Click "Show keys"
3. Copy **Connection string** for key1
4. Save as `AZURE_STORAGE_CONNECTION_STRING`

#### Using Azure CLI

```powershell
az storage account show-connection-string `
  --name $STORAGE_ACCOUNT `
  --resource-group $RESOURCE_GROUP `
  --output tsv
```

### Step 5: Configure Environment Variables

```env
# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=stadvisorprod;AccountKey=...;EndpointSuffix=core.windows.net
AZURE_STORAGE_ACCOUNT_NAME=stadvisorprod
AZURE_STORAGE_ACCOUNT_KEY=your-account-key
AZURE_CONTAINER_CSV_UPLOADS=csv-uploads
AZURE_CONTAINER_REPORTS_HTML=reports-html
AZURE_CONTAINER_REPORTS_PDF=reports-pdf
```

---

## Azure Database for PostgreSQL

### Step 1: Create PostgreSQL Server

#### Using Azure Portal

1. **Navigate to Azure Database for PostgreSQL**
   - Search for "Azure Database for PostgreSQL"
   - Click "Create"
   - Select "Flexible server" (recommended)

2. **Basic Configuration**
   - **Resource group**: `rg-azure-advisor-reports-prod`
   - **Server name**: `psql-advisor-prod` (must be globally unique)
   - **Region**: `East US 2`
   - **PostgreSQL version**: `15`
   - **Workload type**: `Production (Medium/Large)`
   - **Compute + storage**: Click "Configure server"
     - **Compute tier**: `General purpose`
     - **Compute size**: `D2s_v3 (2 vCores, 8 GiB memory)`
     - **Storage**: `128 GiB`
     - **IOPS**: `500` (default)
     - Click "Save"

3. **Authentication**
   - **Authentication method**: `PostgreSQL authentication only`
   - **Admin username**: `adminuser`
   - **Password**: Create strong password (save to password manager)

4. **Networking**
   - **Connectivity method**: `Public access (allowed IP addresses)`
   - **Firewall rules**: Add rules for:
     - Your IP: Click "Add current client IP address"
     - Azure services: Check "Allow public access from any Azure service"
   - **SSL enforcement**: `Enabled` (recommended)

5. **High Availability** (optional for production)
   - **Enable high availability**: `Zone redundant`

6. **Backup**
   - **Backup retention period**: `14 days`
   - **Geo-redundant backup**: `Enabled` (for disaster recovery)

7. **Review + Create**

#### Using Azure CLI

```powershell
$DB_SERVER_NAME = "psql-advisor-prod"
$DB_ADMIN_USER = "adminuser"
$DB_ADMIN_PASSWORD = "YourStrongPassword123!"

# Create PostgreSQL flexible server
az postgres flexible-server create `
  --name $DB_SERVER_NAME `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --admin-user $DB_ADMIN_USER `
  --admin-password $DB_ADMIN_PASSWORD `
  --version 15 `
  --sku-name Standard_D2s_v3 `
  --tier GeneralPurpose `
  --storage-size 128 `
  --public-access All `
  --high-availability Enabled

# Create database
az postgres flexible-server db create `
  --resource-group $RESOURCE_GROUP `
  --server-name $DB_SERVER_NAME `
  --database-name azure_advisor_reports_prod

# Add firewall rule for your IP
az postgres flexible-server firewall-rule create `
  --resource-group $RESOURCE_GROUP `
  --name $DB_SERVER_NAME `
  --rule-name AllowMyIP `
  --start-ip-address YOUR_IP `
  --end-ip-address YOUR_IP

# Allow Azure services
az postgres flexible-server firewall-rule create `
  --resource-group $RESOURCE_GROUP `
  --name $DB_SERVER_NAME `
  --rule-name AllowAzureServices `
  --start-ip-address 0.0.0.0 `
  --end-ip-address 0.0.0.0
```

### Step 2: Configure Database

```powershell
# Connect to database
psql "host=psql-advisor-prod.postgres.database.azure.com port=5432 dbname=azure_advisor_reports_prod user=adminuser password=YourPassword sslmode=require"

# Or using connection string
psql "postgresql://adminuser:YourPassword@psql-advisor-prod.postgres.database.azure.com:5432/azure_advisor_reports_prod?sslmode=require"
```

### Step 3: Environment Variables

```env
# PostgreSQL Configuration
DATABASE_URL=postgresql://adminuser:YourPassword@psql-advisor-prod.postgres.database.azure.com:5432/azure_advisor_reports_prod?sslmode=require
DB_HOST=psql-advisor-prod.postgres.database.azure.com
DB_NAME=azure_advisor_reports_prod
DB_USER=adminuser
DB_PASSWORD=YourStrongPassword123!
DB_PORT=5432
DB_SSLMODE=require
```

---

## Azure Cache for Redis

### Step 1: Create Redis Cache

#### Using Azure Portal

1. **Navigate to Azure Cache for Redis**
   - Search for "Azure Cache for Redis"
   - Click "Create"

2. **Basic Configuration**
   - **Resource group**: `rg-azure-advisor-reports-prod`
   - **DNS name**: `redis-advisor-prod` (globally unique)
   - **Location**: `East US 2`
   - **Cache type**: `Standard C2` (2.5 GB)
   - **Clustering**: Not available for Standard tier

3. **Advanced Settings**
   - **Non-SSL port**: `Disabled` (use SSL only for security)
   - **Redis version**: `6.0` or `6.2`
   - **Data persistence**: `RDB` (recommended for durability)

4. **Networking**
   - **Connectivity method**: `Public endpoint`
   - **Firewall**: Add your IP address

5. **Review + Create**

#### Using Azure CLI

```powershell
$REDIS_NAME = "redis-advisor-prod"

az redis create `
  --name $REDIS_NAME `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --sku Standard `
  --vm-size C2 `
  --enable-non-ssl-port false `
  --redis-version 6

# Get access keys
az redis list-keys `
  --name $REDIS_NAME `
  --resource-group $RESOURCE_GROUP
```

### Step 2: Configure Environment Variables

```env
# Redis Configuration
REDIS_URL=rediss://:YourRedisAccessKey@redis-advisor-prod.redis.cache.windows.net:6380/0
REDIS_HOST=redis-advisor-prod.redis.cache.windows.net
REDIS_PORT=6380
REDIS_PASSWORD=YourRedisAccessKey
REDIS_SSL=True

# Celery Configuration
CELERY_BROKER_URL=rediss://:YourRedisAccessKey@redis-advisor-prod.redis.cache.windows.net:6380/0
CELERY_RESULT_BACKEND=rediss://:YourRedisAccessKey@redis-advisor-prod.redis.cache.windows.net:6380/0
```

---

## Azure App Service

### Backend App Service

#### Step 1: Create App Service Plan

```powershell
$APP_SERVICE_PLAN_BACKEND = "asp-advisor-backend-prod"

az appservice plan create `
  --name $APP_SERVICE_PLAN_BACKEND `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --is-linux `
  --sku P2V3
```

#### Step 2: Create Web App

```powershell
$BACKEND_APP_NAME = "app-advisor-backend-prod"

az webapp create `
  --name $BACKEND_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --plan $APP_SERVICE_PLAN_BACKEND `
  --runtime "PYTHON|3.11"

# Configure app settings (environment variables)
az webapp config appsettings set `
  --name $BACKEND_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --settings `
    DEBUG=False `
    SECRET_KEY="your-secret-key" `
    DATABASE_URL="postgresql://..." `
    REDIS_URL="rediss://..." `
    AZURE_STORAGE_CONNECTION_STRING="..." `
    AZURE_CLIENT_ID="..." `
    AZURE_CLIENT_SECRET="..." `
    AZURE_TENANT_ID="..." `
    ALLOWED_HOSTS="$BACKEND_APP_NAME.azurewebsites.net"
```

### Frontend App Service

```powershell
$APP_SERVICE_PLAN_FRONTEND = "asp-advisor-frontend-prod"
$FRONTEND_APP_NAME = "app-advisor-frontend-prod"

# Create app service plan
az appservice plan create `
  --name $APP_SERVICE_PLAN_FRONTEND `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --is-linux `
  --sku P1V3

# Create web app
az webapp create `
  --name $FRONTEND_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --plan $APP_SERVICE_PLAN_FRONTEND `
  --runtime "NODE|18-lts"
```

---

## Application Insights

### Step 1: Create Application Insights

```powershell
$APPINSIGHTS_NAME = "appi-advisor-prod"

az monitor app-insights component create `
  --app $APPINSIGHTS_NAME `
  --location $LOCATION `
  --resource-group $RESOURCE_GROUP `
  --application-type web

# Get instrumentation key
az monitor app-insights component show `
  --app $APPINSIGHTS_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "instrumentationKey" -o tsv
```

### Step 2: Configure Environment Variables

```env
# Application Insights
APPINSIGHTS_INSTRUMENTATION_KEY=your-instrumentation-key
APPINSIGHTS_CONNECTION_STRING=InstrumentationKey=your-key;IngestionEndpoint=...
```

---

## Cost Estimation

### Monthly Cost Breakdown (Production Environment)

| Service | Configuration | Monthly Cost (USD) |
|---------|--------------|-------------------|
| **Azure Database for PostgreSQL** | Flexible Server, D2s_v3, 128GB, HA | $250 |
| **Azure Cache for Redis** | Standard C2 (2.5GB) | $73 |
| **Azure Blob Storage** | Standard LRS, 100GB, 10K transactions | $3 |
| **App Service Plan (Backend)** | Premium P2v3 (2 instances) | $292 |
| **App Service Plan (Frontend)** | Premium P1v3 (1 instance) | $146 |
| **Application Insights** | Pay-as-you-go, 5GB ingestion | $15 |
| **Data Transfer** | Outbound 100GB | $9 |
| **Total Estimated Monthly Cost** | | **~$788/month** |

### Development Environment Cost (Lower Tier)

| Service | Configuration | Monthly Cost (USD) |
|---------|--------------|-------------------|
| PostgreSQL | Burstable B2s, 32GB | $35 |
| Redis | Basic C0 (250MB) | $16 |
| Blob Storage | Standard LRS, 10GB | $0.50 |
| App Service | Basic B2 (2 instances) | $110 |
| **Total Dev Environment** | | **~$162/month** |

### Cost Optimization Tips

1. **Use Azure Reserved Instances** (save 30-50%)
2. **Enable auto-scaling** to scale down during low usage
3. **Use Azure Hybrid Benefit** if you have Windows Server licenses
4. **Monitor and set budget alerts** in Azure Cost Management
5. **Use Azure Dev/Test subscription** for non-production environments
6. **Clean up unused resources** regularly

---

## Security Best Practices

### 1. Network Security

- Enable **Azure Private Link** for database and Redis (production)
- Configure **Network Security Groups (NSGs)** to restrict traffic
- Use **Azure Front Door** with **Web Application Firewall (WAF)**
- Enable **DDoS Protection** (Standard tier)

### 2. Identity & Access Management

- Use **Managed Identities** instead of connection strings where possible
- Implement **Azure RBAC** for fine-grained access control
- Enable **Azure AD Conditional Access** for authentication
- Rotate secrets regularly (every 90 days)

### 3. Data Protection

- Enable **encryption at rest** for all storage services (enabled by default)
- Use **TLS 1.2+** for all connections
- Enable **soft delete** and **versioning** for blob storage
- Configure **automated backups** with geo-redundancy

### 4. Monitoring & Compliance

- Enable **Azure Security Center** (Defender for Cloud)
- Configure **audit logging** for all services
- Set up **alerts** for suspicious activities
- Implement **Azure Policy** for compliance

### 5. Secrets Management

- Store secrets in **Azure Key Vault**
- Use **Managed Service Identity (MSI)** to access Key Vault
- Never commit secrets to Git
- Use **environment-specific secrets**

### Example: Using Azure Key Vault

```powershell
# Create Key Vault
az keyvault create `
  --name "kv-advisor-prod" `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION

# Store secrets
az keyvault secret set --vault-name "kv-advisor-prod" --name "SECRET-KEY" --value "your-secret-key"
az keyvault secret set --vault-name "kv-advisor-prod" --name "DATABASE-URL" --value "postgresql://..."

# Grant App Service access
az webapp identity assign --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP
$PRINCIPAL_ID = az webapp identity show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query "principalId" -o tsv
az keyvault set-policy --name "kv-advisor-prod" --object-id $PRINCIPAL_ID --secret-permissions get list

# Reference in App Service
az webapp config appsettings set `
  --name $BACKEND_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --settings `
    SECRET_KEY="@Microsoft.KeyVault(SecretUri=https://kv-advisor-prod.vault.azure.net/secrets/SECRET-KEY/)"
```

---

## Connection Strings Reference

### Format Examples

#### PostgreSQL
```
# Standard
postgresql://username:password@hostname:5432/database?sslmode=require

# Azure
postgresql://adminuser:password@psql-advisor-prod.postgres.database.azure.com:5432/azure_advisor_reports_prod?sslmode=require
```

#### Redis
```
# Standard (SSL)
rediss://:password@hostname:6380/0

# Azure
rediss://:YourAccessKey@redis-advisor-prod.redis.cache.windows.net:6380/0
```

#### Azure Blob Storage
```
DefaultEndpointsProtocol=https;AccountName=stadvisorprod;AccountKey=YourAccountKey;EndpointSuffix=core.windows.net
```

#### Azure AD Authority
```
https://login.microsoftonline.com/{tenant-id}
```

---

## Verification Checklist

After setup, verify each service:

### Azure AD
```powershell
# Test token acquisition
curl -X POST "https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token" `
  -d "client_id={client-id}&client_secret={client-secret}&scope=https://graph.microsoft.com/.default&grant_type=client_credentials"
```

### Blob Storage
```powershell
# Test file upload
az storage blob upload `
  --account-name stadvisorprod `
  --container-name csv-uploads `
  --name test.txt `
  --file test.txt
```

### PostgreSQL
```powershell
# Test connection
psql "postgresql://adminuser:password@psql-advisor-prod.postgres.database.azure.com:5432/azure_advisor_reports_prod?sslmode=require" -c "SELECT version();"
```

### Redis
```powershell
# Test connection (requires redis-cli)
redis-cli -h redis-advisor-prod.redis.cache.windows.net -p 6380 -a YourAccessKey --tls ping
```

---

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Check firewall rules
   - Verify network connectivity
   - Ensure SSL is configured correctly

2. **Authentication Failures**
   - Verify credentials are correct
   - Check Azure AD app permissions
   - Ensure admin consent is granted

3. **High Costs**
   - Review Azure Cost Management dashboard
   - Scale down unused resources
   - Use auto-scaling rules

4. **Performance Issues**
   - Check Application Insights for bottlenecks
   - Scale up tier if needed
   - Review database query performance

---

## Additional Resources

- [Azure Documentation](https://docs.microsoft.com/azure)
- [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)
- [Azure Architecture Center](https://docs.microsoft.com/azure/architecture/)
- [Azure Security Best Practices](https://docs.microsoft.com/azure/security/)

---

**Last Updated:** October 1, 2025
**Version:** 1.0
**Maintained By:** DevOps Team
