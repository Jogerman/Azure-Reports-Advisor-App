#!/bin/bash
# Deployment script for CSV Processing Fix v1.3.20
# Fixes: CSV parsing errors with commas within quoted fields

set -e  # Exit on error

VERSION="v1.3.20"
REGISTRY="advisorreportsacr-afc0cmayd8hcekaf.azurecr.io"
IMAGE_NAME="advisor-reports-backend"
RESOURCE_GROUP="rg-azure-advisor-app"

echo "=========================================="
echo "Deploying CSV Fix - Version $VERSION"
echo "=========================================="
echo ""
echo "Changes in this version:"
echo "- Fixed CSV parsing to handle commas within quoted fields"
echo "- Added Python engine for better error tolerance"
echo "- Added retry logic with lenient settings"
echo "- Improved error logging for CSV parsing issues"
echo ""

# Navigate to backend directory
cd azure_advisor_reports

# Step 1: Build Docker image
echo ""
echo "[1/6] Building Docker image..."
docker build -t $REGISTRY/$IMAGE_NAME:$VERSION -f Dockerfile.prod .

# Step 2: Login to Azure Container Registry
echo ""
echo "[2/6] Logging in to Azure Container Registry..."
az acr login --name advisorreportsacr

# Step 3: Push image
echo ""
echo "[3/6] Pushing image to registry..."
docker push $REGISTRY/$IMAGE_NAME:$VERSION

# Step 4: Update Worker (most critical - this is where CSV processing happens)
echo ""
echo "[4/6] Updating Celery Worker..."
az containerapp update \
  --name advisor-reports-worker \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY/$IMAGE_NAME:$VERSION

echo "✓ Worker updated"

# Step 5: Update Backend (also processes CSVs via API)
echo ""
echo "[5/6] Updating Backend..."
az containerapp update \
  --name advisor-reports-backend \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY/$IMAGE_NAME:$VERSION

echo "✓ Backend updated"

# Step 6: Update Beat scheduler (runs scheduled CSV processing)
echo ""
echo "[6/6] Updating Celery Beat..."
az containerapp update \
  --name advisor-reports-beat \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY/$IMAGE_NAME:$VERSION

echo "✓ Beat updated"

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
echo "1. Monitor worker logs for CSV processing:"
echo "   az containerapp logs show --name advisor-reports-worker --resource-group $RESOURCE_GROUP --follow"
echo ""
echo "2. Test CSV upload and processing:"
echo "   - Upload an Azure Advisor CSV file"
echo "   - Process the CSV"
echo "   - Verify no 'Error tokenizing data' errors"
echo "   - Check that recommendations are extracted successfully"
echo ""
echo "3. Expected log messages (GOOD):"
echo "   - 'Successfully read CSV with encoding: utf-8'"
echo "   - 'Extracted N recommendations'"
echo "   - 'CSV processing completed successfully'"
echo ""
echo "4. If you see warnings about skipped lines:"
echo "   - This is normal for malformed rows"
echo "   - Parser will warn but continue processing"
echo "   - Check CSV file manually for issues"
echo ""
echo "=========================================="
