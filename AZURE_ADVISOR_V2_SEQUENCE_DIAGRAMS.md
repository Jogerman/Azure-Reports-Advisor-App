# Azure Advisor Reports v2.0 - Diagramas de Secuencia

**Documento complementario a la Arquitectura v2.0**

---

## 1. Flujo Completo: Creación de Reporte vía Azure API

```
┌────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐     ┌──────────┐     ┌──────────────┐
│ User   │     │ Frontend │     │ Backend  │     │   Celery   │     │  Azure   │     │  Database    │
│(Browser)│     │  (React) │     │  (Django)│     │  Worker    │     │   API    │     │ (PostgreSQL) │
└───┬────┘     └────┬─────┘     └────┬─────┘     └─────┬──────┘     └────┬─────┘     └──────┬───────┘
    │                │                │                 │                  │                   │
    │ 1. Click      │                │                 │                  │                   │
    │"Create Report"│                │                 │                  │                   │
    ├──────────────>│                │                 │                  │                   │
    │                │                │                 │                  │                   │
    │ 2. Open Modal │                │                 │                  │                   │
    │ & Select      │                │                 │                  │                   │
    │"Fetch from    │                │                 │                  │                   │
    │ Azure"        │                │                 │                  │                   │
    │<──────────────┤                │                 │                  │                   │
    │                │                │                 │                  │                   │
    │ 3. Fill Form: │                │                 │                  │                   │
    │ - Client      │                │                 │                  │                   │
    │ - Subscription│                │                 │                  │                   │
    │ - Report Type │                │                 │                  │                   │
    ├──────────────>│                │                 │                  │                   │
    │                │                │                 │                  │                   │
    │                │ 4. POST /api/reports/           │                  │                   │
    │                │ {                                │                  │                   │
    │                │   "client": "uuid",             │                  │                   │
    │                │   "source": "azure_api",        │                  │                   │
    │                │   "azure_subscription": "uuid", │                  │                   │
    │                │   "report_type": "detailed"     │                  │                   │
    │                │ }                                │                  │                   │
    │                ├───────────────>│                 │                  │                   │
    │                │                │                 │                  │                   │
    │                │                │ 5. Validate request               │                   │
    │                │                │ - Check subscription exists       │                   │
    │                │                │ - Check subscription is active    │                   │
    │                │                ├────────────────────────────────────────────────────────>│
    │                │                │                 │                  │ SELECT * FROM     │
    │                │                │                 │                  │ azure_subscriptions│
    │                │                │<────────────────────────────────────────────────────────┤
    │                │                │                 │                  │                   │
    │                │                │ 6. Create Report instance         │                   │
    │                │                │ - status = 'pending'              │                   │
    │                │                │ - source = 'azure_api'            │                   │
    │                │                ├────────────────────────────────────────────────────────>│
    │                │                │                 │                  │ INSERT INTO       │
    │                │                │                 │                  │ reports           │
    │                │                │<────────────────────────────────────────────────────────┤
    │                │                │                 │                  │                   │
    │                │                │ 7. Dispatch Celery task           │                   │
    │                │                │ fetch_azure_advisor_              │                   │
    │                │                │ recommendations.delay(report_id)  │                   │
    │                │                ├────────────────>│                  │                   │
    │                │                │                 │                  │                   │
    │                │ 8. Return 201 Created           │                  │                   │
    │                │ { "id": "...", "status":        │                  │                   │
    │                │   "pending" }  │                 │                  │                   │
    │                │<───────────────┤                 │                  │                   │
    │                │                │                 │                  │                   │
    │ 9. Show       │                │                 │                  │                   │
    │ "Processing..." │                │                 │                  │                   │
    │ notification   │                │                 │                  │                   │
    │<──────────────┤                 │                 │                  │                   │
    │                │                │                 │                  │                   │
    │                │                │                 │ 10. Task starts  │                   │
    │                │                │                 │ - Get Report     │                   │
    │                │                │                 ├──────────────────────────────────────>│
    │                │                │                 │                  │ SELECT * FROM     │
    │                │                │                 │                  │ reports           │
    │                │                │                 │<──────────────────────────────────────┤
    │                │                │                 │                  │                   │
    │                │                │                 │ 11. Get Azure Subscription           │
    │                │                │                 │ - Decrypt credentials                │
    │                │                │                 ├──────────────────────────────────────>│
    │                │                │                 │<──────────────────────────────────────┤
    │                │                │                 │                  │                   │
    │                │                │                 │ 12. Update Report status             │
    │                │                │                 │ status = 'processing'                │
    │                │                │                 ├──────────────────────────────────────>│
    │                │                │                 │                  │ UPDATE reports    │
    │                │                │                 │<──────────────────────────────────────┤
    │                │                │                 │                  │                   │
    │                │                │                 │ 13. Initialize AzureAdvisorClient    │
    │                │                │                 │ - Create credential object           │
    │                │                │                 │ - Create Azure SDK client            │
    │                │                │                 │                  │                   │
    │                │                │                 │ 14. Call Azure Advisor API           │
    │                │                │                 │ GET /subscriptions/{id}/providers/   │
    │                │                │                 │ Microsoft.Advisor/recommendations    │
    │                │                │                 ├─────────────────>│                   │
    │                │                │                 │                  │ Authenticate      │
    │                │                │                 │                  │ with Service      │
    │                │                │                 │                  │ Principal         │
    │                │                │                 │                  │                   │
    │                │                │                 │                  │ Fetch             │
    │                │                │                 │                  │ recommendations   │
    │                │                │                 │<─────────────────┤                   │
    │                │                │                 │ 200 OK           │                   │
    │                │                │                 │ [recommendations]│                   │
    │                │                │                 │                  │                   │
    │                │                │                 │ 15. Transform Azure data             │
    │                │                │                 │ - Map categories │                   │
    │                │                │                 │ - Map impact     │                   │
    │                │                │                 │ - Extract savings│                   │
    │                │                │                 │ - Parse resource IDs                 │
    │                │                │                 │                  │                   │
    │                │                │                 │ 16. Bulk create Recommendations      │
    │                │                │                 │ (batch_size=1000)│                   │
    │                │                │                 ├──────────────────────────────────────>│
    │                │                │                 │                  │ INSERT INTO       │
    │                │                │                 │                  │ recommendations   │
    │                │                │                 │<──────────────────────────────────────┤
    │                │                │                 │                  │                   │
    │                │                │                 │ 17. Calculate statistics             │
    │                │                │                 │ - Total recommendations              │
    │                │                │                 │ - Total savings  │                   │
    │                │                │                 │ - By category    │                   │
    │                │                │                 ├──────────────────────────────────────>│
    │                │                │                 │<──────────────────────────────────────┤
    │                │                │                 │                  │                   │
    │                │                │                 │ 18. Update Report                    │
    │                │                │                 │ - status = 'completed'               │
    │                │                │                 │ - analysis_data = stats              │
    │                │                │                 │ - fetch_completed_at = now           │
    │                │                │                 ├──────────────────────────────────────>│
    │                │                │                 │                  │ UPDATE reports    │
    │                │                │                 │<──────────────────────────────────────┤
    │                │                │                 │                  │                   │
    │                │                │                 │ 19. Mark subscription sync success   │
    │                │                │                 ├──────────────────────────────────────>│
    │                │                │                 │                  │ UPDATE azure_     │
    │                │                │                 │                  │ subscriptions     │
    │                │                │                 │<──────────────────────────────────────┤
    │                │                │                 │                  │                   │
    │                │                │                 │ 20. Dispatch generate_report task    │
    │                │                │                 │ generate_report.delay(report_id)     │
    │                │                │                 ├─────────────────>│                   │
    │                │                │                 │                  │ (HTML/PDF         │
    │                │                │                 │                  │  generation)      │
    │                │                │                 │                  │                   │
    │ 21. Frontend  │                │                 │                  │                   │
    │ polls status  │                │                 │                  │                   │
    │ GET /api/     │                │                 │                  │                   │
    │ reports/{id}  │                │                 │                  │                   │
    ├──────────────>│                │                 │                  │                   │
    │                ├───────────────>│                 │                  │                   │
    │                │                ├────────────────────────────────────────────────────────>│
    │                │                │<────────────────────────────────────────────────────────┤
    │                │<───────────────┤                 │                  │                   │
    │ { "status":    │                │                 │                  │                   │
    │   "completed" }│                │                 │                  │                   │
    │<──────────────┤                 │                 │                  │                   │
    │                │                │                 │                  │                   │
    │ 22. Redirect  │                │                 │                  │                   │
    │ to Report     │                │                 │                  │                   │
    │ Details Page  │                │                 │                  │                   │
    │                │                │                 │                  │                   │
```

---

## 2. Flujo: Agregar Azure Subscription con Validación

```
┌────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐     ┌──────────┐
│ User   │     │ Frontend │     │ Backend  │     │   Celery   │     │  Azure   │
└───┬────┘     └────┬─────┘     └────┬─────┘     └─────┬──────┘     └────┬─────┘
    │                │                │                 │                  │
    │ 1. Navigate to│                │                 │                  │
    │ Client Settings│                │                 │                  │
    ├──────────────>│                │                 │                  │
    │                │                │                 │                  │
    │ 2. Click      │                │                 │                  │
    │"Add Azure     │                │                 │                  │
    │ Subscription" │                │                 │                  │
    ├──────────────>│                │                 │                  │
    │                │                │                 │                  │
    │ 3. Fill Form: │                │                 │                  │
    │ - Subscription Name             │                 │                  │
    │ - Subscription ID               │                 │                  │
    │ - Tenant ID   │                │                 │                  │
    │ - Client ID   │                │                 │                  │
    │ - Client Secret │                │                 │                  │
    ├──────────────>│                │                 │                  │
    │                │                │                 │                  │
    │                │ 4. POST /api/azure-subscriptions/                  │
    │                ├───────────────>│                 │                  │
    │                │                │                 │                  │
    │                │                │ 5. Validate GUIDs format          │
    │                │                │ - subscription_id is valid UUID   │
    │                │                │ - tenant_id is valid UUID         │
    │                │                │                 │                  │
    │                │                │ 6. Encrypt credentials             │
    │                │                │ - Encrypt client_id                │
    │                │                │ - Encrypt client_secret            │
    │                │                │                 │                  │
    │                │                │ 7. Create AzureSubscription        │
    │                │                │ - status = 'pending'               │
    │                │                │ - Save to database                 │
    │                │                │                 │                  │
    │                │                │ 8. Dispatch validation task        │
    │                │                │ validate_azure_subscription.       │
    │                │                │ delay(subscription_id)             │
    │                │                ├────────────────>│                  │
    │                │                │                 │                  │
    │                │ 9. Return 201 Created           │                  │
    │                │<───────────────┤                 │                  │
    │                │                │                 │                  │
    │ 10. Show      │                │                 │                  │
    │ "Validating..." │                │                 │                  │
    │<──────────────┤                 │                 │                  │
    │                │                │                 │                  │
    │                │                │                 │ 11. Task starts  │
    │                │                │                 │ - Get AzureSubscription│
    │                │                │                 │ - Decrypt credentials  │
    │                │                │                 │                  │
    │                │                │                 │ 12. Initialize   │
    │                │                │                 │ AzureAdvisorClient     │
    │                │                │                 │                  │
    │                │                │                 │ 13. Test API call│
    │                │                │                 │ (list recommendations, │
    │                │                │                 │  limit=1)        │
    │                │                │                 ├─────────────────>│
    │                │                │                 │                  │
    │                │                │                 │                  │ Authenticate
    │                │                │                 │                  │ with Azure AD
    │                │                │                 │                  │
    │                │                │                 │<─────────────────┤
    │                │                │                 │ 200 OK / 401 / 403│
    │                │                │                 │                  │
    │                │                │                 │ 14. Process result│
    │                │                │                 │                  │
    │                │                │                 ├─ If Success ─────┤
    │                │                │                 │ - Set status='active'│
    │                │                │                 │ - Set validated_at│
    │                │                │                 │                  │
    │                │                │                 ├─ If 401/403 ─────┤
    │                │                │                 │ - Set status='error'│
    │                │                │                 │ - Save error message│
    │                │                │                 │                  │
    │                │                │                 │ 15. Update database│
    │                │                │                 │                  │
    │ 16. Frontend  │                │                 │                  │
    │ polls status  │                │                 │                  │
    │ GET /api/azure-subscriptions/{id}/health/        │                  │
    ├──────────────>│                │                 │                  │
    │                ├───────────────>│                 │                  │
    │                │<───────────────┤                 │                  │
    │ {             │                │                 │                  │
    │  "status": "active",            │                 │                  │
    │  "health_status": "healthy"     │                 │                  │
    │ }              │                │                 │                  │
    │<──────────────┤                 │                 │                  │
    │                │                │                 │                  │
    │ 17. Show      │                │                 │                  │
    │ success toast │                │                 │                  │
    │                │                │                 │                  │
```

---

## 3. Flujo: Scheduled Auto-Fetch (Celery Beat)

```
┌────────────┐     ┌──────────┐     ┌────────────┐     ┌──────────┐
│Celery Beat │     │ Database │     │   Celery   │     │  Azure   │
│ (Scheduler)│     │          │     │  Worker    │     │   API    │
└─────┬──────┘     └────┬─────┘     └─────┬──────┘     └────┬─────┘
      │                 │                 │                  │
      │ Daily at 2:00 AM│                 │                  │
      │                 │                 │                  │
      │ 1. Trigger scheduled_fetch_azure_recommendations     │
      │ task            │                 │                  │
      ├─────────────────────────────────>│                  │
      │                 │                 │                  │
      │                 │                 │ 2. Query active subscriptions│
      │                 │                 │ WHERE is_active=true         │
      │                 │                 │ AND auto_fetch_enabled=true  │
      │                 │                 │ AND needs_fetch=true         │
      │                 │                 ├─────────────────>│
      │                 │<────────────────┤                  │
      │                 │ [List of subscriptions]            │
      │                 │                 │                  │
      │                 │                 │ 3. For each subscription:    │
      │                 │                 │                  │
      │                 │                 │ 4. Create background Report  │
      │                 │                 ├─────────────────>│
      │                 │<────────────────┤                  │
      │                 │ Report created  │                  │
      │                 │                 │                  │
      │                 │                 │ 5. Dispatch fetch task       │
      │                 │                 │ fetch_azure_advisor_         │
      │                 │                 │ recommendations.delay(id)    │
      │                 │                 ├─────────────────>│
      │                 │                 │                  │ (Celery Queue)
      │                 │                 │                  │
      │                 │                 │                  │ 6. Process as
      │                 │                 │                  │ normal fetch
      │                 │                 │                  │ (see Diagram 1)
      │                 │                 │                  │
      │                 │                 │ 7. Log completion│
      │                 │                 │ "Processed 5 subscriptions"  │
      │                 │                 │                  │
```

---

## 4. Flujo: Error Handling y Retry Logic

```
┌────────────┐     ┌──────────┐     ┌──────────┐
│   Celery   │     │ Database │     │  Azure   │
│  Worker    │     │          │     │   API    │
└─────┬──────┘     └────┬─────┘     └────┬─────┘
      │                 │                 │
      │ 1. Fetch task starts              │
      │                 │                 │
      │ 2. Call Azure API                 │
      ├────────────────────────────────────>│
      │                 │                 │
      │                 │                 │ ERROR
      │                 │                 │ (Network timeout,
      │                 │                 │  Rate limit, etc.)
      │<────────────────────────────────────┤
      │ Error: 429 Too Many Requests      │
      │                 │                 │
      │ 3. Log error    │                 │
      │                 │                 │
      │ 4. Check retry count              │
      │ (current: 0 < max: 3)             │
      │                 │                 │
      │ 5. Update Report│                 │
      │ - retry_count += 1                │
      ├────────────────>│                 │
      │                 │ UPDATE reports  │
      │<────────────────┤                 │
      │                 │                 │
      │ 6. Schedule retry with exponential│
      │ backoff: 120s * (retry_count + 1) │
      │ = 240 seconds   │                 │
      │                 │                 │
      │ ... wait 240 seconds ...          │
      │                 │                 │
      │ 7. Retry task   │                 │
      ├────────────────────────────────────>│
      │                 │                 │
      │                 │                 │ SUCCESS
      │<────────────────────────────────────┤
      │ Recommendations │                 │
      │                 │                 │
      │ 8. Process normally               │
      │                 │                 │
      │ 9. Update Report│                 │
      │ - status = 'completed'            │
      │ - retry_count reset               │
      ├────────────────>│                 │
      │                 │                 │
      │                 │                 │
      │ --- OR (if max retries exceeded) ─│
      │                 │                 │
      │ 10. Final failure                 │
      │ - status = 'failed'               │
      │ - error_message saved             │
      ├────────────────>│                 │
      │                 │                 │
      │ 11. Mark subscription as error    │
      │ - consecutive_failures += 1       │
      │ - If >= 5: disable auto_fetch     │
      ├────────────────>│                 │
      │                 │                 │
```

---

## 5. Flujo: Rate Limiting

```
┌────────────┐     ┌──────────┐     ┌──────────┐
│   Celery   │     │  Redis   │     │  Azure   │
│  Worker    │     │  Cache   │     │   API    │
└─────┬──────┘     └────┬─────┘     └────┬─────┘
      │                 │                 │
      │ 1. About to call Azure API        │
      │                 │                 │
      │ 2. Check rate limit               │
      │ GET rate_limit_key                │
      ├────────────────>│                 │
      │ Current count: 95/100             │
      │<────────────────┤                 │
      │                 │                 │
      │ 3. Check: 95 < 100 ✓              │
      │ OK to proceed   │                 │
      │                 │                 │
      │ 4. Increment counter              │
      │ INCR rate_limit_key               │
      ├────────────────>│                 │
      │<────────────────┤                 │
      │ New count: 96   │                 │
      │                 │                 │
      │ 5. Call Azure API                 │
      ├────────────────────────────────────>│
      │<────────────────────────────────────┤
      │ Success         │                 │
      │                 │                 │
      │ --- Later call (rate limit hit) ───│
      │                 │                 │
      │ 6. Check rate limit               │
      ├────────────────>│                 │
      │ Current count: 100/100            │
      │<────────────────┤                 │
      │                 │                 │
      │ 7. Check: 100 >= 100 ✗            │
      │ Rate limit reached                │
      │                 │                 │
      │ 8. Get TTL of key                 │
      │ TTL rate_limit_key                │
      ├────────────────>│                 │
      │ TTL: 1200 seconds                 │
      │<────────────────┤                 │
      │                 │                 │
      │ 9. Sleep(1200)  │                 │
      │ Wait 20 minutes │                 │
      │                 │                 │
      │ ... wait ...    │                 │
      │                 │                 │
      │ 10. Retry call  │                 │
      │ (counter reset after TTL)         │
      ├────────────────────────────────────>│
      │<────────────────────────────────────┤
      │ Success         │                 │
```

---

## 6. Comparación: CSV vs Azure API Flow

### CSV Upload Flow
```
User → Frontend → Upload CSV → Backend creates Report
  → Celery: process_csv_file
    → Parse CSV
    → Validate rows
    → Create Recommendations
    → Update Report (completed)
  → Celery: generate_report (HTML/PDF)
```

### Azure API Flow
```
User → Frontend → Select Azure Sub → Backend creates Report
  → Celery: fetch_azure_advisor_recommendations
    → Decrypt credentials
    → Authenticate with Azure
    → Call Azure Advisor API
    → Transform Azure data
    → Create Recommendations
    → Update Report (completed)
  → Celery: generate_report (HTML/PDF)
```

**Diferencias clave:**
- CSV: Synchronous file upload, local processing
- Azure API: Asynchronous API calls, external dependency
- CSV: No credential management
- Azure API: Encrypted credential storage
- CSV: One-time data snapshot
- Azure API: Can be scheduled for recurring fetches

---

## Conclusión

Estos diagramas de secuencia ilustran los flujos principales de la integración v2.0:

1. **Flujo principal**: Creación de reporte desde Azure API
2. **Gestión de credenciales**: Agregar y validar Azure Subscriptions
3. **Automatización**: Scheduled fetches mediante Celery Beat
4. **Resiliencia**: Error handling y retry logic
5. **Performance**: Rate limiting para evitar throttling

Cada flujo está diseñado para ser robusto, escalable y seguro.
