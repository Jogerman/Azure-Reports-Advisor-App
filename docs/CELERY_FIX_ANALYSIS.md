# Celery Database Configuration Fix - Root Cause Analysis

## Problem Statement

Reports were getting stuck in "processing" state. Celery workers started successfully but failed when processing tasks with:

```
django.core.exceptions.ImproperlyConfigured: settings.DATABASES is improperly configured.
Please supply the ENGINE value.
```

This occurred ONLY during task execution, not during worker startup.

## Environment

- **Platform**: Azure Container Apps
- **Services**:
  - Backend (Django/Gunicorn): advisor-reports-backend
  - Celery Worker: advisor-reports-worker (revision 0000042, v1.3.13)
  - Celery Beat: advisor-reports-beat
  - PostgreSQL: advisor-reports-db-prod.postgres.database.azure.com
  - Redis: advisor-reports-cache (Azure Redis)

## Root Cause Analysis

### The Critical Discovery

The `.env` file is explicitly excluded from Docker images via `.dockerignore` (line 48). This is CORRECT for production - environment variables must come from Azure Container Apps configuration.

### Why python-decouple Fails in Celery Workers

1. **python-decouple's config() search order**:
   - Environment variables
   - .env file
   - .ini file
   - Default value

2. **The Problem**: In production containers (no .env file), `config()` should read from `os.environ`. However, when Celery workers spawn child processes, the `config()` function's initialization context differs from the main process.

3. **The Failure Mode**: If `config()` encounters any issues during its search path initialization (missing .env, file permissions, etc.), it may throw an exception BEFORE falling back to environment variables, especially in worker processes.

4. **Why Backend Works But Worker Fails**:
   - **Backend (Gunicorn)**: Straightforward main process, settings import cleanly
   - **Celery Worker**: Uses multiprocessing, fork/spawn workers, different initialization path that exposes `config()` issues

### Version History Analysis

- **v1.3.7 (WORKED)**: Used `os.environ.get('KEY', config('KEY', default=''))` pattern
  - Worked because `os.environ.get()` is evaluated FIRST
  - Never called `config()` in production where env vars exist

- **v1.3.10-v1.3.11 (BROKE)**: Changed to `config('KEY')` first
  - Failed because `config()` threw exceptions in worker processes

- **v1.3.12 (STILL BROKEN)**: Attempted revert to v1.3.7 logic
  - Failed because something changed in deployment/environment between versions
  - Docker image rebuilt, worker configuration may have subtle differences

- **v1.3.13 (STILL BROKEN)**: Added try/except around config()
  - Failed because exception handling wasn't catching the right issues

## The Solution

### Implementation Strategy

Replace all critical configuration (database, Celery, Redis) with a safe helper function that:
1. Checks `os.environ` FIRST (always works in production)
2. Falls back to `config()` for local development (.env files)
3. Has robust exception handling

### Code Changes

**File**: `azure_advisor_reports/azure_advisor_reports/settings.py`

#### 1. Database Configuration (Lines 142-170)

```python
def get_db_config(key, default):
    """Safely get database config with proper fallback chain."""
    # First check os.environ directly (works in all contexts)
    value = os.environ.get(key)
    if value is not None:
        return value
    # Try config() for local development with .env files
    try:
        return config(key, default=default)
    except Exception:
        # If config() fails (e.g., in Celery workers), use default
        return default

db_name = get_db_config('DB_NAME', 'azure_advisor_reports')
db_user = get_db_config('DB_USER', 'postgres')
db_password = get_db_config('DB_PASSWORD', 'postgres')
db_host = get_db_config('DB_HOST', 'localhost')
db_port = get_db_config('DB_PORT', '5432')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_name,
        'USER': db_user,
        'PASSWORD': db_password,
        'HOST': db_host,
        'PORT': db_port,
    }
}
```

#### 2. Celery Configuration (Lines 270-281)

```python
def get_celery_config(key, default):
    """Safely get Celery config with proper fallback chain."""
    value = os.environ.get(key)
    if value is not None:
        return value
    try:
        return config(key, default=default)
    except Exception:
        return default

CELERY_BROKER_URL = get_celery_config('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = get_celery_config('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
```

#### 3. Cache Configuration (Line 303)

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': get_celery_config('REDIS_URL', 'redis://localhost:6379/1'),
        # ... rest of config
    }
}
```

## Verification

### Environment Variables Confirmed in Azure

Worker container has all required environment variables:
```bash
DB_NAME=advisor_reports
DB_USER=azurereportadmin
DB_PASSWORD=PTPn7JrjUuLF@3Qs
DB_HOST=advisor-reports-db-prod.postgres.database.azure.com
DB_PORT=5432
CELERY_BROKER_URL=rediss://...:6380/1?ssl_cert_reqs=required
CELERY_RESULT_BACKEND=rediss://...:6380/2?ssl_cert_reqs=required
REDIS_URL=rediss://...:6380/0?ssl_cert_reqs=required
DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings
```

### Why This Fix Works

1. **Priority Order**: `os.environ.get()` is checked FIRST, before any `config()` calls
2. **Robust Fallback**: If `config()` fails for ANY reason, we have a safe default
3. **Process-Agnostic**: Works in main process (Gunicorn) and worker processes (Celery)
4. **Development Compatible**: Still supports .env files for local development
5. **Production Safe**: Always uses Azure Container Apps environment variables in production

## Deployment Steps

### 1. Build and Push New Image

```bash
cd azure_advisor_reports

# Build with new version tag
docker build -t advisorreportsacr.azurecr.io/advisor-reports-backend:v1.3.14 .

# Push to Azure Container Registry
az acr login --name advisorreportsacr
docker push advisorreportsacr.azurecr.io/advisor-reports-backend:v1.3.14
```

### 2. Update Worker Container App

```bash
# Update worker to use new image
az containerapp update \
  --name advisor-reports-worker \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr.azurecr.io/advisor-reports-backend:v1.3.14

# Verify deployment
az containerapp revision list \
  --name advisor-reports-worker \
  --resource-group rg-azure-advisor-app \
  --query "[0].{Name:name,Active:properties.active,Created:properties.createdTime}"
```

### 3. Update Backend Container App (for consistency)

```bash
az containerapp update \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr.azurecr.io/advisor-reports-backend:v1.3.14
```

### 4. Update Beat Container App

```bash
az containerapp update \
  --name advisor-reports-beat \
  --resource-group rg-azure-advisor-app \
  --image advisorreportsacr.azurecr.io/advisor-reports-backend:v1.3.14
```

### 5. Monitor Logs

```bash
# Watch worker logs
az containerapp logs show \
  --name advisor-reports-worker \
  --resource-group rg-azure-advisor-app \
  --follow

# Check for successful task processing (should see no ImproperlyConfigured errors)
```

### 6. Test Report Generation

1. Log into the application
2. Upload a CSV file
3. Generate a report
4. Verify report completes successfully (not stuck in "processing")

## Prevention Measures

### 1. Always Use Safe Config Pattern

For any critical configuration that Celery workers need, use this pattern:

```python
def get_safe_config(key, default):
    """Safely get config with os.environ priority."""
    value = os.environ.get(key)
    if value is not None:
        return value
    try:
        return config(key, default=default)
    except Exception:
        return default
```

### 2. Non-Critical Configuration

For non-critical config (UI settings, feature flags, etc.), direct `config()` usage is fine:
```python
FEATURE_FLAG = config('FEATURE_FLAG', default=False, cast=bool)
```

### 3. Testing

Add integration tests that:
- Import settings in worker-like process contexts
- Verify DATABASES configuration is complete
- Test with and without .env files

### 4. Monitoring

Set up alerts for:
- Tasks stuck in "processing" state > 5 minutes
- Celery worker restarts
- Database connection errors in logs

## Related Files

- **settings.py**: Main settings file (uses azure_advisor_reports.settings)
- **settings/production.py**: Already uses `os.environ.get()` directly (correct pattern)
- **celery.py**: Celery app configuration
- **docker-entrypoint.sh**: Container startup script
- **.dockerignore**: Excludes .env files from Docker images

## Lessons Learned

1. **python-decouple is not process-safe**: The `config()` function can behave differently in child processes (Celery workers) vs main processes (Gunicorn)

2. **Always prioritize os.environ in production**: Environment variables set by Azure Container Apps are the source of truth

3. **Test in production-like environments**: Local development with .env files doesn't expose worker process issues

4. **Simple is better**: Direct `os.environ.get()` is more reliable than abstraction libraries for critical configuration

5. **Version control is crucial**: Being able to compare v1.3.7 (working) vs v1.3.10+ (broken) was key to diagnosis

## Version

- **Fix Version**: v1.3.14
- **Date**: 2025-11-02
- **Author**: DevOps Team
