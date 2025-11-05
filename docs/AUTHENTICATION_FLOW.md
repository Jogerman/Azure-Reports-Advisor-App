# Flujo de Autenticación - Azure Advisor Reports Platform
## Arquitectura y Diagnóstico v1.2.2

---

## 🔐 Arquitectura de Autenticación

### Componentes Principales

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│                 │      │                  │      │                 │
│  React Frontend │◄────►│  Azure AD (MSAL) │◄────►│  Microsoft      │
│  (Port 3000)    │      │  Authentication  │      │  Login          │
│                 │      │                  │      │  (oauth2)       │
└────────┬────────┘      └──────────────────┘      └─────────────────┘
         │
         │ JWT Token
         │
         ▼
┌─────────────────┐
│  Django Backend │
│  (Port 8000)    │
│                 │
│  - Validate     │
│  - Create User  │
│  - Issue JWT    │
└─────────────────┘
```

---

## 🔄 Flujo de Login Completo

### Paso 1: Usuario hace click en "Sign In"

```
Frontend (AuthContext.tsx)
│
├─► login() llamado
│   │
│   ├─► msalInstance.loginRedirect(loginRequest)
│   │
│   └─► Redirige a Microsoft Login
```

### Paso 2: Microsoft Authentication

```
Usuario → Microsoft Login Page
│
├─► Introduce credenciales
│
├─► Microsoft valida usuario
│
├─► Microsoft genera tokens:
│   ├─► Access Token
│   ├─► ID Token
│   └─► Refresh Token
│
└─► Redirige de vuelta a la app
    con tokens en URL params
```

### Paso 3: Frontend maneja respuesta

```
Frontend (AuthContext.tsx)
│
├─► msalInstance.handleRedirectPromise()
│   │
│   ├─► Extrae tokens de URL
│   │
│   ├─► Guarda en localStorage:
│   │   ├─► msal.token.keys.*
│   │   ├─► msal.account.keys
│   │   └─► msal.token.binding.key
│   │
│   └─► setActiveAccount(response.account)
│
└─► loadUserProfile(account, azureToken)
```

### Paso 4: Backend Authentication

```
Frontend
│
└─► authService.login(azureToken)
    │
    POST /api/v1/auth/login/
    Body: { "access_token": "<azure_token>" }
    │
    ▼
Backend (views.py: AzureADLoginView)
│
├─► AzureADService.validate_token(azure_token)
│   │
│   ├─► Llama a Microsoft Graph API
│   │   GET https://graph.microsoft.com/v1.0/me
│   │   Headers: Authorization: Bearer <azure_token>
│   │
│   └─► Obtiene user info:
│       ├─► email
│       ├─► displayName
│       ├─► givenName
│       └─► surname
│
├─► create_or_update_user(azure_user_info)
│   │
│   ├─► Busca usuario por email
│   ├─► Si no existe: CREATE
│   └─► Si existe: UPDATE
│
├─► JWTService.generate_token(user)
│   │
│   └─► Genera JWT tokens:
│       ├─► access_token (1 hora)
│       └─► refresh_token (7 días)
│
└─► Response:
    {
      "access_token": "<jwt_token>",
      "refresh_token": "<refresh_token>",
      "expires_in": 3600,
      "token_type": "Bearer",
      "user": { ... }
    }
```

### Paso 5: Frontend guarda tokens

```
Frontend (AuthContext.tsx)
│
├─► localStorage.setItem('access_token', backendResponse.access_token)
├─► localStorage.setItem('refresh_token', backendResponse.refresh_token)
│
├─► setUser(userData)
├─► setIsAuthenticated(true)
│
└─► Usuario logueado exitosamente ✓
```

---

## 🔍 Dónde Puede Fallar (Troubleshooting)

### Error 1: "Tenant not found"

```
PROBLEMA:
┌──────────────────────────────┐
│ localStorage                 │
│                              │
│ msal.authority =             │
│   "https://login.microsoft   │
│    online.com/06bf3e54..."   │  ← ¡Tenant ID INCORRECTO!
│                              │     (del cache antiguo)
│ Pero en .env.local:          │
│   TENANT_ID = 9acf6dd6...    │  ← Tenant ID CORRECTO
└──────────────────────────────┘

SOLUCIÓN:
Limpiar localStorage → Eliminar cache antiguo
```

**Dónde ocurre:**
```
Frontend → MSAL → Microsoft Login
                    │
                    ▼
                  ❌ AADSTS90002: Tenant '06bf3e54...' not found
                    (usando valor del cache en lugar de .env)
```

### Error 2: "Invalid token"

```
PROBLEMA:
Frontend                    Backend
  ↓                           ↓
CLIENT_ID: a6401ee1...    CLIENT_ID: DIFERENTE ❌
TENANT_ID: 9acf6dd6...    TENANT_ID: DIFERENTE ❌

SOLUCIÓN:
Asegurar que ambos archivos .env tienen los MISMOS valores
```

### Error 3: "redirect_uri_mismatch"

```
PROBLEMA:
Azure AD Config              Frontend .env
  ↓                            ↓
Redirect URI:              REDIRECT_URI:
http://localhost:3000      http://localhost:3000/ ❌
                           (con trailing slash)

SOLUCIÓN:
Las URIs deben coincidir EXACTAMENTE (sin vs con slash final)
```

### Error 4: "CORS error"

```
PROBLEMA:
Frontend (localhost:3000)
  ↓
  POST /api/v1/auth/login/
  ↓
Backend (localhost:8000)
  ↓
  ❌ CORS origin not allowed

SOLUCIÓN:
Backend .env:
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## 🗂️ Configuración de Variables de Entorno

### Frontend (.env.local)

```env
# Azure AD - FRONTEND
REACT_APP_AZURE_CLIENT_ID=a6401ee1-0c80-439a-9ca7-e1069fa770ba
REACT_APP_AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565
REACT_APP_AZURE_REDIRECT_URI=http://localhost:3000

# API Backend
REACT_APP_API_URL=http://localhost:8000/api/v1
```

### Backend (.env)

```env
# Azure AD - BACKEND
AZURE_CLIENT_ID=a6401ee1-0c80-439a-9ca7-e1069fa770ba
AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565
AZURE_CLIENT_SECRET=your-client-secret-here

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**⚠️ IMPORTANTE:** Los valores de `CLIENT_ID` y `TENANT_ID` deben ser **IDÉNTICOS** en ambos archivos.

---

## 💾 LocalStorage Structure (MSAL)

### Después de login exitoso:

```javascript
localStorage = {
  // MSAL Token Cache
  "msal.token.keys.06bf3e54-...": "...",           // ← ¡PUEDE SER ANTIGUO!
  "msal.account.keys": "...",
  "msal.token.binding.key": "...",

  // JWT Tokens del Backend
  "access_token": "eyJhbGciOiJIUzI1NiIs...",      // JWT del backend (1h)
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",     // Refresh token (7d)

  // Otros datos
  "theme": "light",
  "language": "en"
}
```

### Lo que limpia `clear-auth-cache.html`:

```javascript
// Busca y elimina:
- msal.*                     // Todos los datos de MSAL
- access_token              // JWT del backend
- refresh_token             // Refresh token
- *azure*                   // Cualquier dato relacionado con Azure

// También limpia:
- sessionStorage
- Cookies de MSAL
- Service Workers
- Cache API
```

---

## 🔄 Token Refresh Flow

### Cuando el JWT expira (1 hora):

```
Frontend
│
├─► API call falla con 401
│   │
│   └─► Interceptor detecta error
│
├─► Intenta refresh:
│   │
│   POST /api/v1/auth/refresh/
│   Body: { "refresh_token": "<refresh_token>" }
│   │
│   ├─► Backend valida refresh token
│   │
│   └─► Responde con nuevo access_token
│
├─► Guarda nuevo access_token en localStorage
│
└─► Reintenta la API call original
```

### Si refresh token también expiró:

```
Frontend
│
├─► Refresh falla con 401
│   │
│   ├─► localStorage.removeItem('access_token')
│   ├─► localStorage.removeItem('refresh_token')
│   │
│   ├─► setIsAuthenticated(false)
│   ├─► setUser(null)
│   │
│   └─► Redirige a login page
│
└─► Usuario debe hacer login nuevamente
```

---

## 🛠️ Herramientas de Diagnóstico

### 1. Browser DevTools Console

```javascript
// Ver configuración de MSAL
console.log('MSAL Config:', msalInstance.config);

// Ver authority (debe mostrar Tenant ID correcto)
console.log('Authority:', msalInstance.config.auth.authority);
// Esperado: "https://login.microsoftonline.com/9acf6dd6-1978-4d9c-9a9c-c9be95245565"

// Ver accounts activas
console.log('Accounts:', msalInstance.getAllAccounts());

// Ver tokens en localStorage
Object.keys(localStorage).filter(k => k.includes('msal')).forEach(key => {
  console.log(key, localStorage.getItem(key));
});

// Ver variables de entorno (solo en development)
console.log('Env vars:', {
  CLIENT_ID: process.env.REACT_APP_AZURE_CLIENT_ID,
  TENANT_ID: process.env.REACT_APP_AZURE_TENANT_ID,
  REDIRECT_URI: process.env.REACT_APP_AZURE_REDIRECT_URI
});
```

### 2. Network Tab (DevTools)

**Verificar llamadas correctas:**

```
✅ Correcto:
POST http://localhost:8000/api/v1/auth/login/
Status: 200 OK
Response: { "access_token": "...", "user": {...} }

❌ Error:
POST http://localhost:8000/api/v1/auth/login/
Status: 401 Unauthorized
Response: { "error": "Invalid Azure AD token" }
```

### 3. Application Tab (DevTools)

**Verificar localStorage:**

```
Application → Storage → Local Storage → http://localhost:3000

Keys to check:
✅ access_token         (JWT del backend)
✅ refresh_token        (Refresh token)
⚠️ msal.token.keys.*    (deben tener Tenant ID correcto)
```

---

## 📊 Estados de Autenticación

```
┌─────────────────────────────────────────────────────────┐
│                  Estado: NO AUTENTICADO                 │
│                                                         │
│  isAuthenticated: false                                 │
│  user: null                                             │
│  localStorage: vacío                                    │
│                                                         │
│  UI: Muestra login button                              │
└─────────────────────────────────────────────────────────┘
                            │
                            │ Usuario click "Sign In"
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Estado: LOADING                       │
│                                                         │
│  isLoading: true                                        │
│  UI: Muestra spinner                                    │
│                                                         │
│  Proceso: Redirigiendo a Microsoft...                  │
└─────────────────────────────────────────────────────────┘
                            │
                            │ Usuario autentica en MS
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Estado: PROCESSING TOKENS                  │
│                                                         │
│  isLoading: true                                        │
│                                                         │
│  Proceso:                                               │
│  1. Recibir tokens de Azure AD                         │
│  2. Validar con backend                                 │
│  3. Obtener JWT                                         │
│  4. Guardar en localStorage                             │
└─────────────────────────────────────────────────────────┘
                            │
                            │ Autenticación exitosa
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  Estado: AUTENTICADO                    │
│                                                         │
│  isAuthenticated: true                                  │
│  user: { id, email, name, role }                       │
│  localStorage:                                          │
│    - access_token: "eyJ..."                            │
│    - refresh_token: "eyJ..."                           │
│    - msal.*: {...}                                     │
│                                                         │
│  UI: Muestra app con user menu                         │
└─────────────────────────────────────────────────────────┘
                            │
                            │ Token expira (1h)
                            ▼
┌─────────────────────────────────────────────────────────┐
│               Estado: REFRESHING TOKEN                  │
│                                                         │
│  isAuthenticated: true (mantiene estado)                │
│                                                         │
│  Proceso: Renovar access_token usando refresh_token    │
└─────────────────────────────────────────────────────────┘
                            │
                            │ Refresh exitoso
                            ▼
                   [AUTENTICADO] (continúa)
                            │
                            │ Refresh falla o usuario logout
                            ▼
              [NO AUTENTICADO] (vuelta al inicio)
```

---

## 🧪 Testing del Flujo

### Test 1: Login Fresh (Sin Cache)

```bash
# 1. Limpiar cache completamente
http://localhost:3000/clear-auth-cache.html

# 2. Verificar localStorage vacío
# DevTools Console:
Object.keys(localStorage).length  // Debería ser 0 o muy bajo

# 3. Iniciar login
# Click en "Sign In"

# 4. Verificar en Console:
✅ Azure AD Configuration initialized:
  - Client ID: a6401ee1...
  - Tenant ID: 9acf6dd6...

# 5. Completar login en Microsoft

# 6. Verificar en Console:
✅ User <email> successfully logged in via Azure AD

# 7. Verificar localStorage:
# Debe tener:
- access_token
- refresh_token
- msal.token.keys.* (con Tenant ID correcto)
```

### Test 2: Login con Cache Válido

```bash
# 1. Ya logueado previamente
# localStorage tiene tokens válidos

# 2. Cerrar navegador

# 3. Reabrir app en http://localhost:3000

# 4. Verificar:
# App debe cargar automáticamente con usuario logueado
# NO debe redirigir a Microsoft login
# UI debe mostrar user menu
```

### Test 3: Login con Cache Inválido (El Problema)

```bash
# Simular el problema:
# 1. Editar localStorage manualmente en DevTools:
localStorage.setItem('msal.token.keys.06bf3e54-7223-498a-a4db-2f4e68d7e38d', '...')

# 2. Intentar login

# 3. Resultado:
❌ AADSTS90002: Tenant '06bf3e54-7223-498a-a4db-2f4e68d7e38d' not found

# 4. Solución:
# Usar clear-auth-cache.html para limpiar
```

---

## 🎯 Checklist de Verificación

### Configuración

- [ ] `.env.local` existe con todos los valores
- [ ] CLIENT_ID es idéntico en frontend y backend
- [ ] TENANT_ID es idéntico en frontend y backend
- [ ] REDIRECT_URI coincide con Azure AD config
- [ ] Backend CORS incluye frontend URL

### Logs Esperados

- [ ] `✅ Azure AD Configuration initialized:` visible en console
- [ ] CLIENT_ID y TENANT_ID ofuscados coinciden con esperados
- [ ] No hay errores de "Missing required..." en console

### localStorage

- [ ] No hay keys con Tenant ID incorrecto `06bf3e54...`
- [ ] `msal.*` keys existen después de login
- [ ] `access_token` y `refresh_token` existen
- [ ] Tokens son strings largos (JWT válidos)

### Network

- [ ] POST `/api/v1/auth/login/` responde 200 OK
- [ ] Response tiene `access_token`, `refresh_token`, `user`
- [ ] No hay errores CORS en console
- [ ] Headers incluyen `Content-Type: application/json`

---

## 📚 Referencias

### Archivos del Proyecto

- `frontend/src/config/authConfig.ts` - Configuración MSAL
- `frontend/src/context/AuthContext.tsx` - Lógica de autenticación
- `frontend/src/services/authService.ts` - API calls
- `azure_advisor_reports/apps/authentication/views.py` - Backend auth
- `azure_advisor_reports/apps/authentication/services.py` - Azure AD service

### Documentación

- `AUTHENTICATION_FIX_GUIDE.md` - Guía completa de solución
- `QUICK_FIX.md` - Solución rápida
- `AUTHENTICATION_FIX_SUMMARY.md` - Resumen de correcciones

### Herramientas

- `fix-authentication.ps1` - Script Windows
- `fix-authentication.sh` - Script Linux/Mac
- `frontend/public/clear-auth-cache.html` - Limpieza visual de cache

---

**Última actualización:** 30 de Octubre, 2025
**Versión:** 1.2.2
**Estado:** Documentado y Verificado
