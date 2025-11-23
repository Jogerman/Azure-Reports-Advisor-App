# Phase 3 Quick Start Guide

## What Was Implemented

Phase 3 added comprehensive REST API endpoints for Azure subscription management and dual data source report creation.

### Key Features

✅ **Azure Subscription Management** - CRUD + 4 custom actions (test-connection, statistics, sync-now, reports)
✅ **Dual Data Source Reports** - Create reports from CSV OR Azure API (XOR validation)
✅ **API Documentation** - Swagger UI at `/api/docs/`
✅ **55 Comprehensive Tests** - Full coverage of all endpoints
✅ **Security** - Encryption, authentication, ownership validation

---

## Quick Test Commands

### Run All Phase 3 Tests

```bash
cd /path/to/azure_advisor_reports

# Run Azure Integration tests (31 tests)
pytest apps/azure_integration/tests/test_views.py -v

# Run Report tests (24 tests)
pytest apps/reports/tests/test_report_views.py -v

# Run with coverage
pytest apps/azure_integration/tests/test_views.py \
       apps/reports/tests/test_report_views.py \
       --cov=apps.azure_integration.views \
       --cov=apps.reports.views \
       --cov-report=html
```

---

## API Endpoints Quick Reference

### Azure Subscriptions

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/azure/subscriptions/` | List subscriptions |
| POST | `/api/v1/azure/subscriptions/` | Create subscription |
| GET | `/api/v1/azure/subscriptions/{id}/` | Get details |
| PATCH | `/api/v1/azure/subscriptions/{id}/` | Update subscription |
| DELETE | `/api/v1/azure/subscriptions/{id}/` | Soft delete |
| POST | `/api/v1/azure/subscriptions/{id}/test-connection/` | Test Azure connection |
| GET | `/api/v1/azure/subscriptions/{id}/statistics/` | Get Advisor stats |
| POST | `/api/v1/azure/subscriptions/{id}/sync-now/` | Force refresh |
| GET | `/api/v1/azure/subscriptions/{id}/reports/` | List reports |

### Reports (Enhanced)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/reports/` | Create report (CSV or Azure API) |
| GET | `/api/v1/reports/` | List reports |
| GET | `/api/v1/reports/{id}/` | Get report details |
| GET | `/api/v1/reports/data-source-stats/` | Data source analytics |

---

## Example: Create Azure Subscription

```bash
curl -X POST http://localhost:8000/api/v1/azure/subscriptions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Subscription",
    "subscription_id": "12345678-1234-1234-1234-123456789012",
    "tenant_id": "87654321-4321-4321-4321-210987654321",
    "client_id": "abcdef12-ab12-ab12-ab12-abcdef123456",
    "client_secret": "your-secret-key-min-20-chars",
    "is_active": true
  }'
```

---

## Example: Create Report from CSV

```bash
curl -X POST http://localhost:8000/api/v1/reports/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "client_id=CLIENT_UUID" \
  -F "report_type=detailed" \
  -F "data_source=csv" \
  -F "csv_file=@/path/to/report.csv"
```

---

## Example: Create Report from Azure API

```bash
curl -X POST http://localhost:8000/api/v1/reports/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "CLIENT_UUID",
    "report_type": "cost",
    "data_source": "azure_api",
    "azure_subscription": "SUBSCRIPTION_UUID",
    "filters": {
      "category": "Cost",
      "impact": "High"
    }
  }'
```

---

## Test Azure Connection

```bash
curl -X POST http://localhost:8000/api/v1/azure/subscriptions/SUB_UUID/test-connection/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Get Azure Statistics

```bash
curl -X GET http://localhost:8000/api/v1/azure/subscriptions/SUB_UUID/statistics/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Interactive API Testing

1. Start the server: `python manage.py runserver`
2. Navigate to: `http://localhost:8000/api/docs/`
3. Click "Authorize" and enter JWT token
4. Try any endpoint interactively!

---

## Files Created/Modified

### New Test Files
- `/apps/azure_integration/tests/test_views.py` - 31 tests
- `/apps/reports/tests/test_report_views.py` - 24 tests

### Existing Implementation (Already Complete)
- `/apps/azure_integration/views.py` - AzureSubscriptionViewSet
- `/apps/azure_integration/permissions.py` - Permission classes
- `/apps/reports/views.py` - ReportViewSet (enhanced)
- `/apps/reports/serializers.py` - ReportCreateSerializer
- `/azure_advisor_reports/urls.py` - API docs routes

---

## Security Features

✅ **Encryption** - Client secrets encrypted with Fernet
✅ **Authentication** - JWT required for all endpoints
✅ **Authorization** - Users only access their own subscriptions
✅ **Validation** - XOR constraint (CSV OR Azure, not both)
✅ **No Leaks** - Sensitive data never in responses

---

## Common Scenarios

### Scenario 1: Add Azure Subscription
1. POST `/api/v1/azure/subscriptions/` with credentials
2. POST `/api/v1/azure/subscriptions/{id}/test-connection/` to verify
3. GET `/api/v1/azure/subscriptions/{id}/statistics/` to see recommendations

### Scenario 2: Create Azure API Report
1. Have an active Azure subscription (from Scenario 1)
2. POST `/api/v1/reports/` with `data_source=azure_api`
3. Task automatically fetches recommendations from Azure
4. GET `/api/v1/reports/{id}/` to check status

### Scenario 3: Create CSV Report (Traditional)
1. POST `/api/v1/reports/` with `data_source=csv` and file
2. Task automatically processes CSV
3. GET `/api/v1/reports/{id}/` to check status

---

## Troubleshooting

**403 Forbidden when accessing subscription?**
- Check you're the owner of the subscription
- Users can only access their own subscriptions

**400 Bad Request when creating report?**
- Check XOR validation: provide either CSV OR Azure subscription, not both
- Ensure Azure subscription is active
- Validate filter values (category, impact)

**401 Unauthorized?**
- Check JWT token is valid and not expired
- Include header: `Authorization: Bearer TOKEN`

---

## Next Steps

1. **Run Tests** - Verify all 55 tests pass
2. **Try Swagger UI** - Interactive API exploration
3. **Test Endpoints** - Use curl or Postman
4. **Review Completion Report** - See full documentation

For detailed information, see: `PHASE_3_REST_API_COMPLETION_REPORT.md`
