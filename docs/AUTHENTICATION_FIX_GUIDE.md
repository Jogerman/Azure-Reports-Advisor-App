# Guía de Solución de Problemas de Autenticación
## Azure Advisor Reports Platform v1.2.2

---

## 📋 Resumen del Problema

**Error reportado:** `AADSTS90002: Tenant '06bf3e54-7223-498a-a4db-2f4e68d7e38d' not found`

**Causa raíz:** El Tenant ID `06bf3e54-7223-498a-a4db-2f4e68d7e38d` NO existe en los archivos de configuración actuales. Este error proviene de:

1. **Cache del navegador (localStorage)** - MSAL almacena configuración antigua
2. **Service Worker cache** - Puede estar sirviendo código obsoleto
3. **Build cache** - Bundle de producción con valores hardcodeados antiguos

---

## ✅ Configuración Correcta Actual

### Frontend (.env.local)
```env
REACT_APP_AZURE_CLIENT_ID=a6401ee1-0c80-439a-9ca7-e1069fa770ba
REACT_APP_AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565
REACT_APP_AZURE_REDIRECT_URI=http://localhost:3000
```

### Backend (.env)
```env
AZURE_CLIENT_ID=a6401ee1-0c80-439a-9ca7-e1069fa770ba
AZURE_CLIENT_SECRET=your-client-secret-here
AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565
```

---

## 🔧 Soluciones Implementadas

### 1. **Actualización de Versión** ✅
- **Archivo:** `frontend/package.json`
- **Cambio:** Versión actualizada de `0.1.0` → `1.2.2`
- **Motivo:** Tracking apropiado de versiones para producción

### 2. **Validación de Variables de Entorno** ✅
- **Archivo:** `frontend/src/config/authConfig.ts`
- **Mejoras implementadas:**
  - Validación automática de variables de entorno requeridas
  - Logs de diagnóstico para depuración
  - Mensajes de error claros cuando faltan variables
  - Uso de TypeScript non-null assertion (`!`) para mayor seguridad de tipos

**Características:**
```typescript
// Validación automática al cargar el módulo
validateEnvVars();

// Logs informativos (sin datos sensibles)
console.log('✅ Azure AD Configuration initialized:');
console.log('  - Client ID:', clientId.substring(0, 8) + '...');
console.log('  - Tenant ID:', tenantId.substring(0, 8) + '...');
```

### 3. **Script de Limpieza de Cache** ✅
- **Archivo:** `frontend/public/clear-auth-cache.html`
- **Ubicación:** `http://localhost:3000/clear-auth-cache.html` (una vez desplegado)
- **Funcionalidad:**
  - Limpia localStorage (tokens MSAL y JWT)
  - Limpia sessionStorage
  - Elimina cookies relacionadas con MSAL
  - Desregistra Service Workers
  - Limpia Cache API del navegador
  - Interfaz visual amigable con estado en tiempo real

**Uso:**
1. Navegar a: `http://localhost:3000/clear-auth-cache.html`
2. Click en "Clear All Authentication Cache"
3. Esperar confirmación de limpieza exitosa
4. Regresar a la aplicación

### 4. **Actualización de .env.production** ✅
- **Archivo:** `frontend/.env.production`
- **Mejoras:**
  - Documentación detallada en el archivo
  - Instrucciones paso a paso para obtener los valores
  - Ejemplos claros (marcados como NO USAR)
  - Warnings visibles sobre placeholder values
  - Se agregó `REACT_APP_AZURE_POST_LOGOUT_REDIRECT_URI`

---

## 🚀 Pasos para Resolver el Problema

### Opción A: Solución Rápida (Recomendada)

#### 1. Limpiar Cache del Navegador

**Método 1: Usar el Script de Limpieza**
```bash
# En una nueva terminal
cd frontend
npm start

# Luego, en el navegador:
# Navegar a: http://localhost:3000/clear-auth-cache.html
# Click en "Clear All Authentication Cache"
```

**Método 2: Manual en el Navegador**
1. Abrir DevTools (F12)
2. Application → Storage → Clear site data
3. Seleccionar todo y click en "Clear data"
4. Cerrar y reabrir el navegador

#### 2. Limpiar Cache de Build
```bash
cd frontend

# Limpiar node_modules y reinstalar (opcional pero recomendado)
rm -rf node_modules
rm -rf build
npm cache clean --force
npm install

# Rebuild
npm run build
```

#### 3. Verificar Variables de Entorno
```bash
# Verificar que las variables están correctas
cat frontend/.env.local | grep AZURE

# Deberías ver:
# REACT_APP_AZURE_CLIENT_ID=a6401ee1-0c80-439a-9ca7-e1069fa770ba
# REACT_APP_AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565
```

#### 4. Reiniciar la Aplicación
```bash
# Detener el servidor (Ctrl+C)

# Limpiar y reiniciar
cd frontend
npm start

# En otra terminal, iniciar backend
cd azure_advisor_reports
python manage.py runserver
```

#### 5. Verificar en la Consola del Navegador
Abre DevTools (F12) y verifica que veas:
```
✅ Azure AD Configuration initialized:
  - Client ID: a6401ee1...
  - Tenant ID: 9acf6dd6...
  - Redirect URI: http://localhost:3000
```

### Opción B: Solución Completa con Rebuild

```bash
# 1. Detener todos los servidores
# Ctrl+C en todas las terminales

# 2. Limpiar completamente el frontend
cd frontend
rm -rf node_modules
rm -rf build
rm -rf .cache
npm cache clean --force

# 3. Reinstalar dependencias
npm install

# 4. Verificar configuración
echo "Verificando .env.local..."
cat .env.local | grep AZURE

# 5. Rebuild y restart
npm start
```

---

## 🔍 Verificación y Diagnóstico

### Verificar Configuración Cargada

#### En el navegador (DevTools Console):
```javascript
// Ver configuración actual de MSAL
console.log('MSAL Config:', msalInstance.config);

// Ver localStorage
Object.keys(localStorage).filter(k => k.includes('msal'));

// Ver todas las variables de entorno (solo development)
console.log('Client ID:', process.env.REACT_APP_AZURE_CLIENT_ID);
console.log('Tenant ID:', process.env.REACT_APP_AZURE_TENANT_ID);
```

### Logs Esperados

**✅ Configuración Correcta:**
```
✅ Azure AD Configuration initialized:
  - Client ID: a6401ee1...
  - Tenant ID: 9acf6dd6...
  - Redirect URI: http://localhost:3000
```

**❌ Configuración Incorrecta:**
```
❌ Missing required Azure AD environment variables: [...]
Please check your .env.local or .env.production file
```

### Verificar Backend

```bash
cd azure_advisor_reports

# Verificar variables de entorno
python -c "from decouple import config; print('Tenant ID:', config('AZURE_TENANT_ID'))"

# Debería imprimir:
# Tenant ID: 9acf6dd6-1978-4d9c-9a9c-c9be95245565
```

---

## 🏭 Configuración de Producción

### Paso 1: Obtener Valores de Azure Portal

1. **Ir a Azure Portal:** https://portal.azure.com
2. **Navegar a:** Azure Active Directory → App registrations
3. **Seleccionar:** Tu aplicación de producción
4. **Copiar valores:**
   - Application (client) ID → `REACT_APP_AZURE_CLIENT_ID`
   - Directory (tenant) ID → `REACT_APP_AZURE_TENANT_ID`

### Paso 2: Configurar .env.production

**Editar:** `frontend/.env.production`

```env
# ============================================
# Azure AD Configuration
# ============================================
REACT_APP_AZURE_CLIENT_ID=<tu-client-id-de-produccion>
REACT_APP_AZURE_TENANT_ID=<tu-tenant-id-de-produccion>
REACT_APP_AZURE_REDIRECT_URI=https://tu-dominio-produccion.com
REACT_APP_AZURE_POST_LOGOUT_REDIRECT_URI=https://tu-dominio-produccion.com
```

### Paso 3: Configurar Redirect URIs en Azure AD

1. En Azure Portal → App registration
2. Ir a "Authentication"
3. Agregar Platform → Single-page application
4. Agregar Redirect URIs:
   ```
   https://tu-dominio-produccion.com
   https://tu-dominio-produccion.com/
   ```
5. Configurar Logout URL:
   ```
   https://tu-dominio-produccion.com
   ```

### Paso 4: Build de Producción

```bash
cd frontend

# Build con variables de producción
npm run build:prod

# O si quieres usar .env.production.local para testing
cp .env.production .env.production.local
# Editar .env.production.local con valores reales
npm run build
```

---

## 📚 Archivos Modificados

### Frontend

1. **`package.json`**
   - ✅ Versión actualizada a `1.2.2`

2. **`src/config/authConfig.ts`**
   - ✅ Validación de variables de entorno
   - ✅ Logs de diagnóstico
   - ✅ Mensajes de error mejorados
   - ✅ TypeScript non-null assertions

3. **`public/clear-auth-cache.html`** (NUEVO)
   - ✅ Script de limpieza de cache
   - ✅ Interfaz visual amigable
   - ✅ Limpieza completa de MSAL

4. **`.env.production`**
   - ✅ Documentación mejorada
   - ✅ Instrucciones paso a paso
   - ✅ Ejemplos y warnings claros

### Backend

**No requiere cambios** - La configuración actual es correcta:
- `settings.py` - Correctamente configurado con variables de entorno
- `settings/production.py` - CORS y seguridad correctamente configurados
- `.env` - Valores correctos para desarrollo

---

## ⚠️ Problemas Comunes y Soluciones

### Error: "Missing required Azure AD environment variables"

**Solución:**
```bash
# Verificar que .env.local existe y tiene las variables
cd frontend
cat .env.local

# Si no existe, copiar de ejemplo
cp .env.example .env.local

# Editar con los valores correctos
nano .env.local  # o tu editor preferido
```

### Error: "redirect_uri_mismatch"

**Solución:**
1. Ir a Azure Portal → App registration → Authentication
2. Verificar que la Redirect URI coincide exactamente con tu .env:
   - Development: `http://localhost:3000`
   - Production: `https://tu-dominio.com`
3. Asegurarse de que el tipo es "Single-page application" (SPA)

### Error: Token inválido después de login

**Solución:**
```bash
# Backend - Verificar que los valores coinciden con el frontend
cd azure_advisor_reports
cat .env | grep AZURE

# Los valores de AZURE_CLIENT_ID y AZURE_TENANT_ID deben ser IDÉNTICOS
# a los del frontend
```

### Error: CORS en producción

**Solución:**
```env
# En .env del backend (producción)
CORS_ALLOWED_ORIGINS=https://tu-frontend.com,https://www.tu-frontend.com
CSRF_TRUSTED_ORIGINS=https://tu-frontend.com,https://www.tu-frontend.com

# NO usar trailing slash en las URLs
```

---

## 🧪 Testing

### Test de Autenticación Local

```bash
# 1. Iniciar backend
cd azure_advisor_reports
python manage.py runserver

# 2. Iniciar frontend
cd frontend
npm start

# 3. Abrir navegador en http://localhost:3000
# 4. Abrir DevTools (F12)
# 5. Verificar logs de configuración en Console
# 6. Click en "Sign In"
# 7. Verificar que redirige a Microsoft login
```

### Test de Cache Limpio

```bash
# 1. Navegar a: http://localhost:3000/clear-auth-cache.html
# 2. Verificar que detecta datos de cache
# 3. Click en "Clear All Authentication Cache"
# 4. Verificar que todo se marca como "Cleared"
# 5. Click en "Return to Application"
# 6. Verificar que el login funciona correctamente
```

---

## 📞 Soporte y Recursos

### Documentación Relacionada

- **MSAL.js Documentation:** https://github.com/AzureAD/microsoft-authentication-library-for-js
- **Azure AD Error Codes:** https://docs.microsoft.com/en-us/azure/active-directory/develop/reference-aadsts-error-codes
- **React Environment Variables:** https://create-react-app.dev/docs/adding-custom-environment-variables/

### Logs Útiles para Debug

```javascript
// En el navegador (DevTools Console)

// Ver todas las claves de localStorage
console.log('LocalStorage keys:', Object.keys(localStorage));

// Ver configuración de MSAL
console.log('MSAL config:', msalInstance.config);

// Ver accounts activas
console.log('Active accounts:', msalInstance.getAllAccounts());

// Ver cache de MSAL
console.log('MSAL cache:', localStorage.getItem('msal.account.keys'));
```

### Comandos de Diagnóstico

```bash
# Verificar versión de dependencias críticas
npm list @azure/msal-browser @azure/msal-react

# Verificar variables de entorno disponibles
npm run env | grep REACT_APP_AZURE

# Test de build de producción
npm run build:prod && npx serve -s build

# Analizar bundle size
npm run build:analyze
```

---

## ✨ Resumen de Mejoras

### Mejoras de Seguridad
- ✅ Validación automática de variables de entorno requeridas
- ✅ Logs sin exponer información sensible completa
- ✅ TypeScript strict mode para configuración
- ✅ Documentación de seguridad en .env.production

### Mejoras de UX
- ✅ Script visual de limpieza de cache
- ✅ Mensajes de error claros y accionables
- ✅ Logs informativos durante el proceso de autenticación
- ✅ Feedback visual del estado de la cache

### Mejoras de DevOps
- ✅ Versionado apropiado (1.2.2)
- ✅ Documentación completa en .env.production
- ✅ Scripts de diagnóstico y limpieza
- ✅ Guía completa de troubleshooting

---

## 🎯 Próximos Pasos

1. **Inmediato:**
   - [ ] Ejecutar limpieza de cache en tu navegador
   - [ ] Verificar logs de configuración en console
   - [ ] Probar login con usuario de prueba

2. **Pre-Producción:**
   - [ ] Obtener valores reales de Azure Portal
   - [ ] Actualizar .env.production con valores reales
   - [ ] Configurar Redirect URIs en Azure AD
   - [ ] Probar build de producción localmente

3. **Deployment:**
   - [ ] Configurar variables de entorno en Azure App Service
   - [ ] Verificar CORS y CSRF trusted origins
   - [ ] Probar autenticación en producción
   - [ ] Monitorear logs de Application Insights

---

## 📝 Changelog

### v1.2.2 (2025-10-30)

**Added:**
- Validación automática de variables de entorno en authConfig.ts
- Script de limpieza de cache (clear-auth-cache.html)
- Documentación mejorada en .env.production
- Logs de diagnóstico para troubleshooting

**Changed:**
- Versión del frontend: 0.1.0 → 1.2.2
- authConfig.ts: Agregado validación y logging
- .env.production: Agregadas instrucciones detalladas

**Fixed:**
- Problema de Tenant ID incorrecto desde cache
- Mensajes de error poco claros en autenticación
- Falta de validación de variables de entorno

---

**Última actualización:** 30 de Octubre, 2025
**Versión del documento:** 1.0
**Autor:** Azure Advisor Reports Team
