# Quick Fix Reference - Database Configuration

## TL;DR - What Was Fixed

Django was loading with dummy backend because:
1. WSGI pointed to settings package instead of production.py
2. Production.py didn't support DATABASE_URL

**Files Changed**: 3 files
- `azure_advisor_reports/settings/production.py` - Added DATABASE_URL support
- `azure_advisor_reports/wsgi.py` - Points to production.py now
- `azure_advisor_reports/asgi.py` - Points to production.py now

---

## Azure Container Apps - Set This ONE Variable

```bash
DATABASE_URL=postgresql://user:password@host.postgres.database.azure.com:5432/dbname?sslmode=require
```

Example:
```bash
DATABASE_URL=postgresql://azurereportadmin:PTPn7JrjUuLF%403Qs@advisor-reports-db-prod.postgres.database.azure.com:5432/advisor_reports?sslmode=require
```

**That's it!** The code now reads DATABASE_URL automatically.

---

## Azure CLI - Quick Setup

```bash
# Set DATABASE_URL as secret
az containerapp update \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --set-env-vars "DATABASE_URL=secretref:database-url" \
  --secrets "database-url=postgresql://user:pass@host:5432/db?sslmode=require"

# Restart app
az containerapp revision restart \
  --name azure-advisor-reports \
  --resource-group your-rg
```

---

## Verify It Works

### Check Logs
```bash
az containerapp logs show \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --follow
```

**Look for**:
- ✓ "Database engine: django.db.backends.postgresql"
- ✗ "Database backend: django.db.backends.dummy" (BAD)

### Test Connection
```bash
az containerapp exec \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --command "python manage.py check"
```

**Expected**: "System check identified no issues"

### Run Migrations
```bash
az containerapp exec \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --command "python manage.py migrate"
```

---

## Troubleshooting

### Still Getting Dummy Backend?

1. **Check if DATABASE_URL is set**:
   ```bash
   az containerapp show \
     --name azure-advisor-reports \
     --resource-group your-rg \
     --query "properties.template.containers[0].env" -o table
   ```

2. **Verify password is URL-encoded**:
   - Special characters in password must be encoded
   - `@` becomes `%40`
   - `#` becomes `%23`
   - `!` becomes `%21`
   - Example: `Pass@123` → `Pass%40123`

3. **Check password in Azure Portal**:
   - Go to PostgreSQL server
   - Reset password if needed
   - Update DATABASE_URL with new password

### Connection Refused?

1. **Check PostgreSQL firewall**:
   ```bash
   az postgres flexible-server firewall-rule create \
     --resource-group your-rg \
     --name advisor-reports-db-prod \
     --rule-name AllowAzureServices \
     --start-ip-address 0.0.0.0 \
     --end-ip-address 0.0.0.0
   ```

2. **Verify server hostname**:
   ```bash
   az postgres flexible-server show \
     --resource-group your-rg \
     --name advisor-reports-db-prod \
     --query "fullyQualifiedDomainName"
   ```

### Import Errors?

Make sure requirements.txt has:
```
dj-database-url>=2.0.0
psycopg2-binary>=2.9.9
```

---

## Local Development

### Option 1: Use DATABASE_URL (Like Production)
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/azure_advisor_reports"
export DJANGO_SETTINGS_MODULE="azure_advisor_reports.settings.production"
python manage.py runserver
```

### Option 2: Use Development Settings (Individual Vars)
```bash
export DJANGO_SETTINGS_MODULE="azure_advisor_reports.settings.development"
python manage.py runserver
```

Development settings use DB_NAME, DB_USER, etc. from .env file.

---

## Key Files Reference

### Production Settings
`azure_advisor_reports/settings/production.py`
- Reads DATABASE_URL first
- Falls back to DB_NAME, DB_USER, etc.
- Handles test mode with SQLite

### WSGI (Azure Container Apps Entry Point)
`azure_advisor_reports/wsgi.py`
- Now defaults to production settings
- Can be overridden with DJANGO_SETTINGS_MODULE env var

### Diagnostic Script
`diagnose_db_issue.py`
- Run anytime: `python diagnose_db_issue.py`
- Shows what Django sees
- Identifies configuration issues

---

## What If I Want Individual DB Variables?

**You can!** The code supports both:

```bash
# Remove DATABASE_URL, set these instead:
DB_NAME=advisor_reports
DB_USER=azurereportadmin
DB_PASSWORD=your_password
DB_HOST=advisor-reports-db-prod.postgres.database.azure.com
DB_PORT=5432
```

But DATABASE_URL is preferred for cloud deployments (simpler, more secure).

---

## Success Checklist

After deploying the fix:

- [ ] DATABASE_URL is set in Azure Container App
- [ ] Container App restarted
- [ ] Logs show PostgreSQL backend (not dummy)
- [ ] `python manage.py check` passes
- [ ] `python manage.py migrate` works
- [ ] Application can query database
- [ ] No errors in Application Insights

---

## Emergency Rollback

If something breaks:

```bash
# List revisions
az containerapp revision list \
  --name azure-advisor-reports \
  --resource-group your-rg -o table

# Activate previous working revision
az containerapp revision activate \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --revision <previous-revision-name>
```

---

## Need More Details?

See these files:
- `CRITICAL_FIX_SUMMARY.md` - Full technical explanation
- `DATABASE_CONFIG_FIX.md` - Detailed analysis
- `DEPLOYMENT_CHECKLIST.md` - Complete deployment guide

---

**Last Updated**: 2025-10-27
**Status**: Production Ready
**Tested**: Azure Container Apps + Azure PostgreSQL
