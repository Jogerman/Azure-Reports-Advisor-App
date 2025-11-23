# 📘 Guía: Generar Reportes con Azure API

Esta guía te muestra cómo configurar y generar reportes automáticos usando la integración directa con Azure API.

---

## 📋 Tabla de Contenidos

1. [Prerrequisitos](#prerrequisitos)
2. [Parte 1: Configuración en Azure (Una sola vez)](#parte-1-configuración-en-azure)
3. [Parte 2: Configuración en la Aplicación](#parte-2-configuración-en-la-aplicación)
4. [Parte 3: Generar Reportes](#parte-3-generar-reportes)
5. [Solución de Problemas](#solución-de-problemas)

---

## Prerrequisitos

Antes de comenzar, necesitas:

- ✅ **Cuenta de Azure** con permisos de administrador en la suscripción
- ✅ **Acceso al Portal de Azure** (portal.azure.com)
- ✅ **Usuario en la aplicación** Azure Advisor Reports

---

## Parte 1: Configuración en Azure

### 🎯 Objetivo
Crear un **Service Principal (App Registration)** que permita a la aplicación acceder a las recomendaciones de Azure Advisor.

### Paso 1: Crear App Registration

1. **Inicia sesión en el Portal de Azure**
   - Ir a: https://portal.azure.com

2. **Navega a Azure Active Directory**
   - En el menú lateral, busca **"Azure Active Directory"** o **"Microsoft Entra ID"**
   - Click en el servicio

3. **Crear nueva App Registration**
   - En el menú lateral, selecciona **"App registrations"**
   - Click en **"+ New registration"**

4. **Configurar la aplicación**
   - **Name**: `Azure Advisor Reports API` (o el nombre que prefieras)
   - **Supported account types**: Selecciona **"Accounts in this organizational directory only"**
   - **Redirect URI**: Déjalo en blanco (no es necesario)
   - Click en **"Register"**

5. **Guardar información importante**

   Después de crear la app, verás la página de Overview. **Copia y guarda** estos valores:

   ```
   📝 Application (client) ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   📝 Directory (tenant) ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ```

### Paso 2: Crear Client Secret

1. **Ir a Certificates & secrets**
   - En el menú lateral de tu App Registration, selecciona **"Certificates & secrets"**

2. **Crear nuevo secret**
   - Click en **"+ New client secret"**
   - **Description**: `Advisor Reports API Key`
   - **Expires**: Selecciona **"24 months"** (o según tu política de seguridad)
   - Click en **"Add"**

3. **Guardar el Client Secret**

   ⚠️ **IMPORTANTE**: Copia el valor del secret **INMEDIATAMENTE**. No podrás verlo después.

   ```
   🔐 Client Secret (Value): xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### Paso 3: Obtener Subscription ID

1. **Ir a Subscriptions**
   - En el buscador superior del portal, escribe **"Subscriptions"**
   - Selecciona el servicio **"Subscriptions"**

2. **Seleccionar tu suscripción**
   - Click en la suscripción que deseas monitorear
   - Copia el **Subscription ID**

   ```
   📝 Subscription ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ```

### Paso 4: Asignar Permisos

1. **Ir a Access Control (IAM)**
   - Dentro de tu suscripción, selecciona **"Access control (IAM)"** en el menú lateral

2. **Agregar rol**
   - Click en **"+ Add"** → **"Add role assignment"**

3. **Seleccionar rol**
   - En la pestaña **"Role"**, busca y selecciona **"Reader"**
   - Click en **"Next"**

4. **Asignar a la aplicación**
   - En la pestaña **"Members"**:
     - Selecciona **"User, group, or service principal"**
     - Click en **"+ Select members"**
     - Busca el nombre de tu App Registration: `Azure Advisor Reports API`
     - Selecciónala y click en **"Select"**
   - Click en **"Review + assign"**
   - Click en **"Review + assign"** nuevamente para confirmar

### ✅ Resumen de Credenciales

Al finalizar esta parte, debes tener estos 4 valores:

```plaintext
┌─────────────────────────────────────────────────────────────┐
│ CREDENCIALES DE AZURE                                       │
├─────────────────────────────────────────────────────────────┤
│ 1. Tenant ID:        xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  │
│ 2. Subscription ID:  xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  │
│ 3. Client ID:        xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  │
│ 4. Client Secret:    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx      │
└─────────────────────────────────────────────────────────────┘
```

⚠️ **Guarda estos valores de forma segura**. Los necesitarás para el siguiente paso.

---

## Parte 2: Configuración en la Aplicación

### Paso 1: Acceder a la Aplicación

1. Inicia sesión en **Azure Advisor Reports**
2. Navega a la sección **"Clients"** en el menú lateral

### Paso 2: Crear o Seleccionar Cliente

#### Opción A: Crear Nuevo Cliente

1. Click en **"Add Client"**
2. Completa la información del cliente:
   - **Company Name**: Nombre de la empresa
   - **Industry**: Selecciona la industria
   - **Contact Email**: Email del contacto principal
   - **Contact Phone**: (Opcional) Teléfono
   - **Status**: Active
3. Click en **"Create Client"**

#### Opción B: Usar Cliente Existente

1. En la lista de clientes, click en el nombre del cliente

### Paso 3: Configurar Azure Subscription

1. **Ir a la página de detalles del cliente**
   - Verás una sección llamada **"Azure Subscriptions"**

2. **Agregar nueva subscription**
   - Click en el botón **"Add Subscription"**

3. **Completar el formulario**

   Ingresa las credenciales que obtuviste en la Parte 1:

   | Campo | Valor | Ejemplo |
   |-------|-------|---------|
   | **Name** | Nombre descriptivo | "Production - Contoso Corp" |
   | **Subscription ID** | ID de la suscripción Azure | `a1b2c3d4-e5f6-...` |
   | **Tenant ID** | ID del directorio Azure | `a1b2c3d4-e5f6-...` |
   | **Client ID** | Application ID del App Registration | `a1b2c3d4-e5f6-...` |
   | **Client Secret** | Secret value que copiaste | `xxxxxxxxxxxxxxxx` |

4. **Guardar configuración**
   - Click en **"Submit"** o **"Add"**

5. **Verificar conexión (opcional)**
   - Después de guardar, puedes hacer click en el botón **"Sync Now"** (icono de refresh)
   - Si todo está correcto, verás el status cambiar a **"Success"**

### ✅ Configuración Completada

Tu cliente ahora está configurado para generar reportes automáticamente desde Azure API.

---

## Parte 3: Generar Reportes

### Opción 1: Generar Reporte desde la Página del Cliente

1. **Navegar al cliente**
   - Ir a **Clients** → Seleccionar el cliente configurado

2. **Generar reporte**
   - Scroll down hasta la sección **"Reports History"**
   - Click en **"Generate Report"**
   - Serás redirigido a la página de reportes

### Opción 2: Generar Reporte desde la Página Reports

#### Paso 1: Seleccionar Cliente

1. Ir a la sección **"Reports"** en el menú lateral
2. Click en **"Generate New Report"** (si está visible) o sigue los pasos del wizard
3. Selecciona el **cliente** de la lista
4. Click en **"Next"** o **"Continue"**

#### Paso 2: Seleccionar Data Source

1. Verás dos opciones:
   - **CSV Upload**: Subir archivo CSV manualmente
   - **Azure API**: Conexión directa con Azure ✅

2. Selecciona **"Azure API"**
3. Click en **"Next"** o **"Continue"**

#### Paso 3: Seleccionar Azure Subscription

1. Verás un dropdown con las subscriptions configuradas para este cliente
2. Selecciona la subscription que deseas analizar
3. **(Opcional)** Aplica filtros:
   - **Category**: Cost, Security, Performance, etc.
   - **Impact**: High, Medium, Low
   - **Resource Group**: Filtrar por grupo específico

4. Click en **"Continue to Report Type"**

#### Paso 4: Seleccionar Tipo de Reporte

Selecciona el tipo de reporte que necesitas:

- **📊 Detailed Report**: Reporte completo con todas las recomendaciones
- **📋 Executive Summary**: Resumen ejecutivo para stakeholders
- **💰 Cost Optimization**: Enfocado en ahorro de costos
- **🔒 Security Assessment**: Enfocado en seguridad
- **⚙️ Operational Excellence**: Enfocado en operaciones

#### Paso 5: Generar Reporte

1. Click en **"Generate Report"**
2. El reporte comenzará a procesarse
3. Verás un mensaje: **"Report creation initiated from Azure API!"**

### Visualizar el Reporte

1. **Estado del reporte**
   - El reporte aparecerá en la lista con estado **"Processing"** o **"Generating"**
   - La página se actualiza automáticamente cada 5 segundos

2. **Reporte completado**
   - Cuando el estado cambie a **"Completed"**, verás los botones:
     - **"View Report"**: Ver el reporte HTML en el navegador
     - **"Generate PDF"**: (Opcional) Generar versión PDF
     - **"Download PDF"**: Descargar el PDF (si ya fue generado)

3. **Ver y compartir**
   - Click en **"View Report"** para abrir el reporte en una nueva pestaña
   - Usa Ctrl+P (Cmd+P en Mac) para imprimir o guardar como PDF desde el navegador

---

## 📊 Ventajas de Usar Azure API vs CSV

| Característica | Azure API ✅ | CSV Upload |
|----------------|-------------|-----------|
| **Automatización** | Automático, datos en tiempo real | Manual, requiere exportar |
| **Actualización** | Siempre actualizado | Solo al momento de exportar |
| **Facilidad** | Un click | Varios pasos |
| **Frecuencia** | Sin límites | Requiere nuevo CSV cada vez |
| **Datos históricos** | Mantiene historial | Solo snapshot |

---

## Solución de Problemas

### ❌ Error: "Failed to initiate sync"

**Causas posibles:**
- Credenciales incorrectas
- Service Principal sin permisos
- Subscription ID incorrecto

**Solución:**
1. Verificar que las 4 credenciales estén correctas
2. Confirmar que el Service Principal tiene rol **"Reader"** en la suscripción
3. Verificar que el Service Principal no esté expirado (check Client Secret expiration)

### ❌ Error: "No active Azure subscriptions configured"

**Causa:**
No has configurado ninguna Azure subscription para este cliente.

**Solución:**
1. Ir a la página de detalles del cliente
2. Agregar una Azure subscription (ver Parte 2, Paso 3)

### ❌ Error: "Connection test failed"

**Causas posibles:**
- Tenant ID incorrecto
- Client Secret inválido o expirado
- Problemas de red

**Solución:**
1. Re-crear el Client Secret en Azure Portal
2. Actualizar la subscription en la aplicación con el nuevo secret
3. Volver a intentar

### ⏱️ El reporte se queda en "Processing"

**Causa:**
Puede haber un problema con el worker de Celery o la suscripción tiene muchas recomendaciones.

**Solución:**
1. Esperar 2-3 minutos (reportes grandes pueden tardar)
2. Refrescar la página
3. Si persiste después de 5 minutos, contactar al administrador

### 🔐 ¿Cuánto tiempo dura el Client Secret?

- Los secrets expiran según la configuración (generalmente 24 meses)
- Cuando expire, deberás:
  1. Crear un nuevo secret en Azure Portal
  2. Actualizar la subscription en la aplicación
  3. No es necesario crear un nuevo App Registration

---

## 🔒 Mejores Prácticas de Seguridad

1. **Rotar secrets regularmente**
   - Crea un recordatorio para renovar el Client Secret antes de que expire

2. **Principio de menor privilegio**
   - El rol **"Reader"** es suficiente
   - No uses roles como "Contributor" o "Owner" innecesariamente

3. **Monitorear accesos**
   - Revisa periódicamente los logs de Sign-ins en Azure AD
   - Verifica que solo usuarios autorizados tengan acceso

4. **Un Service Principal por cliente**
   - Es recomendable crear un Service Principal diferente para cada cliente
   - Esto facilita la auditoría y revocación de accesos

5. **Documentar configuraciones**
   - Mantén un registro de qué Service Principal corresponde a qué cliente
   - Documenta las fechas de expiración de secrets

---

## 📞 Soporte

Si encuentras problemas no listados en esta guía:

1. **Contacta al administrador de la aplicación**
2. **Revisa los logs** en la sección Analytics (si tienes permisos)
3. **Verifica la configuración** en Azure Portal

---

## 📚 Recursos Adicionales

- [Documentación de Azure App Registrations](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Azure Advisor Documentation](https://learn.microsoft.com/en-us/azure/advisor/)
- [Service Principal Best Practices](https://learn.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal)

---

**Versión de la guía**: 1.0
**Última actualización**: 20 de noviembre de 2025
**Aplicación**: Azure Advisor Reports v2.0.15

---

*¿Tienes sugerencias para mejorar esta guía? Contacta al equipo de desarrollo.*
