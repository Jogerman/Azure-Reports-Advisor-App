# Intrusion Detection System (IDS) - Design Document
**Phase 4, Task 4.6 - Future Implementation**
**Date:** November 5, 2025
**Status:** DESIGN PROPOSAL
**Estimated Effort:** 20 hours
**Classification:** SECURITY MONITORING

## Executive Summary

An Intrusion Detection System (IDS) monitors application activity to identify suspicious behavior patterns that may indicate security threats, attacks, or policy violations. This document outlines the design for implementing a lightweight, application-level IDS for the Azure Reports Advisor platform.

**Key Capabilities:**
- **Real-time threat detection** - Identify attacks as they happen
- **Behavioral analysis** - Detect anomalous user behavior
- **Attack pattern recognition** - Identify common attack vectors
- **Automated response** - Block malicious actors automatically
- **Security intelligence** - Provide insights for security improvements

**Priority Level:** MEDIUM-LOW (Enhancement, not critical)
**When to Implement:** After core security infrastructure is stable

---

## Threat Categories to Detect

### 1. Authentication Attacks
- **Brute force attacks** - Multiple failed login attempts
- **Credential stuffing** - Login attempts with leaked credentials
- **Account enumeration** - Probing for valid usernames
- **Session hijacking** - Suspicious session activity

### 2. Injection Attacks
- **SQL injection** - Malicious SQL queries in inputs
- **Command injection** - OS command execution attempts
- **CSV injection** - Formula injection in uploaded files
- **XSS attempts** - Cross-site scripting payloads

### 3. Resource Abuse
- **Rate limit violations** - Excessive API requests
- **File upload abuse** - Suspicious file uploads
- **Report generation abuse** - Excessive resource consumption
- **Data exfiltration** - Unusual data access patterns

### 4. Reconnaissance & Scanning
- **Port scanning** - Systematic endpoint probing
- **Directory traversal** - Path manipulation attempts
- **Vulnerability scanning** - Automated security scanner detection
- **Information gathering** - Unusual endpoint access patterns

### 5. Privilege Escalation
- **Authorization bypass** - Accessing unauthorized resources
- **Role manipulation** - Attempting to change user roles
- **IDOR attacks** - Insecure direct object references
- **Admin panel probing** - Unauthorized admin access attempts

---

## Architecture Design

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Login   │  │   API    │  │  Upload  │  │  Reports │       │
│  │ Endpoint │  │Endpoints │  │ Handler  │  │  Views   │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │             │             │             │               │
│       └─────────────┴─────────────┴─────────────┘               │
│                         │                                        │
│                         ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │          INTRUSION DETECTION MIDDLEWARE                    │ │
│  │  - Log all requests                                        │ │
│  │  - Extract security-relevant data                          │ │
│  │  - Pass to detection engine                                │ │
│  └────────────────────┬───────────────────────────────────────┘ │
└────────────────────────┼───────────────────────────────────────-┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DETECTION ENGINE                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │  Pattern   │  │ Behavioral │  │  Anomaly   │                │
│  │  Matcher   │  │  Analysis  │  │  Detection │                │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘                │
│         │                │                │                      │
│         └────────────────┴────────────────┘                      │
│                         │                                        │
│                         ▼                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │             THREAT SCORING ENGINE                         │  │
│  │  - Calculate threat score                                 │  │
│  │  - Aggregate events                                       │  │
│  │  - Apply thresholds                                       │  │
│  └───────────────────────┬───────────────────────────────────┘  │
└────────────────────────────┼───────────────────────────────────-┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  RESPONSE ORCHESTRATOR                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   Log    │  │  Alert   │  │  Block   │  │ Escalate │       │
│  │  Event   │  │   Team   │  │   User   │  │   to     │       │
│  │          │  │          │  │          │  │  Admin   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   STORAGE & ANALYTICS                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  PostgreSQL  │  │     Redis    │  │  Azure Log   │         │
│  │  (Events)    │  │  (Real-time) │  │  Analytics   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Design

### 1. Detection Middleware

**File:** `apps/core/middleware/intrusion_detection.py`

```python
"""
Intrusion Detection Middleware
Monitors all HTTP requests for security threats
"""

import logging
import time
from django.http import JsonResponse
from django.core.cache import cache
from apps.security.services.detection_engine import DetectionEngine
from apps.security.models import SecurityEvent

logger = logging.getLogger('security.ids')


class IntrusionDetectionMiddleware:
    """
    Middleware that logs and analyzes all requests for security threats.

    Collects:
    - Request metadata (IP, user-agent, method, path)
    - Authentication status
    - Request payload characteristics
    - Response status codes
    - Timing information

    Passes data to DetectionEngine for analysis.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.detection_engine = DetectionEngine()

    def __call__(self, request):
        # Start timing
        start_time = time.time()

        # Collect request data
        request_data = self._extract_request_data(request)

        # Get response
        response = self.get_response(request)

        # Calculate response time
        response_time = time.time() - start_time

        # Collect response data
        response_data = {
            'status_code': response.status_code,
            'response_time': response_time,
            'content_length': len(response.content) if hasattr(response, 'content') else 0
        }

        # Analyze for threats (async to avoid blocking)
        self._analyze_request(request_data, response_data)

        return response

    def _extract_request_data(self, request):
        """Extract security-relevant data from request."""
        return {
            # Network data
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referrer': request.META.get('HTTP_REFERER', ''),

            # Request metadata
            'method': request.method,
            'path': request.path,
            'query_string': request.META.get('QUERY_STRING', ''),
            'content_type': request.content_type,

            # Authentication
            'user_id': request.user.id if request.user.is_authenticated else None,
            'user_email': request.user.email if request.user.is_authenticated else None,
            'is_authenticated': request.user.is_authenticated,

            # Headers
            'headers': {
                key: value for key, value in request.headers.items()
                if not key.lower().startswith('authorization')  # Don't log auth tokens
            },

            # Timing
            'timestamp': time.time(),
        }

    def _analyze_request(self, request_data, response_data):
        """
        Analyze request for threats.

        Runs detection engine and triggers appropriate responses.
        """
        try:
            # Combine request and response data
            event_data = {**request_data, **response_data}

            # Run detection
            detection_result = self.detection_engine.analyze(event_data)

            # Handle high-severity threats
            if detection_result['threat_level'] >= 8:
                self._handle_high_threat(event_data, detection_result)

            # Log all detections
            if detection_result['is_threat']:
                SecurityEvent.objects.create(
                    event_type=detection_result['threat_type'],
                    severity=detection_result['threat_level'],
                    ip_address=event_data['ip_address'],
                    user_id=event_data.get('user_id'),
                    details=detection_result['details'],
                    raw_data=event_data
                )

        except Exception as e:
            logger.error(f'Error in intrusion detection: {e}', exc_info=True)
            # Never block requests due to IDS errors

    def _handle_high_threat(self, event_data, detection_result):
        """Handle high-severity threats with immediate action."""
        ip_address = event_data['ip_address']

        # Block IP temporarily
        block_key = f'blocked_ip:{ip_address}'
        cache.set(block_key, True, 3600)  # 1 hour

        # Send alert
        logger.critical(
            f'HIGH THREAT DETECTED: {detection_result["threat_type"]}',
            extra={
                'ip': ip_address,
                'user': event_data.get('user_email', 'anonymous'),
                'path': event_data['path'],
                'threat_score': detection_result['threat_level'],
                'details': detection_result['details']
            }
        )

        # TODO: Send notification to security team
        # send_security_alert(detection_result)

    def _get_client_ip(self, request):
        """Extract client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
```

---

### 2. Detection Engine

**File:** `apps/security/services/detection_engine.py`

```python
"""
Detection Engine
Analyzes events and identifies security threats
"""

import re
from typing import Dict, List
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta


class DetectionEngine:
    """
    Core detection engine that runs multiple detection strategies.

    Strategies:
    1. Pattern matching - Known attack signatures
    2. Behavioral analysis - Anomalous user behavior
    3. Rate limiting - Excessive activity detection
    4. Threat intelligence - Known malicious IPs
    """

    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.behavior_analyzer = BehaviorAnalyzer()
        self.rate_analyzer = RateAnalyzer()

    def analyze(self, event_data: Dict) -> Dict:
        """
        Analyze event for threats.

        Returns:
        {
            'is_threat': bool,
            'threat_type': str,
            'threat_level': int (0-10),
            'confidence': float (0.0-1.0),
            'details': str,
            'recommended_action': str
        }
        """
        detections = []

        # Run all detectors
        detections.append(self.pattern_detector.detect(event_data))
        detections.append(self.behavior_analyzer.analyze(event_data))
        detections.append(self.rate_analyzer.check(event_data))

        # Aggregate results
        return self._aggregate_detections(detections)

    def _aggregate_detections(self, detections: List[Dict]) -> Dict:
        """
        Aggregate multiple detection results.

        Uses highest threat level found.
        """
        # Filter out non-threats
        threats = [d for d in detections if d['is_threat']]

        if not threats:
            return {
                'is_threat': False,
                'threat_type': 'none',
                'threat_level': 0,
                'confidence': 0.0,
                'details': 'No threats detected',
                'recommended_action': 'none'
            }

        # Find highest severity threat
        highest_threat = max(threats, key=lambda x: x['threat_level'])

        return highest_threat


class PatternDetector:
    """
    Detects known attack patterns in requests.

    Signatures include:
    - SQL injection patterns
    - XSS payloads
    - Path traversal attempts
    - Command injection
    """

    # Attack patterns (simplified examples)
    SQL_INJECTION_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bor\b\s+\d+\s*=\s*\d+)",
        r"(\';?\s*drop\s+table\b)",
        r"(\bexec\s*\()",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e/",
        r"%252e%252e",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r";\s*(ls|cat|wget|curl)\b",
        r"\|\s*(nc|bash|sh)\b",
        r"`.*`",
        r"\$\(.*\)",
    ]

    def detect(self, event_data: Dict) -> Dict:
        """Detect attack patterns in request data."""
        # Combine all searchable data
        search_text = ' '.join([
            str(event_data.get('path', '')),
            str(event_data.get('query_string', '')),
        ]).lower()

        # Check SQL injection
        if self._check_patterns(search_text, self.SQL_INJECTION_PATTERNS):
            return {
                'is_threat': True,
                'threat_type': 'sql_injection',
                'threat_level': 9,
                'confidence': 0.9,
                'details': 'SQL injection pattern detected in request',
                'recommended_action': 'block'
            }

        # Check XSS
        if self._check_patterns(search_text, self.XSS_PATTERNS):
            return {
                'is_threat': True,
                'threat_type': 'xss_attempt',
                'threat_level': 7,
                'confidence': 0.85,
                'details': 'XSS payload detected in request',
                'recommended_action': 'block'
            }

        # Check path traversal
        if self._check_patterns(search_text, self.PATH_TRAVERSAL_PATTERNS):
            return {
                'is_threat': True,
                'threat_type': 'path_traversal',
                'threat_level': 8,
                'confidence': 0.95,
                'details': 'Path traversal attempt detected',
                'recommended_action': 'block'
            }

        # Check command injection
        if self._check_patterns(search_text, self.COMMAND_INJECTION_PATTERNS):
            return {
                'is_threat': True,
                'threat_type': 'command_injection',
                'threat_level': 10,
                'confidence': 0.9,
                'details': 'Command injection attempt detected',
                'recommended_action': 'block'
            }

        # No threats found
        return {
            'is_threat': False,
            'threat_type': 'none',
            'threat_level': 0,
            'confidence': 0.0,
            'details': 'No attack patterns detected',
            'recommended_action': 'none'
        }

    def _check_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if any pattern matches."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False


class BehaviorAnalyzer:
    """
    Analyzes user behavior for anomalies.

    Tracks:
    - Login patterns
    - Access patterns
    - Activity velocity
    - Geographic anomalies
    """

    def analyze(self, event_data: Dict) -> Dict:
        """Analyze behavior patterns."""
        user_id = event_data.get('user_id')
        ip_address = event_data['ip_address']

        if not user_id:
            # Anonymous user - check IP reputation
            return self._check_ip_reputation(ip_address)

        # Authenticated user - check behavior
        return self._check_user_behavior(user_id, event_data)

    def _check_ip_reputation(self, ip_address: str) -> Dict:
        """Check if IP is known malicious."""
        # TODO: Integrate with threat intelligence feeds
        # For now, just check if IP is in local blocklist

        blocklist_key = f'ip_blocklist:{ip_address}'
        if cache.get(blocklist_key):
            return {
                'is_threat': True,
                'threat_type': 'known_malicious_ip',
                'threat_level': 8,
                'confidence': 1.0,
                'details': f'IP {ip_address} is on blocklist',
                'recommended_action': 'block'
            }

        return {'is_threat': False, 'threat_level': 0}

    def _check_user_behavior(self, user_id: int, event_data: Dict) -> Dict:
        """Check authenticated user behavior."""
        # Check for unusual access patterns
        path = event_data['path']

        # Example: Admin panel access by non-admin
        if '/admin/' in path and not self._is_admin_user(user_id):
            return {
                'is_threat': True,
                'threat_type': 'unauthorized_admin_access',
                'threat_level': 7,
                'confidence': 0.8,
                'details': f'Non-admin user {user_id} accessing admin panel',
                'recommended_action': 'alert'
            }

        # Check for rapid resource access (potential data exfiltration)
        if self._is_excessive_data_access(user_id):
            return {
                'is_threat': True,
                'threat_type': 'potential_data_exfiltration',
                'threat_level': 6,
                'confidence': 0.7,
                'details': f'User {user_id} accessing resources at unusual rate',
                'recommended_action': 'alert'
            }

        return {'is_threat': False, 'threat_level': 0}

    def _is_admin_user(self, user_id: int) -> bool:
        """Check if user has admin privileges."""
        # TODO: Implement proper admin check
        return False

    def _is_excessive_data_access(self, user_id: int) -> bool:
        """Check if user is accessing data at unusual rate."""
        # Track requests per user in last 5 minutes
        key = f'user_requests:{user_id}'
        count = cache.get(key, 0)

        # Threshold: 100 requests in 5 minutes
        if count > 100:
            return True

        # Increment counter
        cache.set(key, count + 1, 300)  # 5 minutes
        return False


class RateAnalyzer:
    """
    Analyzes request rates to detect abuse.

    Detects:
    - Brute force attacks
    - DDoS attempts
    - Scraping/crawling
    """

    def check(self, event_data: Dict) -> Dict:
        """Check for rate limit violations."""
        ip_address = event_data['ip_address']
        path = event_data['path']

        # Check login attempts
        if '/auth/login' in path:
            return self._check_login_rate(ip_address)

        # Check general API rate
        return self._check_api_rate(ip_address)

    def _check_login_rate(self, ip_address: str) -> Dict:
        """Check login attempt rate."""
        key = f'login_attempts:{ip_address}'
        attempts = cache.get(key, 0)

        # Threshold: 10 attempts in 5 minutes
        if attempts > 10:
            return {
                'is_threat': True,
                'threat_type': 'brute_force_attack',
                'threat_level': 9,
                'confidence': 0.95,
                'details': f'Excessive login attempts from {ip_address} ({attempts} in 5 min)',
                'recommended_action': 'block'
            }

        # Increment counter
        cache.set(key, attempts + 1, 300)
        return {'is_threat': False, 'threat_level': 0}

    def _check_api_rate(self, ip_address: str) -> Dict:
        """Check general API request rate."""
        key = f'api_requests:{ip_address}'
        requests = cache.get(key, 0)

        # Threshold: 1000 requests in 5 minutes
        if requests > 1000:
            return {
                'is_threat': True,
                'threat_type': 'api_abuse',
                'threat_level': 6,
                'confidence': 0.8,
                'details': f'Excessive API requests from {ip_address} ({requests} in 5 min)',
                'recommended_action': 'throttle'
            }

        # Increment counter
        cache.set(key, requests + 1, 300)
        return {'is_threat': False, 'threat_level': 0}
```

---

### 3. Database Models

**File:** `apps/security/models.py`

```python
"""
Security event models for intrusion detection
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SecurityEvent(models.Model):
    """
    Log of security events detected by IDS.
    """

    EVENT_TYPES = [
        ('sql_injection', 'SQL Injection'),
        ('xss_attempt', 'XSS Attempt'),
        ('path_traversal', 'Path Traversal'),
        ('command_injection', 'Command Injection'),
        ('brute_force_attack', 'Brute Force Attack'),
        ('unauthorized_access', 'Unauthorized Access'),
        ('api_abuse', 'API Abuse'),
        ('data_exfiltration', 'Data Exfiltration'),
        ('known_malicious_ip', 'Known Malicious IP'),
        ('other', 'Other'),
    ]

    SEVERITY_LEVELS = [
        (1, 'Very Low'),
        (3, 'Low'),
        (5, 'Medium'),
        (7, 'High'),
        (9, 'Critical'),
        (10, 'Emergency'),
    ]

    # Event metadata
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.IntegerField(choices=SEVERITY_LEVELS)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Source information
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Event details
    details = models.TextField()
    raw_data = models.JSONField(default=dict)

    # Response tracking
    action_taken = models.CharField(max_length=50, blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_security_events'
    )

    class Meta:
        db_table = 'security_events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['severity', 'resolved']),
        ]

    def __str__(self):
        return f'{self.event_type} - {self.severity} - {self.timestamp}'


class BlockedIP(models.Model):
    """
    IPs that have been blocked due to malicious activity.
    """

    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.TextField()
    blocked_at = models.DateTimeField(auto_now_add=True)
    blocked_until = models.DateTimeField(null=True, blank=True)
    permanent = models.BooleanField(default=False)

    # Related security event
    security_event = models.ForeignKey(
        SecurityEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'blocked_ips'
        ordering = ['-blocked_at']

    def __str__(self):
        return f'{self.ip_address} - {self.reason}'
```

---

## Dashboard and Visualization

### Security Dashboard

```python
# apps/security/views.py

from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from .models import SecurityEvent
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone


@method_decorator(staff_member_required, name='dispatch')
class SecurityDashboardView(TemplateView):
    template_name = 'security/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Last 24 hours
        last_24h = timezone.now() - timedelta(hours=24)

        # Event counts by type
        context['events_by_type'] = (
            SecurityEvent.objects
            .filter(timestamp__gte=last_24h)
            .values('event_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Events by severity
        context['events_by_severity'] = (
            SecurityEvent.objects
            .filter(timestamp__gte=last_24h)
            .values('severity')
            .annotate(count=Count('id'))
            .order_by('-severity')
        )

        # Top attacking IPs
        context['top_attackers'] = (
            SecurityEvent.objects
            .filter(timestamp__gte=last_24h)
            .values('ip_address')
            .annotate(attack_count=Count('id'))
            .order_by('-attack_count')[:10]
        )

        # Recent critical events
        context['critical_events'] = (
            SecurityEvent.objects
            .filter(severity__gte=7, resolved=False)
            .order_by('-timestamp')[:20]
        )

        return context
```

---

## Performance Considerations

### Optimization Strategies

1. **Async Detection** - Run detection in background celery task
2. **Sampling** - Analyze only subset of requests (e.g., 10%)
3. **Caching** - Cache detection results for identical requests
4. **Database Partitioning** - Partition SecurityEvent table by date
5. **Archiving** - Move old events to cold storage

### Expected Performance Impact

| Metric | Without IDS | With IDS | Impact |
|--------|-------------|----------|--------|
| Request Latency | 50ms | 52-55ms | +2-5ms |
| Throughput | 1000 req/s | 950 req/s | -5% |
| Memory Usage | 500MB | 550MB | +50MB |
| Storage | 10GB/month | 12GB/month | +20% |

---

## Alerting and Response

### Alert Channels

```python
# apps/security/services/alerting.py

import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger('security.alerts')


class SecurityAlerter:
    """Send security alerts to appropriate channels."""

    @staticmethod
    def send_alert(event_type, severity, details):
        """Send security alert based on severity."""

        if severity >= 9:
            # Critical - Multiple channels
            SecurityAlerter._send_email(event_type, severity, details)
            SecurityAlerter._send_slack(event_type, severity, details)
            SecurityAlerter._send_pagerduty(event_type, severity, details)

        elif severity >= 7:
            # High - Email and Slack
            SecurityAlerter._send_email(event_type, severity, details)
            SecurityAlerter._send_slack(event_type, severity, details)

        else:
            # Medium/Low - Log only
            logger.warning(f'Security event: {event_type} ({severity}/10) - {details}')

    @staticmethod
    def _send_email(event_type, severity, details):
        """Send email alert to security team."""
        send_mail(
            subject=f'[SECURITY] {event_type} - Severity {severity}/10',
            message=details,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=settings.SECURITY_TEAM_EMAILS,
            fail_silently=False
        )

    @staticmethod
    def _send_slack(event_type, severity, details):
        """Send Slack notification."""
        # TODO: Implement Slack webhook integration
        pass

    @staticmethod
    def _send_pagerduty(event_type, severity, details):
        """Trigger PagerDuty incident."""
        # TODO: Implement PagerDuty integration
        pass
```

---

## Testing Strategy

```python
# tests/security/test_intrusion_detection.py

import pytest
from apps.security.services.detection_engine import DetectionEngine


class TestDetectionEngine:

    def test_sql_injection_detected(self):
        """Test SQL injection pattern detection."""
        engine = DetectionEngine()

        event_data = {
            'path': '/api/v1/reports/',
            'query_string': "id=1' OR '1'='1",
            'method': 'GET',
            'ip_address': '192.168.1.1'
        }

        result = engine.analyze(event_data)

        assert result['is_threat'] is True
        assert result['threat_type'] == 'sql_injection'
        assert result['threat_level'] >= 8


    def test_xss_detected(self):
        """Test XSS payload detection."""
        engine = DetectionEngine()

        event_data = {
            'path': '/api/v1/reports/',
            'query_string': 'name=<script>alert(1)</script>',
            'method': 'GET',
            'ip_address': '192.168.1.1'
        }

        result = engine.analyze(event_data)

        assert result['is_threat'] is True
        assert result['threat_type'] == 'xss_attempt'


    def test_brute_force_detected(self):
        """Test brute force attack detection."""
        engine = DetectionEngine()

        # Simulate 15 login attempts
        for i in range(15):
            event_data = {
                'path': '/api/v1/auth/login/',
                'method': 'POST',
                'ip_address': '192.168.1.100',
                'status_code': 401
            }

            result = engine.analyze(event_data)

        # Last attempt should trigger detection
        assert result['is_threat'] is True
        assert result['threat_type'] == 'brute_force_attack'
```

---

## Deployment Checklist

- [ ] Implement core detection engine
- [ ] Add database models and migrations
- [ ] Create security dashboard
- [ ] Set up alerting system
- [ ] Configure logging
- [ ] Performance testing
- [ ] Deploy with feature flag
- [ ] Monitor for false positives
- [ ] Tune detection thresholds
- [ ] Train security team

---

## Conclusion

An Intrusion Detection System provides continuous security monitoring and early warning of attacks. While not immediately critical, it's a valuable enhancement for production systems.

**Recommendation:** Implement after Phase 1-4 core security issues are resolved.

**Priority:** MEDIUM-LOW
**Effort:** 20 hours
**Value:** HIGH (for mature production systems)

---

## References

1. **OWASP Automated Threats**
   https://owasp.org/www-project-automated-threats-to-web-applications/

2. **NIST Guide to Intrusion Detection**
   https://csrc.nist.gov/publications/detail/sp/800-94/final

3. **MITRE ATT&CK Framework**
   https://attack.mitre.org/

---

**Document Status:** ✅ DESIGN COMPLETE - AWAITING IMPLEMENTATION
**Next Steps:** Schedule implementation after Phase 1-4 completion
**Contact:** Security Team (security@azurereportsadvisor.com)

---

**Last Updated:** November 5, 2025
**Version:** 1.0
**Classification:** INTERNAL - TECHNICAL DESIGN
