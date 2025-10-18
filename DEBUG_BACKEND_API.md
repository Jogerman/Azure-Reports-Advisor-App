# Debugging Backend API - Step-by-Step Guide

## Prerequisites

1. Backend is running on `http://localhost:8000`
2. You have access to PowerShell or Command Prompt
3. You have Docker Desktop installed

---

## Step 1: Check Backend Status

```powershell
# Check if backend container is running
docker ps | findstr backend

# Should show:
# azure-advisor-backend   Up X minutes   8000/tcp
```

---

## Step 2: Check Database for Reports

```powershell
# Access the backend container shell
docker exec -it azure-advisor-backend python manage.py shell
```

Then in the Python shell:

```python
from apps.reports.models import Report, Recommendation

# Check total reports
total_reports = Report.objects.count()
print(f"Total reports: {total_reports}")

# Check completed reports
completed_reports = Report.objects.filter(status='completed')
print(f"Completed reports: {completed_reports.count()}")

# If there are completed reports, inspect one
if completed_reports.exists():
    report = completed_reports.first()
    print(f"\nReport ID: {report.id}")
    print(f"Status: {report.status}")
    print(f"Client: {report.client.company_name}")
    print(f"Recommendations count: {report.recommendations.count()}")
    print(f"\nAnalysis Data Keys: {list(report.analysis_data.keys())}")
    print(f"\nAnalysis Data:")
    import json
    print(json.dumps(report.analysis_data, indent=2))

    # Check first recommendation
    if report.recommendations.exists():
        rec = report.recommendations.first()
        print(f"\nFirst Recommendation:")
        print(f"  Category: {rec.category}")
        print(f"  Business Impact: {rec.business_impact}")
        print(f"  Potential Savings: {rec.potential_savings}")
        print(f"  Resource: {rec.resource_name}")

# Exit the shell
exit()
```

---

## Step 3: Check Backend Logs

```powershell
# View recent logs
docker-compose logs --tail=100 backend

# Follow logs in real-time
docker-compose logs -f backend
```

Look for:
- Any error messages
- CSV processing logs
- API request logs
- Statistics calculation logs

---

## Step 4: Test API Endpoints (Without Auth)

First, let's check if the endpoints respond:

```powershell
# Test health endpoint
curl http://localhost:8000/health/

# Test reports list (will return 401 if auth required)
curl http://localhost:8000/api/v1/reports/
```

Expected response:
- 401 Unauthorized (authentication required)
- Or a list of reports if authentication is disabled

---

## Step 5: Get Authentication Token

If you have a test user, get a token:

```powershell
# Login to get token
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login/" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"admin@example.com","password":"your_password"}'

$token = ($response.Content | ConvertFrom-Json).access_token
Write-Host "Token: $token"
```

Or using curl:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@example.com\",\"password\":\"your_password\"}"
```

---

## Step 6: Test Statistics Endpoint

### Using PowerShell:

```powershell
# Replace {report-id} with actual report ID from Step 2
$reportId = "your-report-id-here"
$token = "your-token-here"

$headers = @{
    "Authorization" = "Bearer $token"
}

$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/reports/$reportId/statistics/" `
  -Method GET `
  -Headers $headers

Write-Host "Status Code: $($response.StatusCode)"
Write-Host "Response:"
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Using curl:

```bash
curl -X GET "http://localhost:8000/api/v1/reports/{report-id}/statistics/" \
  -H "Authorization: Bearer {token}" \
  | python -m json.tool
```

### Expected Response:

```json
{
  "status": "success",
  "data": {
    "total_recommendations": 42,
    "total_potential_savings": 50000.0,
    "average_potential_savings": 1190.48,
    "average_savings_per_recommendation": 1190.48,
    "estimated_monthly_savings": 4166.67,
    "category_distribution": {...},
    "business_impact_distribution": {...}
  }
}
```

---

## Step 7: Test Recommendations Endpoint

### Using PowerShell:

```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/reports/$reportId/recommendations/" `
  -Method GET `
  -Headers $headers

Write-Host "Status Code: $($response.StatusCode)"
Write-Host "Response:"
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Using curl:

```bash
curl -X GET "http://localhost:8000/api/v1/reports/{report-id}/recommendations/" \
  -H "Authorization: Bearer {token}" \
  | python -m json.tool
```

### Expected Response:

```json
{
  "status": "success",
  "count": 42,
  "data": [
    {
      "id": "uuid",
      "category": "cost",
      "business_impact": "high",
      "recommendation": "...",
      "resource_name": "vm-001",
      "potential_savings": 1234.56,
      "currency": "USD"
    }
  ]
}
```

---

## Step 8: Check for Null/Undefined Values

### In Python Shell:

```python
from apps.reports.models import Report, Recommendation

# Get a completed report
report = Report.objects.filter(status='completed').first()

if report:
    # Check statistics
    stats = report.analysis_data
    print("Statistics:")
    print(f"  total_potential_savings: {stats.get('total_potential_savings')}")
    print(f"  average_potential_savings: {stats.get('average_potential_savings')}")
    print(f"  average_savings_per_recommendation: {stats.get('average_savings_per_recommendation')}")

    # Check recommendations
    for rec in report.recommendations.all()[:5]:
        print(f"\nRecommendation {rec.id}:")
        print(f"  potential_savings: {rec.potential_savings}")
        print(f"  potential_savings is None: {rec.potential_savings is None}")
        print(f"  potential_savings type: {type(rec.potential_savings)}")
```

---

## Step 9: Enable Debug Logging

### Option A: Temporary (via shell)

```powershell
docker exec -it azure-advisor-backend python manage.py shell
```

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Option B: Permanent (edit settings)

Edit `azure_advisor_reports/azure_advisor_reports/settings/development.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'apps.reports': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

Then restart:

```powershell
docker-compose restart backend
```

---

## Step 10: Upload and Process a Test CSV

### 1. Prepare a test CSV file

Create `test_advisor_data.csv`:

```csv
Category,Recommendation,Impact,Subscription ID,Resource Name,Potential Annual Cost Savings
Cost,Resize underutilized VM,High,sub-123,vm-prod-001,1200.50
Security,Enable MFA,High,sub-123,user-group-001,0
Performance,Upgrade to Premium Storage,Medium,sub-123,storage-001,500.00
```

### 2. Upload via API

```powershell
$clientId = "your-client-id"
$token = "your-token"

# Create multipart form data
$filePath = "test_advisor_data.csv"
$fileContent = Get-Content $filePath -Raw

$boundary = [System.Guid]::NewGuid().ToString()
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "multipart/form-data; boundary=$boundary"
}

# Upload CSV
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/reports/upload/" `
  -Method POST `
  -Headers $headers `
  -InFile $filePath

$reportId = ($response.Content | ConvertFrom-Json).data.report_id
Write-Host "Report ID: $reportId"
```

### 3. Process the CSV

```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/reports/$reportId/process/" `
  -Method POST `
  -Headers $headers

Write-Host "Processing result:"
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### 4. Check statistics

```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/reports/$reportId/statistics/" `
  -Method GET `
  -Headers $headers

Write-Host "Statistics:"
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## Step 11: Compare with Frontend Expectations

### Frontend expects (from your description):

```typescript
interface ReportStatistics {
  total_potential_savings: number;
  average_savings_per_recommendation: number;  // This was missing!
  // ... other fields
}

interface Recommendation {
  potential_savings: number;
  // ... other fields
}
```

### Backend now provides:

```json
{
  "data": {
    "total_potential_savings": 50000.0,
    "average_potential_savings": 1190.48,
    "average_savings_per_recommendation": 1190.48  // NOW AVAILABLE!
  }
}
```

---

## Common Issues and Solutions

### Issue 1: "No module named 'django_celery_beat'"

**Solution**: Install missing dependency
```powershell
docker exec -it azure-advisor-backend pip install django-celery-beat django-celery-results
docker-compose restart backend
```

### Issue 2: "Report is not completed yet"

**Solution**: Report status must be 'completed'
```python
# In shell
report = Report.objects.get(id='your-report-id')
print(f"Status: {report.status}")

# If status is not 'completed', process the CSV
# Or manually update status for testing
report.status = 'completed'
report.save()
```

### Issue 3: Empty analysis_data

**Solution**: Process the CSV to populate statistics
```powershell
curl -X POST "http://localhost:8000/api/v1/reports/{report-id}/process/" \
  -H "Authorization: Bearer {token}"
```

### Issue 4: 401 Unauthorized

**Solution**: Get a valid authentication token
- Check if Azure AD is configured correctly
- Use a test user account
- Check authentication settings

---

## Expected Output Summary

After following these steps, you should have:

1. **Confirmed**: Backend endpoints exist and are accessible
2. **Verified**: Database has reports and recommendations
3. **Tested**: API returns expected data structure
4. **Checked**: No null/undefined values in responses
5. **Validated**: Field alias `average_savings_per_recommendation` works

---

## Report Your Findings

After running these steps, report back with:

1. Number of completed reports in database
2. Sample output from statistics endpoint
3. Sample output from recommendations endpoint
4. Any error messages or unexpected behavior
5. Whether the field `average_savings_per_recommendation` is present

---

**Last Updated**: 2025-10-13
**Status**: Backend fixes applied, awaiting testing
