# Guía de Despliegue Azure MVP - Azure Portal (Web)

Esta guía te llevará paso a paso por el despliegue completo del Azure Advisor Reports Platform MVP usando únicamente el **Azure Portal** (interfaz web).

## Tabla de Contenidos

1. [Pre-requisitos](#pre-requisitos)
2. [Fase 1: Configuración Inicial](#fase-1-configuración-inicial)
3. [Fase 2: Base de Datos PostgreSQL](#fase-2-base-de-datos-postgresql)
4. [Fase 3: Almacenamiento (Blob Storage)](#fase-3-almacenamiento-blob-storage)
5. [Fase 4: Redis Cache](#fase-4-redis-cache)
6. [Fase 5: Container Registry](#fase-5-container-registry)
7. [Fase 6: Log Analytics y Application Insights](#fase-6-log-analytics-y-application-insights)
8. [Fase 7: Preparar Imágenes Docker](#fase-7-preparar-imágenes-docker)
9. [Fase 8: Container Apps](#fase-8-container-apps)
10. [Fase 9: Configuración Final](#fase-9-configuración-final)
11. [Verificación y Testing](#verificación-y-testing)
12. [Troubleshooting](#troubleshooting)

---

## Pre-requisitos

### Lo que necesitas antes de empezar:

- ✅ Cuenta de Azure activa (puedes crear una gratuita en https://azure.microsoft.com/free/)
- ✅ Navegador web actualizado (Chrome, Edge, Firefox)
- ✅ Docker Desktop instalado en tu máquina local (para construir imágenes)
- ✅ Acceso al código del proyecto Azure Advisor Reports
- ✅ Presupuesto estimado: $90-163 USD/mes

### Información que necesitarás guardar:

A medida que avances, guarda esta información en un documento (puedes usar Notepad, Word, etc.):

```
INFORMACIÓN DE DESPLIEGUE - AZURE ADVISOR REPORTS
==================================================

Resource Group: _____________________________
Location: eastus

--- BASE DE DATOS ---
PostgreSQL Server Name: _____________________________
Admin Username: _____________________________
Admin Password: _____________________________
Connection String: _____________________________

--- STORAGE ---
Storage Account Name: _____________________________
Storage Key: _____________________________
Container Names: media, reports

--- REDIS ---
Redis Name: _____________________________
Redis Hostname: _____________________________
Redis Primary Key: _____________________________

--- CONTAINER REGISTRY ---
Registry Name: _____________________________
Login Server: _____________________________
Username: _____________________________
Password: _____________________________

--- MONITORING ---
Log Analytics Workspace ID: _____________________________
Application Insights Instrumentation Key: _____________________________
Application Insights Connection String: _____________________________

--- CONTAINER APPS ---
Backend URL: _____________________________
Environment Name: _____________________________

--- SECRETS DJANGO ---
Django Secret Key: _____________________________
```

---

## Fase 1: Configuración Inicial

### Paso 1.1: Acceder al Azure Portal

1. Abre tu navegador y ve a: **https://portal.azure.com**
2. Inicia sesión con tu cuenta de Azure
3. Verás el Dashboard principal de Azure

![Azure Portal Dashboard](https://learn.microsoft.com/azure/media/portal-overview.png)

### Paso 1.2: Crear Resource Group

Un Resource Group es un contenedor lógico para todos tus recursos de Azure.

1. En la barra de búsqueda superior, escribe: **Resource groups**
2. Haz clic en **"Resource groups"** en los resultados
3. Haz clic en el botón **"+ Create"** (arriba a la izquierda)

**Configuración:**
- **Subscription**: Selecciona tu suscripción
- **Resource group**: `azure-advisor-reports-mvp`
- **Region**: `East US` (o tu región preferida)

4. Haz clic en **"Review + create"**
5. Haz clic en **"Create"**

✅ **Verificación**: Deberías ver el mensaje "Your deployment is complete"

📝 **Guarda**: El nombre del Resource Group: `azure-advisor-reports-mvp`

### Paso 1.3: Generar Django Secret Key

Antes de continuar, necesitas generar un Django Secret Key seguro.

**Opción 1 - Usando Python (si lo tienes instalado):**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Opción 2 - Online Generator:**
1. Ve a: https://djecrety.ir/
2. Haz clic en "Generate"
3. Copia el secret key generado

📝 **Guarda**: El Django Secret Key en tu documento de información

---

## Fase 2: Base de Datos PostgreSQL

### Paso 2.1: Crear PostgreSQL Flexible Server

1. En la barra de búsqueda superior, escribe: **Azure Database for PostgreSQL**
2. Selecciona **"Azure Database for PostgreSQL flexible servers"**
3. Haz clic en **"+ Create"**
4. Selecciona **"Flexible server"** y haz clic en **"Create"**

### Paso 2.2: Configuración Básica

**Pestaña "Basics":**

- **Subscription**: Tu suscripción
- **Resource group**: `azure-advisor-reports-mvp` (selecciona el que creaste)
- **Server name**: `advisor-reports-db-prod` (debe ser único globalmente)
- **Region**: `East US` (misma región que el Resource Group)
- **PostgreSQL version**: `14`
- **Workload type**: Selecciona **"Development"**

**Compute + storage:**
- Haz clic en **"Configure server"**
- Selecciona:
  - **Compute tier**: `Burstable`
  - **Compute size**: `Standard_B1ms (1 vCore, 2 GiB memory)`
  - **Storage size**: `32 GiB`
  - **Backup retention period**: `7 days`
- Haz clic en **"Save"**

**Authentication:**
- **Authentication method**: Selecciona **"PostgreSQL authentication only"**
- **Admin username**: `azureadmin`
- **Password**: Crea una contraseña fuerte (guárdala en tu documento)
- **Confirm password**: Repite la contraseña

📝 **Guarda**: Server name, Admin username, y Password

### Paso 2.3: Configuración de Red

**Pestaña "Networking":**

- **Connectivity method**: Selecciona **"Public access (allowed IP addresses)"**
- **Firewall rules**:
  - ✅ Marca **"Allow public access from any Azure service within Azure to this server"**
  - Haz clic en **"+ Add current client IP address"** (para acceder desde tu computadora)

### Paso 2.4: Configuración Adicional

**Pestaña "Tags"** (opcional pero recomendado):
- **Name**: `Environment` → **Value**: `production`
- **Name**: `Project` → **Value**: `advisor-reports`

### Paso 2.5: Crear

1. Haz clic en **"Review + create"**
2. Revisa la configuración
3. **Costo estimado**: Verás el costo mensual estimado (~$15-20/mes)
4. Haz clic en **"Create"**

⏱️ **Tiempo de espera**: 5-10 minutos

✅ **Verificación**: Espera a que aparezca "Your deployment is complete"

### Paso 2.6: Crear Base de Datos

1. Una vez completado, haz clic en **"Go to resource"**
2. En el menú izquierdo, bajo "Settings", haz clic en **"Databases"**
3. Haz clic en **"+ Add"**
4. **Database name**: `advisor_reports`
5. Haz clic en **"Save"**

✅ **Verificación**: La base de datos `advisor_reports` debe aparecer en la lista

### Paso 2.7: Obtener Connection String

1. En el menú izquierdo, haz clic en **"Overview"**
2. Copia el **"Server name"** (algo como: `advisor-reports-db-prod.postgres.database.azure.com`)

📝 **Guarda el Connection String** en este formato:
```
postgresql://azureadmin:[TU_PASSWORD]@advisor-reports-db-prod.postgres.database.azure.com:5432/advisor_reports?sslmode=require
```

Reemplaza `[TU_PASSWORD]` con la contraseña que creaste.

---

## Fase 3: Almacenamiento (Blob Storage)

### Paso 3.1: Crear Storage Account

1. En la barra de búsqueda superior, escribe: **Storage accounts**
2. Haz clic en **"Storage accounts"**
3. Haz clic en **"+ Create"**

### Paso 3.2: Configuración Básica

**Pestaña "Basics":**

- **Subscription**: Tu suscripción
- **Resource group**: `azure-advisor-reports-mvp`
- **Storage account name**: `advisorreportsstor` (debe ser único, solo minúsculas y números)
- **Region**: `East US`
- **Performance**: `Standard`
- **Redundancy**: `Locally-redundant storage (LRS)` (más económico para MVP)

### Paso 3.3: Configuración Avanzada

**Pestaña "Advanced":**

- **Security**:
  - ✅ **Require secure transfer for REST API operations**: Habilitado
  - **Minimum TLS version**: `Version 1.2`
  - ❌ **Allow Blob anonymous access**: Deshabilitado (por seguridad)

- **Data Lake Storage Gen2**:
  - ❌ **Enable hierarchical namespace**: Deshabilitado

- **Blob storage**:
  - **Access tier**: `Hot` (para acceso frecuente)

### Paso 3.4: Configuración de Red

**Pestaña "Networking":**

- **Network connectivity**: `Enable public access from all networks`
  (Más adelante puedes restringir esto por seguridad)

### Paso 3.5: Tags

**Pestaña "Tags":**
- **Name**: `Environment` → **Value**: `production`
- **Name**: `Project` → **Value**: `advisor-reports`

### Paso 3.6: Crear

1. Haz clic en **"Review + create"**
2. Haz clic en **"Create"**

⏱️ **Tiempo de espera**: 1-2 minutos

✅ **Verificación**: Espera a "Your deployment is complete"

### Paso 3.7: Crear Containers

1. Haz clic en **"Go to resource"**
2. En el menú izquierdo, bajo "Data storage", haz clic en **"Containers"**
3. Haz clic en **"+ Container"** (arriba)

**Primer Container:**
- **Name**: `media`
- **Public access level**: `Private (no anonymous access)`
- Haz clic en **"Create"**

**Segundo Container:**
- Repite el proceso
- **Name**: `reports`
- **Public access level**: `Private (no anonymous access)`
- Haz clic en **"Create"**

✅ **Verificación**: Deberías ver dos containers: `media` y `reports`

### Paso 3.8: Obtener Access Key

1. En el menú izquierdo, bajo "Security + networking", haz clic en **"Access keys"**
2. Haz clic en **"Show"** junto a "key1"
3. Copia:
   - **Storage account name**: `advisorreportsstor`
   - **Key**: (la cadena larga de caracteres)

📝 **Guarda**: Storage account name y Key1

### Paso 3.9: Configurar CORS (para frontend)

1. En el menú izquierdo, bajo "Settings", haz clic en **"Resource sharing (CORS)"**
2. Selecciona la pestaña **"Blob service"**
3. Haz clic en **"+ Add"**

**Configuración CORS:**
- **Allowed origins**: `*` (o especifica tu dominio: `https://yourdomain.com`)
- **Allowed methods**: Marca ✅ `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`
- **Allowed headers**: `*`
- **Exposed headers**: `*`
- **Max age**: `3600`

4. Haz clic en **"Save"** (arriba)

✅ **Verificación**: La regla CORS debe aparecer en la tabla

---

## Fase 4: Redis Cache

### Paso 4.1: Crear Azure Cache for Redis

1. En la barra de búsqueda superior, escribe: **Azure Cache for Redis**
2. Haz clic en **"Azure Cache for Redis"**
3. Haz clic en **"+ Create"**

### Paso 4.2: Configuración Básica

**Pestaña "Basics":**

- **Subscription**: Tu suscripción
- **Resource group**: `azure-advisor-reports-mvp`
- **DNS name**: `advisor-reports-cache` (debe ser único globalmente)
- **Location**: `East US`
- **Cache type**: `Basic C0 (250 MB Cache)`
- **Pricing**: Verás el costo estimado (~$16.50/mes)

⚠️ **Importante**: El tier Basic es suficiente para MVP, pero no tiene alta disponibilidad (SLA).

### Paso 4.3: Configuración Avanzada

**Pestaña "Advanced":**

- **Non-TLS port**: ❌ **Deshabilitado** (solo usar puerto seguro 6380)
- **Clustering policy**: No aplica para Basic tier
- **Redis version**: `6` (última versión estable)

### Paso 4.4: Tags

**Pestaña "Tags":**
- **Name**: `Environment` → **Value**: `production`
- **Name**: `Project` → **Value**: `advisor-reports`

### Paso 4.5: Crear

1. Haz clic en **"Review + create"**
2. Haz clic en **"Create"**

⏱️ **Tiempo de espera**: 10-15 minutos (Redis tarda más en desplegarse)

💡 **Tip**: Mientras esperas, puedes continuar con la Fase 5 (Container Registry)

✅ **Verificación**: Espera a "Your deployment is complete"

### Paso 4.6: Obtener Connection Info

1. Haz clic en **"Go to resource"**
2. En el menú izquierdo, haz clic en **"Overview"**
3. Copia el **"Host name"**: `advisor-reports-cache.redis.cache.windows.net`

4. En el menú izquierdo, bajo "Settings", haz clic en **"Access keys"**
5. Copia la **"Primary connection string (StackExchange.Redis)"**
   - Debería verse así: `advisor-reports-cache.redis.cache.windows.net:6380,password=XXXXX,ssl=True,abortConnect=False`

📝 **Guarda**: Redis hostname y Primary connection string

**Construir URLs para Django y Celery:**

Redis Connection String (Django cache):
```
rediss://:REDIS_PASSWORD@advisor-reports-cache.redis.cache.windows.net:6380/0?ssl_cert_reqs=required
```

Celery Broker (base de datos 1):
```
rediss://:REDIS_PASSWORD@advisor-reports-cache.redis.cache.windows.net:6380/1?ssl_cert_reqs=required
```

Celery Result Backend (base de datos 2):
```
rediss://:REDIS_PASSWORD@advisor-reports-cache.redis.cache.windows.net:6380/2?ssl_cert_reqs=required
```

Reemplaza `REDIS_PASSWORD` con la contraseña que copiaste del "Primary connection string".

---

## Fase 5: Container Registry

### Paso 5.1: Crear Azure Container Registry

1. En la barra de búsqueda superior, escribe: **Container registries**
2. Haz clic en **"Container registries"**
3. Haz clic en **"+ Create"**

### Paso 5.2: Configuración Básica

**Pestaña "Basics":**

- **Subscription**: Tu suscripción
- **Resource group**: `azure-advisor-reports-mvp`
- **Registry name**: `advisorreportsacr` (debe ser único, solo alfanumérico)
- **Location**: `East US`
- **SKU**: `Basic` (suficiente para MVP, ~$5/mes)

### Paso 5.3: Configuración de Red

**Pestaña "Networking":**

- **Public access**: `All networks` (para MVP)

### Paso 5.4: Tags

**Pestaña "Tags":**
- **Name**: `Environment` → **Value**: `production`
- **Name**: `Project` → **Value**: `advisor-reports`

### Paso 5.5: Crear

1. Haz clic en **"Review + create"**
2. Haz clic en **"Create"**

⏱️ **Tiempo de espera**: 1-2 minutos

✅ **Verificación**: Espera a "Your deployment is complete"

### Paso 5.6: Habilitar Admin User

1. Haz clic en **"Go to resource"**
2. En el menú izquierdo, bajo "Settings", haz clic en **"Access keys"**
3. Activa el toggle **"Admin user"** (debe ponerse en azul)
4. Copia:
   - **Login server**: `advisorreportsacr.azurecr.io`
   - **Username**: `advisorreportsacr`
   - **password**: (la primera contraseña que aparece)

📝 **Guarda**: Login server, Username, y Password

---

## Fase 6: Log Analytics y Application Insights

### Paso 6.1: Crear Log Analytics Workspace

1. En la barra de búsqueda superior, escribe: **Log Analytics workspaces**
2. Haz clic en **"Log Analytics workspaces"**
3. Haz clic en **"+ Create"**

**Configuración:**

- **Subscription**: Tu suscripción
- **Resource group**: `azure-advisor-reports-mvp`
- **Name**: `advisor-reports-logs`
- **Region**: `East US`

**Tags:**
- **Name**: `Environment` → **Value**: `production`
- **Name**: `Project` → **Value**: `advisor-reports`

4. Haz clic en **"Review + create"**
5. Haz clic en **"Create"**

⏱️ **Tiempo de espera**: 1 minuto

### Paso 6.2: Crear Application Insights

1. En la barra de búsqueda superior, escribe: **Application Insights**
2. Haz clic en **"Application Insights"**
3. Haz clic en **"+ Create"**

**Configuración:**

- **Subscription**: Tu suscripción
- **Resource group**: `azure-advisor-reports-mvp`
- **Name**: `advisor-reports-insights`
- **Region**: `East US`
- **Resource Mode**: `Workspace-based`
- **Log Analytics Workspace**: Selecciona `advisor-reports-logs` (el que acabas de crear)

**Tags:**
- **Name**: `Environment` → **Value**: `production`
- **Name**: `Project` → **Value**: `advisor-reports`

4. Haz clic en **"Review + create"**
5. Haz clic en **"Create"**

⏱️ **Tiempo de espera**: 1-2 minutos

### Paso 6.3: Obtener Instrumentation Key y Connection String

1. Haz clic en **"Go to resource"**
2. En la página **"Overview"**, busca y copia:
   - **Instrumentation Key**: (una GUID como `12345678-1234-1234-1234-123456789abc`)
   - **Connection String**: (empieza con `InstrumentationKey=...`)

📝 **Guarda**: Instrumentation Key y Connection String completo

---

## Fase 7: Preparar Imágenes Docker

Antes de crear las Container Apps, necesitas construir y subir las imágenes Docker a tu Container Registry.

### Paso 7.1: Build de la Imagen Backend

Abre una terminal/PowerShell en tu computadora y navega al proyecto:

```bash
cd "D:\Code\Azure Reports"
```

### Paso 7.2: Login al Container Registry

```bash
# Windows PowerShell
docker login advisorreportsacr.azurecr.io
# Username: advisorreportsacr
# Password: [pegar el password del ACR que guardaste]
```

### Paso 7.3: Build y Push Backend Image

```bash
# Build backend image
cd azure_advisor_reports
docker build -t advisorreportsacr.azurecr.io/advisorreportsbackend:latest .

# Push backend image
docker push advisorreportsacr.azurecr.io/advisorreportsbackend:latest

cd ..
```

⏱️ **Tiempo de espera**: 5-10 minutos (primera vez puede tardar más)

### Paso 7.4: Verificar en Azure Portal

1. Ve al Azure Portal
2. Busca tu Container Registry: `advisorreportsacr`
3. En el menú izquierdo, bajo "Services", haz clic en **"Repositories"**
4. Deberías ver `advisorreportsbackend` con tag `latest`

✅ **Verificación**: La imagen debe aparecer con tamaño (varios MB) y fecha de push

---

## Fase 8: Container Apps

### Paso 8.1: Crear Container Apps Environment

1. En la barra de búsqueda superior, escribe: **Container Apps**
2. Haz clic en **"Container Apps"**
3. En la nueva vista, primero necesitas crear un "Environment"
4. Haz clic en **"Manage environments"** (en el banner superior)
5. Haz clic en **"+ Create"**

**Configuración:**

**Pestaña "Basics":**
- **Subscription**: Tu suscripción
- **Resource group**: `azure-advisor-reports-mvp`
- **Environment name**: `advisor-reports-env`
- **Region**: `East US`

**Pestaña "Monitoring":**
- **Logs destination**: Selecciona `Log Analytics workspace`
- **Log Analytics workspace**: Selecciona `advisor-reports-logs`

**Pestaña "Tags":**
- **Name**: `Environment` → **Value**: `production`
- **Name**: `Project` → **Value**: `advisor-reports`

6. Haz clic en **"Review + create"**
7. Haz clic en **"Create"**

⏱️ **Tiempo de espera**: 3-5 minutos

✅ **Verificación**: El environment debe aparecer en estado "Ready"

### Paso 8.2: Crear Backend Container App

1. Regresa a **"Container Apps"** (usando la búsqueda superior)
2. Haz clic en **"+ Create"**

**Pestaña "Basics":**

- **Subscription**: Tu suscripción
- **Resource group**: `azure-advisor-reports-mvp`
- **Container app name**: `advisor-reports-backend`
- **Region**: `East US`
- **Container Apps environment**: Selecciona `advisor-reports-env`

**Pestaña "Container":**

- **Use quickstart image**: ❌ Desmarca esto
- **Name**: `backend`
- **Image source**: `Azure Container Registry`
- **Registry**: Selecciona `advisorreportsacr.azurecr.io`
- **Image**: `advisorreportsbackend`
- **Image tag**: `latest`
- **Authentication**: Selecciona `Admin credentials`

**CPU and Memory:**
- **CPU cores**: `0.5`
- **Memory (Gi)**: `1.0`

**Haz clic en el acordeón "Environment variables":**

Agrega las siguientes variables (haz clic en **"+ Add"** para cada una):

| Name | Value | Type |
|------|-------|------|
| DJANGO_SETTINGS_MODULE | azure_advisor_reports.settings | Manual entry |
| DJANGO_SECRET_KEY | [Tu Django Secret Key] | Manual entry |
| DJANGO_DEBUG | False | Manual entry |
| DATABASE_URL | [Tu PostgreSQL Connection String] | Manual entry |
| REDIS_URL | [Tu Redis URL db 0] | Manual entry |
| CELERY_BROKER_URL | [Tu Redis URL db 1] | Manual entry |
| CELERY_RESULT_BACKEND | [Tu Redis URL db 2] | Manual entry |
| AZURE_ACCOUNT_NAME | advisorreportsstor | Manual entry |
| AZURE_ACCOUNT_KEY | [Tu Storage Key] | Manual entry |
| AZURE_CONTAINER | media | Manual entry |
| APPLICATIONINSIGHTS_CONNECTION_STRING | [Tu App Insights Connection String] | Manual entry |

💡 **Tip**: Usa los valores que guardaste en tu documento de información.

**Pestaña "Ingress":**

- **Ingress**: ✅ Habilitado
- **Ingress traffic**: `Accepting traffic from anywhere`
- **Ingress type**: `HTTP`
- **Target port**: `8000`
- **Transport**: `Auto`

**Pestaña "Scale":**

- **Min replicas**: `1`
- **Max replicas**: `3`

**Pestaña "Tags":**
- **Name**: `Environment` → **Value**: `production`
- **Name**: `Project` → **Value**: `advisor-reports`
- **Name**: `Component` → **Value**: `backend`

3. Haz clic en **"Review + create"**
4. Haz clic en **"Create"**

⏱️ **Tiempo de espera**: 3-5 minutos

✅ **Verificación**: Estado debe ser "Running"

### Paso 8.3: Obtener Backend URL

1. Una vez creado, haz clic en **"Go to resource"**
2. En la página **"Overview"**, copia la **"Application Url"**
   - Ejemplo: `https://advisor-reports-backend.proudsky-12345678.eastus.azurecontainerapps.io`

📝 **Guarda**: Backend URL

3. Abre la URL en tu navegador y verifica que funcione (deberías ver un error 404 o la página de admin de Django en `/admin/`)

### Paso 8.4: Ejecutar Migraciones de Base de Datos

Necesitamos ejecutar las migraciones de Django. Lo haremos usando un "Job" de Container Apps.

1. En la barra de búsqueda superior, escribe: **Container Apps jobs**
2. Haz clic en **"Container Apps jobs"**
3. Haz clic en **"+ Create"**

**Pestaña "Basics":**
- **Subscription**: Tu suscripción
- **Resource group**: `azure-advisor-reports-mvp`
- **Job name**: `advisor-reports-migrate`
- **Region**: `East US`
- **Container Apps environment**: `advisor-reports-env`

**Pestaña "Container":**
- **Name**: `migrate`
- **Image source**: `Azure Container Registry`
- **Registry**: `advisorreportsacr.azurecr.io`
- **Image**: `advisorreportsbackend`
- **Image tag**: `latest`
- **Authentication**: `Admin credentials`

**CPU and Memory:**
- **CPU cores**: `0.5`
- **Memory (Gi)**: `1.0`

**Command override:**
- **Command**: `/bin/sh`
- **Args**: `-c,python manage.py migrate --noinput`

**Environment variables** (agrega solo estas):

| Name | Value |
|------|-------|
| DJANGO_SETTINGS_MODULE | azure_advisor_reports.settings |
| DJANGO_SECRET_KEY | [Tu Django Secret Key] |
| DATABASE_URL | [Tu PostgreSQL Connection String] |

**Pestaña "Trigger":**
- **Trigger type**: `Manual`
- **Replica timeout**: `600` (segundos)

4. Haz clic en **"Review + create"**
5. Haz clic en **"Create"**

### Paso 8.5: Ejecutar el Job de Migración

1. Una vez creado, haz clic en **"Go to resource"**
2. Haz clic en el botón **"Start execution"** (arriba)
3. Espera a que el estado cambie a "Succeeded"
4. Haz clic en **"Execution history"** para ver los logs

✅ **Verificación**: El job debe completarse con estado "Succeeded"

### Paso 8.6: Crear Superuser de Django

Repite el proceso de crear un Job para crear el superuser:

1. Ve a **"Container Apps jobs"** → **"+ Create"**

**Configuración** (similar al job anterior):
- **Job name**: `advisor-reports-createsuperuser`
- **Container**: Igual que el job de migraciones
- **Command**: `/bin/sh`
- **Args**: `-c,echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'Change_This_Password_123!')" | python manage.py shell`
- **Environment variables**: Las mismas 3 que el job de migraciones

2. Crea y ejecuta el job (**"Start execution"**)

📝 **Guarda las credenciales de admin**:
- Username: `admin`
- Password: `Change_This_Password_123!`

⚠️ **IMPORTANTE**: Cambia esta contraseña inmediatamente después de loguear por primera vez.

### Paso 8.7: Verificar Admin de Django

1. Abre tu navegador
2. Ve a: `https://[TU_BACKEND_URL]/admin/`
3. Login con: `admin` / `Change_This_Password_123!`

✅ **Verificación**: Deberías ver el admin panel de Django

### Paso 8.8: Crear Celery Worker Container App

1. Ve a **"Container Apps"** → **"+ Create"**

**Pestaña "Basics":**
- **Container app name**: `advisor-reports-worker`
- **Resource group**: `azure-advisor-reports-mvp`
- **Container Apps environment**: `advisor-reports-env`

**Pestaña "Container":**
- **Name**: `celery-worker`
- **Image source**: `Azure Container Registry`
- **Registry**: `advisorreportsacr.azurecr.io`
- **Image**: `advisorreportsbackend`
- **Image tag**: `latest`

**CPU and Memory:**
- **CPU cores**: `0.5`
- **Memory (Gi)**: `1.0`

**Command override:**
- **Command**: `celery`
- **Args**: `-A,azure_advisor_reports,worker,-l,info,--pool=solo`

**Environment variables** (las mismas que el backend):

| Name | Value |
|------|-------|
| DJANGO_SETTINGS_MODULE | azure_advisor_reports.settings |
| DJANGO_SECRET_KEY | [Tu Django Secret Key] |
| DATABASE_URL | [Tu PostgreSQL Connection String] |
| REDIS_URL | [Tu Redis URL] |
| CELERY_BROKER_URL | [Tu Celery Broker URL] |
| CELERY_RESULT_BACKEND | [Tu Celery Result Backend URL] |
| AZURE_ACCOUNT_NAME | advisorreportsstor |
| AZURE_ACCOUNT_KEY | [Tu Storage Key] |
| AZURE_CONTAINER | media |
| APPLICATIONINSIGHTS_CONNECTION_STRING | [Tu App Insights Connection String] |

**Pestaña "Ingress":**
- **Ingress**: ❌ Deshabilitado (el worker no necesita ingress)

**Pestaña "Scale":**
- **Min replicas**: `1`
- **Max replicas**: `5`

**Pestaña "Tags":**
- **Component** → **Value**: `celery-worker`

2. Haz clic en **"Review + create"**
3. Haz clic en **"Create"**

✅ **Verificación**: Estado debe ser "Running"

### Paso 8.9: Crear Celery Beat Container App

1. Ve a **"Container Apps"** → **"+ Create"**

**Configuración** (similar al worker):
- **Container app name**: `advisor-reports-beat`
- Todo igual que el worker EXCEPTO:

**Command override:**
- **Command**: `celery`
- **Args**: `-A,azure_advisor_reports,beat,-l,info`

**Scale:**
- **Min replicas**: `1`
- **Max replicas**: `1` ⚠️ **MUY IMPORTANTE**: Beat debe tener siempre 1 sola réplica

**Tags:**
- **Component** → **Value**: `celery-beat`

2. Crea el container app

✅ **Verificación**: Estado debe ser "Running"

### Paso 8.10: Verificar Logs de Celery

**Para Celery Worker:**
1. Ve al Container App `advisor-reports-worker`
2. En el menú izquierdo, bajo "Monitoring", haz clic en **"Log stream"**
3. Deberías ver logs como:
   ```
   [timestamp] [INFO/MainProcess] celery@xxxxx ready.
   [timestamp] [INFO/MainProcess] Connected to redis://...
   ```

**Para Celery Beat:**
1. Ve al Container App `advisor-reports-beat`
2. En el menú izquierdo, haz clic en **"Log stream"**
3. Deberías ver:
   ```
   [timestamp] [INFO/MainProcess] beat: Starting...
   [timestamp] [INFO/MainProcess] Scheduler: Sending due task...
   ```

✅ **Verificación**: Si ves "ready" y "Starting...", todo funciona correctamente.

---

## Fase 9: Configuración Final

### Paso 9.1: Actualizar ALLOWED_HOSTS en Backend

Ahora que tienes la URL del backend, necesitas actualizar la variable de entorno `DJANGO_ALLOWED_HOSTS`.

1. Ve al Container App `advisor-reports-backend`
2. En el menú izquierdo, bajo "Application", haz clic en **"Containers"**
3. Haz clic en **"Edit and deploy"**
4. En la sección "Environment variables", busca o agrega:
   - **Name**: `DJANGO_ALLOWED_HOSTS`
   - **Value**: `advisor-reports-backend.proudsky-12345678.eastus.azurecontainerapps.io,*.azurecontainerapps.io`
     (Reemplaza con tu URL real del backend sin el https://)
5. Haz clic en **"Create"** (abajo)

⏱️ **Tiempo de espera**: 2-3 minutos (creará una nueva revisión)

### Paso 9.2: Configurar Custom Domain (Opcional)

Si tienes un dominio personalizado:

1. Ve al Container App `advisor-reports-backend`
2. En el menú izquierdo, bajo "Settings", haz clic en **"Custom domains"**
3. Haz clic en **"+ Add custom domain"**
4. Sigue el asistente para agregar tu dominio (necesitarás configurar DNS)

### Paso 9.3: Configurar Alertas

**Alerta de CPU Alta:**

1. Ve al Container App `advisor-reports-backend`
2. En el menú izquierdo, bajo "Monitoring", haz clic en **"Alerts"**
3. Haz clic en **"+ New alert rule"**

**Configuración:**
- **Signal name**: `CPU usage`
- **Operator**: `Greater than`
- **Threshold value**: `80`
- **Check every**: `5 minutes`
- **Lookback period**: `5 minutes`

**Action group:**
- Haz clic en **"Create action group"**
- **Action group name**: `advisor-reports-alerts`
- **Short name**: `AdvisorAlrt`
- En "Notifications", agrega:
  - **Notification type**: `Email/SMS/Push/Voice`
  - **Name**: `AdminEmail`
  - **Email**: `tu-email@dominio.com`
- Haz clic en **"Review + create"** → **"Create"**

4. Asigna el action group a tu alerta
5. Haz clic en **"Create alert rule"**

Repite este proceso para alertas de:
- **Memory usage** > 80%
- **HTTP 5xx errors** > 10 por 5 minutos

### Paso 9.4: Configurar Azure Key Vault (Opcional pero Recomendado)

Para mayor seguridad, guarda tus secretos en Key Vault:

1. En la búsqueda superior, escribe: **Key vaults**
2. Haz clic en **"+ Create"**

**Configuración:**
- **Resource group**: `azure-advisor-reports-mvp`
- **Key vault name**: `advisor-reports-kv`
- **Region**: `East US`
- **Pricing tier**: `Standard`

3. Haz clic en **"Review + create"** → **"Create"**

**Agregar Secretos:**

1. Ve al Key Vault creado
2. En el menú izquierdo, bajo "Objects", haz clic en **"Secrets"**
3. Haz clic en **"+ Generate/Import"**

Agrega estos secretos:
- **Name**: `django-secret-key` → **Value**: [Tu Django Secret Key]
- **Name**: `db-admin-password` → **Value**: [Tu DB Password]
- **Name**: `redis-key` → **Value**: [Tu Redis Key]
- **Name**: `storage-key` → **Value**: [Tu Storage Key]

---

## Verificación y Testing

### Test 1: Health Check del Backend

Abre tu navegador y ve a:
```
https://[TU_BACKEND_URL]/health/
```

✅ **Esperado**: HTTP 200 OK o una respuesta JSON

### Test 2: Admin Panel

Abre:
```
https://[TU_BACKEND_URL]/admin/
```

Loguea con `admin` / `Change_This_Password_123!`

✅ **Esperado**: Deberías ver el Django admin panel

### Test 3: API Endpoints

Abre:
```
https://[TU_BACKEND_URL]/api/
```

✅ **Esperado**: Deberías ver la API root o un listado de endpoints

### Test 4: Verificar Base de Datos

En el admin de Django:
1. Ve a cualquier modelo (ej: Users)
2. Verifica que puedes crear, editar, y borrar objetos

✅ **Esperado**: CRUD operations funcionan correctamente

### Test 5: Verificar Celery Worker

Desde el Django admin o shell, ejecuta una tarea de Celery para verificar que el worker la procese.

### Test 6: Verificar Blob Storage

Intenta subir un archivo a través del admin o API.

✅ **Esperado**: El archivo debería aparecer en tu container `media` en el Storage Account

### Test 7: Verificar PDF Generation

Genera un reporte PDF desde el admin o API.

✅ **Esperado**: El PDF se genera y se guarda en el container `reports`

### Test 8: Verificar Application Insights

1. Ve a Application Insights: `advisor-reports-insights`
2. En el menú izquierdo, haz clic en **"Application map"**
3. Deberías ver el flujo de requests

4. Haz clic en **"Performance"** (en "Investigate")
5. Deberías ver gráficos de response times

✅ **Esperado**: Telemetría aparece en los dashboards

---

## Troubleshooting

### Problema 1: Container App no inicia

**Síntomas**: Estado "Provisioning" o "Failed"

**Solución**:
1. Ve al Container App
2. En "Monitoring" → **"Console"**, haz clic para ver logs
3. Busca errores en las variables de entorno o connection strings
4. Verifica que la imagen Docker existe en el Container Registry
5. En "Revisions and replicas", verifica el estado de la última revisión

### Problema 2: No puedo conectar a PostgreSQL

**Síntomas**: Error "could not connect to server"

**Solución**:
1. Ve a PostgreSQL Flexible Server
2. En "Networking" → "Firewall rules"
3. Verifica que "Allow public access from any Azure service" está habilitado
4. Verifica que tu connection string tiene `?sslmode=require` al final

### Problema 3: Redis connection timeout

**Síntomas**: Error "Redis connection timeout"

**Solución**:
1. Ve a Azure Cache for Redis
2. En "Access keys", verifica que copiaste la key correcta
3. Asegúrate de usar el puerto 6380 (SSL) y no el 6379
4. Verifica que tu connection string tiene `ssl=True` y `rediss://` (con doble 's')

### Problema 4: 404 en todas las URLs

**Síntomas**: Todas las URLs devuelven 404

**Solución**:
1. Verifica que las migraciones se ejecutaron correctamente
2. Ve al Container App backend → "Log stream"
3. Busca errores de Django en los logs
4. Verifica que `DJANGO_SETTINGS_MODULE` está correctamente configurado

### Problema 5: Celery no procesa tareas

**Síntomas**: Tareas en estado PENDING indefinidamente

**Solución**:
1. Ve al Container App `advisor-reports-worker`
2. En "Log stream", verifica que el worker está conectado a Redis
3. Busca el mensaje "celery@xxxxx ready"
4. Verifica que `CELERY_BROKER_URL` es correcto
5. Asegúrate que el worker tiene las mismas variables de entorno que el backend

### Problema 6: No puedo subir archivos

**Síntomas**: Error al subir archivos o generar PDFs

**Solución**:
1. Ve a Storage Account → "Access keys"
2. Verifica que la key es correcta
3. Ve a "Containers" y verifica que `media` y `reports` existen
4. Verifica CORS configuration en "Resource sharing (CORS)"
5. En el backend, verifica variables: `AZURE_ACCOUNT_NAME`, `AZURE_ACCOUNT_KEY`, `AZURE_CONTAINER`

### Problema 7: High memory usage / Container se reinicia

**Síntomas**: Container se reinicia frecuentemente

**Solución**:
1. Ve al Container App
2. En "Containers" → "Edit and deploy"
3. Aumenta la memoria a `2.0 Gi` o más
4. Especialmente importante para el backend (Playwright consume memoria)
5. Ajusta el `Max replicas` para escalar horizontalmente

---

## Resumen de URLs y Accesos

Al finalizar el despliegue, tendrás:

### URLs Públicas:
- **Backend API**: `https://advisor-reports-backend.[random].eastus.azurecontainerapps.io`
- **Admin Panel**: `https://advisor-reports-backend.[random].eastus.azurecontainerapps.io/admin/`
- **API Root**: `https://advisor-reports-backend.[random].eastus.azurecontainerapps.io/api/`

### Accesos:
- **Django Admin**: `admin` / `Change_This_Password_123!` (⚠️ cambiar inmediatamente)
- **PostgreSQL**: `azureadmin` / [tu password]

### Recursos en Azure:
- **Resource Group**: `azure-advisor-reports-mvp`
- **PostgreSQL Server**: `advisor-reports-db-prod`
- **Storage Account**: `advisorreportsstor`
- **Redis Cache**: `advisor-reports-cache`
- **Container Registry**: `advisorreportsacr`
- **Container Apps**:
  - `advisor-reports-backend`
  - `advisor-reports-worker`
  - `advisor-reports-beat`
- **Application Insights**: `advisor-reports-insights`

### Costos Mensuales Estimados:
- PostgreSQL (B1ms): ~$15
- Storage Account: ~$5-10
- Redis (Basic C0): ~$16.50
- Container Registry (Basic): ~$5
- Container Apps: ~$40-100 (depende del uso)
- Log Analytics: ~$5-10
- **Total**: ~$90-163 USD/mes

---

## Próximos Pasos

1. ✅ **Cambiar password del superuser**
   - Loguea en el admin
   - Ve a Users → admin → Change password

2. ✅ **Configurar backups de PostgreSQL**
   - Ve a PostgreSQL → "Backup and restore"
   - Configura retention period a 30 días

3. ✅ **Configurar dominio personalizado**
   - Compra un dominio
   - Configúralo en Container Apps

4. ✅ **Setup CI/CD**
   - Configura GitHub Actions para deployments automáticos

5. ✅ **Documentar variables de entorno**
   - Guarda todas las connection strings de forma segura

6. ✅ **Implementar rate limiting**
   - Usa Azure API Management o middleware de Django

7. ✅ **Configurar WAF (Web Application Firewall)**
   - Usa Azure Front Door para protección adicional

---

## Checklist Final

- [ ] Resource Group creado
- [ ] PostgreSQL desplegado y accesible
- [ ] Base de datos `advisor_reports` creada
- [ ] Migraciones ejecutadas
- [ ] Superuser creado
- [ ] Storage Account con containers `media` y `reports`
- [ ] CORS configurado en Storage
- [ ] Redis Cache desplegado
- [ ] Container Registry creado
- [ ] Backend image pushed al registry
- [ ] Container Apps Environment creado
- [ ] Backend Container App corriendo
- [ ] Backend URL funcionando
- [ ] Admin panel accesible
- [ ] Celery Worker corriendo
- [ ] Celery Beat corriendo
- [ ] Application Insights recibiendo telemetría
- [ ] Alertas configuradas
- [ ] Health checks pasando
- [ ] CRUD operations funcionando
- [ ] File upload funcionando
- [ ] PDF generation funcionando
- [ ] Password de admin cambiado
- [ ] Documentación actualizada

**¡Felicidades! Has desplegado exitosamente el Azure Advisor Reports Platform MVP usando Azure Portal.**

---

## Recursos Útiles

- [Azure Portal](https://portal.azure.com)
- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Azure PostgreSQL Documentation](https://learn.microsoft.com/azure/postgresql/)
- [Azure Storage Documentation](https://learn.microsoft.com/azure/storage/)
- [Azure Redis Cache Documentation](https://learn.microsoft.com/azure/azure-cache-for-redis/)

¿Necesitas ayuda? Consulta la sección de Troubleshooting o busca en Azure Documentation.
