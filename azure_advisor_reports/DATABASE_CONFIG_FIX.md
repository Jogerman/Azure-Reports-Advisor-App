# Django Database Configuration Fix

## Problem Summary

Django was loading with `django.db.backends.dummy` instead of PostgreSQL in Azure Container Apps, despite `DATABASE_URL` being correctly set in the environment.

## Root Cause Analysis

### Multiple Contributing Issues Identified:

#### 1. Split Settings Architecture Mismatch
The project has TWO different settings configurations coexisting:

- **OLD**: Single `settings.py` file (unused) with DATABASE_URL logic
- **NEW**: Split settings package structure:
  - `settings/__init__.py` - Routes to base.py only
  - `settings/base.py` - No DATABASE configuration (causes dummy backend)
  - `settings/development.py` - Uses individual DB env vars
  - `settings/production.py` - Uses individual DB env vars (NOT DATABASE_URL)

#### 2. WSGI Configuration Problem
The `wsgi.py` was pointing to `azure_advisor_reports.settings`, which loaded `settings/__init__.py`, which only imported `base.py` that had NO database configuration. When Django has no DATABASES setting, it defaults to `django.db.backends.dummy`.

#### 3. Production Settings Missing DATABASE_URL Support
The `production.py` file expected individual environment variables:
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

But Azure Container Apps was providing `DATABASE_URL` instead, which was being completely ignored.

#### 4. Settings Routing Logic Incomplete
The `settings/__init__.py` file was not properly routing to environment-specific settings:

```python
# Old code - always loads base.py which has no DATABASE config
from .base import *
```

## The Fix

### Changes Made:

#### 1. Updated `production.py` to Support DATABASE_URL

**File**: `azure_advisor_reports/settings/production.py`

Added logic to:
- Check for `DATABASE_URL` environment variable first (Azure Container Apps standard)
- Parse it using `dj_database_url.parse()`
- Fallback to individual env vars if DATABASE_URL not provided
- Handle test mode with SQLite

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
    # Try DATABASE_URL first (Azure Container Apps), fallback to individual vars
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
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
        # Fallback to individual environment variables
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

#### 2. Updated WSGI to Use Production Settings

**File**: `azure_advisor_reports/wsgi.py`

Changed from:
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
```

To:
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings.production')
```

#### 3. Updated ASGI for Consistency

**File**: `azure_advisor_reports/asgi.py`

Applied same change as WSGI for consistency.

## Azure Container Apps Configuration

### Required Environment Variables

For Azure Container Apps, ensure the following environment variable is set:

```
DATABASE_URL=postgresql://username:password@host:5432/database?sslmode=require
```

Example for Azure PostgreSQL:
```
DATABASE_URL=postgresql://azurereportadmin:PTPn7JrjUuLF%403Qs@advisor-reports-db-prod.postgres.database.azure.com:5432/advisor_reports?sslmode=require
```

### Optional: Override Settings Module

You can also explicitly set the settings module:
```
DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production
```

However, this is now the default in `wsgi.py` and `asgi.py`.

## Verification Steps

### 1. Test Locally with DATABASE_URL

```bash
export DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"
python manage.py check
python manage.py migrate --dry-run
```

### 2. Verify Settings Loading

```python
import os
os.environ['DATABASE_URL'] = 'postgresql://user:pass@host:5432/db'
os.environ['DJANGO_SETTINGS_MODULE'] = 'azure_advisor_reports.settings.production'

import django
django.setup()

from django.conf import settings
print(settings.DATABASES['default']['ENGINE'])
# Should print: django.db.backends.postgresql
```

### 3. Test in Azure Container Apps

Deploy the application and check logs:

```bash
az containerapp logs show --name <app-name> --resource-group <rg-name> --follow
```

Look for database connection logs. You should see PostgreSQL connections, not dummy backend errors.

## Why This Was Hard to Debug

1. **Two settings files**: The old `settings.py` had the correct logic but wasn't being used
2. **Settings package routing**: The `__init__.py` only imported base.py (no DB config)
3. **Silent failure**: Django doesn't error when using dummy backend, it just won't work
4. **Env var vs file**: DATABASE_URL was in `.env` but not in environment when Django loaded
5. **Azure abstraction**: Container Apps environment variables weren't visible during local testing

## Best Practices for Django Settings

### 1. Use Environment-Specific Settings Files

- `base.py` - Common settings
- `development.py` - Local development
- `production.py` - Production (Azure)
- `testing.py` - Test runner

### 2. Always Support DATABASE_URL in Production

Cloud platforms (Azure, Heroku, Railway, etc.) provide DATABASE_URL as standard.

### 3. Explicit WSGI/ASGI Configuration

Point directly to the production settings module in `wsgi.py` and `asgi.py`.

### 4. Environment Variable Priority

```python
# 1. Try DATABASE_URL (cloud standard)
database_url = os.environ.get('DATABASE_URL')

# 2. Fallback to individual vars (local/legacy)
if not database_url:
    # Use DB_NAME, DB_USER, etc.
```

## Testing the Fix

### Local Testing

1. Set DATABASE_URL in your environment or `.env` file
2. Run Django with production settings:
   ```bash
   DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production python manage.py check
   ```

### Azure Container Apps

1. Ensure `DATABASE_URL` is set in Container App environment variables
2. Deploy the updated code
3. Check logs for successful database connection
4. Run migrations:
   ```bash
   az containerapp exec --name <app> --resource-group <rg> --command "python manage.py migrate"
   ```

## Additional Debugging Tools

The diagnostic script `diagnose_db_issue.py` has been created to help identify similar issues:

```bash
python diagnose_db_issue.py
```

This script checks:
- Environment variables
- Settings module routing
- .env file presence
- DATABASE configuration loading
- Settings file structure

## Conclusion

The issue was caused by a mismatch between:
1. Where Django was looking for settings (settings package)
2. What those settings contained (no DATABASE config in base.py)
3. What environment variables were expected (individual DB vars vs DATABASE_URL)

The fix ensures that:
1. Production settings are loaded by default in WSGI/ASGI
2. Production settings support DATABASE_URL (Azure standard)
3. Fallback to individual vars still works for flexibility
4. Test mode uses SQLite (no PostgreSQL dependency for tests)

This fix will work reliably in Azure Container Apps and other cloud platforms that use DATABASE_URL.
