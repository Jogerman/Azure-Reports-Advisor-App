# Azure Advisor Reports v2.0 - Deployment Checklist

## 📋 Pre-Deployment Checklist

### ✅ Código Completado
- [x] Backend Foundation (Encryption, Models, Services, Serializers)
- [x] Celery Tasks (async Azure API integration)
- [x] REST API Endpoints (ViewSets, permissions, documentation)
- [x] Frontend Components (React/TypeScript UI)
- [x] Migraciones de base de datos creadas
- [x] Tests escritos (251 tests backend)

### ✅ Configuración Actualizada
- [x] `apps.azure_integration` agregado a INSTALLED_APPS
- [x] `apps.cost_monitoring` agregado a INSTALLED_APPS
- [x] `drf_spectacular` agregado a THIRD_PARTY_APPS
- [x] `SPECTACULAR_SETTINGS` configurado
- [x] `REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS']` configurado
- [x] Celery task_routes configurado para `azure_api` queue
- [x] URLs configuradas para `/api/v1/azure/`

### ✅ Dependencias
Todas las dependencias están en `requirements.txt`:
- drf-spectacular==0.27.0
- azure-identity==1.15.0
- azure-mgmt-advisor==9.0.0
- azure-mgmt-core==1.4.0
- tenacity==8.2.3

## 🚀 Pasos de Deployment

### 1. Build Docker Image (v2.0.0)

```bash
cd /Users/josegomez/Documents/Code/Azure-Reports-Advisor-App/azure_advisor_reports

# Build usando Azure Container Registry
az acr build --registry advisorreportsacr \
  --image azure-advisor-backend:2.0.0 \
  --image azure-advisor-backend:latest \
  --file Dockerfile \
  .
```

### 2. Ejecutar Migraciones en Producción

**IMPORTANTE:** Ejecutar ANTES de actualizar los containers.

```bash
# Opción A: Usar Azure Container Apps exec (si está disponible)
az containerapp exec \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --command "python manage.py migrate --no-input"

# Opción B: Usar Azure Portal Console
# 1. Ir a Azure Portal > advisor-reports-backend
# 2. Abrir "Console"
# 3. Ejecutar: python manage.py migrate --no-input
```

**Migraciones que se ejecutarán:**
- `azure_integration.0001_initial` - Crea tabla AzureSubscription
- `reports.0004_add_azure_integration_support` - Agrega campos dual data source a Report

### 3. Actualizar Backend Container

```bash
az containerapp update \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:2.0.0
```

### 4. Actualizar Worker Container

```bash
az containerapp update \
  --name advisor-reports-worker \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:2.0.0
```

**IMPORTANTE:** Verificar que el worker tenga configurado:
- Command: `["/bin/sh"]`
- Args: `["-c", "celery -A azure_advisor_reports worker -l info --pool=gevent --concurrency=4 -Q default,reports,priority,azure_api"]`

⚠️ **Nota:** Agregar `,azure_api` al final de `-Q` para procesar las nuevas tareas.

### 5. Actualizar Beat Container

```bash
az containerapp update \
  --name advisor-reports-beat \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:2.0.0
```

### 6. Build y Deploy Frontend

```bash
cd /Users/josegomez/Documents/Code/Azure-Reports-Advisor-App/frontend

# Install dependencies (si es necesario)
npm install

# Build para producción
npm run build

# Los archivos estarán en: frontend/build/
```

**Deployment del Frontend:**
```bash
# Actualizar frontend container o static files hosting
az containerapp update \
  --name advisor-reports-frontend \
  --resource-group rg-azure-advisor-app \
  --image <frontend-image>:2.0.0
```

## 🔍 Verificación Post-Deployment

### 1. Verificar Containers Healthy

```bash
# Backend
az containerapp show \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --query "properties.{status:runningStatus,revision:latestRevisionName}"

# Worker
az containerapp show \
  --name advisor-reports-worker \
  --resource-group rg-azure-advisor-app \
  --query "properties.{status:runningStatus,revision:latestRevisionName}"

# Beat
az containerapp show \
  --name advisor-reports-beat \
  --resource-group rg-azure-advisor-app \
  --query "properties.{status:runningStatus,revision:latestRevisionName}"
```

**Expected:** `"status": "Running"` para todos.

### 2. Verificar Migraciones Aplicadas

```bash
az containerapp exec \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --command "python manage.py showmigrations azure_integration reports"
```

**Expected:**
```
azure_integration
 [X] 0001_initial
reports
 [X] 0001_initial
 [X] 0002_...
 [X] 0003_...
 [X] 0004_add_azure_integration_support
```

### 3. Verificar API Endpoints

```bash
# Test backend health
curl https://advisor-reports-backend.nicefield-788f351e.eastus.azurecontainerapps.io/health/

# Test Swagger docs
curl https://advisor-reports-backend.nicefield-788f351e.eastus.azurecontainerapps.io/api/docs/

# Test Azure subscriptions endpoint (requiere auth)
curl https://advisor-reports-backend.nicefield-788f351e.eastus.azurecontainerapps.io/api/v1/azure/subscriptions/
```

### 4. Verificar Logs

```bash
# Backend logs
az containerapp logs show \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --tail 50

# Worker logs (verificar que procesa azure_api queue)
az containerapp logs show \
  --name advisor-reports-worker \
  --resource-group rg-azure-advisor-app \
  --tail 50 \
  | grep -E "(azure_api|azure_integration)"
```

### 5. Prueba Funcional End-to-End

**Paso 1:** Login en el frontend
```
https://advisor-reports-frontend.nicefield-788f351e.eastus.azurecontainerapps.io
```

**Paso 2:** Navegar a "Azure Integration" > "Azure Subscriptions"

**Paso 3:** Agregar nueva Azure Subscription con credenciales de prueba

**Paso 4:** Hacer "Test Connection" - debe mostrar éxito/error

**Paso 5:** Crear nuevo reporte seleccionando:
- Data Source: Azure API
- Azure Subscription: (seleccionar la recién creada)
- Filters: Category=Cost, Impact=High

**Paso 6:** Verificar que el reporte se procesa correctamente

## 🐛 Troubleshooting

### Error: "No module named 'drf_spectacular'"

**Causa:** Dependencias no instaladas en container.

**Solución:**
1. Verificar que `drf-spectacular==0.27.0` está en requirements.txt
2. Rebuild Docker image
3. Redeploy containers

### Error: "apps.azure_integration not found"

**Causa:** App no registrada en INSTALLED_APPS.

**Solución:**
1. Verificar en settings.py línea 122: `'apps.azure_integration',`
2. Rebuild y redeploy

### Error: "azure_api queue not found"

**Causa:** Worker no configurado para procesar nueva queue.

**Solución:**
Actualizar worker args para incluir `azure_api`:
```
-Q default,reports,priority,azure_api
```

### Reports stuck in "processing"

**Causa:** Celery worker no procesando tareas o error en tasks.

**Solución:**
1. Verificar worker logs
2. Verificar Redis connectivity
3. Verificar Azure credentials en AzureSubscription

## 📊 Monitoring Post-Deployment

### Key Metrics to Monitor

1. **Container Health:**
   - All 3 containers (backend, worker, beat) should be "Running"

2. **Celery Queue Lengths:**
   - `default`, `reports`, `priority`, `azure_api` queues should not accumulate

3. **Report Processing Times:**
   - CSV reports: ~30s - 2min
   - Azure API reports: ~1-5min (depending on filters)

4. **Error Rates:**
   - Monitor Application Insights for:
     - `AzureAuthenticationError`
     - `AzureAPIError`
     - `AzureConnectionError`

5. **API Response Times:**
   - `/api/v1/azure/subscriptions/`: < 500ms
   - `/api/v1/azure/subscriptions/{id}/statistics/`: < 5s

## 🔄 Rollback Plan

Si v2.0 tiene problemas críticos:

```bash
# Rollback a v1.6.1 (última versión estable)
az containerapp update \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:1.6.1

az containerapp update \
  --name advisor-reports-worker \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:1.6.1

az containerapp update \
  --name advisor-reports-beat \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:1.6.1
```

**IMPORTANTE:** Las migraciones de v2.0 son compatibles hacia atrás. No es necesario hacer rollback de base de datos.

## ✅ Deployment Complete Checklist

- [ ] Docker image v2.0.0 built successfully
- [ ] Migraciones ejecutadas sin errores
- [ ] Backend container updated y healthy
- [ ] Worker container updated con azure_api queue
- [ ] Beat container updated y healthy
- [ ] Frontend build completado
- [ ] Frontend deployed
- [ ] API endpoints responding correctamente
- [ ] Swagger docs accesible en /api/docs/
- [ ] Test end-to-end completado exitosamente
- [ ] Logs verificados sin errores críticos
- [ ] Monitoring configurado
- [ ] Equipo notificado del deployment

## 📞 Support

En caso de problemas durante deployment:

1. **Revisar logs inmediatamente:**
   ```bash
   az containerapp logs show --name advisor-reports-backend --resource-group rg-azure-advisor-app --tail 100
   ```

2. **Verificar Application Insights** para errores detallados

3. **Ejecutar rollback** si hay problemas críticos

4. **Documentar el issue** para análisis post-mortem

---

**Versión:** 2.0.0
**Fecha:** Noviembre 2025
**Status:** Ready for Deployment
