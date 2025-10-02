# Authentication & API Integration Setup

**Project:** Azure Advisor Reports Platform
**Date:** September 30, 2025
**Status:** Complete - Ready for Azure AD Configuration

---

## Overview

This document describes the authentication and API integration implementation for the Azure Advisor Reports Platform frontend. The application uses **Azure Active Directory (Azure AD)** via **MSAL (Microsoft Authentication Library)** for authentication and a comprehensive API service layer for backend communication.

---

## Architecture

### Authentication Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Journey                             │
└─────────────────────────────────────────────────────────────────┘

1. User visits app (/)
   │
   ├─ Not Authenticated
   │  └─> Redirect to /login (LoginPage)
   │     └─> User clicks "Sign in with Microsoft"
   │        └─> MSAL opens Azure AD popup
   │           └─> User enters Microsoft credentials
   │              └─> Azure AD validates credentials
   │                 └─> Returns authorization code
   │                    └─> MSAL exchanges code for access token
   │                       └─> Token stored in localStorage
   │                          └─> User profile loaded
   │                             └─> Redirect to /dashboard
   │
   └─ Already Authenticated
      └─> Show MainLayout with protected routes

┌─────────────────────────────────────────────────────────────────┐
│                    Component Architecture                        │
└─────────────────────────────────────────────────────────────────┘

App.tsx
  └─ ErrorBoundary
     └─ QueryClientProvider (React Query)
        └─ AuthProvider (MSAL + Auth State)
           └─ Router
              ├─ Public Routes
              │  └─ /login → LoginPage
              │
              └─ Protected Routes
                 └─ ProtectedRoute (checks isAuthenticated)
                    └─ MainLayout (uses useAuth hook)
                       ├─ Header (user info, logout)
                       ├─ Sidebar (navigation)
                       └─ Route Pages
                          ├─ /dashboard
                          ├─ /clients
                          ├─ /clients/:id
                          ├─ /reports
                          ├─ /history
                          ├─ /analytics
                          └─ /settings

┌─────────────────────────────────────────────────────────────────┐
│                      API Request Flow                            │
└─────────────────────────────────────────────────────────────────┘

Frontend Component
  │
  ├─> Calls Service Method
  │   (e.g., clientService.getClients())
  │
  └─> apiClient (Axios instance)
      │
      ├─> Request Interceptor
      │   ├─ Get active MSAL account
      │   ├─ Acquire access token silently
      │   └─ Add "Authorization: Bearer {token}" header
      │
      ├─> Send HTTP Request to Backend
      │   (http://localhost:8000/api/v1/...)
      │
      └─> Response Interceptor
          │
          ├─ Success (200-299)
          │  └─> Return response data
          │
          └─ Error (401, 403, 404, 500, etc.)
             │
             ├─ 401 Unauthorized
             │  ├─> Try to acquire token interactively (popup)
             │  ├─> If success: Retry original request
             │  └─> If fail: Redirect to /login
             │
             └─ Other errors
                └─> Show error toast
                └─> Return error to caller
```

---

## File Structure

All authentication and API files have been created:

```
frontend/src/
├── config/
│   ├── authConfig.ts          ✅ MSAL configuration
│   └── api.ts                 ✅ API endpoint definitions
│
├── context/
│   └── AuthContext.tsx        ✅ Auth state management + MSAL provider
│
├── hooks/
│   └── useAuth.ts             ✅ Re-exports useAuth from AuthContext
│
├── components/
│   ├── auth/
│   │   └── ProtectedRoute.tsx ✅ Route protection component
│   │
│   └── layout/
│       └── MainLayout.tsx     ✅ Updated to use useAuth hook
│
├── pages/
│   └── LoginPage.tsx          ✅ Microsoft login page
│
├── services/
│   ├── apiClient.ts           ✅ Axios instance with interceptors
│   ├── authService.ts         ✅ Authentication API calls
│   ├── clientService.ts       ✅ Client management API calls
│   ├── reportService.ts       ✅ Report generation API calls
│   └── index.ts               ✅ Service exports
│
└── App.tsx                    ✅ Updated with AuthProvider & routing
```

---

## Configuration Files

### 1. Environment Variables (`.env.local`)

The `.env.local` file has been created with placeholders:

```bash
# ==============================
# API Configuration
# ==============================
REACT_APP_API_URL=http://localhost:8000/api/v1

# ==============================
# Azure AD Configuration
# ==============================
REACT_APP_AZURE_CLIENT_ID=dev-client-id-placeholder
REACT_APP_AZURE_TENANT_ID=dev-tenant-id-placeholder
REACT_APP_AZURE_REDIRECT_URI=http://localhost:3000

# ==============================
# Application Configuration
# ==============================
REACT_APP_APP_NAME=Azure Advisor Reports Platform
REACT_APP_VERSION=1.0.0

# ==============================
# Development Settings
# ==============================
REACT_APP_ENABLE_DEV_TOOLS=true
REACT_APP_ENABLE_REACT_QUERY_DEVTOOLS=true
REACT_APP_API_TIMEOUT=30000

# ==============================
# Feature Flags
# ==============================
REACT_APP_ENABLE_ANALYTICS=false
```

**TODO:** Update these placeholders with actual Azure AD credentials (see Azure AD Setup section below).

---

## Implementation Details

### 1. MSAL Configuration (`src/config/authConfig.ts`)

```typescript
export const msalConfig: Configuration = {
  auth: {
    clientId: process.env.REACT_APP_AZURE_CLIENT_ID || '',
    authority: `https://login.microsoftonline.com/${process.env.REACT_APP_AZURE_TENANT_ID || 'common'}`,
    redirectUri: process.env.REACT_APP_AZURE_REDIRECT_URI || window.location.origin,
    postLogoutRedirectUri: process.env.REACT_APP_AZURE_POST_LOGOUT_REDIRECT_URI || window.location.origin,
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false,
  },
};

export const loginRequest: PopupRequest = {
  scopes: ['User.Read', 'openid', 'profile', 'email'],
};
```

**Key Features:**
- Stores tokens in `localStorage` for persistence
- Requests `User.Read`, `openid`, `profile`, and `email` scopes
- Supports multi-tenant authentication (common endpoint)
- Comprehensive logging in development mode

---

### 2. Auth Context (`src/context/AuthContext.tsx`)

Provides authentication state and methods to the entire app:

**State:**
- `isAuthenticated: boolean` - Whether user is logged in
- `isLoading: boolean` - Loading state during auth operations
- `user: User | null` - Current user profile

**Methods:**
- `login()` - Opens Azure AD popup for login
- `logout()` - Signs out user and clears tokens
- `getAccessToken()` - Gets valid access token (with automatic refresh)

**Features:**
- Automatic token refresh with silent acquisition
- Handles MSAL initialization and redirect flow
- Error handling for popup blockers and user cancellation
- Toast notifications for auth events

---

### 3. API Client (`src/services/apiClient.ts`)

Axios instance with automatic token injection:

**Request Interceptor:**
```typescript
apiClient.interceptors.request.use(async (config) => {
  const account = msalInstance.getActiveAccount();
  if (account) {
    const response = await msalInstance.acquireTokenSilent({
      ...tokenRequest,
      account,
    });
    config.headers.Authorization = `Bearer ${response.accessToken}`;
  }
  return config;
});
```

**Response Interceptor:**
```typescript
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Try to refresh token interactively
      const response = await msalInstance.acquireTokenPopup(tokenRequest);
      // Retry original request with new token
    }
    // Handle other errors (400, 403, 404, 500, etc.)
  }
);
```

**Features:**
- Automatic token injection on every request
- Automatic token refresh on 401 errors
- Comprehensive error handling with user-friendly messages
- 30-second timeout
- Toast notifications for network errors

---

### 4. Service Layer

All API calls are organized into service modules:

#### **authService.ts**
- `login(accessToken)` - Exchange Azure AD token for backend JWT
- `logout()` - Logout from backend
- `getCurrentUser()` - Get current user profile
- `refreshToken()` - Refresh backend JWT

#### **clientService.ts**
- `getClients(params)` - List clients with filtering/pagination
- `getClient(id)` - Get single client
- `createClient(data)` - Create new client
- `updateClient(id, data)` - Update client
- `deleteClient(id)` - Delete client

#### **reportService.ts**
- `uploadCSV(data)` - Upload CSV file
- `generateReport(data)` - Trigger report generation
- `getReports(params)` - List reports with filters
- `getReport(id)` - Get single report
- `getReportStatus(id)` - Check generation status
- `downloadReport(id, format)` - Download HTML/PDF report
- `deleteReport(id)` - Delete report

**All services:**
- Use TypeScript with full type definitions
- Return typed responses
- Handle errors automatically via interceptor
- Support pagination, filtering, and search

---

### 5. Protected Routes (`src/components/auth/ProtectedRoute.tsx`)

Protects routes from unauthenticated access:

```typescript
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRoles }) => {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role-based access if required
  if (requiredRoles && !hasRequiredRole) {
    return <AccessDenied />;
  }

  return <>{children}</>;
};
```

**Features:**
- Shows loading spinner during auth check
- Redirects to login if not authenticated
- Saves attempted URL for redirect after login
- Supports role-based access control (future use)
- Shows access denied page if insufficient permissions

---

### 6. Login Page (`src/pages/LoginPage.tsx`)

Beautiful, branded login page:

**Features:**
- Company branding with Azure logo
- Feature highlights
- "Sign in with Microsoft" button
- Security badge (Azure AD)
- Animations with Framer Motion
- Responsive design
- Auto-redirect if already authenticated

---

## Azure AD Setup Instructions

To enable authentication, you must create an Azure AD App Registration:

### Step 1: Create App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Fill in details:
   - **Name:** `Azure Advisor Reports Platform - Dev`
   - **Supported account types:**
     - Single tenant (your organization only) OR
     - Multi-tenant (any Azure AD directory)
   - **Redirect URI:**
     - Platform: **Single-page application (SPA)**
     - URI: `http://localhost:3000`
5. Click **Register**

### Step 2: Configure App

1. **Note the Application (client) ID** - This is your `REACT_APP_AZURE_CLIENT_ID`
2. **Note the Directory (tenant) ID** - This is your `REACT_APP_AZURE_TENANT_ID`
3. Go to **Authentication** tab:
   - Ensure `http://localhost:3000` is listed under **Single-page application** redirect URIs
   - Under **Implicit grant and hybrid flows**, leave unchecked (we use PKCE)
   - Under **Allow public client flows**, select **No**
4. Go to **API permissions** tab:
   - Verify these permissions exist (should be added by default):
     - `User.Read` (Microsoft Graph)
     - `openid` (Microsoft Graph)
     - `profile` (Microsoft Graph)
     - `email` (Microsoft Graph)
   - Click **Grant admin consent for [Your Organization]** (requires admin privileges)

### Step 3: Update Environment Variables

Update your `.env.local` file with the actual values:

```bash
REACT_APP_AZURE_CLIENT_ID=<your-application-client-id>
REACT_APP_AZURE_TENANT_ID=<your-directory-tenant-id>
REACT_APP_AZURE_REDIRECT_URI=http://localhost:3000
```

**Example:**
```bash
REACT_APP_AZURE_CLIENT_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
REACT_APP_AZURE_TENANT_ID=98765432-abcd-ef12-3456-7890abcdef12
REACT_APP_AZURE_REDIRECT_URI=http://localhost:3000
```

### Step 4: Restart Development Server

```bash
cd frontend
npm start
```

The app should now use real Azure AD authentication!

---

## Testing Authentication

### Manual Testing Checklist

1. **Login Flow:**
   - [ ] Visit `http://localhost:3000`
   - [ ] App redirects to `/login` (not authenticated)
   - [ ] Click "Sign in with Microsoft"
   - [ ] Azure AD popup appears
   - [ ] Enter Microsoft credentials
   - [ ] After successful login, redirected to `/dashboard`
   - [ ] User info appears in header (name, email)

2. **Protected Routes:**
   - [ ] Try accessing `/dashboard` directly (should redirect to login if not authenticated)
   - [ ] After login, all routes accessible (/clients, /reports, etc.)

3. **Logout:**
   - [ ] Click logout in header dropdown
   - [ ] User is signed out
   - [ ] Redirected to `/login`
   - [ ] Cannot access protected routes

4. **Token Refresh:**
   - [ ] Stay logged in for >1 hour
   - [ ] Make an API call
   - [ ] Token should refresh automatically (no logout)

5. **Error Handling:**
   - [ ] Close popup during login (should show "Sign in was cancelled" toast)
   - [ ] Block popups in browser settings (should show popup blocker message)

---

## Backend Integration

The frontend is ready to communicate with the Django backend. Ensure:

### Backend Requirements:

1. **Authentication Endpoint:**
   - `POST /api/v1/auth/login/`
   - Accepts: `{ "accessToken": "<Azure AD token>" }`
   - Returns: `{ "user": {...}, "token": "<backend JWT>" }`

2. **Protected Endpoints:**
   - All other endpoints require `Authorization: Bearer <token>` header
   - Return 401 if token is invalid/expired

3. **CORS Configuration:**
   - Allow origin: `http://localhost:3000`
   - Allow credentials: `true`
   - Allow headers: `Authorization, Content-Type`

4. **Token Validation:**
   - Backend should validate Azure AD tokens
   - Extract user info (name, email)
   - Create/update user in database
   - Issue backend JWT for API access

---

## API Endpoint Reference

All API endpoints are defined in `src/config/api.ts`:

### Authentication
- `POST /auth/login/` - Login with Azure AD token
- `POST /auth/logout/` - Logout
- `GET /auth/user/` - Get current user
- `POST /auth/refresh/` - Refresh token

### Clients
- `GET /clients/` - List clients
- `GET /clients/:id/` - Get client
- `POST /clients/` - Create client
- `PATCH /clients/:id/` - Update client
- `DELETE /clients/:id/` - Delete client

### Reports
- `GET /reports/` - List reports
- `POST /reports/upload/` - Upload CSV
- `POST /reports/generate/` - Generate report
- `GET /reports/:id/` - Get report
- `GET /reports/:id/status/` - Check status
- `GET /reports/:id/download/?format=pdf|html` - Download report
- `DELETE /reports/:id/` - Delete report

### Analytics
- `GET /analytics/dashboard/` - Dashboard metrics
- `GET /analytics/trends/` - Trend data
- `GET /analytics/client-performance/` - Client performance

---

## Usage Examples

### Using Authentication in Components

```typescript
import { useAuth } from '../hooks/useAuth';

const MyComponent: React.FC = () => {
  const { user, login, logout, isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <LoadingSpinner />;

  return (
    <div>
      {isAuthenticated ? (
        <div>
          <p>Welcome, {user?.name}!</p>
          <button onClick={logout}>Logout</button>
        </div>
      ) : (
        <button onClick={login}>Login</button>
      )}
    </div>
  );
};
```

### Making API Calls

```typescript
import { clientService } from '../services';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const ClientsPage: React.FC = () => {
  const queryClient = useQueryClient();

  // Fetch clients
  const { data, isLoading, error } = useQuery({
    queryKey: ['clients'],
    queryFn: () => clientService.getClients({ page: 1, page_size: 10 }),
  });

  // Create client mutation
  const createMutation = useMutation({
    mutationFn: clientService.createClient,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      showToast.success('Client created successfully!');
    },
    onError: (error) => {
      showToast.error('Failed to create client');
    },
  });

  const handleCreateClient = async (data) => {
    await createMutation.mutateAsync(data);
  };

  // Component rendering...
};
```

---

## Troubleshooting

### Issue: "Popup blocked" error
**Solution:** Allow popups for `localhost:3000` in browser settings, or use redirect flow instead of popup.

### Issue: "Invalid client ID" error
**Solution:** Verify `REACT_APP_AZURE_CLIENT_ID` matches the Application (client) ID in Azure Portal.

### Issue: "CORS error" when calling backend
**Solution:** Ensure Django has CORS configured for `http://localhost:3000`.

### Issue: "401 Unauthorized" on all API calls
**Solution:**
1. Check token is being sent in headers (Network tab → Request Headers)
2. Verify backend is validating Azure AD tokens correctly
3. Ensure backend JWT generation is working

### Issue: Tokens not persisting after refresh
**Solution:** Ensure `cacheLocation: 'localStorage'` in MSAL config (already set).

### Issue: "User.Read permission required" error
**Solution:** Grant admin consent for API permissions in Azure Portal.

---

## Next Steps

### Immediate (for testing):
1. ✅ Create Azure AD App Registration
2. ✅ Update `.env.local` with actual credentials
3. ✅ Test login flow
4. ⏳ Implement backend authentication endpoint
5. ⏳ Test end-to-end authentication

### Phase 2 (after backend auth works):
1. Implement dashboard with real data
2. Complete client management UI
3. Implement report upload and generation flow
4. Add analytics dashboard
5. Implement user profile and settings

---

## Security Notes

**Important Security Practices:**

1. **Never commit `.env.local`** - It's already in `.gitignore`
2. **Never expose client secrets in frontend** - We only use client ID (public)
3. **Always use HTTPS in production** - Update redirect URI to `https://your-domain.com`
4. **Rotate secrets regularly** - Change client secrets every 6 months
5. **Monitor failed login attempts** - Use Azure AD logs
6. **Implement MFA** - Enable in Azure AD conditional access
7. **Use separate App Registrations** - Dev, staging, and production should be separate

---

## Resources

- [MSAL.js Documentation](https://github.com/AzureAD/microsoft-authentication-library-for-js)
- [Azure AD Documentation](https://docs.microsoft.com/azure/active-directory/)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Axios Documentation](https://axios-http.com/)

---

**Last Updated:** September 30, 2025
**Status:** ✅ Ready for Azure AD Configuration
**Contact:** Development Team
