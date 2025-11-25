# Actualización de Logos en Templates de Reportes

## Resumen de Cambios

Se han actualizado los templates de reportes para reorganizar la ubicación de los logos según el nuevo diseño:

### Cambios Realizados

#### 1. Portada del Reporte (Cover Page)

**Antes:**
- **Círculo negro (arriba izquierda)**: Ícono genérico SVG
- **Centro**: Logo de Solvex
- **Texto**: Nombre del cliente abajo del logo de Solvex

**Después:**
- **Círculo negro (arriba izquierda)**: Logo de Solvex
- **Centro**: Logo del cliente (si existe) + Nombre del cliente
- **Estilo mejorado**: Logo del cliente con efecto circular, backdrop blur y sombras

### Archivos Modificados

1. **`azure_advisor_reports/templates/reports/base.html`**
   - Actualizado el HTML de la portada (cover page)
   - Modificado CSS del `.cover-logo` para mejor visualización de imágenes
   - Agregado soporte para mostrar el logo del cliente en el centro

2. **`azure_advisor_reports/templates/reports/base_redesigned.html`**
   - Mismos cambios aplicados para mantener consistencia
   - Actualizado HTML y CSS de la portada

### Detalles Técnicos

#### CSS Actualizado para `.cover-logo`:
```css
.cover-logo {
    width: 120px;           /* Aumentado de 80px */
    height: 120px;          /* Aumentado de 80px */
    background: rgba(255, 255, 255, 0.95);  /* Más opaco para mejor contraste */
    backdrop-filter: blur(10px);
    border-radius: var(--radius-xl);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: var(--spacing-6);
    box-shadow: var(--shadow-lg);
    overflow: hidden;       /* Añadido */
}

.cover-logo img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}
```

#### HTML de la Portada - Logo de Solvex (Arriba Izquierda):
```html
<div class="cover-logo">
    <!-- Solvex Logo -->
    <img src="data:image/png;base64,{% include 'reports/partials/logo_base64.html' %}"
         alt="Solvex Logo"
         style="width: 100%; height: 100%; object-fit: contain; padding: 8px;">
</div>
```

#### HTML de la Portada - Logo del Cliente (Centro):
```html
<div style="margin: 30px 0; text-align: center;">
    <!-- Client Logo -->
    {% if client.logo %}
    <div style="margin-bottom: 20px;">
        <img src="{{ client.logo.url }}"
             alt="{{ client.company_name }} Logo"
             style="max-width: 250px;
                    max-height: 250px;
                    object-fit: contain;
                    border-radius: 50%;
                    background: rgba(255, 255, 255, 0.15);
                    backdrop-filter: blur(10px);
                    padding: 30px;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1),
                                0 10px 10px -5px rgba(0, 0, 0, 0.04);">
    </div>
    {% endif %}
    <div style="font-size: 2rem;
                color: white;
                font-weight: 600;
                margin-bottom: 20px;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);">
        {{ client.company_name }}
    </div>
</div>
```

### Comportamiento

1. **Logo de Solvex**: Siempre se muestra en la esquina superior izquierda de la portada
2. **Logo del Cliente**:
   - Se muestra en el centro si existe (`{% if client.logo %}`)
   - Tiene estilo circular con efecto de blur y sombra
   - Máximo 250x250px, se ajusta proporcionalmente
3. **Nombre del Cliente**: Siempre se muestra debajo del logo (o en el centro si no hay logo)

### Compatibilidad

- ✅ Logo del cliente funciona con la nueva funcionalidad de upload de logos
- ✅ Si el cliente no tiene logo, solo se muestra el nombre del cliente
- ✅ El logo de Solvex se carga desde base64 (ya existente)
- ✅ Los templates que extienden de `base.html` heredan estos cambios automáticamente

### Templates Afectados

Todos los reportes que usan estos templates base verán los cambios:
- Cost Reports (`cost.html`, `cost_enhanced.html`, `cost_redesigned.html`)
- Executive Reports (`executive.html`, `executive_enhanced.html`)
- Security Reports (`security.html`, `security_enhanced.html`)
- Operations Reports (`operations.html`)

### Próximos Pasos

1. **Generar un reporte de prueba** con un cliente que tenga logo
2. **Verificar** que el logo de Solvex aparece correctamente arriba a la izquierda
3. **Verificar** que el logo del cliente aparece correctamente en el centro con su nombre
4. **Revisar** el diseño en PDF generado

### Notas de Desarrollo

- El logo de Solvex se mantiene en base64 para evitar dependencias de archivos externos
- El logo del cliente se carga desde `client.logo.url` (campo agregado en feature anterior)
- Los estilos están inline para garantizar compatibilidad con PDF
- El backdrop-filter puede no funcionar en todos los navegadores/PDFs, pero degrada gracefully

## Testing

Para probar los cambios:

```bash
# 1. Asegurarse de tener un cliente con logo
# 2. Generar un reporte para ese cliente
# 3. Verificar la portada del PDF generado
```

## Referencias

- Diseño de referencia: `Context_docs/Diseno reporte.png`
- Logo de Solvex: `Context_docs/logo Solvex.png`
- Template base64 del logo: `templates/reports/partials/logo_base64.html`
