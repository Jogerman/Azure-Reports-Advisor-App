#!/bin/bash
# Deployment script for PDF_ENGINE Settings Fix v1.3.17

set -e  # Exit on error

VERSION="v1.3.17"
REGISTRY="advisorreportsacr-afc0cmayd8hcekaf.azurecr.io"
IMAGE_NAME="advisor-reports-backend"
RESOURCE_GROUP="rg-azure-advisor-app"

echo "=========================================="
echo "Deploying PDF_ENGINE Settings Fix"
echo "Version: $VERSION"
echo "=========================================="
echo ""
echo "Changes in this version:"
echo "  - Fixed: PDF_ENGINE setting now in settings/base.py"
echo "  - Fixed: Settings object missing PDF_ENGINE attribute"
echo "  - Now production.py will properly inherit PDF_ENGINE"
echo "  - Playwright should now be used correctly"
echo ""

# Navigate to backend directory
cd azure_advisor_reports

# Step 1: Build Docker image
echo ""
echo "[1/6] Building Docker image..."
docker build -t $REGISTRY/$IMAGE_NAME:$VERSION -f Dockerfile .
docker tag $REGISTRY/$IMAGE_NAME:$VERSION $REGISTRY/$IMAGE_NAME:latest

# Step 2: Login to Azure Container Registry
echo ""
echo "[2/6] Logging in to Azure Container Registry..."
az acr login --name advisorreportsacr

# Step 3: Push images
echo ""
echo "[3/6] Pushing images to registry..."
docker push $REGISTRY/$IMAGE_NAME:$VERSION
docker push $REGISTRY/$IMAGE_NAME:latest

# Step 4: Update Worker (most critical for report generation)
echo ""
echo "[4/6] Updating Celery Worker..."
az containerapp update \
  --name advisor-reports-worker \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY/$IMAGE_NAME:$VERSION

echo "✓ Worker updated"

# Step 5: Update Backend
echo ""
echo "[5/6] Updating Backend..."
az containerapp update \
  --name advisor-reports-backend \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY/$IMAGE_NAME:$VERSION

echo "✓ Backend updated"

# Step 6: Update Beat scheduler
echo ""
echo "[6/6] Updating Celery Beat..."
az containerapp update \
  --name advisor-reports-beat \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY/$IMAGE_NAME:$VERSION

echo "✓ Beat updated"

# Return to root directory
cd ..

# Verification
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Verifying deployments..."
echo ""

# Check worker revision
echo "Worker:"
az containerapp revision list \
  --name advisor-reports-worker \
  --resource-group $RESOURCE_GROUP \
  --query "[0].{Name:name,Active:properties.active,Image:properties.template.containers[0].image,Created:properties.createdTime}" \
  -o table

echo ""
echo "Backend:"
az containerapp revision list \
  --name advisor-reports-backend \
  --resource-group $RESOURCE_GROUP \
  --query "[0].{Name:name,Active:properties.active,Image:properties.template.containers[0].image,Created:properties.createdTime}" \
  -o table

echo ""
echo "Beat:"
az containerapp revision list \
  --name advisor-reports-beat \
  --resource-group $RESOURCE_GROUP \
  --query "[0].{Name:name,Active:properties.active,Image:properties.template.containers[0].image,Created:properties.createdTime}" \
  -o table

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Wait for new report uploads to trigger auto-generation"
echo ""
echo "2. Or manually trigger for existing stuck report:"
echo "   az containerapp exec --name advisor-reports-worker \\"
echo "     --resource-group rg-azure-advisor-app \\"
echo "     --command \"python -c \\\"import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings.production'); import sys; sys.path.insert(0, '/app'); django.setup(); from apps.reports.tasks import generate_report; task = generate_report.delay('b0a78df6-7387-4b02-be7f-37fa2cd93bca', format_type='both'); print(f'Task dispatched: {task.id}')\\\"\""
echo ""
echo "3. Monitor worker logs:"
echo "   az containerapp logs show --name advisor-reports-worker \\"
echo "     --resource-group rg-azure-advisor-app --follow --tail 100"
echo ""
echo "4. Look for successful PDF generation with Playwright:"
echo "   - 'PDF Engine Configuration Debug'"
echo "   - 'settings.PDF_ENGINE value: playwright'"
echo "   - '✓ Using Playwright PDF engine'"
echo ""
echo "=========================================="
