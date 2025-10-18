# Monitoring and Alerting Setup Guide

**Document Version:** 1.0
**Last Updated:** October 4, 2025
**Platform:** Azure Application Insights + Azure Monitor

---

## Table of Contents

1. [Overview](#overview)
2. [Application Insights Setup](#application-insights-setup)
3. [Custom Dashboards](#custom-dashboards)
4. [Alert Rules](#alert-rules)
5. [Log Analytics Queries](#log-analytics-queries)
6. [Performance Monitoring](#performance-monitoring)
7. [Cost Optimization](#cost-optimization)

---

## Overview

This guide provides step-by-step instructions to configure comprehensive monitoring for the Azure Advisor Reports Platform using Application Insights and Azure Monitor.

### Monitoring Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Application Layer                          │
│   ┌──────────────┐         ┌──────────────┐            │
│   │   Frontend   │         │   Backend    │            │
│   │   (React)    │────────▶│   (Django)   │            │
│   └──────┬───────┘         └──────┬───────┘            │
│          │                        │                     │
│          │  Telemetry             │  Telemetry          │
│          │                        │                     │
└──────────┼────────────────────────┼─────────────────────┘
           │                        │
           ▼                        ▼
┌─────────────────────────────────────────────────────────┐
│         Application Insights                            │
│   ┌──────────────────────────────────────────────┐     │
│   │  • Request tracking                           │     │
│   │  • Dependency monitoring                      │     │
│   │  • Exception logging                          │     │
│   │  • Custom metrics and events                  │     │
│   │  • User analytics                             │     │
│   └──────────────────────────────────────────────┘     │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│         Log Analytics Workspace                         │
│   ┌──────────────────────────────────────────────┐     │
│   │  • Centralized log storage                    │     │
│   │  • KQL query engine                           │     │
│   │  • 30/90 day retention                        │     │
│   └──────────────────────────────────────────────┘     │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│         Azure Monitor Alerts                            │
│   ┌──────────────────────────────────────────────┐     │
│   │  • Performance alerts                         │     │
│   │  • Error rate alerts                          │     │
│   │  • Availability alerts                        │     │
│   │  • Resource health alerts                     │     │
│   └──────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## Application Insights Setup

### 1. Verify Application Insights Deployment

```powershell
# Check if Application Insights exists
$appInsightsName = "appi-advisor-prod"
$resourceGroup = "rg-azure-advisor-reports-prod"

az monitor app-insights component show `
    --app $appInsightsName `
    --resource-group $resourceGroup
```

### 2. Get Connection String

```powershell
# Get Application Insights connection string
$connString = az monitor app-insights component show `
    --app $appInsightsName `
    --resource-group $resourceGroup `
    --query connectionString -o tsv

Write-Host "Connection String: $connString"

# Set as environment variable in Web Apps
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name "app-advisor-backend-prod" `
    --settings "APPLICATIONINSIGHTS_CONNECTION_STRING=$connString"

az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name "app-advisor-frontend-prod" `
    --settings "APPLICATIONINSIGHTS_CONNECTION_STRING=$connString"
```

### 3. Configure Backend (Django)

**In `settings/production.py`:**

```python
# Application Insights configuration
APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')

if APPLICATIONINSIGHTS_CONNECTION_STRING:
    # Add OpenCensus middleware
    MIDDLEWARE = [
        'opencensus.ext.django.middleware.OpencensusMiddleware',
    ] + MIDDLEWARE

    # Configure OpenCensus
    OPENCENSUS = {
        'TRACE': {
            'SAMPLER': 'opencensus.trace.samplers.ProbabilitySampler(rate=1.0)',
            'EXPORTER': f'''opencensus.ext.azure.trace_exporter.AzureExporter(
                connection_string="{APPLICATIONINSIGHTS_CONNECTION_STRING}"
            )''',
        }
    }

    # Configure logging to Application Insights
    LOGGING = {
        'version': 1,
        'handlers': {
            'azure': {
                'level': 'INFO',
                'class': 'opencensus.ext.azure.log_exporter.AzureLogHandler',
                'connection_string': APPLICATIONINSIGHTS_CONNECTION_STRING,
            },
        },
        'loggers': {
            'django': {
                'handlers': ['azure'],
                'level': 'INFO',
            },
        },
    }
```

### 4. Configure Frontend (React)

**In `src/config/appInsights.ts`:**

```typescript
import { ApplicationInsights } from '@microsoft/applicationinsights-web';

const appInsights = new ApplicationInsights({
  config: {
    connectionString: process.env.REACT_APP_APPLICATIONINSIGHTS_CONNECTION_STRING,
    enableAutoRouteTracking: true,
    enableRequestHeaderTracking: true,
    enableResponseHeaderTracking: true,
    enableCorsCorrelation: true,
    enableAjaxPerfTracking: true,
  }
});

appInsights.loadAppInsights();
appInsights.trackPageView(); // Track initial page view

export { appInsights };
```

---

## Custom Dashboards

### Dashboard 1: Application Performance Overview

**Create via Azure Portal:**

1. Navigate to Application Insights
2. Click "Dashboard" → "New Dashboard"
3. Name: "Azure Advisor Reports - Performance Overview"
4. Add the following tiles:

**Tiles to Add:**

```kql
// 1. Request Rate (Requests/minute)
requests
| where timestamp > ago(1h)
| summarize RequestCount = count() by bin(timestamp, 1m)
| render timechart

// 2. Response Time (95th percentile)
requests
| where timestamp > ago(1h)
| summarize Percentile95 = percentile(duration, 95) by bin(timestamp, 5m)
| render timechart

// 3. Failed Requests
requests
| where timestamp > ago(24h) and success == false
| summarize FailedRequests = count() by bin(timestamp, 1h), resultCode
| render barchart

// 4. Top 10 Slowest Endpoints
requests
| where timestamp > ago(24h)
| summarize AvgDuration = avg(duration), RequestCount = count() by operation_Name
| top 10 by AvgDuration desc
| project operation_Name, AvgDuration, RequestCount

// 5. Exception Rate
exceptions
| where timestamp > ago(24h)
| summarize ExceptionCount = count() by bin(timestamp, 1h), type
| render timechart
```

### Dashboard 2: Business Metrics

```kql
// 1. Reports Generated (Daily)
customEvents
| where name == "ReportGenerated"
| where timestamp > ago(30d)
| summarize ReportsGenerated = count() by bin(timestamp, 1d)
| render columnchart

// 2. Report Generation Time
customMetrics
| where name == "ReportGenerationDuration"
| where timestamp > ago(7d)
| summarize AvgDuration = avg(value), MaxDuration = max(value) by bin(timestamp, 1h)
| render timechart

// 3. Active Users
customEvents
| where name == "UserLogin"
| where timestamp > ago(7d)
| summarize UniqueUsers = dcount(user_Id) by bin(timestamp, 1d)
| render columnchart

// 4. Report Types Distribution
customEvents
| where name == "ReportGenerated" and timestamp > ago(30d)
| extend ReportType = tostring(customDimensions["reportType"])
| summarize Count = count() by ReportType
| render piechart
```

### Dashboard 3: Infrastructure Health

```kql
// 1. Database Query Performance
dependencies
| where type == "SQL"
| where timestamp > ago(1h)
| summarize AvgDuration = avg(duration), Count = count() by bin(timestamp, 5m)
| render timechart

// 2. Redis Cache Hit Rate
dependencies
| where type == "Redis"
| where timestamp > ago(1h)
| extend CacheHit = iff(resultCode == "0", 1, 0)
| summarize HitRate = 100.0 * sum(CacheHit) / count() by bin(timestamp, 5m)
| render timechart

// 3. Blob Storage Operations
dependencies
| where type == "Azure blob"
| where timestamp > ago(1h)
| summarize Operations = count(), AvgDuration = avg(duration) by bin(timestamp, 5m), success
| render timechart

// 4. Celery Task Queue Length
customMetrics
| where name == "CeleryQueueLength"
| where timestamp > ago(1h)
| summarize AvgQueueLength = avg(value) by bin(timestamp, 5m)
| render timechart
```

---

## Alert Rules

### Critical Alerts (P0)

#### 1. High Error Rate Alert

```powershell
az monitor metrics alert create `
    --name "High Error Rate - Production" `
    --resource-group $resourceGroup `
    --scopes "/subscriptions/{subscription-id}/resourceGroups/$resourceGroup/providers/Microsoft.Insights/components/$appInsightsName" `
    --condition "count requests/failed > 10" `
    --window-size 5m `
    --evaluation-frequency 1m `
    --severity 0 `
    --description "Triggers when failed request count exceeds 10 in 5 minutes"
```

**Equivalent KQL Alert Query:**
```kql
requests
| where timestamp > ago(5m) and success == false
| summarize FailedRequests = count()
| where FailedRequests > 10
```

#### 2. Application Unavailable Alert

```powershell
az monitor metrics alert create `
    --name "Application Unavailable - Production" `
    --resource-group $resourceGroup `
    --scopes "/subscriptions/{subscription-id}/resourceGroups/$resourceGroup/providers/Microsoft.Web/sites/app-advisor-backend-prod" `
    --condition "avg HttpResponseTime > 5000" `
    --window-size 5m `
    --evaluation-frequency 1m `
    --severity 0 `
    --description "Triggers when average response time exceeds 5 seconds"
```

#### 3. Database Connection Failure

```kql
dependencies
| where type == "SQL" and timestamp > ago(5m)
| where success == false
| summarize FailedConnections = count()
| where FailedConnections > 5
```

**Create Log Alert:**
```powershell
az monitor scheduled-query create `
    --name "Database Connection Failures" `
    --resource-group $resourceGroup `
    --scopes $appInsightsResourceId `
    --condition "count > 5" `
    --condition-query "dependencies | where type == 'SQL' and timestamp > ago(5m) | where success == false | summarize FailedConnections = count()" `
    --window-size 5m `
    --evaluation-frequency 1m `
    --severity 0
```

### High Priority Alerts (P1)

#### 4. Slow Response Time Alert

```kql
requests
| where timestamp > ago(15m)
| summarize Percentile95 = percentile(duration, 95)
| where Percentile95 > 2000  // 2 seconds
```

#### 5. High Memory Usage

```powershell
az monitor metrics alert create `
    --name "High Memory Usage - Backend" `
    --resource-group $resourceGroup `
    --scopes "/subscriptions/{subscription-id}/resourceGroups/$resourceGroup/providers/Microsoft.Web/sites/app-advisor-backend-prod" `
    --condition "avg MemoryWorkingSet > 1600000000" `
    --window-size 5m `
    --evaluation-frequency 1m `
    --severity 1 `
    --description "Triggers when memory usage exceeds 1.6GB (80% of 2GB)"
```

#### 6. High CPU Usage

```powershell
az monitor metrics alert create `
    --name "High CPU Usage - Backend" `
    --resource-group $resourceGroup `
    --scopes "/subscriptions/{subscription-id}/resourceGroups/$resourceGroup/providers/Microsoft.Web/sites/app-advisor-backend-prod" `
    --condition "avg CpuPercentage > 80" `
    --window-size 15m `
    --evaluation-frequency 5m `
    --severity 1
```

### Medium Priority Alerts (P2)

#### 7. Report Generation Failures

```kql
customEvents
| where name == "ReportGenerationFailed" and timestamp > ago(30m)
| summarize FailureCount = count()
| where FailureCount > 3
```

#### 8. Low Cache Hit Rate

```kql
dependencies
| where type == "Redis" and timestamp > ago(30m)
| extend CacheHit = iff(resultCode == "0", 1, 0)
| summarize HitRate = 100.0 * sum(CacheHit) / count()
| where HitRate < 50  // Alert if hit rate drops below 50%
```

---

## Log Analytics Queries

### Useful Queries for Troubleshooting

#### Find All Errors in Last Hour

```kql
union exceptions, traces
| where timestamp > ago(1h) and severityLevel >= 3
| project timestamp, message, operation_Name, severityLevel
| order by timestamp desc
```

#### Track User Journey

```kql
requests
| where user_Id == "specific-user-id" and timestamp > ago(24h)
| project timestamp, operation_Name, duration, success
| order by timestamp asc
```

#### Analyze Report Generation Performance

```kql
customEvents
| where name == "ReportGenerated" and timestamp > ago(7d)
| extend ReportType = tostring(customDimensions["reportType"])
| extend Duration = todouble(customMeasurements["duration"])
| summarize
    AvgDuration = avg(Duration),
    MaxDuration = max(Duration),
    Count = count()
    by ReportType
| order by AvgDuration desc
```

#### Failed Dependencies by Type

```kql
dependencies
| where timestamp > ago(24h) and success == false
| summarize FailureCount = count() by type, target
| order by FailureCount desc
```

---

## Performance Monitoring

### Key Performance Indicators (KPIs)

| Metric | Target | Alert Threshold | Query |
|--------|--------|-----------------|-------|
| **Response Time (95th)** | < 500ms | > 2000ms | `requests \| summarize percentile(duration, 95)` |
| **Error Rate** | < 1% | > 5% | `requests \| summarize ErrorRate = 100.0 * countif(success == false) / count()` |
| **Availability** | > 99.5% | < 99% | `availabilityResults \| summarize Availability = 100.0 * countif(success == true) / count()` |
| **Report Generation Time** | < 45s | > 120s | `customMetrics \| where name == "ReportGenerationDuration" \| summarize avg(value)` |
| **Database Query Time** | < 100ms | > 500ms | `dependencies \| where type == "SQL" \| summarize avg(duration)` |

### Set Up Availability Tests

```powershell
# Create availability test for backend health endpoint
az monitor app-insights web-test create `
    --resource-group $resourceGroup `
    --name "Backend Health Check" `
    --location "East US" `
    --web-test-name "Backend-Health-Test" `
    --enabled true `
    --frequency 300 `
    --timeout 30 `
    --web-test-kind "ping" `
    --locations "us-east-1" "us-west-1" "eu-west-1" `
    --retry-enabled true `
    --test-url "https://app-advisor-backend-prod.azurewebsites.net/api/health/"
```

---

## Cost Optimization

### Monitoring Costs

Application Insights charges are based on:
- Data ingestion (per GB)
- Data retention (beyond 90 days)
- Availability tests

### Reduce Costs

1. **Sampling**: Reduce telemetry volume
```python
# In Django settings
OPENCENSUS = {
    'TRACE': {
        'SAMPLER': 'opencensus.trace.samplers.ProbabilitySampler(rate=0.5)',  # 50% sampling
    }
}
```

2. **Adjust Retention**: Default is 90 days, reduce if not needed
```powershell
az monitor app-insights component update `
    --app $appInsightsName `
    --resource-group $resourceGroup `
    --retention-time 30  # 30 days
```

3. **Filter Noisy Telemetry**: Exclude health check pings
```python
# Telemetry processor to filter health checks
from opencensus.trace import execution_context

def filter_health_checks(envelope):
    if '/api/health/' in envelope.data.baseData.get('url', ''):
        return False
    return True
```

---

## Action Groups for Alerts

### Create Email Action Group

```powershell
az monitor action-group create `
    --name "DevOps Team - Email" `
    --resource-group $resourceGroup `
    --short-name "DevOpsTeam" `
    --email-receiver name="DevOps Team" email-address="devops@company.com"
```

### Create SMS Action Group

```powershell
az monitor action-group create `
    --name "On-Call Team - SMS" `
    --resource-group $resourceGroup `
    --short-name "OnCallTeam" `
    --sms-receiver name="On-Call Engineer" country-code="1" phone-number="5551234567"
```

---

## Summary Checklist

After completing this setup, verify:

- [ ] Application Insights deployed and configured
- [ ] Backend sending telemetry data
- [ ] Frontend sending telemetry data
- [ ] Custom dashboards created (3 dashboards)
- [ ] Critical alerts configured (3 alerts)
- [ ] High priority alerts configured (3 alerts)
- [ ] Medium priority alerts configured (2+ alerts)
- [ ] Action groups configured for notifications
- [ ] Availability tests running
- [ ] Log Analytics queries saved for common scenarios
- [ ] Cost monitoring enabled

---

**Document End**
