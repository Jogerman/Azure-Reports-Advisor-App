# Azure Advisor Reports v2.0 - Resumen Ejecutivo

**Para:** Stakeholders y Product Owners
**Fecha:** 2025-11-17
**Versión:** 2.0.0

---

## Visión General

Azure Advisor Reports v2.0 introduce **integración directa con Azure Advisor API**, permitiendo a los usuarios obtener recomendaciones de Azure automáticamente sin necesidad de descargar y subir archivos CSV manualmente.

---

## Problema Actual (v1.6.1)

```
Usuario → Descarga CSV desde Azure Portal
       → Sube CSV a la plataforma
       → Espera procesamiento
       → Visualiza reporte
```

**Pain Points:**
- Proceso manual y tedioso
- Requiere acceso al Azure Portal
- Datos pueden estar desactualizados
- Propenso a errores humanos
- No escalable para múltiples suscripciones

---

## Solución Propuesta (v2.0)

```
Usuario → Configura credenciales Azure una vez
       → Clic en "Fetch from Azure"
       → Espera procesamiento automático
       → Visualiza reporte actualizado
```

**Beneficios:**
- Automatización completa del proceso
- Datos siempre actualizados desde Azure
- Soporte para múltiples suscripciones
- Posibilidad de fetches programados (diarios, semanales)
- Mantiene compatibilidad con CSV (ambos flujos coexisten)

---

## Características Principales

### 1. Gestión de Azure Subscriptions

- Almacenamiento seguro de credenciales (Service Principal)
- Validación automática de permisos
- Health monitoring de conexiones
- Soporte multi-tenant (cada cliente gestiona sus propias suscripciones)

### 2. Integración con Azure Advisor API

- Autenticación mediante Azure AD Service Principal
- Fetching automático de recomendaciones
- Transformación de datos a formato interno
- Rate limiting y manejo de errores

### 3. Dual Source Support

Los usuarios pueden elegir:
- **Opción A:** Subir CSV manualmente (flujo existente)
- **Opción B:** Fetch automático desde Azure API (nuevo flujo)

Ambas opciones generan el mismo tipo de reporte.

### 4. Scheduled Fetching

- Configuración de fetches automáticos (diario, semanal, etc.)
- Background processing sin intervención del usuario
- Notificaciones cuando nuevos reportes están listos

---

## Arquitectura Técnica (High-Level)

```
┌─────────────────────────────────────────────────────────────┐
│                      REACT FRONTEND                         │
│  - Azure Subscription Manager                              │
│  - Source Selector (CSV vs Azure API)                      │
│  - Enhanced Report Creation                                │
└────────────────┬────────────────────────────────────────────┘
                 │ REST API
┌────────────────┴────────────────────────────────────────────┐
│                  DJANGO BACKEND                             │
│  - New App: azure_integration                              │
│  - AzureAdvisorClient (Azure SDK)                          │
│  - Encrypted Credential Storage                            │
│  - Enhanced Report Model                                   │
└────────────────┬────────────────────────────────────────────┘
                 │ Tasks
┌────────────────┴────────────────────────────────────────────┐
│                  CELERY WORKERS                             │
│  - fetch_azure_advisor_recommendations (NEW)               │
│  - validate_azure_subscription (NEW)                       │
│  - scheduled_fetch_azure_recommendations (NEW)             │
│  - process_csv_file (EXISTING)                             │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
   ┌────▼─────┐    ┌──────▼──────┐
   │PostgreSQL│    │Azure Advisor│
   │ Database │    │     API     │
   └──────────┘    └─────────────┘
```

---

## Seguridad

### Credenciales Azure

- **Encriptación:** Client ID y Client Secret se encriptan antes de almacenar en base de datos
- **Algoritmo:** Fernet symmetric encryption (estándar Python cryptography)
- **Key Management:** Derivado de Django SECRET_KEY
- **Acceso:** Solo usuarios autorizados pueden gestionar Azure Subscriptions

### Permisos Azure Requeridos

El Service Principal requiere el rol:
- **Advisor Reader** (recomendado) o **Reader** (más amplio)
- Scope: Nivel de suscripción

```bash
# Comando para asignar permisos
az role assignment create \
  --assignee <service-principal-id> \
  --role "Advisor Reader" \
  --scope "/subscriptions/{subscription-id}"
```

---

## Cambios en Modelos de Datos

### Nuevo Modelo: AzureSubscription

```python
{
  "id": "uuid",
  "client": "Client FK",
  "subscription_id": "Azure GUID",
  "subscription_name": "Production Subscription",
  "tenant_id": "Azure AD Tenant GUID",
  "client_id_encrypted": "binary",      # Encriptado
  "client_secret_encrypted": "binary",  # Encriptado
  "status": "active|error|pending",
  "is_active": true,
  "auto_fetch_enabled": true,
  "fetch_frequency_hours": 24,
  "last_sync_at": "2025-11-17T10:00:00Z",
  "health_status": "healthy|degraded|unhealthy"
}
```

### Cambios en Report Model

```python
# Nuevos campos
source: "csv" | "azure_api"
azure_subscription: FK to AzureSubscription (optional)
fetch_started_at: DateTime (for API source)
fetch_completed_at: DateTime (for API source)
```

### Cambios en Recommendation Model

```python
# Nuevos campos
azure_recommendation_id: String (Azure ID)
azure_recommendation_name: String
last_updated_by_azure: DateTime
suppression_ids: JSON Array
```

---

## Flujo de Usuario

### Setup Inicial (One-time)

1. Usuario navega a Client Settings
2. Clic en "Azure Subscriptions" tab
3. Clic en "Add Azure Subscription"
4. Proporciona:
   - Subscription Name (friendly name)
   - Subscription ID (GUID)
   - Tenant ID (GUID)
   - Client ID (Application ID)
   - Client Secret
5. Sistema valida credenciales automáticamente
6. Si exitoso, subscription queda "Active"

### Generación de Reporte (Recurring)

1. Usuario clic en "Create Report"
2. Selecciona source: **"Fetch from Azure"**
3. Selecciona Azure Subscription (del dropdown)
4. Selecciona Report Type (Detailed, Executive, etc.)
5. Clic en "Generate Report"
6. Sistema:
   - Llama a Azure Advisor API
   - Obtiene recomendaciones
   - Las procesa y almacena
   - Genera reporte HTML/PDF
7. Usuario recibe notificación cuando está listo
8. Usuario visualiza reporte

---

## Timeline de Implementación

| Fase | Duración | Tareas Clave | Entregables |
|------|----------|--------------|-------------|
| **Fase 1: Infraestructura** | 1-2 semanas | - Nueva app django<br>- Modelos de datos<br>- Sistema encriptación | Modelos funcionando |
| **Fase 2: Azure Client** | 1-2 semanas | - Azure SDK integration<br>- API client<br>- Rate limiting | Cliente Azure completo |
| **Fase 3: Backend** | 2 semanas | - API endpoints<br>- Celery tasks<br>- Dual routing | Backend completo |
| **Fase 4: Frontend** | 2 semanas | - UI components<br>- Azure sub manager<br>- Source selector | UI completa |
| **Fase 5: Testing** | 1 semana | - Unit tests<br>- Integration tests<br>- E2E tests | Test suite completa |
| **Fase 6: Deployment** | 1 semana | - Staging deploy<br>- UAT<br>- Production deploy | Sistema en producción |
| **TOTAL** | **8-10 semanas** | | **v2.0 Release** |

---

## Riesgos y Mitigaciones

### Riesgo 1: Azure API Rate Limits

**Descripción:** Azure limita número de requests por hora.

**Probabilidad:** Media

**Impacto:** Medio (fetches pueden fallar temporalmente)

**Mitigación:**
- Implementar rate limiting en cliente
- Caching de resultados (TTL 1 hora)
- Retry logic con exponential backoff
- Monitoreo de cuotas

### Riesgo 2: Complejidad de Credenciales

**Descripción:** Usuarios pueden tener dificultad configurando Service Principal.

**Probabilidad:** Alta (usuarios no técnicos)

**Impacto:** Medio (fricción en onboarding)

**Mitigación:**
- Documentación detallada con screenshots
- Video tutorial paso a paso
- Script automatizado para setup
- Soporte técnico dedicado

### Riesgo 3: Scope Creep

**Descripción:** Tentación de agregar features adicionales durante desarrollo.

**Probabilidad:** Media

**Impacto:** Alto (retrasos en timeline)

**Mitigación:**
- Definición clara de MVP
- Backlog separado para v2.1+
- Code review estricto
- Sprint planning disciplinado

### Riesgo 4: Breaking Changes en Azure API

**Descripción:** Azure depreca o cambia API sin aviso.

**Probabilidad:** Baja

**Impacto:** Alto (sistema puede dejar de funcionar)

**Mitigación:**
- Usar API version específica (2020-01-01)
- Monitoreo de Azure announcements
- Tests de integración automatizados
- Fallback a CSV si API falla

---

## Métricas de Éxito (KPIs)

### Adopción

- **Target:** 60% de clientes activos usan Azure API en 3 meses post-launch
- **Medición:** Ratio de reports generados con source='azure_api' vs 'csv'

### Performance

- **Target:** 95% de fetches completan en < 2 minutos
- **Medición:** Promedio de `fetch_completed_at - fetch_started_at`

### Reliability

- **Target:** 99% success rate en fetches
- **Medición:** Ratio de reports con status='completed' vs 'failed'

### User Satisfaction

- **Target:** Net Promoter Score (NPS) > 8/10
- **Medición:** Encuesta post-uso de nueva funcionalidad

### Time Savings

- **Target:** Reducir tiempo promedio de generación de reporte de 15 min a 3 min
- **Medición:** Análisis tiempo de usuario (manual upload vs API fetch)

---

## Costos Estimados

### Desarrollo

| Recurso | Tiempo | Costo |
|---------|--------|-------|
| Backend Developer | 6 semanas | €X,XXX |
| Frontend Developer | 4 semanas | €X,XXX |
| QA Engineer | 2 semanas | €X,XXX |
| DevOps | 1 semana | €X,XXX |
| **TOTAL** | | **€XX,XXX** |

### Operación (mensual)

| Concepto | Costo Mensual |
|----------|---------------|
| Azure API calls | Incluido en suscripción cliente |
| Redis (cache + broker) | Existente |
| PostgreSQL storage | +5% (nuevos modelos) |
| Celery workers | Existente |
| **TOTAL** | **Marginal** |

---

## ROI (Return on Investment)

### Beneficios Cuantificables

1. **Ahorro de tiempo usuario:**
   - Tiempo actual: 15 min/reporte (descarga CSV, upload, espera)
   - Tiempo nuevo: 3 min/reporte (seleccionar subscription, click)
   - Ahorro: 12 min/reporte
   - Si promedio 100 reportes/semana → **20 horas/semana ahorradas**

2. **Reducción de errores:**
   - Tasa de error CSV: ~5% (formato incorrecto, datos corruptos)
   - Tasa de error API: ~0.5% (solo failures Azure)
   - Mejora: 4.5% menos re-trabajos

3. **Incremento en uso:**
   - Barrera de entrada menor → Más reportes generados
   - Estimado: +30% en volumen de reportes
   - Más valor para clientes → Mayor retención

### Beneficios No Cuantificables

- Mejora en satisfacción de usuario
- Imagen de producto moderno
- Ventaja competitiva vs alternativas
- Foundation para futuras integraciones Azure (Cost Management, Security Center, etc.)

---

## Próximos Pasos

### Inmediatos (Semana 1-2)

1. **Aprobación stakeholders** de arquitectura propuesta
2. **Setup de entorno de desarrollo**
   - Branch feature/azure-api-integration
   - Azure test subscription para desarrollo
3. **Sprint Planning Fase 1**
   - Breakdodown de tareas
   - Asignación de recursos

### Corto Plazo (Semana 3-4)

4. **Inicio de desarrollo Fase 1**
   - Modelos de datos
   - Sistema de encriptación
5. **Documentación de onboarding**
   - Cómo crear Service Principal
   - Cómo asignar permisos

### Medio Plazo (Semana 5-8)

6. **Desarrollo Fases 2-4**
7. **Testing continuo**
8. **Demo a stakeholders** (sprint reviews)

### Largo Plazo (Semana 9-10)

9. **Deployment a staging**
10. **User Acceptance Testing**
11. **Production deployment**
12. **Monitoreo post-launch**

---

## Preguntas Frecuentes (FAQ)

### Q1: ¿Qué pasa si un cliente no quiere dar credenciales Azure?

**R:** El flujo de CSV seguirá disponible. La integración Azure API es opcional, no reemplaza el flujo existente.

### Q2: ¿Los datos de Azure quedan almacenados en nuestros servidores?

**R:** Sí, las recomendaciones se almacenan en PostgreSQL para generar reportes históricos. Las credenciales se almacenan encriptadas.

### Q3: ¿Qué pasa si Azure cambia su API?

**R:** Usamos versiones específicas de API (2020-01-01) que tienen garantía de backward compatibility. Monitoreamos deprecations activamente.

### Q4: ¿Funciona con Azure Government Cloud o Azure China?

**R:** En v2.0, solo soportamos Azure Public Cloud. Clouds soberanos serían v2.1+.

### Q5: ¿Puedo scheduled fetches para que se ejecuten automáticamente?

**R:** Sí, en la configuración de Azure Subscription puedes habilitar auto-fetch y definir frecuencia (diaria, semanal, mensual).

### Q6: ¿Qué permisos necesita el Service Principal?

**R:** Rol "Advisor Reader" a nivel de suscripción. Es read-only, no puede hacer cambios en recursos Azure.

### Q7: ¿Cuánto tiempo tarda un fetch desde Azure?

**R:** Típicamente 1-3 minutos, dependiendo del número de recomendaciones. Mucho más rápido que descarga/upload manual de CSV.

---

## Conclusión

Azure Advisor Reports v2.0 representa una evolución significativa de la plataforma, transformando un proceso manual en uno automatizado. La integración directa con Azure API proporciona:

- **Mayor eficiencia** para usuarios
- **Datos más actualizados** para mejores decisiones
- **Escalabilidad** para clientes con múltiples suscripciones
- **Foundation sólida** para futuras integraciones Azure

El proyecto está bien scoped, con riesgos identificados y mitigados, y un ROI claro tanto en ahorro de tiempo como en mejora de satisfacción de usuario.

**Recomendación:** Proceder con implementación según timeline propuesto.

---

**Documentos relacionados:**
- [Arquitectura Detallada](/Users/josegomez/Documents/Code/Azure-Reports-Advisor-App/AZURE_ADVISOR_V2_ARCHITECTURE.md)
- [Diagramas de Secuencia](/Users/josegomez/Documents/Code/Azure-Reports-Advisor-App/AZURE_ADVISOR_V2_SEQUENCE_DIAGRAMS.md)

**Preparado por:** Software Architecture Team
**Fecha:** 2025-11-17
