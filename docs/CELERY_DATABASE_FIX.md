# Celery Database Configuration Fix

## Problem Summary

**Root Cause**: The Celery worker process was failing to access the PostgreSQL database due to a critical bug in Django settings configuration that caused the database configuration to be replaced with SQLite in-memory during task execution.

## The Bug: `'pytest' in sys.modules`

### What Went Wrong

The original code in `settings.py` and `settings/production.py` had this pattern:

```python
if 'test' in sys.argv or 'pytest' in sys.modules:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    # PostgreSQL configuration...
```

### Why This Failed in Celery

1. **Non-deterministic module loading**: `'pytest' in sys.modules` checks if pytest has been imported anywhere in the process
2. **pytest installed in production**: pytest was in the production environment (dependencies or development packages)
3. **Celery worker lifecycle**: When Celery workers spawn processes and execute tasks:
   - Parent process loads settings correctly (PostgreSQL)
   - Worker processes may import various modules
   - If any module imports pytest (directly or indirectly), it gets added to `sys.modules`
   - Settings get re-evaluated or checked during task execution
   - `'pytest' in sys.modules` becomes TRUE
   - DATABASES gets set to SQLite, overwriting PostgreSQL config
4. **Works in Gunicorn, fails in Celery**:
   - Gunicorn loads settings once and rarely re-evaluates
   - Celery workers spawn multiple processes and reload modules dynamically

## The Fix

### 1. Removed Dangerous `'pytest' in sys.modules` Check

**Before**:
```python
if 'test' in sys.argv or 'pytest' in sys.modules:
```

**After**:
```python
if 'test' in sys.argv:
```

Only check for explicit test execution via `python manage.py test`, not module presence.

### 2. Fixed Celery Settings Module Loading

**File**: `azure_advisor_reports/celery.py`

**Before**:
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings.development')
```

**After**:
```python
environment = os.environ.get('DJANGO_ENVIRONMENT', 'development').lower()
if environment == 'production':
    settings_module = 'azure_advisor_reports.settings.production'
elif environment == 'staging':
    settings_module = 'azure_advisor_reports.settings.staging'
else:
    settings_module = 'azure_advisor_reports.settings.development'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
```

Now Celery respects the `DJANGO_ENVIRONMENT` variable.

### 3. Hardened Production Database Configuration

**File**: `settings/production.py`

- **Removed** conditional pytest/test checks entirely
- **Changed** from `config()` to `os.environ.get()` for production reliability
- **Added** database validation to fail fast if configuration is missing
- **Added** explicit comments warning against conditional database config

```python
# PRODUCTION ALWAYS uses PostgreSQL - NO conditional logic based on pytest
# Testing should use a separate settings file (settings/testing.py)
# NEVER check for 'pytest' in sys.modules - it's unreliable in production!

database_url = os.environ.get('DATABASE_URL')
if database_url:
    DATABASES = {'default': dj_database_url.parse(database_url, ...)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', ''),
            'USER': os.environ.get('DB_USER', ''),
            # ... direct os.environ.get() calls
        }
    }

# Validate configuration
if not DATABASES['default'].get('NAME'):
    raise ValueError("DATABASE configuration is missing!")
```

### 4. Created Dedicated Testing Settings

**File**: `settings/testing.py`

- Separate settings file specifically for tests
- Uses SQLite in-memory database
- Eager Celery execution (no broker needed)
- Fast password hashers
- Minimal logging

**Usage**:
```bash
pytest --ds=azure_advisor_reports.settings.testing
python manage.py test --settings=azure_advisor_reports.settings.testing
```

### 5. Added Worker Initialization Diagnostics

**File**: `celery.py`

Added `worker_process_init` signal handler to:
- Log which settings module is being used
- Verify database configuration on worker startup
- Test database connection before accepting tasks
- Provide detailed error messages if configuration fails

```python
@worker_process_init.connect
def configure_workers(sender=None, conf=None, **kwargs):
    logger.info(f"Worker initialized with settings module: {settings_module}")
    logger.info(f"Database engine: {db_engine}")
    logger.info(f"Database name: {db_name}")
    # Test connection...
```

## Why python-decouple Can Cause Issues in Celery

The `config()` function from `python-decouple` can behave differently in worker processes:

1. **File reading timing**: Looks for `.env` files at import time
2. **Process isolation**: Worker processes may have different working directories
3. **Environment inheritance**: Child processes inherit environment but may not re-read `.env` files
4. **Cache behavior**: May cache values differently in parent vs child processes

**Solution**: In production settings, use direct `os.environ.get()` instead of `config()`.

## Deployment Checklist

### Required Environment Variables

Set `DJANGO_ENVIRONMENT=production` in your Azure Container App environment variables to ensure Celery uses the production settings module.

Verify these environment variables are set:

**Option 1: DATABASE_URL (Preferred)**
```
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

**Option 2: Individual Variables**
```
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=your_database_host
DB_PORT=5432
```

**Celery Environment**
```
DJANGO_ENVIRONMENT=production
CELERY_BROKER_URL=redis://...
REDIS_URL=redis://...
```

### Testing the Fix Locally

1. **Set production environment**:
   ```bash
   export DJANGO_ENVIRONMENT=production
   export DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
   ```

2. **Start Celery worker**:
   ```bash
   celery -A azure_advisor_reports worker --loglevel=info
   ```

3. **Check worker logs** for:
   ```
   Worker initialized with settings module: azure_advisor_reports.settings.production
   Database engine: django.db.backends.postgresql
   Database name: your_database_name
   Database connection successful
   ```

4. **Trigger a task** and verify it can access the database:
   ```python
   from apps.reports.tasks import process_csv_file
   result = process_csv_file.delay(report_id)
   ```

### Production Deployment

1. **Update Azure Container App environment variables**:
   - Add: `DJANGO_ENVIRONMENT=production`
   - Verify: `DATABASE_URL` or individual DB variables are set

2. **Deploy updated code** with the fixes

3. **Monitor Celery worker logs** after deployment:
   ```bash
   az containerapp logs show --name backend-container-app --resource-group your-rg --follow
   ```

4. **Look for initialization messages**:
   - "Worker initialized with settings module: azure_advisor_reports.settings.production"
   - "Database engine: django.db.backends.postgresql"
   - "Database connection successful"

5. **Test task execution** by uploading a CSV file or triggering report generation

## Best Practices for Django Settings in Celery

### ✅ DO

1. **Use environment-specific settings files**:
   - `settings/base.py` - Common settings
   - `settings/development.py` - Local development
   - `settings/production.py` - Production
   - `settings/testing.py` - Tests only

2. **Set DJANGO_SETTINGS_MODULE consistently**:
   ```python
   # celery.py
   environment = os.environ.get('DJANGO_ENVIRONMENT', 'development')
   settings_module = f'azure_advisor_reports.settings.{environment}'
   os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
   ```

3. **Use direct environment variable access in production**:
   ```python
   # production.py
   DB_NAME = os.environ.get('DB_NAME', '')
   ```

4. **Validate critical configuration**:
   ```python
   if not DATABASES['default'].get('NAME'):
       raise ValueError("Database not configured!")
   ```

5. **Add worker initialization diagnostics**:
   ```python
   @worker_process_init.connect
   def configure_workers(sender=None, conf=None, **kwargs):
       # Log configuration, test connections
   ```

### ❌ DON'T

1. **NEVER use `'pytest' in sys.modules`** for production logic
   - It's non-deterministic
   - pytest can be imported by any dependency
   - Causes random failures in worker processes

2. **Don't hardcode settings modules**:
   ```python
   # BAD
   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.development')
   ```

3. **Don't mix test and production logic**:
   ```python
   # BAD - test logic in production settings
   if 'test' in sys.argv or 'pytest' in sys.modules:
       DATABASES = {...}
   ```

4. **Don't rely solely on python-decouple in production**:
   - Use `os.environ.get()` as primary source
   - Use `config()` only as fallback for local development

5. **Don't assume settings are immutable**:
   - Worker processes can reload modules
   - Settings may be re-evaluated during task execution

## Django Settings Lifecycle in Celery

### Understanding the Problem

```
┌─────────────────────────────────────────────────────────────┐
│ CELERY WORKER LIFECYCLE                                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Parent Process Starts                                   │
│     ├── Load celery.py                                      │
│     ├── Set DJANGO_SETTINGS_MODULE                          │
│     ├── Import Django settings (settings.py loads)          │
│     └── DATABASES configured (PostgreSQL) ✓                 │
│                                                              │
│  2. Worker Process Spawns                                   │
│     ├── Fork/spawn child process                            │
│     ├── Inherit environment variables ✓                     │
│     └── Inherit sys.modules (partially) ⚠️                  │
│                                                              │
│  3. Task Execution Begins                                   │
│     ├── Import task module                                  │
│     ├── Import dependencies (may import pytest!) ⚠️         │
│     └── sys.modules['pytest'] = <module pytest> 💥          │
│                                                              │
│  4. Database Query Executed                                 │
│     ├── Django ORM accesses settings.DATABASES              │
│     ├── Settings re-evaluated (conditional check runs)      │
│     ├── 'pytest' in sys.modules == TRUE 💥                  │
│     ├── DATABASES = SQLite in-memory 💥                     │
│     └── PostgreSQL config LOST 💥                           │
│                                                              │
│  5. Query Fails                                             │
│     └── ImproperlyConfigured: ENGINE value missing 💥       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Why Web Process (Gunicorn) Works

```
┌─────────────────────────────────────────────────────────────┐
│ GUNICORN WORKER LIFECYCLE                                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Worker Process Starts                                   │
│     ├── Load wsgi.py                                        │
│     ├── Set DJANGO_SETTINGS_MODULE                          │
│     ├── Import Django settings (settings.py loads ONCE)     │
│     └── DATABASES configured (PostgreSQL) ✓                 │
│                                                              │
│  2. Request Handling                                        │
│     ├── Settings already loaded (cached)                    │
│     ├── No re-evaluation of conditional logic               │
│     └── DATABASES remains PostgreSQL ✓                      │
│                                                              │
│  3. Occasional Module Import                                │
│     ├── pytest might get imported                           │
│     ├── But settings NOT re-evaluated                       │
│     └── DATABASES still PostgreSQL ✓                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Summary

The fix addresses three critical issues:

1. **Removed non-deterministic pytest check** that randomly triggered in worker processes
2. **Fixed Celery settings module loading** to respect environment configuration
3. **Hardened production database config** with validation and explicit environment variable access

This ensures Celery workers consistently use PostgreSQL in production, regardless of which modules get imported during task execution.

## Files Modified

- `azure_advisor_reports/celery.py` - Environment-aware settings loading + diagnostics
- `azure_advisor_reports/settings.py` - Removed pytest module check
- `azure_advisor_reports/settings/production.py` - Hardened database config, removed pytest check
- `azure_advisor_reports/settings/testing.py` - NEW: Dedicated test settings

## References

- Django Settings: https://docs.djangoproject.com/en/4.2/topics/settings/
- Celery Django Integration: https://docs.celeryq.dev/en/stable/django/
- Django Database Configuration: https://docs.djangoproject.com/en/4.2/ref/settings/#databases
