# History Module - Backend Endpoints Documentation

## Overview
This document describes all the backend endpoints implemented for the History module of the Azure Advisor Reports Platform.

All endpoints require authentication via JWT token.

---

## Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/reports/` | List reports with advanced filtering |
| GET | `/api/v1/reports/history/statistics/` | Get aggregated statistics |
| GET | `/api/v1/reports/history/trends/` | Get trend data for charts |
| GET | `/api/v1/reports/users/` | Get users list for filters |
| POST | `/api/v1/reports/export-csv/` | Export reports to CSV |

---

## 1. GET /api/v1/reports/ (Enhanced)

### Description
List all reports with advanced filtering, searching, and pagination support.

### Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `report_type` | string | No | Comma-separated report types | `cost,security` |
| `status` | string | No | Comma-separated statuses | `completed,failed` |
| `created_by` | string | No | Comma-separated user IDs or emails | `uuid1,user@example.com` |
| `client_id` | UUID | No | Filter by client | `123e4567-e89b-12d3-a456-426614174000` |
| `date_from` | date | No | Start date (YYYY-MM-DD) | `2025-01-01` |
| `date_to` | date | No | End date (YYYY-MM-DD) | `2025-01-31` |
| `search` | string | No | Search in title and client name | `azure` |
| `ordering` | string | No | Sort field (prefix with - for desc) | `-created_at` |
| `page` | integer | No | Page number | `1` |
| `page_size` | integer | No | Items per page | `20` |

### Valid Values
- **report_type**: `detailed`, `executive`, `cost`, `security`, `operations`
- **status**: `pending`, `uploaded`, `processing`, `generating`, `completed`, `failed`, `cancelled`
- **ordering**: `created_at`, `-created_at`, `client__company_name`, `report_type`, `status`, `updated_at`

### Response Example
```json
{
  "count": 247,
  "next": "http://localhost:8000/api/v1/reports/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "title": "Azure Cost Analysis",
      "report_type": "cost",
      "status": "completed",
      "client": "uuid",
      "client_name": "Acme Corp",
      "created_by": "uuid",
      "created_by_name": "John Doe",
      "created_at": "2025-01-25T10:30:00Z",
      "updated_at": "2025-01-25T11:00:00Z",
      "processing_completed_at": "2025-01-25T11:00:00Z",
      "recommendation_count": 42,
      "total_potential_savings": 15000.00,
      "html_file": "/media/reports/html/2025/01/report.html",
      "pdf_file": "/media/reports/pdf/2025/01/report.pdf"
    }
  ]
}
```

### Example Requests
```bash
# Get all completed cost and security reports
GET /api/v1/reports/?report_type=cost,security&status=completed

# Search for reports containing "azure" for a specific client
GET /api/v1/reports/?search=azure&client_id=uuid123

# Get reports created by specific users in January 2025
GET /api/v1/reports/?created_by=uuid1,uuid2&date_from=2025-01-01&date_to=2025-01-31

# Sort by newest first
GET /api/v1/reports/?ordering=-created_at
```

---

## 2. GET /api/v1/reports/history/statistics/

### Description
Get aggregated statistics for reports with period-over-period comparison.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date_from` | date | No | Start date for filtering |
| `date_to` | date | No | End date for filtering |
| `report_type` | string | No | Comma-separated report types |
| `status` | string | No | Comma-separated statuses |
| `created_by` | string | No | Comma-separated user IDs |
| `client_id` | UUID | No | Filter by client |

### Response Example
```json
{
  "total_reports": 1247,
  "total_reports_change": 12.5,
  "reports_this_month": 87,
  "reports_this_month_change": 5.2,
  "total_size": 2516582400,
  "total_size_formatted": "2.4 GB",
  "total_size_change": 8.1,
  "breakdown": {
    "cost": 45,
    "security": 32,
    "operations": 28,
    "detailed": 15,
    "executive": 12
  }
}
```

### Field Descriptions
- `total_reports`: Total number of reports in the selected period
- `total_reports_change`: Percentage change vs previous period (same duration)
- `reports_this_month`: Reports created in the current month
- `reports_this_month_change`: Percentage change vs previous month
- `total_size`: Total file size in bytes (CSV + HTML + PDF)
- `total_size_formatted`: Human-readable file size
- `total_size_change`: Percentage change in file size vs previous period
- `breakdown`: Count of reports by type

### Caching
This endpoint uses a 2-minute cache to improve performance.

### Example Requests
```bash
# Get statistics for January 2025
GET /api/v1/reports/history/statistics/?date_from=2025-01-01&date_to=2025-01-31

# Get statistics for completed reports only
GET /api/v1/reports/history/statistics/?status=completed

# Get statistics for specific report types
GET /api/v1/reports/history/statistics/?report_type=cost,security
```

---

## 3. GET /api/v1/reports/history/trends/

### Description
Get time-series data for visualizing report creation trends.

### Query Parameters

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `date_from` | date | **Yes** | Start date (YYYY-MM-DD) | - |
| `date_to` | date | **Yes** | End date (YYYY-MM-DD) | - |
| `granularity` | string | No | `day`, `week`, or `month` | `day` |
| `report_type` | string | No | Comma-separated types | - |
| `status` | string | No | Comma-separated statuses | - |
| `created_by` | string | No | Comma-separated user IDs | - |
| `client_id` | UUID | No | Filter by client | - |

### Response Example
```json
{
  "data": [
    {
      "date": "2025-01-01",
      "total": 15,
      "by_type": {
        "cost": 5,
        "security": 4,
        "operations": 3,
        "detailed": 2,
        "executive": 1
      }
    },
    {
      "date": "2025-01-02",
      "total": 18,
      "by_type": {
        "cost": 6,
        "security": 5,
        "operations": 4,
        "detailed": 2,
        "executive": 1
      }
    }
  ]
}
```

### Field Descriptions
- `date`: Date in YYYY-MM-DD format
- `total`: Total reports created on this date
- `by_type`: Breakdown of reports by type for this date

### Notes
- Dates with no reports will have `total: 0` and zeros in `by_type`
- All report types are included in `by_type`, even if count is 0
- Granularity affects date grouping:
  - `day`: One data point per day
  - `week`: One data point per week (starting Monday)
  - `month`: One data point per month

### Example Requests
```bash
# Get daily trends for last 30 days
GET /api/v1/reports/history/trends/?date_from=2024-12-25&date_to=2025-01-25&granularity=day

# Get weekly trends for Q1 2025
GET /api/v1/reports/history/trends/?date_from=2025-01-01&date_to=2025-03-31&granularity=week

# Get trends for cost reports only
GET /api/v1/reports/history/trends/?date_from=2025-01-01&date_to=2025-01-31&report_type=cost
```

---

## 4. GET /api/v1/reports/users/

### Description
Get list of users who have created reports, useful for populating filter dropdowns.

### Query Parameters
None

### Response Example
```json
{
  "users": [
    {
      "id": "uuid-1",
      "username": "john.doe@company.com",
      "full_name": "John Doe",
      "report_count": 42
    },
    {
      "id": "uuid-2",
      "username": "jane.smith@company.com",
      "full_name": "Jane Smith",
      "report_count": 38
    }
  ]
}
```

### Field Descriptions
- `id`: User UUID
- `username`: User's email/username
- `full_name`: User's first and last name
- `report_count`: Number of reports created by this user

### Notes
- Only users with at least 1 report are included
- Users are ordered by `report_count` descending (most active first)

### Example Request
```bash
GET /api/v1/reports/users/
```

---

## 5. POST /api/v1/reports/export-csv/

### Description
Export filtered reports to a CSV file for download.

### Request Body
```json
{
  "date_from": "2025-01-01",
  "date_to": "2025-01-31",
  "report_type": ["cost", "security"],
  "status": ["completed"],
  "created_by": ["uuid1", "uuid2"],
  "client_id": "uuid",
  "search": "azure"
}
```

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date_from` | date | No | Start date (YYYY-MM-DD) |
| `date_to` | date | No | End date (YYYY-MM-DD) |
| `report_type` | array | No | List of report types |
| `status` | array | No | List of statuses |
| `created_by` | array | No | List of user IDs |
| `client_id` | UUID | No | Client UUID |
| `search` | string | No | Search term |

### Response
- **Content-Type**: `text/csv; charset=utf-8`
- **Content-Disposition**: `attachment; filename="reports_export_2025-01-25.csv"`
- **Body**: CSV file with the following columns:

| Column | Description |
|--------|-------------|
| ID | Report UUID |
| Title | Report title |
| Report Type | Human-readable type |
| Client | Client company name |
| Created By | User's full name |
| Created Date | Creation timestamp |
| Status | Human-readable status |
| File Size | Total size (formatted) |
| Recommendations | Number of recommendations |
| Potential Savings | Total potential savings |

### Limits
- Maximum 10,000 records per export
- If more records match the filters, a 400 error is returned with instructions to add more filters

### Example Requests
```bash
# Export all completed reports from January 2025
POST /api/v1/reports/export-csv/
Content-Type: application/json

{
  "date_from": "2025-01-01",
  "date_to": "2025-01-31",
  "status": ["completed"]
}

# Export cost reports for specific client
POST /api/v1/reports/export-csv/
Content-Type: application/json

{
  "report_type": ["cost"],
  "client_id": "uuid123"
}
```

### Error Responses

**Too many records:**
```json
{
  "status": "error",
  "message": "Too many records to export. Maximum is 10000, found 15000. Please add more filters."
}
```

**Invalid date range:**
```json
{
  "status": "error",
  "message": "Invalid request data",
  "errors": {
    "date_to": ["date_to must be greater than or equal to date_from"]
  }
}
```

---

## Authentication

All endpoints require authentication. Include the JWT token in the Authorization header:

```bash
Authorization: Bearer <your-jwt-token>
```

### Example with cURL
```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
     http://localhost:8000/api/v1/reports/history/statistics/
```

---

## Error Handling

### Common Error Responses

**401 Unauthorized** - Missing or invalid authentication
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**400 Bad Request** - Invalid parameters
```json
{
  "status": "error",
  "message": "Invalid date_from format. Use YYYY-MM-DD"
}
```

**500 Internal Server Error** - Server error
```json
{
  "status": "error",
  "message": "Failed to calculate statistics",
  "errors": {
    "detail": "Error details..."
  }
}
```

---

## Performance Considerations

### Database Indexes
The following indexes have been added for optimal performance:
- `idx_report_created`: Index on `created_at` (descending)
- `idx_report_client_status`: Composite index on `client` + `status`
- `idx_report_status_date`: Composite index on `status` + `created_at`
- `idx_report_user_date`: Composite index on `created_by` + `created_at`
- `idx_report_type_status_date`: Composite index on `report_type` + `status` + `created_at`

### Caching
- Statistics endpoint: 2-minute cache
- Cache key based on query parameters
- Automatic cache invalidation after timeout

### Query Optimization
- `select_related()` for foreign keys (client, created_by)
- `prefetch_related()` for reverse relations (recommendations)
- Efficient aggregations using Django ORM
- Bulk operations for large datasets

---

## Testing

Run the test suite:
```bash
python manage.py test apps.reports.tests
```

Test coverage includes:
- All endpoint responses and status codes
- Filter combinations
- Date range validation
- Authentication requirements
- CSV export content validation
- Error handling scenarios

---

## Migration

Apply the database migration for new indexes:
```bash
python manage.py migrate reports 0003_add_history_indexes
```

This adds the composite index for multi-field filtering optimization.

---

## Change Log

### Version 1.0 (2025-01-25)
- Initial implementation of History module endpoints
- Advanced filtering support with multi-value filters
- Statistics endpoint with period-over-period comparison
- Trends endpoint with configurable granularity
- Users list endpoint for filter dropdowns
- CSV export with 10K record limit
- Comprehensive test coverage
- Database indexes for performance optimization
- 2-minute caching for statistics endpoint
