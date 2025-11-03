#!/bin/bash
# Deployment script for Debug PDF Engine Configuration v1.3.16

set -e  # Exit on error

VERSION="v1.3.16"
REGISTRY="advisorreportsacr-afc0cmayd8hcekaf.azurecr.io"
IMAGE_NAME="advisor-reports-backend"
RESOURCE_GROUP="rg-azure-advisor-app"

echo "=========================================="
echo "Deploying PDF Engine Debug Version"
echo "Version: $VERSION"
echo "=========================================="
echo ""
echo "Changes in this version:"
echo "  - Enhanced debug logging for PDF engine selection"
echo "  - Investigate why Playwright is not being used"
echo "  - Log settings.PDF_ENGINE value and comparison result"
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
echo "1. Trigger report generation for stuck report:"
echo "   python fix_stuck_reports.py"
echo ""
echo "2. Monitor worker logs for debug output:"
echo "   az containerapp logs show --name advisor-reports-worker \\"
echo "     --resource-group $RESOURCE_GROUP --follow --tail 100"
echo ""
echo "3. Look for these debug messages:"
echo "   - 'PDF Engine Configuration Debug for report...'"
echo "   - 'settings.PDF_ENGINE value: ...'"
echo "   - 'pdf_engine variable: ...'"
echo "   - 'Comparison result (pdf_engine == playwright): ...'"
echo ""
echo "4. This will reveal why Playwright is not being selected"
echo ""
echo "=========================================="
