# PDF Render Time Improvements

## Fecha: 2025-11-04

## Problema
Los PDFs generados tenían espacios en blanco porque Playwright no esperaba suficiente tiempo para que todo el contenido (especialmente gráficos de Chart.js, imágenes y elementos dinámicos) se renderizaran completamente antes de capturar el PDF.

## Solución Implementada

### 1. Aumento de Timeouts Globales
**Archivo**: `azure_advisor_reports/apps/reports/services/pdf_service.py`

- **DEFAULT_TIMEOUT**: Aumentado de 30s a 60s (líneas 49-50)
  - Proporciona más tiempo para operaciones complejas de página

- **CHART_TIMEOUT**: Aumentado de 10s a 15s (líneas 52-53)
  - Permite más tiempo para renderizar múltiples gráficos Chart.js

### 2. Mejoras en el Flujo de Espera (líneas 149-181)

#### a) Network Idle Timeout
```python
# Aumentado de 5s a 10s
await page.wait_for_load_state('networkidle', timeout=10000)
```
- Más tiempo para que los recursos de red se carguen completamente

#### b) DOM Load State
```python
await page.wait_for_load_state('load', timeout=self.timeout)
```
- Nueva espera explícita para asegurar que el DOM esté completamente cargado

#### c) Lazy-loaded Content
```python
await page.wait_for_timeout(2000)
```
- Espera adicional de 2s para contenido con carga diferida

#### d) Final Wait
```python
# Aumentado de 2s a 4s
await page.wait_for_timeout(4000)
```
- Tiempo adicional para asegurar que todas las animaciones y renders terminen

### 3. Nuevas Funciones de Espera

#### `_wait_for_images()` (líneas 325-397)
Espera explícita para que todas las imágenes se carguen:
- Detecta todas las imágenes en el documento
- Verifica que cada imagen tenga `complete = true` y `naturalHeight > 0`
- Usa event listeners para detectar carga exitosa o errores
- Timeout de 5s como fallback

**Beneficios**:
- Previene espacios en blanco donde deberían aparecer imágenes
- Maneja gracefully los errores de carga de imágenes

#### `_wait_for_elements_visible()` (líneas 399-470)
Verifica que todos los elementos principales sean visibles:
- Busca elementos clave: `.chart-container`, `.recommendation-card`, `table`, `canvas`, etc.
- Verifica dimensiones (width > 0, height > 0)
- Verifica estilos CSS (display, visibility, opacity)
- Chequeo iterativo cada 100ms hasta 5s máximo

**Beneficios**:
- Asegura que todos los elementos tengan dimensiones calculadas
- Previene captura de elementos que aún se están renderizando
- Detecta problemas de CSS que podrían ocultar contenido

### 4. Mejoras en Detección de Chart.js (líneas 234, 278-280)

#### Aumento de Iteraciones
```javascript
const maxChecks = 150; // 15 seconds max (150 * 100ms)
```
- Aumentado de 100 a 150 iteraciones para gráficos complejos

#### Delay Inicial
```javascript
setTimeout(checkCharts, 1000); // Aumentado de 500ms a 1000ms
```
- Más tiempo para que Chart.js se inicialice antes de empezar a verificar

### 5. Orden de Operaciones Optimizado

Nueva secuencia de espera:
1. Network idle (10s timeout)
2. DOM load complete
3. Fonts loading
4. Lazy-loaded content wait (2s)
5. **Chart.js rendering** (hasta 15s)
6. **Images loading** (hasta 5s) ← NUEVO
7. **Elements visibility check** (hasta 5s) ← NUEVO
8. Final animations wait (4s)

## Tiempo Total de Espera

### Antes:
- Network idle: 5s
- Fonts: ~1s
- Charts: hasta 10s
- Final wait: 2s
- **Total: ~18s máximo**

### Después:
- Network idle: 10s
- DOM load: variable
- Fonts: ~1s
- Lazy content: 2s
- Charts: hasta 15s (con delay inicial de 1s)
- Images: hasta 5s
- Elements visibility: hasta 5s
- Final wait: 4s
- **Total: ~42s máximo**

## Logging Mejorado

Cada paso ahora registra información detallada:
```python
logger.info("Network idle state reached")
logger.info("DOM load complete")
logger.info("Waited for lazy-loaded content")
logger.info("All images loaded successfully")
logger.info("All elements are visible")
logger.info("Final wait complete - all content should be rendered")
```

## Impacto Esperado

### Pros:
✅ Eliminación de espacios en blanco en PDFs
✅ Gráficos Chart.js completamente renderizados
✅ Todas las imágenes cargadas
✅ Todos los elementos visibles con dimensiones correctas
✅ Mejor calidad general de PDFs
✅ Logs detallados para debugging

### Contras:
⚠️ Tiempo de generación aumentado en ~25-30s por PDF
⚠️ Mayor uso de recursos del servidor durante más tiempo

## Recomendaciones

1. **Monitoreo**: Vigilar los logs de Celery para asegurar que los timeouts sean suficientes
2. **Ajuste Fino**: Si algunos PDFs aún tienen espacios, considerar aumentar los timeouts específicos
3. **Optimización Futura**: Una vez estable, se pueden ajustar los timeouts a la baja si no son necesarios
4. **Azure Container Apps**: Asegurar que el timeout del contenedor sea mayor a 60s

## Testing

Para probar los cambios:

```bash
# En producción
python trigger_report_generation.py

# Verificar logs
python check_reports.py

# Revisar el PDF generado para asegurar que no hay espacios en blanco
```

## Notas Técnicas

- Los cambios son **backward compatible** - no rompen nada existente
- Todos los timeouts tienen fallbacks graceful con warnings en logs
- La detección de Chart.js verifica píxeles dibujados, no solo dimensiones
- Los event listeners de imágenes manejan tanto éxito como error

## Referencias

- Archivo modificado: `azure_advisor_reports/apps/reports/services/pdf_service.py`
- Líneas clave: 49-53, 149-181, 234, 278-280, 325-470
- Flujo de generación: `base.py:generate_pdf_with_playwright()` (línea 304)
