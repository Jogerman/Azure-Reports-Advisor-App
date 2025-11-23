# Database Optimization Guide
## Azure Advisor Reports Platform

**Version**: 2.0
**Last Updated**: 2025-01-11

---

## Table of Contents

1. [Connection Pooling Configuration](#connection-pooling-configuration)
2. [Recommended Indexes](#recommended-indexes)
3. [Query Caching Strategy](#query-caching-strategy)
4. [N+1 Query Prevention](#n1-query-prevention)
5. [Performance Monitoring](#performance-monitoring)
6. [Maintenance Tasks](#maintenance-tasks)

---

## Connection Pooling Configuration

### Install pg_bouncer or use Django DB Connection Pooling

#### Option 1: Django Persistent Connections (Recommended for small-medium scale)

Add to `settings.py`:

```python
# Database Configuration with Connection Pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),

        # Connection Pooling Settings
        'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
        'CONN_HEALTH_CHECKS': True,  # Django 4.1+ health check feature

        # Connection Options
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30 second statement timeout
        },

        # Pool Configuration (if using django-db-connection-pool)
        'POOL_OPTIONS': {
            'POOL_SIZE': 10,  # Number of connections to pool
            'MAX_OVERFLOW': 5,  # Additional connections when pool is full
            'RECYCLE': 3600,  # Recycle connections after 1 hour
            'PRE_PING': True,  # Test connections before using
        }
    }
}
```

#### Option 2: PgBouncer (Recommended for high-scale)

1. **Install PgBouncer**:
```bash
sudo apt-get install pgbouncer
```

2. **Configure `/etc/pgbouncer/pgbouncer.ini`**:
```ini
[databases]
azure_advisor_db = host=localhost port=5432 dbname=azure_advisor_db

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 5
max_db_connections = 50
```

3. **Update Django settings**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'azure_advisor_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': '127.0.0.1',
        'PORT': '6432',  # PgBouncer port
    }
}
```

---

## Recommended Indexes

### Apply with Migration or SQL

#### Create Migration:

```bash
python manage.py makemigrations --empty monitoring --name add_performance_indexes
```

#### Edit Migration File:

```python
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
        ('clients', '0001_initial'),
    ]

    operations = [
        # Reports indexes
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_client_status
                    ON reports_report (client_id, status);

                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_created_status
                    ON reports_report (created_at DESC, status);

                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_type_status
                    ON reports_report (report_type, status);

                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_created_by
                    ON reports_report (created_by_id, created_at DESC);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_reports_client_status;
                DROP INDEX IF EXISTS idx_reports_created_status;
                DROP INDEX IF EXISTS idx_reports_type_status;
                DROP INDEX IF EXISTS idx_reports_created_by;
            """
        ),

        # Clients indexes
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clients_status
                    ON clients_client (status, created_at DESC);

                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clients_company_name
                    ON clients_client (company_name);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_clients_status;
                DROP INDEX IF EXISTS idx_clients_company_name;
            """
        ),

        # Audit logs indexes
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_user_timestamp
                    ON audit_logs (user_id, timestamp DESC);

                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_resource
                    ON audit_logs (resource_type, resource_id);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_audit_user_timestamp;
                DROP INDEX IF EXISTS idx_audit_resource;
            """
        ),
    ]
```

#### Or Apply Directly:

```bash
python manage.py analyze_database --apply-indexes
```

---

## Query Caching Strategy

### 1. Django Cache Configuration

Add to `settings.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'azure_advisor',
        'TIMEOUT': 300,  # 5 minutes default
    },

    # Separate cache for query results
    'queries': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/2'),
        'TIMEOUT': 600,  # 10 minutes for queries
    },

    # Separate cache for sessions
    'sessions': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/3'),
        'TIMEOUT': 3600,  # 1 hour for sessions
    },
}

# Use Redis for sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
```

### 2. Using Query Cache

```python
from apps.monitoring.database_optimization import QueryCache

# Cache expensive queries
@QueryCache.cached_query('reports_for_client_{client_id}', timeout=600)
def get_client_reports(client_id):
    return Report.objects.filter(
        client_id=client_id
    ).select_related('client', 'created_by').all()

# Invalidate cache when data changes
def update_report(report_id, data):
    report = Report.objects.get(id=report_id)
    report.status = data['status']
    report.save()

    # Invalidate cached queries
    QueryCache.invalidate(f'reports_for_client_{report.client_id}')
    QueryCache.invalidate_pattern('dashboard_analytics_*')
```

### 3. View-Level Caching

```python
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

# Cache view for 5 minutes
@cache_page(60 * 5)
def dashboard_view(request):
    return render(request, 'dashboard.html', context)

# For class-based views
class DashboardView(View):
    @method_decorator(cache_page(60 * 5))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
```

### 4. Template Fragment Caching

```django
{% load cache %}

{% cache 600 sidebar request.user.id %}
    <!-- Expensive sidebar rendering -->
    {% for item in expensive_query %}
        ...
    {% endfor %}
{% endcache %}
```

---

## N+1 Query Prevention

### Common Patterns and Solutions

#### 1. Foreign Key Access

❌ **Bad** (N+1 queries):
```python
reports = Report.objects.all()
for report in reports:
    print(report.client.name)  # Hits DB for each report!
    print(report.created_by.username)  # Another hit!
```

✅ **Good** (2 queries total):
```python
reports = Report.objects.select_related('client', 'created_by').all()
for report in reports:
    print(report.client.name)  # No DB hit
    print(report.created_by.username)  # No DB hit
```

#### 2. Reverse Foreign Key

❌ **Bad**:
```python
clients = Client.objects.all()
for client in clients:
    report_count = client.reports.count()  # N+1!
```

✅ **Good**:
```python
from django.db.models import Count

clients = Client.objects.annotate(
    report_count=Count('reports')
).all()
for client in clients:
    print(client.report_count)  # No additional query
```

#### 3. Many-to-Many Relationships

❌ **Bad**:
```python
reports = Report.objects.all()
for report in reports:
    categories = report.categories.all()  # N+1!
```

✅ **Good**:
```python
reports = Report.objects.prefetch_related('categories').all()
for report in reports:
    categories = report.categories.all()  # Prefetched
```

#### 4. Complex Prefetching

```python
from django.db.models import Prefetch

# Prefetch with filtering
completed_reports = Report.objects.filter(status='completed')

clients = Client.objects.prefetch_related(
    Prefetch(
        'reports',
        queryset=completed_reports,
        to_attr='completed_reports'
    )
).all()

for client in clients:
    for report in client.completed_reports:
        print(report.title)
```

### Detection Tool

Use the decorator to detect N+1 queries:

```python
from apps.monitoring.database_optimization import track_query_performance

@track_query_performance
def my_view_function():
    # Will log warning if > 50 queries or > 1s
    reports = Report.objects.all()
    for report in reports:
        print(report.client.name)
```

---

## Performance Monitoring

### 1. Enable Query Logging in Development

Add to `settings.py`:

```python
if DEBUG:
    LOGGING['loggers']['django.db.backends'] = {
        'level': 'DEBUG',
        'handlers': ['console'],
    }
```

### 2. Django Debug Toolbar

Install and configure:

```bash
pip install django-debug-toolbar
```

```python
# settings.py
INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

INTERNAL_IPS = ['127.0.0.1']
```

### 3. Analyze Database Performance

```bash
# Run comprehensive analysis
python manage.py analyze_database

# Show optimization tips
python manage.py analyze_database --show-tips

# Apply recommended indexes
python manage.py analyze_database --apply-indexes

# Export as JSON
python manage.py analyze_database --format json > db_analysis.json
```

### 4. Monitor Slow Queries

Add to your views:

```python
from apps.monitoring.database_optimization import QueryAnalyzer

def admin_dashboard(request):
    if request.user.is_staff:
        slow_queries = QueryAnalyzer.get_slow_queries(threshold_ms=100)
        context = {'slow_queries': slow_queries}
        return render(request, 'admin/performance.html', context)
```

---

## Maintenance Tasks

### 1. Regular VACUUM

```sql
-- Manual VACUUM
VACUUM ANALYZE;

-- VACUUM specific table
VACUUM ANALYZE reports_report;

-- Full VACUUM (requires exclusive lock)
VACUUM FULL;
```

### 2. Update Statistics

```sql
ANALYZE;

-- Or for specific table
ANALYZE reports_report;
```

### 3. Reindex

```sql
-- Rebuild all indexes
REINDEX DATABASE azure_advisor_db;

-- Rebuild table indexes
REINDEX TABLE reports_report;
```

### 4. Check for Bloat

```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS external_size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 5. Scheduled Maintenance (Celery Beat)

```python
# celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'analyze-database-weekly': {
        'task': 'apps.monitoring.tasks.analyze_database_performance',
        'schedule': crontab(day_of_week='sunday', hour=2, minute=0),
    },
    'cleanup-old-audit-logs': {
        'task': 'apps.audit.tasks.cleanup_old_logs',
        'schedule': crontab(day_of_week='sunday', hour=3, minute=0),
    },
}
```

---

## Performance Benchmarks

### Target Metrics

- **API Response Time**: < 200ms (p95)
- **Database Query Time**: < 50ms (average)
- **Max Queries per Request**: < 20
- **Cache Hit Rate**: > 80%
- **Connection Pool Utilization**: 50-70%

### Monitoring Queries

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- Long-running queries
SELECT
    pid,
    now() - query_start as duration,
    query
FROM pg_stat_activity
WHERE state = 'active'
AND query_start < now() - interval '1 minute'
ORDER BY duration DESC;

-- Index hit rate (should be > 99%)
SELECT
    sum(idx_blks_hit) / nullif(sum(idx_blks_hit + idx_blks_read), 0) * 100 as index_hit_rate
FROM pg_statio_user_indexes;

-- Cache hit rate (should be > 99%)
SELECT
    sum(heap_blks_hit) / nullif(sum(heap_blks_hit + heap_blks_read), 0) * 100 as cache_hit_rate
FROM pg_statio_user_tables;
```

---

## Troubleshooting

### Issue: High CPU Usage

**Symptoms**: Database CPU at 100%

**Solutions**:
1. Identify slow queries: `SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;`
2. Add missing indexes
3. Optimize query logic
4. Consider query result caching

### Issue: High Memory Usage

**Symptoms**: OOM errors, slow queries

**Solutions**:
1. Reduce `shared_buffers` if too high
2. Limit connection pool size
3. Use `LIMIT` in queries
4. Implement pagination

### Issue: Connection Pool Exhausted

**Symptoms**: "Too many connections" errors

**Solutions**:
1. Increase `max_connections` in PostgreSQL
2. Implement connection pooling (PgBouncer)
3. Fix connection leaks in code
4. Reduce `CONN_MAX_AGE` if too high

---

## Resources

- [Django Database Optimization](https://docs.djangoproject.com/en/4.2/topics/db/optimization/)
- [PostgreSQL Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/)
- [PgBouncer Documentation](https://www.pgbouncer.org/usage.html)

---

**Last Updated**: 2025-01-11
**Maintained By**: Development Team
