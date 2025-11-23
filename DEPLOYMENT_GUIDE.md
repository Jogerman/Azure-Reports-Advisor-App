# Azure Advisor Reports Platform - Complete Deployment Guide

**Version:** 2.0 (Includes Phase 1, 2, and 3 Features)
**Date:** November 11, 2025
**Status:** Production Ready (after configuration)

---

## Table of Contents

1. [Pre-Deployment Checklist](#1-pre-deployment-checklist)
2. [Azure Resources Setup](#2-azure-resources-setup)
3. [Database Migrations](#3-database-migrations)
4. [Environment Configuration](#4-environment-configuration)
5. [Backend Deployment](#5-backend-deployment)
6. [Frontend Deployment](#6-frontend-deployment)
7. [Post-Deployment Configuration](#7-post-deployment-configuration)
8. [Monitoring & Health Checks](#8-monitoring--health-checks)
9. [Troubleshooting](#9-troubleshooting)
10. [Rollback Procedures](#10-rollback-procedures)

---

## 1. Pre-Deployment Checklist

### ✅ Code Readiness

- [ ] All code committed to repository
- [ ] All tests passing locally
- [ ] No security vulnerabilities in dependencies
- [ ] Environment variables documented
- [ ] Database migrations created and tested
- [ ] Static files collected and tested
- [ ] API documentation updated

### ✅ Testing Completed

- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests
- [ ] Frontend E2E tests (Playwright)
- [ ] Load testing (100+ concurrent users)
- [ ] Security scanning (OWASP)
- [ ] Accessibility testing (WCAG 2.1 AA)
- [ ] Cross-browser testing

### ✅ Infrastructure Prepared

- [ ] Azure subscription active
- [ ] Resource group created
- [ ] Bicep templates updated
- [ ] Azure CLI installed and configured
- [ ] GitHub Actions configured (if using CI/CD)
- [ ] DNS records prepared
- [ ] SSL certificates ready

### ✅ Third-Party Services

- [ ] Email service configured (SMTP or SendGrid)
- [ ] Azure Key Vault created
- [ ] Application Insights created
- [ ] Azure Storage account created
- [ ] Redis cache created (optional)
- [ ] ClamAV server or Azure Defender enabled

### ✅ Documentation

- [ ] Deployment guide (this document)
- [ ] Operations manual
- [ ] Incident response plan
- [ ] Backup and recovery procedures
- [ ] User documentation
- [ ] API documentation

---

## 2. Azure Resources Setup

### 2.1. Create Resource Group

```bash
# Set variables
RESOURCE_GROUP="rg-azure-advisor-reports-prod"
LOCATION="eastus"
SUBSCRIPTION_ID="your-subscription-id"

# Login to Azure
az login

# Set subscription
az account set --subscription $SUBSCRIPTION_ID

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --tags Environment=Production Application=AzureAdvisorReports
```

### 2.2. Create Azure Key Vault

```bash
# Set variables
KEY_VAULT_NAME="kv-advisor-reports-prod"

# Create Key Vault
az keyvault create \
  --name $KEY_VAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku standard \
  --enable-rbac-authorization false \
  --enabled-for-deployment true \
  --enabled-for-template-deployment true

# Get current user object ID
USER_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv)

# Grant yourself access
az keyvault set-policy \
  --name $KEY_VAULT_NAME \
  --object-id $USER_OBJECT_ID \
  --secret-permissions get list set delete

# Add secrets
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "django-secret-key" \
  --value "$(openssl rand -base64 50)"

az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "database-password" \
  --value "YOUR_STRONG_PASSWORD"

az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "email-smtp-password" \
  --value "YOUR_EMAIL_PASSWORD"

# Store the Key Vault URL
KEY_VAULT_URL="https://${KEY_VAULT_NAME}.vault.azure.net/"
echo "Key Vault URL: $KEY_VAULT_URL"
```

### 2.3. Create PostgreSQL Database

```bash
# Set variables
DB_SERVER_NAME="psql-advisor-reports-prod"
DB_NAME="advisor_reports_db"
DB_ADMIN_USER="adminuser"
DB_ADMIN_PASSWORD="YOUR_STRONG_PASSWORD"  # Use Key Vault value

# Create PostgreSQL server
az postgres flexible-server create \
  --name $DB_SERVER_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --admin-user $DB_ADMIN_USER \
  --admin-password $DB_ADMIN_PASSWORD \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --version 14 \
  --storage-size 32 \
  --backup-retention 7 \
  --geo-redundant-backup Disabled \
  --high-availability Disabled \
  --public-access 0.0.0.0-255.255.255.255

# Create database
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_SERVER_NAME \
  --database-name $DB_NAME

# Get connection string
DB_HOST="${DB_SERVER_NAME}.postgres.database.azure.com"
echo "Database Host: $DB_HOST"
```

### 2.4. Create Redis Cache (Optional but Recommended)

```bash
# Set variables
REDIS_NAME="redis-advisor-reports-prod"

# Create Redis
az redis create \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Basic \
  --vm-size c0 \
  --enable-non-ssl-port false

# Get Redis connection info
REDIS_HOST="${REDIS_NAME}.redis.cache.windows.net"
REDIS_PASSWORD=$(az redis list-keys \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query primaryKey -o tsv)

# Store in Key Vault
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "redis-password" \
  --value "$REDIS_PASSWORD"

echo "Redis Host: $REDIS_HOST"
```

### 2.5. Create Storage Account

```bash
# Set variables
STORAGE_ACCOUNT_NAME="stadvreportsprod"  # Must be globally unique

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --access-tier Hot \
  --https-only true \
  --min-tls-version TLS1_2

# Create containers
az storage container create \
  --name media \
  --account-name $STORAGE_ACCOUNT_NAME \
  --public-access off

az storage container create \
  --name static \
  --account-name $STORAGE_ACCOUNT_NAME \
  --public-access blob

# Enable Azure Defender for Storage (Virus Scanning)
az security pricing create \
  --name StorageAccounts \
  --tier standard

# Get connection string
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --query connectionString -o tsv)

# Store in Key Vault
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "storage-connection-string" \
  --value "$STORAGE_CONNECTION_STRING"
```

### 2.6. Create Application Insights

```bash
# Set variables
APP_INSIGHTS_NAME="appi-advisor-reports-prod"

# Create Application Insights
az monitor app-insights component create \
  --app $APP_INSIGHTS_NAME \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --kind web \
  --application-type web

# Get instrumentation key and connection string
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app $APP_INSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey -o tsv)

CONNECTION_STRING=$(az monitor app-insights component show \
  --app $APP_INSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query connectionString -o tsv)

# Store in Key Vault
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "appinsights-instrumentation-key" \
  --value "$INSTRUMENTATION_KEY"

az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "appinsights-connection-string" \
  --value "$CONNECTION_STRING"
```

### 2.7. Create App Service Plan and Web Apps

```bash
# Set variables
APP_SERVICE_PLAN="asp-advisor-reports-prod"
BACKEND_APP_NAME="app-advisor-reports-api-prod"
FRONTEND_APP_NAME="app-advisor-reports-web-prod"

# Create App Service Plan (Linux, Python 3.11)
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --is-linux \
  --sku B2

# Create Backend Web App
az webapp create \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --runtime "PYTHON|3.11"

# Create Frontend Web App
az webapp create \
  --name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --runtime "NODE|18-lts"

# Enable system-assigned managed identity for backend
az webapp identity assign \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Get the identity's object ID
BACKEND_IDENTITY_ID=$(az webapp identity show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

# Grant Key Vault access to backend identity
az keyvault set-policy \
  --name $KEY_VAULT_NAME \
  --object-id $BACKEND_IDENTITY_ID \
  --secret-permissions get list

echo "Backend App URL: https://${BACKEND_APP_NAME}.azurewebsites.net"
echo "Frontend App URL: https://${FRONTEND_APP_NAME}.azurewebsites.net"
```

---

## 3. Database Migrations

### 3.1. Prepare Local Environment

```bash
# Navigate to backend directory
cd azure_advisor_reports

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3.2. Create Migrations for New Features

```bash
# Create migrations for all apps
python manage.py makemigrations

# Specifically for Phase 2 & 3
python manage.py makemigrations audit
python manage.py makemigrations notifications
python manage.py makemigrations authentication

# Review migrations
python manage.py showmigrations
```

### 3.3. Test Migrations Locally

```bash
# Apply migrations to local database
python manage.py migrate

# Verify migrations
python manage.py showmigrations

# Test rollback (optional)
python manage.py migrate <app_name> <previous_migration>
python manage.py migrate <app_name> <current_migration>
```

### 3.4. Apply Migrations to Production

```bash
# Set production database connection
export DATABASE_URL="postgresql://${DB_ADMIN_USER}:${DB_ADMIN_PASSWORD}@${DB_HOST}:5432/${DB_NAME}?sslmode=require"

# Run migrations
python manage.py migrate --no-input

# Create superuser (if needed)
python manage.py createsuperuser \
  --username admin \
  --email admin@example.com \
  --noinput

# Optional: Load initial data
python manage.py loaddata initial_data.json
```

### 3.5. Verify Database

```bash
# Connect to database
psql "$DATABASE_URL"

# Check tables
\dt

# Expected tables (partial list):
# - auth_user_extended
# - auth_api_key
# - auth_token_blacklist
# - email_notifications
# - webhooks
# - webhook_deliveries
# - inapp_notifications
# - audit_logs
# - security_events
# - clients_client
# - reports_report
# - reports_recommendation

# Exit
\q
```

---

## 4. Environment Configuration

### 4.1. Backend Environment Variables

Create `.env.production` file or set in Azure App Service Configuration:

```bash
# Django Settings
DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production
SECRET_KEY=<from-key-vault>
DEBUG=False
ALLOWED_HOSTS=app-advisor-reports-api-prod.azurewebsites.net,yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require
DATABASE_HOST=<from-azure>
DATABASE_NAME=advisor_reports_db
DATABASE_USER=adminuser
DATABASE_PASSWORD=<from-key-vault>
DATABASE_PORT=5432

# Azure Key Vault
AZURE_KEY_VAULT_URL=https://kv-advisor-reports-prod.vault.azure.net/

# Redis Cache
REDIS_URL=rediss://:password@host:6380/0
REDIS_HOST=<from-azure>
REDIS_PASSWORD=<from-key-vault>
REDIS_PORT=6380
REDIS_DB=0

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=stadvreportsprod
AZURE_STORAGE_CONNECTION_STRING=<from-key-vault>
AZURE_STORAGE_CONTAINER_NAME=media
STATIC_STORAGE_CONTAINER_NAME=static

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=<from-key-vault>
APPINSIGHTS_INSTRUMENTATION_KEY=<from-key-vault>

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=<from-key-vault>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Frontend URL
FRONTEND_URL=https://app-advisor-reports-web-prod.azurewebsites.net

# CORS Settings
CORS_ALLOWED_ORIGINS=https://app-advisor-reports-web-prod.azurewebsites.net,https://yourdomain.com

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Virus Scanning
VIRUS_SCANNER_TYPE=azure_defender  # or 'clamav' if using ClamAV
QUARANTINE_INFECTED_FILES=True
QUARANTINE_DIR=/home/site/wwwroot/quarantine

# Celery (if using)
CELERY_BROKER_URL=rediss://:password@host:6380/1
CELERY_RESULT_BACKEND=rediss://:password@host:6380/2

# Logging
LOG_LEVEL=INFO
```

### 4.2. Set Environment Variables in Azure

```bash
# Backend App Service
az webapp config appsettings set \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    DJANGO_SETTINGS_MODULE="azure_advisor_reports.settings.production" \
    SECRET_KEY="@Microsoft.KeyVault(SecretUri=https://${KEY_VAULT_NAME}.vault.azure.net/secrets/django-secret-key/)" \
    DEBUG="False" \
    DATABASE_HOST="$DB_HOST" \
    DATABASE_NAME="$DB_NAME" \
    DATABASE_USER="$DB_ADMIN_USER" \
    DATABASE_PASSWORD="@Microsoft.KeyVault(SecretUri=https://${KEY_VAULT_NAME}.vault.azure.net/secrets/database-password/)" \
    AZURE_KEY_VAULT_URL="$KEY_VAULT_URL" \
    REDIS_HOST="$REDIS_HOST" \
    REDIS_PASSWORD="@Microsoft.KeyVault(SecretUri=https://${KEY_VAULT_NAME}.vault.azure.net/secrets/redis-password/)" \
    AZURE_STORAGE_ACCOUNT_NAME="$STORAGE_ACCOUNT_NAME" \
    AZURE_STORAGE_CONNECTION_STRING="@Microsoft.KeyVault(SecretUri=https://${KEY_VAULT_NAME}.vault.azure.net/secrets/storage-connection-string/)" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="@Microsoft.KeyVault(SecretUri=https://${KEY_VAULT_NAME}.vault.azure.net/secrets/appinsights-connection-string/)" \
    EMAIL_HOST="smtp.gmail.com" \
    EMAIL_HOST_USER="noreply@yourdomain.com" \
    EMAIL_HOST_PASSWORD="@Microsoft.KeyVault(SecretUri=https://${KEY_VAULT_NAME}.vault.azure.net/secrets/email-smtp-password/)" \
    FRONTEND_URL="https://${FRONTEND_APP_NAME}.azurewebsites.net"
```

### 4.3. Frontend Environment Variables

Create `.env.production` in frontend directory:

```bash
# API Configuration
VITE_API_URL=https://app-advisor-reports-api-prod.azurewebsites.net/api
VITE_API_VERSION=v1

# Azure AD Authentication (if using)
VITE_AZURE_AD_CLIENT_ID=your-client-id
VITE_AZURE_AD_TENANT_ID=your-tenant-id
VITE_AZURE_AD_REDIRECT_URI=https://app-advisor-reports-web-prod.azurewebsites.net/auth/callback

# Application Insights (Frontend)
VITE_APPINSIGHTS_INSTRUMENTATION_KEY=your-key

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_NOTIFICATIONS=true
VITE_ENABLE_DARK_MODE=true

# Environment
VITE_ENVIRONMENT=production
```

---

## 5. Backend Deployment

### 5.1. Build Backend

```bash
cd azure_advisor_reports

# Collect static files
python manage.py collectstatic --no-input

# Create requirements.txt if not exists
pip freeze > requirements.txt

# Create startup script (startup.sh)
cat > startup.sh << 'EOF'
#!/bin/bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --no-input

# Collect static files
python manage.py collectstatic --no-input

# Start Gunicorn
gunicorn azure_advisor_reports.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 300 \
  --access-logfile - \
  --error-logfile -
EOF

chmod +x startup.sh
```

### 5.2. Deploy Backend to Azure

```bash
# Configure deployment source (GitHub)
az webapp deployment source config \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --repo-url https://github.com/yourusername/azure-advisor-reports \
  --branch main \
  --manual-integration

# OR deploy from local Git
az webapp deployment source config-local-git \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Get Git URL
GIT_URL=$(az webapp deployment source config-local-git \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query url -o tsv)

# Add Azure remote and push
git remote add azure $GIT_URL
git push azure main

# OR deploy using ZIP
az webapp deployment source config-zip \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --src backend-deployment.zip
```

### 5.3. Configure Backend Startup

```bash
# Set startup command
az webapp config set \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "startup.sh"

# Enable detailed logging
az webapp log config \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --application-logging filesystem \
  --level information \
  --web-server-logging filesystem

# Restart app
az webapp restart \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

---

## 6. Frontend Deployment

### 6.1. Build Frontend

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Test build locally
npm run preview
```

### 6.2. Deploy Frontend to Azure

#### Option A: Deploy using Azure CLI

```bash
# Navigate to dist folder
cd dist

# Create deployment ZIP
zip -r ../frontend-deployment.zip .
cd ..

# Deploy
az webapp deployment source config-zip \
  --name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --src frontend-deployment.zip
```

#### Option B: Deploy using Static Web Apps (Recommended)

```bash
# Create Static Web App
az staticwebapp create \
  --name "swa-advisor-reports-prod" \
  --resource-group $RESOURCE_GROUP \
  --location "eastus2" \
  --source https://github.com/yourusername/azure-advisor-reports \
  --branch main \
  --app-location "/frontend" \
  --output-location "dist" \
  --login-with-github

# Configure custom domain (optional)
az staticwebapp hostname set \
  --name "swa-advisor-reports-prod" \
  --resource-group $RESOURCE_GROUP \
  --hostname "reports.yourdomain.com"
```

### 6.3. Configure Frontend Routing

Create `staticwebapp.config.json` in frontend root:

```json
{
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/assets/*", "/api/*"]
  },
  "routes": [
    {
      "route": "/api/*",
      "allowedRoles": ["authenticated"]
    }
  ],
  "responseOverrides": {
    "404": {
      "rewrite": "/index.html",
      "statusCode": 200
    }
  },
  "globalHeaders": {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin"
  },
  "mimeTypes": {
    ".json": "application/json",
    ".js": "application/javascript",
    ".css": "text/css"
  }
}
```

---

## 7. Post-Deployment Configuration

### 7.1. Configure Custom Domain

```bash
# Add custom domain
az webapp config hostname add \
  --webapp-name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --hostname api.yourdomain.com

az webapp config hostname add \
  --webapp-name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --hostname www.yourdomain.com

# Create managed SSL certificate
az webapp config ssl create \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --hostname api.yourdomain.com

az webapp config ssl create \
  --name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --hostname www.yourdomain.com
```

### 7.2. Set Up Email Templates

```bash
# SSH into backend app
az webapp ssh \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Create templates directory
mkdir -p /home/site/wwwroot/templates/emails

# Create template files
cat > /home/site/wwwroot/templates/emails/report_completed.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #0078d4; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f5f5f5; }
        .button { display: inline-block; padding: 12px 24px; background: #0078d4; color: white; text-decoration: none; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Report Ready</h1>
        </div>
        <div class="content">
            <h2>Hello {{ user.first_name }},</h2>
            <p>Your Azure Advisor report for <strong>{{ report.client.company_name }}</strong> is ready.</p>
            <p>Report Type: {{ report.report_type }}</p>
            <p>Generated: {{ report.processing_completed_at|date:"F d, Y H:i" }}</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{{ download_url }}" class="button">Download Report</a>
            </p>
            <p>If you have any questions, please contact support.</p>
        </div>
    </div>
</body>
</html>
EOF

# Create text version
cat > /home/site/wwwroot/templates/emails/report_completed.txt << 'EOF'
Hello {{ user.first_name }},

Your Azure Advisor report for {{ report.client.company_name }} is ready.

Report Type: {{ report.report_type }}
Generated: {{ report.processing_completed_at|date:"F d, Y H:i" }}

Download your report: {{ download_url }}

If you have any questions, please contact support.
EOF

exit
```

### 7.3. Configure Scheduled Tasks

#### Option A: Using Celery Beat (Recommended)

```bash
# Add Celery to requirements.txt
echo "celery[redis]==5.3.4" >> requirements.txt

# Create celerybeat-schedule.py
cat > celerybeat_schedule.py << 'EOF'
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-tokens': {
        'task': 'apps.security.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM daily
    },
    'send-token-expiry-notifications': {
        'task': 'apps.security.tasks.send_expiry_notifications',
        'schedule': crontab(hour=9, minute=0),  # 9:00 AM daily
    },
    'cleanup-old-notifications': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Sundays 3:00 AM
    },
    'database-health-check': {
        'task': 'apps.monitoring.tasks.check_database_health',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}
EOF
```

#### Option B: Using Azure Functions (Alternative)

```bash
# Create Azure Function App
az functionapp create \
  --name "func-advisor-tasks-prod" \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --storage-account $STORAGE_ACCOUNT_NAME

# Deploy function (timer triggers)
# See Azure Functions documentation for details
```

### 7.4. Create Initial Superuser

```bash
# Create superuser via management command
az webapp ssh \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Inside SSH session
python manage.py createsuperuser \
  --username admin \
  --email admin@yourdomain.com

exit
```

---

## 8. Monitoring & Health Checks

### 8.1. Configure Health Check Endpoints

```bash
# Set health check path in App Service
az webapp config set \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --health-check-path "/api/health/"

# Configure auto-healing rules
az webapp config set \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --auto-heal-enabled true
```

### 8.2. Set Up Application Insights Alerts

```bash
# CPU alert
az monitor metrics alert create \
  --name "High CPU Usage" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$BACKEND_APP_NAME" \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action

# Memory alert
az monitor metrics alert create \
  --name "High Memory Usage" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$BACKEND_APP_NAME" \
  --condition "avg MemoryPercentage > 85" \
  --window-size 5m \
  --evaluation-frequency 1m

# Response time alert
az monitor metrics alert create \
  --name "Slow Response Time" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$BACKEND_APP_NAME" \
  --condition "avg AverageResponseTime > 5000" \
  --window-size 5m \
  --evaluation-frequency 1m
```

### 8.3. Configure Log Analytics

```bash
# Create Log Analytics Workspace
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name "law-advisor-reports-prod" \
  --location $LOCATION

# Link App Service to Log Analytics
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group $RESOURCE_GROUP \
  --workspace-name "law-advisor-reports-prod" \
  --query customerId -o tsv)

az monitor diagnostic-settings create \
  --name "DiagnosticSettings" \
  --resource "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$BACKEND_APP_NAME" \
  --workspace $WORKSPACE_ID \
  --logs '[{"category": "AppServiceConsoleLogs", "enabled": true}, {"category": "AppServiceHTTPLogs", "enabled": true}]' \
  --metrics '[{"category": "AllMetrics", "enabled": true}]'
```

### 8.4. Test Health Endpoints

```bash
# Test backend health
curl https://${BACKEND_APP_NAME}.azurewebsites.net/api/health/

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2025-11-11T12:00:00Z",
#   "checks": {
#     "database": "healthy",
#     "cache": "healthy",
#     "storage": "healthy"
#   }
# }

# Test readiness
curl https://${BACKEND_APP_NAME}.azurewebsites.net/api/health/ready/

# Test liveness
curl https://${BACKEND_APP_NAME}.azurewebsites.net/api/health/live/
```

---

## 9. Troubleshooting

### 9.1. Common Issues

#### Backend Won't Start

```bash
# Check logs
az webapp log tail \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Common fixes:
# 1. Check startup command
az webapp config show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query startupCommand

# 2. Verify environment variables
az webapp config appsettings list \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP

# 3. Check Python version
az webapp config show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query linuxFxVersion
```

#### Database Connection Errors

```bash
# Test database connection
psql "postgresql://${DB_ADMIN_USER}:${DB_ADMIN_PASSWORD}@${DB_HOST}:5432/${DB_NAME}?sslmode=require"

# Check firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME

# Add App Service IP if needed
az postgres flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --rule-name AllowAppService \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 255.255.255.255
```

#### Key Vault Access Denied

```bash
# Verify managed identity
az webapp identity show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Check Key Vault access policies
az keyvault show \
  --name $KEY_VAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.accessPolicies

# Re-grant access if needed
IDENTITY_ID=$(az webapp identity show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

az keyvault set-policy \
  --name $KEY_VAULT_NAME \
  --object-id $IDENTITY_ID \
  --secret-permissions get list
```

#### Frontend 404 Errors

```bash
# Check SPA routing configuration
# Ensure staticwebapp.config.json or web.config is properly configured

# For App Service, add web.config:
cat > web.config << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="React Routes" stopProcessing="true">
          <match url=".*" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
            <add input="{REQUEST_URI}" pattern="^/(api)" negate="true" />
          </conditions>
          <action type="Rewrite" url="/index.html" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
EOF
```

### 9.2. Debugging Commands

```bash
# Backend SSH
az webapp ssh --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP

# Download logs
az webapp log download \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --log-file backend-logs.zip

# Stream logs
az webapp log tail \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Check app status
az webapp show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query state

# Restart app
az webapp restart \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

---

## 10. Rollback Procedures

### 10.1. Backend Rollback

```bash
# List deployment history
az webapp deployment list \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Revert to previous deployment
PREVIOUS_DEPLOYMENT_ID="<deployment-id>"

az webapp deployment source sync \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --deployment-id $PREVIOUS_DEPLOYMENT_ID

# OR rollback using slots (if configured)
az webapp deployment slot swap \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot staging \
  --target-slot production
```

### 10.2. Database Rollback

```bash
# Restore from backup
# List available backups
az postgres flexible-server backup list \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_SERVER_NAME

# Restore to point-in-time
az postgres flexible-server restore \
  --resource-group $RESOURCE_GROUP \
  --name "${DB_SERVER_NAME}-restored" \
  --source-server $DB_SERVER_NAME \
  --restore-time "2025-11-10T12:00:00Z"

# OR revert migrations
python manage.py migrate <app_name> <previous_migration>
```

### 10.3. Emergency Rollback Checklist

- [ ] Stop new deployments
- [ ] Notify team and users
- [ ] Take database snapshot
- [ ] Revert application code
- [ ] Revert database migrations (if necessary)
- [ ] Clear caches
- [ ] Verify health endpoints
- [ ] Test critical functionality
- [ ] Monitor error logs
- [ ] Document incident

---

## Post-Deployment Verification

### Final Checklist

- [ ] Backend health endpoint returns 200
- [ ] Frontend loads successfully
- [ ] User can login
- [ ] Can create a client
- [ ] Can upload CSV
- [ ] Can generate report
- [ ] Can download report
- [ ] History page displays data
- [ ] Analytics dashboard shows metrics
- [ ] Notifications are being sent
- [ ] Webhooks are triggering
- [ ] API keys can be created
- [ ] File uploads are scanned for viruses
- [ ] Logs are being collected
- [ ] Alerts are configured
- [ ] Backup is running
- [ ] SSL certificates are valid
- [ ] Custom domain works
- [ ] Performance is acceptable

### Smoke Test Script

```bash
#!/bin/bash

BACKEND_URL="https://app-advisor-reports-api-prod.azurewebsites.net"
FRONTEND_URL="https://app-advisor-reports-web-prod.azurewebsites.net"

echo "Running smoke tests..."

# Test backend health
echo "1. Testing backend health..."
HEALTH=$(curl -s "${BACKEND_URL}/api/health/" | jq -r '.status')
if [ "$HEALTH" = "healthy" ]; then
  echo "✓ Backend is healthy"
else
  echo "✗ Backend health check failed"
  exit 1
fi

# Test frontend
echo "2. Testing frontend..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")
if [ "$STATUS" = "200" ]; then
  echo "✓ Frontend is accessible"
else
  echo "✗ Frontend returned status $STATUS"
  exit 1
fi

# Test API endpoints
echo "3. Testing API endpoints..."
# Add your API tests here

echo "✓ All smoke tests passed!"
```

---

## Maintenance

### Regular Tasks

**Daily:**
- Monitor error logs
- Check health metrics
- Review security alerts

**Weekly:**
- Review database performance
- Check storage usage
- Update dependencies (if needed)
- Review and address security vulnerabilities

**Monthly:**
- Review and optimize costs
- Update SSL certificates (if needed)
- Review backup retention
- Performance tuning
- Security audit

---

## Support & Resources

### Documentation
- [Azure App Service Docs](https://docs.microsoft.com/azure/app-service/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [React Deployment](https://vitejs.dev/guide/static-deploy.html)

### Useful Commands

```bash
# Quick status check
az webapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query state

# Scale up/down
az appservice plan update \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --sku P1V2

# Backup database
az postgres flexible-server backup create \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_SERVER_NAME
```

---

**Deployment Guide Version:** 2.0
**Last Updated:** November 11, 2025
**Status:** ✅ Production Ready
