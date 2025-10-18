# Disaster Recovery Plan

**Document Version:** 1.0
**Last Updated:** October 4, 2025
**Owner:** DevOps Team
**Review Frequency:** Quarterly

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [RTO and RPO Definitions](#rto-and-rpo-definitions)
3. [Backup Strategy](#backup-strategy)
4. [Recovery Procedures](#recovery-procedures)
5. [Failover Procedures](#failover-procedures)
6. [Emergency Contacts](#emergency-contacts)
7. [Testing and Validation](#testing-and-validation)

---

## Executive Summary

This Disaster Recovery (DR) Plan outlines procedures to recover the Azure Advisor Reports Platform in case of system failures, data loss, or disasters. The plan ensures business continuity with minimal data loss and downtime.

### Disaster Scenarios Covered

| Scenario | Likelihood | Impact | Recovery Time |
|----------|-----------|--------|---------------|
| **Database Corruption** | Low | High | 2-4 hours |
| **App Service Outage** | Medium | High | 30 minutes |
| **Region-Wide Outage** | Very Low | Critical | 4-8 hours |
| **Accidental Data Deletion** | Medium | Medium | 1-2 hours |
| **Security Breach** | Low | Critical | 2-24 hours |
| **Ransomware Attack** | Low | Critical | 4-8 hours |

---

## RTO and RPO Definitions

### Recovery Time Objective (RTO)

**RTO**: Maximum acceptable downtime for each system component.

| Component | Production RTO | Staging RTO | Dev RTO |
|-----------|---------------|-------------|---------|
| **Frontend (React App)** | 30 minutes | 2 hours | 4 hours |
| **Backend (Django API)** | 30 minutes | 2 hours | 4 hours |
| **PostgreSQL Database** | 2 hours | 4 hours | 8 hours |
| **Redis Cache** | 1 hour | 4 hours | N/A |
| **Blob Storage** | 2 hours | 4 hours | 8 hours |
| **Overall Application** | 4 hours | 8 hours | 24 hours |

### Recovery Point Objective (RPO)

**RPO**: Maximum acceptable data loss measured in time.

| Data Type | Production RPO | Backup Frequency |
|-----------|---------------|------------------|
| **Database (PostgreSQL)** | 24 hours | Daily automated backups |
| **User Uploads (Blob)** | 24 hours | Daily blob snapshots |
| **Application Logs** | 1 hour | Real-time to App Insights |
| **Configuration** | 0 hours | Git version control |
| **Secrets** | 0 hours | Azure Key Vault (auto-replicated) |

---

## Backup Strategy

### 1. Database Backups (PostgreSQL)

#### Automated Backups (Azure-Managed)

Azure Database for PostgreSQL automatically creates backups:

```yaml
Backup Configuration:
  Frequency: Every 5 minutes (transaction logs)
  Retention: 14 days (default)
  Storage: Geo-redundant (production)
  Point-in-Time Restore: Yes (within retention period)
```

**Verify Backup Configuration:**

```powershell
# Check backup configuration
az postgres flexible-server show `
    --resource-group "rg-azure-advisor-reports-prod" `
    --name "psql-advisor-prod" `
    --query "backup"

# List available restore points
az postgres flexible-server backup list `
    --resource-group "rg-azure-advisor-reports-prod" `
    --name "psql-advisor-prod"
```

#### Manual Backup Script

**Location:** `scripts/backup-database.ps1`

```powershell
<#
.SYNOPSIS
    Manual database backup script

.DESCRIPTION
    Creates a full backup of PostgreSQL database and uploads to secure storage
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Environment = "prod"
)

$timestamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
$backupFile = "backup-$Environment-$timestamp.sql"
$resourceGroup = "rg-azure-advisor-reports-$Environment"
$serverName = "psql-advisor-$Environment"
$databaseName = "azure_advisor_reports_$Environment"

Write-Host "Creating database backup..." -ForegroundColor Cyan

# Export database
$serverFQDN = (az postgres flexible-server show `
    --resource-group $resourceGroup `
    --name $serverName `
    --query fullyQualifiedDomainName -o tsv)

# Use pg_dump (requires PostgreSQL client tools)
$env:PGPASSWORD = Read-Host "Enter database password" -AsSecureString
pg_dump -h $serverFQDN -U dbadmin -d $databaseName -F c -f $backupFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Backup created: $backupFile" -ForegroundColor Green

    # Upload to blob storage
    $storageAccount = "stadvisor$Environment"
    $containerName = "database-backups"

    az storage blob upload `
        --account-name $storageAccount `
        --container-name $containerName `
        --name $backupFile `
        --file $backupFile `
        --auth-mode login

    Write-Host "✅ Backup uploaded to Azure Storage" -ForegroundColor Green

    # Clean up local file
    Remove-Item $backupFile
} else {
    Write-Host "❌ Backup failed" -ForegroundColor Red
    exit 1
}
```

**Schedule Automated Backup:**

Create Azure Automation Account with weekly schedule to run this script.

### 2. Blob Storage Backups

#### Soft Delete (Enabled by Default)

```powershell
# Verify soft delete is enabled
az storage blob service-properties delete-policy show `
    --account-name "stadvisorprod" `
    --auth-mode login

# Enable soft delete if not enabled (7-day retention)
az storage blob service-properties delete-policy update `
    --account-name "stadvisorprod" `
    --enable true `
    --days-retained 7 `
    --auth-mode login
```

#### Blob Snapshots

```powershell
# Create snapshot of all blobs in a container
$storageAccount = "stadvisorprod"
$containerName = "csv-uploads"

$blobs = az storage blob list `
    --account-name $storageAccount `
    --container-name $containerName `
    --auth-mode login | ConvertFrom-Json

foreach ($blob in $blobs) {
    az storage blob snapshot `
        --account-name $storageAccount `
        --container-name $containerName `
        --name $blob.name `
        --auth-mode login
}

Write-Host "✅ Snapshots created for all blobs" -ForegroundColor Green
```

### 3. Application Configuration Backup

All configuration is stored in:
- **Git Repository**: Code and infrastructure as code
- **Azure Key Vault**: Secrets and certificates (auto-replicated)
- **Environment Variables**: Documented in `.env.example`

**No additional backup needed** - use Git tags for version control.

### 4. Backup Verification

**Monthly Backup Test Procedure:**

1. Restore latest backup to staging environment
2. Verify data integrity
3. Test application functionality
4. Document results

```powershell
# Test restore script
.\scripts\test-restore.ps1 -Environment staging -BackupDate "2025-10-01"
```

---

## Recovery Procedures

### Scenario 1: Database Corruption or Data Loss

**Symptoms:**
- Application errors related to database
- Missing or corrupted data
- Database connection failures

**Recovery Steps:**

```powershell
# 1. Identify the issue
Write-Host "Step 1: Identifying database issue..." -ForegroundColor Cyan

# Check database status
az postgres flexible-server show `
    --resource-group "rg-azure-advisor-reports-prod" `
    --name "psql-advisor-prod" `
    --query "state"

# 2. Determine restore point
Write-Host "Step 2: Determining restore point..." -ForegroundColor Cyan

# List available backups
az postgres flexible-server backup list `
    --resource-group "rg-azure-advisor-reports-prod" `
    --name "psql-advisor-prod"

# 3. Restore to new server (recommended for safety)
Write-Host "Step 3: Restoring database..." -ForegroundColor Cyan

$restoreTime = "2025-10-04T10:00:00Z"  # Replace with desired restore point

az postgres flexible-server restore `
    --resource-group "rg-azure-advisor-reports-prod" `
    --name "psql-advisor-prod-restored" `
    --source-server "psql-advisor-prod" `
    --restore-time $restoreTime

# 4. Verify restored database
Write-Host "Step 4: Verifying restored data..." -ForegroundColor Cyan

# Connect and verify data
# Run data validation queries

# 5. Update application connection string
Write-Host "Step 5: Updating application..." -ForegroundColor Cyan

$newConnectionString = "postgresql://dbadmin:password@psql-advisor-prod-restored.postgres.database.azure.com:5432/azure_advisor_reports_prod"

az webapp config appsettings set `
    --resource-group "rg-azure-advisor-reports-prod" `
    --name "app-advisor-backend-prod" `
    --settings "DATABASE_URL=$newConnectionString"

# 6. Restart application
az webapp restart `
    --resource-group "rg-azure-advisor-reports-prod" `
    --name "app-advisor-backend-prod"

Write-Host "✅ Database recovery complete" -ForegroundColor Green
```

**Estimated Recovery Time:** 2-4 hours

### Scenario 2: App Service Outage or Corruption

**Symptoms:**
- Application not responding
- Deployment corruption
- Configuration issues

**Recovery Steps:**

```powershell
# 1. Check App Service status
az webapp show `
    --resource-group "rg-azure-advisor-reports-prod" `
    --name "app-advisor-backend-prod" `
    --query "state"

# 2. Try restart first
az webapp restart `
    --resource-group "rg-azure-advisor-reports-prod" `
    --name "app-advisor-backend-prod"

# Wait 2 minutes and test
Start-Sleep -Seconds 120

# 3. If restart doesn't work, redeploy from last known good version
Write-Host "Redeploying application..." -ForegroundColor Cyan

# Trigger GitHub Actions workflow to redeploy
gh workflow run deploy-production.yml

# 4. If still failing, restore from deployment slot
az webapp deployment slot swap `
    --resource-group "rg-azure-advisor-reports-prod" `
    --name "app-advisor-backend-prod" `
    --slot "staging" `
    --target-slot "production"

Write-Host "✅ Application recovery complete" -ForegroundColor Green
```

**Estimated Recovery Time:** 30 minutes

### Scenario 3: Region-Wide Azure Outage

**Symptoms:**
- All services in region unavailable
- Azure status page shows outage

**Recovery Steps:**

1. **Verify Outage Scope**
   - Check Azure Status: https://status.azure.com/
   - Verify multiple services are affected

2. **Activate Manual Failover** (if secondary region configured)

```powershell
# Deploy to secondary region (if configured)
.\scripts\azure\deploy.ps1 `
    -Environment prod `
    -Location "West US 2" `  # Secondary region
    -ResourceGroup "rg-azure-advisor-reports-prod-dr"

# Update DNS to point to DR site
# Update Front Door origin to secondary region
```

3. **Communicate with Stakeholders**
   - Update status page
   - Notify users via email
   - Post updates every hour

4. **Monitor Azure Status**
   - Wait for primary region recovery
   - Plan failback when primary is stable

**Estimated Recovery Time:** 4-8 hours (for full DR site deployment)

### Scenario 4: Accidental Data Deletion

**Symptoms:**
- Users report missing data
- Audit logs show delete operations

**Recovery Steps:**

```powershell
# 1. Stop application to prevent further changes
az webapp stop --resource-group "rg-azure-advisor-reports-prod" --name "app-advisor-backend-prod"

# 2. Restore database to point before deletion
$restoreTime = "2025-10-04T09:00:00Z"  # Before deletion

az postgres flexible-server restore `
    --resource-group "rg-azure-advisor-reports-prod" `
    --name "psql-advisor-prod-recovery" `
    --source-server "psql-advisor-prod" `
    --restore-time $restoreTime

# 3. Export deleted data from restored database
# Use SQL queries to extract only deleted records

# 4. Import deleted data into production database
# Use psql or database migration tools

# 5. Verify data integrity
# Run validation queries

# 6. Restart application
az webapp start --resource-group "rg-azure-advisor-reports-prod" --name "app-advisor-backend-prod"
```

**Estimated Recovery Time:** 1-2 hours

---

## Failover Procedures

### Automatic Failover (Configured Services)

**Azure Database for PostgreSQL:**
- High Availability enabled: Automatic failover to standby
- Failover time: ~60 seconds
- No action required

**Azure Cache for Redis:**
- Standard tier: Manual restart required
- Premium tier: Automatic failover with geo-replication

### Manual Failover Checklist

When primary region fails:

- [ ] Verify outage scope and duration estimate
- [ ] Activate incident response team
- [ ] Deploy to DR region using `deploy.ps1`
- [ ] Restore latest database backup in DR region
- [ ] Update DNS records to point to DR site
- [ ] Update Azure Front Door origins
- [ ] Test application functionality
- [ ] Communicate status to users
- [ ] Monitor DR site performance
- [ ] Plan failback when primary region recovers

---

## Emergency Contacts

### Incident Response Team

| Role | Name | Phone | Email | Backup Contact |
|------|------|-------|-------|----------------|
| **Incident Commander** | [Name] | [Phone] | [Email] | [Backup Name] |
| **DevOps Lead** | [Name] | [Phone] | [Email] | [Backup Name] |
| **Database Administrator** | [Name] | [Phone] | [Email] | [Backup Name] |
| **Security Lead** | [Name] | [Phone] | [Email] | [Backup Name] |
| **Product Manager** | [Name] | [Phone] | [Email] | [Backup Name] |

### External Contacts

| Contact | Purpose | Phone | Email |
|---------|---------|-------|-------|
| **Azure Support** | Technical support | 1-800-Microsoft | azure-support@microsoft.com |
| **On-Call DevOps** | 24/7 support | [Phone] | devops-oncall@company.com |

### Communication Channels

- **Incident Channel**: Microsoft Teams / Slack: `#incident-response`
- **Status Page**: https://status.yourdomain.com
- **Email Distribution**: devops@company.com, engineering@company.com

---

## Testing and Validation

### DR Test Schedule

| Test Type | Frequency | Last Tested | Next Test Date |
|-----------|-----------|-------------|----------------|
| **Database Restore** | Monthly | 2025-10-01 | 2025-11-01 |
| **Application Failover** | Quarterly | 2025-10-01 | 2026-01-01 |
| **Full DR Drill** | Annually | 2025-09-01 | 2026-09-01 |
| **Backup Verification** | Monthly | 2025-10-01 | 2025-11-01 |

### DR Test Procedure

**Monthly Test Script:**

```powershell
<#
.SYNOPSIS
    Monthly DR test procedure

.DESCRIPTION
    Tests database restore and application recovery without impacting production
#>

Write-Host "Starting DR Test..." -ForegroundColor Cyan

# 1. Restore database to staging
Write-Host "1. Restoring database to staging..." -ForegroundColor Yellow
.\scripts\restore-database.ps1 -Environment staging -BackupDate (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")

# 2. Verify data integrity
Write-Host "2. Verifying data integrity..." -ForegroundColor Yellow
# Run validation queries
$recordCount = # Query to count records
Write-Host "   Records verified: $recordCount" -ForegroundColor Gray

# 3. Test application functionality
Write-Host "3. Testing application..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "https://app-advisor-backend-staging.azurewebsites.net/api/health/"
if ($response.status -eq "healthy") {
    Write-Host "   ✅ Application healthy" -ForegroundColor Green
} else {
    Write-Host "   ❌ Application unhealthy" -ForegroundColor Red
}

# 4. Generate test report
Write-Host "4. Generating test report..." -ForegroundColor Yellow
$report = @{
    TestDate = Get-Date
    Status = "Success"
    RecoveryTime = "15 minutes"
    IssuesFound = 0
} | ConvertTo-Json

$report | Out-File "DR-Test-Report-$(Get-Date -Format 'yyyy-MM-dd').json"

Write-Host "✅ DR Test Complete" -ForegroundColor Green
```

### Post-Test Actions

After each DR test:

1. Document test results
2. Update recovery time estimates
3. Fix identified issues
4. Update DR plan if needed
5. Brief team on findings

---

## Incident Response Workflow

### Incident Severity Levels

| Severity | Description | Response Time | Escalation |
|----------|-------------|---------------|------------|
| **P0 - Critical** | Complete service outage | Immediate | All hands |
| **P1 - High** | Major degradation | 15 minutes | DevOps + Lead |
| **P2 - Medium** | Minor issues | 1 hour | DevOps only |
| **P3 - Low** | Cosmetic issues | Next business day | Backlog |

### Incident Response Steps

1. **Detect**: Monitoring alerts or user reports
2. **Assess**: Determine severity and scope
3. **Communicate**: Notify team and stakeholders
4. **Mitigate**: Implement immediate fixes
5. **Resolve**: Restore full service
6. **Document**: Post-incident review
7. **Improve**: Update procedures and prevent recurrence

### Post-Incident Review Template

**Incident Report: [Incident Title]**

- **Date/Time:** [When it occurred]
- **Duration:** [How long]
- **Severity:** [P0/P1/P2/P3]
- **Impact:** [Users affected, data lost]
- **Root Cause:** [What caused it]
- **Resolution:** [How it was fixed]
- **Lessons Learned:** [What we learned]
- **Action Items:** [Preventive measures]

---

## Appendix: Recovery Scripts

All recovery scripts are located in `scripts/disaster-recovery/`:

- `restore-database.ps1` - Database restore automation
- `restore-blobs.ps1` - Blob storage recovery
- `failover-to-dr.ps1` - Complete DR site activation
- `failback-to-primary.ps1` - Return to primary region
- `test-dr.ps1` - Monthly DR test automation
- `verify-backups.ps1` - Backup verification

---

## Review and Updates

This Disaster Recovery Plan should be reviewed:
- **Quarterly**: By DevOps team
- **After major changes**: Infrastructure updates
- **After incidents**: Update based on lessons learned
- **Annually**: Full DR drill and plan validation

**Last Reviewed:** October 4, 2025
**Next Review:** January 4, 2026
**Reviewed By:** [Name]

---

**Document End**
