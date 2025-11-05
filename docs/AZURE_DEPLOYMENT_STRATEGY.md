# Azure Deployment Strategy - Azure Advisor Reports Platform MVP

## 🏗️ Arquitectura Propuesta

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Azure Cloud                                  │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Resource Group                               │ │
│  │                azure-advisor-reports-prod                       │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │         Azure Container Apps Environment                  │  │ │
│  │  │                                                            │  │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │ │
│  │  │  │  Frontend   │  │   Backend   │  │   Celery    │      │  │ │
│  │  │  │   (React)   │  │  (Django)   │  │   Worker    │      │  │ │
│  │  │  │             │  │             │  │             │      │  │ │
│  │  │  │   Port 80   │  │  Port 8000  │  │  No Port    │      │  │ │
│  │  │  │  (Public)   │  │  (Internal) │  │  (Internal) │      │  │ │
│  │  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │  │ │
│  │  │         │                 │                 │             │  │ │
│  │  └─────────┼─────────────────┼─────────────────┼─────────────┘  │ │
│  │            │                 │                 │                │ │
│  │            │                 │                 │                │ │
│  │            │    ┌────────────┴────────┐        │                │ │
│  │            │    │                     │        │                │ │
│  │            │    ▼                     ▼        ▼                │ │
│  │            │  ┌──────────────┐  ┌──────────────────┐           │ │
│  │            │  │  PostgreSQL  │  │  Redis Cache     │           │ │
│  │            │  │   Flexible   │  │  (Basic C0)      │           │ │
│  │            │  │   Server     │  │                  │           │ │
│  │            │  │  (B1ms)      │  │  - Session Store │           │ │
│  │            │  │              │  │  - Celery Broker │           │ │
│  │            │  │  - Main DB   │  │  - Cache         │           │ │
│  │            │  └──────────────┘  └──────────────────┘           │ │
│  │            │                                                    │ │
│  │            │    ┌──────────────────────────────────┐           │ │
│  │            └───▶│    Blob Storage                  │           │ │
│  │                 │                                   │           │ │
│  │                 │  - Container: reports            │           │ │
│  │                 │  - Container: media              │           │ │
│  │                 │  - Container: staticfiles        │           │ │
│  │                 │                                   │           │ │
│  │                 │  CDN-enabled for static assets   │           │ │
│  │                 └──────────────────────────────────┘           │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │         Application Insights                             │  │ │
│  │  │  - Logs, Metrics, Traces                                │  │ │
│  │  │  - Performance Monitoring                               │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │         Azure Key Vault                                  │  │ │
│  │  │  - Database credentials                                  │  │ │
│  │  │  - Storage keys                                          │  │ │
│  │  │  - Secret keys                                           │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────── ┘
```

## 📋 Servicios de Azure Recomendados

### 1. **Azure Container Apps** (Recomendado para MVP)

**¿Por qué Container Apps y no App Service o AKS?**

| Servicio | Ventaja | Desventaja | Costo Mensual (Estimado) |
|----------|---------|------------|--------------------------|
| **Container Apps** ✅ | - Serverless, paga por uso<br>- Escalado automático 0-N<br>- Perfecto para Celery workers<br>- Built-in HTTPS<br>- Simple deployment | - Menor control granular | **$30-80** |
| App Service | - Conocido<br>- Windows + Linux | - Pago por instancia (siempre corriendo)<br>- Complejo para Celery | **$55-200** |
| AKS | - Máximo control<br>- Enterprise-grade | - Complejo para MVP<br>- Requiere experto K8s<br>- Overhead de gestión | **$150-500** |

**Veredicto:** Container Apps es la mejor opción para MVP porque:
- Perfecto para arquitecturas con múltiples containers (backend, frontend, celery)
- Escalado automático basado en carga (incluyendo a cero cuando no hay tráfico)
- Ideal para workers de Celery (pueden escalar independientemente)
- Costo-efectivo para startups

### 2. **Azure Database for PostgreSQL - Flexible Server**

**Tier Recomendado:** Burstable B1ms (1 vCore, 2 GiB RAM)

```yaml
Configuración:
  - Tier: Burstable B1ms
  - Storage: 32 GB (escalable a 16 TB)
  - Backup: 7 días de retención
  - High Availability: No (para MVP, agregar luego)
  - Region: Same as Container Apps
  - Costo estimado: $15-25/mes
```

**Características:**
- ✅ Backups automáticos
- ✅ Point-in-time restore
- ✅ SSL enforcement
- ✅ Private endpoint support
- ✅ Escalable sin downtime

### 3. **Azure Cache for Redis**

**Tier Recomendado:** Basic C0 (250 MB)

```yaml
Configuración:
  - Tier: Basic C0
  - Memory: 250 MB
  - SSL: Enabled
  - Persistence: No (para MVP)
  - Costo estimado: $16/mes
```

**Uso:**
- Session storage (Django sessions)
- Celery broker y result backend
- Application cache

**¿Por qué no Redis gratuito o self-hosted?**
- Redis en Container Apps costaría similar pero sin backups
- Azure Cache for Redis tiene 99.9% SLA
- Backups y monitoring incluidos

### 4. **Azure Blob Storage**

**Tier Recomendado:** General Purpose v2 - Hot

```yaml
Containers:
  - reports/
    - pdf/       # PDFs generados
    - html/      # HTML reports
  - media/       # User uploads, avatars
  - staticfiles/ # CSS, JS, images (Django static)

Configuración:
  - Tier: Hot (acceso frecuente)
  - Redundancy: LRS (Local-Redundant Storage)
  - CDN: Azure CDN Standard Microsoft
  - Lifecycle: Move to Cool after 90 days
  - Costo estimado: $5-15/mes (para 10-50 GB)
```

**Características:**
- ✅ CDN integration para static files
- ✅ Lifecycle management (auto-archive old reports)
- ✅ Blob versioning
- ✅ Soft delete (7 days)

### 5. **Application Insights**

```yaml
Configuración:
  - Tier: Pay-as-you-go
  - Daily cap: 1 GB (para controlar costos)
  - Retention: 90 días
  - Costo estimado: $5-10/mes
```

**Monitoreo incluido:**
- Request/response times
- Error rates y excepciones
- Custom metrics (report generation time, etc.)
- Dependency tracking (DB, Redis, Blob)
- Live metrics stream

### 6. **Azure Key Vault**

```yaml
Configuración:
  - Tier: Standard
  - Secrets: ~15 secrets
  - Costo estimado: $1-2/mes
```

**Secrets a guardar:**
- `DATABASE_URL`
- `REDIS_URL`
- `AZURE_STORAGE_CONNECTION_STRING`
- `SECRET_KEY` (Django)
- `AZURE_CLIENT_SECRET`

## 🔧 Estrategia de Celery y Redis

### Problema: ¿Cómo manejar tareas asíncronas?

Tu aplicación necesita Celery para:
1. Generar PDFs pesados (Playwright)
2. Procesar CSVs grandes
3. Enviar notificaciones
4. Tareas programadas (reports periódicos)

### Solución Propuesta: Celery Workers en Container Apps

```yaml
Container Apps Configuration:

1. Backend API (Django):
   - Min replicas: 1
   - Max replicas: 3
   - Scale trigger: HTTP requests
   - Port: 8000
   - Command: gunicorn azure_advisor_reports.wsgi:application

2. Celery Worker (Mismo código, diferente comando):
   - Min replicas: 1
   - Max replicas: 5
   - Scale trigger: KEDA Redis scaler (queue length)
   - No port exposed
   - Command: celery -A azure_advisor_reports worker -l info

3. Celery Beat (Scheduler):
   - Min replicas: 1
   - Max replicas: 1 (solo uno!)
   - No scaling
   - Command: celery -A azure_advisor_reports beat -l info
```

### ¿Por qué esta estrategia?

**Ventajas:**
- ✅ Workers escalan automáticamente según la cola
- ✅ Mismo código base (mismo container image)
- ✅ Fácil deployment
- ✅ Cost-effective (escala a 0 cuando no hay carga)

**Alternativas descartadas:**
- ❌ Azure Functions: No soporta Playwright/Chromium fácilmente
- ❌ Azure Batch: Overhead innecesario
- ❌ Logic Apps: No Python nativo

### Configuración de KEDA (Kubernetes Event-Driven Autoscaling)

Container Apps usa KEDA internamente para escalar workers:

```yaml
scale:
  minReplicas: 1
  maxReplicas: 5
  rules:
    - name: redis-scaling
      type: redis
      metadata:
        host: your-redis.redis.cache.windows.net
        port: "6380"
        usernameFromEnv: REDIS_USERNAME
        passwordFromEnv: REDIS_PASSWORD
        listName: celery
        listLength: "5"  # Scale up when 5+ tasks in queue
```

## 💰 Costo Estimado Mensual (MVP)

| Servicio | Tier | Costo Estimado |
|----------|------|----------------|
| **Container Apps** | 3 apps (frontend, backend, celery) | $40-80 |
| **PostgreSQL** | Flexible Server B1ms | $15-25 |
| **Redis Cache** | Basic C0 | $16 |
| **Blob Storage** | Hot, 20 GB | $5-10 |
| **Application Insights** | 1 GB/day | $5-10 |
| **Key Vault** | Standard | $1-2 |
| **CDN** | Standard, 10 GB transfer | $8-15 |
| **Virtual Network** | (opcional) | $0-5 |
| **Total Estimado** | | **$90-163/mes** |

### Optimizaciones de Costo:

1. **Escalado a cero en Container Apps** cuando no hay tráfico nocturno
2. **Blob Storage lifecycle**: Mover reports viejos a Cool/Archive
3. **Redis**: Considerar subir a Standard C1 solo si necesitas clustering
4. **Application Insights**: Daily cap de 1 GB

## 🚀 Plan de Implementación

### Fase 1: Infraestructura Base (Día 1-2)

```bash
# Crear Resource Group
az group create \
  --name azure-advisor-reports-prod \
  --location eastus

# Crear PostgreSQL Flexible Server
az postgres flexible-server create \
  --name azure-advisor-db-prod \
  --resource-group azure-advisor-reports-prod \
  --location eastus \
  --admin-user dbadmin \
  --admin-password <STRONG_PASSWORD> \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32

# Crear Redis Cache
az redis create \
  --name azure-advisor-redis-prod \
  --resource-group azure-advisor-reports-prod \
  --location eastus \
  --sku Basic \
  --vm-size c0 \
  --enable-non-ssl-port false

# Crear Storage Account
az storage account create \
  --name azureadvisorstorage \
  --resource-group azure-advisor-reports-prod \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2

# Crear containers en Blob Storage
az storage container create --name reports --account-name azureadvisorstorage
az storage container create --name media --account-name azureadvisorstorage
az storage container create --name staticfiles --account-name azureadvisorstorage

# Crear Key Vault
az keyvault create \
  --name azure-advisor-kv-prod \
  --resource-group azure-advisor-reports-prod \
  --location eastus
```

### Fase 2: Container Registry (Día 2)

```bash
# Crear Azure Container Registry
az acr create \
  --name azureadvisoracr \
  --resource-group azure-advisor-reports-prod \
  --sku Basic \
  --admin-enabled true

# Login to ACR
az acr login --name azureadvisoracr

# Build y Push Images
docker build -t azureadvisoracr.azurecr.io/backend:latest ./azure_advisor_reports
docker push azureadvisoracr.azurecr.io/backend:latest

docker build -t azureadvisoracr.azurecr.io/frontend:latest ./frontend
docker push azureadvisoracr.azurecr.io/frontend:latest
```

### Fase 3: Container Apps Environment (Día 3)

```bash
# Crear Container Apps Environment
az containerapp env create \
  --name azure-advisor-env-prod \
  --resource-group azure-advisor-reports-prod \
  --location eastus

# Deploy Backend
az containerapp create \
  --name backend \
  --resource-group azure-advisor-reports-prod \
  --environment azure-advisor-env-prod \
  --image azureadvisoracr.azurecr.io/backend:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
    DATABASE_URL=secretref:database-url \
    REDIS_URL=secretref:redis-url \
    AZURE_STORAGE_CONNECTION_STRING=secretref:storage-connection \
    SECRET_KEY=secretref:secret-key \
    PDF_ENGINE=playwright

# Deploy Celery Worker
az containerapp create \
  --name celery-worker \
  --resource-group azure-advisor-reports-prod \
  --environment azure-advisor-env-prod \
  --image azureadvisoracr.azurecr.io/backend:latest \
  --min-replicas 1 \
  --max-replicas 5 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --command "celery" "-A" "azure_advisor_reports" "worker" "-l" "info" \
  --env-vars \
    DATABASE_URL=secretref:database-url \
    REDIS_URL=secretref:redis-url

# Deploy Frontend
az containerapp create \
  --name frontend \
  --resource-group azure-advisor-reports-prod \
  --environment azure-advisor-env-prod \
  --image azureadvisoracr.azurecr.io/frontend:latest \
  --target-port 80 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.25 \
  --memory 0.5Gi
```

### Fase 4: CI/CD con GitHub Actions (Día 4)

Crear `.github/workflows/deploy.yml`

## 📝 Siguientes Pasos

1. ¿Quieres que cree los archivos de Infrastructure as Code (Bicep/Terraform)?
2. ¿Configuramos el GitHub Actions workflow para CI/CD?
3. ¿Creamos los Dockerfiles optimizados para producción?
4. ¿Documentamos las variables de entorno necesarias?

## 🔐 Seguridad

- ✅ Todo el tráfico sobre HTTPS
- ✅ Secrets en Key Vault
- ✅ PostgreSQL con SSL enforcement
- ✅ Redis solo accesible via SSL
- ✅ Blob Storage con SAS tokens
- ✅ Managed Identities para Container Apps
- ✅ Network isolation (opcional VNet)

## 📊 Monitoreo y Alertas

Application Insights dashboards para:
- Request success rate
- API response times
- PDF generation times
- Celery queue length
- Error rates
- Database connection pool

## 🎯 Recomendaciones Finales

1. **Empezar simple**: Deploy básico primero, optimizar después
2. **Monitoreo desde día 1**: Application Insights configurado desde el inicio
3. **Backups**: PostgreSQL backups automáticos + Storage soft-delete
4. **Escalabilidad**: Los workers de Celery escalan automáticamente
5. **Costos**: Empezar con tiers básicos, subir según necesidad real

---

**¿Listo para empezar con la implementación?**
