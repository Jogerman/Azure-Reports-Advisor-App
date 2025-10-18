# Azure Advisor Reports Platform - API Documentation

**Version:** 1.0
**API Version:** v1
**Last Updated:** October 2, 2025
**Base URL:** `https://api.yourdomain.com/api/v1`
**Authentication:** Azure AD OAuth 2.0 + JWT

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Conventions](#api-conventions)
4. [Rate Limiting](#rate-limiting)
5. [Error Handling](#error-handling)
6. [Endpoints](#endpoints)
   - [Authentication](#authentication-endpoints)
   - [Users](#user-management-endpoints)
   - [Clients](#client-management-endpoints)
   - [Reports](#report-management-endpoints)
   - [Analytics](#analytics-endpoints)
   - [Health Check](#health-check-endpoint)
7. [Webhooks](#webhooks)
8. [Code Examples](#code-examples)
9. [SDKs](#sdks)
10. [Changelog](#changelog)

---

## Overview

### API Description

The Azure Advisor Reports Platform API provides programmatic access to all platform features, enabling:
- Automated report generation
- Client management
- Analytics data retrieval
- Integration with existing workflows

### API Features

- **RESTful Design**: Standard HTTP methods (GET, POST, PUT, PATCH, DELETE)
- **JSON Format**: All requests and responses use JSON
- **OAuth 2.0**: Secure authentication via Azure AD
- **Pagination**: Efficient handling of large datasets
- **Filtering**: Advanced query capabilities
- **Versioning**: Backward-compatible API versions
- **Rate Limiting**: Fair usage policies

### API Versioning

Current version: **v1**

Version is specified in the URL path:
```
https://api.yourdomain.com/api/v1/...
```

### Supported Formats

- **Request**: `application/json`, `multipart/form-data` (file uploads)
- **Response**: `application/json`

---

## Authentication

### Overview

The API uses a two-step authentication process:
1. **Azure AD OAuth 2.0**: Authenticate user via Microsoft
2. **JWT Token**: Receive JWT token for API requests

### Authentication Flow

```
┌─────────┐         ┌──────────┐         ┌─────────┐         ┌──────────┐
│ Client  │────────▶│ Azure AD │────────▶│ Backend │────────▶│  Client  │
│         │  Login  │          │  Token  │   API   │   JWT   │          │
└─────────┘         └──────────┘         └─────────┘         └──────────┘
```

### Step 1: Azure AD Authentication

**Frontend Process:**

1. User clicks "Sign in with Microsoft"
2. Redirect to Azure AD login page
3. User authenticates with Azure credentials
4. Azure AD redirects back with authorization code
5. Exchange code for access token

**Required Scopes:**
- `openid`: User identity
- `profile`: User profile information
- `email`: User email address
- `User.Read`: Read user profile

### Step 2: Backend JWT Token

Exchange Azure AD access token for backend JWT token.

**Endpoint:** `POST /api/v1/auth/login/`

**Request:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "def50200abc...",
    "expires_in": 3600,
    "token_type": "Bearer",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@company.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "analyst",
      "is_active": true
    }
  },
  "message": "Login successful"
}
```

### Using the JWT Token

Include the JWT token in all API requests:

**Header:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Example cURL:**
```bash
curl -X GET "https://api.yourdomain.com/api/v1/clients/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Token Expiration

- **Access Token**: Expires in 1 hour
- **Refresh Token**: Expires in 7 days

### Refreshing Tokens

**Endpoint:** `POST /api/v1/auth/refresh/`

**Request:**
```json
{
  "refresh_token": "def50200abc..."
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "token_type": "Bearer"
  },
  "message": "Token refreshed successfully"
}
```

### Security Best Practices

1. **Store tokens securely**: Use secure storage (not localStorage for sensitive apps)
2. **Refresh before expiry**: Implement automatic token refresh
3. **Handle 401 errors**: Catch authentication errors and re-authenticate
4. **Use HTTPS**: Always use HTTPS in production
5. **Don't log tokens**: Never log access tokens in client code

---

## API Conventions

### HTTP Methods

| Method | Purpose | Idempotent |
|--------|---------|------------|
| GET | Retrieve resources | Yes |
| POST | Create new resources | No |
| PUT | Update entire resource | Yes |
| PATCH | Partially update resource | No |
| DELETE | Delete resource | Yes |

### Response Structure

**Success Response:**
```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed successfully",
  "meta": {
    "timestamp": "2025-10-02T14:30:00Z",
    "version": "v1"
  }
}
```

**Error Response:**
```json
{
  "status": "error",
  "errors": {
    "field_name": ["Error message 1", "Error message 2"]
  },
  "message": "Validation failed",
  "code": "VALIDATION_ERROR"
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Temporary downtime |

### Pagination

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Example Request:**
```
GET /api/v1/clients/?page=2&page_size=50
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "count": 150,
    "next": "https://api.yourdomain.com/api/v1/clients/?page=3&page_size=50",
    "previous": "https://api.yourdomain.com/api/v1/clients/?page=1&page_size=50",
    "results": [ ... ]
  }
}
```

### Filtering

**Query Parameters:**
- Field-based filtering: `?status=active`
- Search: `?search=contoso`
- Date range: `?created_after=2025-01-01&created_before=2025-12-31`

**Example:**
```
GET /api/v1/reports/?status=completed&client_id=550e8400-e29b-41d4-a716-446655440000
```

### Sorting

**Query Parameter:**
- `ordering`: Field name (prefix with `-` for descending)

**Examples:**
```
GET /api/v1/clients/?ordering=company_name          # Ascending
GET /api/v1/clients/?ordering=-created_at           # Descending
GET /api/v1/reports/?ordering=-created_at,status    # Multiple fields
```

### Date/Time Format

All dates use **ISO 8601** format:
```
2025-10-02T14:30:00Z      # UTC
2025-10-02T10:30:00-04:00 # With timezone
```

---

## Rate Limiting

### Limits

| User Role | Requests per Minute | Requests per Hour |
|-----------|---------------------|-------------------|
| Viewer | 30 | 500 |
| Analyst | 60 | 1,000 |
| Manager | 120 | 2,000 |
| Admin | 300 | 5,000 |

### Rate Limit Headers

Every response includes:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1696267800
```

### Handling Rate Limits

**429 Response:**
```json
{
  "status": "error",
  "message": "Rate limit exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 30
}
```

**Best Practices:**
1. Check `X-RateLimit-Remaining` header
2. Implement exponential backoff
3. Cache responses when possible
4. Use webhooks instead of polling

---

## Error Handling

### Error Response Format

```json
{
  "status": "error",
  "errors": {
    "field_name": ["Error message"]
  },
  "message": "Human-readable error summary",
  "code": "ERROR_CODE",
  "details": {
    "additional_context": "..."
  }
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Request validation failed | 422 |
| `AUTHENTICATION_REQUIRED` | Missing auth token | 401 |
| `INVALID_TOKEN` | Token invalid or expired | 401 |
| `PERMISSION_DENIED` | Insufficient permissions | 403 |
| `RESOURCE_NOT_FOUND` | Resource doesn't exist | 404 |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 |
| `INTERNAL_ERROR` | Server error | 500 |
| `SERVICE_UNAVAILABLE` | Temporary downtime | 503 |

### Validation Errors

**Example:**
```json
{
  "status": "error",
  "errors": {
    "company_name": ["This field is required."],
    "contact_email": ["Enter a valid email address."],
    "azure_subscription_ids": ["Invalid UUID format."]
  },
  "message": "Validation failed",
  "code": "VALIDATION_ERROR"
}
```

---

## Endpoints

## Authentication Endpoints

### POST /api/v1/auth/login/

Exchange Azure AD access token for JWT token.

**Request:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "def50200abc...",
    "expires_in": 3600,
    "token_type": "Bearer",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@company.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "analyst"
    }
  }
}
```

### POST /api/v1/auth/refresh/

Refresh expired JWT token.

**Request:**
```json
{
  "refresh_token": "def50200abc..."
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600
  }
}
```

### GET /api/v1/auth/user/

Get current authenticated user profile.

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@company.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "analyst",
    "is_active": true,
    "date_joined": "2025-01-15T10:00:00Z",
    "last_login": "2025-10-02T14:30:00Z"
  }
}
```

### PUT /api/v1/auth/user/

Update current user profile.

**Request:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith"
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@company.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "analyst"
  },
  "message": "Profile updated successfully"
}
```

### POST /api/v1/auth/logout/

Logout current user (invalidate tokens).

**Response (200):**
```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```

---

## User Management Endpoints

**Note:** Requires Manager or Admin role.

### GET /api/v1/users/

List all users.

**Query Parameters:**
- `role`: Filter by role (viewer, analyst, manager, admin)
- `is_active`: Filter by active status (true, false)
- `search`: Search by name or email

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "count": 25,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@company.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "analyst",
        "is_active": true,
        "date_joined": "2025-01-15T10:00:00Z"
      }
    ]
  }
}
```

### GET /api/v1/users/{id}/

Get specific user details.

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@company.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "analyst",
    "is_active": true,
    "date_joined": "2025-01-15T10:00:00Z",
    "last_login": "2025-10-02T14:30:00Z",
    "reports_created": 45
  }
}
```

### PATCH /api/v1/users/{id}/

Update user (admin only).

**Request:**
```json
{
  "role": "manager",
  "is_active": true
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": { ... },
  "message": "User updated successfully"
}
```

---

## Client Management Endpoints

### GET /api/v1/clients/

List all clients.

**Query Parameters:**
- `status`: Filter by status (active, inactive)
- `industry`: Filter by industry
- `search`: Search by company name, email, or contact person
- `ordering`: Sort results (e.g., `-created_at`, `company_name`)
- `page`: Page number
- `page_size`: Items per page (max 100)

**Example Request:**
```bash
GET /api/v1/clients/?status=active&search=contoso&ordering=-created_at&page=1&page_size=20
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "count": 150,
    "next": "https://api.yourdomain.com/api/v1/clients/?page=2",
    "previous": null,
    "results": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "company_name": "Contoso Corporation",
        "industry": "technology",
        "status": "active",
        "contact_email": "it@contoso.com",
        "contact_phone": "+1-555-0123",
        "contact_person": "John Doe",
        "azure_subscription_ids": [
          "12345678-1234-1234-1234-123456789012"
        ],
        "notes": "Enterprise client",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-09-20T14:30:00Z",
        "reports_count": 15
      }
    ]
  }
}
```

### GET /api/v1/clients/{id}/

Get specific client details.

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "company_name": "Contoso Corporation",
    "industry": "technology",
    "status": "active",
    "contact_email": "it@contoso.com",
    "contact_phone": "+1-555-0123",
    "contact_person": "John Doe",
    "azure_subscription_ids": [
      "12345678-1234-1234-1234-123456789012",
      "87654321-4321-4321-4321-210987654321"
    ],
    "notes": "Enterprise client with quarterly reporting",
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-09-20T14:30:00Z",
    "reports_count": 15,
    "recent_reports": [
      {
        "id": "abc12345-...",
        "report_type": "executive",
        "status": "completed",
        "created_at": "2025-10-01T10:00:00Z"
      }
    ]
  }
}
```

### POST /api/v1/clients/

Create new client.

**Request:**
```json
{
  "company_name": "Fabrikam Industries",
  "industry": "manufacturing",
  "contact_email": "admin@fabrikam.com",
  "contact_phone": "+1-555-0199",
  "contact_person": "Jane Smith",
  "azure_subscription_ids": [
    "11111111-1111-1111-1111-111111111111"
  ],
  "notes": "New client onboarded Q4 2025",
  "status": "active"
}
```

**Response (201):**
```json
{
  "status": "success",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "company_name": "Fabrikam Industries",
    "industry": "manufacturing",
    "status": "active",
    "contact_email": "admin@fabrikam.com",
    "contact_phone": "+1-555-0199",
    "contact_person": "Jane Smith",
    "azure_subscription_ids": [
      "11111111-1111-1111-1111-111111111111"
    ],
    "notes": "New client onboarded Q4 2025",
    "created_at": "2025-10-02T15:00:00Z",
    "updated_at": "2025-10-02T15:00:00Z",
    "reports_count": 0
  },
  "message": "Client created successfully"
}
```

### PUT /api/v1/clients/{id}/

Update entire client (all fields required).

**Request:**
```json
{
  "company_name": "Fabrikam Industries Inc.",
  "industry": "manufacturing",
  "contact_email": "admin@fabrikam.com",
  "contact_phone": "+1-555-0199",
  "contact_person": "Jane Smith",
  "azure_subscription_ids": [
    "11111111-1111-1111-1111-111111111111",
    "22222222-2222-2222-2222-222222222222"
  ],
  "notes": "Updated subscription list",
  "status": "active"
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": { ... },
  "message": "Client updated successfully"
}
```

### PATCH /api/v1/clients/{id}/

Partially update client (only specified fields).

**Request:**
```json
{
  "contact_person": "John Williams",
  "notes": "Contact person changed"
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": { ... },
  "message": "Client updated successfully"
}
```

### DELETE /api/v1/clients/{id}/

Delete client (requires Manager or Admin role).

**Response (204):**
```
No content
```

**Note:** Deleting a client will also delete all associated reports. This action cannot be undone.

### POST /api/v1/clients/{id}/activate/

Activate an inactive client (custom action).

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "active"
  },
  "message": "Client activated successfully"
}
```

### POST /api/v1/clients/{id}/deactivate/

Deactivate a client (custom action).

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "inactive"
  },
  "message": "Client deactivated successfully"
}
```

### GET /api/v1/clients/{id}/statistics/

Get client statistics (custom action).

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "total_reports": 25,
    "completed_reports": 23,
    "failed_reports": 2,
    "total_recommendations": 450,
    "potential_savings": 125000.00,
    "last_report_date": "2025-10-01T10:00:00Z"
  }
}
```

---

## Report Management Endpoints

### GET /api/v1/reports/

List all reports.

**Query Parameters:**
- `client_id`: Filter by client UUID
- `report_type`: Filter by type (detailed, executive, cost, security, operations)
- `status`: Filter by status (pending, processing, completed, failed)
- `created_after`: Filter by creation date (ISO 8601)
- `created_before`: Filter by creation date (ISO 8601)
- `search`: Search by title or client name
- `ordering`: Sort results

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "count": 250,
    "next": "https://api.yourdomain.com/api/v1/reports/?page=2",
    "previous": null,
    "results": [
      {
        "id": "abc12345-e29b-41d4-a716-446655440000",
        "client": {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "company_name": "Contoso Corporation"
        },
        "report_type": "executive",
        "title": "Q3 2025 Azure Optimization Report",
        "status": "completed",
        "csv_file": "https://storage.../csv_uploads/2025/10/file.csv",
        "html_file": "https://storage.../reports/html/2025/10/report.html",
        "pdf_file": "https://storage.../reports/pdf/2025/10/report.pdf",
        "analysis_data": {
          "total_recommendations": 85,
          "potential_monthly_savings": 12500.00,
          "category_distribution": {
            "cost": 45,
            "security": 20,
            "reliability": 10,
            "operational_excellence": 7,
            "performance": 3
          }
        },
        "created_by": {
          "id": "user-uuid",
          "email": "analyst@company.com",
          "first_name": "John",
          "last_name": "Doe"
        },
        "created_at": "2025-10-01T10:00:00Z",
        "updated_at": "2025-10-01T10:05:30Z"
      }
    ]
  }
}
```

### GET /api/v1/reports/{id}/

Get specific report details.

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "id": "abc12345-e29b-41d4-a716-446655440000",
    "client": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "company_name": "Contoso Corporation",
      "industry": "technology"
    },
    "report_type": "executive",
    "title": "Q3 2025 Azure Optimization Report",
    "status": "completed",
    "csv_file": "https://storage.../file.csv",
    "html_file": "https://storage.../report.html",
    "pdf_file": "https://storage.../report.pdf",
    "analysis_data": {
      "total_recommendations": 85,
      "potential_monthly_savings": 12500.00,
      "estimated_annual_savings": 150000.00,
      "category_distribution": {
        "cost": 45,
        "security": 20,
        "reliability": 10,
        "operational_excellence": 7,
        "performance": 3
      },
      "business_impact_distribution": {
        "high": 25,
        "medium": 40,
        "low": 20
      },
      "advisor_score": 78
    },
    "error_message": "",
    "processing_started_at": "2025-10-01T10:00:10Z",
    "processing_completed_at": "2025-10-01T10:05:30Z",
    "created_by": {
      "id": "user-uuid",
      "email": "analyst@company.com",
      "first_name": "John",
      "last_name": "Doe"
    },
    "created_at": "2025-10-01T10:00:00Z",
    "updated_at": "2025-10-01T10:05:30Z"
  }
}
```

### POST /api/v1/reports/upload/

Upload CSV file and create report.

**Request (multipart/form-data):**
```
POST /api/v1/reports/upload/
Content-Type: multipart/form-data

------WebKitFormBoundary
Content-Disposition: form-data; name="client_id"

550e8400-e29b-41d4-a716-446655440000
------WebKitFormBoundary
Content-Disposition: form-data; name="report_type"

executive
------WebKitFormBoundary
Content-Disposition: form-data; name="title"

Q4 2025 Azure Advisor Report
------WebKitFormBoundary
Content-Disposition: form-data; name="csv_file"; filename="advisor_export.csv"
Content-Type: text/csv

[CSV file contents]
------WebKitFormBoundary--
```

**Response (201):**
```json
{
  "status": "success",
  "data": {
    "id": "new-report-uuid",
    "client": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "company_name": "Contoso Corporation"
    },
    "report_type": "executive",
    "title": "Q4 2025 Azure Advisor Report",
    "status": "processing",
    "csv_file": "https://storage.../file.csv",
    "created_at": "2025-10-02T15:30:00Z"
  },
  "message": "CSV uploaded successfully. Report generation in progress."
}
```

### POST /api/v1/reports/generate/

Trigger report generation (alternative to upload).

**Request:**
```json
{
  "client_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_type": "cost",
  "csv_file_url": "https://yourstorage.../advisor_export.csv",
  "title": "Cost Optimization Q4 2025"
}
```

**Response (201):**
```json
{
  "status": "success",
  "data": {
    "id": "new-report-uuid",
    "status": "processing",
    "estimated_completion": "2025-10-02T15:35:00Z"
  },
  "message": "Report generation started"
}
```

### GET /api/v1/reports/{id}/status/

Check report generation status.

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "id": "abc12345-e29b-41d4-a716-446655440000",
    "status": "generating",
    "progress": 75,
    "current_step": "Generating PDF",
    "estimated_completion": "2025-10-02T15:35:00Z"
  }
}
```

### GET /api/v1/reports/{id}/download/

Get download URLs for report files.

**Query Parameters:**
- `format`: Specify format (html, pdf, both) - default: both

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "html_url": "https://storage.../report.html?signature=...",
    "pdf_url": "https://storage.../report.pdf?signature=...",
    "expires_at": "2025-10-02T16:00:00Z"
  },
  "message": "Download URLs generated (valid for 1 hour)"
}
```

### DELETE /api/v1/reports/{id}/

Delete report (requires Manager or Admin role).

**Response (204):**
```
No content
```

### GET /api/v1/reports/{id}/recommendations/

Get detailed recommendations from report.

**Query Parameters:**
- `category`: Filter by category
- `business_impact`: Filter by impact (high, medium, low)
- `ordering`: Sort results

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "count": 85,
    "results": [
      {
        "id": "rec-uuid",
        "category": "cost",
        "business_impact": "high",
        "recommendation": "Right-size underutilized virtual machines",
        "description": "Your VM 'web-server-01' is running at 15% CPU utilization...",
        "resource_name": "web-server-01",
        "resource_type": "Microsoft.Compute/virtualMachines",
        "subscription_id": "12345678-1234-1234-1234-123456789012",
        "resource_group": "production-rg",
        "potential_savings": 350.00,
        "currency": "USD",
        "impact": "Reduce costs by $350/month"
      }
    ]
  }
}
```

---

## Analytics Endpoints

### GET /api/v1/analytics/dashboard/

Get complete dashboard analytics.

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "metrics": {
      "total_recommendations": {
        "value": 1250,
        "change_percent": 12.5,
        "trend": "up"
      },
      "total_potential_savings": {
        "value": 125000.00,
        "currency": "USD",
        "change_percent": 8.3,
        "trend": "up"
      },
      "active_clients": {
        "value": 45,
        "change_percent": 5.0,
        "trend": "up"
      },
      "reports_generated_this_month": {
        "value": 68,
        "change_percent": 15.2,
        "trend": "up"
      }
    },
    "category_distribution": [
      {
        "category": "cost",
        "count": 525,
        "percentage": 42.0,
        "color": "#0078D4"
      },
      {
        "category": "security",
        "count": 375,
        "percentage": 30.0,
        "color": "#D13438"
      }
    ],
    "business_impact_distribution": [
      {
        "impact": "high",
        "count": 250,
        "percentage": 20.0
      }
    ],
    "trends": {
      "last_7_days": [
        {
          "date": "2025-09-26",
          "recommendations": 150,
          "reports": 8
        }
      ]
    }
  }
}
```

### GET /api/v1/analytics/metrics/

Get dashboard metrics only.

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "total_recommendations": {
      "value": 1250,
      "change_percent": 12.5,
      "trend": "up",
      "previous_value": 1111
    },
    "total_potential_savings": {
      "value": 125000.00,
      "currency": "USD",
      "change_percent": 8.3,
      "trend": "up",
      "previous_value": 115400.00
    },
    "active_clients": {
      "value": 45,
      "change_percent": 5.0,
      "trend": "up",
      "previous_value": 43
    },
    "reports_generated_this_month": {
      "value": 68,
      "change_percent": 15.2,
      "trend": "up",
      "previous_value": 59
    }
  }
}
```

### GET /api/v1/analytics/trends/

Get trend data over time.

**Query Parameters:**
- `days`: Number of days (7, 30, or 90) - default: 30

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "period": "30_days",
    "data_points": [
      {
        "date": "2025-09-03",
        "recommendations": 125,
        "reports_generated": 8,
        "potential_savings": 12500.00
      },
      {
        "date": "2025-09-04",
        "recommendations": 140,
        "reports_generated": 10,
        "potential_savings": 14000.00
      }
    ],
    "summary": {
      "total_recommendations": 3750,
      "average_per_day": 125,
      "peak_day": "2025-09-15",
      "peak_value": 200
    }
  }
}
```

### GET /api/v1/analytics/categories/

Get category distribution.

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "categories": [
      {
        "category": "cost",
        "label": "Cost Optimization",
        "count": 525,
        "percentage": 42.0,
        "color": "#0078D4",
        "potential_savings": 75000.00
      },
      {
        "category": "security",
        "label": "Security",
        "count": 375,
        "percentage": 30.0,
        "color": "#D13438",
        "potential_savings": 0.00
      }
    ],
    "total_count": 1250
  }
}
```

### GET /api/v1/analytics/recent-activity/

Get recent report activity.

**Query Parameters:**
- `limit`: Number of items to return (default: 10, max: 50)

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "activities": [
      {
        "id": "report-uuid",
        "type": "report_completed",
        "client": {
          "id": "client-uuid",
          "company_name": "Contoso Corporation"
        },
        "report_type": "executive",
        "status": "completed",
        "timestamp": "2025-10-02T14:30:00Z",
        "user": {
          "id": "user-uuid",
          "email": "analyst@company.com",
          "first_name": "John",
          "last_name": "Doe"
        }
      }
    ]
  }
}
```

### GET /api/v1/analytics/client-performance/

Get performance metrics for a specific client.

**Query Parameters:**
- `client_id`: Client UUID (required)

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "client": {
      "id": "client-uuid",
      "company_name": "Contoso Corporation"
    },
    "metrics": {
      "total_reports": 25,
      "total_recommendations": 450,
      "potential_savings": 55000.00,
      "average_recommendations_per_report": 18,
      "reports_by_type": {
        "executive": 10,
        "detailed": 8,
        "cost": 4,
        "security": 2,
        "operations": 1
      }
    },
    "trends": {
      "recommendations_over_time": [
        {
          "month": "2025-07",
          "count": 120
        }
      ]
    }
  }
}
```

---

## Health Check Endpoint

### GET /api/health/

Check API health status (no authentication required).

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-02T15:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy",
    "storage": "healthy"
  },
  "uptime": "15 days, 3 hours, 25 minutes"
}
```

**Response (503) - Unhealthy:**
```json
{
  "status": "unhealthy",
  "version": "1.0.0",
  "timestamp": "2025-10-02T15:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "unhealthy",
    "celery": "healthy",
    "storage": "healthy"
  },
  "errors": [
    "Redis connection timeout"
  ]
}
```

---

## Webhooks

### Overview

Webhooks allow your application to receive real-time notifications when events occur in the platform.

### Configuring Webhooks

**Endpoint:** `POST /api/v1/webhooks/` (Admin only)

**Request:**
```json
{
  "url": "https://your-server.com/webhook-receiver",
  "events": ["report.completed", "report.failed"],
  "secret": "your-webhook-secret",
  "active": true
}
```

### Supported Events

| Event | Description |
|-------|-------------|
| `report.completed` | Report generation completed successfully |
| `report.failed` | Report generation failed |
| `client.created` | New client created |
| `client.updated` | Client information updated |
| `client.deleted` | Client deleted |

### Webhook Payload

**Example (report.completed):**
```json
{
  "event": "report.completed",
  "timestamp": "2025-10-02T15:30:00Z",
  "data": {
    "id": "report-uuid",
    "client_id": "client-uuid",
    "client_name": "Contoso Corporation",
    "report_type": "executive",
    "status": "completed",
    "created_at": "2025-10-02T15:25:00Z",
    "completed_at": "2025-10-02T15:30:00Z",
    "download_urls": {
      "html": "https://...",
      "pdf": "https://..."
    }
  },
  "signature": "sha256=abc123..."
}
```

### Verifying Webhook Signatures

Use the secret to verify webhook authenticity:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        f"sha256={expected_signature}",
        signature
    )
```

---

## Code Examples

### Python (requests library)

```python
import requests

# Configuration
API_BASE_URL = "https://api.yourdomain.com/api/v1"
AZURE_AD_TOKEN = "your-azure-ad-token"

# Step 1: Authenticate
def authenticate():
    response = requests.post(
        f"{API_BASE_URL}/auth/login/",
        json={"access_token": AZURE_AD_TOKEN}
    )
    response.raise_for_status()
    data = response.json()
    return data["data"]["access_token"]

# Step 2: Get JWT token
jwt_token = authenticate()

# Step 3: Set up headers
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}

# Example: List all clients
def list_clients():
    response = requests.get(
        f"{API_BASE_URL}/clients/",
        headers=headers,
        params={"status": "active", "page_size": 50}
    )
    response.raise_for_status()
    return response.json()["data"]["results"]

# Example: Create a client
def create_client(company_name, contact_email):
    response = requests.post(
        f"{API_BASE_URL}/clients/",
        headers=headers,
        json={
            "company_name": company_name,
            "contact_email": contact_email,
            "industry": "technology",
            "status": "active"
        }
    )
    response.raise_for_status()
    return response.json()["data"]

# Example: Upload CSV and generate report
def generate_report(client_id, csv_file_path, report_type):
    with open(csv_file_path, 'rb') as f:
        files = {'csv_file': f}
        data = {
            'client_id': client_id,
            'report_type': report_type,
            'title': 'Quarterly Azure Report'
        }

        # Note: For file uploads, use multipart/form-data
        upload_headers = {"Authorization": f"Bearer {jwt_token}"}

        response = requests.post(
            f"{API_BASE_URL}/reports/upload/",
            headers=upload_headers,
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()["data"]

# Example: Check report status
def check_report_status(report_id):
    response = requests.get(
        f"{API_BASE_URL}/reports/{report_id}/status/",
        headers=headers
    )
    response.raise_for_status()
    return response.json()["data"]["status"]

# Usage
if __name__ == "__main__":
    # List clients
    clients = list_clients()
    print(f"Found {len(clients)} active clients")

    # Create client
    new_client = create_client("Fabrikam", "admin@fabrikam.com")
    print(f"Created client: {new_client['id']}")

    # Generate report
    report = generate_report(
        client_id=new_client['id'],
        csv_file_path="advisor_export.csv",
        report_type="executive"
    )
    print(f"Report ID: {report['id']}, Status: {report['status']}")
```

### JavaScript/TypeScript (axios)

```typescript
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = 'https://api.yourdomain.com/api/v1';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Authentication
async function authenticate(azureToken: string): Promise<string> {
  const response = await apiClient.post('/auth/login/', {
    access_token: azureToken
  });
  return response.data.data.access_token;
}

// Set JWT token for all requests
function setAuthToken(token: string) {
  apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

// List clients
async function listClients(params?: any) {
  const response = await apiClient.get('/clients/', { params });
  return response.data.data.results;
}

// Create client
async function createClient(clientData: any) {
  const response = await apiClient.post('/clients/', clientData);
  return response.data.data;
}

// Upload CSV and generate report
async function generateReport(
  clientId: string,
  csvFile: File,
  reportType: string
) {
  const formData = new FormData();
  formData.append('client_id', clientId);
  formData.append('report_type', reportType);
  formData.append('csv_file', csvFile);
  formData.append('title', 'Quarterly Azure Report');

  const response = await apiClient.post('/reports/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });

  return response.data.data;
}

// Check report status
async function checkReportStatus(reportId: string) {
  const response = await apiClient.get(`/reports/${reportId}/status/`);
  return response.data.data.status;
}

// Get dashboard analytics
async function getDashboardAnalytics() {
  const response = await apiClient.get('/analytics/dashboard/');
  return response.data.data;
}

// Error handling
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token expired - handle re-authentication
      console.error('Authentication required');
    }
    return Promise.reject(error);
  }
);

// Usage
async function main() {
  try {
    // Authenticate
    const azureToken = 'your-azure-ad-token';
    const jwtToken = await authenticate(azureToken);
    setAuthToken(jwtToken);

    // List clients
    const clients = await listClients({ status: 'active' });
    console.log(`Found ${clients.length} active clients`);

    // Create client
    const newClient = await createClient({
      company_name: 'Fabrikam',
      contact_email: 'admin@fabrikam.com',
      industry: 'technology',
      status: 'active'
    });
    console.log(`Created client: ${newClient.id}`);

    // Generate report (assuming you have a File object)
    // const file = ... // File object from input
    // const report = await generateReport(newClient.id, file, 'executive');
    // console.log(`Report ID: ${report.id}`);

  } catch (error) {
    console.error('Error:', error);
  }
}
```

### cURL Examples

```bash
# 1. Authenticate
curl -X POST "https://api.yourdomain.com/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "YOUR_AZURE_AD_TOKEN"}'

# Save the JWT token from response
JWT_TOKEN="eyJhbGc..."

# 2. List clients
curl -X GET "https://api.yourdomain.com/api/v1/clients/?status=active&page_size=20" \
  -H "Authorization: Bearer $JWT_TOKEN"

# 3. Create client
curl -X POST "https://api.yourdomain.com/api/v1/clients/" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Fabrikam Industries",
    "contact_email": "admin@fabrikam.com",
    "industry": "manufacturing",
    "status": "active"
  }'

# 4. Upload CSV and generate report
curl -X POST "https://api.yourdomain.com/api/v1/reports/upload/" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "client_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "report_type=executive" \
  -F "title=Q4 2025 Report" \
  -F "csv_file=@advisor_export.csv"

# 5. Check report status
curl -X GET "https://api.yourdomain.com/api/v1/reports/REPORT_ID/status/" \
  -H "Authorization: Bearer $JWT_TOKEN"

# 6. Get dashboard analytics
curl -X GET "https://api.yourdomain.com/api/v1/analytics/dashboard/" \
  -H "Authorization: Bearer $JWT_TOKEN"

# 7. Download report
curl -X GET "https://api.yourdomain.com/api/v1/reports/REPORT_ID/download/?format=pdf" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## SDKs

### Official SDKs

**Python SDK:**
```bash
pip install azure-advisor-reports
```

**Node.js SDK:**
```bash
npm install @azure-advisor-reports/sdk
```

**Documentation:**
- Python SDK: https://docs.yourdomain.com/sdk/python
- Node.js SDK: https://docs.yourdomain.com/sdk/nodejs

### Community SDKs

Check GitHub for community-contributed SDKs in other languages.

---

## Changelog

### Version 1.0 (October 2, 2025)

**Initial Release:**
- Authentication endpoints (login, logout, refresh)
- Client management (CRUD operations)
- Report generation and management
- Analytics and dashboard endpoints
- Health check endpoint
- Webhook support
- Complete API documentation

**API Coverage:**
- 30+ endpoints
- 5 resource types
- Full CRUD operations
- Advanced filtering and pagination
- Real-time status updates

---

## Support

### Getting Help

- **API Documentation**: This document
- **Developer Portal**: https://developers.yourdomain.com
- **Support Email**: api-support@yourcompany.com
- **Status Page**: https://status.yourdomain.com

### Reporting Issues

Include in your bug report:
- API endpoint and method
- Request headers and body
- Response status and body
- Expected vs actual behavior
- Timestamp of the request

### Feature Requests

Submit feature requests to: features@yourcompany.com

---

**API Version:** 1.0
**Last Updated:** October 2, 2025
**Questions?** Contact api-support@yourcompany.com
