# Azure MVP Deployment Guide - Paso a Paso

Esta guía proporciona instrucciones detalladas paso a paso para desplegar el Azure Advisor Reports Platform MVP en Azure.

## Tabla de Contenidos

1. [Pre-requisitos](#pre-requisitos)
2. [Fase 1: Preparación del Entorno](#fase-1-preparación-del-entorno)
3. [Fase 2: Despliegue de Infraestructura Core](#fase-2-despliegue-de-infraestructura-core)
4. [Fase 3: Despliegue de Aplicaciones](#fase-3-despliegue-de-aplicaciones)
5. [Fase 4: Configuración y Verificación](#fase-4-configuración-y-verificación)
6. [Verificación Post-Despliegue](#verificación-post-despliegue)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Procedures](#rollback-procedures)

---

## Pre-requisitos

### Software Requerido

Antes de comenzar, asegúrate de tener instalado:

```bash
# Verificar instalaciones
az --version          # Azure CLI >= 2.50.0
docker --version      # Docker >= 24.0.0
git --version         # Git >= 2.40.0
```

### Instalación de Herramientas (si es necesario)

```bash
# Azure CLI (Windows)
winget install Microsoft.AzureCLI

# Azure CLI (Linux/macOS)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Docker Desktop
# Descargar de: https://www.docker.com/products/docker-desktop
```

### Cuenta y Permisos de Azure

- Cuenta de Azure activa con suscripción válida
- Permisos de "Contributor" o "Owner" en la suscripción
- Budget disponible: $150-200/mes para MVP

### Checklist Pre-Despliegue

- [ ] Azure CLI instalado y configurado
- [ ] Docker instalado y corriendo
- [ ] Acceso a GitHub repository
- [ ] Cuenta Azure con permisos adecuados
- [ ] Nombre de dominio (opcional, pero recomendado)

---

## Fase 1: Preparación del Entorno

### Paso 1.1: Login a Azure

```bash
# Login interactivo
az login

# Si tienes múltiples suscripciones, selecciona la correcta
az account list --output table
az account set --subscription "NOMBRE_O_ID_DE_SUSCRIPCION"

# Verificar suscripción activa
az account show --output table
```

**Verificación**: Deberías ver tu suscripción activa con estado "Enabled".

### Paso 1.2: Configurar Variables de Entorno

Crea un archivo `.env.azure` en el root del proyecto:

```bash
# Copiar template
cp .env.example .env.azure
```

Edita `.env.azure` con tus valores:

```bash
# ============================================
# AZURE CONFIGURATION
# ============================================

# Resource Group
AZURE_LOCATION=eastus
RESOURCE_GROUP=azure-advisor-reports-mvp
PROJECT_NAME=advisor-reports

# Naming Convention
ENV=prod
APP_NAME=advisor-reports

# ============================================
# DATABASE CONFIGURATION
# ============================================

# PostgreSQL Flexible Server
DB_SERVER_NAME=advisor-reports-db-prod
DB_ADMIN_USER=azureadmin
DB_ADMIN_PASSWORD=<GENERAR_PASSWORD_FUERTE>
DB_NAME=advisor_reports
DB_SKU=Standard_B1ms
DB_TIER=Burstable
DB_STORAGE_SIZE=32
DB_VERSION=14

# ============================================
# STORAGE CONFIGURATION
# ============================================

# Blob Storage
STORAGE_ACCOUNT_NAME=advisorreportsstor
STORAGE_CONTAINER_NAME=media
STORAGE_SKU=Standard_LRS

# ============================================
# CACHE CONFIGURATION
# ============================================

# Redis Cache
REDIS_NAME=advisor-reports-cache
REDIS_SKU=Basic
REDIS_CAPACITY=0

# ============================================
# CONTAINER APPS CONFIGURATION
# ============================================

# Container Apps Environment
CONTAINERAPPS_ENV_NAME=advisor-reports-env
LOG_ANALYTICS_WORKSPACE=advisor-reports-logs

# Backend Container App
BACKEND_APP_NAME=advisor-reports-backend
BACKEND_IMAGE_NAME=advisorreportsbackend
BACKEND_IMAGE_TAG=latest
BACKEND_CPU=0.5
BACKEND_MEMORY=1.0Gi
BACKEND_MIN_REPLICAS=1
BACKEND_MAX_REPLICAS=3

# Celery Worker Container App
CELERY_WORKER_APP_NAME=advisor-reports-worker
CELERY_WORKER_CPU=0.5
CELERY_WORKER_MEMORY=1.0Gi
CELERY_WORKER_MIN_REPLICAS=1
CELERY_WORKER_MAX_REPLICAS=5

# Celery Beat Container App
CELERY_BEAT_APP_NAME=advisor-reports-beat
CELERY_BEAT_CPU=0.25
CELERY_BEAT_MEMORY=0.5Gi

# ============================================
# APPLICATION CONFIGURATION
# ============================================

# Django Settings
DJANGO_SECRET_KEY=<GENERAR_SECRET_KEY>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=*.azurecontainerapps.io,yourdomain.com
DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings

# Celery Settings
CELERY_BROKER_URL=<SE_CONFIGURA_DESPUES>
CELERY_RESULT_BACKEND=<SE_CONFIGURA_DESPUES>

# Azure Storage
AZURE_ACCOUNT_NAME=<SE_CONFIGURA_DESPUES>
AZURE_ACCOUNT_KEY=<SE_CONFIGURA_DESPUES>
AZURE_CONTAINER=media

# ============================================
# MONITORING CONFIGURATION
# ============================================

# Application Insights
APP_INSIGHTS_NAME=advisor-reports-insights
APPLICATIONINSIGHTS_CONNECTION_STRING=<SE_CONFIGURA_DESPUES>

# ============================================
# SECURITY CONFIGURATION
# ============================================

# Key Vault
KEYVAULT_NAME=advisor-reports-kv
```

**Importante**: Genera passwords seguros para `DB_ADMIN_PASSWORD` y `DJANGO_SECRET_KEY`:

```bash
# Generar DB_ADMIN_PASSWORD
openssl rand -base64 32

# Generar DJANGO_SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Paso 1.3: Cargar Variables de Entorno

```bash
# Linux/macOS
source .env.azure
export $(grep -v '^#' .env.azure | xargs)

# Windows PowerShell
Get-Content .env.azure | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
```

### Paso 1.4: Crear Resource Group

```bash
# Crear resource group principal
az group create \
  --name $RESOURCE_GROUP \
  --location $AZURE_LOCATION

# Verificar creación
az group show --name $RESOURCE_GROUP --output table
```

**Verificación**: El resource group debe aparecer con estado "Succeeded".

---

## Fase 2: Despliegue de Infraestructura Core

### Paso 2.1: Azure PostgreSQL Flexible Server

#### 2.1.1: Crear PostgreSQL Server

```bash
# Crear servidor PostgreSQL
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --location $AZURE_LOCATION \
  --admin-user $DB_ADMIN_USER \
  --admin-password "$DB_ADMIN_PASSWORD" \
  --sku-name $DB_SKU \
  --tier $DB_TIER \
  --storage-size $DB_STORAGE_SIZE \
  --version $DB_VERSION \
  --public-access 0.0.0.0-255.255.255.255 \
  --tags Environment=production Project=advisor-reports

# Esperar a que el servidor esté listo (puede tomar 5-10 minutos)
az postgres flexible-server show \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --query state \
  --output tsv
```

**Verificación**: El estado debe ser "Ready".

#### 2.1.2: Crear Base de Datos

```bash
# Crear base de datos
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_SERVER_NAME \
  --database-name $DB_NAME

# Verificar creación
az postgres flexible-server db show \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_SERVER_NAME \
  --database-name $DB_NAME \
  --output table
```

#### 2.1.3: Configurar Firewall Rules

```bash
# Permitir servicios de Azure
az postgres flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Permitir tu IP actual (para testing)
MY_IP=$(curl -s https://api.ipify.org)
az postgres flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --rule-name AllowMyIP \
  --start-ip-address $MY_IP \
  --end-ip-address $MY_IP
```

#### 2.1.4: Obtener Connection String

```bash
# Obtener FQDN del servidor
DB_HOST=$(az postgres flexible-server show \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --query fullyQualifiedDomainName \
  --output tsv)

# Construir connection string
echo "DATABASE_URL=postgresql://${DB_ADMIN_USER}:${DB_ADMIN_PASSWORD}@${DB_HOST}:5432/${DB_NAME}?sslmode=require"

# Guardar en .env.azure
echo "" >> .env.azure
echo "# Database Connection (Generated)" >> .env.azure
echo "DB_HOST=${DB_HOST}" >> .env.azure
echo "DATABASE_URL=postgresql://${DB_ADMIN_USER}:${DB_ADMIN_PASSWORD}@${DB_HOST}:5432/${DB_NAME}?sslmode=require" >> .env.azure
```

### Paso 2.2: Azure Blob Storage

#### 2.2.1: Crear Storage Account

```bash
# Crear storage account
az storage account create \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $AZURE_LOCATION \
  --sku $STORAGE_SKU \
  --kind StorageV2 \
  --access-tier Hot \
  --https-only true \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false \
  --tags Environment=production Project=advisor-reports

# Verificar creación
az storage account show \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --query provisioningState \
  --output tsv
```

**Verificación**: El estado debe ser "Succeeded".

#### 2.2.2: Crear Containers

```bash
# Obtener access key
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT_NAME \
  --query '[0].value' \
  --output tsv)

# Crear container para media files
az storage container create \
  --name $STORAGE_CONTAINER_NAME \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --public-access off

# Crear container para PDFs
az storage container create \
  --name reports \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --public-access off

# Verificar containers
az storage container list \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --output table
```

#### 2.2.3: Configurar CORS (para frontend)

```bash
# Configurar CORS
az storage cors add \
  --services b \
  --methods GET POST PUT DELETE OPTIONS \
  --origins https://yourdomain.com https://*.azurecontainerapps.io \
  --allowed-headers "*" \
  --exposed-headers "*" \
  --max-age 3600 \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY
```

#### 2.2.4: Guardar Configuración en .env

```bash
# Guardar storage configuration
echo "" >> .env.azure
echo "# Storage Configuration (Generated)" >> .env.azure
echo "AZURE_ACCOUNT_NAME=${STORAGE_ACCOUNT_NAME}" >> .env.azure
echo "AZURE_ACCOUNT_KEY=${STORAGE_KEY}" >> .env.azure
echo "AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=${STORAGE_ACCOUNT_NAME};AccountKey=${STORAGE_KEY};EndpointSuffix=core.windows.net" >> .env.azure
```

### Paso 2.3: Azure Cache for Redis

#### 2.3.1: Crear Redis Cache

```bash
# Crear Redis cache
az redis create \
  --resource-group $RESOURCE_GROUP \
  --name $REDIS_NAME \
  --location $AZURE_LOCATION \
  --sku $REDIS_SKU \
  --vm-size $REDIS_CAPACITY \
  --enable-non-ssl-port false \
  --minimum-tls-version 1.2 \
  --tags Environment=production Project=advisor-reports

# Esperar a que Redis esté listo (puede tomar 10-15 minutos)
echo "Creando Redis Cache... esto puede tomar 10-15 minutos"
az redis show \
  --resource-group $RESOURCE_GROUP \
  --name $REDIS_NAME \
  --query provisioningState \
  --output tsv
```

**Nota**: La creación de Redis es el paso más largo. Puedes continuar con otros pasos mientras se crea.

#### 2.3.2: Obtener Redis Connection String

```bash
# Esperar a que Redis esté completamente listo
while [ "$(az redis show --resource-group $RESOURCE_GROUP --name $REDIS_NAME --query provisioningState -o tsv)" != "Succeeded" ]; do
  echo "Esperando que Redis esté listo..."
  sleep 30
done

# Obtener hostname
REDIS_HOST=$(az redis show \
  --resource-group $RESOURCE_GROUP \
  --name $REDIS_NAME \
  --query hostName \
  --output tsv)

# Obtener access key
REDIS_KEY=$(az redis list-keys \
  --resource-group $RESOURCE_GROUP \
  --name $REDIS_NAME \
  --query primaryKey \
  --output tsv)

# Construir connection strings
REDIS_URL="rediss://:${REDIS_KEY}@${REDIS_HOST}:6380/0?ssl_cert_reqs=required"
CELERY_BROKER_URL="rediss://:${REDIS_KEY}@${REDIS_HOST}:6380/1?ssl_cert_reqs=required"
CELERY_RESULT_BACKEND="rediss://:${REDIS_KEY}@${REDIS_HOST}:6380/2?ssl_cert_reqs=required"

# Guardar en .env.azure
echo "" >> .env.azure
echo "# Redis Configuration (Generated)" >> .env.azure
echo "REDIS_HOST=${REDIS_HOST}" >> .env.azure
echo "REDIS_KEY=${REDIS_KEY}" >> .env.azure
echo "REDIS_URL=${REDIS_URL}" >> .env.azure
echo "CELERY_BROKER_URL=${CELERY_BROKER_URL}" >> .env.azure
echo "CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}" >> .env.azure
```

### Paso 2.4: Log Analytics Workspace

```bash
# Crear Log Analytics Workspace
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_WORKSPACE \
  --location $AZURE_LOCATION \
  --tags Environment=production Project=advisor-reports

# Obtener workspace ID
LOG_ANALYTICS_WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_WORKSPACE \
  --query customerId \
  --output tsv)

# Obtener workspace key
LOG_ANALYTICS_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_WORKSPACE \
  --query primarySharedKey \
  --output tsv)

# Guardar en .env.azure
echo "" >> .env.azure
echo "# Log Analytics (Generated)" >> .env.azure
echo "LOG_ANALYTICS_WORKSPACE_ID=${LOG_ANALYTICS_WORKSPACE_ID}" >> .env.azure
echo "LOG_ANALYTICS_KEY=${LOG_ANALYTICS_KEY}" >> .env.azure
```

### Paso 2.5: Application Insights

```bash
# Crear Application Insights
az monitor app-insights component create \
  --app $APP_INSIGHTS_NAME \
  --location $AZURE_LOCATION \
  --resource-group $RESOURCE_GROUP \
  --workspace $LOG_ANALYTICS_WORKSPACE_ID \
  --tags Environment=production Project=advisor-reports

# Obtener instrumentation key y connection string
APP_INSIGHTS_KEY=$(az monitor app-insights component show \
  --app $APP_INSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey \
  --output tsv)

APP_INSIGHTS_CONNECTION_STRING=$(az monitor app-insights component show \
  --app $APP_INSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query connectionString \
  --output tsv)

# Guardar en .env.azure
echo "" >> .env.azure
echo "# Application Insights (Generated)" >> .env.azure
echo "APPINSIGHTS_INSTRUMENTATIONKEY=${APP_INSIGHTS_KEY}" >> .env.azure
echo "APPLICATIONINSIGHTS_CONNECTION_STRING=${APP_INSIGHTS_CONNECTION_STRING}" >> .env.azure
```

### Paso 2.6: Azure Key Vault (Opcional pero Recomendado)

```bash
# Crear Key Vault
az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $AZURE_LOCATION \
  --enabled-for-deployment true \
  --enabled-for-template-deployment true \
  --tags Environment=production Project=advisor-reports

# Guardar secretos en Key Vault
az keyvault secret set --vault-name $KEYVAULT_NAME --name "django-secret-key" --value "$DJANGO_SECRET_KEY"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "db-admin-password" --value "$DB_ADMIN_PASSWORD"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "redis-key" --value "$REDIS_KEY"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "storage-key" --value "$STORAGE_KEY"

echo "Secretos guardados en Key Vault: $KEYVAULT_NAME"
```

**Checkpoint Fase 2**: Verifica que todos los servicios están creados:

```bash
# Verificar todos los recursos
az resource list \
  --resource-group $RESOURCE_GROUP \
  --output table
```

Deberías ver:
- PostgreSQL Flexible Server
- Storage Account
- Redis Cache
- Log Analytics Workspace
- Application Insights
- Key Vault (opcional)

---

## Fase 3: Despliegue de Aplicaciones

### Paso 3.1: Crear Container Registry

```bash
# Crear Azure Container Registry
ACR_NAME="${PROJECT_NAME}acr"
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --location $AZURE_LOCATION \
  --admin-enabled true \
  --tags Environment=production Project=advisor-reports

# Obtener login server
ACR_LOGIN_SERVER=$(az acr show \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --query loginServer \
  --output tsv)

# Obtener credentials
ACR_USERNAME=$(az acr credential show \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --query username \
  --output tsv)

ACR_PASSWORD=$(az acr credential show \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --query passwords[0].value \
  --output tsv)

echo "ACR_LOGIN_SERVER=${ACR_LOGIN_SERVER}" >> .env.azure
echo "ACR_USERNAME=${ACR_USERNAME}" >> .env.azure
echo "ACR_PASSWORD=${ACR_PASSWORD}" >> .env.azure
```

### Paso 3.2: Build y Push de Imágenes Docker

#### 3.2.1: Build Backend Image

```bash
# Login a ACR
az acr login --name $ACR_NAME

# Build backend image
cd azure_advisor_reports
docker build -t ${ACR_LOGIN_SERVER}/${BACKEND_IMAGE_NAME}:${BACKEND_IMAGE_TAG} .

# Push backend image
docker push ${ACR_LOGIN_SERVER}/${BACKEND_IMAGE_NAME}:${BACKEND_IMAGE_TAG}

# Verificar push
az acr repository show \
  --name $ACR_NAME \
  --repository $BACKEND_IMAGE_NAME \
  --output table

cd ..
```

#### 3.2.2: Build Frontend Image (si aplica)

```bash
# Si tienes un frontend separado
cd frontend
docker build -t ${ACR_LOGIN_SERVER}/advisorreportsfrontend:latest .
docker push ${ACR_LOGIN_SERVER}/advisorreportsfrontend:latest
cd ..
```

### Paso 3.3: Crear Container Apps Environment

```bash
# Crear Container Apps environment
az containerapp env create \
  --name $CONTAINERAPPS_ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $AZURE_LOCATION \
  --logs-workspace-id $LOG_ANALYTICS_WORKSPACE_ID \
  --logs-workspace-key $LOG_ANALYTICS_KEY \
  --tags Environment=production Project=advisor-reports

# Verificar creación
az containerapp env show \
  --name $CONTAINERAPPS_ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --query provisioningState \
  --output tsv
```

**Verificación**: El estado debe ser "Succeeded".

### Paso 3.4: Desplegar Backend Container App

#### 3.4.1: Crear Backend App

```bash
# Crear backend container app
az containerapp create \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINERAPPS_ENV_NAME \
  --image ${ACR_LOGIN_SERVER}/${BACKEND_IMAGE_NAME}:${BACKEND_IMAGE_TAG} \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8000 \
  --ingress external \
  --cpu $BACKEND_CPU \
  --memory $BACKEND_MEMORY \
  --min-replicas $BACKEND_MIN_REPLICAS \
  --max-replicas $BACKEND_MAX_REPLICAS \
  --env-vars \
    DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings \
    DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" \
    DJANGO_DEBUG=False \
    DATABASE_URL="$DATABASE_URL" \
    REDIS_URL="$REDIS_URL" \
    CELERY_BROKER_URL="$CELERY_BROKER_URL" \
    CELERY_RESULT_BACKEND="$CELERY_RESULT_BACKEND" \
    AZURE_ACCOUNT_NAME="$AZURE_ACCOUNT_NAME" \
    AZURE_ACCOUNT_KEY="$AZURE_ACCOUNT_KEY" \
    AZURE_CONTAINER="$STORAGE_CONTAINER_NAME" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="$APP_INSIGHTS_CONNECTION_STRING" \
  --tags Environment=production Project=advisor-reports Component=backend

# Obtener FQDN del backend
BACKEND_FQDN=$(az containerapp show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn \
  --output tsv)

echo "Backend URL: https://${BACKEND_FQDN}"
echo "BACKEND_FQDN=${BACKEND_FQDN}" >> .env.azure
```

#### 3.4.2: Actualizar ALLOWED_HOSTS

```bash
# Actualizar ALLOWED_HOSTS en el backend
az containerapp update \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars DJANGO_ALLOWED_HOSTS="${BACKEND_FQDN},*.azurecontainerapps.io"
```

### Paso 3.5: Ejecutar Migraciones de Base de Datos

```bash
# Ejecutar migraciones usando container app job
az containerapp job create \
  --name "${BACKEND_APP_NAME}-migrate" \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINERAPPS_ENV_NAME \
  --trigger-type Manual \
  --replica-timeout 600 \
  --replica-retry-limit 1 \
  --replica-completion-count 1 \
  --parallelism 1 \
  --image ${ACR_LOGIN_SERVER}/${BACKEND_IMAGE_NAME}:${BACKEND_IMAGE_TAG} \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --cpu 0.5 \
  --memory 1.0Gi \
  --command "/bin/sh" "-c" "python manage.py migrate --noinput" \
  --env-vars \
    DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings \
    DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" \
    DATABASE_URL="$DATABASE_URL"

# Ejecutar el job de migración
az containerapp job start \
  --name "${BACKEND_APP_NAME}-migrate" \
  --resource-group $RESOURCE_GROUP

# Ver logs de migración
sleep 10
az containerapp job execution list \
  --name "${BACKEND_APP_NAME}-migrate" \
  --resource-group $RESOURCE_GROUP \
  --output table
```

### Paso 3.6: Crear Superuser de Django

```bash
# Crear job para crear superuser
az containerapp job create \
  --name "${BACKEND_APP_NAME}-createsuperuser" \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINERAPPS_ENV_NAME \
  --trigger-type Manual \
  --replica-timeout 300 \
  --replica-retry-limit 1 \
  --replica-completion-count 1 \
  --parallelism 1 \
  --image ${ACR_LOGIN_SERVER}/${BACKEND_IMAGE_NAME}:${BACKEND_IMAGE_TAG} \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --cpu 0.25 \
  --memory 0.5Gi \
  --command "/bin/sh" "-c" "echo \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'Change_This_Password_123!')\" | python manage.py shell" \
  --env-vars \
    DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings \
    DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" \
    DATABASE_URL="$DATABASE_URL"

# Ejecutar el job
az containerapp job start \
  --name "${BACKEND_APP_NAME}-createsuperuser" \
  --resource-group $RESOURCE_GROUP

echo "Superuser creado: admin / Change_This_Password_123!"
echo "IMPORTANTE: Cambia esta contraseña inmediatamente después de loguearte"
```

### Paso 3.7: Desplegar Celery Worker

```bash
# Crear Celery worker container app
az containerapp create \
  --name $CELERY_WORKER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINERAPPS_ENV_NAME \
  --image ${ACR_LOGIN_SERVER}/${BACKEND_IMAGE_NAME}:${BACKEND_IMAGE_TAG} \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --cpu $CELERY_WORKER_CPU \
  --memory $CELERY_WORKER_MEMORY \
  --min-replicas $CELERY_WORKER_MIN_REPLICAS \
  --max-replicas $CELERY_WORKER_MAX_REPLICAS \
  --command "celery" "-A" "azure_advisor_reports" "worker" "-l" "info" "--pool=solo" \
  --env-vars \
    DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings \
    DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" \
    DATABASE_URL="$DATABASE_URL" \
    REDIS_URL="$REDIS_URL" \
    CELERY_BROKER_URL="$CELERY_BROKER_URL" \
    CELERY_RESULT_BACKEND="$CELERY_RESULT_BACKEND" \
    AZURE_ACCOUNT_NAME="$AZURE_ACCOUNT_NAME" \
    AZURE_ACCOUNT_KEY="$AZURE_ACCOUNT_KEY" \
    AZURE_CONTAINER="$STORAGE_CONTAINER_NAME" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="$APP_INSIGHTS_CONNECTION_STRING" \
  --tags Environment=production Project=advisor-reports Component=celery-worker

echo "Celery Worker desplegado: $CELERY_WORKER_APP_NAME"
```

### Paso 3.8: Desplegar Celery Beat

```bash
# Crear Celery beat container app
az containerapp create \
  --name $CELERY_BEAT_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINERAPPS_ENV_NAME \
  --image ${ACR_LOGIN_SERVER}/${BACKEND_IMAGE_NAME}:${BACKEND_IMAGE_TAG} \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --cpu $CELERY_BEAT_CPU \
  --memory $CELERY_BEAT_MEMORY \
  --min-replicas 1 \
  --max-replicas 1 \
  --command "celery" "-A" "azure_advisor_reports" "beat" "-l" "info" \
  --env-vars \
    DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings \
    DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" \
    DATABASE_URL="$DATABASE_URL" \
    REDIS_URL="$REDIS_URL" \
    CELERY_BROKER_URL="$CELERY_BROKER_URL" \
    CELERY_RESULT_BACKEND="$CELERY_RESULT_BACKEND" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="$APP_INSIGHTS_CONNECTION_STRING" \
  --tags Environment=production Project=advisor-reports Component=celery-beat

echo "Celery Beat desplegado: $CELERY_BEAT_APP_NAME"
```

### Paso 3.9: Configurar KEDA Scaling para Celery Worker

```bash
# Crear KEDA scaling rule para Celery worker
az containerapp update \
  --name $CELERY_WORKER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --scale-rule-name redis-queue-length \
  --scale-rule-type azure-queue \
  --scale-rule-metadata \
    queueName=celery \
    queueLength=5 \
    connectionFromEnv=CELERY_BROKER_URL \
  --scale-rule-auth trigger=Connection

echo "KEDA scaling configurado para Celery worker"
```

**Checkpoint Fase 3**: Verifica que todas las aplicaciones están corriendo:

```bash
# Listar todas las container apps
az containerapp list \
  --resource-group $RESOURCE_GROUP \
  --output table

# Ver estado de cada app
az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query properties.runningStatus
az containerapp show --name $CELERY_WORKER_APP_NAME --resource-group $RESOURCE_GROUP --query properties.runningStatus
az containerapp show --name $CELERY_BEAT_APP_NAME --resource-group $RESOURCE_GROUP --query properties.runningStatus
```

Todos deben mostrar estado "Running".

---

## Fase 4: Configuración y Verificación

### Paso 4.1: Configurar Custom Domain (Opcional)

```bash
# Si tienes un dominio personalizado
CUSTOM_DOMAIN="api.yourdomain.com"

# Agregar custom domain
az containerapp hostname add \
  --hostname $CUSTOM_DOMAIN \
  --resource-group $RESOURCE_GROUP \
  --name $BACKEND_APP_NAME

# Obtener validation token
VALIDATION_TOKEN=$(az containerapp hostname list \
  --resource-group $RESOURCE_GROUP \
  --name $BACKEND_APP_NAME \
  --query "[?name=='$CUSTOM_DOMAIN'].bindingType" \
  --output tsv)

echo "Agrega este TXT record en tu DNS:"
echo "Name: asuid.$CUSTOM_DOMAIN"
echo "Value: $VALIDATION_TOKEN"

# Después de agregar el DNS record, bind el certificado
az containerapp hostname bind \
  --hostname $CUSTOM_DOMAIN \
  --resource-group $RESOURCE_GROUP \
  --name $BACKEND_APP_NAME \
  --environment $CONTAINERAPPS_ENV_NAME \
  --validation-method CNAME
```

### Paso 4.2: Configurar Azure CDN para Blob Storage (Opcional)

```bash
# Crear CDN profile
CDN_PROFILE_NAME="${PROJECT_NAME}-cdn"
az cdn profile create \
  --name $CDN_PROFILE_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $AZURE_LOCATION \
  --sku Standard_Microsoft

# Crear CDN endpoint
CDN_ENDPOINT_NAME="${PROJECT_NAME}-media"
az cdn endpoint create \
  --name $CDN_ENDPOINT_NAME \
  --profile-name $CDN_PROFILE_NAME \
  --resource-group $RESOURCE_GROUP \
  --origin ${STORAGE_ACCOUNT_NAME}.blob.core.windows.net \
  --origin-host-header ${STORAGE_ACCOUNT_NAME}.blob.core.windows.net \
  --enable-compression true

# Obtener CDN endpoint URL
CDN_ENDPOINT_URL=$(az cdn endpoint show \
  --name $CDN_ENDPOINT_NAME \
  --profile-name $CDN_PROFILE_NAME \
  --resource-group $RESOURCE_GROUP \
  --query hostName \
  --output tsv)

echo "CDN Endpoint: https://${CDN_ENDPOINT_URL}"
echo "CDN_ENDPOINT_URL=${CDN_ENDPOINT_URL}" >> .env.azure

# Actualizar backend para usar CDN
az containerapp update \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars AZURE_CDN_URL="https://${CDN_ENDPOINT_URL}"
```

### Paso 4.3: Configurar Health Checks

```bash
# Configurar health probe para backend
az containerapp update \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars \
    HEALTH_CHECK_PATH=/health/

# La configuración de health probes se hace en el YAML del container app
# Crear archivo health-probe.yaml

cat > health-probe.yaml <<EOF
properties:
  configuration:
    ingress:
      external: true
      targetPort: 8000
      transport: auto
      corsPolicy:
        allowedOrigins:
          - "*"
        allowedMethods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS
        allowedHeaders:
          - "*"
      customDomains: []
      exposedPort: 0
      traffic:
        - latestRevision: true
          weight: 100
      allowInsecure: false
    dapr: null
    maxInactiveRevisions: 10
  template:
    containers:
      - image: ${ACR_LOGIN_SERVER}/${BACKEND_IMAGE_NAME}:${BACKEND_IMAGE_TAG}
        name: $BACKEND_APP_NAME
        resources:
          cpu: $BACKEND_CPU
          memory: $BACKEND_MEMORY
        probes:
          - type: liveness
            httpGet:
              path: /health/
              port: 8000
              scheme: HTTP
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          - type: readiness
            httpGet:
              path: /health/
              port: 8000
              scheme: HTTP
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
EOF

# Aplicar configuración (nota: esto requiere Azure CLI 2.50+)
# az containerapp update --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --yaml health-probe.yaml
```

### Paso 4.4: Configurar Alertas de Monitoring

```bash
# Crear action group para notificaciones
ACTION_GROUP_NAME="${PROJECT_NAME}-alerts"
az monitor action-group create \
  --name $ACTION_GROUP_NAME \
  --resource-group $RESOURCE_GROUP \
  --short-name "AdvisorAlrt" \
  --email-receiver \
    name=AdminEmail \
    email-address=admin@yourdomain.com \
    use-common-alert-schema=true

# Alerta: High CPU usage en backend
az monitor metrics alert create \
  --name "${BACKEND_APP_NAME}-high-cpu" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.App/containerApps/${BACKEND_APP_NAME}" \
  --condition "avg UsageNanoCores > 400000000" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action $ACTION_GROUP_NAME \
  --description "Alert when backend CPU usage is high"

# Alerta: High memory usage en backend
az monitor metrics alert create \
  --name "${BACKEND_APP_NAME}-high-memory" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.App/containerApps/${BACKEND_APP_NAME}" \
  --condition "avg WorkingSetBytes > 900000000" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action $ACTION_GROUP_NAME \
  --description "Alert when backend memory usage is high"

# Alerta: HTTP 5xx errors
az monitor metrics alert create \
  --name "${BACKEND_APP_NAME}-http-errors" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.App/containerApps/${BACKEND_APP_NAME}" \
  --condition "total Requests > 10 where ResultCode >= 500" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action $ACTION_GROUP_NAME \
  --description "Alert when backend returns too many 5xx errors"

echo "Alertas configuradas para monitoring"
```

### Paso 4.5: Configurar Log Queries en Application Insights

```bash
# Crear saved queries útiles en Application Insights
az monitor app-insights query \
  --app $APP_INSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --analytics-query "requests | where resultCode >= 500 | summarize count() by resultCode, bin(timestamp, 1h)"

az monitor app-insights query \
  --app $APP_INSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --analytics-query "dependencies | where type == 'SQL' | summarize avg(duration), count() by name"

az monitor app-insights query \
  --app $APP_INSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --analytics-query "exceptions | summarize count() by type, bin(timestamp, 1h)"
```

---

## Verificación Post-Despliegue

### Paso 5.1: Verificar Health Endpoints

```bash
# Verificar backend health
curl -I https://${BACKEND_FQDN}/health/

# Verificar API admin
curl -I https://${BACKEND_FQDN}/admin/

# Verificar API endpoints
curl -I https://${BACKEND_FQDN}/api/
```

**Resultado Esperado**: HTTP 200 OK para todos los endpoints.

### Paso 5.2: Verificar Database Connectivity

```bash
# Conectar a PostgreSQL para verificar
az postgres flexible-server connect \
  --name $DB_SERVER_NAME \
  --resource-group $RESOURCE_GROUP \
  --admin-user $DB_ADMIN_USER \
  --admin-password "$DB_ADMIN_PASSWORD" \
  --database-name $DB_NAME \
  --interactive

# En el prompt de PostgreSQL, ejecutar:
# \dt
# SELECT * FROM django_migrations;
# \q
```

### Paso 5.3: Verificar Celery Workers

```bash
# Ver logs del Celery worker
az containerapp logs show \
  --name $CELERY_WORKER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow

# Ver logs del Celery beat
az containerapp logs show \
  --name $CELERY_BEAT_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow
```

**Buscar en logs**:
- "celery@[hostname] ready"
- "beat: Starting..."

### Paso 5.4: Verificar Blob Storage

```bash
# Listar containers
az storage container list \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --output table

# Verificar que puedes subir un archivo de prueba
echo "test" > test.txt
az storage blob upload \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --container-name $STORAGE_CONTAINER_NAME \
  --name test.txt \
  --file test.txt

# Verificar que el archivo se subió
az storage blob list \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --container-name $STORAGE_CONTAINER_NAME \
  --output table

# Limpiar
rm test.txt
az storage blob delete \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --container-name $STORAGE_CONTAINER_NAME \
  --name test.txt
```

### Paso 5.5: Verificar Redis Connectivity

```bash
# Test Redis connection usando redis-cli
# (necesitas tener redis-cli instalado localmente)

# Linux/macOS
redis-cli -h $REDIS_HOST -p 6380 -a "$REDIS_KEY" --tls --sni $REDIS_HOST PING

# Windows
# redis-cli.exe -h %REDIS_HOST% -p 6380 -a "%REDIS_KEY%" --tls --sni %REDIS_HOST% PING
```

**Resultado Esperado**: "PONG"

### Paso 5.6: Verificar Application Insights

```bash
# Ver telemetry en Application Insights
az monitor app-insights metrics show \
  --app $APP_INSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --metric requests/count \
  --aggregation count \
  --interval PT1H

# Ver excepciones recientes
az monitor app-insights query \
  --app $APP_INSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --analytics-query "exceptions | top 10 by timestamp desc"
```

### Paso 5.7: Test End-to-End

```bash
# Login al admin de Django
echo "Abre en tu navegador: https://${BACKEND_FQDN}/admin/"
echo "Usuario: admin"
echo "Password: Change_This_Password_123!"

# Probar API endpoints
curl -X GET https://${BACKEND_FQDN}/api/reports/ \
  -H "Accept: application/json"

# Probar generación de reporte (después de autenticarte)
# Este es un ejemplo, ajusta según tu API
curl -X POST https://${BACKEND_FQDN}/api/reports/generate/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_API_TOKEN" \
  -d '{"report_type": "executive"}'
```

### Paso 5.8: Resumen de Despliegue

```bash
# Generar resumen de despliegue
cat > deployment-summary.txt <<EOF
=====================================
AZURE ADVISOR REPORTS - DEPLOYMENT SUMMARY
=====================================

Resource Group: $RESOURCE_GROUP
Location: $AZURE_LOCATION

INFRASTRUCTURE:
---------------
PostgreSQL Server: $DB_SERVER_NAME
  - Host: $DB_HOST
  - Database: $DB_NAME
  - Admin User: $DB_ADMIN_USER

Storage Account: $STORAGE_ACCOUNT_NAME
  - Containers: $STORAGE_CONTAINER_NAME, reports

Redis Cache: $REDIS_NAME
  - Host: $REDIS_HOST

Container Registry: $ACR_NAME
  - Login Server: $ACR_LOGIN_SERVER

Log Analytics: $LOG_ANALYTICS_WORKSPACE
Application Insights: $APP_INSIGHTS_NAME

APPLICATIONS:
-------------
Backend API: $BACKEND_APP_NAME
  - URL: https://$BACKEND_FQDN
  - Admin: https://$BACKEND_FQDN/admin/
  - API: https://$BACKEND_FQDN/api/

Celery Worker: $CELERY_WORKER_APP_NAME
  - Replicas: $CELERY_WORKER_MIN_REPLICAS-$CELERY_WORKER_MAX_REPLICAS (auto-scaling)

Celery Beat: $CELERY_BEAT_APP_NAME
  - Replicas: 1 (fixed)

NEXT STEPS:
-----------
1. Cambiar password de superuser inmediatamente
2. Configurar dominio personalizado (opcional)
3. Configurar CI/CD con GitHub Actions
4. Configurar backups de base de datos
5. Revisar y ajustar alertas de monitoring

ESTIMATED MONTHLY COST: \$90-163 USD

Deployment Date: $(date)
=====================================
EOF

cat deployment-summary.txt
echo ""
echo "Resumen guardado en: deployment-summary.txt"
```

---

## Troubleshooting

### Problema 1: Container App no inicia

**Síntomas**: Container app muestra estado "Provisioning" o "Failed"

**Solución**:

```bash
# Ver logs del container
az containerapp logs show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --tail 100

# Ver revisiones
az containerapp revision list \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table

# Ver detalles de la última revisión
LATEST_REVISION=$(az containerapp revision list \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query '[0].name' \
  --output tsv)

az containerapp revision show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --revision $LATEST_REVISION
```

**Causas Comunes**:
- Variables de entorno incorrectas
- Imagen Docker no encontrada
- Puertos mal configurados
- Health checks fallando

### Problema 2: Database Connection Failed

**Síntomas**: Backend muestra errores de conexión a PostgreSQL

**Solución**:

```bash
# Verificar que el firewall permite Container Apps
az postgres flexible-server firewall-rule list \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --output table

# Verificar connection string
echo $DATABASE_URL

# Probar conexión desde local
psql "$DATABASE_URL"
```

**Causas Comunes**:
- Firewall rules no configuradas
- Connection string incorrecta
- SSL mode incorrecto
- Database no existe

### Problema 3: Celery Worker no procesa tareas

**Síntomas**: Tareas se quedan en estado "PENDING"

**Solución**:

```bash
# Ver logs del worker
az containerapp logs show \
  --name $CELERY_WORKER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow

# Verificar que Redis está accesible
redis-cli -h $REDIS_HOST -p 6380 -a "$REDIS_KEY" --tls --sni $REDIS_HOST PING

# Verificar que Celery Beat está corriendo
az containerapp logs show \
  --name $CELERY_BEAT_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --tail 50
```

**Causas Comunes**:
- CELERY_BROKER_URL incorrecta
- Redis no accesible
- Celery Beat no corriendo
- Worker crashed

### Problema 4: Blob Storage upload failed

**Síntomas**: Error al subir archivos o generar PDFs

**Solución**:

```bash
# Verificar storage account key
az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT_NAME \
  --output table

# Verificar CORS configuration
az storage cors list \
  --services b \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY

# Test upload manual
az storage blob upload \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --container-name $STORAGE_CONTAINER_NAME \
  --name test.txt \
  --file test.txt
```

**Causas Comunes**:
- AZURE_ACCOUNT_KEY incorrecta
- Container no existe
- CORS no configurado
- Permisos insuficientes

### Problema 5: High Memory Usage

**Síntomas**: Container se reinicia frecuentemente por OOM (Out of Memory)

**Solución**:

```bash
# Ver métricas de memoria
az monitor metrics list \
  --resource "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.App/containerApps/${BACKEND_APP_NAME}" \
  --metric WorkingSetBytes \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT5M

# Aumentar memoria del container
az containerapp update \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --memory 2.0Gi
```

**Causas Comunes**:
- Playwright consumiendo mucha memoria
- Memory leaks en la aplicación
- Configuración de memoria muy baja
- Demasiadas peticiones concurrentes

### Problema 6: Playwright PDF generation failed

**Síntomas**: Error al generar PDFs con Playwright

**Solución**:

```bash
# Ver logs detallados
az containerapp logs show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow

# Verificar que Playwright está instalado en la imagen
az containerapp exec \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --command "python -m playwright --version"

# Aumentar timeout y memoria
az containerapp update \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars \
    PLAYWRIGHT_TIMEOUT=60000 \
    PLAYWRIGHT_HEADLESS=true
```

**Causas Comunes**:
- Chromium no instalado correctamente
- Timeout muy corto
- Memoria insuficiente
- Chart.js no cargando

---

## Rollback Procedures

### Rollback Rápido - Revisión Anterior

Si el despliegue más reciente tiene problemas:

```bash
# Listar revisiones
az containerapp revision list \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table

# Activar revisión anterior (asumiendo que la anterior es estable)
PREVIOUS_REVISION=$(az containerapp revision list \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query '[1].name' \
  --output tsv)

az containerapp revision activate \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --revision $PREVIOUS_REVISION

# Dirigir 100% del tráfico a la revisión anterior
az containerapp ingress traffic set \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --revision-weight ${PREVIOUS_REVISION}=100
```

### Rollback de Base de Datos

```bash
# Si hiciste migraciones que necesitas revertir
az containerapp job create \
  --name "${BACKEND_APP_NAME}-migrate-rollback" \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINERAPPS_ENV_NAME \
  --trigger-type Manual \
  --replica-timeout 600 \
  --replica-retry-limit 1 \
  --replica-completion-count 1 \
  --parallelism 1 \
  --image ${ACR_LOGIN_SERVER}/${BACKEND_IMAGE_NAME}:previous-stable-tag \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --cpu 0.5 \
  --memory 1.0Gi \
  --command "/bin/sh" "-c" "python manage.py migrate <app_name> <migration_number>" \
  --env-vars \
    DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings \
    DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" \
    DATABASE_URL="$DATABASE_URL"

az containerapp job start \
  --name "${BACKEND_APP_NAME}-migrate-rollback" \
  --resource-group $RESOURCE_GROUP
```

### Rollback Completo - Borrar y Recrear

Si todo está roto y necesitas empezar de nuevo:

```bash
# ADVERTENCIA: Esto borrará TODO excepto la base de datos y storage

# Borrar container apps
az containerapp delete --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --yes
az containerapp delete --name $CELERY_WORKER_APP_NAME --resource-group $RESOURCE_GROUP --yes
az containerapp delete --name $CELERY_BEAT_APP_NAME --resource-group $RESOURCE_GROUP --yes

# Borrar container apps environment
az containerapp env delete --name $CONTAINERAPPS_ENV_NAME --resource-group $RESOURCE_GROUP --yes

# Re-desplegar desde Fase 3.3
# (seguir los pasos desde "Crear Container Apps Environment")
```

### Backup y Restore de Base de Datos

```bash
# Backup manual
az postgres flexible-server backup create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --backup-name "manual-backup-$(date +%Y%m%d-%H%M%S)"

# Listar backups
az postgres flexible-server backup list \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --output table

# Restore desde backup (crea un nuevo servidor)
az postgres flexible-server restore \
  --resource-group $RESOURCE_GROUP \
  --name "${DB_SERVER_NAME}-restored" \
  --source-server $DB_SERVER_NAME \
  --restore-time "2024-01-15T14:30:00Z"
```

---

## Próximos Pasos Recomendados

### 1. Configurar CI/CD con GitHub Actions

Crear `.github/workflows/deploy-production.yml` para automatizar despliegues.

### 2. Configurar Backups Automáticos

```bash
# Habilitar backups automáticos en PostgreSQL (ya está habilitado por defecto)
az postgres flexible-server show \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --query backup \
  --output table

# Configurar backup retention
az postgres flexible-server parameter set \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_SERVER_NAME \
  --name backup_retention_days \
  --value 30
```

### 3. Implementar Rate Limiting

Configurar rate limiting en Container Apps o usar Azure API Management.

### 4. Configurar WAF (Web Application Firewall)

Usar Azure Front Door o Application Gateway con WAF para protección adicional.

### 5. Optimizar Costos

```bash
# Revisar costos actuales
az consumption usage list \
  --start-date $(date -d '30 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --query "[?contains(instanceId, '$RESOURCE_GROUP')]" \
  --output table

# Configurar presupuesto
az consumption budget create \
  --resource-group $RESOURCE_GROUP \
  --budget-name "${PROJECT_NAME}-monthly-budget" \
  --amount 200 \
  --time-grain Monthly \
  --start-date $(date +%Y-%m-01) \
  --end-date $(date -d '+1 year' +%Y-%m-01)
```

---

## Recursos y Referencias

### Azure Documentation
- [Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- [PostgreSQL Flexible Server](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/)
- [Azure Blob Storage](https://learn.microsoft.com/en-us/azure/storage/blobs/)
- [Azure Cache for Redis](https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/)

### Project Documentation
- `AZURE_DEPLOYMENT_STRATEGY.md` - Architectural decisions
- `README.md` - Project overview
- `DJANGO_DEPLOYMENT.md` - Django-specific deployment notes

### Support Contacts
- Azure Support: https://azure.microsoft.com/support/
- Project Issues: [GitHub Issues URL]

---

## Checklist Final de Despliegue

- [ ] Resource Group creado
- [ ] PostgreSQL Flexible Server desplegado y accesible
- [ ] Migraciones de base de datos ejecutadas
- [ ] Superuser de Django creado
- [ ] Blob Storage configurado con containers
- [ ] Redis Cache desplegado y accesible
- [ ] Container Registry creado
- [ ] Backend image built y pushed
- [ ] Container Apps Environment creado
- [ ] Backend Container App desplegado
- [ ] Celery Worker Container App desplegado
- [ ] Celery Beat Container App desplegado
- [ ] KEDA scaling configurado
- [ ] Application Insights configurado
- [ ] Alertas de monitoring configuradas
- [ ] Health checks funcionando
- [ ] End-to-end tests pasando
- [ ] Documentación actualizada
- [ ] Passwords seguros cambiados

**¡Felicidades! Tu Azure Advisor Reports Platform MVP está desplegado en producción.**
