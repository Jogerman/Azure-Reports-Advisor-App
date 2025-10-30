# Guía para Generar el PDF Optimizado

## Método Recomendado: Django Management Command

### Paso 1: Activar el Entorno Virtual

```bash
cd "D:\Code\Azure Reports\azure_advisor_reports"
```

**En Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**En Windows CMD:**
```cmd
.\venv\Scripts\activate.bat
```

**En Git Bash:**
```bash
source venv/Scripts/activate
```

### Paso 2: Verificar que Django esté disponible

```bash
python -c "import django; print(f'Django version: {django.get_version()}')"
```

Deberías ver algo como: `Django version: 5.1.2`

### Paso 3: Generar el PDF Optimizado

**Opción A - Via Django Shell:**

```bash
python manage.py shell
```

Luego ejecuta:

```python
from apps.reports.models import Client
from apps.reports.services.report_generator import ReportGenerator
import os

# Obtener el cliente Autozama
client = Client.objects.get(company_name='Autozama')
print(f"Cliente encontrado: {client.company_name}")

# Crear el generador
generator = ReportGenerator()

# Generar el PDF optimizado
output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath('.'))), 'playwright_optimized.pdf')
pdf_path = generator.generate_executive_report(
    client=client,
    output_filename='playwright_optimized.pdf'
)

print(f"\nPDF generado exitosamente!")
print(f"Ruta: {pdf_path}")

# Obtener tamaño del archivo
import os
size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
print(f"Tamaño: {size_mb:.2f} MB")
```

**Opción B - Script Python Directo:**

Crear un archivo `generate_pdf.py` en `azure_advisor_reports/`:

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
django.setup()

from apps.reports.models import Client
from apps.reports.services.report_generator import ReportGenerator

def main():
    # Obtener cliente
    client = Client.objects.get(company_name='Autozama')

    # Generar PDF
    generator = ReportGenerator()
    pdf_path = generator.generate_executive_report(
        client=client,
        output_filename='playwright_optimized.pdf'
    )

    # Mostrar resultados
    size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
    print(f"PDF generado: {pdf_path}")
    print(f"Tamaño: {size_mb:.2f} MB")

if __name__ == '__main__':
    main()
```

Luego ejecutar:

```bash
python generate_pdf.py
```

### Paso 4: Comparar con el Original

```bash
cd "D:\Code\Azure Reports"

# Ver tamaño del archivo original
ls -lh playwright_current.pdf

# Ver tamaño del archivo optimizado
ls -lh playwright_optimized.pdf
```

O en PowerShell:

```powershell
# Original
Get-Item playwright_current.pdf | Select-Object Name, @{Name="SizeMB";Expression={[math]::Round($_.Length/1MB, 2)}}

# Optimizado
Get-Item playwright_optimized.pdf | Select-Object Name, @{Name="SizeMB";Expression={[math]::Round($_.Length/1MB, 2)}}
```

## Método Alternativo: Via Web Interface

### Paso 1: Iniciar el Servidor

```bash
cd "D:\Code\Azure Reports\azure_advisor_reports"
.\venv\Scripts\activate
python manage.py runserver
```

### Paso 2: Acceder a la Interfaz Web

Abre tu navegador en: `http://localhost:8000/`

### Paso 3: Generar el Reporte

1. Navega a la sección de reportes
2. Selecciona el cliente "Autozama"
3. Elige "Executive Report"
4. Haz clic en "Generate PDF"
5. El PDF se descargará automáticamente

### Paso 4: Comparar

El archivo descargado será el PDF optimizado. Compáralo con `playwright_current.pdf`.

## Verificación de Optimizaciones

### Checklist Visual:

#### Página 1 (Cover):
- ✅ Cover page completa sin cambios

#### Página 2 (Executive Summary):
- ✅ Header compacto
- ✅ Grid de 4 metric cards visible completo

#### Página 3 (Key Insights):
- ✅ Strategic Overview box más compacto
- ✅ Siguiente sección comienza en la misma página

#### Página 4-5 (Charts):
- ✅ Charts de 200px de altura (no 300px)
- ✅ Tabla de categorías en la misma página que los charts

#### Página 6-7 (Quick Wins):
- ✅ Tabla más compacta
- ✅ Padding reducido en celdas

#### Página 8-10 (Top 10 + Roadmap):
- ✅ Tabla Top 10 sin página vacía
- ✅ Roadmap cards con font-size 2.5rem (no 3rem)
- ✅ Line-height 1.8 en listas (no 2.2)

#### Página 11-12 (Financial Impact):
- ✅ Metric cards compactos
- ✅ Info box con line-height 1.7

#### Última Página (Footer):
- ✅ Disclaimer compacto
- ✅ Footer credits con font-size 0.75rem

### Checklist Técnico:

```bash
# Verificar tamaño
du -h playwright_optimized.pdf
# Objetivo: ≤700 KB (0.7 MB)

# Contar páginas (aproximado)
# Abrir el PDF y verificar número de páginas
# Objetivo: 10-12 páginas (vs 16 originales)
```

### Checklist de Calidad:

- ✅ **Gráficos Chart.js**: Se ven correctamente, sin cortes
- ✅ **Colores**: Todos los colores Azure se mantienen
- ✅ **Texto legible**: Fuente mínima 0.7rem es legible
- ✅ **Tablas**: No se cortan entre páginas
- ✅ **Icons/Emojis**: Todos visibles correctamente
- ✅ **Gradients**: Backgrounds con gradientes se mantienen

## Troubleshooting

### Error: "No module named 'django'"

**Solución:** Activar el entorno virtual primero

```bash
cd azure_advisor_reports
.\venv\Scripts\activate
```

### Error: "Client matching query does not exist"

**Solución:** Verificar que el cliente Autozama existe en la base de datos

```bash
python manage.py shell
```

```python
from apps.reports.models import Client
clients = Client.objects.all()
for c in clients:
    print(f"ID: {c.id}, Name: {c.company_name}")
```

Si no existe, créalo:

```python
client = Client.objects.create(
    company_name='Autozama',
    contact_name='Test Contact',
    contact_email='test@autozama.com',
    industry='automotive'
)
```

### Error: "playwright not installed"

**Solución:** Instalar Playwright

```bash
pip install playwright
python -m playwright install chromium
```

### PDF no se genera / timeout

**Solución:** Aumentar el timeout en `pdf_service.py`

```python
# En pdf_service.py, línea ~50
DEFAULT_TIMEOUT = 60000  # Aumentar a 60 segundos
```

## Métricas Esperadas

### Antes de las Optimizaciones:
- **Tamaño**: 1.2 MB
- **Páginas**: 16
- **Tiempo de generación**: ~3 segundos

### Después de las Optimizaciones:
- **Tamaño objetivo**: 500-700 KB (40-60% reducción)
- **Páginas objetivo**: 10-12 (25-37% reducción)
- **Tiempo de generación**: ~3 segundos (sin cambio)

## Siguientes Pasos

Una vez generado el PDF optimizado:

1. **Abrir ambos PDFs** (original y optimizado) lado a lado
2. **Comparar página por página** usando la lista de verificación arriba
3. **Medir el tamaño** con el comando `ls -lh` o PowerShell
4. **Contar páginas** en el visor de PDF
5. **Calcular porcentaje de mejora**:
   ```
   Reducción de tamaño = ((Original - Optimizado) / Original) * 100%
   Reducción de páginas = Original - Optimizado
   ```

## Reporte de Resultados

Crea un archivo `OPTIMIZATION_RESULTS.md` con:

```markdown
# Resultados de Optimización del PDF

## Métricas

### Tamaño del Archivo:
- Original: X.XX MB
- Optimizado: X.XX MB
- Reducción: XX.X%

### Número de Páginas:
- Original: 16 páginas
- Optimizado: XX páginas
- Reducción: X páginas

### Calidad Visual:
- ✅ Gráficos Chart.js: OK
- ✅ Legibilidad: OK
- ✅ Colores y branding: OK
- ✅ Tablas completas: OK

## Conclusión

[Describe si las optimizaciones fueron exitosas y si hay
necesidad de ajustes adicionales]
```

## Contacto

Si tienes problemas generando el PDF, revisa:
1. `PDF_OPTIMIZATION_SUMMARY.md` - Lista completa de cambios
2. Los archivos modificados directamente
3. Los logs de Django para errores específicos
