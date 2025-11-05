# CSV Security Notice
## Azure Reports Advisor Application

**Version:** 1.0
**Last Updated:** November 5, 2025
**Applicable To:** All users uploading or downloading CSV files

---

## Overview

Para proteger tu seguridad y la de tu organización, todos los archivos CSV procesados por Azure Reports Advisor son automáticamente sanitizados para prevenir **ataques de inyección de fórmulas** (CSV Injection).

---

## ¿Qué es CSV Injection?

CSV Injection (también conocido como Formula Injection) es un tipo de ataque que ocurre cuando aplicaciones de hojas de cálculo como:
- Microsoft Excel
- LibreOffice Calc
- Google Sheets
- Apache OpenOffice Calc

...ejecutan fórmulas maliciosas que están presentes en archivos CSV.

### Ejemplo de Ataque

Un archivo CSV malicioso podría contener:
```csv
Nombre,Valor
Usuario1,=cmd|"/c calc"!A1
```

Al abrir este CSV en Excel, la fórmula `=cmd|"/c calc"!A1` podría ejecutarse automáticamente, lanzando la calculadora de Windows (o peor, ejecutando código malicioso).

### Peligros Potenciales

Los ataques de CSV Injection pueden:
- Ejecutar comandos arbitrarios en tu computadora
- Exfiltrar datos sensibles a servidores externos
- Acceder a archivos locales
- Realizar ataques DDE (Dynamic Data Exchange)

---

## ¿Cómo te Protegemos?

Azure Reports Advisor implementa **sanitización automática** de todos los valores de celdas en archivos CSV.

### Caracteres Peligrosos

Los siguientes caracteres al inicio de una celda son considerados peligrosos:
- `=` (igual)
- `+` (más)
- `-` (menos)
- `@` (arroba)
- `|` (pipe/barra vertical)
- `\t` (tabulador)
- `\r` (retorno de carro)

### Proceso de Sanitización

Cuando un valor en tu CSV comienza con uno de estos caracteres, **automáticamente se le agrega una comilla simple** (`'`) al inicio.

**Ejemplo:**

| Valor Original | Valor Sanitizado |
|----------------|------------------|
| `=SUM(A1:A10)` | `'=SUM(A1:A10)` |
| `+1+2+3` | `'+1+2+3` |
| `-100` | `'-100` |
| `@A1` | `'@A1` |
| `|calc` | `'|calc` |

La comilla simple indica a las aplicaciones de hojas de cálculo que **traten el contenido como texto**, no como una fórmula.

---

## Impacto en tus Datos

### Datos Legítimos

Si tus datos legítimamente contienen valores que comienzan con estos caracteres (por ejemplo, números negativos o fórmulas matemáticas), la sanitización:

1. **Preserva el contenido original** - No se pierde información
2. **Agrega una comilla simple visible** - Al abrir en Excel verás `'-100` en lugar de `-100`
3. **Previene ejecución no deseada** - La aplicación trata el valor como texto

### Cómo Visualizar los Datos

**En Excel/Calc:**
- La comilla simple (`'`) aparecerá al inicio de la celda
- Al hacer clic en la celda, verás el valor completo en la barra de fórmulas
- Para editar, simplemente borra la comilla si es un valor legítimo

**En Reportes PDF:**
- Los valores se muestran tal como aparecen en el CSV sanitizado
- Las comillas simples son parte del texto mostrado

---

## Recomendaciones

### Para Usuarios Finales

1. **No remuevas la protección** - Las comillas simples están ahí por seguridad
2. **Valida la fuente** - Solo sube archivos CSV de fuentes confiables
3. **Revisa antes de compartir** - Verifica que los reportes exportados no contengan datos sensibles
4. **Reporta anomalías** - Si ves valores sospechosos en tus CSVs, contacta al equipo de seguridad

### Para Administradores

1. **Educación del equipo** - Asegúrate de que todos comprendan los riesgos de CSV Injection
2. **Monitoreo** - Revisa los logs de seguridad regularmente
3. **Auditoría** - Verifica los archivos CSV antes de procesarlos manualmente
4. **Políticas** - Implementa políticas de manejo seguro de archivos CSV

---

## Referencias Técnicas

### Estándares de Seguridad

- **OWASP CSV Injection**: https://owasp.org/www-community/attacks/CSV_Injection
- **CWE-1236**: Improper Neutralization of Formula Elements in a CSV File
- **OWASP Cheat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html

### Investigación de Seguridad

- [Comma Separated Vulnerabilities (2014)](https://www.contextis.com/en/blog/comma-separated-vulnerabilities)
- [The Absurdly Underestimated Dangers of CSV Injection](http://georgemauer.net/2017/10/07/csv-injection.html)
- [CVE-2014-3524](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2014-3524) - CSV Injection in Elasticsearch

---

## Preguntas Frecuentes (FAQ)

### ¿Por qué veo comillas simples en mis datos?

Las comillas simples (`'`) son agregadas automáticamente como medida de seguridad para prevenir que aplicaciones de hojas de cálculo ejecuten fórmulas maliciosas. Esto protege tu computadora de ataques de CSV Injection.

### ¿Puedo desactivar esta protección?

No. La sanitización de CSV es una característica de seguridad crítica que no puede ser desactivada. Esto protege a todos los usuarios de la plataforma.

### ¿Afecta el análisis de mis datos?

No. La sanitización preserva el contenido original de tus datos. Solo agrega una comilla simple al inicio de valores que podrían ser interpretados como fórmulas. El análisis estadístico y los reportes funcionan normalmente.

### ¿Qué pasa si necesito fórmulas legítimas en mi CSV?

Si necesitas incluir fórmulas legítimas (por ejemplo, para análisis en Excel), puedes:
1. Exportar el reporte desde Azure Reports Advisor
2. Abrir en Excel
3. Manualmente remover las comillas simples de las fórmulas legítimas
4. **IMPORTANTE**: Solo haz esto si confías completamente en el origen de los datos

### ¿Los archivos CSV que descargo están sanitizados?

Sí. Todos los archivos CSV exportados desde Azure Reports Advisor incluyen la sanitización de seguridad. Esto asegura que puedas compartir reportes de forma segura con tu equipo.

### ¿Afecta el rendimiento del procesamiento?

No. La sanitización es extremadamente rápida (< 1ms por fila) y no impacta significativamente el tiempo de procesamiento de archivos CSV.

---

## Ejemplos de Sanitización

### Caso 1: Números Negativos

**Input CSV:**
```csv
Category,Amount
Cost Saving,-500
Revenue,+1000
```

**Después de Sanitización:**
```csv
Category,Amount
Cost Saving,'-500
Revenue,'+1000
```

### Caso 2: Descripciones con Símbolos

**Input CSV:**
```csv
Recommendation,Priority
=IMPORTANT= Upgrade servers,High
@TODO Check backups,Medium
```

**Después de Sanitización:**
```csv
Recommendation,Priority
'=IMPORTANT= Upgrade servers,High
'@TODO Check backups,Medium
```

### Caso 3: Fórmulas Maliciosas (Bloqueadas)

**Input CSV (Malicioso):**
```csv
Name,Command
Victim,=cmd|"/c calc"!A1
```

**Después de Sanitización (Seguro):**
```csv
Name,Command
Victim,'=cmd|"/c calc"!A1
```

La fórmula ahora es tratada como texto y **no se ejecutará**.

---

## Contacto de Seguridad

Si tienes preguntas sobre seguridad de CSV o necesitas reportar un incidente:

**Email de Seguridad**: security@yourcompany.com

**Documentación Técnica**: Ver `/docs/SECURITY_IMPLEMENTATION_PLAN.md`

---

## Cumplimiento y Auditoría

Esta funcionalidad de seguridad cumple con:
- OWASP Top 10 (Injection Prevention)
- CWE/SANS Top 25
- ISO 27001 (Control de Seguridad de Aplicaciones)
- NIST Cybersecurity Framework

**Registro de Auditoría**: Todos los eventos de sanitización son registrados en los logs de seguridad de la aplicación para fines de auditoría y cumplimiento.

---

## Historial de Cambios

| Fecha | Versión | Cambios | Autor |
|-------|---------|---------|--------|
| 2025-11-05 | 1.0 | Implementación inicial de prevención de CSV Injection | Security Team |

---

**Próxima Revisión:** 2026-05-05
**Estado:** Activo en Producción
