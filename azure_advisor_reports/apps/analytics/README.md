# Analytics Module - Azure Advisor Reports Platform

Complete analytics tracking and reporting system for the Azure Advisor Reports Platform.

## Features

- User activity tracking and monitoring
- System health metrics
- Report generation analytics
- Automated metric calculations via Celery
- Performance statistics
- RESTful API endpoints

## Installation & Configuration

### 1. Install Dependencies

Ensure these packages are in your `requirements.txt`:

```txt
psutil>=5.9.0  # For system metrics
celery>=5.3.0  # For background tasks
redis>=4.5.0   # For Celery broker
```

Install:
```bash
pip install -r requirements.txt
```

### 2. Add Middleware

Add the activity tracking middleware to your `settings.py`:

```python
MIDDLEWARE = [
    # ... other middleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Add analytics middleware (place near the end)
    'apps.analytics.middleware.UserActivityTrackingMiddleware',
]
```

### 3. Configure Celery

**Option A: Update existing Celery configuration**

In your `azure_advisor_reports/celery.py`:

```python
from celery import Celery
from apps.analytics.celery_config import ANALYTICS_CELERY_BEAT_SCHEDULE

app = Celery('azure_advisor_reports')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Update beat schedule
app.conf.beat_schedule = ANALYTICS_CELERY_BEAT_SCHEDULE

app.autodiscover_tasks()
```

**Option B: Merge in settings.py**

In your `settings.py`:

```python
from apps.analytics.celery_config import ANALYTICS_CELERY_BEAT_SCHEDULE

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Merge analytics beat schedule
CELERY_BEAT_SCHEDULE = {
    **ANALYTICS_CELERY_BEAT_SCHEDULE,
    # Add other scheduled tasks here
}
```

### 4. Run Migrations

```bash
python manage.py migrate analytics
```

### 5. Start Celery Workers

**Terminal 1 - Celery Worker:**
```bash
celery -A azure_advisor_reports worker --loglevel=info
```

**Terminal 2 - Celery Beat (Scheduler):**
```bash
celery -A azure_advisor_reports beat --loglevel=info
```

**Combined (Development):**
```bash
celery -A azure_advisor_reports worker --beat --loglevel=info
```

## API Endpoints

### New Endpoints

1. **User Activity** - `GET /api/v1/analytics/user-activity/`
   - Get detailed user activity with filtering and pagination
   - Supports filters: user_id, date_from, date_to, activity_type

2. **Activity Summary** - `GET /api/v1/analytics/activity-summary/`
   - Get aggregated activity summary
   - Supports grouping by: activity_type, user, day

3. **System Health** - `GET /api/v1/analytics/system-health/`
   - Get comprehensive system health metrics
   - Admin/Manager only

### Existing Endpoints

- `GET /api/v1/analytics/dashboard/` - Complete dashboard analytics
- `GET /api/v1/analytics/metrics/` - Dashboard metrics only
- `GET /api/v1/analytics/trends/` - Trend data over time
- `GET /api/v1/analytics/categories/` - Category distribution
- `GET /api/v1/analytics/recent-activity/` - Recent activity
- `GET /api/v1/analytics/client-performance/` - Client performance metrics
- `GET /api/v1/analytics/business-impact/` - Business impact distribution
- `POST /api/v1/analytics/cache/invalidate/` - Invalidate caches (admin only)

See [ANALYTICS_API_DOCUMENTATION.md](./ANALYTICS_API_DOCUMENTATION.md) for complete API documentation.

## Celery Tasks

### Scheduled Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `calculate_daily_metrics` | Daily at 2:00 AM | Calculate and cache all analytics metrics |
| `cleanup_old_activities` | Weekly (Sunday 3:00 AM) | Delete user activities older than 90 days |
| `calculate_dashboard_metrics_periodic` | Daily at 1:00 AM | Calculate dashboard metrics for different periods |
| `cleanup_old_system_metrics` | Weekly (Sunday 4:00 AM) | Delete system metrics older than 30 days |
| `update_report_usage_stats` | Hourly (:05) | Update hourly usage statistics |
| `generate_weekly_report` | Weekly (Monday 9:00 AM) | Generate weekly analytics report |

### Manual Task Execution

Run tasks manually for testing:

```python
from apps.analytics.tasks import calculate_daily_metrics

# Run synchronously
result = calculate_daily_metrics()

# Run asynchronously via Celery
task = calculate_daily_metrics.delay()
print(task.state)  # Check task status
```

## Activity Tracking

### Tracked Activities

The middleware automatically tracks:

- **Report Operations:**
  - `generate_report` - Report creation
  - `download_report` - Report downloads
  - `delete_report` - Report deletion
  - `share_report` - Report sharing

- **Client Operations:**
  - `create_client` - Client creation
  - `update_client` - Client updates
  - `delete_client` - Client deletion

- **Data Operations:**
  - `upload_csv` - CSV uploads

- **User Operations:**
  - `login` - User login
  - `logout` - User logout
  - `view_dashboard` - Dashboard views

### Manual Activity Logging

You can also manually log activities:

```python
from apps.analytics.services import AnalyticsService

AnalyticsService.log_activity(
    action='custom_action',
    description='User performed custom action',
    user=request.user,
    client=client_instance,  # Optional
    report=report_instance,  # Optional
    ip_address='192.168.1.1',
    user_agent=request.META.get('HTTP_USER_AGENT'),
    metadata={'custom_field': 'value'}
)
```

## Models

### UserActivity

Tracks individual user actions.

**Fields:**
- `user` - ForeignKey to User
- `action` - Type of action (CharField with choices)
- `description` - Human-readable description
- `client` - Related client (optional)
- `report` - Related report (optional)
- `ip_address` - User's IP address
- `user_agent` - Browser/client user agent
- `metadata` - Additional JSON data
- `created_at` - Timestamp

### DashboardMetrics

Pre-calculated dashboard metrics for performance.

**Fields:**
- `date` - Date for metrics
- `period_type` - daily, weekly, monthly, yearly
- `total_clients` - Total client count
- `active_clients` - Active client count
- `total_reports` - Total report count
- `category_distribution` - JSON breakdown
- `impact_distribution` - JSON breakdown
- `avg_processing_time_seconds` - Processing time
- `success_rate_percentage` - Success rate

### ReportUsageStats

Hourly usage statistics for detailed tracking.

### SystemHealthMetrics

System health snapshots for monitoring.

## Performance Optimization

### Caching

Analytics data is heavily cached:

- **Dashboard Metrics:** 15 minutes TTL
- **System Health:** 5 minutes TTL
- **Trend Data:** 15 minutes TTL
- **Category Distribution:** 15 minutes TTL

**Clear cache manually:**
```python
from apps.analytics.services import AnalyticsService

AnalyticsService.invalidate_cache()
```

**Or via API:**
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/cache/invalidate/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Database Indexes

Optimized indexes on:
- `UserActivity.created_at`
- `UserActivity.user + action`
- `UserActivity.action + created_at`
- `DashboardMetrics.date + period_type`

### Query Optimization

- Uses `select_related()` and `prefetch_related()` for related objects
- Pagination on large datasets
- Aggregation queries for summaries

## Testing

Run analytics tests:

```bash
# All analytics tests
python manage.py test apps.analytics

# Specific test files
python manage.py test apps.analytics.tests.test_new_endpoints
python manage.py test apps.analytics.tests.test_middleware
python manage.py test apps.analytics.tests.test_tasks

# With coverage
coverage run --source='apps.analytics' manage.py test apps.analytics
coverage report
coverage html
```

## Monitoring

### Health Checks

Check system health programmatically:

```python
from apps.analytics.services import AnalyticsService

health = AnalyticsService.get_system_health()

if health['error_rate'] > 5.0:
    # Alert: High error rate
    send_alert(f"Error rate: {health['error_rate']}%")

if health['active_users_today'] == 0:
    # Alert: No active users
    send_alert("No users active today")
```

### Celery Task Monitoring

Monitor Celery tasks using Flower:

```bash
pip install flower
celery -A azure_advisor_reports flower
```

Access Flower dashboard at: `http://localhost:5555`

## Troubleshooting

### Common Issues

**1. Middleware not tracking activities**

- Check middleware is properly configured in `settings.py`
- Verify user is authenticated
- Check response status codes (only 2xx tracked)

**2. Celery tasks not running**

- Ensure Redis is running: `redis-cli ping`
- Check Celery worker is running
- Check Celery beat is running
- Verify task names in logs

**3. High memory usage**

- Reduce cache TTL values
- Run cleanup tasks more frequently
- Check for memory leaks in custom tasks

**4. Slow query performance**

- Run `python manage.py migrate` to ensure indexes exist
- Check database query plans
- Consider adding additional indexes

### Debug Mode

Enable debug logging for analytics:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'analytics': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Production Deployment

### Checklist

- [ ] Configure Redis with persistence
- [ ] Set up Celery worker monitoring (Supervisor/systemd)
- [ ] Configure Celery beat scheduler
- [ ] Enable production caching (Redis/Memcached)
- [ ] Set up log aggregation (CloudWatch/ELK)
- [ ] Configure database connection pooling
- [ ] Enable database query optimization
- [ ] Set up automated backups for analytics data
- [ ] Configure rate limiting
- [ ] Monitor system health endpoint
- [ ] Set up alerts for critical metrics

### Environment Variables

```bash
# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Analytics
ANALYTICS_CACHE_TTL=900  # 15 minutes
ANALYTICS_RETENTION_DAYS=90
```

## Contributing

See main project [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

See main project [LICENSE](../../LICENSE) file.

## Support

For issues specific to analytics module:
1. Check this README and API documentation
2. Search existing issues
3. Create new issue with:
   - Environment details
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs

---

**Module Version:** 1.0.0
**Last Updated:** January 2025
