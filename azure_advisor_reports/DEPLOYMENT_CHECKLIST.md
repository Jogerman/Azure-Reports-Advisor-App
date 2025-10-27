# Azure Container Apps Deployment Checklist

## Pre-Deployment Verification

### 1. Environment Variables Configuration

Ensure these environment variables are set in Azure Container App:

#### Required Database Configuration
```bash
# Option A: Use DATABASE_URL (Recommended for Azure)
DATABASE_URL=postgresql://username:password@host.postgres.database.azure.com:5432/dbname?sslmode=require

# Option B: Use individual variables (Fallback)
DB_NAME=advisor_reports
DB_USER=azurereportadmin
DB_PASSWORD=your_password
DB_HOST=advisor-reports-db-prod.postgres.database.azure.com
DB_PORT=5432
```

#### Required Django Configuration
```bash
SECRET_KEY=<generate-strong-secret-key>
DEBUG=False
ALLOWED_HOSTS=your-app.azurecontainerapps.io,your-custom-domain.com
DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production  # Optional (now default)
```

#### Required Azure Services
```bash
# Redis (for cache and Celery)
REDIS_URL=rediss://your-redis.redis.cache.windows.net:6380?ssl_cert_reqs=CERT_NONE

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account
AZURE_STORAGE_ACCOUNT_KEY=your_storage_key
AZURE_STORAGE_CONTAINER=static

# Azure AD
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
AZURE_REDIRECT_URI=https://your-app.azurecontainerapps.io

# CORS
CORS_ALLOWED_ORIGINS=https://your-frontend.com,https://www.your-frontend.com
CSRF_TRUSTED_ORIGINS=https://your-app.azurecontainerapps.io
```

#### Optional Monitoring
```bash
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;IngestionEndpoint=xxx
```

## Setting Environment Variables in Azure

### Using Azure Portal

1. Navigate to your Container App
2. Go to "Settings" > "Environment variables"
3. Click "Add" for each variable
4. Mark sensitive values (passwords, keys) as "Secret"
5. Click "Save"

### Using Azure CLI

```bash
# Set DATABASE_URL
az containerapp update \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --set-env-vars \
    "DATABASE_URL=secretref:database-url" \
  --secrets \
    "database-url=postgresql://user:pass@host:5432/db?sslmode=require"

# Set other required variables
az containerapp update \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --set-env-vars \
    "SECRET_KEY=secretref:secret-key" \
    "DEBUG=False" \
    "ALLOWED_HOSTS=your-app.azurecontainerapps.io" \
    "REDIS_URL=secretref:redis-url" \
  --secrets \
    "secret-key=your-secret-key-here" \
    "redis-url=rediss://your-redis-instance"
```

## Deployment Steps

### 1. Build and Push Docker Image

```bash
# Build the image
docker build -t azure-advisor-reports:latest .

# Tag for Azure Container Registry
docker tag azure-advisor-reports:latest yourregistry.azurecr.io/azure-advisor-reports:latest

# Push to ACR
docker push yourregistry.azurecr.io/azure-advisor-reports:latest
```

### 2. Update Container App

```bash
# Update the container image
az containerapp update \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --image yourregistry.azurecr.io/azure-advisor-reports:latest
```

### 3. Run Database Migrations

```bash
# Execute migrations in the container
az containerapp exec \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --command "python manage.py migrate"
```

### 4. Create Superuser (First Time Only)

```bash
# Create Django superuser
az containerapp exec \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --command "python manage.py createsuperuser --noinput --username admin --email admin@example.com"
```

### 5. Collect Static Files

```bash
# Collect static files to Azure Blob Storage
az containerapp exec \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --command "python manage.py collectstatic --noinput"
```

## Post-Deployment Verification

### 1. Check Application Logs

```bash
# View real-time logs
az containerapp logs show \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --follow

# Look for:
# - Successful database connection
# - No "dummy backend" errors
# - Successful WSGI startup
```

### 2. Verify Database Connection

```bash
# Test database connectivity
az containerapp exec \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --command "python manage.py dbshell --command 'SELECT version();'"
```

### 3. Run Django System Check

```bash
# Run Django's production deployment check
az containerapp exec \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --command "python manage.py check --deploy"
```

Expected output: "System check identified no issues"

### 4. Test Health Endpoint

```bash
# Test the application is responding
curl https://your-app.azurecontainerapps.io/health/
```

### 5. Verify Settings Loading

Check logs for these indicators:

```
✓ GOOD: "Connected to PostgreSQL database: advisor_reports"
✓ GOOD: "Using production settings: azure_advisor_reports.settings.production"
✓ GOOD: "Database engine: django.db.backends.postgresql"

✗ BAD: "Using database backend: django.db.backends.dummy"
✗ BAD: "No database configured"
✗ BAD: "Connection to database failed"
```

## Troubleshooting

### Issue: Still Getting Dummy Backend

**Check:**
1. Is `DATABASE_URL` set in Container App environment variables?
2. Is the URL format correct (postgresql://...)?
3. Check logs for environment variable loading

**Fix:**
```bash
# Verify environment variable
az containerapp show \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --query "properties.template.containers[0].env" -o table

# If not set, add it
az containerapp update \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --set-env-vars "DATABASE_URL=secretref:database-url" \
  --secrets "database-url=postgresql://..."
```

### Issue: Database Connection Refused

**Check:**
1. PostgreSQL server firewall rules (allow Azure services)
2. Connection string format (especially URL-encoded password)
3. SSL mode is set to "require"

**Fix:**
```bash
# Update PostgreSQL firewall
az postgres flexible-server firewall-rule create \
  --resource-group your-rg \
  --name advisor-reports-db-prod \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### Issue: Settings Module Not Found

**Check:**
1. DJANGO_SETTINGS_MODULE is set correctly
2. wsgi.py has the correct default

**Fix:**
The wsgi.py now defaults to production settings, but you can override:
```bash
az containerapp update \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --set-env-vars "DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production"
```

### Issue: Import Errors

**Check:**
1. All dependencies are installed in Docker image
2. requirements.txt includes dj-database-url, psycopg2-binary

**Fix:**
Ensure requirements.txt has:
```
dj-database-url>=2.0.0
psycopg2-binary>=2.9.9
python-decouple>=3.8
```

## Monitoring

### Set Up Alerts

1. Database connection failures
2. High error rates (500 errors)
3. High response times
4. Container restarts

### Application Insights

If using Application Insights, monitor:
- Request duration
- Failed requests
- Database query performance
- Exceptions

### Log Queries

```bash
# Check for database errors
az containerapp logs show \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --query "[?contains(message, 'database')]"

# Check for errors
az containerapp logs show \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --query "[?contains(level, 'ERROR')]"
```

## Rollback Plan

If deployment fails:

```bash
# Revert to previous revision
az containerapp revision list \
  --name azure-advisor-reports \
  --resource-group your-rg -o table

# Activate previous revision
az containerapp revision activate \
  --name azure-advisor-reports \
  --resource-group your-rg \
  --revision <previous-revision-name>
```

## Security Checklist

- [ ] DEBUG is set to False
- [ ] SECRET_KEY is strong and unique
- [ ] ALLOWED_HOSTS is properly configured
- [ ] Database uses SSL (sslmode=require)
- [ ] Sensitive env vars are marked as secrets
- [ ] CORS origins are restricted
- [ ] CSRF trusted origins are configured
- [ ] PostgreSQL firewall is configured
- [ ] Container registry credentials are secure
- [ ] No sensitive data in logs

## Performance Optimization

After deployment, consider:

1. Enable connection pooling (CONN_MAX_AGE=600)
2. Configure Redis cache
3. Enable static file compression (WhiteNoise)
4. Set up CDN for static files
5. Configure database query optimization
6. Enable Application Insights for monitoring

## Regular Maintenance

### Weekly
- Review application logs for errors
- Check database performance metrics
- Monitor disk and memory usage

### Monthly
- Review and rotate secrets
- Update dependencies (security patches)
- Review and optimize database queries
- Clean up old container revisions

### Quarterly
- Review and update firewall rules
- Audit user access and permissions
- Review monitoring and alert configurations
- Load testing and performance optimization
