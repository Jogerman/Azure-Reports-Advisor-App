# API Request Signing - Design Document
**Phase 4, Task 4.5 - Future Implementation**
**Date:** November 5, 2025
**Status:** DESIGN PROPOSAL
**Estimated Effort:** 16 hours
**Classification:** SECURITY ENHANCEMENT

## Executive Summary

API Request Signing is an advanced security mechanism that ensures the **integrity and authenticity** of API requests. It provides protection against:
- **Request tampering** - Detection if request data is modified in transit
- **Replay attacks** - Prevention of reusing captured valid requests
- **Man-in-the-Middle (MITM) attacks** - Verification that requests come from legitimate clients
- **API abuse** - Additional layer beyond JWT authentication

This document outlines the design for implementing HMAC-based request signing for the Azure Reports Advisor API.

## Security Benefits

| Threat | Without Request Signing | With Request Signing |
|--------|------------------------|---------------------|
| Request Tampering | ⚠️ Possible | ✅ Detected |
| Replay Attacks | ⚠️ Possible | ✅ Prevented (with nonce) |
| MITM | ⚠️ Vulnerable | ✅ Mitigated |
| Unauthorized API Access | 🔒 JWT Only | 🔒 JWT + Signature |
| Data Integrity | ⚠️ Not Guaranteed | ✅ Cryptographically Verified |

**Priority Level:** MEDIUM-LOW (Enhancement, not critical)
**When to Implement:** After Phase 1-4 core security issues are resolved

---

## Architecture Overview

### High-Level Flow

```
┌─────────────┐                                ┌─────────────┐
│   Client    │                                │   Server    │
│  (Browser)  │                                │  (Django)   │
└──────┬──────┘                                └──────┬──────┘
       │                                              │
       │ 1. Prepare Request                           │
       │    - URL: /api/v1/reports/                   │
       │    - Body: {...}                             │
       │    - Timestamp: 1699123456                   │
       │    - Nonce: random_uuid                      │
       │                                              │
       │ 2. Generate Signature                        │
       │    - String to sign:                         │
       │      "POST\n/api/v1/reports/\n              │
       │       timestamp=1699123456&nonce=xyz\n       │
       │       {request_body}"                        │
       │    - HMAC-SHA256(secret, string_to_sign)    │
       │                                              │
       │ 3. Send Request with Headers                 │
       │    Authorization: Bearer {jwt}               │
       │    X-Signature: {signature}                  │
       │    X-Timestamp: {timestamp}                  │
       │    X-Nonce: {nonce}                          │
       ├─────────────────────────────────────────────>│
       │                                              │
       │                                     4. Validate
       │                                        - Check timestamp
       │                                        - Check nonce uniqueness
       │                                        - Recompute signature
       │                                        - Compare signatures
       │                                              │
       │                          5. Response (200 OK) │
       │<─────────────────────────────────────────────┤
       │                                              │
```

---

## Component Design

### 1. Client-Side Signing (Frontend)

**File:** `frontend/src/utils/requestSigning.js`

```javascript
import CryptoJS from 'crypto-js';
import { v4 as uuidv4 } from 'uuid';

class RequestSigner {
  constructor(signingKey) {
    this.signingKey = signingKey; // Derived from user session
  }

  /**
   * Sign an HTTP request
   * @param {string} method - HTTP method (GET, POST, etc.)
   * @param {string} url - Request URL path
   * @param {object} body - Request body (will be stringified)
   * @param {number} timestamp - Unix timestamp (seconds)
   * @param {string} nonce - Unique request identifier (UUID)
   * @returns {string} HMAC-SHA256 signature (hex)
   */
  signRequest(method, url, body = null, timestamp = null, nonce = null) {
    // Generate timestamp and nonce if not provided
    timestamp = timestamp || Math.floor(Date.now() / 1000);
    nonce = nonce || uuidv4();

    // Construct canonical string to sign
    const canonicalString = this._buildCanonicalString(
      method,
      url,
      body,
      timestamp,
      nonce
    );

    // Generate HMAC-SHA256 signature
    const signature = CryptoJS.HmacSHA256(canonicalString, this.signingKey)
      .toString(CryptoJS.enc.Hex);

    return {
      signature,
      timestamp,
      nonce
    };
  }

  /**
   * Build canonical string for signing
   * Format: METHOD\nURL\nQUERY_STRING\nBODY_HASH
   */
  _buildCanonicalString(method, url, body, timestamp, nonce) {
    const parts = [
      method.toUpperCase(),
      url,
      `timestamp=${timestamp}&nonce=${nonce}`,
    ];

    // Add body hash if present (for POST/PUT/PATCH)
    if (body) {
      const bodyString = typeof body === 'string' ? body : JSON.stringify(body);
      const bodyHash = CryptoJS.SHA256(bodyString).toString(CryptoJS.enc.Hex);
      parts.push(bodyHash);
    }

    return parts.join('\n');
  }

  /**
   * Verify signing key is present
   */
  static isSigningEnabled() {
    return !!sessionStorage.getItem('signing_key');
  }
}

// Usage in API client
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
});

// Request interceptor to add signature
apiClient.interceptors.request.use(config => {
  // Only sign requests if signing is enabled
  if (RequestSigner.isSigningEnabled()) {
    const signingKey = sessionStorage.getItem('signing_key');
    const signer = new RequestSigner(signingKey);

    const { signature, timestamp, nonce } = signer.signRequest(
      config.method,
      config.url,
      config.data
    );

    // Add signature headers
    config.headers['X-Signature'] = signature;
    config.headers['X-Timestamp'] = timestamp;
    config.headers['X-Nonce'] = nonce;
  }

  return config;
});

export default RequestSigner;
```

---

### 2. Server-Side Validation (Backend)

**File:** `azure_advisor_reports/apps/core/middleware/request_signing.py`

```python
"""
Request Signing Middleware
Validates HMAC-SHA256 signatures on incoming API requests
"""

import hashlib
import hmac
import time
import logging
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger('security')


class RequestSigningMiddleware:
    """
    Middleware to validate request signatures.

    Checks:
    1. Signature header is present
    2. Timestamp is within allowed window (prevents replay attacks)
    3. Nonce has not been used before (prevents replay attacks)
    4. Signature is valid (verifies request integrity)
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Configuration
        self.enabled = getattr(settings, 'REQUEST_SIGNING_ENABLED', False)
        self.timestamp_tolerance = getattr(
            settings,
            'REQUEST_SIGNING_TIMESTAMP_TOLERANCE',
            300  # 5 minutes
        )
        self.required_paths = getattr(
            settings,
            'REQUEST_SIGNING_REQUIRED_PATHS',
            ['/api/v1/reports/', '/api/v1/clients/']
        )

    def __call__(self, request):
        # Skip if signing not enabled
        if not self.enabled:
            return self.get_response(request)

        # Skip if path doesn't require signing
        if not self._requires_signing(request.path):
            return self.get_response(request)

        # Validate signature
        validation_result = self._validate_signature(request)

        if not validation_result['valid']:
            logger.warning(
                f'Invalid request signature: {validation_result["error"]}',
                extra={
                    'path': request.path,
                    'method': request.method,
                    'ip': self._get_client_ip(request),
                    'user': getattr(request.user, 'email', 'anonymous')
                }
            )

            return JsonResponse({
                'error': 'Invalid request signature',
                'detail': validation_result['error'] if settings.DEBUG else None
            }, status=401)

        # Signature valid - proceed with request
        return self.get_response(request)

    def _requires_signing(self, path):
        """Check if path requires signature validation."""
        return any(path.startswith(prefix) for prefix in self.required_paths)

    def _validate_signature(self, request):
        """
        Validate request signature.

        Returns dict with 'valid' (bool) and 'error' (str) keys.
        """
        # Extract signature headers
        signature = request.headers.get('X-Signature')
        timestamp = request.headers.get('X-Timestamp')
        nonce = request.headers.get('X-Nonce')

        # Check required headers present
        if not all([signature, timestamp, nonce]):
            return {
                'valid': False,
                'error': 'Missing signature headers'
            }

        # Validate timestamp
        try:
            timestamp = int(timestamp)
        except ValueError:
            return {
                'valid': False,
                'error': 'Invalid timestamp format'
            }

        current_time = int(time.time())
        time_diff = abs(current_time - timestamp)

        if time_diff > self.timestamp_tolerance:
            return {
                'valid': False,
                'error': f'Timestamp outside allowed window ({time_diff}s > {self.timestamp_tolerance}s)'
            }

        # Check nonce uniqueness (prevent replay attacks)
        nonce_key = f'request_nonce:{nonce}'
        if cache.get(nonce_key):
            return {
                'valid': False,
                'error': 'Nonce already used (replay attack detected)'
            }

        # Store nonce for timestamp tolerance duration
        cache.set(nonce_key, True, self.timestamp_tolerance * 2)

        # Get signing key for user
        signing_key = self._get_signing_key(request)
        if not signing_key:
            return {
                'valid': False,
                'error': 'Signing key not found'
            }

        # Reconstruct canonical string
        canonical_string = self._build_canonical_string(
            request,
            timestamp,
            nonce
        )

        # Compute expected signature
        expected_signature = hmac.new(
            signing_key.encode('utf-8'),
            canonical_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Compare signatures (constant-time comparison)
        if not hmac.compare_digest(signature, expected_signature):
            return {
                'valid': False,
                'error': 'Signature mismatch'
            }

        # All checks passed
        return {'valid': True, 'error': None}

    def _build_canonical_string(self, request, timestamp, nonce):
        """
        Build canonical string matching client-side implementation.

        Format: METHOD\nURL\nQUERY_STRING\nBODY_HASH
        """
        parts = [
            request.method.upper(),
            request.path,
            f'timestamp={timestamp}&nonce={nonce}',
        ]

        # Add body hash for POST/PUT/PATCH requests
        if request.method.upper() in ['POST', 'PUT', 'PATCH']:
            body = request.body.decode('utf-8') if request.body else ''
            body_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
            parts.append(body_hash)

        return '\n'.join(parts)

    def _get_signing_key(self, request):
        """
        Get signing key for authenticated user.

        Options:
        1. Derive from JWT token
        2. Store in user session
        3. Use per-user secret key from database
        """
        if not request.user.is_authenticated:
            return None

        # Option 1: Use user-specific signing key from profile
        # (Would be generated during login and stored in UserProfile)
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'signing_key'):
            return request.user.profile.signing_key

        # Option 2: Derive from JWT token
        # Extract JWT from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            # Use token as signing key (or derive key from token)
            return hashlib.sha256(token.encode('utf-8')).hexdigest()

        return None

    def _get_client_ip(self, request):
        """Extract client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
```

---

### 3. Settings Configuration

**File:** `azure_advisor_reports/azure_advisor_reports/settings.py`

```python
# ============================================================================
# REQUEST SIGNING CONFIGURATION
# ============================================================================

# Enable/disable request signing
REQUEST_SIGNING_ENABLED = config('REQUEST_SIGNING_ENABLED', default=False, cast=bool)

# Timestamp tolerance in seconds (prevents replay attacks)
# Requests with timestamps outside this window are rejected
REQUEST_SIGNING_TIMESTAMP_TOLERANCE = 300  # 5 minutes

# Paths that require signature validation
REQUEST_SIGNING_REQUIRED_PATHS = [
    '/api/v1/reports/',
    '/api/v1/clients/',
    '/api/v1/analytics/',
]

# Paths that are exempt from signing (even if enabled)
REQUEST_SIGNING_EXEMPT_PATHS = [
    '/api/v1/auth/login/',
    '/api/v1/auth/refresh/',
    '/api/health/',
]

# Add middleware
MIDDLEWARE = [
    # ... existing middleware ...
    'apps.core.middleware.request_signing.RequestSigningMiddleware',
]
```

---

### 4. Signing Key Management

**Option A: Per-User Signing Key (RECOMMENDED)**

```python
# apps/authentication/models.py

import secrets
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    signing_key = models.CharField(max_length=128, blank=True)

    def generate_signing_key(self):
        """Generate a new signing key for this user."""
        self.signing_key = secrets.token_urlsafe(64)
        self.save()
        return self.signing_key

    def rotate_signing_key(self):
        """Rotate signing key (security best practice)."""
        old_key = self.signing_key
        new_key = self.generate_signing_key()

        # Optionally: blacklist old key for grace period
        # SigningKeyBlacklist.objects.create(key=old_key, expires_at=...)

        return new_key


# apps/authentication/views.py

class AzureADLoginView(views.APIView):
    def post(self, request):
        # ... authentication logic ...

        # Generate or retrieve signing key
        if not user.profile.signing_key:
            user.profile.generate_signing_key()

        # Return signing key to client (only on login)
        return Response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'signing_key': user.profile.signing_key,  # Client stores this
            'user': UserSerializer(user).data
        })
```

**Option B: Derive from JWT Token**

```python
# Simpler but less flexible
def get_signing_key_from_jwt(jwt_token):
    """Derive signing key from JWT token."""
    return hashlib.sha256(jwt_token.encode('utf-8')).hexdigest()

# No need to store separately - derived on-the-fly
# Less secure if JWT is compromised
```

---

## Security Considerations

### 1. Timestamp Validation (Replay Attack Prevention)

```python
# Reject requests with old timestamps
TIMESTAMP_TOLERANCE = 300  # 5 minutes

current_time = int(time.time())
if abs(current_time - request_timestamp) > TIMESTAMP_TOLERANCE:
    raise InvalidSignature("Request timestamp too old or in future")
```

**Prevents:** Attacker capturing and replaying valid requests

### 2. Nonce Tracking (Replay Attack Prevention)

```python
# Track used nonces in Redis cache
nonce_key = f'request_nonce:{nonce}'

if cache.get(nonce_key):
    raise InvalidSignature("Nonce already used - replay attack detected")

# Store for 2x timestamp tolerance
cache.set(nonce_key, True, TIMESTAMP_TOLERANCE * 2)
```

**Prevents:** Attacker replaying same request within timestamp window

### 3. Constant-Time Comparison

```python
# ALWAYS use constant-time comparison for signatures
# Prevents timing attacks

# BAD (vulnerable to timing attacks)
if computed_signature == provided_signature:
    pass

# GOOD (constant-time comparison)
if hmac.compare_digest(computed_signature, provided_signature):
    pass
```

### 4. Signing Key Protection

- **NEVER** log signing keys
- **NEVER** expose in error messages
- **Store encrypted** in database
- **Rotate regularly** (every 90 days)
- **Use HTTPS** to protect in transit

---

## Testing Strategy

### Unit Tests

```python
# tests/security/test_request_signing.py

import pytest
from django.test import RequestFactory
from apps.core.middleware.request_signing import RequestSigningMiddleware

class TestRequestSigning:

    def test_valid_signature_accepted(self):
        """Test that valid signatures are accepted."""
        # Setup
        request = self._create_signed_request(
            method='POST',
            path='/api/v1/reports/',
            body={'title': 'Test Report'},
            signing_key='test_key'
        )

        # Execute
        response = self.middleware(request)

        # Verify
        assert response.status_code == 200


    def test_invalid_signature_rejected(self):
        """Test that invalid signatures are rejected."""
        request = self._create_signed_request(
            method='POST',
            path='/api/v1/reports/',
            body={'title': 'Test Report'},
            signing_key='wrong_key'
        )

        response = self.middleware(request)
        assert response.status_code == 401


    def test_replay_attack_prevented(self):
        """Test that nonce reuse is detected."""
        request1 = self._create_signed_request(nonce='test_nonce')
        request2 = self._create_signed_request(nonce='test_nonce')  # Same nonce

        # First request succeeds
        response1 = self.middleware(request1)
        assert response1.status_code == 200

        # Second request (replay) is rejected
        response2 = self.middleware(request2)
        assert response2.status_code == 401


    def test_old_timestamp_rejected(self):
        """Test that old timestamps are rejected."""
        old_timestamp = int(time.time()) - 600  # 10 minutes ago

        request = self._create_signed_request(timestamp=old_timestamp)

        response = self.middleware(request)
        assert response.status_code == 401
```

### Integration Tests

```python
# tests/api/test_signed_requests.py

def test_signed_report_creation():
    """Test creating report with valid signature."""
    client = SignedAPIClient(signing_key=user.profile.signing_key)

    response = client.post('/api/v1/reports/', {
        'title': 'Q3 Azure Report',
        'client_id': client_id
    })

    assert response.status_code == 201
    assert 'id' in response.json()
```

---

## Performance Considerations

### Impact Analysis

| Operation | Overhead | Mitigation |
|-----------|----------|------------|
| Signature Generation (Client) | ~1-2ms | Negligible for user experience |
| Signature Validation (Server) | ~2-3ms | Use fast HMAC implementation |
| Nonce Storage (Redis) | ~0.5ms | Use Redis for fast lookups |
| **Total Per Request** | **~3-5ms** | Acceptable overhead |

### Optimization Strategies

1. **Async Validation** - Validate signature in background
2. **Caching** - Cache user signing keys
3. **Selective Signing** - Only sign critical endpoints
4. **Redis Connection Pool** - Reuse connections

---

## Rollout Plan

### Phase 1: Implementation (Week 1-2)
- [ ] Implement client-side signing
- [ ] Implement server-side validation
- [ ] Add signing key management
- [ ] Write unit tests

### Phase 2: Testing (Week 3)
- [ ] Integration testing
- [ ] Performance testing
- [ ] Security review

### Phase 3: Gradual Deployment (Week 4+)
- [ ] Deploy with feature flag OFF
- [ ] Enable for internal users only
- [ ] Monitor performance and errors
- [ ] Gradual rollout to all users

---

## Monitoring and Alerting

### Metrics to Track

```python
# Key metrics
REQUEST_SIGNING_VALIDATIONS_TOTAL = Counter(
    'request_signing_validations_total',
    'Total signature validations',
    ['result']  # 'valid', 'invalid'
)

REQUEST_SIGNING_FAILURES = Counter(
    'request_signing_failures_total',
    'Signature validation failures',
    ['reason']  # 'invalid_signature', 'replay', 'expired'
)

REQUEST_SIGNING_LATENCY = Histogram(
    'request_signing_validation_seconds',
    'Signature validation latency'
)
```

### Alerts

- **High failure rate** (>5% invalid signatures)
- **Replay attacks detected** (nonce reuse)
- **Clock skew issues** (consistent timestamp errors)

---

## Alternatives Considered

### Alternative 1: OAuth 2.0 MAC Tokens
**Pros:** Industry standard
**Cons:** More complex, requires OAuth 2.0 setup
**Verdict:** Overkill for internal API

### Alternative 2: AWS Signature V4
**Pros:** Battle-tested by AWS
**Cons:** Complex canonicalization, requires AWS SDK
**Verdict:** Too complex for our needs

### Alternative 3: JSON Web Signatures (JWS)
**Pros:** Standard JWT extension
**Cons:** Larger payload size, requires full JWT library
**Verdict:** Good alternative if already using JWTs heavily

---

## Conclusion

Request signing provides an additional security layer for critical API endpoints. While not immediately critical (JWT authentication is sufficient for MVP), it's a valuable enhancement for production systems handling sensitive data.

**Recommendation:** Implement after Phase 1-4 core security issues are resolved.

**Priority:** MEDIUM-LOW
**Effort:** 16 hours
**Value:** HIGH (for production systems)

---

## References

1. **RFC 6234 - US Secure Hash Algorithms**
   https://tools.ietf.org/html/rfc6234

2. **HMAC: Keyed-Hashing for Message Authentication**
   https://tools.ietf.org/html/rfc2104

3. **AWS Signature Version 4**
   https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html

4. **OWASP - API Security**
   https://owasp.org/www-project-api-security/

---

**Document Status:** ✅ DESIGN COMPLETE - AWAITING IMPLEMENTATION
**Next Steps:** Schedule implementation after Phase 1-4 completion
**Contact:** Security Team (security@azurereportsadvisor.com)

---

**Last Updated:** November 5, 2025
**Version:** 1.0
**Classification:** INTERNAL - TECHNICAL DESIGN
