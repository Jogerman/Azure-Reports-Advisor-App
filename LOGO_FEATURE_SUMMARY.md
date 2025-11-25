# Feature: Client Logo Upload

## Overview
Se ha implementado la funcionalidad para que los clientes puedan subir y gestionar sus logos empresariales, que luego serán utilizados para personalizar los reportes generados.

## Cambios Realizados

### Backend (Django)

#### 1. Modelo de Cliente (`azure_advisor_reports/apps/clients/models.py`)
- ✅ Agregado campo `logo` de tipo `ImageField`
- Ubicación: `upload_to='client_logos/'`
- Características: Campo opcional (blank=True, null=True)

#### 2. Migración de Base de Datos
- ✅ Creada migración: `0003_add_client_logo_field.py`
- **IMPORTANTE**: Ejecutar la migración antes de usar la funcionalidad

#### 3. Serializers (`azure_advisor_reports/apps/clients/serializers.py`)
- ✅ Agregado campo `logo` a:
  - `ClientListSerializer` - Para mostrar en listas
  - `ClientDetailSerializer` - Para detalle del cliente
  - `ClientCreateUpdateSerializer` - Para crear/actualizar con logo

#### 4. Configuración de Media Files
- ✅ Ya configurado en `settings.py`:
  - `MEDIA_URL = '/media/'`
  - `MEDIA_ROOT = BASE_DIR / 'media'`
  - `MultiPartParser` habilitado en REST_FRAMEWORK

### Frontend (React + TypeScript)

#### 1. Interfaces TypeScript (`frontend/src/services/clientService.ts`)
- ✅ Actualizada interfaz `Client` con campo `logo?: string | null`
- ✅ Actualizada interfaz `CreateClientData` con campo `logo?: File | null`
- ✅ Actualizada interfaz `UpdateClientData` para soportar logo
- ✅ Modificados métodos `createClient` y `updateClient` para soportar FormData

#### 2. Formulario de Cliente (`frontend/src/components/clients/ClientForm.tsx`)
- ✅ Agregado campo de subida de archivo con:
  - Validación de tipo de archivo (solo imágenes)
  - Validación de tamaño (máximo 5MB)
  - Vista previa del logo
  - Opción para remover el logo
  - Mensajes informativos

#### 3. Vista de Detalle del Cliente (`frontend/src/pages/ClientDetailPage.tsx`)
- ✅ Agregada visualización del logo en el encabezado (al lado del nombre de la compañía)

#### 4. Tarjeta de Cliente (`frontend/src/components/clients/ClientCard.tsx`)
- ✅ Agregada visualización del logo en la tarjeta de lista de clientes

## Características de la Funcionalidad

### Upload de Logo
- **Tipos de archivo soportados**: Todas las imágenes (PNG, JPG, GIF, etc.)
- **Tamaño máximo**: 5MB
- **Vista previa**: Muestra el logo inmediatamente después de seleccionarlo
- **Validaciones**:
  - Solo permite archivos de imagen
  - Verifica el tamaño del archivo
  - Muestra mensajes de error si no cumple los requisitos

### Visualización del Logo
- **En la lista de clientes**: Logo de 48x48px con bordes redondeados
- **En la página de detalle**: Logo de 64x64px con bordes redondeados
- **En el formulario**: Vista previa de 96x96px con botón para remover

### Edición del Logo
- Se puede actualizar el logo desde el formulario de edición del cliente
- El logo actual se muestra como vista previa
- Se puede remover el logo haciendo clic en el botón "X"

## Pasos para Probar

### 1. Ejecutar la Migración
```bash
cd azure_advisor_reports
python3 manage.py migrate clients
```

### 2. Asegurar que la Carpeta Media Existe
```bash
mkdir -p azure_advisor_reports/media/client_logos
```

### 3. Configurar URLs para Servir Media Files (Desarrollo)
Verificar que en `azure_advisor_reports/urls.py` esté configurado para servir archivos media en desarrollo:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... tus urls existentes
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 4. Iniciar el Backend
```bash
cd azure_advisor_reports
python3 manage.py runserver
```

### 5. Iniciar el Frontend
```bash
cd frontend
npm start
```

### 6. Probar la Funcionalidad

#### Crear un Cliente con Logo:
1. Ir a la página de clientes
2. Hacer clic en "Crear Cliente"
3. Llenar los datos requeridos
4. En el campo "Company Logo", hacer clic en "Choose File"
5. Seleccionar una imagen (PNG, JPG, etc.)
6. Verificar que aparece la vista previa
7. Hacer clic en "Crear Cliente"
8. Verificar que el logo aparece en la tarjeta del cliente

#### Editar el Logo de un Cliente:
1. Ir a la página de detalle de un cliente
2. Hacer clic en "Edit"
3. Cambiar el logo seleccionando un nuevo archivo
4. Hacer clic en "Update Client"
5. Verificar que el logo se actualizó

#### Remover el Logo:
1. Ir a la página de edición de un cliente
2. Hacer clic en el botón "X" rojo sobre la vista previa del logo
3. Hacer clic en "Update Client"
4. Verificar que el logo ya no aparece

## Archivos Modificados

### Backend
- `azure_advisor_reports/apps/clients/models.py`
- `azure_advisor_reports/apps/clients/serializers.py`
- `azure_advisor_reports/apps/clients/migrations/0003_add_client_logo_field.py` (nuevo)

### Frontend
- `frontend/src/services/clientService.ts`
- `frontend/src/components/clients/ClientForm.tsx`
- `frontend/src/pages/ClientDetailPage.tsx`
- `frontend/src/components/clients/ClientCard.tsx`

## Próximos Pasos (Opcional)

### Uso del Logo en Reportes
Para usar el logo en los reportes generados, necesitarás:

1. **En el template del reporte PDF**: Agregar una sección para mostrar el logo del cliente
2. **En el servicio de generación de reportes**: Pasar el logo del cliente al template

Ejemplo en el template HTML del reporte:
```html
{% if client.logo %}
<div class="client-logo">
  <img src="{{ client.logo.url }}" alt="{{ client.company_name }} logo" />
</div>
{% endif %}
```

### Optimización de Imágenes (Opcional)
Considerar agregar:
- Redimensionamiento automático de logos muy grandes
- Conversión a formato optimizado (WebP)
- Uso de Pillow para procesar imágenes

## Notas Importantes

1. **Seguridad**: El backend valida que solo se suban archivos de imagen
2. **Tamaño de archivo**: Limitado a 5MB en el frontend y 10MB en el backend
3. **Almacenamiento**: Los logos se guardan en `media/client_logos/`
4. **Producción**: En producción, considera usar un servicio de almacenamiento externo como Azure Blob Storage

## Soporte

Si encuentras algún problema:
1. Verifica que la migración se ejecutó correctamente
2. Verifica que la carpeta `media/client_logos` existe y tiene permisos de escritura
3. Revisa los logs del backend para errores de subida de archivos
4. Verifica que el navegador permite la subida de archivos
