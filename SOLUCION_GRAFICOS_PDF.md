# Solución al Problema de Gráficos en PDFs - Producción

## Resumen del Problema

**Problema**: Los PDFs generados en producción no mostraban los gráficos de visualización en las páginas 5-7 (Distribución por Categoría, Distribución por Nivel de Impacto, y Potencial de Optimización de Costos).

**Causa Raíz**: La plantilla base (`base_redesigned.html`) cargaba Chart.js desde un CDN (jsdelivr.net) que no es accesible cuando Playwright genera PDFs en producción usando `page.set_content()` sin una URL base.

## Solución Implementada

**Corrección**: Incrustar las librerías de Chart.js directamente en el HTML para garantizar que siempre estén disponibles sin importar el acceso a la red.

### Cambios Realizados

#### 1. Descarga de Librerías Chart.js Localmente

Se crearon copias locales de las librerías Chart.js:
- `azure_advisor_reports/static/js/vendor/chart.umd.min.js` (200KB)
- `azure_advisor_reports/static/js/vendor/chartjs-plugin-datalabels.min.js` (13KB)

#### 2. Template Includes Creados

Se copiaron los archivos JavaScript a los includes de plantilla para incrustarlos:
- `azure_advisor_reports/templates/reports/includes/chart.umd.min.js`
- `azure_advisor_reports/templates/reports/includes/chartjs-plugin-datalabels.min.js`

#### 3. Actualización de Plantilla Base

Se modificó `azure_advisor_reports/templates/reports/base_redesigned.html`:

**ANTES** (con CDN - fallaba en producción):
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
```

**AHORA** (incrustado - funciona en todos los entornos):
```html
<script>
{% include 'reports/includes/chart.umd.min.js' %}
</script>
<script>
{% include 'reports/includes/chartjs-plugin-datalabels.min.js' %}
</script>
```

## ¿Por Qué Funciona Esta Solución?

1. **Sin Dependencias Externas**: El código de Chart.js está embebido directamente en el HTML, eliminando la necesidad de peticiones de red externas
2. **Compatible con Playwright**: Cuando Playwright carga el HTML con `page.set_content()`, todo el JavaScript está inmediatamente disponible
3. **Seguro para Producción**: Funciona en entornos con red restringida (contenedores Docker, Azure Container Apps, etc.)
4. **Compatible con Desarrollo**: Sigue funcionando en el entorno de desarrollo sin ningún cambio

## Archivos Modificados

```
azure_advisor_reports/
├── templates/
│   └── reports/
│       ├── base_redesigned.html           # MODIFICADO - Scripts actualizados
│       └── includes/                       # NUEVO - Directorio de includes
│           ├── chart.umd.min.js           # NUEVO - Librería Chart.js
│           └── chartjs-plugin-datalabels.min.js  # NUEVO - Plugin datalabels
└── static/
    └── js/
        └── vendor/                        # NUEVO - Directorio vendor JS
            ├── chart.umd.min.js           # NUEVO - Fuente Chart.js
            └── chartjs-plugin-datalabels.min.js  # NUEVO - Fuente plugin
```

## Pasos para Desplegar en Producción

### Opción 1: Azure Container Apps (Recomendado)

1. **Commit de Cambios**:
   ```bash
   git add .
   git commit -m "fix: Incrustar Chart.js para corregir generación de PDFs en producción"
   git push origin main
   ```

2. **Build y Push a Azure Container Registry**:
   ```bash
   az acr build --registry <tu-registry> \
     --image azure-advisor-backend:v1.2.4 \
     --image azure-advisor-backend:latest \
     --file azure_advisor_reports/Dockerfile.prod \
     azure_advisor_reports
   ```

3. **Actualizar Container App**:
   ```bash
   az containerapp update \
     --name <nombre-de-tu-app> \
     --resource-group <tu-resource-group> \
     --image <tu-registry>.azurecr.io/azure-advisor-backend:v1.2.4
   ```

4. **Verificar el Despliegue**:
   - Genera un reporte detallado
   - Descarga el PDF
   - Verifica que todos los gráficos se rendericen correctamente

### Opción 2: Docker Compose

```bash
docker-compose up -d --build backend
```

## Verificación Post-Despliegue

Después del despliegue, verifica:

- [ ] La página de portada se renderiza correctamente
- [ ] La página de resumen ejecutivo se renderiza correctamente
- [ ] Gráfico de Distribución por Categoría (Página 5) muestra gráfico de dona
- [ ] Gráfico de Distribución por Nivel de Impacto (Página 6) muestra gráfico de dona
- [ ] Gráfico de Potencial de Optimización de Costos (Página 7) muestra gráfico de barras horizontales
- [ ] Las tablas y contenido de texto permanecen intactos
- [ ] El tamaño del PDF es razonable (< 2MB para un reporte típico)
- [ ] Los gráficos están correctamente coloreados y etiquetados

## Impacto

### Tamaño de Archivos
- **Chart.js**: ~200KB (minificado)
- **Plugin Datalabels**: ~13KB (minificado)
- **Total Agregado**: ~213KB al HTML antes de conversión a PDF
- **Impacto en PDF**: Mínimo (JavaScript no se embebe en el PDF final)

### Rendimiento
- **Positivo**: No se necesitan peticiones de red para Chart.js
- **Neutral**: Playwright carga el HTML en memoria de todos modos
- **General**: Debería ser ligeramente más rápido debido a la ausencia de latencia del CDN

## Pruebas

Para probar localmente antes de desplegar:

```bash
cd azure_advisor_reports
python ../test_chart_pdf.py
```

Esto generará `test_chart_rendering.pdf` - ábrelo y verifica que los gráficos sean visibles.

## Plan de Rollback

Si ocurren problemas, revertir cambiando:

```bash
git revert HEAD
# Reconstruir y redesplegar
```

---

**Solucionado por**: Claude Code
**Fecha**: 1 de Noviembre, 2025
**Versión**: v1.2.4 (pendiente)
