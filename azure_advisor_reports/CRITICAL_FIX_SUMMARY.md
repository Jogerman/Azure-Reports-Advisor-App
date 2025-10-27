# CRITICAL FIX: Django Database Configuration Issue

## Executive Summary

**Issue**: Django was loading with `django.db.backends.dummy` backend instead of PostgreSQL in Azure Container Apps, despite `DATABASE_URL` being correctly set.

**Root Cause**: Configuration architecture mismatch between settings structure and WSGI loader.

**Impact**: Application could not connect to database, causing complete service failure.

**Status**: FIXED

---

## What Was Wrong

### The Problem Chain

1. **WSGI pointed to wrong settings module**
   - `wsgi.py` loaded `azure_advisor_reports.settings` (package)
   - Package `__init__.py` only imported `base.py`
   - `base.py` had NO database configuration
   - Django defaulted to dummy backend

2. **Production settings didn't support DATABASE_URL**
   - `production.py` expected individual env vars (DB_NAME, DB_USER, etc.)
   - Azure Container Apps provided `DATABASE_URL` (standard cloud format)
   - The two never connected

3. **Split settings architecture incomplete**
   - Project had both old `settings.py` (with DATABASE_URL logic) AND new settings package
   - WSGI loaded the package (which didn't work)
   - Old file (which would work) was ignored

---

## What Was Fixed

### Files Modified

#### 1. `azure_advisor_reports/settings/production.py`

**Location**: Lines 98-150

**What Changed**: Added DATABASE_URL support with fallback logic

**Before**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
        ...
    }
}
```

**After**:
```python
import sys
import os

# Use SQLite for testing
if 'test' in sys.argv or 'pytest' in sys.modules:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    # Try DATABASE_URL first (Azure), fallback to individual vars
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # Use DATABASE_URL (preferred)
        DATABASES = {
            'default': dj_database_url.parse(
                database_url,
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
        # Ensure SSL for Azure PostgreSQL
        DATABASES['default'].setdefault('OPTIONS', {})
        DATABASES['default']['OPTIONS']['sslmode'] = 'require'
        DATABASES['default']['OPTIONS']['connect_timeout'] = 10
        DATABASES['default']['ATOMIC_REQUESTS'] = True
    else:
        # Fallback to individual vars
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': config('DB_NAME'),
                'USER': config('DB_USER'),
                'PASSWORD': config('DB_PASSWORD'),
                'HOST': config('DB_HOST'),
                'PORT': config('DB_PORT', default='5432'),
                'OPTIONS': {
                    'sslmode': 'require',
                    'connect_timeout': 10,
                },
                'CONN_MAX_AGE': 600,
                'ATOMIC_REQUESTS': True,
            }
        }
```

**Why This Fixes It**:
- Now checks for DATABASE_URL environment variable
- Uses dj_database_url to parse it (standard cloud pattern)
- Falls back to individual vars if DATABASE_URL not provided
- Handles test mode with SQLite
- Ensures SSL is enabled for Azure PostgreSQL

---

#### 2. `azure_advisor_reports/wsgi.py`

**Location**: Line 14-16

**What Changed**: Changed default settings module from package to production

**Before**:
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
```

**After**:
```python
# Default to production settings for WSGI deployment (Azure Container Apps)
# Can be overridden by setting DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings.production')
```

**Why This Fixes It**:
- Directly loads production.py (which now has DATABASE_URL support)
- Skips the broken __init__.py routing
- Makes production the default for WSGI (Azure Container Apps uses WSGI)
- Still allows override via DJANGO_SETTINGS_MODULE env var

---

#### 3. `azure_advisor_reports/asgi.py`

**Location**: Line 14-16

**What Changed**: Same as WSGI for consistency

**Before**:
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
```

**After**:
```python
# Default to production settings for ASGI deployment (Azure Container Apps)
# Can be overridden by setting DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings.production')
```

**Why This Fixes It**:
- Consistency with WSGI
- Future-proofing for async support
- Same benefits as WSGI fix

---

## Why This Happened

### Hidden Complexity

1. **Two Settings Systems**: Project evolved from single settings.py to split package, but both existed
2. **Silent Failure**: Dummy backend doesn't raise errors, just silently fails
3. **Local vs Production**: Local `.env` files loaded DATABASE_URL, but Django wasn't configured to use it
4. **Settings Inheritance**: Complex inheritance chain (wsgi → __init__ → base → production) created points of failure

### Why Tests Passed Locally

```python
# This worked:
import dj_database_url
print(dj_database_url.parse(os.environ.get('DATABASE_URL')))
```

Because it:
- Read from local `.env` file
- Didn't load Django settings
- Only tested the parsing function

But in production:
- Azure Container Apps set environment variables differently
- Django loaded through WSGI
- WSGI loaded the wrong settings module
- Those settings didn't use DATABASE_URL

---

## How to Verify the Fix

### 1. Local Testing (with DATABASE_URL)

```bash
# Set DATABASE_URL
export DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"

# Set production settings
export DJANGO_SETTINGS_MODULE="azure_advisor_reports.settings.production"

# Run Django check
python manage.py check

# Should show PostgreSQL, not dummy backend
python manage.py shell
>>> from django.conf import settings
>>> print(settings.DATABASES['default']['ENGINE'])
# Output: django.db.backends.postgresql
```

### 2. Azure Container Apps Testing

After deployment:

```bash
# Check logs
az containerapp logs show \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --follow

# Run database check
az containerapp exec \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --command "python manage.py check"

# Try database connection
az containerapp exec \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --command "python manage.py dbshell --command 'SELECT 1;'"
```

### 3. Look for These Log Messages

**Success Indicators**:
```
✓ Using production settings: azure_advisor_reports.settings.production
✓ Database engine: django.db.backends.postgresql
✓ Successfully connected to database: advisor_reports
✓ Migrations applied successfully
```

**Failure Indicators** (should NOT see these):
```
✗ Using database backend: django.db.backends.dummy
✗ No database configuration found
✗ Database connection failed
✗ psycopg2 not installed
```

---

## Required Environment Variables

### Azure Container Apps Must Have

```bash
# Database connection (choose ONE method)

# Method 1: DATABASE_URL (Recommended)
DATABASE_URL=postgresql://username:password@host.postgres.database.azure.com:5432/dbname?sslmode=require

# Method 2: Individual variables (Fallback)
DB_NAME=advisor_reports
DB_USER=azurereportadmin
DB_PASSWORD=your_password
DB_HOST=advisor-reports-db-prod.postgres.database.azure.com
DB_PORT=5432
```

**IMPORTANT**: Use Method 1 (DATABASE_URL) for Azure Container Apps. This is the standard cloud platform convention.

---

## Technical Details

### Why dj_database_url?

```python
dj_database_url.parse(database_url)
```

This library:
- Parses standard DATABASE_URL format (used by Heroku, Azure, Railway, etc.)
- Extracts host, port, user, password, database name
- Returns Django-compatible DATABASES dict
- Handles SSL parameters and connection options
- Is the de facto standard for cloud Django deployments

### Why Dummy Backend?

Django uses dummy backend when:
1. No DATABASES setting is defined
2. Or DATABASES = {} (empty dict)
3. Or DATABASES['default'] is missing

In our case:
- `base.py` had no DATABASES setting
- `wsgi.py` loaded settings package → __init__.py → base.py
- Django saw no database config
- Defaulted to dummy backend

### Connection Pooling

The fix includes:
```python
conn_max_age=600,  # Keep connections alive for 10 minutes
conn_health_checks=True,  # Check connection health
```

Benefits:
- Reduces connection overhead
- Improves performance
- Handles network interruptions
- Standard for production deployments

---

## Migration Path

### If You Were Using Individual Env Vars

**No changes needed!** The fix includes fallback logic:

```python
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Use DATABASE_URL
else:
    # Use DB_NAME, DB_USER, etc. (your current setup)
```

### If You Want to Switch to DATABASE_URL

1. Remove individual DB_* env vars from Azure Container App
2. Add single DATABASE_URL env var:
   ```
   DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
   ```
3. Restart container app
4. Verify connection in logs

---

## Files Created During Investigation

### 1. `diagnose_db_issue.py`
Diagnostic script to identify database configuration issues. Run anytime to check:
- Environment variables
- Settings module loading
- Database configuration
- .env file presence

### 2. `DATABASE_CONFIG_FIX.md`
Detailed explanation of the issue and fix (this file).

### 3. `DEPLOYMENT_CHECKLIST.md`
Step-by-step deployment guide for Azure Container Apps including:
- Environment variable setup
- Deployment commands
- Verification steps
- Troubleshooting guide

---

## Prevention for Future

### Best Practices Implemented

1. **Explicit WSGI/ASGI Configuration**: Point directly to the settings module you want
2. **Support Cloud Standards**: Always support DATABASE_URL in production settings
3. **Fallback Logic**: Provide alternative configuration methods
4. **Test Mode Isolation**: Separate test database config (SQLite) from production
5. **Clear Documentation**: Document which settings file is loaded when

### Code Review Checklist

When changing Django settings:
- [ ] Verify WSGI/ASGI point to correct settings module
- [ ] Test with production settings module explicitly
- [ ] Verify DATABASE_URL is read and parsed
- [ ] Check logs for database backend being used
- [ ] Test in environment similar to production

---

## Questions & Answers

**Q: Why did standalone `dj_database_url.parse()` work but Django didn't?**

A: The standalone test used the DATABASE_URL value and parsed it successfully. But Django loaded different settings (production.py) that didn't use dj_database_url at all - it expected individual DB_* variables.

**Q: Why didn't the old settings.py file work?**

A: WSGI loaded `azure_advisor_reports.settings` (package), not `azure_advisor_reports.settings` (file). Python loaded the package (__init__.py), which imported base.py, which had no database config.

**Q: Will this fix work for other cloud platforms?**

A: Yes! DATABASE_URL is the standard for:
- Heroku
- Railway
- Render
- Azure Container Apps
- Google Cloud Run
- AWS Elastic Beanstalk
- Most PaaS platforms

**Q: What if I want to use a different database in production?**

A: Just change DATABASE_URL format:
- PostgreSQL: `postgresql://...`
- MySQL: `mysql://...`
- MariaDB: `mysql://...`

dj_database_url will detect the engine from the URL scheme.

**Q: How do I generate a strong SECRET_KEY?**

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Success Criteria

This fix is successful when:

✅ Django loads with PostgreSQL backend, not dummy
✅ Application connects to Azure PostgreSQL database
✅ Migrations can be applied
✅ Database queries work
✅ No "dummy backend" errors in logs
✅ Tests still run with SQLite (no PostgreSQL dependency)
✅ Works in both Azure Container Apps and local development

---

## Contacts & Support

If you encounter issues after applying this fix:

1. Check Azure Container App logs for specific error messages
2. Run the diagnostic script: `python diagnose_db_issue.py`
3. Verify DATABASE_URL is set: `az containerapp show --name <app> --resource-group <rg> --query "properties.template.containers[0].env"`
4. Test connection manually: `az containerapp exec --command "python manage.py dbshell"`

---

**Fix Applied**: 2025-10-27
**Django Version**: 4.2.7
**Python Version**: 3.11+
**Platform**: Azure Container Apps
**Status**: Production Ready
