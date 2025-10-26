# History Module - Implementation Guide

## Overview
This document provides implementation details and usage instructions for the History module backend endpoints of the Azure Advisor Reports Platform.

## Files Modified/Created

### New Files Created
```
apps/reports/
├── filters.py              # Advanced filtering for reports
├── utils.py               # Helper functions for statistics and trends
├── tests.py               # Comprehensive test suite
└── migrations/
    └── 0003_add_history_indexes.py  # Database migration for indexes
```

### Files Modified
```
apps/reports/
├── views.py               # Added 5 new endpoint methods
├── serializers.py         # Added 6 new serializers
└── models.py             # Updated indexes for performance
```

---

## Installation & Setup

### 1. Apply Database Migrations
```bash
cd azure_advisor_reports
python manage.py migrate reports 0003_add_history_indexes
```

This creates the new composite index for optimized filtering.

### 2. Verify Installation
Check that all endpoints are accessible:
```bash
python manage.py show_urls | grep reports
```

Expected output should include:
```
/api/v1/reports/                                    GET, POST
/api/v1/reports/history/statistics/                 GET
/api/v1/reports/history/trends/                     GET
/api/v1/reports/users/                              GET
/api/v1/reports/export-csv/                         POST
```

### 3. Run Tests
```bash
python manage.py test apps.reports.tests -v 2
```

All tests should pass with >80% coverage.

---

## Architecture Overview

### Component Structure

```
┌─────────────────────────────────────────────────┐
│              Frontend (React)                    │
│  - History Dashboard                            │
│  - Statistics Cards                             │
│  - Trends Chart                                 │
│  - Filters UI                                   │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/REST API
┌──────────────────▼──────────────────────────────┐
│              Backend (Django)                    │
│                                                  │
│  ┌────────────────────────────────────────┐    │
│  │ ReportViewSet (views.py)               │    │
│  │  - history_statistics()                │    │
│  │  - history_trends()                    │    │
│  │  - users_list()                        │    │
│  │  - export_csv()                        │    │
│  └────────────┬───────────────────────────┘    │
│               │                                  │
│  ┌────────────▼───────────────────────────┐    │
│  │ Business Logic (utils.py)              │    │
│  │  - calculate_period_comparison()       │    │
│  │  - get_trends_data()                   │    │
│  │  - apply_filters_from_params()         │    │
│  └────────────┬───────────────────────────┘    │
│               │                                  │
│  ┌────────────▼───────────────────────────┐    │
│  │ Data Layer (models.py)                 │    │
│  │  - Report                              │    │
│  │  - Recommendation                      │    │
│  └────────────┬───────────────────────────┘    │
│               │                                  │
└───────────────┼──────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────┐
│          PostgreSQL Database                  │
│  - Optimized indexes                         │
│  - Composite indexes for filtering           │
└──────────────────────────────────────────────┘
```

---

## Key Features

### 1. Advanced Filtering
- **Multi-value filters**: Support for comma-separated values
- **Date range filtering**: Flexible date ranges with validation
- **Search functionality**: Full-text search in title and client name
- **Sorting**: Multiple sort fields with ascending/descending order

### 2. Statistics Calculation
- **Period comparison**: Automatic comparison with previous period
- **Percentage changes**: Calculate growth/decline rates
- **Breakdown by type**: Distribution of reports by type
- **File size tracking**: Total storage usage with human-readable formatting

### 3. Trend Analysis
- **Flexible granularity**: Day, week, or month grouping
- **Time series data**: Perfect for charting libraries
- **Gap filling**: Ensures continuous data even on days with no reports
- **Type breakdown**: See trends for each report type

### 4. CSV Export
- **Large dataset support**: Up to 10,000 records
- **All filters supported**: Export exactly what you see
- **Formatted output**: Human-readable dates and file sizes
- **Automatic filename**: Includes export date in filename

---

## Usage Examples

### Example 1: Dashboard Statistics
Get statistics for the current month:

```python
import requests

response = requests.get(
    'http://localhost:8000/api/v1/reports/history/statistics/',
    headers={'Authorization': f'Bearer {token}'},
    params={
        'date_from': '2025-01-01',
        'date_to': '2025-01-31'
    }
)

data = response.json()
print(f"Total reports: {data['total_reports']}")
print(f"Growth: {data['total_reports_change']}%")
```

### Example 2: Trends Chart Data
Get daily trends for the last 30 days:

```python
response = requests.get(
    'http://localhost:8000/api/v1/reports/history/trends/',
    headers={'Authorization': f'Bearer {token}'},
    params={
        'date_from': '2024-12-26',
        'date_to': '2025-01-25',
        'granularity': 'day'
    }
)

trends_data = response.json()['data']
# Use with Chart.js, Recharts, etc.
```

### Example 3: Filter by User
Get all reports created by specific users:

```python
response = requests.get(
    'http://localhost:8000/api/v1/reports/',
    headers={'Authorization': f'Bearer {token}'},
    params={
        'created_by': 'user1@example.com,user2@example.com',
        'status': 'completed'
    }
)
```

### Example 4: Export to CSV
Export all completed cost reports from Q1 2025:

```python
response = requests.post(
    'http://localhost:8000/api/v1/reports/export-csv/',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'date_from': '2025-01-01',
        'date_to': '2025-03-31',
        'report_type': ['cost'],
        'status': ['completed']
    }
)

# Save to file
with open('reports_export.csv', 'wb') as f:
    f.write(response.content)
```

---

## Performance Optimization

### Database Indexes
The module uses composite indexes for optimal query performance:

```sql
-- Created by migration 0003_add_history_indexes
CREATE INDEX idx_report_type_status_date
ON reports (report_type, status, created_at DESC);

-- Existing indexes from migration 0002
CREATE INDEX idx_report_created ON reports (created_at DESC);
CREATE INDEX idx_report_user_date ON reports (created_by, created_at DESC);
CREATE INDEX idx_report_status_date ON reports (status, created_at DESC);
```

### Caching Strategy
Statistics endpoint uses Django's cache framework:
```python
# Cache key based on query parameters
cache_key = f"history_stats_{hash(sorted(params))}"
cache.set(cache_key, data, 120)  # 2 minutes
```

To use Redis for production caching, update `settings.py`:
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Query Optimization
All endpoints use:
- `select_related()` for ForeignKey lookups
- `prefetch_related()` for reverse relations
- Efficient aggregations with `Count()`, `Sum()`
- Limited result sets to prevent memory issues

---

## Frontend Integration

### React Example with Axios

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});

// Get statistics
const getStatistics = async (filters) => {
  const response = await api.get('/reports/history/statistics/', {
    params: filters
  });
  return response.data;
};

// Get trends
const getTrends = async (dateFrom, dateTo, granularity = 'day') => {
  const response = await api.get('/reports/history/trends/', {
    params: { date_from: dateFrom, date_to: dateTo, granularity }
  });
  return response.data;
};

// Export CSV
const exportCSV = async (filters) => {
  const response = await api.post('/reports/export-csv/', filters, {
    responseType: 'blob'
  });

  // Trigger download
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `reports_export_${new Date().toISOString().split('T')[0]}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};
```

### TypeScript Types

```typescript
interface StatisticsResponse {
  total_reports: number;
  total_reports_change: number;
  reports_this_month: number;
  reports_this_month_change: number;
  total_size: number;
  total_size_formatted: string;
  total_size_change: number;
  breakdown: {
    [key: string]: number;
  };
}

interface TrendDataPoint {
  date: string;
  total: number;
  by_type: {
    [key: string]: number;
  };
}

interface TrendsResponse {
  data: TrendDataPoint[];
}

interface User {
  id: string;
  username: string;
  full_name: string;
  report_count: number;
}

interface UsersListResponse {
  users: User[];
}
```

---

## Error Handling

### Common Errors and Solutions

**Error: "Both date_from and date_to are required"**
```javascript
// Solution: Always provide both dates for trends endpoint
const params = {
  date_from: '2025-01-01',
  date_to: '2025-01-31',  // Both required
  granularity: 'day'
};
```

**Error: "Too many records to export"**
```javascript
// Solution: Add more filters to reduce result set
const filters = {
  date_from: '2025-01-01',
  date_to: '2025-01-31',
  status: ['completed'],  // Add filters
  report_type: ['cost']   // to reduce count
};
```

**Error: "Invalid granularity"**
```javascript
// Solution: Use only valid granularity values
const validGranularities = ['day', 'week', 'month'];
const granularity = 'day';  // Must be one of these
```

---

## Testing

### Running Tests
```bash
# Run all tests
python manage.py test apps.reports.tests

# Run specific test class
python manage.py test apps.reports.tests.HistoryStatisticsEndpointTests

# Run with coverage
coverage run --source='apps.reports' manage.py test apps.reports.tests
coverage report
coverage html  # Generate HTML report
```

### Test Coverage
The test suite includes:
- ✅ All endpoint HTTP methods
- ✅ Query parameter validation
- ✅ Authentication requirements
- ✅ Filter combinations
- ✅ Date range validation
- ✅ CSV export content
- ✅ Error responses
- ✅ Edge cases (empty data, invalid inputs)

Expected coverage: >80%

---

## Deployment Checklist

### Pre-deployment
- [ ] Run all tests: `python manage.py test apps.reports.tests`
- [ ] Apply migrations: `python manage.py migrate`
- [ ] Check for migration conflicts: `python manage.py showmigrations`
- [ ] Verify database indexes: Check PostgreSQL query plans
- [ ] Update environment variables for production cache

### Production Configuration

**settings.py** additions for production:
```python
# Cache configuration (use Redis in production)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# CSV Export limits
MAX_EXPORT_RECORDS = 10000  # Adjust based on server capacity

# Logging for history endpoints
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/history.log',
        },
    },
    'loggers': {
        'apps.reports.views': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

### Post-deployment
- [ ] Monitor logs for errors
- [ ] Check cache hit rates
- [ ] Verify response times (<200ms for statistics)
- [ ] Test CSV exports with large datasets
- [ ] Monitor database query performance

---

## Troubleshooting

### Slow Statistics Endpoint
**Symptom**: Statistics endpoint takes >2 seconds to respond

**Solutions**:
1. Check if indexes are created: `\d reports` in PostgreSQL
2. Verify cache is working: Check Redis/cache backend
3. Reduce date range for queries
4. Add more specific filters to reduce dataset

### CSV Export Timeouts
**Symptom**: CSV export fails with timeout error

**Solutions**:
1. Reduce MAX_EXPORT_RECORDS in settings
2. Add pagination for large exports
3. Use Celery for async export (future enhancement)
4. Optimize queries with `only()` and `defer()`

### Missing Trends Data
**Symptom**: Trends endpoint returns empty data array

**Solutions**:
1. Verify reports exist in the date range
2. Check date format (must be YYYY-MM-DD)
3. Verify timezone settings match database
4. Check filters aren't too restrictive

---

## Future Enhancements

### Planned Features
1. **Async CSV Export**: Use Celery for large exports
2. **Real-time Updates**: WebSocket support for live statistics
3. **Advanced Analytics**: Predictive trends, anomaly detection
4. **Custom Reports**: User-defined report templates
5. **Data Visualization**: Server-side chart generation
6. **Export Formats**: Add Excel, JSON, XML export options

### API Versioning
When adding new features, use API versioning:
```python
# urls.py
urlpatterns = [
    path('api/v1/', include('apps.reports.urls')),
    path('api/v2/', include('apps.reports.urls_v2')),  # Future
]
```

---

## Support & Contribution

### Getting Help
- Check the documentation: `HISTORY_ENDPOINTS_DOCUMENTATION.md`
- Review test cases for usage examples
- Check Django logs for error details

### Contributing
When adding new features:
1. Write tests first (TDD approach)
2. Update documentation
3. Add migration if changing models
4. Follow existing code patterns
5. Add logging for debugging

---

## Version History

### v1.0.0 (2025-01-25)
- Initial release
- 5 new endpoints implemented
- Advanced filtering support
- Statistics with period comparison
- Trends analysis
- CSV export
- Comprehensive test suite
- Performance optimizations

---

## License
Internal use only - Azure Advisor Reports Platform
