# Guía de Deployment a Producción - Azure Advisor Reports Platform v1.2.2

## Problema Identificado

**Error actual:** `AADSTS90002: Tenant '06bf3e54-7223-498a-a4db-2f4e68d7e38d' not found`

**Causa raíz:** El Tenant ID incorrecto está siendo usado en la configuración de producción. El Tenant ID correcto es:
```
9acf6dd6-1978-4d9c-9a9c-c9be95245565 (Solvex Dominicana)
```

## Índice

1. [Variables de Entorno Requeridas](#variables-de-entorno-requeridas)
2. [Configuración de Azure AD](#configuración-de-azure-ad)
3. [Proceso de Build](#proceso-de-build)
4. [Deployment a Azure](#deployment-a-azure)
5. [Verificación Post-Deployment](#verificación-post-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Variables de Entorno Requeridas

### Backend (Django) - Azure App Service Configuration

Configure estas variables en **Azure Portal > App Service > Configuration > Application Settings**:

```bash
# ============================================
# Django Core Settings
# ============================================
SECRET_KEY=<generate-strong-random-key>
DEBUG=False
DJANGO_ENVIRONMENT=production
DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production

# ============================================
# Azure AD Authentication - CRÍTICO
# ============================================
AZURE_CLIENT_ID=<your-azure-ad-app-registration-client-id>
AZURE_CLIENT_SECRET=<your-azure-ad-app-registration-client-secret>
AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565
AZURE_REDIRECT_URI=https://your-backend.azurewebsites.net/api/auth/callback

# ============================================
# Database - Azure PostgreSQL
# ============================================
# Opción 1: Use DATABASE_URL (recomendado para Azure Container Apps)
DATABASE_URL=postgresql://username:password@hostname:5432/dbname?sslmode=require

# Opción 2: Variables individuales (para Azure App Service)
DB_NAME=azure_advisor_reports_prod
DB_USER=dbadmin@your-server
DB_PASSWORD=<strong-password>
DB_HOST=your-server.postgres.database.azure.com
DB_PORT=5432

# ============================================
# Redis Cache - Azure Redis Cache
# ============================================
REDIS_URL=rediss://your-cache.redis.cache.windows.net:6380
REDIS_PASSWORD=<redis-access-key>
CELERY_BROKER_URL=rediss://your-cache.redis.cache.windows.net:6380
CELERY_RESULT_BACKEND=rediss://your-cache.redis.cache.windows.net:6380

# ============================================
# Azure Storage - Blob Storage
# ============================================
AZURE_STORAGE_ACCOUNT_NAME=yourstorageaccount
AZURE_STORAGE_ACCOUNT_KEY=<storage-access-key>
AZURE_STORAGE_CONTAINER=media
AZURE_ACCOUNT_NAME=yourstorageaccount
AZURE_ACCOUNT_KEY=<storage-access-key>
AZURE_CONTAINER=reports

# ============================================
# Application Insights
# ============================================
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=<key>;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/

# ============================================
# Security Settings
# ============================================
ALLOWED_HOSTS=your-backend.azurewebsites.net,advisor-reports-backend.nicefield-788f351e.eastus.azurecontainerapps.io
CORS_ALLOWED_ORIGINS=https://your-frontend.azurewebsites.net,https://advisor-reports-frontend.nicefield-788f351e.eastus.azurecontainerapps.io
CSRF_TRUSTED_ORIGINS=https://your-backend.azurewebsites.net,https://your-frontend.azurewebsites.net,https://advisor-reports-backend.nicefield-788f351e.eastus.azurecontainerapps.io,https://advisor-reports-frontend.nicefield-788f351e.eastus.azurecontainerapps.io

# ============================================
# Gunicorn Settings (Backend)
# ============================================
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=120
GUNICORN_GRACEFUL_TIMEOUT=30
GUNICORN_MAX_REQUESTS=1000
GUNICORN_MAX_REQUESTS_JITTER=50
GUNICORN_LOG_LEVEL=info

# ============================================
# PDF Generation
# ============================================
PDF_ENGINE=playwright
PDF_WAIT_FOR_CHARTS=True
PDF_WAIT_FOR_FONTS=True
PDF_HEADLESS_BROWSER=True
```

### Frontend (React) - Build Arguments

Para el frontend, estas variables se configuran como **build arguments** durante el proceso de build de Docker:

```bash
# ============================================
# API Configuration
# ============================================
REACT_APP_API_URL=https://your-backend.azurewebsites.net/api

# ============================================
# Azure AD Configuration - CRÍTICO
# ============================================
REACT_APP_AZURE_CLIENT_ID=<your-azure-ad-app-registration-client-id>
REACT_APP_AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565
REACT_APP_AZURE_REDIRECT_URI=https://your-frontend.azurewebsites.net

# ============================================
# Build Configuration
# ============================================
REACT_APP_ENVIRONMENT=production
GENERATE_SOURCEMAP=false
NODE_ENV=production

# ============================================
# Feature Flags
# ============================================
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_ERROR_TRACKING=true
```

---

## Configuración de Azure AD

### 1. Verificar App Registration en Azure Portal

1. Navegue a **Azure Portal > Azure Active Directory > App registrations**
2. Seleccione su aplicación (o cree una nueva)
3. Verifique la siguiente información:

```
Application (client) ID: <use-this-as-AZURE_CLIENT_ID>
Directory (tenant) ID: 9acf6dd6-1978-4d9c-9a9c-c9be95245565
Supported account types: Single tenant (Solvex Dominicana)
```

### 2. Configurar Redirect URIs

En **App Registration > Authentication > Redirect URIs**, agregue:

```
Frontend redirect URIs (SPA):
- https://your-frontend.azurewebsites.net
- https://advisor-reports-frontend.nicefield-788f351e.eastus.azurecontainerapps.io
- http://localhost:3000 (para desarrollo)

Backend redirect URIs (Web):
- https://your-backend.azurewebsites.net/api/auth/callback
- https://advisor-reports-backend.nicefield-788f351e.eastus.azurecontainerapps.io/api/auth/callback
- http://localhost:8000/api/auth/callback (para desarrollo)
```

### 3. Configurar API Permissions

En **App Registration > API permissions**, asegúrese de tener:

```
Microsoft Graph:
- User.Read (Delegated)
- profile (Delegated)
- email (Delegated)
- openid (Delegated)
```

### 4. Crear Client Secret

1. Vaya a **App Registration > Certificates & secrets**
2. Click en **New client secret**
3. Descripción: "Production Secret v1.2.2"
4. Expiration: 24 months (recomendado)
5. **Copie el valor inmediatamente** - úselo como `AZURE_CLIENT_SECRET`

---

## Proceso de Build

### Backend (Django)

#### Opción 1: Build Local y Push a Azure Container Registry

```powershell
# 1. Login a Azure Container Registry
az acr login --name yourregistryname

# 2. Build y push de la imagen
cd "D:\Code\Azure Reports\azure_advisor_reports"

docker build -f Dockerfile.prod -t yourregistryname.azurecr.io/azure-advisor-backend:1.2.2 -t yourregistryname.azurecr.io/azure-advisor-backend:latest .

docker push yourregistryname.azurecr.io/azure-advisor-backend:1.2.2
docker push yourregistryname.azurecr.io/azure-advisor-backend:latest
```

#### Opción 2: Build Directamente en Azure (Recomendado)

```powershell
# Build directamente en Azure Container Registry (más rápido)
cd "D:\Code\Azure Reports"

az acr build --registry yourregistryname `
  --image azure-advisor-backend:1.2.2 `
  --image azure-advisor-backend:latest `
  --file azure_advisor_reports/Dockerfile.prod `
  azure_advisor_reports
```

### Frontend (React)

#### Actualizar package.json a versión 1.2.2

```powershell
cd "D:\Code\Azure Reports\frontend"

# Actualizar versión en package.json
# Editar manualmente o usar npm version
npm version 1.2.2 --no-git-tag-version
```

#### Build con Variables de Entorno Correctas

```powershell
# Build de la imagen Docker con build args
docker build -f Dockerfile.prod `
  --build-arg REACT_APP_API_URL=https://your-backend.azurewebsites.net/api `
  --build-arg REACT_APP_AZURE_CLIENT_ID=<your-client-id> `
  --build-arg REACT_APP_AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565 `
  --build-arg REACT_APP_AZURE_REDIRECT_URI=https://your-frontend.azurewebsites.net `
  --build-arg REACT_APP_ENVIRONMENT=production `
  -t yourregistryname.azurecr.io/azure-advisor-frontend:1.2.2 `
  -t yourregistryname.azurecr.io/azure-advisor-frontend:latest `
  .

# Push a Azure Container Registry
docker push yourregistryname.azurecr.io/azure-advisor-frontend:1.2.2
docker push yourregistryname.azurecr.io/azure-advisor-frontend:latest
```

#### Opción: Build Directamente en Azure

```powershell
cd "D:\Code\Azure Reports"

az acr build --registry yourregistryname `
  --image azure-advisor-frontend:1.2.2 `
  --image azure-advisor-frontend:latest `
  --build-arg REACT_APP_API_URL=https://your-backend.azurewebsites.net/api `
  --build-arg REACT_APP_AZURE_CLIENT_ID=<your-client-id> `
  --build-arg REACT_APP_AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565 `
  --build-arg REACT_APP_AZURE_REDIRECT_URI=https://your-frontend.azurewebsites.net `
  --file frontend/Dockerfile.prod `
  frontend
```

---

## Deployment a Azure

### Opción 1: Azure App Service (Web Apps)

#### Backend Deployment

```powershell
# 1. Configurar App Service para usar Container Registry
az webapp config container set `
  --name your-backend-webapp `
  --resource-group your-resource-group `
  --docker-custom-image-name yourregistryname.azurecr.io/azure-advisor-backend:1.2.2 `
  --docker-registry-server-url https://yourregistryname.azurecr.io `
  --docker-registry-server-user <registry-username> `
  --docker-registry-server-password <registry-password>

# 2. Configurar variables de entorno (ver sección Variables de Entorno)
az webapp config appsettings set `
  --name your-backend-webapp `
  --resource-group your-resource-group `
  --settings @backend-appsettings.json

# 3. Restart para aplicar cambios
az webapp restart --name your-backend-webapp --resource-group your-resource-group
```

#### Frontend Deployment

```powershell
# 1. Configurar App Service para usar Container Registry
az webapp config container set `
  --name your-frontend-webapp `
  --resource-group your-resource-group `
  --docker-custom-image-name yourregistryname.azurecr.io/azure-advisor-frontend:1.2.2 `
  --docker-registry-server-url https://yourregistryname.azurecr.io

# 2. Restart
az webapp restart --name your-frontend-webapp --resource-group your-resource-group
```

### Opción 2: Azure Container Apps

#### Backend Deployment

```powershell
# Actualizar Container App con nueva imagen
az containerapp update `
  --name advisor-reports-backend `
  --resource-group your-resource-group `
  --image yourregistryname.azurecr.io/azure-advisor-backend:1.2.2 `
  --set-env-vars `
    AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565 `
    DJANGO_ENVIRONMENT=production `
    # ... otras variables ...
```

#### Frontend Deployment

```powershell
az containerapp update `
  --name advisor-reports-frontend `
  --resource-group your-resource-group `
  --image yourregistryname.azurecr.io/azure-advisor-frontend:1.2.2
```

### Opción 3: CI/CD con GitHub Actions

Cree `.github/workflows/deploy-production.yml`:

```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*.*.*'

env:
  AZURE_TENANT_ID: '9acf6dd6-1978-4d9c-9a9c-c9be95245565'
  REGISTRY_NAME: yourregistryname.azurecr.io

jobs:
  build-and-deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Login to Azure Container Registry
        uses: azure/docker-login@v1
        with:
          login-server: ${{ env.REGISTRY_NAME }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}

      - name: Build and Push Backend
        run: |
          cd azure_advisor_reports
          docker build -f Dockerfile.prod \
            -t ${{ env.REGISTRY_NAME }}/azure-advisor-backend:${{ github.ref_name }} \
            -t ${{ env.REGISTRY_NAME }}/azure-advisor-backend:latest \
            .
          docker push ${{ env.REGISTRY_NAME }}/azure-advisor-backend:${{ github.ref_name }}
          docker push ${{ env.REGISTRY_NAME }}/azure-advisor-backend:latest

      - name: Deploy to Azure App Service
        uses: azure/webapps-deploy@v2
        with:
          app-name: your-backend-webapp
          images: ${{ env.REGISTRY_NAME }}/azure-advisor-backend:${{ github.ref_name }}

  build-and-deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Login to Azure Container Registry
        uses: azure/docker-login@v1
        with:
          login-server: ${{ env.REGISTRY_NAME }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}

      - name: Build and Push Frontend
        run: |
          cd frontend
          docker build -f Dockerfile.prod \
            --build-arg REACT_APP_API_URL=${{ secrets.BACKEND_URL }}/api \
            --build-arg REACT_APP_AZURE_CLIENT_ID=${{ secrets.AZURE_CLIENT_ID }} \
            --build-arg REACT_APP_AZURE_TENANT_ID=${{ env.AZURE_TENANT_ID }} \
            --build-arg REACT_APP_AZURE_REDIRECT_URI=${{ secrets.FRONTEND_URL }} \
            -t ${{ env.REGISTRY_NAME }}/azure-advisor-frontend:${{ github.ref_name }} \
            -t ${{ env.REGISTRY_NAME }}/azure-advisor-frontend:latest \
            .
          docker push ${{ env.REGISTRY_NAME }}/azure-advisor-frontend:${{ github.ref_name }}
          docker push ${{ env.REGISTRY_NAME }}/azure-advisor-frontend:latest

      - name: Deploy to Azure App Service
        uses: azure/webapps-deploy@v2
        with:
          app-name: your-frontend-webapp
          images: ${{ env.REGISTRY_NAME }}/azure-advisor-frontend:${{ github.ref_name }}
```

---

## Verificación Post-Deployment

### 1. Verificar Backend

```powershell
# Health check
curl https://your-backend.azurewebsites.net/api/health/

# Verificar configuración de Azure AD
curl https://your-backend.azurewebsites.net/api/auth/config
```

**Respuesta esperada del config endpoint:**
```json
{
  "clientId": "your-client-id",
  "tenantId": "9acf6dd6-1978-4d9c-9a9c-c9be95245565",
  "redirectUri": "https://your-frontend.azurewebsites.net",
  "authority": "https://login.microsoftonline.com/9acf6dd6-1978-4d9c-9a9c-c9be95245565"
}
```

### 2. Verificar Frontend

```powershell
# Health check
curl https://your-frontend.azurewebsites.net/health

# Verificar que la aplicación cargue
curl https://your-frontend.azurewebsites.net/
```

### 3. Verificar Autenticación End-to-End

1. Abra el frontend en el navegador: `https://your-frontend.azurewebsites.net`
2. Haga clic en "Sign In"
3. Debería redirigir a Microsoft login con el tenant correcto (Solvex Dominicana)
4. Después del login, verifique que el token sea válido en las Developer Tools:
   - Abra Developer Tools (F12)
   - Vaya a Application > Local Storage
   - Busque las claves de MSAL y verifique que el `tid` sea `9acf6dd6-1978-4d9c-9a9c-c9be95245565`

### 4. Verificar Application Insights

```powershell
# Verificar que los logs estén llegando
az monitor app-insights query `
  --app your-app-insights `
  --analytics-query "traces | where timestamp > ago(1h) | take 10"
```

### 5. Verificar Base de Datos

```powershell
# Conectarse a la base de datos PostgreSQL
psql "host=your-server.postgres.database.azure.com port=5432 dbname=azure_advisor_reports_prod user=dbadmin@your-server sslmode=require"

# Verificar migraciones
SELECT * FROM django_migrations ORDER BY applied DESC LIMIT 10;

# Verificar usuarios
SELECT id, email, first_name, last_name, is_active FROM authentication_user LIMIT 10;
```

---

## Troubleshooting

### Error: Tenant Not Found

**Error:** `AADSTS90002: Tenant '06bf3e54-7223-498a-a4db-2f4e68d7e38d' not found`

**Solución:**
1. Verifique que `AZURE_TENANT_ID` esté configurado correctamente en ambos frontend y backend
2. Para backend: Verifique en Azure Portal > App Service > Configuration
3. Para frontend: Reconstruya la imagen con el build arg correcto
4. El Tenant ID correcto es: `9acf6dd6-1978-4d9c-9a9c-c9be95245565`

### Error: Invalid Client

**Error:** `AADSTS700016: Application with identifier 'xxx' was not found in the directory`

**Solución:**
1. Verifique que el `AZURE_CLIENT_ID` corresponda a la aplicación registrada en el tenant correcto
2. Verifique que la aplicación esté en el mismo tenant (9acf6dd6-1978-4d9c-9a9c-c9be95245565)

### Error: Redirect URI Mismatch

**Error:** `AADSTS50011: The redirect URI specified in the request does not match the redirect URIs configured`

**Solución:**
1. Vaya a Azure Portal > App Registration > Authentication
2. Agregue el redirect URI exacto mostrado en el error
3. Para SPA (frontend): Use tipo "Single-page application"
4. Para backend: Use tipo "Web"

### Error: CORS

**Error:** `Access to fetch at 'xxx' from origin 'yyy' has been blocked by CORS policy`

**Solución:**
1. Verifique `CORS_ALLOWED_ORIGINS` en backend incluye la URL del frontend
2. Verifique `CSRF_TRUSTED_ORIGINS` incluye ambas URLs (frontend y backend)
3. Asegúrese de usar HTTPS en producción

### Error: Database Connection

**Error:** `could not connect to server: Connection timed out`

**Solución:**
1. Verifique firewall rules en Azure PostgreSQL:
   ```powershell
   az postgres server firewall-rule create \
     --resource-group your-resource-group \
     --server-name your-server \
     --name AllowAppService \
     --start-ip-address 0.0.0.0 \
     --end-ip-address 0.0.0.0
   ```
2. Verifique connection strings y SSL mode

### Error: Container Won't Start

**Error:** Container exits with code 1 or 137

**Solución:**
1. Verifique logs:
   ```powershell
   az webapp log tail --name your-backend-webapp --resource-group your-resource-group
   ```
2. Verifique que todas las variables de entorno requeridas estén configuradas
3. Verifique que el entrypoint script tenga permisos de ejecución

---

## Checklist de Pre-Deployment

Antes de hacer deployment a producción, verifique:

- [ ] Tenant ID correcto configurado: `9acf6dd6-1978-4d9c-9a9c-c9be95245565`
- [ ] Client ID y Client Secret válidos para el tenant
- [ ] Redirect URIs configurados en Azure AD App Registration
- [ ] Todas las variables de entorno configuradas en App Service
- [ ] Database migrations aplicadas
- [ ] Static files collected
- [ ] Redis cache accesible
- [ ] Blob storage configurado
- [ ] Application Insights configurado
- [ ] Firewall rules de PostgreSQL configurados
- [ ] SSL/HTTPS habilitado
- [ ] Health checks funcionando
- [ ] Celery workers corriendo (si aplica)
- [ ] Backup de base de datos configurado
- [ ] Monitoring y alertas configuradas

---

## Seguridad y Mejores Prácticas

### 1. Secretos

- **NUNCA** hardcodee secretos en código o Dockerfiles
- Use Azure Key Vault para almacenar secretos sensibles
- Rote los secretos regularmente (cada 90 días recomendado)
- Use Managed Identities cuando sea posible para evitar contraseñas

### 2. Network Security

- Configure Network Security Groups (NSGs) apropiados
- Use Private Endpoints para servicios Azure (PostgreSQL, Redis, Storage)
- Implemente Azure Front Door o Application Gateway para WAF
- Use Azure DDoS Protection

### 3. Monitoring

- Configure alertas en Application Insights para errores críticos
- Monitoree métricas de rendimiento (CPU, memoria, response times)
- Configure availability tests
- Revise logs regularmente

### 4. Backup y DR

- Configure automated backups para PostgreSQL (punto en el tiempo)
- Pruebe el proceso de restore regularmente
- Mantenga backups en múltiples regiones
- Documente el proceso de disaster recovery

### 5. Cost Optimization

- Use Azure Cost Management para monitorear gastos
- Configure autoscaling basado en métricas
- Use reserved instances para recursos predecibles
- Revise y elimine recursos no utilizados

---

## Contacto y Soporte

Para problemas o preguntas relacionadas con el deployment:

- **Equipo de Desarrollo:** [Agregar contacto]
- **Azure Support:** https://portal.azure.com > Help + support
- **Documentación:** https://docs.microsoft.com/azure/

---

**Última actualización:** 2025-10-30
**Versión:** 1.2.2
**Autor:** DevOps Team
