# Analytics Module - Quick Start Guide

## Setup (5 minutes)

### Step 1: Add Middleware

Edit `azure_advisor_reports/settings.py`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Add this line:
    'apps.analytics.middleware.UserActivityTrackingMiddleware',
]
```

### Step 2: Configure Celery Beat

Add to `azure_advisor_reports/settings.py`:

```python
from apps.analytics.celery_config import ANALYTICS_CELERY_BEAT_SCHEDULE

# Merge with existing schedule
CELERY_BEAT_SCHEDULE = {
    **ANALYTICS_CELERY_BEAT_SCHEDULE,
}
```

### Step 3: Initialize

```bash
# Run migrations (if needed)
python manage.py migrate analytics

# Initialize analytics
python manage.py initialize_analytics

# Start Celery (in separate terminal)
celery -A azure_advisor_reports worker --beat --loglevel=info
```

---

## New Endpoints

### 1. User Activity

**Get detailed user activity with filters**

```bash
GET /api/v1/analytics/user-activity/
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/user-activity/?date_from=2025-01-01&activity_type=generate_report&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Query Parameters:**
- `user_id` (UUID) - Filter by user (admin only)
- `date_from` (ISO date) - Start date
- `date_to` (ISO date) - End date
- `activity_type` - Type of activity (generate_report, upload_csv, etc.)
- `limit` (int) - Items per page (default: 25, max: 100)
- `offset` (int) - Pagination offset

**Response:**

```json
{
  "activities": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "username": "john.doe@company.com",
        "full_name": "John Doe"
      },
      "activity_type": "generate_report",
      "description": "Generated a new report",
      "metadata": {
        "path": "/api/v1/reports/",
        "method": "POST",
        "client_id": "abc-123",
        "report_type": "executive"
      },
      "timestamp": "2025-01-15T10:30:00Z"
    }
  ],
  "total_count": 145,
  "limit": 10,
  "offset": 0,
  "has_next": true,
  "has_previous": false
}
```

---

### 2. Activity Summary

**Get aggregated activity statistics**

```bash
GET /api/v1/analytics/activity-summary/
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/activity-summary/?group_by=activity_type&date_from=2025-01-01" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Query Parameters:**
- `date_from` (ISO date) - Start date
- `date_to` (ISO date) - End date
- `group_by` - Group by: `activity_type`, `user`, or `day` (default: activity_type)

**Response (grouped by activity_type):**

```json
{
  "summary": [
    {
      "activity_type": "generate_report",
      "count": 87,
      "percentage": 45.5
    },
    {
      "activity_type": "download_report",
      "count": 65,
      "percentage": 34.0
    },
    {
      "activity_type": "upload_csv",
      "count": 27,
      "percentage": 14.1
    }
  ],
  "total_activities": 191,
  "date_range": {
    "from": "2025-01-01",
    "to": "2025-01-31"
  },
  "group_by": "activity_type"
}
```

**Response (grouped by user):**

```json
{
  "summary": [
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "username": "john.doe@company.com",
      "count": 145,
      "percentage": 52.3
    },
    {
      "user_id": "456e7890-e89b-12d3-a456-426614174001",
      "username": "jane.smith@company.com",
      "count": 132,
      "percentage": 47.7
    }
  ],
  "total_activities": 277,
  "date_range": {
    "from": "2025-01-01",
    "to": "2025-01-31"
  },
  "group_by": "user"
}
```

---

### 3. System Health

**Get comprehensive system health metrics**

```bash
GET /api/v1/analytics/system-health/
```

**Permissions:** Admin or Manager only

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/system-health/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**

```json
{
  "database_size": 524288000,
  "database_size_formatted": "500.00 MB",
  "total_reports": 1247,
  "active_users_today": 15,
  "active_users_this_week": 42,
  "avg_report_generation_time": 45.5,
  "error_rate": 2.3,
  "storage_used": 2516582400,
  "storage_used_formatted": "2.34 GB",
  "uptime": "15 days, 7 hours",
  "last_calculated": "2025-01-15T10:30:00Z"
}
```

---

## Python Examples

### Get User Activity

```python
import requests

BASE_URL = "http://localhost:8000"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Get activity for last 7 days
response = requests.get(
    f"{BASE_URL}/api/v1/analytics/user-activity/",
    headers=headers,
    params={
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "limit": 50
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Total activities: {data['total_count']}")
    for activity in data['activities']:
        print(f"{activity['timestamp']}: {activity['description']}")
else:
    print(f"Error: {response.status_code}")
```

### Get Activity Summary

```python
# Get summary by activity type
response = requests.get(
    f"{BASE_URL}/api/v1/analytics/activity-summary/",
    headers=headers,
    params={"group_by": "activity_type"}
)

if response.status_code == 200:
    data = response.json()
    for item in data['summary']:
        print(f"{item['activity_type']}: {item['count']} ({item['percentage']}%)")
```

### Get System Health

```python
# Get system health (admin only)
response = requests.get(
    f"{BASE_URL}/api/v1/analytics/system-health/",
    headers=headers
)

if response.status_code == 200:
    health = response.json()
    print(f"Error Rate: {health['error_rate']}%")
    print(f"Active Users Today: {health['active_users_today']}")
    print(f"Database Size: {health['database_size_formatted']}")
```

---

## JavaScript/React Examples

### Get User Activity

```javascript
const BASE_URL = 'http://localhost:8000';
const TOKEN = 'your-jwt-token';

async function getUserActivity() {
  try {
    const response = await fetch(
      `${BASE_URL}/api/v1/analytics/user-activity/?limit=25`,
      {
        headers: {
          'Authorization': `Bearer ${TOKEN}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Total activities:', data.total_count);

    data.activities.forEach(activity => {
      console.log(`${activity.timestamp}: ${activity.description}`);
    });

  } catch (error) {
    console.error('Error fetching activity:', error);
  }
}

getUserActivity();
```

### Get Activity Summary

```javascript
async function getActivitySummary(groupBy = 'activity_type') {
  try {
    const response = await fetch(
      `${BASE_URL}/api/v1/analytics/activity-summary/?group_by=${groupBy}`,
      {
        headers: {
          'Authorization': `Bearer ${TOKEN}`,
          'Content-Type': 'application/json'
        }
      }
    );

    const data = await response.json();
    console.log('Activity Summary:', data);

    data.summary.forEach(item => {
      console.log(`${item.activity_type}: ${item.count} (${item.percentage}%)`);
    });

  } catch (error) {
    console.error('Error:', error);
  }
}

getActivitySummary('activity_type');
```

---

## Activity Types Reference

| Activity Type | Description |
|--------------|-------------|
| `login` | User login |
| `logout` | User logout |
| `create_client` | Client creation |
| `update_client` | Client update |
| `delete_client` | Client deletion |
| `upload_csv` | CSV file upload |
| `generate_report` | Report generation |
| `download_report` | Report download |
| `share_report` | Report sharing |
| `view_dashboard` | Dashboard view |
| `other` | Other activities |

---

## Common Use Cases

### 1. Track User Report Generation

```bash
GET /api/v1/analytics/user-activity/?activity_type=generate_report&date_from=2025-01-01
```

### 2. Get Daily Activity Breakdown

```bash
GET /api/v1/analytics/activity-summary/?group_by=day&date_from=2025-01-01&date_to=2025-01-31
```

### 3. Monitor System Health

```bash
GET /api/v1/analytics/system-health/
```

### 4. Analyze User Engagement

```bash
GET /api/v1/analytics/activity-summary/?group_by=user&date_from=2025-01-01
```

### 5. Track Specific User Activity

```bash
GET /api/v1/analytics/user-activity/?user_id=123e4567-e89b-12d3-a456-426614174000
```

---

## Troubleshooting

### Middleware Not Tracking Activities

1. Verify middleware is in `settings.py`
2. Ensure user is authenticated
3. Check response status codes (only 2xx tracked)

### Celery Tasks Not Running

1. Ensure Redis is running: `redis-cli ping`
2. Check Celery worker is running
3. Check Celery beat is running
4. Verify task names in logs

### Empty Activity Data

1. Generate some test activities (create/download reports)
2. Wait a few seconds for middleware to process
3. Check database: `select * from analytics_user_activity limit 10;`

---

## Next Steps

1. Test endpoints with Postman or curl
2. Integrate into frontend dashboard
3. Set up monitoring alerts
4. Review analytics data regularly
5. Adjust cache TTLs based on usage

---

## Full Documentation

- **API Reference:** `apps/analytics/ANALYTICS_API_DOCUMENTATION.md`
- **Module Documentation:** `apps/analytics/README.md`
- **Implementation Report:** `ANALYTICS_MODULE_COMPLETION_REPORT.md`

---

**Ready to use! 🚀**
