# Azure AD Authentication Testing Guide

**Platform:** Azure Advisor Reports Platform
**Date:** October 1, 2025
**Status:** Ready for Testing

---

## 📋 Quick Reference

### Authentication Endpoints

| Endpoint | Method | Authentication | Purpose |
|----------|--------|----------------|---------|
| `/api/auth/login/` | POST | None | Login with Azure AD token |
| `/api/auth/logout/` | POST | Required | Logout |
| `/api/auth/refresh/` | POST | None | Refresh access token |
| `/api/auth/user/` | GET | Required | Get current user |
| `/api/auth/user/` | PUT | Required | Update profile |
| `/api/auth/users/` | GET | Admin | List users |
| `/api/auth/users/{id}/` | GET | Admin | Get user details |
| `/api/auth/users/{id}/activate/` | POST | Admin | Activate user |
| `/api/auth/users/{id}/deactivate/` | POST | Admin | Deactivate user |
| `/api/auth/users/{id}/change-role/` | POST | Admin | Change user role |
| `/api/auth/users/statistics/` | GET | Admin | Get user statistics |

---

## 🚀 Setup for Testing

### 1. Prerequisites

**Services Running:**
```bash
# Check Docker containers
docker ps

# Should see:
# - azure-advisor-postgres (port 5432)
# - azure-advisor-redis (port 6379)
```

**Environment Variables:**
```bash
# Check .env file has these values
AZURE_CLIENT_ID=your-azure-ad-client-id
AZURE_CLIENT_SECRET=your-azure-ad-client-secret
AZURE_TENANT_ID=your-azure-tenant-id
SECRET_KEY=your-django-secret-key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/azure_advisor_reports
REDIS_URL=redis://localhost:6379/0
```

### 2. Start Django Server

**Option A: Via Docker**
```bash
docker-compose up backend
```

**Option B: Local (Windows PowerShell)**
```powershell
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

**Verify Server Running:**
```bash
curl http://localhost:8000/health/
```

Expected Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-01T10:00:00Z",
  "services": {
    "database": "connected",
    "redis": "connected"
  }
}
```

---

## 🧪 Testing Scenarios

### Scenario 1: Login with Azure AD (Full Integration)

**Prerequisites:**
- Frontend running with MSAL configured
- Real Azure AD app registration

**Steps:**

1. **Frontend: Get Azure AD Token**
```javascript
// In your React frontend
import { useMsal } from "@azure/msal-react";

const { instance } = useMsal();

const loginRequest = {
  scopes: ["openid", "profile", "email"]
};

const response = await instance.acquireTokenSilent(loginRequest);
const azureToken = response.accessToken;
```

2. **Backend: Exchange for JWT**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"access_token\": \"${azureToken}\"}"
```

3. **Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600,
  "token_type": "Bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john.doe",
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "analyst",
    "role_display": "Analyst",
    "job_title": "Cloud Analyst",
    "department": "IT",
    "phone_number": "",
    "created_at": "2025-10-01T10:00:00Z"
  }
}
```

4. **Save Tokens for Future Requests:**
```javascript
// In your frontend
localStorage.setItem('access_token', response.access_token);
localStorage.setItem('refresh_token', response.refresh_token);
```

---

### Scenario 2: Test Protected Endpoint

**Get Current User Profile:**

```bash
# Replace YOUR_JWT_TOKEN with actual token from login
curl -X GET http://localhost:8000/api/auth/user/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john.doe",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "role": "analyst",
  "role_display": "Analyst",
  "job_title": "Cloud Analyst",
  "department": "IT",
  "phone_number": "",
  "created_at": "2025-10-01T10:00:00Z"
}
```

**Test Without Token (Should Fail):**
```bash
curl -X GET http://localhost:8000/api/auth/user/
```

**Expected Response (401 Unauthorized):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### Scenario 3: Update User Profile

```bash
curl -X PUT http://localhost:8000/api/auth/user/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "phone_number": "+1234567890"
  }'
```

**Expected Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "jane.smith",
  "email": "jane.smith@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "full_name": "Jane Smith",
  "role": "analyst",
  "role_display": "Analyst",
  "job_title": "Cloud Analyst",
  "department": "IT",
  "phone_number": "+1234567890",
  "created_at": "2025-10-01T10:00:00Z"
}
```

---

### Scenario 4: Token Refresh

**When Access Token Expires (after 1 hour):**

```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

**Update Frontend Token:**
```javascript
localStorage.setItem('access_token', newAccessToken);
```

---

### Scenario 5: Test Expired Token

**Manually Expire Token (for testing):**
```python
# In Django shell
from apps.authentication.services import JWTService
from datetime import datetime, timedelta

# Generate token that expires immediately
user = User.objects.first()
payload = {
    'user_id': str(user.id),
    'email': user.email,
    'role': user.role,
    'exp': datetime.utcnow() - timedelta(seconds=1),  # Already expired
    'iat': datetime.utcnow(),
    'type': 'access'
}
import jwt
from django.conf import settings
expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
print(expired_token)
```

**Test with Expired Token:**
```bash
curl -X GET http://localhost:8000/api/auth/user/ \
  -H "Authorization: Bearer EXPIRED_TOKEN"
```

**Expected Response (401 Unauthorized):**
```json
{
  "detail": "Invalid token"
}
```

---

### Scenario 6: Logout

```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "message": "Successfully logged out"
}
```

**Note:** In stateless JWT system, tokens remain valid until expiration. For production, implement token blacklisting.

---

### Scenario 7: Role-Based Access Control

**Test as Viewer (read-only):**

```bash
# Login as viewer
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"access_token": "VIEWER_AZURE_TOKEN"}'

# Try to create client (should fail)
curl -X POST http://localhost:8000/api/clients/ \
  -H "Authorization: Bearer VIEWER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Company",
    "contact_email": "test@example.com"
  }'
```

**Expected Response (403 Forbidden):**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Test as Manager (can create clients):**

```bash
# Login as manager
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"access_token": "MANAGER_AZURE_TOKEN"}'

# Create client (should succeed)
curl -X POST http://localhost:8000/api/clients/ \
  -H "Authorization: Bearer MANAGER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Company",
    "contact_email": "test@example.com"
  }'
```

**Expected Response (201 Created):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "company_name": "Test Company",
  "contact_email": "test@example.com",
  ...
}
```

---

### Scenario 8: Admin User Management

**List All Users (Admin Only):**

```bash
curl -X GET http://localhost:8000/api/auth/users/ \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "admin",
      "email": "admin@example.com",
      "full_name": "Admin User",
      "role": "admin",
      "role_display": "Administrator",
      "job_title": "System Administrator",
      "department": "IT",
      "is_active": true,
      "last_login": "2025-10-01T10:00:00Z",
      "created_at": "2025-09-01T10:00:00Z"
    },
    ...
  ]
}
```

**Filter Users by Role:**
```bash
curl -X GET "http://localhost:8000/api/auth/users/?role=analyst" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

**Search Users:**
```bash
curl -X GET "http://localhost:8000/api/auth/users/?search=john" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

**Change User Role:**
```bash
curl -X POST http://localhost:8000/api/auth/users/{user_id}/change-role/ \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "manager"}'
```

**Deactivate User:**
```bash
curl -X POST http://localhost:8000/api/auth/users/{user_id}/deactivate/ \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

**Get User Statistics:**
```bash
curl -X GET http://localhost:8000/api/auth/users/statistics/ \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "total_users": 10,
  "active_users": 8,
  "inactive_users": 2,
  "users_by_role": {
    "viewer": 2,
    "analyst": 5,
    "manager": 2,
    "admin": 1
  }
}
```

---

## 🧰 Testing Tools

### 1. Postman Collection

**Create Collection with these requests:**

**Environment Variables:**
```json
{
  "base_url": "http://localhost:8000",
  "access_token": "{{access_token}}",
  "refresh_token": "{{refresh_token}}"
}
```

**Pre-request Script for Protected Endpoints:**
```javascript
pm.request.headers.add({
  key: 'Authorization',
  value: 'Bearer ' + pm.environment.get('access_token')
});
```

### 2. Python Testing Script

**File:** `test_auth.py`
```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_login(azure_token):
    """Test login with Azure AD token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        json={"access_token": azure_token}
    )
    print(f"Login Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Access Token: {data['access_token'][:50]}...")
        print(f"User: {data['user']['email']}")
        return data['access_token'], data['refresh_token']
    else:
        print(f"Error: {response.json()}")
        return None, None

def test_protected_endpoint(access_token):
    """Test protected endpoint"""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/api/auth/user/", headers=headers)
    print(f"Profile Status: {response.status_code}")
    if response.status_code == 200:
        print(f"User Data: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.json()}")

def test_refresh_token(refresh_token):
    """Test token refresh"""
    response = requests.post(
        f"{BASE_URL}/api/auth/refresh/",
        json={"refresh_token": refresh_token}
    )
    print(f"Refresh Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"New Access Token: {data['access_token'][:50]}...")
        return data['access_token']
    else:
        print(f"Error: {response.json()}")
        return None

def test_logout(access_token):
    """Test logout"""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(f"{BASE_URL}/api/auth/logout/", headers=headers)
    print(f"Logout Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    # Replace with real Azure AD token
    azure_token = "YOUR_AZURE_AD_TOKEN"

    print("=" * 50)
    print("Testing Authentication Flow")
    print("=" * 50)

    # Test login
    print("\n1. Testing Login...")
    access_token, refresh_token = test_login(azure_token)

    if access_token:
        # Test protected endpoint
        print("\n2. Testing Protected Endpoint...")
        test_protected_endpoint(access_token)

        # Test token refresh
        print("\n3. Testing Token Refresh...")
        new_access_token = test_refresh_token(refresh_token)

        # Test logout
        print("\n4. Testing Logout...")
        test_logout(new_access_token or access_token)
```

**Run:**
```bash
python test_auth.py
```

---

## 🔍 Debugging

### Check Django Logs

```bash
# If running via Docker
docker-compose logs -f backend

# If running locally
# Logs printed to terminal
```

### Common Issues

#### 1. "Invalid Azure AD token"

**Cause:** Azure token validation failed

**Debug:**
```python
# In Django shell
from apps.authentication.services import AzureADService

service = AzureADService()
is_valid, user_info = service.validate_token("YOUR_AZURE_TOKEN")
print(f"Valid: {is_valid}")
print(f"User Info: {user_info}")
```

**Solution:**
- Ensure Azure AD app is properly configured
- Check CLIENT_ID, TENANT_ID in .env
- Verify token is not expired
- Ensure correct scopes requested

#### 2. "JWT token has expired"

**Cause:** Access token expired (1 hour lifetime)

**Solution:**
- Use refresh token to get new access token
- Implement automatic token refresh in frontend

#### 3. "User does not have permission"

**Cause:** Role-based access control blocking request

**Debug:**
```python
# In Django shell
from apps.authentication.services import RoleService
from apps.authentication.models import User

user = User.objects.get(email="user@example.com")
print(f"User Role: {user.role}")
print(f"Can create clients: {RoleService.can_create_clients(user)}")
print(f"Can manage users: {RoleService.can_manage_users(user)}")
```

**Solution:**
- Verify user role is correct
- Check permission requirements for endpoint
- Admin can change user role if needed

#### 4. "Database connection refused"

**Cause:** PostgreSQL container not running

**Solution:**
```bash
docker-compose up -d postgres
docker-compose ps  # Check status
```

---

## 📊 Test Checklist

### Functional Tests

- [ ] Login with valid Azure AD token succeeds
- [ ] Login with invalid Azure AD token fails
- [ ] JWT token is returned on successful login
- [ ] Protected endpoint requires authentication
- [ ] Protected endpoint works with valid JWT
- [ ] Protected endpoint fails with invalid JWT
- [ ] Protected endpoint fails with expired JWT
- [ ] Token refresh works with valid refresh token
- [ ] Token refresh fails with invalid refresh token
- [ ] Logout succeeds
- [ ] User profile retrieval works
- [ ] User profile update works
- [ ] Role-based permissions enforced

### Permission Tests

- [ ] Viewer can read but not create
- [ ] Analyst can create reports
- [ ] Manager can create clients
- [ ] Admin can manage users
- [ ] Users cannot modify their own role
- [ ] Users cannot deactivate themselves
- [ ] Admin user management endpoints work

### Security Tests

- [ ] Tokens expire after configured time
- [ ] Token type validation works (access vs refresh)
- [ ] Invalid tokens are rejected
- [ ] Token payload is validated
- [ ] Azure AD signature verification works
- [ ] Rate limiting works (if implemented)

---

## 📝 Test Results Template

```markdown
## Test Results - [Date]

**Tester:** [Name]
**Environment:** Development / Staging / Production
**Browser/Tool:** Postman / curl / Python script

### Test Results

| Test | Status | Notes |
|------|--------|-------|
| Login with Azure AD | ✅ Pass | |
| Get current user | ✅ Pass | |
| Update profile | ✅ Pass | |
| Token refresh | ✅ Pass | |
| Logout | ✅ Pass | |
| Expired token rejection | ✅ Pass | |
| Viewer permissions | ✅ Pass | Cannot create clients |
| Manager permissions | ✅ Pass | Can create clients |
| Admin user management | ✅ Pass | All actions work |

### Issues Found

1. **Issue:** [Description]
   - **Severity:** High / Medium / Low
   - **Steps to reproduce:** [Steps]
   - **Expected:** [What should happen]
   - **Actual:** [What happened]

### Notes

[Any additional observations or comments]
```

---

## 🎉 Success Criteria

Authentication system is ready when:

- ✅ All functional tests pass
- ✅ All permission tests pass
- ✅ All security tests pass
- ✅ No critical bugs found
- ✅ Documentation is complete
- ✅ Frontend integration works

---

**Document Version:** 1.0
**Last Updated:** October 1, 2025
**Status:** Ready for Testing
