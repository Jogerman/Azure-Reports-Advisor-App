#!/bin/bash

################################################################################
# Azure Advisor Reports Platform - Deployment Script
# Version: 2.0
# Date: November 11, 2025
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  Azure Advisor Reports Platform - Deployment Script           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

confirm() {
    read -p "$1 (y/n): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Main deployment
print_header

################################################################################
# Step 1: Gather Configuration
################################################################################

print_step "1. Gathering Configuration"

# Check if config file exists
if [ -f ".deployment-config" ]; then
    print_info "Found existing configuration file"
    if confirm "Do you want to use existing configuration?"; then
        source .deployment-config
        print_success "Configuration loaded"
    else
        rm .deployment-config
    fi
fi

# Prompt for configuration if not loaded
if [ ! -f ".deployment-config" ]; then
    print_info "Please provide deployment configuration:"

    # Environment
    read -p "Environment (dev/staging/prod) [prod]: " ENVIRONMENT
    ENVIRONMENT=${ENVIRONMENT:-prod}

    # Resource Group
    read -p "Resource Group Name [rg-azure-advisor-reports-${ENVIRONMENT}]: " RESOURCE_GROUP
    RESOURCE_GROUP=${RESOURCE_GROUP:-rg-azure-advisor-reports-${ENVIRONMENT}}

    # Location
    read -p "Azure Location [eastus]: " LOCATION
    LOCATION=${LOCATION:-eastus}

    # Naming prefix
    read -p "Resource Naming Prefix [advisor-reports]: " PREFIX
    PREFIX=${PREFIX:-advisor-reports}

    # Database
    read -p "Database Admin Username [adminuser]: " DB_ADMIN_USER
    DB_ADMIN_USER=${DB_ADMIN_USER:-adminuser}

    read -sp "Database Admin Password (will be stored in Key Vault): " DB_ADMIN_PASSWORD
    echo
    if [ -z "$DB_ADMIN_PASSWORD" ]; then
        print_error "Database password cannot be empty"
        exit 1
    fi

    # Email
    read -p "Email Host [smtp.gmail.com]: " EMAIL_HOST
    EMAIL_HOST=${EMAIL_HOST:-smtp.gmail.com}

    read -p "Email User: " EMAIL_USER

    read -sp "Email Password (will be stored in Key Vault): " EMAIL_PASSWORD
    echo

    # Frontend Domain (optional)
    read -p "Custom Domain (optional, press Enter to skip): " CUSTOM_DOMAIN

    # Save configuration
    cat > .deployment-config << EOF
# Deployment Configuration
ENVIRONMENT="$ENVIRONMENT"
RESOURCE_GROUP="$RESOURCE_GROUP"
LOCATION="$LOCATION"
PREFIX="$PREFIX"
DB_ADMIN_USER="$DB_ADMIN_USER"
DB_ADMIN_PASSWORD="$DB_ADMIN_PASSWORD"
EMAIL_HOST="$EMAIL_HOST"
EMAIL_USER="$EMAIL_USER"
EMAIL_PASSWORD="$EMAIL_PASSWORD"
CUSTOM_DOMAIN="$CUSTOM_DOMAIN"
EOF

    print_success "Configuration saved to .deployment-config"
fi

# Generate resource names
KEY_VAULT_NAME="kv-${PREFIX}-${ENVIRONMENT}"
# Key Vault names have a 24 character limit and must be globally unique
KEY_VAULT_NAME=$(echo "$KEY_VAULT_NAME" | cut -c1-24 | sed 's/-$//')

DB_SERVER_NAME="psql-${PREFIX}-${ENVIRONMENT}"
REDIS_NAME="redis-${PREFIX}-${ENVIRONMENT}"
STORAGE_ACCOUNT_NAME="st${PREFIX}${ENVIRONMENT}" | tr -d '-'
STORAGE_ACCOUNT_NAME=$(echo "$STORAGE_ACCOUNT_NAME" | tr -d '-' | cut -c1-24)
APP_INSIGHTS_NAME="appi-${PREFIX}-${ENVIRONMENT}"
APP_SERVICE_PLAN="asp-${PREFIX}-${ENVIRONMENT}"
BACKEND_APP_NAME="app-${PREFIX}-api-${ENVIRONMENT}"
FRONTEND_APP_NAME="app-${PREFIX}-web-${ENVIRONMENT}"

print_info "Resource names generated:"
print_info "  Resource Group: $RESOURCE_GROUP"
print_info "  Key Vault: $KEY_VAULT_NAME"
print_info "  Database: $DB_SERVER_NAME"
print_info "  Storage: $STORAGE_ACCOUNT_NAME"
print_info "  Backend App: $BACKEND_APP_NAME"
print_info "  Frontend App: $FRONTEND_APP_NAME"

if ! confirm "Continue with deployment?"; then
    print_warning "Deployment cancelled"
    exit 0
fi

################################################################################
# Step 2: Create Resource Group
################################################################################

print_step "2. Creating Resource Group"

if az group show --name "$RESOURCE_GROUP" &>/dev/null; then
    print_info "Resource group already exists"
else
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --tags Environment="$ENVIRONMENT" Application=AzureAdvisorReports

    print_success "Resource group created"
fi

################################################################################
# Step 3: Create Azure Key Vault
################################################################################

print_step "3. Creating Azure Key Vault"

if az keyvault show --name "$KEY_VAULT_NAME" &>/dev/null; then
    print_info "Key Vault already exists"
else
    az keyvault create \
        --name "$KEY_VAULT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --sku standard \
        --enable-rbac-authorization false \
        --enabled-for-deployment true \
        --enabled-for-template-deployment true

    print_success "Key Vault created"
fi

# Grant current user access
USER_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv)
az keyvault set-policy \
    --name "$KEY_VAULT_NAME" \
    --object-id "$USER_OBJECT_ID" \
    --secret-permissions get list set delete

print_info "Storing secrets in Key Vault..."

# Generate Django secret key
DJANGO_SECRET_KEY=$(openssl rand -base64 50)

# Store secrets
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "django-secret-key" --value "$DJANGO_SECRET_KEY" --output none
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "database-password" --value "$DB_ADMIN_PASSWORD" --output none
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "email-smtp-password" --value "$EMAIL_PASSWORD" --output none

KEY_VAULT_URL="https://${KEY_VAULT_NAME}.vault.azure.net/"
print_success "Secrets stored in Key Vault"

################################################################################
# Step 4: Create PostgreSQL Database
################################################################################

print_step "4. Creating PostgreSQL Database"

DB_NAME="advisor_reports_db"

if az postgres flexible-server show --name "$DB_SERVER_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    print_info "Database server already exists"
else
    print_info "Creating PostgreSQL server (this may take a few minutes)..."

    az postgres flexible-server create \
        --name "$DB_SERVER_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --admin-user "$DB_ADMIN_USER" \
        --admin-password "$DB_ADMIN_PASSWORD" \
        --sku-name Standard_B1ms \
        --tier Burstable \
        --version 14 \
        --storage-size 32 \
        --backup-retention 7 \
        --public-access 0.0.0.0-255.255.255.255 \
        --yes

    print_success "PostgreSQL server created"
fi

# Create database if it doesn't exist
if az postgres flexible-server db show --resource-group "$RESOURCE_GROUP" --server-name "$DB_SERVER_NAME" --database-name "$DB_NAME" &>/dev/null; then
    print_info "Database already exists"
else
    az postgres flexible-server db create \
        --resource-group "$RESOURCE_GROUP" \
        --server-name "$DB_SERVER_NAME" \
        --database-name "$DB_NAME"

    print_success "Database created"
fi

DB_HOST="${DB_SERVER_NAME}.postgres.database.azure.com"

################################################################################
# Step 5: Create Redis Cache (Optional)
################################################################################

print_step "5. Creating Redis Cache"

if confirm "Do you want to create Redis Cache? (Recommended for production)"; then
    if az redis show --name "$REDIS_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
        print_info "Redis cache already exists"
    else
        print_info "Creating Redis cache (this may take 10-15 minutes)..."

        az redis create \
            --name "$REDIS_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --location "$LOCATION" \
            --sku Basic \
            --vm-size c0 \
            --enable-non-ssl-port false &

        REDIS_PID=$!
        print_info "Redis creation started in background (PID: $REDIS_PID)"
    fi

    REDIS_ENABLED=true
else
    REDIS_ENABLED=false
    print_info "Skipping Redis cache creation"
fi

################################################################################
# Step 6: Create Storage Account
################################################################################

print_step "6. Creating Storage Account"

if az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    print_info "Storage account already exists"
else
    az storage account create \
        --name "$STORAGE_ACCOUNT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --sku Standard_LRS \
        --kind StorageV2 \
        --access-tier Hot \
        --https-only true \
        --min-tls-version TLS1_2

    print_success "Storage account created"
fi

# Create containers
az storage container create \
    --name media \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --public-access off \
    --auth-mode login &>/dev/null || true

az storage container create \
    --name static \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --public-access blob \
    --auth-mode login &>/dev/null || true

# Get connection string
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
    --name "$STORAGE_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query connectionString -o tsv)

# Store in Key Vault
az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "storage-connection-string" \
    --value "$STORAGE_CONNECTION_STRING" \
    --output none

print_success "Storage account configured"

################################################################################
# Step 7: Create Application Insights
################################################################################

print_step "7. Creating Application Insights"

if az monitor app-insights component show --app "$APP_INSIGHTS_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    print_info "Application Insights already exists"
else
    az monitor app-insights component create \
        --app "$APP_INSIGHTS_NAME" \
        --location "$LOCATION" \
        --resource-group "$RESOURCE_GROUP" \
        --kind web \
        --application-type web

    print_success "Application Insights created"
fi

# Get connection string
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
    --app "$APP_INSIGHTS_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query instrumentationKey -o tsv)

CONNECTION_STRING=$(az monitor app-insights component show \
    --app "$APP_INSIGHTS_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query connectionString -o tsv)

# Store in Key Vault
az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "appinsights-instrumentation-key" \
    --value "$INSTRUMENTATION_KEY" \
    --output none

az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "appinsights-connection-string" \
    --value "$CONNECTION_STRING" \
    --output none

################################################################################
# Step 8: Create App Service Plan
################################################################################

print_step "8. Creating App Service Plan"

if az appservice plan show --name "$APP_SERVICE_PLAN" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    print_info "App Service Plan already exists"
else
    az appservice plan create \
        --name "$APP_SERVICE_PLAN" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --is-linux \
        --sku B2

    print_success "App Service Plan created"
fi

################################################################################
# Step 9: Create Backend Web App
################################################################################

print_step "9. Creating Backend Web App"

if az webapp show --name "$BACKEND_APP_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    print_info "Backend app already exists"
else
    az webapp create \
        --name "$BACKEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --plan "$APP_SERVICE_PLAN" \
        --runtime "PYTHON|3.11"

    print_success "Backend app created"
fi

# Enable managed identity
az webapp identity assign \
    --name "$BACKEND_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --output none

# Get identity ID
BACKEND_IDENTITY_ID=$(az webapp identity show \
    --name "$BACKEND_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query principalId -o tsv)

# Grant Key Vault access
az keyvault set-policy \
    --name "$KEY_VAULT_NAME" \
    --object-id "$BACKEND_IDENTITY_ID" \
    --secret-permissions get list

BACKEND_URL="https://${BACKEND_APP_NAME}.azurewebsites.net"
print_success "Backend app configured"

################################################################################
# Step 10: Configure Backend Environment Variables
################################################################################

print_step "10. Configuring Backend Environment"

# Wait for Redis if it's being created
if [ "$REDIS_ENABLED" = true ] && [ ! -z "$REDIS_PID" ]; then
    print_info "Waiting for Redis creation to complete..."
    wait $REDIS_PID || true

    # Get Redis info
    REDIS_HOST="${REDIS_NAME}.redis.cache.windows.net"
    REDIS_PASSWORD=$(az redis list-keys \
        --name "$REDIS_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query primaryKey -o tsv)

    # Store in Key Vault
    az keyvault secret set \
        --vault-name "$KEY_VAULT_NAME" \
        --name "redis-password" \
        --value "$REDIS_PASSWORD" \
        --output none

    REDIS_URL="rediss://:${REDIS_PASSWORD}@${REDIS_HOST}:6380/0"
fi

# Configure app settings
print_info "Setting backend environment variables..."

SETTINGS=""
SETTINGS+=" DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production"
SETTINGS+=" DEBUG=False"
SETTINGS+=" SECRET_KEY=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URL}secrets/django-secret-key/)"
SETTINGS+=" ALLOWED_HOSTS=${BACKEND_APP_NAME}.azurewebsites.net"
SETTINGS+=" DATABASE_HOST=$DB_HOST"
SETTINGS+=" DATABASE_NAME=$DB_NAME"
SETTINGS+=" DATABASE_USER=$DB_ADMIN_USER"
SETTINGS+=" DATABASE_PASSWORD=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URL}secrets/database-password/)"
SETTINGS+=" DATABASE_PORT=5432"
SETTINGS+=" AZURE_KEY_VAULT_URL=$KEY_VAULT_URL"
SETTINGS+=" AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT_NAME"
SETTINGS+=" AZURE_STORAGE_CONNECTION_STRING=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URL}secrets/storage-connection-string/)"
SETTINGS+=" APPLICATIONINSIGHTS_CONNECTION_STRING=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URL}secrets/appinsights-connection-string/)"
SETTINGS+=" EMAIL_HOST=$EMAIL_HOST"
SETTINGS+=" EMAIL_HOST_USER=$EMAIL_USER"
SETTINGS+=" EMAIL_HOST_PASSWORD=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URL}secrets/email-smtp-password/)"
SETTINGS+=" FRONTEND_URL=$BACKEND_URL"
SETTINGS+=" VIRUS_SCANNER_TYPE=azure_defender"

if [ "$REDIS_ENABLED" = true ]; then
    SETTINGS+=" REDIS_HOST=$REDIS_HOST"
    SETTINGS+=" REDIS_PASSWORD=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URL}secrets/redis-password/)"
    SETTINGS+=" REDIS_PORT=6380"
fi

az webapp config appsettings set \
    --name "$BACKEND_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings $SETTINGS \
    --output none

print_success "Backend environment configured"

################################################################################
# Step 11: Deploy Backend Code
################################################################################

print_step "11. Deploying Backend Code"

print_info "Building backend..."

# Navigate to backend directory
cd azure_advisor_reports

# Create deployment package
print_info "Creating deployment package..."

# Create startup script
cat > startup.sh << 'EOFSTARTUP'
#!/bin/bash
echo "Starting application..."

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
EOFSTARTUP

chmod +x startup.sh

# Create .deployment file
cat > ../.deployment << 'EOFDEPLOYMENT'
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT=true
EOFDEPLOYMENT

cd ..

# Deploy using ZIP
print_info "Deploying backend to Azure..."

# Use ZIP deploy
cd azure_advisor_reports
zip -r ../backend-deploy.zip . -x "*.git*" -x "*__pycache__*" -x "*.pyc" -x "*venv*" 2>&1 | grep -v "adding:"
cd ..

az webapp deployment source config-zip \
    --name "$BACKEND_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --src backend-deploy.zip

# Set startup command
az webapp config set \
    --name "$BACKEND_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --startup-file "startup.sh" \
    --output none

# Enable logging
az webapp log config \
    --name "$BACKEND_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --application-logging filesystem \
    --level information \
    --web-server-logging filesystem \
    --output none

print_success "Backend deployed"

################################################################################
# Step 12: Run Database Migrations
################################################################################

print_step "12. Running Database Migrations"

print_info "Waiting for backend to start..."
sleep 30

# Try to run migrations via SSH
print_info "Running migrations..."
print_warning "Note: You may need to run migrations manually if this fails"

# Restart to ensure migrations run
az webapp restart \
    --name "$BACKEND_APP_NAME" \
    --resource-group "$RESOURCE_GROUP"

print_info "Waiting for restart..."
sleep 20

print_success "Backend restarted"

################################################################################
# Step 13: Create Frontend App
################################################################################

print_step "13. Creating Frontend Web App"

if az webapp show --name "$FRONTEND_APP_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    print_info "Frontend app already exists"
else
    az webapp create \
        --name "$FRONTEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --plan "$APP_SERVICE_PLAN" \
        --runtime "NODE|18-lts"

    print_success "Frontend app created"
fi

FRONTEND_URL="https://${FRONTEND_APP_NAME}.azurewebsites.net"

# Update backend CORS settings
az webapp config appsettings set \
    --name "$BACKEND_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings FRONTEND_URL="$FRONTEND_URL" \
    --output none

################################################################################
# Step 14: Build and Deploy Frontend
################################################################################

print_step "14. Building and Deploying Frontend"

cd frontend

# Create production env file
cat > .env.production << EOFENV
VITE_API_URL=${BACKEND_URL}/api
VITE_ENVIRONMENT=production
VITE_APPINSIGHTS_INSTRUMENTATION_KEY=$INSTRUMENTATION_KEY
EOFENV

# Install dependencies and build
print_info "Installing frontend dependencies..."
npm install

print_info "Building frontend..."
npm run build

# Deploy
print_info "Deploying frontend..."
cd dist
zip -r ../../frontend-deploy.zip . 2>&1 | grep -v "adding:"
cd ../..

az webapp deployment source config-zip \
    --name "$FRONTEND_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --src frontend-deploy.zip

print_success "Frontend deployed"

################################################################################
# Step 15: Final Configuration
################################################################################

print_step "15. Final Configuration"

# Configure health check for backend
az webapp config set \
    --name "$BACKEND_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --health-check-path "/api/health/" \
    --output none

print_success "Health check configured"

################################################################################
# Deployment Complete
################################################################################

print_header
print_success "DEPLOYMENT COMPLETE!"
echo
echo "======================================================================"
echo "                    DEPLOYMENT SUMMARY                                "
echo "======================================================================"
echo
echo "Resource Group:    $RESOURCE_GROUP"
echo "Location:          $LOCATION"
echo "Environment:       $ENVIRONMENT"
echo
echo "Backend URL:       $BACKEND_URL"
echo "Frontend URL:      $FRONTEND_URL"
echo
echo "Key Vault:         $KEY_VAULT_NAME"
echo "Database Server:   $DB_SERVER_NAME"
echo "Storage Account:   $STORAGE_ACCOUNT_NAME"
echo
echo "======================================================================"
echo "                    NEXT STEPS                                        "
echo "======================================================================"
echo
echo "1. Test Backend Health:"
echo "   curl ${BACKEND_URL}/api/health/"
echo
echo "2. Access Frontend:"
echo "   open $FRONTEND_URL"
echo
echo "3. Create Superuser (via Azure Portal or SSH):"
echo "   az webapp ssh --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP"
echo "   python manage.py createsuperuser"
echo
echo "4. View Logs:"
echo "   az webapp log tail --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP"
echo
echo "5. Monitor Application:"
echo "   https://portal.azure.com/#@/resource/subscriptions/.../resourceGroups/$RESOURCE_GROUP"
echo
echo "======================================================================"
echo

# Save deployment info
cat > deployment-info.txt << EOFINFO
Deployment Information
======================
Date: $(date)
Environment: $ENVIRONMENT

URLs:
  Backend:  $BACKEND_URL
  Frontend: $FRONTEND_URL

Resources:
  Resource Group: $RESOURCE_GROUP
  Key Vault: $KEY_VAULT_NAME
  Database: $DB_SERVER_NAME
  Storage: $STORAGE_ACCOUNT_NAME
  Backend App: $BACKEND_APP_NAME
  Frontend App: $FRONTEND_APP_NAME

Database Connection:
  Host: $DB_HOST
  Database: $DB_NAME
  User: $DB_ADMIN_USER

Health Check:
  ${BACKEND_URL}/api/health/
EOFINFO

print_success "Deployment information saved to deployment-info.txt"
print_success "Configuration saved to .deployment-config"

echo
print_warning "IMPORTANT: Keep .deployment-config secure as it contains sensitive information!"
echo
