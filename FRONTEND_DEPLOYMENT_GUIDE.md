# Guía de Despliegue del Frontend - Azure Portal

Esta guía te llevará paso a paso por el despliegue del frontend React usando Azure Container Apps.

## Tabla de Contenidos

1. [Pre-requisitos](#pre-requisitos)
2. [Fase 1: Preparación](#fase-1-preparación)
3. [Fase 2: Build de la Imagen Docker](#fase-2-build-de-la-imagen-docker)
4. [Fase 3: Push a Container Registry](#fase-3-push-a-container-registry)
5. [Fase 4: Crear Container App](#fase-4-crear-container-app)
6. [Fase 5: Verificación](#fase-5-verificación)
7. [Troubleshooting](#troubleshooting)

---

## Pre-requisitos

### Lo que necesitas antes de empezar:

- ✅ Backend ya desplegado y funcionando
- ✅ URL del backend (ej: `https://advisor-reports-backend.proudsky-12345678.eastus.azurecontainerapps.io`)
- ✅ Azure Container Registry creado (`advisorreportsacr`)
- ✅ Container Apps Environment creado (`advisor-reports-env`)
- ✅ Docker Desktop corriendo en tu máquina
- ✅ Credenciales del Container Registry

### Información que necesitarás guardar:

```
FRONTEND DEPLOYMENT INFO
==================================================

Backend API URL: _____________________________
Frontend URL (después de deployment): _____________________________

--- AZURE AD (REQUERIDO) ---
Client ID: _____________________________
Tenant ID: _____________________________
Redirect URI (será el Frontend URL): _____________________________
```

---

## Fase 1: Preparación

### Paso 1.1: Obtener la URL del Backend

1. Ve a Azure Portal → **Container Apps**
2. Abre `advisor-reports-backend`
3. En la página **Overview**, copia la **Application Url**
   - Ejemplo: `https://advisor-reports-backend.proudsky-12345678.eastus.azurecontainerapps.io`

📝 **Guarda**: Backend API URL

### Paso 1.2: Obtener Credenciales de Azure AD

Ya que tienes configurado Azure AD, necesitas obtener estos valores del App Registration:

1. Ve a **Azure Portal** → Busca **"Azure Active Directory"** o **"Microsoft Entra ID"**
2. En el menú izquierdo, haz clic en **"App registrations"**
3. Busca y haz clic en tu aplicación (ej: "Azure Advisor Reports" o el nombre que le hayas puesto)

**Obtener Application (client) ID:**
1. En la página **Overview** del App Registration
2. Copia el **Application (client) ID**
   - Ejemplo: `12345678-1234-1234-1234-123456789abc`

📝 **Guarda**: Application (client) ID como `AZURE_CLIENT_ID`

**Obtener Directory (tenant) ID:**
1. En la misma página **Overview**
2. Copia el **Directory (tenant) ID**
   - Ejemplo: `87654321-4321-4321-4321-987654321cba`

📝 **Guarda**: Directory (tenant) ID como `AZURE_TENANT_ID`

**Configurar Redirect URI (lo haremos después):**
- Por ahora, solo ten en cuenta que necesitarás agregar la URL del frontend después del deployment
- Ejemplo de lo que será: `https://advisor-reports-frontend.proudsky-12345678.eastus.azurecontainerapps.io`

💡 **Nota Importante**: El Redirect URI debe agregarse al App Registration DESPUÉS de obtener la URL del frontend en Azure. Lo haremos en la Fase 5.

### Paso 1.3: Verificar Estructura del Proyecto

Abre una terminal en tu máquina:

```bash
cd "D:\Code\Azure Reports\frontend"

# Verificar que existe el Dockerfile.prod
ls Dockerfile.prod

# Verificar que existe nginx.conf
ls nginx.conf
```

✅ **Verificación**: Deberías ver ambos archivos listados.

---

## Fase 2: Build de la Imagen Docker

### Paso 2.1: Entender las Variables de Entorno

El frontend React necesita conocer la URL del backend y las credenciales de Azure AD **en el momento del build** (no en runtime). Por eso usamos `ARG` en el Dockerfile.

**Variables que necesitamos:**
- `REACT_APP_API_URL`: URL del backend para las peticiones API
- `REACT_APP_AZURE_CLIENT_ID`: El Client ID de Azure AD
- `REACT_APP_AZURE_TENANT_ID`: El Tenant ID de Azure AD
- `REACT_APP_AZURE_REDIRECT_URI`: La URL del frontend (usaremos un placeholder por ahora)
- `REACT_APP_ENVIRONMENT`: Ambiente de producción

### Paso 2.2: Preparar el Build Command

Abre una terminal/PowerShell y navega al directorio del frontend:

```powershell
cd "D:\Code\Azure Reports\frontend"
```

### Paso 2.3: Construir la Imagen

Ahora vamos a construir la imagen. **IMPORTANTE**: Reemplaza los siguientes valores con tu información real:
- `TU_BACKEND_URL`: URL de tu backend (Paso 1.1)
- `TU_AZURE_CLIENT_ID`: Application ID de Azure AD (Paso 1.2)
- `TU_AZURE_TENANT_ID`: Directory ID de Azure AD (Paso 1.2)

**Comando de Build:**

```powershell
# Build de la imagen con variables de entorno
docker build `
  --build-arg REACT_APP_API_URL=https://TU_BACKEND_URL/api `
  --build-arg REACT_APP_AZURE_CLIENT_ID=TU_AZURE_CLIENT_ID `
  --build-arg REACT_APP_AZURE_TENANT_ID=TU_AZURE_TENANT_ID `
  --build-arg REACT_APP_AZURE_REDIRECT_URI=https://localhost:3000 `
  --build-arg REACT_APP_ENVIRONMENT=production `
  -t advisorreportsacr.azurecr.io/advisorreportsfrontend:latest `
  -f Dockerfile.prod `
  .
```

💡 **Nota sobre REDIRECT_URI**: Por ahora usamos `https://localhost:3000` como placeholder. Lo actualizaremos más adelante cuando tengamos la URL real del frontend en Azure.

**Ejemplo real** (reemplaza con tus valores):
```powershell
docker build `
  --build-arg REACT_APP_API_URL=https://advisor-reports-backend.proudsky-12345678.eastus.azurecontainerapps.io/api `
  --build-arg REACT_APP_AZURE_CLIENT_ID=12345678-1234-1234-1234-123456789abc `
  --build-arg REACT_APP_AZURE_TENANT_ID=87654321-4321-4321-4321-987654321cba `
  --build-arg REACT_APP_AZURE_REDIRECT_URI=https://localhost:3000 `
  --build-arg REACT_APP_ENVIRONMENT=production `
  -t advisorreportsacr.azurecr.io/advisorreportsfrontend:latest `
  -f Dockerfile.prod `
  .
```

⏱️ **Tiempo de espera**: 5-10 minutos (primera vez puede tardar más)

📝 **Explicación de los parámetros:**
- `--build-arg REACT_APP_API_URL=...`: URL del backend para que el frontend sepa dónde hacer las peticiones
- `--build-arg REACT_APP_AZURE_CLIENT_ID=...`: Client ID de Azure AD para autenticación
- `--build-arg REACT_APP_AZURE_TENANT_ID=...`: Tenant ID de Azure AD
- `--build-arg REACT_APP_AZURE_REDIRECT_URI=...`: URL a donde Azure AD redirige después del login (placeholder por ahora)
- `--build-arg REACT_APP_ENVIRONMENT=production`: Indica que es ambiente de producción
- `-t advisorreportsacr.azurecr.io/advisorreportsfrontend:latest`: Tag de la imagen
- `-f Dockerfile.prod`: Usa el Dockerfile de producción
- `.`: Contexto de build (directorio actual)

### Paso 2.4: Verificar la Imagen

```powershell
# Ver las imágenes Docker locales
docker images | Select-String "advisorreportsfrontend"
```

✅ **Verificación**: Deberías ver la imagen `advisorreportsacr.azurecr.io/advisorreportsfrontend` con tag `latest`

### Paso 2.5: Probar la Imagen Localmente (Opcional pero Recomendado)

Antes de subir a Azure, prueba que la imagen funciona:

```powershell
# Ejecutar el contenedor localmente
docker run -d -p 3000:80 --name frontend-test advisorreportsacr.azurecr.io/advisorreportsfrontend:latest

# Espera 5 segundos y luego abre en el navegador
Start-Sleep -Seconds 5
Start-Process "http://localhost:3000"
```

**Prueba en el navegador:**
1. Deberías ver la aplicación React cargando
2. Verifica que la interfaz se vea correctamente
3. Intenta navegar a diferentes páginas (no necesitas login aún)

**Detener el contenedor de prueba:**
```powershell
docker stop frontend-test
docker rm frontend-test
```

✅ **Verificación**: Si la aplicación carga correctamente en http://localhost:3000, ¡todo bien!

---

## Fase 3: Push a Container Registry

### Paso 3.1: Login al Container Registry

```powershell
# Login con las credenciales de tu ACR
docker login advisorreportsacr.azurecr.io
```

Te pedirá:
- **Username**: `advisorreportsacr` (o el nombre de tu registry)
- **Password**: [El password que guardaste del ACR]

💡 **Tip**: Si no recuerdas el password:
1. Ve a Azure Portal → **Container Registry** → `advisorreportsacr`
2. En el menú izquierdo → **Access keys**
3. Copia la password

✅ **Verificación**: Deberías ver "Login Succeeded"

### Paso 3.2: Push de la Imagen

```powershell
# Push de la imagen al registry
docker push advisorreportsacr.azurecr.io/advisorreportsfrontend:latest
```

⏱️ **Tiempo de espera**: 3-5 minutos (dependiendo de tu conexión a internet)

Verás algo como:
```
The push refers to repository [advisorreportsacr.azurecr.io/advisorreportsfrontend]
latest: digest: sha256:xxxx size: 1234
```

### Paso 3.3: Verificar en Azure Portal

1. Ve a Azure Portal
2. Busca tu Container Registry: `advisorreportsacr`
3. En el menú izquierdo, bajo **Services**, haz clic en **Repositories**
4. Deberías ver dos repositorios ahora:
   - `advisorreportsbackend` (del backend)
   - `advisorreportsfrontend` (nuevo, del frontend)
5. Haz clic en `advisorreportsfrontend`
6. Deberías ver el tag `latest` con la fecha/hora actual

✅ **Verificación**: La imagen debe aparecer con tamaño (~50-150 MB) y timestamp reciente

---

## Fase 4: Crear Container App

### Paso 4.1: Crear Frontend Container App

1. En Azure Portal, busca: **Container Apps**
2. Haz clic en **"+ Create"**

### Paso 4.2: Configuración Básica

**Pestaña "Basics":**

- **Subscription**: Tu suscripción
- **Resource group**: `azure-advisor-reports-mvp` (el mismo que el backend)
- **Container app name**: `advisor-reports-frontend`
- **Region**: `East US` (misma región que el backend)
- **Container Apps environment**: Selecciona `advisor-reports-env` (el mismo que el backend)

### Paso 4.3: Configuración del Container

**Pestaña "Container":**

- **Use quickstart image**: ❌ Desmarca esto
- **Name**: `frontend`
- **Image source**: `Azure Container Registry`
- **Registry**: Selecciona `advisorreportsacr.azurecr.io`
- **Image**: `advisorreportsfrontend`
- **Image tag**: `latest`
- **Authentication**: Selecciona `Admin credentials`

**CPU and Memory:**
- **CPU cores**: `0.25` (el frontend necesita menos recursos que el backend)
- **Memory (Gi)**: `0.5`

💡 **Explicación**: El frontend solo sirve archivos estáticos (HTML, CSS, JS) a través de nginx, no necesita mucha CPU o memoria.

### Paso 4.4: Configuración de Ingress

**Pestaña "Ingress":**

- **Ingress**: ✅ Habilitado
- **Ingress traffic**: `Accepting traffic from anywhere`
- **Ingress type**: `HTTP`
- **Target port**: `80` ⚠️ **IMPORTANTE**: Es 80, no 3000 (nginx escucha en el puerto 80)
- **Transport**: `Auto`

💡 **Explicación**:
- El frontend React se construyó como archivos estáticos
- Nginx los sirve en el puerto 80
- Por eso usamos puerto 80, no 3000 (que es para desarrollo)

### Paso 4.5: Configuración de Escala

**Pestaña "Scale":**

- **Min replicas**: `1`
- **Max replicas**: `3`

💡 **Explicación**: Con el tráfico bajo al inicio, 1 réplica es suficiente. Azure escalará automáticamente si aumenta el tráfico.

### Paso 4.6: Tags

**Pestaña "Tags":**
- **Name**: `Environment` → **Value**: `production`
- **Name**: `Project` → **Value**: `advisor-reports`
- **Name**: `Component` → **Value**: `frontend`

### Paso 4.7: Crear

1. Haz clic en **"Review + create"**
2. Revisa la configuración
3. **Costo estimado**: Verás el costo mensual (~$5-10/mes para el frontend)
4. Haz clic en **"Create"**

⏱️ **Tiempo de espera**: 3-5 minutos

✅ **Verificación**: Espera a que aparezca "Your deployment is complete"

### Paso 4.8: Obtener Frontend URL

1. Una vez creado, haz clic en **"Go to resource"**
2. En la página **Overview**, copia la **Application Url**
   - Ejemplo: `https://advisor-reports-frontend.proudsky-12345678.eastus.azurecontainerapps.io`

📝 **Guarda**: Frontend URL

---

## Fase 4.9: ⚠️ IMPORTANTE - Actualizar Azure AD Redirect URI

Ahora que tienes la URL real del frontend, necesitas hacer dos cosas:

### Paso 4.9.1: Agregar Redirect URI en Azure AD

1. Ve a **Azure Portal** → **Azure Active Directory** (o Microsoft Entra ID)
2. En el menú izquierdo, haz clic en **"App registrations"**
3. Busca y abre tu aplicación
4. En el menú izquierdo, haz clic en **"Authentication"**
5. En la sección **"Platform configurations"**, busca **"Single-page application"**
   - Si no existe, haz clic en **"+ Add a platform"** → **"Single-page application"**
6. En **"Redirect URIs"**, agrega tu frontend URL:
   ```
   https://advisor-reports-frontend.proudsky-12345678.eastus.azurecontainerapps.io
   ```
   ⚠️ **SIN barra al final** `/`

7. También agrega (si quieres poder probar localmente):
   ```
   http://localhost:3000
   ```

8. En **"Front-channel logout URL"** (opcional):
   ```
   https://advisor-reports-frontend.proudsky-12345678.eastus.azurecontainerapps.io
   ```

9. Haz clic en **"Save"** (arriba)

✅ **Verificación**: Deberías ver tus Redirect URIs listados en la página de Authentication.

### Paso 4.9.2: Rebuildar Frontend con URL Real

Ahora que tienes la URL real del frontend, necesitas rebuildar la imagen Docker con el Redirect URI correcto.

**¿Por qué?** Porque en el build anterior usamos `https://localhost:3000` como placeholder. Azure AD necesita que el Redirect URI en la aplicación coincida EXACTAMENTE con el configurado en Azure AD.

**Pasos:**

1. Abre PowerShell y navega al directorio del frontend:
   ```powershell
   cd "D:\Code\Azure Reports\frontend"
   ```

2. Rebuilda la imagen con la URL REAL del frontend:
   ```powershell
   docker build `
     --build-arg REACT_APP_API_URL=https://TU_BACKEND_URL/api `
     --build-arg REACT_APP_AZURE_CLIENT_ID=TU_AZURE_CLIENT_ID `
     --build-arg REACT_APP_AZURE_TENANT_ID=TU_AZURE_TENANT_ID `
     --build-arg REACT_APP_AZURE_REDIRECT_URI=https://TU_FRONTEND_URL `
     --build-arg REACT_APP_ENVIRONMENT=production `
     -t advisorreportsacr.azurecr.io/advisorreportsfrontend:latest `
     -f Dockerfile.prod `
     .
   ```

   **Ejemplo real** (reemplaza con tus valores):
   ```powershell
   docker build `
     --build-arg REACT_APP_API_URL=https://advisor-reports-backend.proudsky-12345678.eastus.azurecontainerapps.io/api `
     --build-arg REACT_APP_AZURE_CLIENT_ID=12345678-1234-1234-1234-123456789abc `
     --build-arg REACT_APP_AZURE_TENANT_ID=87654321-4321-4321-4321-987654321cba `
     --build-arg REACT_APP_AZURE_REDIRECT_URI=https://advisor-reports-frontend.proudsky-12345678.eastus.azurecontainerapps.io `
     --build-arg REACT_APP_ENVIRONMENT=production `
     -t advisorreportsacr.azurecr.io/advisorreportsfrontend:latest `
     -f Dockerfile.prod `
     .
   ```

3. Push de la nueva imagen:
   ```powershell
   docker push advisorreportsacr.azurecr.io/advisorreportsfrontend:latest
   ```

4. Restart del Container App en Azure:
   - Ve a Azure Portal → Container App `advisor-reports-frontend`
   - Haz clic en **"Restart"** (botón arriba)
   - Espera 2-3 minutos

✅ **Verificación**: El Container App debe reiniciarse y estar en estado "Running"

💡 **Explicación de este paso**:
- Azure AD valida que el Redirect URI en la petición coincida EXACTAMENTE con el configurado
- Como el Redirect URI se "bake" en el build de React, necesitamos rebuildar con el valor correcto
- Este es un paso necesario solo para producción; en desarrollo usas localhost

---

## Fase 5: Verificación

### Test 1: Acceder al Frontend

1. Abre tu navegador
2. Ve a: `https://[TU_FRONTEND_URL]`

✅ **Esperado**:
- Deberías ver la página principal de la aplicación
- La interfaz debe cargarse correctamente
- CSS y estilos deben aplicarse

❌ **Si ves error**: Ve a la sección [Troubleshooting](#troubleshooting)

### Test 2: Verificar Health Check

Abre en tu navegador:
```
https://[TU_FRONTEND_URL]/health
```

✅ **Esperado**: Deberías ver el texto `healthy`

### Test 3: Verificar Azure AD Login

1. En la aplicación frontend, haz clic en **"Sign in with Microsoft"** o el botón de login
2. Deberías ser redirigido a la página de login de Microsoft
3. Ingresa tus credenciales de Azure AD/Microsoft
4. Azure AD te pedirá consentimiento (primera vez)
5. Deberías ser redirigido de vuelta a tu aplicación

✅ **Esperado**:
- El login con Azure AD funciona correctamente
- Eres redirigido de vuelta a la aplicación después del login
- Puedes ver tu información de usuario en la aplicación
- No aparecen errores de CORS

❌ **Si hay errores**:
- **"AADSTS50011: The redirect URI specified in the request does not match"**
  → Verifica que el Redirect URI en Azure AD coincide EXACTAMENTE con el de tu frontend
  → Rebuilda la imagen con la URL correcta (Paso 4.9.2)

- **Errores de CORS**: Ve a [Troubleshooting - Problema 1](#problema-1-errores-de-cors)

- **"Invalid client_id" o "Invalid tenant_id"**:
  → Verifica que los valores de Azure AD son correctos
  → Rebuilda la imagen con los valores correctos

### Test 4: Verificar Console del Navegador

1. Abre el frontend en tu navegador
2. Presiona `F12` para abrir DevTools
3. Ve a la pestaña **Console**

✅ **Esperado**:
- No deberías ver errores rojos
- Puede haber warnings (amarillos), pero no errores

### Test 5: Verificar Network Requests

1. En DevTools, ve a la pestaña **Network**
2. Recarga la página (`F5`)
3. Filtra por "Fetch/XHR"

✅ **Esperado**:
- Deberías ver peticiones a tu backend URL
- Status codes deben ser 200 (OK) o 304 (Not Modified)
- No debería haber 404s o 500s

### Test 6: Verificar Logs del Container

1. Ve a Azure Portal → Container App `advisor-reports-frontend`
2. En el menú izquierdo, bajo **Monitoring**, haz clic en **Log stream**

✅ **Esperado**:
```
/docker-entrypoint.sh: Configuration complete; ready for start up
```

No deberían aparecer errores.

---

## Configuración Adicional (Opcional)

### Configurar CORS en el Backend

Si ves errores de CORS, necesitas actualizar la configuración del backend:

1. Ve a Container App: `advisor-reports-backend`
2. **Containers** → **Edit and deploy**
3. Busca o agrega la variable de entorno:
   - **Name**: `CORS_ALLOWED_ORIGINS`
   - **Value**: `https://advisor-reports-frontend.proudsky-12345678.eastus.azurecontainerapps.io`
     (Reemplaza con tu frontend URL real)
4. Haz clic en **Create**

⏱️ **Tiempo**: 2-3 minutos para aplicar cambios

### Configurar Custom Domain (Opcional)

Si tienes un dominio personalizado (ej: `reports.tuempresa.com`):

1. Ve al Container App `advisor-reports-frontend`
2. En el menú izquierdo, bajo **Settings**, haz clic en **Custom domains**
3. Haz clic en **"+ Add custom domain"**
4. Sigue el asistente:
   - Ingresa tu dominio
   - Crea un CNAME record en tu DNS apuntando a la URL del Container App
   - Verifica el dominio
   - Agrega un certificado SSL (Azure puede proveer uno gratuito)

---

## Troubleshooting

### Problema 1: Errores de CORS

**Síntomas**:
- En la consola del navegador ves: `Access to fetch at '...' from origin '...' has been blocked by CORS policy`

**Solución**:

1. Ve al backend Container App: `advisor-reports-backend`
2. **Containers** → **Edit and deploy** → **Environment variables**
3. Agrega o actualiza:
   ```
   CORS_ALLOWED_ORIGINS=https://advisor-reports-frontend.proudsky-12345678.eastus.azurecontainerapps.io
   ```
   (Usa tu URL de frontend real)
4. Si ya existe, asegúrate de que incluya tu frontend URL
5. Si tienes múltiples URLs, sepáralas con comas:
   ```
   CORS_ALLOWED_ORIGINS=https://frontend1.com,https://frontend2.com
   ```

### Problema 2: El Frontend Carga Pero No Se Conecta al Backend

**Síntomas**:
- El frontend se ve bien visualmente
- Pero no puedes hacer login o cargar datos
- En la consola ves errores de red

**Solución**:

**Causa**: La URL del backend no se configuró correctamente en el build.

**Pasos**:

1. Verifica que usaste la URL correcta en el build:
   ```powershell
   # Revisa el comando que usaste
   docker history advisorreportsacr.azurecr.io/advisorreportsfrontend:latest
   ```

2. Si usaste una URL incorrecta, necesitas rebuild:
   ```powershell
   cd "D:\Code\Azure Reports\frontend"

   # Build con la URL CORRECTA
   docker build `
     --build-arg REACT_APP_API_URL=https://TU_BACKEND_URL_CORRECTA/api `
     --build-arg REACT_APP_ENVIRONMENT=production `
     -t advisorreportsacr.azurecr.io/advisorreportsfrontend:latest `
     -f Dockerfile.prod `
     .

   # Push de nuevo
   docker push advisorreportsacr.azurecr.io/advisorreportsfrontend:latest
   ```

3. En Azure Portal, restart el Container App:
   - Ve a `advisor-reports-frontend`
   - Haz clic en **Restart** (arriba)

### Problema 3: Container No Inicia o Se Reinicia Constantemente

**Síntomas**: Estado "Provisioning" o "Failed", o se reinicia cada pocos segundos

**Solución**:

1. Ve al Container App `advisor-reports-frontend`
2. **Monitoring** → **Log stream**
3. Busca errores en los logs

**Errores Comunes**:

- `nginx: [emerg] bind() to 0.0.0.0:80 failed`: El puerto 80 ya está en uso (no debería pasar en Container Apps)
- `Permission denied`: Problemas de permisos (verifica que nginx.conf es correcto)

4. Si ves errores en el build, rebuilda la imagen:
   ```powershell
   cd "D:\Code\Azure Reports\frontend"
   docker build --no-cache -f Dockerfile.prod -t advisorreportsacr.azurecr.io/advisorreportsfrontend:latest .
   ```

### Problema 4: 404 en Todas las Rutas Excepto la Principal

**Síntomas**:
- La página principal (`/`) funciona
- Pero `/reports`, `/clients`, etc. dan 404

**Solución**:

Esto es un problema de nginx routing para SPAs (Single Page Applications).

**Causa**: El nginx.conf no está configurado correctamente.

**Verificar nginx.conf tiene**:
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

Si no lo tiene, actualiza el archivo `frontend/nginx.conf` línea 81-85 con esto y rebuilda.

### Problema 5: Estilos No Se Aplican (Página Sin CSS)

**Síntomas**: La página carga pero sin estilos, parece texto plano

**Solución**:

1. Abre DevTools → Network → Busca archivos `.css` o `.js`
2. Si ves 404 en estos archivos, es un problema de build

**Rebuilda con cache limpio**:
```powershell
cd "D:\Code\Azure Reports\frontend"

# Limpia node_modules y build
Remove-Item -Recurse -Force node_modules, build -ErrorAction SilentlyContinue

# Reinstala dependencias
npm ci

# Build local para verificar
npm run build

# Verifica que build/ tiene archivos
ls build/static/css
ls build/static/js

# Si todo se ve bien, rebuilda Docker
docker build --no-cache -f Dockerfile.prod `
  --build-arg REACT_APP_API_URL=https://TU_BACKEND_URL/api `
  -t advisorreportsacr.azurecr.io/advisorreportsfrontend:latest .

# Push
docker push advisorreportsacr.azurecr.io/advisorreportsfrontend:latest
```

### Problema 6: "Failed to fetch" en el Login

**Síntomas**: Al intentar login, aparece error "Failed to fetch" o "Network error"

**Causas Posibles**:
1. Backend no está corriendo
2. URL del backend incorrecta
3. CORS no configurado

**Solución**:

**Paso 1**: Verifica que el backend está corriendo:
```
https://TU_BACKEND_URL/api/
```
Debería responder con JSON.

**Paso 2**: Verifica la URL en el frontend:
- Abre DevTools → Network
- Intenta login
- Mira la URL de la petición
- ¿Es correcta? ¿Tiene `/api` al final?

**Paso 3**: Configura CORS (ver Problema 1)

### Problema 7: Errores de Azure AD Authentication

**Síntomas**: No puedes hacer login con Azure AD

**Error 1: "AADSTS50011: The redirect URI specified in the request does not match"**

**Causa**: El Redirect URI en Azure AD no coincide con el que está en tu aplicación.

**Solución**:

1. Verifica en Azure AD → App Registration → Authentication:
   - Debe tener exactamente: `https://advisor-reports-frontend.proudsky-12345678.eastus.azurecontainerapps.io`
   - SIN barra al final `/`
   - Debe ser "Single-page application" type

2. Verifica que rebuildeaste la imagen con la URL correcta:
   ```powershell
   cd "D:\Code\Azure Reports\frontend"

   docker build `
     --build-arg REACT_APP_API_URL=https://TU_BACKEND_URL/api `
     --build-arg REACT_APP_AZURE_CLIENT_ID=TU_CLIENT_ID `
     --build-arg REACT_APP_AZURE_TENANT_ID=TU_TENANT_ID `
     --build-arg REACT_APP_AZURE_REDIRECT_URI=https://TU_FRONTEND_URL `
     --build-arg REACT_APP_ENVIRONMENT=production `
     -t advisorreportsacr.azurecr.io/advisorreportsfrontend:latest `
     -f Dockerfile.prod .

   docker push advisorreportsacr.azurecr.io/advisorreportsfrontend:latest
   ```

3. Restart el Container App en Azure

**Error 2: "AADSTS700016: Application with identifier was not found"**

**Causa**: Client ID incorrecto

**Solución**:
1. Ve a Azure AD → App Registration → Overview
2. Copia el **Application (client) ID** correcto
3. Rebuilda con el Client ID correcto

**Error 3: "AADSTS90002: Tenant not found"**

**Causa**: Tenant ID incorrecto

**Solución**:
1. Ve a Azure AD → App Registration → Overview
2. Copia el **Directory (tenant) ID** correcto
3. Rebuilda con el Tenant ID correcto

**Error 4: "AADSTS65001: The user or administrator has not consented"**

**Causa**: Es la primera vez que usas la app y necesitas dar consentimiento

**Solución**:
1. Esto es normal la primera vez
2. Haz clic en "Accept" cuando Azure AD pida permisos
3. Si el error persiste:
   - Ve a Azure AD → App Registration → API permissions
   - Verifica que tiene permisos: `User.Read`, `openid`, `profile`, `email`
   - Haz clic en "Grant admin consent" (si tienes permisos de admin)

**Error 5: "CORS error" al hacer login con Azure AD**

**Causa**: Configuración de CORS faltante

**Solución**:
1. Verifica que el backend tiene configurado CORS para tu frontend
2. Ve al backend Container App → Environment variables
3. Verifica `CORS_ALLOWED_ORIGINS` incluye tu frontend URL

---

## Resumen de URLs Finales

Al finalizar, tendrás:

### URLs Públicas:
- **Frontend**: `https://advisor-reports-frontend.[random].eastus.azurecontainerapps.io`
- **Backend API**: `https://advisor-reports-backend.[random].eastus.azurecontainerapps.io`

### Acceso:
- **Frontend**: Acceso público directo por URL
- **Login**: Usa las credenciales de Django admin

### Recursos en Azure:
- **Container Apps**:
  - `advisor-reports-backend` (ya existente)
  - `advisor-reports-frontend` (nuevo)
  - `advisor-reports-worker` (ya existente)
  - `advisor-reports-beat` (ya existente)

### Costos Estimados Adicionales:
- Frontend Container App: ~$5-10/mes (muy bajo porque es solo nginx sirviendo estáticos)

---

## Próximos Pasos

1. ✅ **Configurar HTTPS** (ya está - Container Apps provee certificados automáticamente)

2. ✅ **Configurar Custom Domain** (opcional)
   - Compra un dominio
   - Configúralo en ambos Container Apps (frontend y backend)

3. ✅ **Habilitar Azure AD** (opcional, para autenticación empresarial)
   - Crea App Registration en Azure AD
   - Actualiza variables de entorno
   - Rebuilda frontend con nuevos valores

4. ✅ **Configurar CDN** (opcional, para mejor rendimiento)
   - Azure Front Door
   - Azure CDN

5. ✅ **Monitoreo**
   - Los logs ya están en Application Insights
   - Configura alertas para el frontend también

---

## Checklist de Deployment

**Fase Inicial:**
- [ ] Backend URL obtenida
- [ ] Azure AD Client ID y Tenant ID obtenidos
- [ ] Imagen Docker construida con placeholder
- [ ] Imagen probada localmente (http://localhost:3000)
- [ ] Imagen pushed a Container Registry
- [ ] Container App del frontend creado
- [ ] Frontend URL obtenida

**Configuración de Azure AD:**
- [ ] Redirect URI agregado en Azure AD App Registration
- [ ] Redirect URI configurado como "Single-page application"
- [ ] Imagen rebuildeada con URL real del frontend
- [ ] Nueva imagen pushed a Container Registry
- [ ] Container App reiniciado

**Verificación:**
- [ ] Frontend carga correctamente en el navegador
- [ ] Health check responde (/health)
- [ ] Login con Azure AD funciona correctamente
- [ ] Usuario redirigido correctamente después del login
- [ ] Dashboard y páginas principales accesibles
- [ ] No hay errores en la consola del navegador
- [ ] Network requests al backend funcionan correctamente
- [ ] CORS configurado en el backend
- [ ] Documentación actualizada con URLs finales

**¡Felicidades! Has desplegado exitosamente el frontend del Azure Advisor Reports Platform.**

---

## Comandos de Referencia Rápida

```powershell
# ========================================
# Build INICIAL (con placeholder)
# ========================================
cd "D:\Code\Azure Reports\frontend"
docker build `
  --build-arg REACT_APP_API_URL=https://TU_BACKEND_URL/api `
  --build-arg REACT_APP_AZURE_CLIENT_ID=TU_CLIENT_ID `
  --build-arg REACT_APP_AZURE_TENANT_ID=TU_TENANT_ID `
  --build-arg REACT_APP_AZURE_REDIRECT_URI=https://localhost:3000 `
  --build-arg REACT_APP_ENVIRONMENT=production `
  -t advisorreportsacr.azurecr.io/advisorreportsfrontend:latest `
  -f Dockerfile.prod .

# ========================================
# Build FINAL (con URL real del frontend)
# ========================================
docker build `
  --build-arg REACT_APP_API_URL=https://TU_BACKEND_URL/api `
  --build-arg REACT_APP_AZURE_CLIENT_ID=TU_CLIENT_ID `
  --build-arg REACT_APP_AZURE_TENANT_ID=TU_TENANT_ID `
  --build-arg REACT_APP_AZURE_REDIRECT_URI=https://TU_FRONTEND_URL `
  --build-arg REACT_APP_ENVIRONMENT=production `
  -t advisorreportsacr.azurecr.io/advisorreportsfrontend:latest `
  -f Dockerfile.prod .

# Login al registry
docker login advisorreportsacr.azurecr.io

# Push de la imagen
docker push advisorreportsacr.azurecr.io/advisorreportsfrontend:latest

# Probar localmente
docker run -d -p 3000:80 --name test advisorreportsacr.azurecr.io/advisorreportsfrontend:latest
# Abrir http://localhost:3000 en el navegador
docker stop test && docker rm test

# Ver logs del contenedor local
docker logs test

# Limpiar imágenes antiguas
docker image prune -a
```

---

## Recursos Útiles

- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)
- [React Production Build](https://create-react-app.dev/docs/production-build/)
- [Docker Build Documentation](https://docs.docker.com/engine/reference/commandline/build/)

¿Necesitas ayuda? Consulta la sección de Troubleshooting o revisa los logs en Azure Portal.
