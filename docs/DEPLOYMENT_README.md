# Azure Advisor Reports Platform - Production Deployment Package v1.2.2

## Resumen

Este paquete contiene toda la documentación, scripts y configuraciones necesarias para desplegar la aplicación Azure Advisor Reports Platform a producción en Azure.

**Problema Resuelto:** Error de autenticación con Tenant ID incorrecto
**Tenant ID Correcto:** `9acf6dd6-1978-4d9c-9a9c-c9be95245565` (Solvex Dominicana)
**Versión:** 1.2.2
**Fecha:** 2025-10-30

---

## Estructura de Archivos de Deployment

```
D:\Code\Azure Reports\
├── PRODUCTION_DEPLOYMENT_GUIDE.md          # Guía completa y detallada
├── DEPLOYMENT_CHECKLIST.md                 # Checklist paso a paso
├── DEPLOYMENT_SUMMARY.md                   # Resumen ejecutivo
├── QUICK_DEPLOYMENT_COMMANDS.md           # Comandos rápidos
├── DEPLOYMENT_README.md                    # Este archivo
├── deploy-production.ps1                   # Script automatizado de deployment
├── verify-deployment-config.ps1           # Script de verificación
├── backend-appsettings.example.json       # Ejemplo de variables de entorno
│
├── frontend/
│   ├── Dockerfile.prod                    # Dockerfile para frontend
│   ├── .env.production                    # Variables de entorno del frontend
│   ├── nginx.conf                         # Configuración de Nginx
│   └── package.json                       # Version 1.2.2
│
└── azure_advisor_reports/
    ├── Dockerfile.prod                    # Dockerfile para backend
    ├── docker-entrypoint.sh              # Entrypoint script
    └── azure_advisor_reports/
        └── settings/
            └── production.py              # Settings de producción Django
```

---

## Flujo de Trabajo Recomendado

### 1. Preparación (Primera Vez)

1. Leer `DEPLOYMENT_SUMMARY.md` para entender el problema y la solución
2. Revisar `DEPLOYMENT_CHECKLIST.md` completo
3. Configurar Azure AD App Registration
4. Preparar recursos Azure (PostgreSQL, Redis, Storage, etc.)
5. Configurar variables de entorno

### 2. Pre-Deployment

1. Ejecutar script de verificación:
   ```powershell
   .\verify-deployment-config.ps1
   ```
2. Revisar output y corregir issues encontrados
3. Confirmar que todos los checks pasan

### 3. Deployment

**Opción A: Automatizado (Recomendado)**
```powershell
.\deploy-production.ps1 -RegistryName <name> -ResourceGroup <rg> ...
```

**Opción B: Manual**
- Seguir `QUICK_DEPLOYMENT_COMMANDS.md` para comandos específicos
- O seguir `PRODUCTION_DEPLOYMENT_GUIDE.md` para proceso detallado

### 4. Post-Deployment

1. Verificar health checks
2. Verificar Tenant ID en configuración
3. Probar autenticación end-to-end
4. Ejecutar functional tests
5. Monitorear logs por 2 horas

---

## Documentos por Rol

### DevOps Engineer

**Lectura Obligatoria:**
1. `DEPLOYMENT_SUMMARY.md` - Entender el contexto
2. `PRODUCTION_DEPLOYMENT_GUIDE.md` - Guía técnica completa
3. `DEPLOYMENT_CHECKLIST.md` - Para el día del deployment

**Scripts:**
- `deploy-production.ps1` - Automatización
- `verify-deployment-config.ps1` - Pre-deployment checks

**Referencia Rápida:**
- `QUICK_DEPLOYMENT_COMMANDS.md` - Comandos copy-paste

### Tech Lead / Project Manager

**Lectura Recomendada:**
1. `DEPLOYMENT_SUMMARY.md` - Resumen ejecutivo
2. `DEPLOYMENT_CHECKLIST.md` - Para tracking de progreso

**Para Revisión:**
- Security checklist en `DEPLOYMENT_CHECKLIST.md`
- Post-deployment tasks en `DEPLOYMENT_SUMMARY.md`

### Developer

**Lectura Recomendada:**
1. `DEPLOYMENT_SUMMARY.md` - Entender cambios
2. `QUICK_DEPLOYMENT_COMMANDS.md` - Para local testing

**Para Desarrollo:**
- `frontend/.env.production` - Variables del frontend
- `backend-appsettings.example.json` - Variables del backend

---

## Scripts Disponibles

### deploy-production.ps1

Script automatizado de PowerShell para build y deployment.

**Características:**
- Build de imágenes Docker en Azure Container Registry
- Deployment a Azure App Service
- Verificación de configuración
- Health checks
- Colorized output

**Uso Básico:**
```powershell
.\deploy-production.ps1 `
  -RegistryName yourregistry `
  -ResourceGroup your-rg `
  -Version 1.2.2 `
  -BackendAppName backend-app `
  -FrontendAppName frontend-app `
  -AzureClientId <client-id> `
  -BackendUrl https://backend.azurewebsites.net `
  -FrontendUrl https://frontend.azurewebsites.net
```

**Opciones:**
- `-BuildOnly` - Solo build, sin deployment
- `-SkipBackend` - Skip backend deployment
- `-SkipFrontend` - Skip frontend deployment

**Ver ayuda:**
```powershell
Get-Help .\deploy-production.ps1 -Detailed
```

### verify-deployment-config.ps1

Script de verificación pre-deployment.

**Características:**
- Verifica archivos locales
- Verifica Azure AD configuration
- Verifica Azure App Service settings
- Verifica conectividad
- Verifica Tenant ID en todas las configuraciones

**Uso:**
```powershell
.\verify-deployment-config.ps1 `
  -BackendAppName backend-app `
  -FrontendAppName frontend-app `
  -ResourceGroup your-rg
```

---

## Información Crítica

### Tenant ID

**IMPORTANTE:** El Tenant ID correcto es:
```
9acf6dd6-1978-4d9c-9a9c-c9be95245565
```

Este debe estar configurado en:
- [ ] Frontend: `REACT_APP_AZURE_TENANT_ID`
- [ ] Backend: `AZURE_TENANT_ID`
- [ ] Azure AD App Registration
- [ ] Build arguments del Docker frontend

### Variables de Entorno Requeridas

**Backend (Mínimas):**
```bash
AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>
SECRET_KEY=<generated-secret>
DEBUG=False
DJANGO_ENVIRONMENT=production
DATABASE_URL=<postgres-connection-string>
REDIS_URL=<redis-connection-string>
```

**Frontend (Build Args):**
```bash
REACT_APP_AZURE_TENANT_ID=9acf6dd6-1978-4d9c-9a9c-c9be95245565
REACT_APP_AZURE_CLIENT_ID=<your-client-id>
REACT_APP_AZURE_REDIRECT_URI=https://your-frontend.azurewebsites.net
REACT_APP_API_URL=https://your-backend.azurewebsites.net/api
REACT_APP_ENVIRONMENT=production
```

---

## Troubleshooting Rápido

### Error: Tenant Not Found

**Síntoma:** `AADSTS90002: Tenant 'xxx' not found`

**Solución Rápida:**
1. Verificar `AZURE_TENANT_ID` en backend App Service
2. Rebuild frontend con tenant ID correcto en build args
3. Limpiar cache del navegador
4. Ver sección completa en `PRODUCTION_DEPLOYMENT_GUIDE.md`

### Error: Cannot Connect to Database

**Solución Rápida:**
1. Verificar firewall rules en PostgreSQL
2. Verificar connection string
3. Verificar SSL mode configurado

### Error: Container Won't Start

**Solución Rápida:**
1. Ver logs: `az webapp log tail --name <app>`
2. Verificar todas las variables de entorno
3. Verificar imagen existe en registry

**Para más troubleshooting, ver:**
- `PRODUCTION_DEPLOYMENT_GUIDE.md` - Sección Troubleshooting
- `DEPLOYMENT_SUMMARY.md` - Common Issues

---

## Security Considerations

### Secretos

- **NUNCA** commitear secretos al repositorio
- Usar Azure Key Vault para producción
- Rotar secretos cada 90 días
- Client Secret expira en 24 meses

### Network Security

- Usar HTTPS siempre en producción
- Configurar CORS apropiadamente
- Habilitar firewall rules en Azure services
- Usar Private Endpoints cuando sea posible

### Access Control

- Usar Managed Identities
- Principle of least privilege
- Revisar accesos regularmente

---

## Monitoring y Alertas

### Health Checks

```powershell
# Backend
curl https://your-backend.azurewebsites.net/api/health/

# Frontend
curl https://your-frontend.azurewebsites.net/health
```

### Application Insights

Queries útiles documentadas en `DEPLOYMENT_SUMMARY.md`:
- Errores de autenticación
- Performance metrics
- Exception tracking

### Alertas Recomendadas

1. Authentication failures
2. High response time
3. Error rate
4. CPU/Memory usage
5. Availability

Configuración detallada en `PRODUCTION_DEPLOYMENT_GUIDE.md`.

---

## Rollback Procedure

Si hay problemas críticos:

```powershell
# Backend
az webapp config container set \
  --name your-backend \
  --resource-group your-rg \
  --docker-custom-image-name registry.azurecr.io/azure-advisor-backend:1.2.1

# Frontend
az webapp config container set \
  --name your-frontend \
  --resource-group your-rg \
  --docker-custom-image-name registry.azurecr.io/azure-advisor-frontend:1.2.1

# Restart
az webapp restart --name your-backend --resource-group your-rg
az webapp restart --name your-frontend --resource-group your-rg
```

**Rollback completo documentado en:** `DEPLOYMENT_SUMMARY.md`

---

## Post-Deployment Checklist

Después del deployment exitoso:

### Inmediato
- [ ] Health checks pasan
- [ ] Authentication funciona
- [ ] Logs sin errores
- [ ] Metrics normales

### Día 1
- [ ] Monitorear logs por 2 horas
- [ ] Ejecutar smoke tests
- [ ] Notificar stakeholders
- [ ] Documentar issues

### Semana 1
- [ ] Revisar logs diariamente
- [ ] Monitorear costos
- [ ] Recolectar feedback
- [ ] Ajustar alertas

### Mes 1
- [ ] Optimizar costos
- [ ] Analizar performance
- [ ] Programar rotación de secretos
- [ ] Review lessons learned

---

## Support y Contactos

### Documentation

- **Este Paquete:** Todos los archivos DEPLOYMENT_*.md
- **Azure Docs:** https://docs.microsoft.com/azure/
- **Django Docs:** https://docs.djangoproject.com/
- **React Docs:** https://react.dev/

### Technical Support

- **Team Email:** [Agregar]
- **Team Slack:** [Agregar]
- **On-Call:** [Agregar]

### Azure Support

- **Portal:** https://portal.azure.com > Help + support
- **Phone:** [Agregar número]

---

## FAQs

### ¿Necesito todo esto para un simple deployment?

Para el primer deployment a producción con el fix del Tenant ID, sí. Después del primer deployment exitoso, puede usar solo `QUICK_DEPLOYMENT_COMMANDS.md`.

### ¿Puedo hacer deployment sin los scripts de PowerShell?

Sí, puede hacer deployment manual usando los comandos en `QUICK_DEPLOYMENT_COMMANDS.md` o siguiendo `PRODUCTION_DEPLOYMENT_GUIDE.md`.

### ¿Qué pasa si ya hay una versión en producción?

El script y la guía incluyen procedimientos de rollback. Siempre puede volver a la versión anterior si hay problemas.

### ¿Cómo sé que el Tenant ID está configurado correctamente?

Use el script `verify-deployment-config.ps1` que verifica todas las configuraciones incluyendo el Tenant ID.

### ¿Necesito crear nuevos recursos Azure?

Si es el primer deployment, sí. Si ya existen los recursos, solo necesita actualizar las imágenes y configuración.

---

## Version History

### v1.2.2 (2025-10-30)

**Fixed:**
- Tenant ID configuration (corrected to 9acf6dd6-1978-4d9c-9a9c-c9be95245565)
- Azure AD authentication flow
- Docker build arguments

**Added:**
- Comprehensive deployment documentation
- Automated deployment scripts
- Configuration verification scripts
- Deployment checklists

**Improved:**
- Security practices documentation
- Monitoring setup
- Troubleshooting guides

---

## Next Steps

1. **LEER** `DEPLOYMENT_SUMMARY.md` primero
2. **REVISAR** `DEPLOYMENT_CHECKLIST.md` completo
3. **EJECUTAR** `verify-deployment-config.ps1`
4. **SEGUIR** el proceso de deployment apropiado
5. **MONITOREAR** después del deployment

---

## License

[Agregar información de licencia si aplica]

---

## Maintainers

- DevOps Team
- [Agregar nombres/contactos]

---

**Última Actualización:** 2025-10-30
**Versión del Documento:** 1.0
**Versión de la Aplicación:** 1.2.2
**Tenant ID:** 9acf6dd6-1978-4d9c-9a9c-c9be95245565 (Solvex Dominicana)
