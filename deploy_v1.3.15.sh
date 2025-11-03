#!/bin/bash
# Deployment script for Auto-Report Generation Fix v1.3.15

set -e  # Exit on error

VERSION="v1.3.15"
REGISTRY="advisorreportsacr.azurecr.io"
IMAGE_NAME="advisor-reports-backend"
RESOURCE_GROUP="rg-azure-advisor-app"

echo "=========================================="
echo "Deploying Auto-Report Generation Fix"
echo "Version: $VERSION"
echo "=========================================="
echo ""
echo "Changes in this version:"
echo "  - Auto-generate HTML/PDF after CSV processing"
echo "  - Fix for stuck reports in 'completed' status"
echo "  - Playwright PDF engine confirmed working"
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
echo "Testing Instructions:"
echo "=========================================="
echo ""
echo "1. Test automatic report generation:"
echo "   - Upload a new CSV file"
echo "   - Wait for CSV processing to complete"
echo "   - Verify HTML and PDF files are auto-generated"
echo ""
echo "2. Fix existing stuck reports:"
echo "   - Run: python fix_stuck_reports.py"
echo "   - This will trigger generation for completed reports without files"
echo ""
echo "3. Monitor worker logs:"
echo "   az containerapp logs show --name advisor-reports-worker \\"
echo "     --resource-group $RESOURCE_GROUP --follow --tail 100"
echo ""
echo "4. Check for successful generation:"
echo "   - Look for 'Triggering automatic report generation' messages"
echo "   - Look for 'Generating HTML report' and 'Generating PDF report' messages"
echo "   - Confirm Playwright is being used (not WeasyPrint)"
echo ""
echo "=========================================="
echo "Configuration Confirmed:"
echo "=========================================="
echo "  - PDF_ENGINE: playwright ✓"
echo "  - Chromium: installed ✓"
echo "  - Auto-generation: enabled ✓"
echo "=========================================="
