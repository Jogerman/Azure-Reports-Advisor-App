# Solución Rápida - Error de Autenticación

## Problema: `AADSTS90002: Tenant not found`

### Causa
El Tenant ID `06bf3e54-7223-498a-a4db-2f4e68d7e38d` está guardado en el cache del navegador pero NO existe en tu configuración actual.

---

## ⚡ Solución Rápida (5 minutos)

### Opción 1: Script Automático (RECOMENDADO)

**Windows (PowerShell):**
```powershell
.\fix-authentication.ps1
```

**Linux/Mac:**
```bash
chmod +x fix-authentication.sh
./fix-authentication.sh
```

El script automáticamente:
- ✅ Verifica las variables de entorno
- ✅ Limpia cache de npm y build
- ✅ Reinstala dependencias (opcional)
- ✅ Valida la configuración

### Opción 2: Manual (Navegador)

1. **Abrir en tu navegador:**
   ```
   http://localhost:3000/clear-auth-cache.html
   ```

2. **Click en:** "Clear All Authentication Cache"

3. **Esperar** confirmación de limpieza exitosa

4. **Regresar** a la aplicación y volver a hacer login

### Opción 3: DevTools Manual

1. Abrir **DevTools** (F12)
2. Ir a **Application** → **Storage**
3. Click en **"Clear site data"**
4. Seleccionar todo y click en **"Clear data"**
5. Cerrar y reabrir el navegador

---

## 🔍 Verificación

Después de aplicar la solución, abre DevTools (F12) Console y deberías ver:

```
✅ Azure AD Configuration initialized:
  - Client ID: a6401ee1...
  - Tenant ID: 9acf6dd6...
  - Redirect URI: http://localhost:3000
```

---

## 📋 Valores Correctos

### Development (.env.local)
```env
REACT_APP_AZURE_CLIENT_ID=a6401ee1-0c80-439a-9ca7-e1069fa770ba
REACT_APP_AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565
REACT_APP_AZURE_REDIRECT_URI=http://localhost:3000
```

---

## ❌ Si Aún No Funciona

1. **Limpiar completamente y rebuild:**
   ```bash
   cd frontend
   rm -rf node_modules build
   npm cache clean --force
   npm install
   npm start
   ```

2. **Verificar variables:**
   ```bash
   cat frontend/.env.local | grep AZURE
   ```

3. **Ver documentación completa:**
   - `AUTHENTICATION_FIX_GUIDE.md` - Guía detallada
   - Incluye troubleshooting avanzado
   - Instrucciones de producción

---

## 🚀 Iniciar Aplicación

```bash
# Terminal 1 - Backend
cd azure_advisor_reports
python manage.py runserver

# Terminal 2 - Frontend
cd frontend
npm start
```

Luego abrir: http://localhost:3000

---

**Última actualización:** 30 de Octubre, 2025
**Versión:** 1.2.2
