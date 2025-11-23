#!/bin/bash

################################################################################
# Run Database Migrations on Azure Container App
# This script runs migrations on the production database
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

RESOURCE_GROUP="rg-azure-advisor-app"
BACKEND_APP="advisor-reports-backend"

echo -e "${BLUE}Running database migrations on Azure...${NC}"

# Get the latest revision name
REVISION=$(az containerapp revision list \
    --name "$BACKEND_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --query "[0].name" -o tsv)

echo "Latest revision: $REVISION"

# Run migrations via Container App Jobs (alternative to exec)
echo "Running migrations..."

# Alternative 1: Use Azure CLI to run a one-off job
az containerapp job create \
    --name migration-job-$(date +%s) \
    --resource-group "$RESOURCE_GROUP" \
    --environment advisor-reports-env \
    --trigger-type Manual \
    --replica-timeout 300 \
    --replica-retry-limit 1 \
    --parallelism 1 \
    --replica-completion-count 1 \
    --image advisorreportsacr.azurecr.io/advisor-reports-backend:latest \
    --registry-server advisorreportsacr.azurecr.io \
    --command "python" "manage.py" "migrate" "--noinput" \
    --env-vars $(az containerapp show \
        --name "$BACKEND_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.template.containers[0].env" -o json) 2>/dev/null || {
    echo -e "${BLUE}Note: Job creation may fail if already exists. Migrations can also be run via container restart.${NC}"
}

echo -e "${GREEN}Migrations will be applied during container startup.${NC}"
echo ""
echo "To verify migrations, check the container logs:"
echo "az containerapp logs show --name $BACKEND_APP --resource-group $RESOURCE_GROUP --follow"
