# Guía de Deploy: Mejoras de Render de PDF

## 🚀 Deployment a Azure Container Apps

### Paso 1: Verificar cambios localmente (Opcional)

```bash
# Test local (si tienes Playwright instalado)
python test_pdf_render_timing.py
```

### Paso 2: Commit y push de cambios

```bash
git add azure_advisor_reports/apps/reports/services/pdf_service.py
git add PDF_RENDER_IMPROVEMENTS.md
git add DEPLOY_RENDER_IMPROVEMENTS.md
git add test_pdf_render_timing.py

git commit -m "feat: Improve PDF render timing to eliminate blank spaces

- Increase DEFAULT_TIMEOUT from 30s to 60s
- Increase CHART_TIMEOUT from 10s to 15s
- Add _wait_for_images() method to ensure all images load
- Add _wait_for_elements_visible() to verify element dimensions
- Improve Chart.js detection with more iterations (150 vs 100)
- Add comprehensive logging for each wait step
- Total render time now ~27-42s (was ~18s)

This fixes blank spaces in PDFs caused by incomplete rendering."

git push origin main
```

### Paso 3: Deploy automático
El GitHub Actions workflow debería detectar el push y hacer deploy automáticamente.

### Paso 4: Verificar deploy en Azure

```bash
# Ver logs del contenedor
az containerapp logs show \
  --name azure-advisor-reports \
  --resource-group AzureAdvisorReportsPlatform-rg \
  --follow

# O verificar revisión actual
az containerapp revision list \
  --name azure-advisor-reports \
  --resource-group AzureAdvisorReportsPlatform-rg \
  --output table
```

### Paso 5: Trigger test en producción

```bash
# Opción 1: Usar el script de trigger
python trigger_report_generation.py

# Opción 2: Desde Azure Portal
# Ve a Container Apps → Jobs → Run job manually
```

### Paso 6: Monitorear generación

```bash
# Verificar estado del job
python check_reports.py

# Ver logs específicos de PDF generation
az containerapp logs show \
  --name azure-advisor-reports \
  --resource-group AzureAdvisorReportsPlatform-rg \
  --follow | grep -E "PDF|Playwright|Chart|wait|timeout"
```

## 📊 Qué buscar en los Logs

### ✅ Logs Esperados (Good)

```
INFO - HTML content loaded into browser
INFO - Network idle state reached
INFO - DOM load complete
INFO - Fonts loaded successfully
INFO - Waited for lazy-loaded content
INFO - Waiting for Chart.js charts to render...
INFO - Found X canvas elements, waiting for Chart.js rendering...
INFO - All X charts rendered successfully after XXXms
INFO - Waiting for images to load...
INFO - All images loaded successfully
INFO - Waiting for all elements to be visible...
INFO - All elements are visible
INFO - Final wait complete - all content should be rendered
INFO - All animations complete, proceeding with PDF generation
INFO - PDF generated successfully: /path/to/file.pdf
```

### ⚠️ Warnings Esperados (Normal)

```
WARNING - Network idle timeout - continuing anyway
WARNING - Image loading timeout after 5s (X/Y loaded)
WARNING - Element visibility check timeout after XXXms
WARNING - Chart rendering timeout after XXXms, proceeding anyway
```

Estos warnings son normales si el contenido ya está listo antes del timeout.

### ❌ Errores a Investigar (Bad)

```
ERROR - Playwright error during PDF generation
ERROR - Timeout during PDF generation
ERROR - Failed to generate PDF report with Playwright
```

Si ves estos errores, revisa:
1. ¿Playwright está instalado en el contenedor?
2. ¿El timeout del contenedor es suficiente (>60s)?
3. ¿Hay problemas de memoria?

## 🧪 Testing en Producción

### Test 1: Verificar timing
```bash
# Los logs deberían mostrar ~27-42 segundos total
# Busca "PDF generated successfully" y calcula el tiempo desde "Starting PDF generation"
```

### Test 2: Descargar y verificar PDF
```bash
# Desde Azure Portal:
# 1. Ve a Storage Account → Containers → media → reports → pdf
# 2. Descarga el PDF más reciente
# 3. Abre y verifica:
#    - No hay espacios en blanco
#    - Todos los gráficos están visibles
#    - Todas las tablas tienen contenido
#    - Todas las imágenes cargaron
```

### Test 3: Comparación antes/después
```bash
# Genera un reporte antes del deploy (si es posible)
# Genera un reporte después del deploy
# Compara visualmente ambos PDFs
```

## 📈 Métricas de Éxito

| Métrica | Antes | Después | Status |
|---------|-------|---------|--------|
| Tiempo de generación | ~18s | ~35s | ✅ Esperado |
| Espacios en blanco | Sí | No | ✅ Objetivo |
| Gráficos renderizados | Parcial | Completo | ✅ Objetivo |
| Imágenes cargadas | Parcial | Completo | ✅ Objetivo |
| Calidad del PDF | Media | Alta | ✅ Objetivo |

## 🔧 Troubleshooting

### Problema: PDF tarda más de 60s
**Solución**: Aumentar `DEFAULT_TIMEOUT` en `pdf_service.py` línea 50

### Problema: Aún hay espacios en blanco
**Solución**: Aumentar los timeouts específicos:
- `CHART_TIMEOUT` (línea 53)
- Final wait (línea 180)
- Chart maxChecks (línea 234)

### Problema: Container timeout
**Solución**: Ajustar timeout en Azure Container Apps:
```bash
az containerapp update \
  --name azure-advisor-reports \
  --resource-group AzureAdvisorReportsPlatform-rg \
  --timeout 300  # 5 minutos
```

### Problema: Out of Memory
**Solución**: Aumentar memoria del contenedor:
```bash
az containerapp update \
  --name azure-advisor-reports \
  --resource-group AzureAdvisorReportsPlatform-rg \
  --memory 2.0Gi
```

## 📝 Rollback Plan

Si algo sale mal:

```bash
# Ver revisiones anteriores
az containerapp revision list \
  --name azure-advisor-reports \
  --resource-group AzureAdvisorReportsPlatform-rg \
  --output table

# Activar revisión anterior
az containerapp revision activate \
  --name azure-advisor-reports \
  --resource-group AzureAdvisorReportsPlatform-rg \
  --revision <revision-name>

# O hacer rollback del código
git revert <commit-hash>
git push origin main
```

## 🎯 Next Steps

1. **Optimización**: Una vez confirmado que funciona, podemos ajustar los timeouts a la baja
2. **Monitoreo**: Configurar alertas si la generación tarda más de X segundos
3. **Cacheo**: Considerar cachear recursos estáticos (Chart.js, CSS) para acelerar
4. **Async**: Evaluar si se pueden hacer algunas esperas en paralelo

## 📞 Support

Si tienes problemas:
1. Revisa los logs detallados arriba
2. Verifica el PDF generado manualmente
3. Compara con el documento `PDF_RENDER_IMPROVEMENTS.md`
4. Ajusta timeouts según necesidad
