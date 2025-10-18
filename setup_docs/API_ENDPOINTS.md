# API Endpoints Documentation

**Azure Advisor Reports Platform**
**API Version:** v1
**Last Updated:** October 6, 2025
**Base URL:** `http://localhost:8000/api/v1` (Development)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Reports API](#reports-api)
3. [Clients API](#clients-api)
4. [Recommendations API](#recommendations-api)
5. [Analytics API](#analytics-api)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)

---

## Authentication

All API endpoints require authentication using JWT tokens obtained from Azure AD.

### Headers Required

```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

### Authentication Endpoints

#### Login with Azure AD

```http
POST /api/auth/login/
```

**Request Body:**
```json
{
  "access_token": "azure_ad_access_token"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "access_token": "jwt_token",
    "refresh_token": "refresh_token",
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "analyst"
    }
  }
}
```

#### Get Current User

```http
GET /api/auth/user/
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "analyst",
    "created_at": "2025-10-01T10:00:00Z"
  }
}
```

#### Logout

```http
POST /api/auth/logout/
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Logout successful"
}
```

---

## Reports API

### List Reports

```http
GET /api/v1/reports/
```

**Query Parameters:**
- `client` (UUID): Filter by client ID
- `report_type` (string): Filter by report type (`detailed`, `executive`, `cost`, `security`, `operations`)
- `status` (string): Filter by status (`pending`, `uploaded`, `processing`, `generating`, `completed`, `failed`, `cancelled`)
- `search` (string): Search by title or client name
- `ordering` (string): Order by field (prefix with `-` for descending)
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 20)

**Response (200 OK):**
```json
{
  "status": "success",
  "count": 42,
  "next": "http://localhost:8000/api/v1/reports/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "client": {
        "id": "uuid",
        "company_name": "Acme Corporation"
      },
      "report_type": "detailed",
      "report_type_display": "Detailed Report",
      "title": "Q4 2025 Azure Optimization Report",
      "status": "completed",
      "status_display": "Completed",
      "created_by": {
        "id": "uuid",
        "name": "John Doe",
        "email": "john@example.com"
      },
      "recommendation_count": 42,
      "total_potential_savings": "12500.00",
      "created_at": "2025-10-05T14:30:00Z",
      "updated_at": "2025-10-05T15:00:00Z",
      "processing_started_at": "2025-10-05T14:31:00Z",
      "processing_completed_at": "2025-10-05T14:35:00Z"
    }
  ]
}
```

### Get Report Details

```http
GET /api/v1/reports/{id}/
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "client": {
      "id": "uuid",
      "company_name": "Acme Corporation",
      "industry": "Technology"
    },
    "report_type": "detailed",
    "title": "Q4 2025 Azure Optimization Report",
    "status": "completed",
    "csv_file": "/media/csv_uploads/2025/10/report.csv",
    "html_file": "/media/reports/html/2025/10/report.html",
    "pdf_file": "/media/reports/pdf/2025/10/report.pdf",
    "analysis_data": {
      "total_recommendations": 42,
      "category_distribution": {
        "cost": 15,
        "security": 12,
        "reliability": 8,
        "operational_excellence": 5,
        "performance": 2
      },
      "business_impact_distribution": {
        "high": 10,
        "medium": 22,
        "low": 10
      },
      "estimated_monthly_savings": "1041.67",
      "estimated_annual_savings": "12500.00",
      "advisor_score": 87.5
    },
    "error_message": "",
    "retry_count": 0,
    "created_by": {
      "id": "uuid",
      "name": "John Doe",
      "email": "john@example.com"
    },
    "created_at": "2025-10-05T14:30:00Z",
    "updated_at": "2025-10-05T15:00:00Z",
    "csv_uploaded_at": "2025-10-05T14:30:00Z",
    "processing_started_at": "2025-10-05T14:31:00Z",
    "processing_completed_at": "2025-10-05T14:35:00Z"
  }
}
```

### Upload CSV File

```http
POST /api/v1/reports/upload/
```

**Request (multipart/form-data):**
```
csv_file: <file>
client_id: uuid
report_type: detailed (optional, default: detailed)
title: Custom Report Title (optional)
```

**Response (201 Created):**
```json
{
  "status": "success",
  "message": "CSV uploaded successfully",
  "data": {
    "report_id": "uuid",
    "report": {
      "id": "uuid",
      "client": {
        "id": "uuid",
        "company_name": "Acme Corporation"
      },
      "report_type": "detailed",
      "title": "Custom Report Title",
      "status": "uploaded",
      "created_at": "2025-10-05T14:30:00Z"
    }
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Validation failed",
  "errors": {
    "csv_file": ["This field is required."],
    "client_id": ["This field is required."]
  }
}
```

### Process CSV File

```http
POST /api/v1/reports/{id}/process/
```

**Description:** Processes the uploaded CSV file and extracts recommendations. This operation is synchronous for now but will be moved to async processing in production.

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "CSV processed successfully",
  "data": {
    "report_id": "uuid",
    "recommendations_count": 42,
    "statistics": {
      "total_recommendations": 42,
      "category_distribution": {
        "cost": 15,
        "security": 12,
        "reliability": 8,
        "operational_excellence": 5,
        "performance": 2
      },
      "business_impact_distribution": {
        "high": 10,
        "medium": 22,
        "low": 10
      },
      "estimated_monthly_savings": "1041.67",
      "estimated_annual_savings": "12500.00"
    }
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "message": "CSV processing failed",
  "errors": {
    "detail": "Invalid CSV format: Missing required column 'Recommendation'"
  }
}
```

### Generate Report Files

```http
POST /api/v1/reports/{id}/generate/
```

**Request Body:**
```json
{
  "format": "both",  // "html", "pdf", or "both" (default: "both")
  "async": true      // Generate asynchronously (default: true)
}
```

**Response (202 Accepted) - Async Mode:**
```json
{
  "status": "success",
  "message": "Report generation started",
  "data": {
    "report_id": "uuid",
    "task_id": "celery-task-id",
    "status_url": "http://localhost:8000/api/v1/reports/uuid/status/?task_id=celery-task-id"
  }
}
```

**Response (200 OK) - Sync Mode:**
```json
{
  "status": "success",
  "message": "HTML, PDF report generated successfully",
  "data": {
    "report_id": "uuid",
    "files_generated": ["HTML", "PDF"],
    "html_url": "http://localhost:8000/api/v1/reports/uuid/download/html/",
    "pdf_url": "http://localhost:8000/api/v1/reports/uuid/download/pdf/"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Report must be completed before generation. Current status: processing"
}
```

### Get Report Status

```http
GET /api/v1/reports/{id}/status/?task_id={celery-task-id}
```

**Description:** Get the current status of a report and optionally track Celery task progress.

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "report_id": "uuid",
    "report_status": "completed",
    "report_data": {
      "client": "Acme Corporation",
      "report_type": "Detailed Report",
      "created_at": "2025-10-05T14:30:00Z",
      "updated_at": "2025-10-05T15:00:00Z"
    },
    "task_id": "celery-task-id",
    "task_state": "SUCCESS",
    "task_info": null,
    "message": "Task completed successfully",
    "task_result": {
      "status": "success",
      "report_id": "uuid",
      "files_generated": ["HTML", "PDF"],
      "file_paths": {
        "html": "/media/reports/html/2025/10/report.html",
        "pdf": "/media/reports/pdf/2025/10/report.pdf"
      }
    },
    "html_url": "http://localhost:8000/api/v1/reports/uuid/download/html/",
    "pdf_url": "http://localhost:8000/api/v1/reports/uuid/download/pdf/",
    "processing_started_at": "2025-10-05T14:31:00Z",
    "processing_completed_at": "2025-10-05T14:35:00Z",
    "processing_duration_seconds": 240.5
  }
}
```

**Task States:**
- `PENDING`: Task is pending or does not exist
- `STARTED`: Task has started
- `SUCCESS`: Task completed successfully
- `FAILURE`: Task failed
- `RETRY`: Task is retrying

### Get Report Statistics

```http
GET /api/v1/reports/{id}/statistics/
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "total_recommendations": 42,
    "category_distribution": {
      "cost": 15,
      "security": 12,
      "reliability": 8,
      "operational_excellence": 5,
      "performance": 2
    },
    "business_impact_distribution": {
      "high": 10,
      "medium": 22,
      "low": 10
    },
    "estimated_monthly_savings": "1041.67",
    "estimated_annual_savings": "12500.00",
    "advisor_score": 87.5,
    "top_recommendations": [
      {
        "category": "cost",
        "business_impact": "high",
        "recommendation": "Right-size underutilized virtual machines",
        "potential_savings": "3500.00",
        "resource_name": "vm-prod-01"
      }
    ]
  }
}
```

### Get Report Recommendations

```http
GET /api/v1/reports/{id}/recommendations/
```

**Query Parameters:**
- `category` (string): Filter by category
- `business_impact` (string): Filter by impact level
- `min_savings` (decimal): Minimum potential savings

**Response (200 OK):**
```json
{
  "status": "success",
  "count": 42,
  "data": [
    {
      "id": "uuid",
      "category": "cost",
      "category_display": "Cost",
      "business_impact": "high",
      "business_impact_display": "High",
      "recommendation": "Right-size underutilized virtual machines",
      "subscription_id": "sub-123",
      "subscription_name": "Production Subscription",
      "resource_group": "rg-production",
      "resource_name": "vm-prod-01",
      "resource_type": "Microsoft.Compute/virtualMachines",
      "potential_savings": "3500.00",
      "currency": "USD",
      "potential_benefits": "Reduce costs by downsizing VM",
      "advisor_score_impact": "2.5",
      "created_at": "2025-10-05T14:35:00Z"
    }
  ]
}
```

### Download Report File

```http
GET /api/v1/reports/{id}/download/html/
GET /api/v1/reports/{id}/download/pdf/
```

**Description:** Download the generated HTML or PDF report file.

**Response (200 OK):**
- **Content-Type:** `text/html; charset=utf-8` (for HTML) or `application/pdf` (for PDF)
- **Content-Disposition:** `attachment; filename="Acme_Corporation_Detailed_Report_20251005.html"`
- **Body:** File content

**Error Response (404 Not Found):**
```json
{
  "status": "error",
  "message": "HTML report has not been generated yet"
}
```

### Update Report

```http
PUT /api/v1/reports/{id}/
PATCH /api/v1/reports/{id}/
```

**Request Body (PATCH):**
```json
{
  "title": "Updated Report Title",
  "status": "cancelled"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "title": "Updated Report Title",
    "status": "cancelled",
    "updated_at": "2025-10-05T16:00:00Z"
  }
}
```

### Delete Report

```http
DELETE /api/v1/reports/{id}/
```

**Response (204 No Content)**

---

## Clients API

### List Clients

```http
GET /api/v1/clients/
```

**Query Parameters:**
- `status` (string): Filter by status (`active`, `inactive`)
- `industry` (string): Filter by industry
- `search` (string): Search by company name or contact email
- `ordering` (string): Order by field

**Response (200 OK):**
```json
{
  "status": "success",
  "count": 25,
  "results": [
    {
      "id": "uuid",
      "company_name": "Acme Corporation",
      "industry": "Technology",
      "contact_email": "contact@acme.com",
      "contact_phone": "+1-555-0100",
      "status": "active",
      "azure_subscription_ids": ["sub-123", "sub-456"],
      "created_at": "2025-09-01T10:00:00Z",
      "updated_at": "2025-10-01T10:00:00Z"
    }
  ]
}
```

### Get Client Details

```http
GET /api/v1/clients/{id}/
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "company_name": "Acme Corporation",
    "industry": "Technology",
    "contact_email": "contact@acme.com",
    "contact_phone": "+1-555-0100",
    "contact_person": "Jane Smith",
    "account_manager": {
      "id": "uuid",
      "name": "John Doe",
      "email": "john@example.com"
    },
    "status": "active",
    "azure_subscription_ids": ["sub-123", "sub-456"],
    "notes": "Key client - quarterly reviews",
    "created_at": "2025-09-01T10:00:00Z",
    "updated_at": "2025-10-01T10:00:00Z"
  }
}
```

### Create Client

```http
POST /api/v1/clients/
```

**Request Body:**
```json
{
  "company_name": "Acme Corporation",
  "industry": "Technology",
  "contact_email": "contact@acme.com",
  "contact_phone": "+1-555-0100",
  "contact_person": "Jane Smith",
  "azure_subscription_ids": ["sub-123", "sub-456"],
  "notes": "Key client - quarterly reviews"
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "message": "Client created successfully",
  "data": {
    "id": "uuid",
    "company_name": "Acme Corporation",
    "created_at": "2025-10-06T10:00:00Z"
  }
}
```

### Update Client

```http
PUT /api/v1/clients/{id}/
PATCH /api/v1/clients/{id}/
```

**Request Body (PATCH):**
```json
{
  "contact_email": "newemail@acme.com",
  "notes": "Updated notes"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "company_name": "Acme Corporation",
    "contact_email": "newemail@acme.com",
    "updated_at": "2025-10-06T11:00:00Z"
  }
}
```

### Delete Client

```http
DELETE /api/v1/clients/{id}/
```

**Response (204 No Content)**

### Get Client Statistics

```http
GET /api/v1/clients/{id}/statistics/
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "total_reports": 15,
    "reports_by_type": {
      "detailed": 5,
      "executive": 4,
      "cost": 3,
      "security": 2,
      "operations": 1
    },
    "total_recommendations": 630,
    "total_potential_savings": "187500.00",
    "average_advisor_score": 85.3,
    "last_report_date": "2025-10-05T14:30:00Z"
  }
}
```

---

## Recommendations API

### List Recommendations

```http
GET /api/v1/recommendations/
```

**Query Parameters:**
- `report` (UUID): Filter by report ID
- `report_id` (UUID): Alternative filter by report ID
- `category` (string): Filter by category
- `business_impact` (string): Filter by impact level
- `search` (string): Search in recommendation text, resource name, or type
- `ordering` (string): Order by field (default: `-potential_savings`)

**Response (200 OK):**
```json
{
  "status": "success",
  "count": 42,
  "results": [
    {
      "id": "uuid",
      "report": {
        "id": "uuid",
        "client": "Acme Corporation",
        "report_type": "Detailed Report"
      },
      "category": "cost",
      "category_display": "Cost",
      "business_impact": "high",
      "business_impact_display": "High",
      "recommendation": "Right-size underutilized virtual machines",
      "subscription_id": "sub-123",
      "subscription_name": "Production Subscription",
      "resource_group": "rg-production",
      "resource_name": "vm-prod-01",
      "resource_type": "Microsoft.Compute/virtualMachines",
      "potential_savings": "3500.00",
      "currency": "USD",
      "monthly_savings": "291.67",
      "potential_benefits": "Reduce costs by downsizing VM",
      "retirement_date": null,
      "retiring_feature": "",
      "advisor_score_impact": "2.5",
      "created_at": "2025-10-05T14:35:00Z"
    }
  ]
}
```

### Get Recommendation Details

```http
GET /api/v1/recommendations/{id}/
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "report": {
      "id": "uuid",
      "client": "Acme Corporation",
      "report_type": "Detailed Report",
      "created_at": "2025-10-05T14:30:00Z"
    },
    "category": "cost",
    "business_impact": "high",
    "recommendation": "Right-size underutilized virtual machines",
    "subscription_id": "sub-123",
    "subscription_name": "Production Subscription",
    "resource_group": "rg-production",
    "resource_name": "vm-prod-01",
    "resource_type": "Microsoft.Compute/virtualMachines",
    "potential_savings": "3500.00",
    "currency": "USD",
    "monthly_savings": "291.67",
    "potential_benefits": "Reduce costs by downsizing VM from Standard_D4s_v3 to Standard_D2s_v3",
    "advisor_score_impact": "2.5",
    "csv_row_number": 5,
    "created_at": "2025-10-05T14:35:00Z"
  }
}
```

---

## Analytics API

### Get Dashboard Metrics

```http
GET /api/v1/analytics/dashboard/
```

**Query Parameters:**
- `start_date` (date): Filter metrics from this date (format: YYYY-MM-DD)
- `end_date` (date): Filter metrics until this date (format: YYYY-MM-DD)
- `client_id` (UUID): Filter by specific client

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "summary": {
      "total_clients": 25,
      "total_reports": 150,
      "total_recommendations": 6300,
      "total_potential_savings": "1875000.00",
      "average_advisor_score": 85.3
    },
    "reports_by_month": [
      {
        "month": "2025-10",
        "count": 15,
        "total_savings": "187500.00"
      }
    ],
    "reports_by_type": {
      "detailed": 50,
      "executive": 40,
      "cost": 30,
      "security": 20,
      "operations": 10
    },
    "recommendations_by_category": {
      "cost": 2100,
      "security": 1890,
      "reliability": 1260,
      "operational_excellence": 787,
      "performance": 263
    },
    "top_clients_by_savings": [
      {
        "client_id": "uuid",
        "client_name": "Acme Corporation",
        "total_savings": "250000.00",
        "report_count": 15
      }
    ]
  }
}
```

### Get Client Analytics

```http
GET /api/v1/analytics/clients/{client_id}/
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "client": {
      "id": "uuid",
      "company_name": "Acme Corporation"
    },
    "reports_timeline": [
      {
        "date": "2025-10-05",
        "report_count": 1,
        "advisor_score": 87.5,
        "potential_savings": "12500.00"
      }
    ],
    "recommendations_breakdown": {
      "by_category": {
        "cost": 15,
        "security": 12,
        "reliability": 8,
        "operational_excellence": 5,
        "performance": 2
      },
      "by_impact": {
        "high": 10,
        "medium": 22,
        "low": 10
      }
    },
    "savings_trend": [
      {
        "month": "2025-10",
        "potential_savings": "12500.00"
      }
    ]
  }
}
```

---

## Error Handling

All error responses follow a consistent format:

### Standard Error Response

```json
{
  "status": "error",
  "message": "Brief error description",
  "errors": {
    "field_name": ["Error detail 1", "Error detail 2"]
  }
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 202 | Accepted | Request accepted for processing (async) |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid request data or parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 502 | Bad Gateway | Upstream service error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Common Error Examples

**Validation Error (400):**
```json
{
  "status": "error",
  "message": "Validation failed",
  "errors": {
    "csv_file": ["This field is required."],
    "client_id": ["Invalid UUID format."]
  }
}
```

**Authentication Error (401):**
```json
{
  "status": "error",
  "message": "Authentication credentials were not provided."
}
```

**Permission Error (403):**
```json
{
  "status": "error",
  "message": "You do not have permission to perform this action."
}
```

**Not Found Error (404):**
```json
{
  "status": "error",
  "message": "Report with ID '123e4567-e89b-12d3-a456-426614174000' not found."
}
```

**Server Error (500):**
```json
{
  "status": "error",
  "message": "An internal error occurred. Please try again later.",
  "errors": {
    "detail": "Error details (only in debug mode)"
  }
}
```

---

## Rate Limiting

API endpoints are rate-limited to ensure fair usage and system stability.

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1633024800
```

### Default Limits

| User Role | Requests per Hour |
|-----------|-------------------|
| Viewer | 100 |
| Analyst | 500 |
| Manager | 1000 |
| Admin | 5000 |

### Rate Limit Exceeded Response (429)

```json
{
  "status": "error",
  "message": "Rate limit exceeded. Please try again later.",
  "errors": {
    "detail": "Request limit: 1000 per hour. Resets at 2025-10-06T12:00:00Z"
  }
}
```

---

## Examples

### Complete Workflow: Upload CSV to Download Report

#### Step 1: Upload CSV File

```bash
curl -X POST http://localhost:8000/api/v1/reports/upload/ \
  -H "Authorization: Bearer {jwt_token}" \
  -F "csv_file=@azure_advisor_export.csv" \
  -F "client_id=123e4567-e89b-12d3-a456-426614174000" \
  -F "report_type=detailed" \
  -F "title=Q4 2025 Azure Optimization Report"
```

Response:
```json
{
  "status": "success",
  "message": "CSV uploaded successfully",
  "data": {
    "report_id": "789e4567-e89b-12d3-a456-426614174999",
    "report": {...}
  }
}
```

#### Step 2: Process CSV File

```bash
curl -X POST http://localhost:8000/api/v1/reports/789e4567-e89b-12d3-a456-426614174999/process/ \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json"
```

Response:
```json
{
  "status": "success",
  "message": "CSV processed successfully",
  "data": {
    "report_id": "789e4567-e89b-12d3-a456-426614174999",
    "recommendations_count": 42,
    "statistics": {...}
  }
}
```

#### Step 3: Generate Report (Async)

```bash
curl -X POST http://localhost:8000/api/v1/reports/789e4567-e89b-12d3-a456-426614174999/generate/ \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "both",
    "async": true
  }'
```

Response:
```json
{
  "status": "success",
  "message": "Report generation started",
  "data": {
    "report_id": "789e4567-e89b-12d3-a456-426614174999",
    "task_id": "abc123-task-id",
    "status_url": "http://localhost:8000/api/v1/reports/789.../status/?task_id=abc123-task-id"
  }
}
```

#### Step 4: Check Status

```bash
curl -X GET "http://localhost:8000/api/v1/reports/789e4567-e89b-12d3-a456-426614174999/status/?task_id=abc123-task-id" \
  -H "Authorization: Bearer {jwt_token}"
```

Response:
```json
{
  "status": "success",
  "data": {
    "report_id": "789e4567-e89b-12d3-a456-426614174999",
    "report_status": "completed",
    "task_id": "abc123-task-id",
    "task_state": "SUCCESS",
    "message": "Task completed successfully",
    "html_url": "http://localhost:8000/api/v1/reports/789.../download/html/",
    "pdf_url": "http://localhost:8000/api/v1/reports/789.../download/pdf/"
  }
}
```

#### Step 5: Download Report

```bash
# Download HTML
curl -X GET http://localhost:8000/api/v1/reports/789e4567-e89b-12d3-a456-426614174999/download/html/ \
  -H "Authorization: Bearer {jwt_token}" \
  -o report.html

# Download PDF
curl -X GET http://localhost:8000/api/v1/reports/789e4567-e89b-12d3-a456-426614174999/download/pdf/ \
  -H "Authorization: Bearer {jwt_token}" \
  -o report.pdf
```

### Using JavaScript/TypeScript

```typescript
// API Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';
const AUTH_TOKEN = 'your-jwt-token';

// Upload CSV
const uploadCSV = async (file: File, clientId: string, reportType: string = 'detailed') => {
  const formData = new FormData();
  formData.append('csv_file', file);
  formData.append('client_id', clientId);
  formData.append('report_type', reportType);

  const response = await fetch(`${API_BASE_URL}/reports/upload/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${AUTH_TOKEN}`,
    },
    body: formData,
  });

  return response.json();
};

// Process CSV
const processCSV = async (reportId: string) => {
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}/process/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${AUTH_TOKEN}`,
      'Content-Type': 'application/json',
    },
  });

  return response.json();
};

// Generate Report (Async)
const generateReport = async (reportId: string, format: string = 'both') => {
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}/generate/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${AUTH_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      format,
      async: true,
    }),
  });

  return response.json();
};

// Check Status
const checkStatus = async (reportId: string, taskId?: string) => {
  const url = taskId
    ? `${API_BASE_URL}/reports/${reportId}/status/?task_id=${taskId}`
    : `${API_BASE_URL}/reports/${reportId}/status/`;

  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${AUTH_TOKEN}`,
    },
  });

  return response.json();
};

// Complete Workflow
const completeWorkflow = async (file: File, clientId: string) => {
  try {
    // 1. Upload CSV
    console.log('Uploading CSV...');
    const uploadResult = await uploadCSV(file, clientId, 'detailed');
    const reportId = uploadResult.data.report_id;
    console.log('CSV uploaded. Report ID:', reportId);

    // 2. Process CSV
    console.log('Processing CSV...');
    const processResult = await processCSV(reportId);
    console.log('CSV processed:', processResult.data.recommendations_count, 'recommendations found');

    // 3. Generate Report
    console.log('Generating report...');
    const generateResult = await generateReport(reportId, 'both');
    const taskId = generateResult.data.task_id;
    console.log('Report generation started. Task ID:', taskId);

    // 4. Poll for status
    const pollStatus = async () => {
      const statusResult = await checkStatus(reportId, taskId);

      if (statusResult.data.task_state === 'SUCCESS') {
        console.log('Report generation completed!');
        console.log('HTML URL:', statusResult.data.html_url);
        console.log('PDF URL:', statusResult.data.pdf_url);
        return statusResult.data;
      } else if (statusResult.data.task_state === 'FAILURE') {
        throw new Error('Report generation failed: ' + statusResult.data.task_error);
      } else {
        console.log('Report generation in progress...');
        setTimeout(pollStatus, 2000); // Poll every 2 seconds
      }
    };

    await pollStatus();

  } catch (error) {
    console.error('Error in workflow:', error);
    throw error;
  }
};
```

### Using Python

```python
import requests
import time

# API Configuration
API_BASE_URL = 'http://localhost:8000/api/v1'
AUTH_TOKEN = 'your-jwt-token'

# Headers
headers = {
    'Authorization': f'Bearer {AUTH_TOKEN}',
}

def upload_csv(file_path, client_id, report_type='detailed'):
    """Upload CSV file"""
    with open(file_path, 'rb') as f:
        files = {'csv_file': f}
        data = {
            'client_id': client_id,
            'report_type': report_type,
        }
        response = requests.post(
            f'{API_BASE_URL}/reports/upload/',
            headers=headers,
            files=files,
            data=data
        )
        return response.json()

def process_csv(report_id):
    """Process CSV file"""
    response = requests.post(
        f'{API_BASE_URL}/reports/{report_id}/process/',
        headers=headers
    )
    return response.json()

def generate_report(report_id, format_type='both', async_mode=True):
    """Generate report files"""
    headers_json = {**headers, 'Content-Type': 'application/json'}
    data = {
        'format': format_type,
        'async': async_mode,
    }
    response = requests.post(
        f'{API_BASE_URL}/reports/{report_id}/generate/',
        headers=headers_json,
        json=data
    )
    return response.json()

def check_status(report_id, task_id=None):
    """Check report and task status"""
    url = f'{API_BASE_URL}/reports/{report_id}/status/'
    if task_id:
        url += f'?task_id={task_id}'

    response = requests.get(url, headers=headers)
    return response.json()

def download_report(report_id, format_type='pdf', output_path=None):
    """Download report file"""
    response = requests.get(
        f'{API_BASE_URL}/reports/{report_id}/download/{format_type}/',
        headers=headers
    )

    if output_path:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return output_path
    else:
        return response.content

def complete_workflow(csv_file_path, client_id):
    """Complete workflow from upload to download"""

    # 1. Upload CSV
    print('Uploading CSV...')
    upload_result = upload_csv(csv_file_path, client_id)
    report_id = upload_result['data']['report_id']
    print(f'CSV uploaded. Report ID: {report_id}')

    # 2. Process CSV
    print('Processing CSV...')
    process_result = process_csv(report_id)
    recs_count = process_result['data']['recommendations_count']
    print(f'CSV processed: {recs_count} recommendations found')

    # 3. Generate Report
    print('Generating report...')
    generate_result = generate_report(report_id, format_type='both')
    task_id = generate_result['data']['task_id']
    print(f'Report generation started. Task ID: {task_id}')

    # 4. Poll for status
    while True:
        status_result = check_status(report_id, task_id)
        task_state = status_result['data'].get('task_state')

        if task_state == 'SUCCESS':
            print('Report generation completed!')
            print(f"HTML URL: {status_result['data']['html_url']}")
            print(f"PDF URL: {status_result['data']['pdf_url']}")
            break
        elif task_state == 'FAILURE':
            error_msg = status_result['data'].get('task_error', 'Unknown error')
            raise Exception(f'Report generation failed: {error_msg}')
        else:
            print(f'Report generation in progress... (state: {task_state})')
            time.sleep(2)  # Poll every 2 seconds

    # 5. Download Report
    print('Downloading PDF report...')
    pdf_path = download_report(report_id, 'pdf', 'report.pdf')
    print(f'Report downloaded: {pdf_path}')

    return report_id

# Example usage
if __name__ == '__main__':
    report_id = complete_workflow(
        csv_file_path='azure_advisor_export.csv',
        client_id='123e4567-e89b-12d3-a456-426614174000'
    )
    print(f'Workflow completed successfully! Report ID: {report_id}')
```

---

## Additional Notes

### Pagination

All list endpoints support pagination:

```http
GET /api/v1/reports/?page=2&page_size=50
```

Response includes pagination metadata:
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/reports/?page=3",
  "previous": "http://localhost:8000/api/v1/reports/?page=1",
  "results": [...]
}
```

### Filtering

Use query parameters for filtering:

```http
GET /api/v1/reports/?client=uuid&status=completed&report_type=detailed
```

### Searching

Use the `search` parameter for full-text search:

```http
GET /api/v1/reports/?search=optimization
```

### Ordering

Use the `ordering` parameter to sort results:

```http
GET /api/v1/reports/?ordering=-created_at  # Descending
GET /api/v1/reports/?ordering=created_at   # Ascending
```

### Date Filtering

Use date range filters:

```http
GET /api/v1/reports/?created_after=2025-10-01&created_before=2025-10-31
```

---

**End of API Documentation**

For additional support or questions, please contact the development team or refer to the project documentation.
