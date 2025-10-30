# Azure Advisor Reports - Production Deployment Checklist v1.2.2

## Pre-Deployment

### 1. Azure AD Configuration

- [ ] Verificar App Registration existe en Azure Portal
- [ ] Confirmar Tenant ID: `9acf6dd6-1978-4d9c-9a9c-c9be95245565` (Solvex Dominicana)
- [ ] Copiar Client ID de la aplicación
- [ ] Generar nuevo Client Secret (expira en 24 meses)
- [ ] Configurar Redirect URIs:
  - [ ] Frontend SPA: `https://your-frontend.azurewebsites.net`
  - [ ] Backend Web: `https://your-backend.azurewebsites.net/api/auth/callback`
  - [ ] Localhost para dev: `http://localhost:3000` y `http://localhost:8000/api/auth/callback`
- [ ] Verificar API Permissions:
  - [ ] Microsoft Graph: User.Read
  - [ ] Microsoft Graph: profile
  - [ ] Microsoft Graph: email
  - [ ] Microsoft Graph: openid
- [ ] Grant admin consent si es requerido

### 2. Azure Resources

#### PostgreSQL Database
- [ ] Crear Azure Database for PostgreSQL Flexible Server
- [ ] Configurar firewall rules:
  - [ ] Allow Azure Services
  - [ ] Allow App Service outbound IPs
- [ ] Crear database: `azure_advisor_reports_prod`
- [ ] Crear usuario de aplicación con permisos apropiados
- [ ] Habilitar SSL/TLS enforcement
- [ ] Configurar automated backups (retención: 35 días recomendado)
- [ ] Copiar connection string

#### Redis Cache
- [ ] Crear Azure Cache for Redis (Standard C1 mínimo)
- [ ] Habilitar SSL port (6380)
- [ ] Configurar firewall rules
- [ ] Copiar Primary connection string
- [ ] Copiar Primary access key

#### Blob Storage
- [ ] Crear Storage Account (Standard LRS o GRS)
- [ ] Crear container: `media`
- [ ] Crear container: `reports`
- [ ] Configurar CORS si es necesario
- [ ] Copiar Account name
- [ ] Copiar Access key

#### Application Insights
- [ ] Crear Application Insights resource
- [ ] Copiar Connection String
- [ ] Configurar alertas básicas:
  - [ ] Response time > 3s
  - [ ] Failed requests > 5%
  - [ ] Exception rate > 10/min

#### Container Registry
- [ ] Crear Azure Container Registry (Standard tier mínimo)
- [ ] Habilitar Admin user
- [ ] Copiar Login server
- [ ] Copiar Username
- [ ] Copiar Password

#### App Service Plans
- [ ] Crear App Service Plan para Backend (P1v3 mínimo)
- [ ] Crear App Service Plan para Frontend (B2 mínimo)
- [ ] O usar Azure Container Apps (más rentable)

### 3. Local Preparation

- [ ] Código actualizado en branch main
- [ ] Todos los tests pasando: `npm test` y `pytest`
- [ ] Version actualizada a 1.2.2 en `frontend/package.json`
- [ ] Docker Desktop corriendo
- [ ] Azure CLI instalado y actualizado
- [ ] Autenticado en Azure CLI: `az login`
- [ ] Tenant correcto seleccionado

### 4. Environment Variables Preparation

- [ ] Crear archivo con variables de entorno del backend
- [ ] Crear archivo con build args del frontend
- [ ] Generar SECRET_KEY fuerte (Django):
  ```python
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- [ ] Verificar todas las URLs usan HTTPS en producción
- [ ] Verificar Tenant ID en todas las configuraciones

---

## Build Phase

### Backend Build

- [ ] Navegar a directorio del proyecto
- [ ] Login a Azure Container Registry:
  ```powershell
  az acr login --name yourregistryname
  ```
- [ ] Build backend image:
  ```powershell
  cd azure_advisor_reports
  az acr build --registry yourregistryname \
    --image azure-advisor-backend:1.2.2 \
    --image azure-advisor-backend:latest \
    --file Dockerfile.prod \
    --platform linux \
    .
  ```
- [ ] Verificar imagen en ACR:
  ```powershell
  az acr repository show-tags --name yourregistryname --repository azure-advisor-backend
  ```

### Frontend Build

- [ ] Actualizar version en package.json a 1.2.2
- [ ] Build frontend image con variables correctas:
  ```powershell
  cd frontend
  az acr build --registry yourregistryname \
    --image azure-advisor-frontend:1.2.2 \
    --image azure-advisor-frontend:latest \
    --build-arg REACT_APP_API_URL=https://your-backend.azurewebsites.net/api \
    --build-arg REACT_APP_AZURE_CLIENT_ID=<your-client-id> \
    --build-arg REACT_APP_AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565 \
    --build-arg REACT_APP_AZURE_REDIRECT_URI=https://your-frontend.azurewebsites.net \
    --file Dockerfile.prod \
    --platform linux \
    .
  ```
- [ ] Verificar imagen en ACR

**Alternativa: Usar script automatizado**
- [ ] Configurar parámetros en `deploy-production.ps1`
- [ ] Ejecutar build:
  ```powershell
  .\deploy-production.ps1 `
    -RegistryName yourregistryname `
    -ResourceGroup your-resource-group `
    -Version 1.2.2 `
    -AzureClientId <client-id> `
    -BackendUrl https://your-backend.azurewebsites.net `
    -FrontendUrl https://your-frontend.azurewebsites.net `
    -BuildOnly
  ```

---

## Deployment Phase

### Backend Deployment

#### Opción A: Azure App Service

- [ ] Crear Web App para Backend:
  ```powershell
  az webapp create \
    --name your-backend-webapp \
    --resource-group your-resource-group \
    --plan your-backend-plan \
    --deployment-container-image-name yourregistryname.azurecr.io/azure-advisor-backend:1.2.2
  ```

- [ ] Configurar Container Registry credentials:
  ```powershell
  az webapp config container set \
    --name your-backend-webapp \
    --resource-group your-resource-group \
    --docker-custom-image-name yourregistryname.azurecr.io/azure-advisor-backend:1.2.2 \
    --docker-registry-server-url https://yourregistryname.azurecr.io \
    --docker-registry-server-user <username> \
    --docker-registry-server-password <password>
  ```

- [ ] Configurar variables de entorno:
  ```powershell
  # Método 1: Una por una
  az webapp config appsettings set \
    --name your-backend-webapp \
    --resource-group your-resource-group \
    --settings \
      AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565 \
      AZURE_CLIENT_ID=<client-id> \
      AZURE_CLIENT_SECRET=<client-secret> \
      # ... otras variables

  # Método 2: Desde archivo JSON
  az webapp config appsettings set \
    --name your-backend-webapp \
    --resource-group your-resource-group \
    --settings @backend-appsettings.json
  ```

- [ ] Configurar siempre on:
  ```powershell
  az webapp config set \
    --name your-backend-webapp \
    --resource-group your-resource-group \
    --always-on true
  ```

- [ ] Restart app:
  ```powershell
  az webapp restart --name your-backend-webapp --resource-group your-resource-group
  ```

#### Opción B: Azure Container Apps

- [ ] Crear Container App:
  ```powershell
  az containerapp create \
    --name advisor-reports-backend \
    --resource-group your-resource-group \
    --environment your-container-env \
    --image yourregistryname.azurecr.io/azure-advisor-backend:1.2.2 \
    --target-port 8000 \
    --ingress external \
    --registry-server yourregistryname.azurecr.io \
    --registry-username <username> \
    --registry-password <password> \
    --env-vars \
      AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565 \
      AZURE_CLIENT_ID=<client-id> \
      # ... otras variables
  ```

### Frontend Deployment

#### Opción A: Azure App Service

- [ ] Crear Web App para Frontend:
  ```powershell
  az webapp create \
    --name your-frontend-webapp \
    --resource-group your-resource-group \
    --plan your-frontend-plan \
    --deployment-container-image-name yourregistryname.azurecr.io/azure-advisor-frontend:1.2.2
  ```

- [ ] Configurar Container Registry credentials

- [ ] Restart app

#### Opción B: Azure Container Apps

- [ ] Crear Container App para frontend

### Database Migration

- [ ] Conectar a backend app (SSH o kudu console)
- [ ] Ejecutar migraciones:
  ```bash
  python manage.py migrate --no-input
  ```
- [ ] Crear superuser si es necesario:
  ```bash
  python manage.py createsuperuser
  ```
- [ ] Collect static files (si no se hizo en entrypoint):
  ```bash
  python manage.py collectstatic --no-input
  ```

**Alternativa: Usar Job en Container Apps**
- [ ] Crear job para migrations
- [ ] Ejecutar job antes de deployment

---

## Post-Deployment Verification

### 1. Health Checks

- [ ] Backend health check:
  ```powershell
  curl https://your-backend.azurewebsites.net/api/health/
  ```
  Esperado: HTTP 200 con `{"status": "healthy"}`

- [ ] Frontend health check:
  ```powershell
  curl https://your-frontend.azurewebsites.net/health
  ```
  Esperado: HTTP 200 con "healthy"

### 2. Azure AD Configuration Verification

- [ ] Verificar endpoint de configuración:
  ```powershell
  curl https://your-backend.azurewebsites.net/api/auth/config
  ```
  Verificar que retorna:
  ```json
  {
    "clientId": "your-client-id",
    "tenantId": "9acf6dd6-1978-4d9c-9a9c-c9be95245565",
    "authority": "https://login.microsoftonline.com/9acf6dd6-1978-4d9c-9a9c-c9be95245565"
  }
  ```

### 3. Authentication Flow Testing

- [ ] Abrir frontend en browser: `https://your-frontend.azurewebsites.net`
- [ ] Click en "Sign In"
- [ ] Verificar redirect a Microsoft login
- [ ] Verificar que muestra "Solvex Dominicana" como organización
- [ ] Login con credenciales de prueba
- [ ] Verificar redirect exitoso al frontend
- [ ] Verificar que el usuario aparece en la UI
- [ ] Verificar en Developer Tools > Application > Local Storage:
  - [ ] Verificar tokens de MSAL presentes
  - [ ] Verificar `tid` en token es `9acf6dd6-1978-4d9c-9a9c-c9be95245565`

### 4. Functional Testing

- [ ] Navegar a Dashboard
- [ ] Verificar que los datos cargan correctamente
- [ ] Crear un client de prueba
- [ ] Subir un CSV de prueba
- [ ] Generar un report
- [ ] Descargar PDF del report
- [ ] Verificar PDF se genera correctamente
- [ ] Verificar gráficas en PDF
- [ ] Verificar Analytics tracking (si habilitado)
- [ ] Verificar History tracking

### 5. Logs and Monitoring

- [ ] Verificar logs del backend:
  ```powershell
  az webapp log tail --name your-backend-webapp --resource-group your-resource-group
  ```
- [ ] Verificar logs del frontend:
  ```powershell
  az webapp log tail --name your-frontend-webapp --resource-group your-resource-group
  ```
- [ ] Verificar Application Insights:
  - [ ] Logs llegando correctamente
  - [ ] No hay errores críticos
  - [ ] Performance metrics normales
  - [ ] Availability tests configurados

### 6. Database Verification

- [ ] Conectar a PostgreSQL:
  ```bash
  psql "host=your-server.postgres.database.azure.com port=5432 dbname=azure_advisor_reports_prod user=dbadmin sslmode=require"
  ```
- [ ] Verificar migraciones aplicadas:
  ```sql
  SELECT * FROM django_migrations ORDER BY applied DESC LIMIT 10;
  ```
- [ ] Verificar tablas principales existen:
  ```sql
  \dt
  ```
- [ ] Verificar datos de prueba (si aplica)

### 7. Redis Cache Verification

- [ ] Conectar a Redis:
  ```bash
  redis-cli -h your-cache.redis.cache.windows.net -p 6380 -a <access-key> --tls
  ```
- [ ] Verificar cache funciona:
  ```redis
  PING
  SET test "hello"
  GET test
  ```

### 8. Blob Storage Verification

- [ ] Verificar containers existen:
  ```powershell
  az storage container list --account-name yourstorageaccount --account-key <key>
  ```
- [ ] Subir archivo de prueba
- [ ] Verificar archivo se guarda en blob storage

### 9. Performance Testing

- [ ] Medir tiempo de carga del frontend (< 3s objetivo)
- [ ] Medir tiempo de respuesta del backend (< 500ms para APIs simples)
- [ ] Medir tiempo de generación de PDF (< 10s para report típico)
- [ ] Verificar que no hay memory leaks
- [ ] Verificar CPU usage normal (< 70%)

### 10. Security Verification

- [ ] Verificar HTTPS enforcement
- [ ] Verificar headers de seguridad presentes:
  - [ ] X-Frame-Options
  - [ ] X-Content-Type-Options
  - [ ] Strict-Transport-Security
- [ ] Verificar CORS configurado correctamente
- [ ] Verificar CSRF tokens funcionando
- [ ] Verificar secrets no están en logs
- [ ] Verificar source maps deshabilitados en frontend

---

## Rollback Plan

Si hay problemas críticos:

### Rollback Backend

```powershell
# Revertir a versión anterior
az webapp config container set \
  --name your-backend-webapp \
  --resource-group your-resource-group \
  --docker-custom-image-name yourregistryname.azurecr.io/azure-advisor-backend:1.2.1

az webapp restart --name your-backend-webapp --resource-group your-resource-group
```

### Rollback Frontend

```powershell
az webapp config container set \
  --name your-frontend-webapp \
  --resource-group your-resource-group \
  --docker-custom-image-name yourregistryname.azurecr.io/azure-advisor-frontend:1.2.1

az webapp restart --name your-frontend-webapp --resource-group your-resource-group
```

### Rollback Database

- [ ] Restaurar backup de database si es necesario:
  ```powershell
  az postgres flexible-server restore \
    --name your-server-restored \
    --resource-group your-resource-group \
    --source-server your-server \
    --restore-time "2025-10-30T10:00:00Z"
  ```

---

## Post-Deployment Tasks

### Documentation

- [ ] Actualizar CHANGELOG.md con cambios de v1.2.2
- [ ] Documentar cualquier cambio de configuración
- [ ] Actualizar runbooks si es necesario
- [ ] Documentar issues encontrados y soluciones

### Communication

- [ ] Notificar a stakeholders del deployment exitoso
- [ ] Actualizar status page si aplica
- [ ] Comunicar nuevas features a usuarios

### Monitoring Setup

- [ ] Configurar alertas en Application Insights:
  - [ ] Response time > 3s
  - [ ] Error rate > 5%
  - [ ] Availability < 99%
  - [ ] CPU > 80%
  - [ ] Memory > 90%
- [ ] Configurar dashboards en Azure Monitor
- [ ] Configurar log retention policies
- [ ] Configurar cost alerts

### Backup Verification

- [ ] Verificar backups automáticos configurados
- [ ] Verificar retention policies
- [ ] Documentar proceso de restore
- [ ] Programar prueba de restore

### Security Review

- [ ] Revisar access logs
- [ ] Revisar firewall rules
- [ ] Revisar API permissions
- [ ] Programar próxima rotación de secretos

---

## Sign-off

- [ ] Deployment completado exitosamente
- [ ] Todas las verificaciones pasadas
- [ ] Rollback plan documentado
- [ ] Team notificado

**Deployed by:** ___________________
**Date:** ___________________
**Version:** 1.2.2
**Sign-off:** ___________________

---

## Troubleshooting Quick Reference

### Tenant ID Issues
- Error: `AADSTS90002: Tenant not found`
- Solución: Verificar `AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565` en todas las configuraciones

### Authentication Issues
- Error: `AADSTS700016: Application not found`
- Solución: Verificar Client ID y que la app está en el tenant correcto

### Database Connection Issues
- Error: `could not connect to server`
- Solución: Verificar firewall rules y connection string

### Container Won't Start
- Error: Container exits with code 1
- Solución: Verificar logs y variables de entorno

Para más detalles, ver: `PRODUCTION_DEPLOYMENT_GUIDE.md`
