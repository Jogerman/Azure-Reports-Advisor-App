# ⚡ Referencia Rápida: Azure API Reports

## 🎯 Configuración Azure (Una sola vez)

### 1. Crear App Registration
```
Portal Azure → Azure Active Directory → App registrations → + New registration
Name: "Azure Advisor Reports API"
```

### 2. Obtener Credenciales

| Campo | Ubicación |
|-------|-----------|
| **Tenant ID** | App Registration → Overview |
| **Client ID** | App Registration → Overview |
| **Client Secret** | App Registration → Certificates & secrets → + New client secret |
| **Subscription ID** | Subscriptions → [Tu suscripción] |

### 3. Asignar Permisos
```
Subscriptions → [Tu suscripción] → Access Control (IAM)
→ + Add role assignment
→ Role: Reader
→ Assign to: [Tu App Registration]
```

---

## 🚀 Configuración en la App

### 1. Crear/Seleccionar Cliente
```
Clients → Add Client o seleccionar existente
```

### 2. Agregar Azure Subscription
```
Client Details → Azure Subscriptions → Add Subscription
```

**Completar formulario:**
- Name: Nombre descriptivo
- Subscription ID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- Tenant ID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- Client ID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- Client Secret: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## 📊 Generar Reporte

### Flujo Rápido
```
Reports → Select Client → Azure API → Select Subscription → Select Report Type → Generate
```

### Tipos de Reporte
- **Detailed**: Completo con todas las recomendaciones
- **Executive**: Resumen ejecutivo
- **Cost**: Enfocado en ahorro de costos
- **Security**: Enfocado en seguridad
- **Operations**: Enfocado en operaciones

---

## 🔧 Troubleshooting

| Error | Solución |
|-------|----------|
| "Failed to initiate sync" | Verificar credenciales y permisos Reader |
| "No subscriptions configured" | Agregar Azure subscription al cliente |
| "Connection test failed" | Verificar Tenant ID y Client Secret |
| Processing muy lento | Esperar 2-3 min, reportes grandes tardan más |

---

## ⚠️ Recordatorios

- ✅ Client Secret expira (generalmente 24 meses)
- ✅ Rol Reader es suficiente (no usar Contributor/Owner)
- ✅ Un Service Principal por cliente (recomendado)
- ✅ Guardar credenciales de forma segura

---

## 🔗 Ver Guía Completa

Para instrucciones detalladas paso a paso, consulta:
→ `GUIA_REPORTES_AZURE_API.md`

---

**v2.0.15** | Última actualización: 20 Nov 2025
