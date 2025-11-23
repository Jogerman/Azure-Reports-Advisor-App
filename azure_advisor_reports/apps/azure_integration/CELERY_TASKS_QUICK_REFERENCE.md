# Azure Integration Celery Tasks - Quick Reference

## Task Overview

| Task | Queue | Timeout | Retry | Purpose |
|------|-------|---------|-------|---------|
| `fetch_azure_recommendations` | `azure_api` | 10 min | 3x | Fetch recommendations from Azure API |
| `generate_azure_report` | `reports` | 20 min | 3x | Generate PDF/HTML reports |
| `test_azure_connection` | `azure_api` | 30 sec | 1x | Test Azure credentials |
| `sync_azure_statistics` | `azure_api` | 2 min | 0x | Sync dashboard statistics |

---

## Usage Examples

### Fetch Azure Recommendations

```python
from apps.azure_integration.tasks import fetch_azure_recommendations
from apps.reports.models import Report

# Create report
report = Report.objects.create(
    client=client,
    created_by=user,
    report_type='cost',
    data_source='azure_api',
    azure_subscription=subscription,
    status='pending',
    api_sync_metadata={
        'filters': {
            'category': 'Cost',    # Optional: Cost, Security, Performance, etc.
            'impact': 'High',      # Optional: High, Medium, Low
        }
    }
)

# Trigger async task
result = fetch_azure_recommendations.delay(str(report.id))

# Get task status
print(result.state)  # PENDING, SUCCESS, FAILURE, RETRY

# Get result (blocks until complete)
task_result = result.get(timeout=600)
print(task_result)
# {'status': 'success', 'report_id': '...', 'recommendations_count': 42}
```

### Generate Report

```python
from apps.azure_integration.tasks import generate_azure_report

# Generate PDF only
generate_azure_report.delay(str(report.id), format_type='pdf')

# Generate HTML only
generate_azure_report.delay(str(report.id), format_type='html')

# Generate both (default)
generate_azure_report.delay(str(report.id), format_type='both')
```

### Test Azure Connection

```python
from apps.azure_integration.tasks import test_azure_connection
from apps.azure_integration.models import AzureSubscription

# When user adds new subscription
subscription = AzureSubscription.objects.create(
    name='Production',
    subscription_id='12345678-1234-1234-1234-123456789012',
    tenant_id='...',
    client_id='...',
)
subscription.client_secret = 'secret-key'  # Auto-encrypted
subscription.save()

# Test connection
result = test_azure_connection.delay(str(subscription.id))
connection_test = result.get(timeout=30)

if connection_test['success']:
    print(f"✅ Connected to {connection_test['subscription_name']}")
else:
    print(f"❌ Connection failed: {connection_test['error_message']}")
```

### Sync Statistics

```python
from apps.azure_integration.tasks import sync_azure_statistics

# Sync statistics (cached for 1 hour)
result = sync_azure_statistics.delay(str(subscription.id))
stats = result.get(timeout=120)

print(f"Total: {stats['total_recommendations']}")
print(f"By Category: {stats['by_category']}")
print(f"By Impact: {stats['by_impact']}")
print(f"Savings: ${stats['total_potential_savings']} {stats['currency']}")
```

---

## Error Handling

### Task Result on Error

```python
try:
    result = fetch_azure_recommendations.delay(report_id)
    task_result = result.get(timeout=600)
except Exception as e:
    # Check report for error details
    report.refresh_from_db()
    print(f"Status: {report.status}")
    print(f"Error: {report.error_message}")
```

### Retry Behavior

| Error Type | Example | Retry? | Action |
|------------|---------|--------|--------|
| Authentication | Invalid client secret | ❌ No | Update credentials |
| API Error | Rate limit exceeded | ✅ Yes (3x) | Waits 60s, 120s, 180s |
| Connection | Network timeout | ✅ Yes (3x) | Waits 60s, 120s, 180s |
| Timeout | Task > 10 minutes | ❌ No | Check data volume |
| Not Found | Report deleted | ❌ No (Ignore) | Normal, user deleted |

---

## Status Flow

### Report Status

```
pending → processing → completed
   ↓          ↓
   ↓       failed
   ↓
cancelled
```

### Subscription Sync Status

```
never_synced → success
               ↓    ↑
            failed  ↓
               ↓────┘
            (retry to success)
```

---

## Monitoring

### Check Task Status

```python
# Get task by ID
from celery.result import AsyncResult
task = AsyncResult(task_id)

print(f"State: {task.state}")        # PENDING, SUCCESS, FAILURE
print(f"Ready: {task.ready()}")      # True if complete
print(f"Success: {task.successful()}")  # True if succeeded
print(f"Failed: {task.failed()}")    # True if failed

# Get result (if complete)
if task.ready():
    result = task.result
```

### Query Recent Tasks

```python
from apps.reports.models import Report

# Get reports in progress
in_progress = Report.objects.filter(
    status__in=['processing', 'generating']
)

# Get recent failures
failed = Report.objects.filter(
    status='failed',
    created_at__gte=timezone.now() - timedelta(hours=24)
)

# Get sync status
from apps.azure_integration.models import AzureSubscription
failed_syncs = AzureSubscription.objects.filter(sync_status='failed')
```

---

## Debugging

### Enable Debug Logging

```python
import logging
logging.getLogger('apps.azure_integration.tasks').setLevel(logging.DEBUG)
```

### Check Task Metadata

```python
report = Report.objects.get(id=report_id)

# Check sync metadata
print(report.api_sync_metadata)
# {
#     'filters': {...},
#     'requested_at': '2024-01-15T10:00:00Z',
#     'fetched_at': '2024-01-15T10:02:15Z',
#     'recommendations_count': 42,
#     'fetch_duration_seconds': 135.2,
#     'azure_api_calls': 3
# }

# Check error details
if report.status == 'failed':
    print(f"Error: {report.error_message}")
    print(f"Retries: {report.retry_count}")
```

### Manual Task Execution (for testing)

```python
# Execute synchronously (not async)
from apps.azure_integration.tasks import fetch_azure_recommendations

result = fetch_azure_recommendations(str(report.id))
print(result)
```

---

## Performance Tips

### 1. Use Filters to Reduce Data Volume

```python
# Good: Fetch only high-impact cost recommendations
report.api_sync_metadata = {
    'filters': {
        'category': 'Cost',
        'impact': 'High'
    }
}

# Bad: Fetch all recommendations (can be thousands)
report.api_sync_metadata = {'filters': {}}
```

### 2. Cache Statistics

```python
# Statistics are cached for 1 hour
# Don't call sync_azure_statistics too frequently
# Check cache first:

from django.core.cache import cache
cache_key = f"azure_advisor:{subscription_id}:statistics"
stats = cache.get(cache_key)

if not stats:
    # Trigger sync only if cache miss
    result = sync_azure_statistics.delay(str(subscription_id))
    stats = result.get()
```

### 3. Monitor Queue Lengths

```bash
# Check queue lengths in Redis
redis-cli LLEN celery:azure_api
redis-cli LLEN celery:reports

# If queues are backing up, scale workers
```

---

## Common Issues

### Issue: Task Stuck in PENDING

**Cause:** Worker not processing queue or worker crashed

**Solution:**
```bash
# Check workers
celery -A azure_advisor_reports inspect active

# Restart workers
celery -A azure_advisor_reports worker --pool=gevent --concurrency=4
```

### Issue: Authentication Errors

**Cause:** Invalid or expired Azure credentials

**Solution:**
```python
# Update credentials
subscription.client_secret = 'new-secret'
subscription.save()

# Test connection
test_azure_connection.delay(str(subscription.id))
```

### Issue: Rate Limiting

**Cause:** Too many Azure API calls

**Solution:**
- Enable caching (statistics cached for 1 hour)
- Reduce sync frequency
- Use filters to reduce data volume
- Spread out requests across multiple subscriptions

### Issue: Timeout Errors

**Cause:** Large data volume or slow API

**Solution:**
```python
# Use more aggressive filters
api_sync_metadata = {
    'filters': {
        'category': 'Cost',  # Only cost recommendations
        'impact': 'High',    # Only high impact
    }
}

# Or increase timeout in task decorator (not recommended)
# Better to optimize data volume
```

---

## Testing

### Run Tests

```bash
# All task tests
pytest apps/azure_integration/tests/test_tasks.py -v

# Specific test
pytest apps/azure_integration/tests/test_tasks.py::TestFetchAzureRecommendations::test_successful_fetch -v

# With coverage
pytest apps/azure_integration/tests/test_tasks.py --cov=apps.azure_integration.tasks --cov-report=term-missing
```

### Mock Azure Service in Tests

```python
from unittest.mock import patch, MagicMock

@patch('apps.azure_integration.tasks.AzureAdvisorService')
def test_my_task(mock_service_class):
    # Setup mock
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    mock_service.fetch_recommendations.return_value = [...]

    # Test task
    result = fetch_azure_recommendations(report_id)

    # Assertions
    assert result['status'] == 'success'
    mock_service.fetch_recommendations.assert_called_once()
```

---

## Production Deployment

### Worker Commands

```bash
# Start worker for Azure API queue
celery -A azure_advisor_reports worker \
    -Q azure_api \
    -P gevent \
    --concurrency=10 \
    --hostname=azure-api-worker@%h \
    --loglevel=info

# Start worker for reports queue
celery -A azure_advisor_reports worker \
    -Q reports \
    -P gevent \
    --concurrency=4 \
    --hostname=reports-worker@%h \
    --loglevel=info

# Start Flower monitoring (optional)
celery -A azure_advisor_reports flower --port=5555
```

### Environment Variables

```bash
# Required
export DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production
export SECRET_KEY=<your-secret-key>
export CELERY_BROKER_URL=redis://redis:6379/0
export CELERY_RESULT_BACKEND=redis://redis:6379/0

# Azure Storage (for report files)
export AZURE_STORAGE_CONNECTION_STRING=<connection-string>
export AZURE_STORAGE_CONTAINER_NAME=reports

# Optional: Application Insights
export APPINSIGHTS_INSTRUMENTATION_KEY=<key>
```

### Health Checks

```python
# Test Celery is running
from azure_advisor_reports.celery import health_check_task
result = health_check_task.delay()
print(result.get(timeout=5))
# {'status': 'healthy', 'timestamp': '...', 'worker': 'celery@worker1'}
```

---

## Support

For issues or questions:
1. Check logs: `apps/azure_integration/tasks.py` logging
2. Check task status: Flower dashboard at `http://localhost:5555`
3. Check report status: `report.status` and `report.error_message`
4. Check subscription status: `subscription.sync_status` and `subscription.sync_error_message`

---

**Quick Reference Version:** 1.0
**Last Updated:** November 18, 2024
**Coverage:** 88.06%
**Tests:** 33/33 passing
