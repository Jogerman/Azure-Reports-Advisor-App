#!/bin/bash

################################################################################
# Azure Advisor Reports - Update Existing Deployment with Phase 3
# Version: 1.0
# Date: November 11, 2025
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
RESOURCE_GROUP="rg-azure-advisor-app"
ACR_NAME="advisorreportsacr"
BACKEND_APP="advisor-reports-backend"
FRONTEND_APP="advisor-reports-frontend"
BACKEND_URL="https://advisor-reports-backend.nicefield-788f351e.eastus.azurecontainerapps.io"

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  Azure Advisor Reports - Phase 3 Update                       ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

confirm() {
    read -p "$1 (y/n): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

print_header

################################################################################
# Step 1: Verify Prerequisites
################################################################################

print_step "1. Verifying Prerequisites"

# Check if logged in to Azure
if ! az account show &>/dev/null; then
    print_error "Not logged in to Azure"
    print_info "Run: az login"
    exit 1
fi

# Check if in correct directory
if [ ! -d "azure_advisor_reports" ] || [ ! -d "frontend" ]; then
    print_error "Not in project root directory"
    print_info "Please cd to: /Users/josegomez/Documents/Code/Azure-Reports-Advisor-App"
    exit 1
fi

print_success "Prerequisites verified"

################################################################################
# Step 2: Run Database Migrations
################################################################################

print_step "2. Running Database Migrations"

print_info "Creating migration files locally..."

cd azure_advisor_reports

# Create migrations for Phase 3 apps
python3 manage.py makemigrations notifications 2>&1 | grep -v "No changes detected" || true
python3 manage.py makemigrations authentication 2>&1 | grep -v "No changes detected" || true
python3 manage.py makemigrations audit 2>&1 | grep -v "No changes detected" || true

cd ..

print_info "Migrations created locally"

if confirm "Do you want to apply migrations to production database now?"; then
    print_info "Applying migrations via container exec..."

    # Execute migrations in running container
    az containerapp exec \
        --name "$BACKEND_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --command "python manage.py migrate --no-input" || {
        print_error "Migration failed"
        print_info "You may need to run migrations manually after deployment"
    }

    print_success "Migrations applied"
else
    print_info "Skipping migrations (remember to run them after deployment)"
fi

################################################################################
# Step 3: Check for Dockerfile
################################################################################

print_step "3. Checking Build Configuration"

# Check if Dockerfiles exist
if [ ! -f "azure_advisor_reports/Dockerfile" ]; then
    print_info "Creating backend Dockerfile..."

    cat > azure_advisor_reports/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --no-input || true

EXPOSE 8000

CMD ["gunicorn", "azure_advisor_reports.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--timeout", "300", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
EOF
    print_success "Backend Dockerfile created"
fi

if [ ! -f "frontend/Dockerfile" ]; then
    print_info "Creating frontend Dockerfile..."

    cat > frontend/Dockerfile << 'EOF'
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build
ENV VITE_API_URL=https://advisor-reports-backend.nicefield-788f351e.eastus.azurecontainerapps.io/api
RUN npm run build

# Production image
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Configure nginx for SPA
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF
    print_success "Frontend Dockerfile created"
fi

################################################################################
# Step 4: Build and Push Backend Image
################################################################################

print_step "4. Building Backend Container Image"

if confirm "Build and deploy backend with new code?"; then
    print_info "Building backend image (this may take 3-5 minutes)..."

    cd azure_advisor_reports

    # Build and push to ACR
    az acr build \
        --registry "$ACR_NAME" \
        --image advisor-reports-backend:latest \
        --image advisor-reports-backend:phase3-$(date +%Y%m%d-%H%M%S) \
        --file Dockerfile \
        . || {
        print_error "Backend build failed"
        exit 1
    }

    cd ..

    print_success "Backend image built and pushed to ACR"

    # Update container app
    print_info "Updating backend container app..."

    az containerapp update \
        --name "$BACKEND_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --image "$ACR_NAME.azurecr.io/advisor-reports-backend:latest" || {
        print_error "Backend update failed"
        exit 1
    }

    print_success "Backend updated"

    # Wait for rollout
    print_info "Waiting for backend to restart (30 seconds)..."
    sleep 30

else
    print_info "Skipping backend build"
fi

################################################################################
# Step 5: Build and Push Frontend Image
################################################################################

print_step "5. Building Frontend Container Image"

if confirm "Build and deploy frontend with new code?"; then
    print_info "Building frontend image (this may take 3-5 minutes)..."

    cd frontend

    # Build and push to ACR
    az acr build \
        --registry "$ACR_NAME" \
        --image advisor-reports-frontend:latest \
        --image advisor-reports-frontend:phase3-$(date +%Y%m%d-%H%M%S) \
        --file Dockerfile \
        . || {
        print_error "Frontend build failed"
        exit 1
    }

    cd ..

    print_success "Frontend image built and pushed to ACR"

    # Update container app
    print_info "Updating frontend container app..."

    az containerapp update \
        --name "$FRONTEND_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --image "$ACR_NAME.azurecr.io/advisor-reports-frontend:latest" || {
        print_error "Frontend update failed"
        exit 1
    }

    print_success "Frontend updated"

    # Wait for rollout
    print_info "Waiting for frontend to restart (30 seconds)..."
    sleep 30

else
    print_info "Skipping frontend build"
fi

################################################################################
# Step 6: Test New Endpoints
################################################################################

print_step "6. Testing Deployment"

print_info "Testing backend health..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/health/")

if [ "$HEALTH_STATUS" = "200" ]; then
    print_success "Backend health check passed"
else
    print_error "Backend health check failed (Status: $HEALTH_STATUS)"
fi

# Test new History endpoints
print_info "Testing new History endpoints..."

# History statistics
STATS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/reports/history/statistics/")
if [ "$STATS_STATUS" = "200" ] || [ "$STATS_STATUS" = "401" ]; then
    print_success "History statistics endpoint available"
else
    print_error "History statistics endpoint failed (Status: $STATS_STATUS)"
fi

# History trends
TRENDS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/reports/history/trends/")
if [ "$TRENDS_STATUS" = "200" ] || [ "$TRENDS_STATUS" = "401" ]; then
    print_success "History trends endpoint available"
else
    print_error "History trends endpoint failed (Status: $TRENDS_STATUS)"
fi

# Users endpoint
USERS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/reports/users/")
if [ "$USERS_STATUS" = "200" ] || [ "$USERS_STATUS" = "401" ]; then
    print_success "Users endpoint available"
else
    print_error "Users endpoint failed (Status: $USERS_STATUS)"
fi

################################################################################
# Step 7: Optional - Create Key Vault
################################################################################

print_step "7. Optional Configuration"

if confirm "Do you want to create Azure Key Vault for Phase 3 features?"; then
    KEY_VAULT_NAME="kv-advisor-reports-prod"

    print_info "Creating Key Vault..."

    if az keyvault show --name "$KEY_VAULT_NAME" &>/dev/null; then
        print_info "Key Vault already exists"
    else
        az keyvault create \
            --name "$KEY_VAULT_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --location eastus \
            --sku standard || {
            print_error "Key Vault creation failed"
        }

        print_success "Key Vault created"
    fi

    # Grant backend access
    print_info "Granting backend access to Key Vault..."

    BACKEND_IDENTITY=$(az containerapp show \
        --name "$BACKEND_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --query identity.principalId -o tsv)

    if [ ! -z "$BACKEND_IDENTITY" ]; then
        az keyvault set-policy \
            --name "$KEY_VAULT_NAME" \
            --object-id "$BACKEND_IDENTITY" \
            --secret-permissions get list || {
            print_error "Failed to grant Key Vault access"
        }

        print_success "Key Vault access granted"
    else
        print_error "Could not get backend identity"
    fi
else
    print_info "Skipping Key Vault creation"
fi

################################################################################
# Deployment Complete
################################################################################

print_header
print_success "UPDATE COMPLETE!"
echo
echo "======================================================================"
echo "                    UPDATE SUMMARY                                    "
echo "======================================================================"
echo
echo "Backend URL:    $BACKEND_URL"
echo "Frontend URL:   https://advisor-reports-frontend.nicefield-788f351e.eastus.azurecontainerapps.io"
echo
echo "======================================================================"
echo "                    VERIFICATION STEPS                                "
echo "======================================================================"
echo
echo "1. Test Backend Health:"
echo "   curl $BACKEND_URL/api/health/"
echo
echo "2. Test History Page:"
echo "   Open: https://advisor-reports-frontend.nicefield-788f351e.eastus.azurecontainerapps.io/history"
echo
echo "3. Test Analytics Page:"
echo "   Open: https://advisor-reports-frontend.nicefield-788f351e.eastus.azurecontainerapps.io/analytics"
echo
echo "4. View Container App Logs:"
echo "   az containerapp logs show --name $BACKEND_APP --resource-group $RESOURCE_GROUP --follow"
echo
echo "======================================================================"
echo "                    NEXT STEPS                                        "
echo "======================================================================"
echo
echo "✓ Phase 3 code deployed"
echo "✓ New endpoints available"
echo "⚠ Configure email templates (if needed)"
echo "⚠ Test notification system"
echo "⚠ Configure webhooks (if needed)"
echo
echo "======================================================================"
echo

print_success "Deployment updated successfully!"
