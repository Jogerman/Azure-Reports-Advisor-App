# Troubleshooting Guide
## Azure Advisor Reports Platform

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Applies to:** Platform v1.0+

---

## Table of Contents

1. [Quick Diagnostic Tools](#quick-diagnostic-tools)
2. [Authentication & Login Issues](#authentication--login-issues)
3. [CSV Upload & Processing Issues](#csv-upload--processing-issues)
4. [Report Generation Issues](#report-generation-issues)
5. [Dashboard & Analytics Issues](#dashboard--analytics-issues)
6. [Performance Issues](#performance-issues)
7. [Database Issues](#database-issues)
8. [Azure Infrastructure Issues](#azure-infrastructure-issues)
9. [Error Code Reference](#error-code-reference)
10. [Support Escalation](#support-escalation)

---

## Quick Diagnostic Tools

### Health Check Endpoint

**Check overall system health:**
```bash
curl https://your-backend-url.azurewebsites.net/api/health/

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "storage": "connected",
  "version": "1.0.0"
}
```

### Application Insights Queries

**Common diagnostic queries:**

```kusto
// Recent errors (last 24 hours)
exceptions
| where timestamp > ago(24h)
| summarize count() by type, outerMessage
| order by count_ desc

// Slow API requests (>2 seconds)
requests
| where timestamp > ago(1h)
| where duration > 2000
| project timestamp, name, url, duration, resultCode
| order by duration desc

// Failed authentication attempts
traces
| where timestamp > ago(1h)
| where message contains "authentication failed"
| project timestamp, message, customDimensions
```

### Quick Diagnostic Checklist

**If something's not working, check these first:**

- [ ] Is the service running? (Check Azure Portal → App Services)
- [ ] Is the database accessible? (Check health endpoint)
- [ ] Are there recent deployments? (Check Deployment Center)
- [ ] Any Azure service outages? (Check Azure Status)
- [ ] Are there error spikes? (Check Application Insights)
- [ ] Is the user logged in? (Check browser dev tools → Application → Cookies)
- [ ] Clear browser cache and cookies
- [ ] Try in incognito/private mode

---

## Authentication & Login Issues

### Issue 1: "Unable to Login" or "Authentication Failed"

**Symptoms:**
- Login button doesn't work
- Redirected back to login page
- Error: "Authentication failed. Please try again."

**Common Causes:**

**Cause 1: Azure AD App Configuration Issue**

**Diagnosis:**
```powershell
# Check Azure AD app registration
az ad app show --id <client-id>

# Verify redirect URIs are correct
```

**Solution:**
1. Go to Azure Portal → Azure Active Directory → App registrations
2. Find your app: "Azure Advisor Reports"
3. Go to "Authentication" → Redirect URIs
4. Ensure these URIs are present:
   - `https://your-frontend-url.azurewebsites.net`
   - `https://your-custom-domain.com` (if using custom domain)
5. Save changes
6. Wait 5 minutes for changes to propagate
7. Try logging in again

**Cause 2: Expired or Invalid Client Secret**

**Diagnosis:**
```powershell
# Check secret expiration
az ad app credential list --id <client-id>
```

**Solution:**
1. If secret expired, create new secret:
```powershell
az ad app credential reset --id <client-id> --append
```
2. Update App Service configuration with new secret:
```powershell
az webapp config appsettings set \
  --resource-group rg-azure-advisor-reports-prod \
  --name app-advisor-backend-prod \
  --settings AZURE_CLIENT_SECRET="<new-secret>"
```
3. Restart app service
4. Try logging in again

**Cause 3: Browser Cookies or Cache Issue**

**Solution:**
1. Open browser developer tools (F12)
2. Go to Application tab → Cookies
3. Clear all cookies for your domain
4. Clear browser cache (Ctrl+Shift+Delete)
5. Close and reopen browser
6. Try logging in again

**Cause 4: User Not in Azure AD Tenant**

**Solution:**
1. Verify user exists in Azure AD tenant
2. Add user if missing:
```powershell
az ad user create --display-name "User Name" --user-principal-name user@domain.com --password "TempPassword123!"
```
3. User must reset password on first login

### Issue 2: "Token Expired" After Some Time

**Symptoms:**
- Logged in successfully, but after 1 hour get "Token expired" error
- Automatic logout after inactivity

**Solution:**

**User Action:**
1. Click "Refresh" or "Login Again" button
2. Platform will automatically refresh token

**Admin Action (if issue persists):**
1. Check token refresh logic in frontend code
2. Verify token expiration settings:
```javascript
// In frontend config
const tokenRefreshInterval = 55 * 60 * 1000; // 55 minutes (before 1-hour expiration)
```
3. Check Application Insights for token refresh errors

### Issue 3: Stuck on Loading Screen After Login

**Symptoms:**
- Successful Azure AD login
- Redirected back to application
- Spinner keeps spinning, never loads dashboard

**Diagnosis:**
```javascript
// Open browser console (F12) and check for errors
// Look for:
// - CORS errors
// - API connection errors
// - JavaScript errors
```

**Common Solutions:**

**Solution 1: CORS Configuration Issue**

**Check backend CORS settings:**
```powershell
# Check current CORS settings
az webapp cors show \
  --resource-group rg-azure-advisor-reports-prod \
  --name app-advisor-backend-prod
```

**Fix CORS:**
```powershell
# Add frontend origin
az webapp cors add \
  --resource-group rg-azure-advisor-reports-prod \
  --name app-advisor-backend-prod \
  --allowed-origins "https://your-frontend-url.azurewebsites.net"
```

**Solution 2: Backend API Not Responding**

1. Check health endpoint: `https://your-backend-url.azurewebsites.net/api/health/`
2. If not responding, restart backend app service:
```powershell
az webapp restart \
  --resource-group rg-azure-advisor-reports-prod \
  --name app-advisor-backend-prod
```

**Solution 3: Frontend Environment Variables Not Set**

1. Check App Service Configuration:
```powershell
az webapp config appsettings list \
  --resource-group rg-azure-advisor-reports-prod \
  --name app-advisor-frontend-prod
```
2. Ensure these variables exist:
   - `REACT_APP_API_URL`
   - `REACT_APP_AZURE_CLIENT_ID`
   - `REACT_APP_AZURE_TENANT_ID`
3. If missing, add them and restart app service

---

## CSV Upload & Processing Issues

### Issue 4: "File Upload Failed" Error

**Symptoms:**
- CSV upload fails immediately
- Error: "File upload failed. Please try again."

**Common Causes:**

**Cause 1: File Too Large**

**Diagnosis:**
- Check file size (should be <50MB)

**Solution:**
1. Split large CSV into multiple files
2. Or, increase upload limit (admin only):
```python
# In Django settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
```
3. Restart backend service

**Cause 2: Blob Storage Connection Issue**

**Diagnosis:**
```powershell
# Test blob storage connection
az storage container list \
  --connection-string "<connection-string>"
```

**Solution:**
1. Verify connection string in App Service configuration
2. Check blob storage account is accessible
3. Verify firewall rules allow App Service IP

**Cause 3: Incorrect File Format**

**Solution:**
1. Verify file is actually a CSV (not Excel renamed to .csv)
2. Check file encoding (should be UTF-8 or UTF-8-BOM)
3. Open file in text editor to verify it's comma-separated

### Issue 5: CSV Upload Succeeds but Processing Fails

**Symptoms:**
- CSV uploads successfully
- Report status stuck at "Processing"
- Or report status changes to "Failed"

**Diagnosis:**

**Check Celery Worker Logs:**
```powershell
# View app service logs
az webapp log tail \
  --resource-group rg-azure-advisor-reports-prod \
  --name app-advisor-backend-prod
```

**Check Application Insights:**
```kusto
traces
| where timestamp > ago(1h)
| where message contains "CSV processing"
| project timestamp, message, severityLevel
```

**Common Causes:**

**Cause 1: Missing or Incorrect CSV Columns**

**Expected Azure Advisor CSV columns:**
- Category
- Business Impact
- Recommendation
- Subscription ID
- Subscription Name
- Resource Group
- Resource Name
- Type
- Potential Benefits
- Potential Annual Cost Savings (USD)
- Currency
- Retirement Date
- Retiring Feature

**Solution:**
1. Verify CSV has all required columns
2. Column names must match exactly (case-sensitive)
3. Download fresh Azure Advisor export if columns are missing

**Cause 2: Celery Worker Not Running**

**Diagnosis:**
```powershell
# Check if Celery container/process is running
# For App Service: Check "Console" in Azure Portal
ps aux | grep celery
```

**Solution:**
```powershell
# Restart app service (this restarts Celery workers)
az webapp restart \
  --resource-group rg-azure-advisor-reports-prod \
  --name app-advisor-backend-prod
```

**Cause 3: Redis Connection Issue**

**Diagnosis:**
```powershell
# Test Redis connection
az redis show \
  --resource-group rg-azure-advisor-reports-prod \
  --name redis-advisor-prod
```

**Solution:**
1. Verify Redis is running
2. Check Redis connection string in App Service configuration
3. Restart Redis cache if needed (will cause brief downtime)

**Cause 4: Database Connection Timeout**

**Solution:**
1. Check database connection pool settings
2. Increase timeout in Django settings:
```python
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,  # 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```
3. Restart backend service

### Issue 6: CSV Processing is Very Slow

**Symptoms:**
- CSV processing takes >5 minutes
- Report generation takes >2 minutes

**Diagnosis:**
1. Check CSV file size (large files take longer)
2. Check number of recommendations in CSV
3. Check Celery worker count
4. Check database performance

**Solutions:**

**Solution 1: Scale Celery Workers**
```powershell
# Increase worker count (in Dockerfile or startup command)
# Update App Service startup command:
celery -A azure_advisor_reports worker -l info --concurrency=4
```

**Solution 2: Optimize Database Queries**
1. Ensure indexes exist on foreign keys
2. Use bulk_create for inserting recommendations
3. Check for N+1 query issues

**Solution 3: Scale App Service Plan**
```powershell
# Scale up to higher tier
az appservice plan update \
  --resource-group rg-azure-advisor-reports-prod \
  --name asp-advisor-backend-prod \
  --sku P2v3
```

---

## Report Generation Issues

### Issue 7: Report Generation Fails After CSV Processing

**Symptoms:**
- CSV processing succeeds
- Report status changes to "Failed" during generation
- Error message in report: "Report generation failed"

**Common Causes:**

**Cause 1: PDF Generation Memory Issue**

**Diagnosis:**
```kusto
// Check for out-of-memory errors
exceptions
| where timestamp > ago(1h)
| where outerMessage contains "memory"
```

**Solution:**
1. Reduce concurrent report generations
2. Increase App Service instance size
3. Optimize PDF template (reduce images/fonts)

**Cause 2: Report Template Error**

**Diagnosis:**
- Check Application Insights for template rendering errors
- Look for missing template variables

**Solution:**
1. Review report template files
2. Ensure all variables used in template exist in context
3. Add error handling for missing data

**Cause 3: Blob Storage Write Failure**

**Diagnosis:**
```powershell
# Check blob storage metrics
az monitor metrics list \
  --resource <storage-account-resource-id> \
  --metric Availability \
  --start-time 2025-10-06T00:00:00Z
```

**Solution:**
1. Verify blob storage is accessible
2. Check storage account capacity (not full)
3. Verify App Service has permissions to write to blob storage

### Issue 8: Generated Report is Blank or Incomplete

**Symptoms:**
- Report generates successfully
- Downloaded PDF/HTML is blank or missing sections

**Solution:**

**For Blank Reports:**
1. Check if CSV data was actually processed
2. Verify recommendations were created in database:
```sql
SELECT COUNT(*) FROM recommendations WHERE report_id = '<report-id>';
```
3. If count is 0, CSV processing failed silently
4. Re-upload CSV and check for errors

**For Incomplete Reports:**
1. Check which sections are missing
2. Review report template for that report type
3. Check if data for missing sections exists in analysis_data JSON
4. May need to regenerate report

### Issue 9: Can't Download Report Files

**Symptoms:**
- Report shows as "Completed"
- Download button doesn't work or shows error

**Common Causes:**

**Cause 1: Blob Storage SAS Token Expired**

**Solution:**
1. Check SAS token expiration in code
2. Increase SAS token lifetime (e.g., 1 hour → 24 hours)
3. Regenerate download link

**Cause 2: Blob File Deleted**

**Diagnosis:**
```powershell
# Check if file exists in blob storage
az storage blob exists \
  --account-name stadvisorprod \
  --container-name reports-pdf \
  --name <file-name>
```

**Solution:**
- If file doesn't exist, regenerate report
- Check blob storage retention policy

**Cause 3: CORS Issue on Blob Storage**

**Solution:**
```powershell
# Configure CORS on blob storage
az storage cors add \
  --services b \
  --methods GET \
  --origins "https://your-frontend-url.azurewebsites.net" \
  --allowed-headers "*" \
  --exposed-headers "*" \
  --max-age 3600 \
  --account-name stadvisorprod
```

---

## Dashboard & Analytics Issues

### Issue 10: Dashboard Shows No Data

**Symptoms:**
- Dashboard loads but all metrics show 0 or "No data"
- Charts are empty

**Common Causes:**

**Cause 1: No Reports Generated Yet**

**Solution:**
- This is normal for new installations
- Generate at least one report to see data
- Dashboard will update automatically

**Cause 2: Date Range Filter Too Restrictive**

**Solution:**
1. Check date range picker on dashboard
2. Expand date range to "All Time" or "Last 90 Days"
3. Refresh dashboard

**Cause 3: API Connection Issue**

**Diagnosis:**
- Open browser dev tools (F12) → Network tab
- Look for failed API requests to `/api/analytics/`

**Solution:**
1. Check backend API is responding
2. Verify authentication token is valid
3. Check CORS configuration

### Issue 11: Dashboard Data is Outdated

**Symptoms:**
- Just generated a report, but dashboard doesn't show it
- Metrics don't match expectations

**Solution:**

**Cause 1: Client-Side Caching**

**Solution:**
1. Hard refresh browser (Ctrl+F5 or Cmd+Shift+R)
2. Or, click "Refresh" button on dashboard

**Cause 2: Redis Cache Not Invalidated**

**Solution (Admin):**
```powershell
# Clear Redis cache
az redis force-reboot \
  --resource-group rg-azure-advisor-reports-prod \
  --name redis-advisor-prod \
  --reboot-type AllNodes
```
**Note:** This will cause brief interruption (2-3 minutes)

**Cause 3: Database Replication Lag**

**Solution:**
- Wait 1-2 minutes and refresh
- Database replication is eventually consistent

---

## Performance Issues

### Issue 12: Application is Slow

**Symptoms:**
- Pages take >3 seconds to load
- API requests timeout
- Report generation takes >2 minutes

**Diagnosis:**

**Check Application Insights Performance:**
```kusto
requests
| where timestamp > ago(1h)
| summarize avg(duration), percentile(duration, 95) by name
| order by avg_duration desc
```

**Common Causes & Solutions:**

**Cause 1: High CPU/Memory Usage**

**Diagnosis:**
```powershell
# Check metrics
az monitor metrics list \
  --resource <app-service-resource-id> \
  --metric CpuPercentage,MemoryPercentage
```

**Solution:**
1. If CPU >80% or Memory >80%, scale up:
```powershell
# Scale up to larger instance
az appservice plan update \
  --resource-group rg-azure-advisor-reports-prod \
  --name asp-advisor-backend-prod \
  --sku P2v3

# Or scale out (more instances)
az appservice plan update \
  --resource-group rg-azure-advisor-reports-prod \
  --name asp-advisor-backend-prod \
  --number-of-workers 3
```

**Cause 2: Database Performance Issues**

**Diagnosis:**
```sql
-- Check for slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Solution:**
1. Add missing indexes
2. Optimize slow queries
3. Increase database tier if needed:
```powershell
az postgres flexible-server update \
  --resource-group rg-azure-advisor-reports-prod \
  --name psql-advisor-prod \
  --sku-name Standard_D4s_v3
```

**Cause 3: Redis Cache Not Being Used**

**Solution:**
1. Verify Redis connection in health check
2. Check cache hit rate in Application Insights
3. Increase cache expiration times for frequently accessed data

**Cause 4: Too Many Concurrent Requests**

**Solution:**
1. Implement rate limiting
2. Add request queuing
3. Scale horizontally (more instances)

### Issue 13: Report Generation Timeout

**Symptoms:**
- Report processing starts but never completes
- Status stuck at "Processing" for >10 minutes
- Celery task timeout error

**Solution:**

**Increase Celery Task Timeout:**
```python
# In celery config
task_time_limit = 600  # 10 minutes
task_soft_time_limit = 540  # 9 minutes
```

**Optimize Processing:**
1. Use bulk database operations
2. Process CSV in chunks
3. Reduce PDF complexity

**Scale Celery Workers:**
```powershell
# Increase worker concurrency
# Update startup command: --concurrency=6
```

---

## Database Issues

### Issue 14: Database Connection Errors

**Symptoms:**
- "Can't connect to database" errors
- "Connection refused" or "Connection timeout"
- Application can't start

**Diagnosis:**
```powershell
# Check database status
az postgres flexible-server show \
  --resource-group rg-azure-advisor-reports-prod \
  --name psql-advisor-prod \
  --query state
```

**Common Causes:**

**Cause 1: Database is Down or Restarting**

**Solution:**
```powershell
# Check database status
az postgres flexible-server show --resource-group rg-azure-advisor-reports-prod --name psql-advisor-prod

# If stopped, start it
az postgres flexible-server start \
  --resource-group rg-azure-advisor-reports-prod \
  --name psql-advisor-prod
```

**Cause 2: Firewall Rules Blocking Connection**

**Solution:**
```powershell
# Allow Azure services to access database
az postgres flexible-server firewall-rule create \
  --resource-group rg-azure-advisor-reports-prod \
  --name psql-advisor-prod \
  --rule-name AllowAllAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

**Cause 3: Incorrect Connection String**

**Solution:**
1. Verify connection string in App Service configuration
2. Format should be: `postgresql://user:password@server:5432/database?sslmode=require`
3. Update if incorrect and restart app service

**Cause 4: Database Credentials Changed**

**Solution:**
```powershell
# Reset database admin password
az postgres flexible-server update \
  --resource-group rg-azure-advisor-reports-prod \
  --name psql-advisor-prod \
  --admin-password "<new-password>"
```
Update connection string with new password

### Issue 15: Database is Full

**Symptoms:**
- "Disk quota exceeded" error
- Can't create new reports
- Application crashes

**Diagnosis:**
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('azure_advisor_reports'));

-- Check table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

**Solution:**

**Short-term:**
1. Delete old reports and recommendations:
```sql
-- Delete reports older than 90 days
DELETE FROM reports WHERE created_at < NOW() - INTERVAL '90 days';
```
2. Vacuum database to reclaim space:
```sql
VACUUM FULL;
```

**Long-term:**
```powershell
# Increase database storage
az postgres flexible-server update \
  --resource-group rg-azure-advisor-reports-prod \
  --name psql-advisor-prod \
  --storage-size 256
```

---

## Azure Infrastructure Issues

### Issue 16: App Service Down or Not Responding

**Symptoms:**
- Website shows "503 Service Unavailable"
- Application doesn't load
- Health check fails

**Diagnosis:**
```powershell
# Check app service status
az webapp show \
  --resource-group rg-azure-advisor-reports-prod \
  --name app-advisor-backend-prod \
  --query state
```

**Solutions:**

**Solution 1: Restart App Service**
```powershell
az webapp restart \
  --resource-group rg-azure-advisor-reports-prod \
  --name app-advisor-backend-prod
```

**Solution 2: Check App Service Logs**
```powershell
# View recent logs
az webapp log tail \
  --resource-group rg-azure-advisor-reports-prod \
  --name app-advisor-backend-prod
```

**Solution 3: Check App Service Plan Health**
```powershell
az appservice plan show \
  --resource-group rg-azure-advisor-reports-prod \
  --name asp-advisor-backend-prod
```

**Solution 4: Scale Up if Under-resourced**
```powershell
# Check if consistently hitting resource limits
# Scale up if needed
az appservice plan update \
  --resource-group rg-azure-advisor-reports-prod \
  --name asp-advisor-backend-prod \
  --sku P2v3
```

### Issue 17: Azure Region Outage

**Symptoms:**
- All services in region unavailable
- Azure Status page shows outage
- Can't access Azure Portal

**Solution:**

**Immediate Actions:**
1. Check Azure Status: https://status.azure.com
2. Identify affected services and expected recovery time
3. Communicate outage to users
4. Enable maintenance mode banner (if possible)

**Recovery Actions:**
1. Wait for Microsoft to resolve region issue
2. Once region is back, verify all services
3. Run health checks
4. Check data integrity
5. Monitor for residual issues

**Prevention (for future):**
1. Implement multi-region deployment
2. Setup traffic manager for automatic failover
3. Maintain hot standby in secondary region

### Issue 18: Unexpected Azure Costs

**Symptoms:**
- Azure bill higher than expected
- Cost alerts triggering

**Diagnosis:**
```powershell
# Check current costs
az consumption usage list \
  --start-date 2025-10-01 \
  --end-date 2025-10-06

# Check resource costs
az consumption usage list \
  --resource-group rg-azure-advisor-reports-prod
```

**Common Causes:**

**Cause 1: Auto-scaling Out of Control**
- Check App Service instance count
- Verify auto-scale rules

**Solution:**
```powershell
# Set maximum instance limit
az monitor autoscale update \
  --resource-group rg-azure-advisor-reports-prod \
  --name <autoscale-setting-name> \
  --max-count 5
```

**Cause 2: Large Blob Storage Usage**
- Check blob storage size
- Old reports not being cleaned up

**Solution:**
1. Implement blob lifecycle policy (delete blobs >90 days old)
2. Archive old reports to cool/archive tier

**Cause 3: Database Over-provisioned**
- Using higher tier than needed

**Solution:**
```powershell
# Scale down database if not fully utilized
az postgres flexible-server update \
  --resource-group rg-azure-advisor-reports-prod \
  --name psql-advisor-prod \
  --sku-name Standard_D2s_v3
```

---

## Error Code Reference

### Frontend Error Codes

| Error Code | Message | Cause | Solution |
|------------|---------|-------|----------|
| **AUTH001** | Authentication failed | Azure AD login issue | Check Azure AD config, clear cookies |
| **AUTH002** | Token expired | Access token expired | Refresh page or login again |
| **AUTH003** | Invalid token | Token validation failed | Logout and login again |
| **API001** | API connection failed | Backend unreachable | Check backend health, CORS config |
| **API002** | Request timeout | Request took >30s | Check network, backend performance |
| **UPLOAD001** | File upload failed | Upload to backend failed | Check file size, network connection |
| **UPLOAD002** | Invalid file format | Not a CSV file | Ensure file is .csv format |
| **REPORT001** | Report generation failed | Backend processing error | Check report details for error message |
| **REPORT002** | Report not found | Report ID doesn't exist | Verify report ID, may have been deleted |

### Backend Error Codes

| Error Code | Message | Cause | Solution |
|------------|---------|-------|----------|
| **DB001** | Database connection failed | Can't connect to PostgreSQL | Check database status, connection string |
| **DB002** | Query timeout | Database query took too long | Optimize query, check indexes |
| **REDIS001** | Redis connection failed | Can't connect to Redis | Check Redis status, connection string |
| **STORAGE001** | Blob storage error | Can't access Azure Blob Storage | Check connection string, permissions |
| **CSV001** | CSV parsing error | Invalid CSV format | Check CSV structure, encoding |
| **CSV002** | Missing required columns | CSV doesn't have required fields | Verify CSV is from Azure Advisor |
| **PROC001** | Processing timeout | Task exceeded time limit | Check Celery workers, increase timeout |
| **PROC002** | Processing failed | Unexpected error during processing | Check logs for details |
| **GEN001** | Report generation error | PDF/HTML generation failed | Check template, memory usage |
| **GEN002** | Template rendering error | Missing template variables | Check template code |

### HTTP Status Codes

| Status Code | Meaning | Common Causes | Action |
|-------------|---------|---------------|--------|
| **400** | Bad Request | Invalid input data | Check request payload |
| **401** | Unauthorized | Not logged in or token expired | Login again |
| **403** | Forbidden | Insufficient permissions | Check user role, contact admin |
| **404** | Not Found | Resource doesn't exist | Verify resource ID |
| **429** | Too Many Requests | Rate limit exceeded | Wait and retry |
| **500** | Internal Server Error | Server-side error | Check backend logs |
| **502** | Bad Gateway | Backend not responding | Check backend health |
| **503** | Service Unavailable | Server overloaded or down | Wait and retry, check status |
| **504** | Gateway Timeout | Request took too long | Check backend performance |

---

## Support Escalation

### When to Escalate

**Escalate immediately for:**
- Data loss or corruption
- Security breach or vulnerability
- Complete application outage >30 minutes
- Critical bugs affecting all users
- Database failures

**Escalate within 4 hours for:**
- High-priority bugs affecting multiple users
- Performance degradation >50%
- Feature not working for specific user group
- Reports consistently failing

**Escalate within 24 hours for:**
- Low-priority bugs
- Feature requests
- Documentation issues
- Enhancement suggestions

### Escalation Levels

**Level 1: First Line Support**
- Handle common user questions
- Provide workarounds for known issues
- Guide users through standard procedures
- Response time: <1 hour

**Level 2: Technical Support**
- Investigate technical issues
- Access logs and diagnostics
- Perform configuration changes
- Response time: <4 hours

**Level 3: Engineering Team**
- Fix bugs and defects
- Implement hotfixes
- Perform emergency maintenance
- Response time: <8 hours

**Level 4: Leadership/CTO**
- Business-critical decisions
- External communication
- Major incident coordination
- Response time: <2 hours for critical issues

### Escalation Contact Information

| Level | Contact | Email | Phone | Hours |
|-------|---------|-------|-------|-------|
| **L1 Support** | Support Team | support@yourcompany.com | 1-800-XXX-XXXX | 24/7 |
| **L2 Technical** | Tech Team | techsupport@yourcompany.com | Internal only | Business hours |
| **L3 Engineering** | Dev Team | devteam@yourcompany.com | On-call rotation | 24/7 on-call |
| **L4 Leadership** | CTO | cto@yourcompany.com | XXX-XXX-XXXX | On-call for critical |

### Creating a Support Ticket

**Required Information:**

1. **User Information:**
   - Name and email
   - Organization
   - User role

2. **Issue Description:**
   - What were you trying to do?
   - What happened instead?
   - When did this start happening?

3. **Steps to Reproduce:**
   - Step-by-step instructions
   - Expected result
   - Actual result

4. **Environment Details:**
   - Browser (if frontend issue)
   - Operating system
   - Time of issue (with timezone)

5. **Supporting Information:**
   - Screenshots or screen recording
   - Error messages (full text)
   - Report ID or client ID (if applicable)
   - Any workarounds attempted

6. **Impact Assessment:**
   - How many users affected?
   - Is there a workaround?
   - Business impact (high/medium/low)
   - Urgency (immediate/can wait)

### Support Ticket Template

```
Title: [Brief description of issue]

Severity: [Critical / High / Medium / Low]

Description:
[Detailed description of the issue]

Steps to Reproduce:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Expected Result:
[What should happen]

Actual Result:
[What actually happens]

Environment:
- Browser: [e.g., Chrome 118]
- OS: [e.g., Windows 11]
- User: [email]
- Time: [2025-10-06 14:30 UTC]

Additional Information:
[Any other relevant details]

Attachments:
[Screenshots, logs, etc.]
```

---

## Appendix: Useful Commands

### Quick Diagnostics

```powershell
# Check all Azure services status
az resource list \
  --resource-group rg-azure-advisor-reports-prod \
  --output table

# Check all App Services
az webapp list \
  --resource-group rg-azure-advisor-reports-prod \
  --output table

# Check database status
az postgres flexible-server show \
  --resource-group rg-azure-advisor-reports-prod \
  --name psql-advisor-prod \
  --query "{Name:name, State:state, Version:version, Tier:sku.tier}"

# Check Redis status
az redis show \
  --resource-group rg-azure-advisor-reports-prod \
  --name redis-advisor-prod \
  --query "{Name:name, Status:provisioningState, RedisVersion:redisVersion}"
```

### Log Viewing

```powershell
# View backend logs (live)
az webapp log tail \
  --resource-group rg-azure-advisor-reports-prod \
  --name app-advisor-backend-prod

# Download log files
az webapp log download \
  --resource-group rg-azure-advisor-reports-prod \
  --name app-advisor-backend-prod \
  --log-file backend-logs.zip
```

### Quick Fixes

```powershell
# Restart all app services
$apps = @('app-advisor-frontend-prod', 'app-advisor-backend-prod')
foreach ($app in $apps) {
    az webapp restart --resource-group rg-azure-advisor-reports-prod --name $app
}

# Clear Redis cache
az redis force-reboot \
  --resource-group rg-azure-advisor-reports-prod \
  --name redis-advisor-prod \
  --reboot-type AllNodes

# Restart database (brief downtime)
az postgres flexible-server restart \
  --resource-group rg-azure-advisor-reports-prod \
  --name psql-advisor-prod
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-06 | Documentation Team | Initial troubleshooting guide |

---

**Related Documents:**
- [USER_MANUAL.md](USER_MANUAL.md) - Section 8 has user-level troubleshooting
- [ADMIN_GUIDE.md](ADMIN_GUIDE.md) - Section 12 has admin-level troubleshooting
- [FAQ.md](FAQ.md) - Common questions and answers
- [DISASTER_RECOVERY_PLAN.md](DISASTER_RECOVERY_PLAN.md) - Recovery procedures
- [MONITORING_SETUP.md](MONITORING_SETUP.md) - Monitoring and alerting

---

**Need More Help?**
- Email: support@yourcompany.com
- Phone: 1-800-XXX-XXXX
- Chat: Click chat icon in bottom-right of platform
- Community Forum: community.yourplatform.com

---

**End of Troubleshooting Guide**
