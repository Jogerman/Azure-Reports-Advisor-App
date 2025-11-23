# Instrucciones de Deployment - Enhanced Reservations v2.0

**Fecha:** 21 de Noviembre, 2025
**Commit:** 1abb6d5
**Features:** Enhanced Reservation Analysis + Number Formatting

---

## 📋 Resumen de Cambios

Este deployment incluye:

### 1. **Enhanced Reservation & Saving Plans Analysis v2.0**
- Análisis granular de reservas por término (1 año vs 3 años)
- Separación de Savings Plans y Reservas tradicionales
- 4 nuevas tablas en reportes de costo
- 2 migraciones de base de datos
- Mejoras en categorización automática

### 2. **Number Formatting Improvements**
- Formato de números con comas en todos los templates
- Mejor legibilidad de cifras grandes

---

## 🔧 Pre-requisitos

- [ ] Acceso a Azure Container Registry
- [ ] Acceso a Azure Container Apps (rg-azure-advisor-app)
- [ ] Docker con soporte para buildx
- [ ] Azure CLI instalado y autenticado
- [ ] Backup de base de datos (recomendado)

---

## 📝 Proceso de Deployment

### Paso 1: Aplicar Migraciones en Producción ⚠️

**IMPORTANTE:** Las migraciones deben aplicarse ANTES de deployar el nuevo código.

#### Opción A: Usando Azure Container Apps Console (Recomendado)

```bash
# 1. Conectarse al contenedor backend en ejecución
az containerapp exec \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --command /bin/bash

# 2. Dentro del contenedor, aplicar migraciones
cd /app
python manage.py migrate reports 0008
python manage.py migrate reports 0009

# 3. Verificar que se aplicaron correctamente
python manage.py showmigrations reports

# 4. Salir del contenedor
exit
```

#### Opción B: Usando Temp Container Job

```bash
# Crear un job temporal para ejecutar migraciones
az containerapp job create \
  --name migration-job-$(date +%s) \
  --resource-group rg-azure-advisor-app \
  --environment advisor-reports-env \
  --trigger-type Manual \
  --replica-timeout 300 \
  --image advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:latest \
  --cpu 0.5 \
  --memory 1Gi \
  --command "/bin/sh" \
  --args "-c,python manage.py migrate reports 0008 && python manage.py migrate reports 0009"

# Ejecutar el job
az containerapp job start --name migration-job-xxxxx --resource-group rg-azure-advisor-app

# Limpiar después
az containerapp job delete --name migration-job-xxxxx --resource-group rg-azure-advisor-app --yes
```

### Paso 2: Login a Azure Container Registry

```bash
az acr login --name advisorreportsacr
```

### Paso 3: Rebuild Backend con Nuevos Cambios

```bash
# Asegurarse de estar en el directorio correcto
cd /Users/josegomez/Documents/Code/Azure-Reports-Advisor-App

# Build para linux/amd64 (Azure requirement)
cd azure_advisor_reports
docker buildx build --platform linux/amd64 \
  -t advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:2.0.12 \
  -t advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:latest \
  -f Dockerfile . --push

cd ..
```

**Nota:** Usamos 2.0.12 como nueva versión para diferenciar de la anterior.

### Paso 4: Update de Servicios en Azure

```bash
# 1. Update Backend
az containerapp update \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:2.0.12

# 2. Update Celery Worker
az containerapp update \
  --name advisor-reports-worker \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:2.0.12

# 3. Update Celery Beat
az containerapp update \
  --name advisor-reports-beat \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:2.0.12
```

### Paso 5: Verificación Post-Deployment

```bash
# 1. Verificar estado de todos los servicios
az containerapp list \
  --resource-group rg-azure-advisor-app \
  --query "[].{Name:name, Status:properties.runningStatus, Revision:properties.latestRevisionName}" \
  -o table

# 2. Ver logs del backend para detectar errores
az containerapp logs show \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --follow

# 3. Verificar que las migraciones se aplicaron
# (Conectarse al contenedor y ejecutar)
az containerapp exec \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --command "python manage.py showmigrations reports"
```

---

## 🧪 Testing Post-Deployment

### 1. Verificar Migraciones en Base de Datos

```bash
# Conectarse al contenedor backend
az containerapp exec \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --command /bin/bash

# Verificar que los campos existen
python manage.py shell

>>> from apps.reports.models import Recommendation
>>> first_rec = Recommendation.objects.first()
>>> print(first_rec.is_savings_plan)
>>> print(first_rec.commitment_category)
>>> exit()
```

### 2. Test con CSV Upload

1. Acceder a la aplicación: https://advisor-reports-frontend.nicefield-788f351e.eastus.azurecontainerapps.io
2. Login con credenciales de administrador
3. Subir un CSV con recomendaciones de costo
4. Generar un reporte de "Cost Optimization"
5. Verificar que aparezcan las 4 nuevas secciones:
   - Pure Reservations - 3 Year
   - Pure Reservations - 1 Year
   - Combined: Savings Plans + 3 Year
   - Combined: Savings Plans + 1 Year

### 3. Verificar Números Formateados

1. Abrir cualquier reporte generado
2. Verificar que los números grandes muestren comas (ej: 1,234,567)
3. Confirmar que los ahorros se muestren correctamente formateados

---

## 🔄 Rollback Plan (Si es necesario)

Si algo sale mal durante el deployment:

### Opción 1: Rollback de Código (Rápido)

```bash
# Volver a la versión anterior de imágenes
az containerapp update \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:2.0.11

az containerapp update \
  --name advisor-reports-worker \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:2.0.11

az containerapp update \
  --name advisor-reports-beat \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr-afc0cmayd8hcekaf.azurecr.io/azure-advisor-backend:2.0.11
```

**NOTA:** Las migraciones ya aplicadas NO se revertirán, pero el código antiguo es compatible con los nuevos campos (tienen defaults).

### Opción 2: Rollback de Migraciones (Si hay problemas graves)

```bash
# Conectarse al contenedor
az containerapp exec \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --command /bin/bash

# Revertir migraciones
python manage.py migrate reports 0007

# Esto eliminará los campos is_savings_plan y commitment_category
# ADVERTENCIA: Se perderá la data de categorización
```

---

## 📊 Monitoring Post-Deployment

### Métricas a Monitorear

1. **Application Insights:**
   - Errores 500 (should be 0)
   - Response times (should be < 2s)
   - Failed requests (should be minimal)

2. **Container Apps:**
   - CPU usage (should be < 70%)
   - Memory usage (should be < 80%)
   - Restart count (should be 0)

3. **Database:**
   - Query performance (new queries should be < 0.2s)
   - Connection pool usage

### Comandos de Monitoring

```bash
# Ver métricas de backend
az monitor metrics list \
  --resource /subscriptions/92d1d794-a351-42d0-8b66-3dedb3cd3c84/resourceGroups/rg-azure-advisor-app/providers/Microsoft.App/containerApps/advisor-reports-backend \
  --metric "Requests" "CpuUsage" "MemoryWorkingSetBytes" \
  --start-time $(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%SZ') \
  --interval PT1M

# Ver logs de errores
az containerapp logs show \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --type console \
  --follow
```

---

## ✅ Post-Deployment Checklist

- [ ] Migraciones aplicadas exitosamente (0008 y 0009)
- [ ] Backend v2.0.12 desplegado y running
- [ ] Celery Worker v2.0.12 desplegado y running
- [ ] Celery Beat v2.0.12 desplegado y running
- [ ] No hay errores en logs de backend
- [ ] Test de upload CSV exitoso
- [ ] Nuevo reporte genera las 4 tablas de reservations
- [ ] Números formateados correctamente con comas
- [ ] Métricas de performance dentro de rangos normales
- [ ] No hay alerts en Application Insights
- [ ] Comunicar a usuarios sobre nueva funcionalidad

---

## 📞 Support & Troubleshooting

### Problemas Comunes

#### Problema: Migraciones fallan con error de permisos
**Solución:** Verificar que el usuario de BD tiene permisos ALTER TABLE

#### Problema: Tablas no aparecen en reportes
**Solución:**
1. Verificar que las migraciones se aplicaron
2. Limpiar caché de Django
3. Regenerar el reporte con CSV nuevo

#### Problema: Errores de "Field does not exist"
**Solución:**
1. Confirmar que migraciones están aplicadas: `python manage.py showmigrations reports`
2. Verificar que el código deployed incluye los cambios en models.py

### Contactos

- **Developer Lead:** jose.gomez@solvex.com.do
- **DevOps:** [Your DevOps contact]
- **Database Admin:** [Your DBA contact]

---

## 📚 Documentación Adicional

- **Architecture:** `RESERVATION_SAVING_PLANS_ARCHITECTURE.md`
- **Implementation:** `ENHANCED_RESERVATIONS_IMPLEMENTATION_SUMMARY.md`
- **Validation Script:** `validate_enhanced_reservations.py`

---

## 🎯 Expected Outcomes

After successful deployment:

✅ Users can see detailed breakdown of 3Y vs 1Y reservations
✅ Savings Plans are analyzed separately from traditional reservations
✅ Combined analysis shows strategic commitment opportunities
✅ All numbers display with thousand separators for better readability
✅ Reports load in < 2 seconds
✅ No breaking changes to existing functionality

---

**Deployment Prepared By:** Claude Code
**Reviewed By:** [Your Name]
**Approved By:** [Approval Signature]
**Date:** 2025-11-21
