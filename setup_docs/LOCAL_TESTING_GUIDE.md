# 🧪 Guía de Pruebas Locales - Azure Advisor Reports Platform

**Última actualización:** 4 de Octubre, 2025
**Ambiente:** Windows 10/11
**Duración estimada:** 30-45 minutos

---

## 📋 Tabla de Contenidos

1. [Pre-requisitos](#pre-requisitos)
2. [Paso 1: Iniciar Servicios con Docker](#paso-1-iniciar-servicios-con-docker)
3. [Paso 2: Configurar Backend](#paso-2-configurar-backend)
4. [Paso 3: Configurar Frontend](#paso-3-configurar-frontend)
5. [Paso 4: Pruebas Funcionales](#paso-4-pruebas-funcionales)
6. [Paso 5: Verificar Todo Funciona](#paso-5-verificar-todo-funciona)
7. [Solución de Problemas](#solución-de-problemas)

---

## Pre-requisitos

### ✅ Software Necesario

Verifica que tienes instalado:

```powershell
# Python 3.11+
python --version

# Node.js 18+
node --version

# Docker Desktop
docker --version
docker-compose --version
```

**Si falta algo:**
- Python: https://www.python.org/downloads/
- Node.js: https://nodejs.org/
- Docker Desktop: https://www.docker.com/products/docker-desktop/

---

## Paso 1: Iniciar Servicios con Docker

### 1.1 Verificar Docker Desktop está corriendo

Abre Docker Desktop y asegúrate que está corriendo (ícono verde en la barra de tareas).

### 1.2 Iniciar PostgreSQL y Redis

Abre PowerShell en la carpeta del proyecto:

```powershell
# Navegar al proyecto
cd "D:\Code\Azure Reports"

# Iniciar solo PostgreSQL y Redis
docker-compose up -d postgres redis
```

**Salida esperada:**
```
✔ Container azure-advisor-reports-postgres-1  Started
✔ Container azure-advisor-reports-redis-1     Started
```

### 1.3 Verificar servicios están corriendo

```powershell
# Ver servicios activos
docker-compose ps
```

**Debes ver:**
```
NAME                                    STATUS              PORTS
azure-advisor-reports-postgres-1        Up 10 seconds       0.0.0.0:5432->5432/tcp
azure-advisor-reports-redis-1           Up 10 seconds       0.0.0.0:6379->6379/tcp
```

---

## Paso 2: Configurar Backend

### 2.1 Activar entorno virtual de Python

```powershell
cd azure_advisor_reports

# Activar virtual environment
.\venv\Scripts\Activate.ps1
```

**Tu terminal debe mostrar:** `(venv)` al inicio

### 2.2 Verificar dependencias instaladas

```powershell
# Si es la primera vez, instalar dependencias
pip install -r requirements.txt
```

### 2.3 Configurar variables de entorno

Verifica que existe el archivo `.env` en `azure_advisor_reports/`:

```powershell
# Ver si existe .env
Test-Path .env
```

Si retorna `False`, crea el archivo `.env`:

```powershell
# Copiar desde ejemplo
Copy-Item .env.example .env -ErrorAction SilentlyContinue
```

**Edita `.env` con estos valores mínimos para desarrollo:**

```bash
# Django Settings
SECRET_KEY=dev-secret-key-change-in-production-123456789
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (usando Docker)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/azure_advisor_reports

# Redis (usando Docker)
REDIS_URL=redis://localhost:6379/0

# Azure AD (placeholders - no funcional sin Azure AD real)
AZURE_CLIENT_ID=00000000-0000-0000-0000-000000000000
AZURE_CLIENT_SECRET=placeholder-secret
AZURE_TENANT_ID=00000000-0000-0000-0000-000000000000
AZURE_REDIRECT_URI=http://localhost:3000

# Environment
DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.development
```

### 2.4 Ejecutar migraciones de base de datos

```powershell
# Crear tablas en PostgreSQL
python manage.py migrate
```

**Salida esperada:**
```
Operations to perform:
  Apply all migrations: admin, auth, authentication, clients, reports, analytics, ...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
  ✓ Migrations completed successfully
```

### 2.5 Crear usuario administrador (opcional)

```powershell
# Crear superuser para el admin panel
python manage.py createsuperuser

# Te pedirá:
Email: admin@example.com
Password: ********
Password (again): ********
```

### 2.6 Iniciar servidor Django

```powershell
# Iniciar servidor de desarrollo
python manage.py runserver
```

**Salida esperada:**
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
October 04, 2025 - 10:30:00
Django version 4.2.5, using settings 'azure_advisor_reports.settings.development'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### 2.7 Verificar Backend funciona

Abre tu navegador y ve a:

**✅ Health Check:**
- URL: http://localhost:8000/api/health/
- Debe mostrar: `{"status": "healthy", "database": "ok", "cache": "ok"}`

**✅ Admin Panel:**
- URL: http://localhost:8000/admin/
- Debe mostrar la página de login de Django Admin
- Prueba login con el superuser que creaste

**✅ API Root:**
- URL: http://localhost:8000/api/
- Debe mostrar la página de DRF (Django REST Framework)

---

## Paso 3: Configurar Frontend

### 3.1 Abrir nueva terminal de PowerShell

**Importante:** Deja el backend corriendo y abre una **nueva terminal** para el frontend.

```powershell
cd "D:\Code\Azure Reports\frontend"
```

### 3.2 Instalar dependencias (si es primera vez)

```powershell
npm install
```

**Tiempo:** 2-5 minutos dependiendo de tu conexión.

### 3.3 Configurar variables de entorno

Verifica que existe `.env.local`:

```powershell
Test-Path .env.local
```

Si retorna `False`, créalo:

```powershell
# Crear archivo .env.local
@"
# API Backend URL
REACT_APP_API_URL=http://localhost:8000/api

# Azure AD Configuration (placeholders - login no funcionará sin Azure AD real)
REACT_APP_AZURE_CLIENT_ID=00000000-0000-0000-0000-000000000000
REACT_APP_AZURE_TENANT_ID=00000000-0000-0000-0000-000000000000
REACT_APP_AZURE_REDIRECT_URI=http://localhost:3000

# Development Settings
REACT_APP_ENABLE_ANALYTICS=false
REACT_APP_ENABLE_PWA=false
"@ | Out-File -FilePath .env.local -Encoding utf8
```

### 3.4 Iniciar servidor de desarrollo React

```powershell
npm start
```

**Salida esperada:**
```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.1.X:3000

Note that the development build is not optimized.
To create a production build, use npm run build.

webpack compiled successfully
```

El navegador debe abrirse automáticamente en http://localhost:3000

---

## Paso 4: Pruebas Funcionales

### 4.1 Verificar Frontend se carga

**✅ Página de Login debe aparecer:**
- Logo de Azure Advisor Reports
- Botón "Sign in with Microsoft"
- Información del proyecto

**⚠️ Nota:** El login de Azure AD NO funcionará porque necesitas una aplicación real de Azure AD. Esto es normal en desarrollo local.

### 4.2 Verificar API está conectada

Abre las **Developer Tools** del navegador (F12) y ve a la pestaña **Console**.

**No debe haber errores de conexión** como:
- ❌ "Failed to fetch"
- ❌ "Network Error"
- ❌ "CORS Error"

Si ves errores CORS, verifica que el backend tiene CORS configurado en `settings/development.py`.

### 4.3 Probar Health Check desde el Frontend

En la consola del navegador (F12 > Console), ejecuta:

```javascript
fetch('http://localhost:8000/api/health/')
  .then(res => res.json())
  .then(data => console.log('Backend Health:', data))
  .catch(err => console.error('Error:', err));
```

**Debe mostrar:**
```javascript
Backend Health: {
  status: "healthy",
  database: "ok",
  cache: "ok"
}
```

### 4.4 Probar API de Clientes

```javascript
fetch('http://localhost:8000/api/clients/')
  .then(res => res.json())
  .then(data => console.log('Clients API:', data))
  .catch(err => console.error('Error:', err));
```

**Debe retornar lista vacía (sin autenticación):**
```javascript
Clients API: {
  detail: "Authentication credentials were not provided."
}
```

**✅ Esto es correcto** - significa que la API está funcionando pero requiere autenticación.

---

## Paso 5: Verificar Todo Funciona

### ✅ Checklist de Verificación

Marca cada item cuando lo verifiques:

**Backend:**
- [ ] ✅ PostgreSQL corriendo en Docker
- [ ] ✅ Redis corriendo en Docker
- [ ] ✅ Django servidor corriendo en http://localhost:8000
- [ ] ✅ Health check retorna status "healthy"
- [ ] ✅ Admin panel accesible en /admin/
- [ ] ✅ API root accesible en /api/

**Frontend:**
- [ ] ✅ React servidor corriendo en http://localhost:3000
- [ ] ✅ Página de login se carga correctamente
- [ ] ✅ No hay errores en la consola del navegador
- [ ] ✅ Puede conectarse a la API del backend

**Servicios Docker:**
- [ ] ✅ Docker Desktop corriendo
- [ ] ✅ Contenedor postgres healthy
- [ ] ✅ Contenedor redis healthy

### 📊 Panel de Estado

Ejecuta este script para ver el estado de todos los servicios:

```powershell
# Crear script de verificación
@"
Write-Host "=== Estado de Servicios Azure Advisor Reports ===" -ForegroundColor Cyan

# Docker
Write-Host "`n🐳 Docker Containers:" -ForegroundColor Yellow
docker-compose ps

# Backend (verificar si puerto 8000 está en uso)
Write-Host "`n🔧 Backend (Django):" -ForegroundColor Yellow
`$backend = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if (`$backend) {
    Write-Host "   ✅ Django corriendo en puerto 8000" -ForegroundColor Green
} else {
    Write-Host "   ❌ Django NO está corriendo" -ForegroundColor Red
}

# Frontend (verificar si puerto 3000 está en uso)
Write-Host "`n⚛️  Frontend (React):" -ForegroundColor Yellow
`$frontend = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if (`$frontend) {
    Write-Host "   ✅ React corriendo en puerto 3000" -ForegroundColor Green
} else {
    Write-Host "   ❌ React NO está corriendo" -ForegroundColor Red
}

# Health Check
Write-Host "`n🏥 Health Check:" -ForegroundColor Yellow
try {
    `$health = Invoke-RestMethod -Uri "http://localhost:8000/api/health/" -Method Get
    if (`$health.status -eq "healthy") {
        Write-Host "   ✅ Backend healthy" -ForegroundColor Green
        Write-Host "   ✅ Database: `$(`$health.database)" -ForegroundColor Green
        Write-Host "   ✅ Cache: `$(`$health.cache)" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Backend no responde" -ForegroundColor Red
}

Write-Host "`n=============================================" -ForegroundColor Cyan
"@ | Out-File -FilePath check-status.ps1 -Encoding utf8

# Ejecutar
.\check-status.ps1
```

---

## Solución de Problemas

### 🔧 Problema: "Port 5432 already in use"

**Solución:**
```powershell
# Detener todos los contenedores
docker-compose down

# Reiniciar
docker-compose up -d postgres redis
```

### 🔧 Problema: "ModuleNotFoundError: No module named 'apps'"

**Solución:**
```powershell
# Asegúrate de estar en la carpeta correcta
cd azure_advisor_reports

# Reinstalar dependencias
pip install -r requirements.txt
```

### 🔧 Problema: "CORS Error" en el frontend

**Solución:**

Verifica `azure_advisor_reports/settings/development.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

### 🔧 Problema: "Database connection failed"

**Solución:**
```powershell
# Verificar PostgreSQL está corriendo
docker-compose ps postgres

# Ver logs de PostgreSQL
docker-compose logs postgres

# Reiniciar PostgreSQL
docker-compose restart postgres
```

### 🔧 Problema: Frontend no carga en http://localhost:3000

**Solución:**
```powershell
# Detener servidor React
Ctrl+C

# Limpiar cache
npm cache clean --force

# Reinstalar node_modules
Remove-Item -Recurse -Force node_modules
npm install

# Reiniciar
npm start
```

### 🔧 Problema: "Cannot activate virtual environment"

**Solución:**
```powershell
# Si PowerShell bloquea scripts, ejecuta:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Luego intenta activar de nuevo
.\venv\Scripts\Activate.ps1
```

---

## 🧹 Limpieza al Terminar

Cuando termines de probar:

```powershell
# Detener frontend (Ctrl+C en terminal de React)

# Detener backend (Ctrl+C en terminal de Django)

# Detener Docker containers
docker-compose down

# (Opcional) Limpiar volúmenes de Docker
docker-compose down -v
```

---

## 📚 Siguientes Pasos

Una vez que todo funcione en local:

1. ✅ **Completar pruebas unitarias** (backend al 85% coverage)
2. ✅ **Configurar Azure AD** para pruebas de autenticación
3. ✅ **Desplegar a Azure Dev** usando los scripts de deployment
4. ✅ **Pruebas de integración** en Azure Dev
5. ✅ **Desplegar a Staging**
6. 🚀 **Producción**

---

## 📞 ¿Necesitas Ayuda?

Si encuentras problemas:

1. **Revisa los logs:**
   - Backend: Ver terminal de Django
   - Frontend: Ver consola del navegador (F12)
   - Docker: `docker-compose logs`

2. **Documentación:**
   - `TROUBLESHOOTING.md` - Guía de resolución de problemas
   - `README.md` - Información general del proyecto
   - `CLAUDE.md` - Guía de desarrollo

3. **Verifica configuración:**
   - `.env` en backend
   - `.env.local` en frontend
   - `docker-compose.yml`

---

**✅ ¡Listo! Tu ambiente local está funcionando correctamente.**

**URLs importantes:**
- Backend API: http://localhost:8000/api/
- Frontend: http://localhost:3000
- Django Admin: http://localhost:8000/admin/
- Health Check: http://localhost:8000/api/health/
