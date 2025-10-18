# Frontend Deployment Guide
**Azure Advisor Reports Platform - Production Deployment**

Last Updated: October 4, 2025
Version: 1.0.0

---

## Prerequisites

### Required Tools
- Node.js 18+
- npm 9+
- Docker Desktop
- Azure CLI 2.50+
- PowerShell 7+ (Windows)

---

## Local Production Build

### Step 1: Configure Environment
```powershell
cd frontend
Copy-Item .env.production.local.example .env.production.local
notepad .env.production.local
```

### Step 2: Run Build
```powershell
.\scripts\optimize-build.ps1
```

### Step 3: Test Locally
```powershell
npm run serve:prod
# Open http://localhost:3000
```

---

## Docker Deployment

### Build Image
```powershell
docker build -f Dockerfile.prod `
  --build-arg REACT_APP_API_URL=https://backend.azurewebsites.net/api `
  --build-arg REACT_APP_AZURE_CLIENT_ID=your-client-id `
  --build-arg REACT_APP_AZURE_TENANT_ID=your-tenant-id `
  --build-arg REACT_APP_AZURE_REDIRECT_URI=https://frontend.azurewebsites.net `
  -t azure-advisor-frontend:latest .
```

### Run Locally
```powershell
docker run -p 8080:80 azure-advisor-frontend:latest
# Open http://localhost:8080
```

---

## Azure App Service Deployment

### Using Azure CLI
```powershell
# Variables
$resourceGroup = "rg-azure-advisor-prod"
$appName = "azure-advisor-frontend"

# Create App Service
az webapp create `
  --resource-group $resourceGroup `
  --plan asp-azure-advisor-prod `
  --name $appName `
  --deployment-container-image-name azure-advisor-frontend:latest

# Configure environment
az webapp config appsettings set `
  --name $appName `
  --resource-group $resourceGroup `
  --settings `
    REACT_APP_API_URL=https://backend.azurewebsites.net/api `
    REACT_APP_AZURE_CLIENT_ID=your-client-id `
    REACT_APP_AZURE_TENANT_ID=your-tenant-id `
    REACT_APP_AZURE_REDIRECT_URI=https://$appName.azurewebsites.net
```

---

## Environment Variables

| Variable | Value | Required |
|----------|-------|----------|
| REACT_APP_API_URL | Backend API URL | Yes |
| REACT_APP_AZURE_CLIENT_ID | Azure AD Client ID | Yes |
| REACT_APP_AZURE_TENANT_ID | Azure AD Tenant ID | Yes |
| REACT_APP_AZURE_REDIRECT_URI | Frontend URL | Yes |

---

## Troubleshooting

### Build Fails
- Check Node.js version (18+)
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall

### Docker Image Too Large
- Verify multi-stage build (expected: ~100-150MB)

### Azure App Not Starting
```powershell
# Check logs
az webapp log tail --name $appName --resource-group $resourceGroup

# Restart
az webapp restart --name $appName --resource-group $resourceGroup
```

---

## Related Documentation
- USER_MANUAL.md - End-user guide
- ADMIN_GUIDE.md - Admin operations
- AZURE_DEPLOYMENT_GUIDE.md - Azure infrastructure setup
- GITHUB_SECRETS_GUIDE.md - CI/CD configuration

---

**End of Frontend Deployment Guide**
