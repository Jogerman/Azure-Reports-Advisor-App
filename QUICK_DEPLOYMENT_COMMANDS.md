# Quick Deployment Commands - Azure Advisor Reports v1.2.2

## Tenant ID Correcto

```
9acf6dd6-1978-4d9c-9a9c-c9be95245565 (Solvex Dominicana)
```

---

## Pre-requisitos Rápidos

```powershell
# Verificar Azure CLI
az --version

# Login a Azure con tenant correcto
az login --tenant 9acf6dd6-1978-4d9c-9a9c-c9be95245565

# Verificar subscription
az account show

# Verificar Docker
docker version
```

---

## Variables de Entorno - Actualizar con Valores Reales

```powershell
# Definir variables (ACTUALIZAR CON VALORES REALES)
$REGISTRY_NAME = "yourregistryname"
$RESOURCE_GROUP = "your-resource-group"
$BACKEND_APP = "your-backend-webapp"
$FRONTEND_APP = "your-frontend-webapp"
$CLIENT_ID = "your-azure-client-id"
$CLIENT_SECRET = "your-azure-client-secret"
$BACKEND_URL = "https://your-backend.azurewebsites.net"
$FRONTEND_URL = "https://your-frontend.azurewebsites.net"
$VERSION = "1.2.2"
$TENANT_ID = "9acf6dd6-1978-4d9c-9a9c-c9be95245565"
```

---

## Opción 1: Deployment Automatizado (Recomendado)

### Paso 1: Verificar Configuración

```powershell
cd "D:\Code\Azure Reports"

.\verify-deployment-config.ps1 `
  -BackendAppName $BACKEND_APP `
  -FrontendAppName $FRONTEND_APP `
  -ResourceGroup $RESOURCE_GROUP
```

### Paso 2: Deployment Completo

```powershell
.\deploy-production.ps1 `
  -RegistryName $REGISTRY_NAME `
  -ResourceGroup $RESOURCE_GROUP `
  -Version $VERSION `
  -BackendAppName $BACKEND_APP `
  -FrontendAppName $FRONTEND_APP `
  -AzureClientId $CLIENT_ID `
  -BackendUrl $BACKEND_URL `
  -FrontendUrl $FRONTEND_URL
```

---

## Opción 2: Deployment Manual por Componente

### Backend

#### 1. Login a ACR

```powershell
az acr login --name $REGISTRY_NAME
```

#### 2. Build Backend Image

```powershell
cd "D:\Code\Azure Reports"

az acr build --registry $REGISTRY_NAME `
  --image azure-advisor-backend:$VERSION `
  --image azure-advisor-backend:latest `
  --file azure_advisor_reports/Dockerfile.prod `
  --platform linux `
  azure_advisor_reports
```

#### 3. Configurar Backend App Service Variables

**IMPORTANTE: Configurar en Azure Portal o usar script:**

```powershell
# Crear archivo backend-appsettings.json con valores reales
# Luego aplicar:

az webapp config appsettings set `
  --name $BACKEND_APP `
  --resource-group $RESOURCE_GROUP `
  --settings `
    AZURE_TENANT_ID=$TENANT_ID `
    AZURE_CLIENT_ID=$CLIENT_ID `
    AZURE_CLIENT_SECRET=$CLIENT_SECRET `
    AZURE_REDIRECT_URI=$FRONTEND_URL `
    DEBUG=False `
    DJANGO_ENVIRONMENT=production `
    DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production `
    SECRET_KEY="GENERATE_NEW_SECRET_KEY_HERE"
```

**Generar SECRET_KEY:**
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### 4. Deploy Backend

```powershell
az webapp config container set `
  --name $BACKEND_APP `
  --resource-group $RESOURCE_GROUP `
  --docker-custom-image-name "$REGISTRY_NAME.azurecr.io/azure-advisor-backend:$VERSION"

az webapp restart --name $BACKEND_APP --resource-group $RESOURCE_GROUP
```

### Frontend

#### 1. Build Frontend Image

```powershell
cd "D:\Code\Azure Reports"

az acr build --registry $REGISTRY_NAME `
  --image azure-advisor-frontend:$VERSION `
  --image azure-advisor-frontend:latest `
  --build-arg REACT_APP_API_URL="$BACKEND_URL/api" `
  --build-arg REACT_APP_AZURE_CLIENT_ID=$CLIENT_ID `
  --build-arg REACT_APP_AZURE_TENANT_ID=$TENANT_ID `
  --build-arg REACT_APP_AZURE_REDIRECT_URI=$FRONTEND_URL `
  --build-arg REACT_APP_ENVIRONMENT=production `
  --file frontend/Dockerfile.prod `
  --platform linux `
  frontend
```

#### 2. Deploy Frontend

```powershell
az webapp config container set `
  --name $FRONTEND_APP `
  --resource-group $RESOURCE_GROUP `
  --docker-custom-image-name "$REGISTRY_NAME.azurecr.io/azure-advisor-frontend:$VERSION"

az webapp restart --name $FRONTEND_APP --resource-group $RESOURCE_GROUP
```

---

## Opción 3: Build Local y Push

### Backend Build Local

```powershell
cd "D:\Code\Azure Reports\azure_advisor_reports"

docker build -f Dockerfile.prod `
  -t "$REGISTRY_NAME.azurecr.io/azure-advisor-backend:$VERSION" `
  -t "$REGISTRY_NAME.azurecr.io/azure-advisor-backend:latest" `
  .

docker push "$REGISTRY_NAME.azurecr.io/azure-advisor-backend:$VERSION"
docker push "$REGISTRY_NAME.azurecr.io/azure-advisor-backend:latest"
```

### Frontend Build Local

```powershell
cd "D:\Code\Azure Reports\frontend"

docker build -f Dockerfile.prod `
  --build-arg REACT_APP_API_URL="$BACKEND_URL/api" `
  --build-arg REACT_APP_AZURE_CLIENT_ID=$CLIENT_ID `
  --build-arg REACT_APP_AZURE_TENANT_ID=$TENANT_ID `
  --build-arg REACT_APP_AZURE_REDIRECT_URI=$FRONTEND_URL `
  --build-arg REACT_APP_ENVIRONMENT=production `
  -t "$REGISTRY_NAME.azurecr.io/azure-advisor-frontend:$VERSION" `
  -t "$REGISTRY_NAME.azurecr.io/azure-advisor-frontend:latest" `
  .

docker push "$REGISTRY_NAME.azurecr.io/azure-advisor-frontend:$VERSION"
docker push "$REGISTRY_NAME.azurecr.io/azure-advisor-frontend:latest"
```

---

## Verificación Post-Deployment

### Health Checks

```powershell
# Backend health
curl "$BACKEND_URL/api/health/"

# Frontend health
curl "$FRONTEND_URL/health"
```

### Tenant ID Verification

```powershell
# Verificar configuración de autenticación
curl "$BACKEND_URL/api/auth/config"

# Debe retornar:
# {
#   "clientId": "your-client-id",
#   "tenantId": "9acf6dd6-1978-4d9c-9a9c-c9be95245565",
#   ...
# }
```

### Logs

```powershell
# Backend logs
az webapp log tail --name $BACKEND_APP --resource-group $RESOURCE_GROUP

# Frontend logs
az webapp log tail --name $FRONTEND_APP --resource-group $RESOURCE_GROUP
```

### Application Insights

```powershell
# Últimos errores
az monitor app-insights query `
  --app your-app-insights-name `
  --analytics-query "traces | where severityLevel >= 3 | where timestamp > ago(1h) | take 20"
```

---

## Comandos de Troubleshooting

### Backend Issues

```powershell
# Ver configuración actual
az webapp config appsettings list `
  --name $BACKEND_APP `
  --resource-group $RESOURCE_GROUP

# Ver imagen actual
az webapp config container show `
  --name $BACKEND_APP `
  --resource-group $RESOURCE_GROUP

# SSH al container (si está habilitado)
az webapp ssh --name $BACKEND_APP --resource-group $RESOURCE_GROUP
```

### Frontend Issues

```powershell
# Ver imagen actual
az webapp config container show `
  --name $FRONTEND_APP `
  --resource-group $RESOURCE_GROUP

# Revisar logs de startup
az webapp log download `
  --name $FRONTEND_APP `
  --resource-group $RESOURCE_GROUP `
  --log-file frontend-logs.zip
```

### Database Issues

```powershell
# Test conexión a PostgreSQL
psql "host=your-server.postgres.database.azure.com port=5432 dbname=azure_advisor_reports_prod user=dbadmin sslmode=require"

# Ver migraciones aplicadas
# Desde SSH del backend container:
python manage.py showmigrations

# Aplicar migraciones manualmente si es necesario
python manage.py migrate --no-input
```

---

## Rollback Rápido

### Rollback Backend

```powershell
# Cambiar a versión anterior (ejemplo: 1.2.1)
az webapp config container set `
  --name $BACKEND_APP `
  --resource-group $RESOURCE_GROUP `
  --docker-custom-image-name "$REGISTRY_NAME.azurecr.io/azure-advisor-backend:1.2.1"

az webapp restart --name $BACKEND_APP --resource-group $RESOURCE_GROUP
```

### Rollback Frontend

```powershell
az webapp config container set `
  --name $FRONTEND_APP `
  --resource-group $RESOURCE_GROUP `
  --docker-custom-image-name "$REGISTRY_NAME.azurecr.io/azure-advisor-frontend:1.2.1"

az webapp restart --name $FRONTEND_APP --resource-group $RESOURCE_GROUP
```

---

## Configuración de Azure AD (Una Sola Vez)

### 1. Crear App Registration

```powershell
# Via Azure Portal (recomendado):
# Azure AD > App registrations > New registration

# Configurar:
# - Name: Azure Advisor Reports
# - Supported account types: Single tenant
# - Redirect URI (SPA): https://your-frontend.azurewebsites.net
```

### 2. Configurar Redirect URIs

```
Frontend (SPA):
- https://your-frontend.azurewebsites.net
- http://localhost:3000 (dev)

Backend (Web):
- https://your-backend.azurewebsites.net/api/auth/callback
- http://localhost:8000/api/auth/callback (dev)
```

### 3. API Permissions

```
Microsoft Graph:
- User.Read (Delegated)
- profile (Delegated)
- email (Delegated)
- openid (Delegated)

Grant admin consent
```

### 4. Client Secret

```
Certificates & secrets > New client secret
Description: Production v1.2.2
Expires: 24 months
COPIAR EL VALUE INMEDIATAMENTE
```

---

## Monitoring Setup

### Crear Alertas

```powershell
# Response time alert
az monitor metrics alert create `
  --name "High Response Time" `
  --resource-group $RESOURCE_GROUP `
  --scopes "/subscriptions/{sub-id}/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$BACKEND_APP" `
  --condition "avg ResponseTime > 3000" `
  --window-size 5m `
  --evaluation-frequency 1m

# Error rate alert
az monitor metrics alert create `
  --name "High Error Rate" `
  --resource-group $RESOURCE_GROUP `
  --scopes "/subscriptions/{sub-id}/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$BACKEND_APP" `
  --condition "total Http5xx > 10" `
  --window-size 5m `
  --evaluation-frequency 1m
```

---

## Database Backup y Restore

### Manual Backup

```powershell
# PostgreSQL backup
az postgres flexible-server backup create `
  --name manual-backup-v1.2.2 `
  --resource-group $RESOURCE_GROUP `
  --server-name your-postgres-server
```

### Restore

```powershell
az postgres flexible-server restore `
  --name your-server-restored `
  --resource-group $RESOURCE_GROUP `
  --source-server your-postgres-server `
  --restore-time "2025-10-30T10:00:00Z"
```

---

## Útiles One-Liners

```powershell
# Ver todas las imágenes en ACR
az acr repository list --name $REGISTRY_NAME --output table

# Ver tags de una imagen
az acr repository show-tags --name $REGISTRY_NAME --repository azure-advisor-backend --output table

# Ver configuración completa de backend app
az webapp show --name $BACKEND_APP --resource-group $RESOURCE_GROUP --output json

# Ver métricas de CPU
az monitor metrics list `
  --resource "/subscriptions/{sub-id}/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$BACKEND_APP" `
  --metric CpuPercentage `
  --start-time 2025-10-30T00:00:00Z `
  --interval PT1H

# Limpiar imágenes antiguas de ACR (cuidado!)
# az acr repository delete --name $REGISTRY_NAME --image azure-advisor-backend:old-version --yes
```

---

## Contactos de Emergencia

**DevOps Team:**
- Email: [Agregar]
- Slack: [Agregar]
- Phone: [Agregar]

**Azure Support:**
- Portal: https://portal.azure.com
- Phone: [Agregar número de soporte]

---

## Referencias Rápidas

- **Deployment Guide:** `PRODUCTION_DEPLOYMENT_GUIDE.md`
- **Checklist:** `DEPLOYMENT_CHECKLIST.md`
- **Summary:** `DEPLOYMENT_SUMMARY.md`
- **Scripts:** `deploy-production.ps1`, `verify-deployment-config.ps1`

---

**Version:** 1.2.2
**Tenant ID:** 9acf6dd6-1978-4d9c-9a9c-c9be95245565 (Solvex Dominicana)
**Last Updated:** 2025-10-30
