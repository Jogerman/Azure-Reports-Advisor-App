# Analytics API Documentation

Complete API documentation for the Analytics module of Azure Advisor Reports Platform.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [New Endpoints](#new-endpoints)
   - [User Activity](#1-user-activity)
   - [Activity Summary](#2-activity-summary)
   - [System Health](#3-system-health)
4. [Existing Endpoints](#existing-endpoints)
5. [Error Handling](#error-handling)
6. [Examples](#examples)

---

## Overview

The Analytics API provides comprehensive insights into:
- User activity tracking and monitoring
- System health metrics
- Report generation analytics
- Performance statistics

**Base URL:** `/api/v1/analytics/`

**API Version:** v1

---

## Authentication

All analytics endpoints require authentication via JWT token.

**Header:**
```http
Authorization: Bearer <your-jwt-token>
```

**Roles & Permissions:**
- **Admin**: Full access to all analytics endpoints
- **Manager**: Access to most endpoints including system health
- **Analyst**: Access to activity endpoints (own data only)
- **Viewer**: Read-only access to dashboard metrics

---

## New Endpoints

### 1. User Activity

Get detailed user activity with filtering and pagination.

**Endpoint:** `GET /api/v1/analytics/user-activity/`

**Authentication:** Required

**Permissions:**
- Admins can view all user activities
- Regular users can only view their own activities

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_id` | UUID | No | - | Filter by specific user (admin only) |
| `date_from` | ISO Date | No | - | Start date for filtering (YYYY-MM-DD or ISO 8601) |
| `date_to` | ISO Date | No | - | End date for filtering (YYYY-MM-DD or ISO 8601) |
| `activity_type` | String | No | - | Filter by action type (see available types below) |
| `limit` | Integer | No | 25 | Items per page (max: 100) |
| `offset` | Integer | No | 0 | Pagination offset |

#### Available Activity Types

- `login` - User login
- `logout` - User logout
- `create_client` - Client creation
- `update_client` - Client update
- `delete_client` - Client deletion
- `upload_csv` - CSV file upload
- `generate_report` - Report generation
- `download_report` - Report download
- `share_report` - Report sharing
- `view_dashboard` - Dashboard view
- `other` - Other activities

#### Response

**Status:** `200 OK`

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
  "limit": 25,
  "offset": 0,
  "has_next": true,
  "has_previous": false
}
```

#### Example Requests

**Get all activities for current user:**
```bash
curl -X GET "https://api.example.com/api/v1/analytics/user-activity/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Filter by date range:**
```bash
curl -X GET "https://api.example.com/api/v1/analytics/user-activity/?date_from=2025-01-01&date_to=2025-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Filter by activity type:**
```bash
curl -X GET "https://api.example.com/api/v1/analytics/user-activity/?activity_type=generate_report" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Pagination:**
```bash
curl -X GET "https://api.example.com/api/v1/analytics/user-activity/?limit=50&offset=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Error Responses

**400 Bad Request** - Invalid parameters
```json
{
  "error": "Invalid date_from format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
}
```

**401 Unauthorized** - Missing or invalid token
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 2. Activity Summary

Get aggregated activity summary grouped by specified field.

**Endpoint:** `GET /api/v1/analytics/activity-summary/`

**Authentication:** Required

**Permissions:** All authenticated users

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `date_from` | ISO Date | No | - | Start date for filtering |
| `date_to` | ISO Date | No | - | End date for filtering |
| `group_by` | String | No | `activity_type` | Group by field: `activity_type`, `user`, or `day` |

#### Response

**Status:** `200 OK`

**Grouped by activity_type:**
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
    },
    {
      "activity_type": "create_client",
      "count": 12,
      "percentage": 6.3
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

**Grouped by user:**
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

**Grouped by day:**
```json
{
  "summary": [
    {
      "date": "2025-01-15",
      "count": 45,
      "percentage": 23.6
    },
    {
      "date": "2025-01-16",
      "count": 38,
      "percentage": 19.9
    }
  ],
  "total_activities": 191,
  "date_range": {
    "from": "2025-01-01",
    "to": "2025-01-31"
  },
  "group_by": "day"
}
```

#### Example Requests

**Get activity summary by type:**
```bash
curl -X GET "https://api.example.com/api/v1/analytics/activity-summary/?group_by=activity_type" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get activity summary by user for last 30 days:**
```bash
curl -X GET "https://api.example.com/api/v1/analytics/activity-summary/?group_by=user&date_from=2025-01-01&date_to=2025-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get daily activity breakdown:**
```bash
curl -X GET "https://api.example.com/api/v1/analytics/activity-summary/?group_by=day" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Error Responses

**400 Bad Request** - Invalid group_by parameter
```json
{
  "error": "Invalid group_by. Must be one of: activity_type, user, day"
}
```

---

### 3. System Health

Get current system health metrics.

**Endpoint:** `GET /api/v1/analytics/system-health/`

**Authentication:** Required

**Permissions:** Admin or Manager only

#### Query Parameters

None

#### Response

**Status:** `200 OK`

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

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `database_size` | Integer | Database size in bytes |
| `database_size_formatted` | String | Human-readable database size |
| `total_reports` | Integer | Total number of reports in system |
| `active_users_today` | Integer | Number of unique users active today |
| `active_users_this_week` | Integer | Number of unique users active this week |
| `avg_report_generation_time` | Float | Average report generation time in seconds |
| `error_rate` | Float | Error rate percentage (last 24 hours) |
| `storage_used` | Integer | Storage usage in bytes |
| `storage_used_formatted` | String | Human-readable storage size |
| `uptime` | String | System uptime |
| `last_calculated` | String | ISO timestamp of calculation |

#### Example Request

```bash
curl -X GET "https://api.example.com/api/v1/analytics/system-health/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Error Responses

**403 Forbidden** - Insufficient permissions
```json
{
  "error": "Permission denied",
  "message": "Only admins and managers can view system health"
}
```

---

## Existing Endpoints

### Dashboard Analytics
`GET /api/v1/analytics/dashboard/`

Returns complete dashboard data including metrics, trends, and recent activity.

### Dashboard Metrics
`GET /api/v1/analytics/metrics/`

Returns key metrics only (without chart data).

### Trend Data
`GET /api/v1/analytics/trends/?days=30`

Returns trend data for specified period (7, 30, or 90 days).

### Category Distribution
`GET /api/v1/analytics/categories/`

Returns recommendation distribution by category.

### Recent Activity
`GET /api/v1/analytics/recent-activity/?limit=10`

Returns recent report activity.

### Client Performance
`GET /api/v1/analytics/client-performance/?client_id=<uuid>`

Returns performance metrics for a specific client.

### Business Impact Distribution
`GET /api/v1/analytics/business-impact/`

Returns distribution by business impact level.

### Cache Invalidation
`POST /api/v1/analytics/cache/invalidate/`

Invalidates all analytics caches (admin only).

---

## Error Handling

All endpoints follow consistent error response format:

### Common HTTP Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Error Response Format

```json
{
  "error": "Error type or message",
  "message": "Detailed error description"
}
```

---

## Examples

### Python Example (using requests)

```python
import requests
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://api.example.com"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Get user activity for last 7 days
date_from = (datetime.now() - timedelta(days=7)).isoformat()
date_to = datetime.now().isoformat()

response = requests.get(
    f"{BASE_URL}/api/v1/analytics/user-activity/",
    headers=headers,
    params={
        "date_from": date_from,
        "date_to": date_to,
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
    print(response.json())
```

### JavaScript Example (using fetch)

```javascript
const BASE_URL = 'https://api.example.com';
const TOKEN = 'your-jwt-token';

async function getActivitySummary() {
  try {
    const response = await fetch(
      `${BASE_URL}/api/v1/analytics/activity-summary/?group_by=activity_type`,
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
    console.log('Activity Summary:', data);

    // Process summary data
    data.summary.forEach(item => {
      console.log(`${item.activity_type}: ${item.count} (${item.percentage}%)`);
    });

  } catch (error) {
    console.error('Error fetching activity summary:', error);
  }
}

getActivitySummary();
```

### cURL Examples

**Get system health:**
```bash
curl -X GET "https://api.example.com/api/v1/analytics/system-health/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

**Get activity summary grouped by user:**
```bash
curl -X GET "https://api.example.com/api/v1/analytics/activity-summary/?group_by=user&date_from=2025-01-01" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

**Get paginated user activities:**
```bash
curl -X GET "https://api.example.com/api/v1/analytics/user-activity/?limit=25&offset=0&activity_type=generate_report" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## Rate Limiting

Analytics endpoints are cached and optimized for performance:

- **System Health:** Cached for 5 minutes
- **Activity Summary:** No caching (real-time)
- **User Activity:** No caching (real-time)
- **Dashboard Metrics:** Cached for 15 minutes

**Note:** Admins can force cache refresh using the cache invalidation endpoint.

---

## Best Practices

1. **Pagination:** Always use pagination for large datasets
2. **Date Filtering:** Limit date ranges to avoid performance issues
3. **Caching:** Be aware of cache TTLs when expecting real-time data
4. **Error Handling:** Always handle error responses gracefully
5. **Authentication:** Securely store and manage JWT tokens

---

## Support

For issues or questions:
- **Email:** support@azureadvisorreports.com
- **Documentation:** https://docs.azureadvisorreports.com
- **GitHub:** https://github.com/your-org/azure-advisor-reports

---

**Last Updated:** January 2025
**API Version:** v1.0
