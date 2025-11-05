# Database Query Auditing - Design Document
**Phase 4, Task 4.7 - Future Implementation**
**Date:** November 5, 2025
**Status:** DESIGN PROPOSAL
**Estimated Effort:** 12 hours
**Classification:** SECURITY & COMPLIANCE

## Executive Summary

Database Query Auditing provides comprehensive logging and monitoring of all database operations, enabling:
- **Compliance** - Meet regulatory requirements (GDPR, HIPAA, SOX, PCI DSS)
- **Security monitoring** - Detect unauthorized data access
- **Performance optimization** - Identify slow and problematic queries
- **Forensic analysis** - Investigate security incidents
- **Change tracking** - Maintain audit trail of data modifications

This document outlines the design for implementing comprehensive database query auditing for the Azure Reports Advisor application.

**Priority Level:** MEDIUM (Compliance-driven)
**When to Implement:** Required for compliance certification

---

## Compliance Requirements

### GDPR (General Data Protection Regulation)
- **Article 30** - Records of processing activities
- **Article 32** - Security of processing (audit logs)
- **Article 33** - Breach notification (requires audit trail)

### HIPAA (Health Insurance Portability and Accountability Act)
- **164.308(a)(1)(ii)(D)** - Information system activity review
- **164.312(b)** - Audit controls

### SOX (Sarbanes-Oxley Act)
- **Section 404** - Internal controls assessment
- Requires database access audit trail

### PCI DSS (Payment Card Industry Data Security Standard)
- **Requirement 10** - Track and monitor all access to network resources and cardholder data
- **10.2** - Audit trail for all system components
- **10.3** - Record audit trail entries

---

## Audit Scope

### Events to Audit

| Event Category | Priority | Examples |
|---------------|----------|----------|
| **Authentication** | CRITICAL | Login, logout, failed login attempts |
| **Authorization** | CRITICAL | Role changes, permission grants/revokes |
| **Data Access** | HIGH | SELECT queries on sensitive tables |
| **Data Modification** | CRITICAL | INSERT, UPDATE, DELETE operations |
| **Schema Changes** | CRITICAL | ALTER TABLE, CREATE/DROP operations |
| **Administrative** | CRITICAL | User creation, privilege escalation |
| **Errors & Exceptions** | HIGH | Failed queries, constraint violations |
| **Performance** | MEDIUM | Slow queries, resource exhaustion |

### Sensitive Tables to Monitor

```python
# High-priority tables requiring full audit
AUDIT_PRIORITY_TABLES = {
    'authentication_user': 'CRITICAL',  # User accounts
    'authentication_tokenblacklist': 'HIGH',  # Revoked tokens
    'clients_client': 'HIGH',  # Client information
    'reports_report': 'HIGH',  # Generated reports
    'reports_csvupload': 'MEDIUM',  # Uploaded data
}
```

---

## Architecture Design

### Component Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Django   │  │   Views    │  │   Admin    │            │
│  │    ORM     │  │            │  │   Panel    │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
│        │                │                │                    │
│        └────────────────┴────────────────┘                    │
│                         │                                     │
│                         ▼                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          DATABASE QUERY MIDDLEWARE                    │   │
│  │  - Intercept all queries                              │   │
│  │  - Extract query metadata                             │   │
│  │  - Classify query type                                │   │
│  │  - Pass to audit logger                               │   │
│  └─────────────────────┬────────────────────────────────┘   │
└────────────────────────┼────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    AUDIT PROCESSING                           │
│  ┌───────────────────┐  ┌───────────────────┐               │
│  │  Query Analyzer   │  │  Sensitivity      │               │
│  │  - Parse SQL      │  │  Classifier       │               │
│  │  - Extract tables │  │  - Identify PII   │               │
│  │  - Identify ops   │  │  - Risk scoring   │               │
│  └──────┬────────────┘  └──────┬────────────┘               │
│         │                       │                             │
│         └───────────┬───────────┘                             │
│                     │                                         │
│                     ▼                                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │             AUDIT LOG WRITER                           │ │
│  │  - Format audit record                                 │ │
│  │  - Apply retention policy                              │ │
│  │  - Write to audit database                             │ │
│  └────────────────────┬───────────────────────────────────┘ │
└────────────────────────┼───────────────────────────────────-┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                   AUDIT STORAGE                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    Azure     │  │    SIEM      │      │
│  │ Audit Table  │  │ Log Analytics│  │ Integration  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Design

### 1. Django Middleware for Query Auditing

**File:** `apps/core/middleware/query_auditing.py`

```python
"""
Database Query Auditing Middleware
Logs all database queries for compliance and security monitoring
"""

import logging
import time
from django.db import connection
from django.conf import settings
from apps.audit.models import QueryAuditLog
from apps.audit.services.query_analyzer import QueryAnalyzer

logger = logging.getLogger('audit.database')


class QueryAuditingMiddleware:
    """
    Middleware that audits all database queries.

    For each request, captures:
    - All SQL queries executed
    - Query execution time
    - User context
    - Result set size
    - Affected tables
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'DATABASE_AUDITING_ENABLED', False)
        self.query_analyzer = QueryAnalyzer()

    def __call__(self, request):
        if not self.enabled:
            return self.get_response(request)

        # Store request context for query logging
        request._audit_context = {
            'user_id': request.user.id if request.user.is_authenticated else None,
            'user_email': request.user.email if request.user.is_authenticated else None,
            'ip_address': self._get_client_ip(request),
            'path': request.path,
            'method': request.method,
        }

        # Get initial query count
        initial_queries = len(connection.queries)

        # Execute request
        response = self.get_response(request)

        # Audit queries executed during request
        if settings.DEBUG or hasattr(connection, 'queries'):
            queries = connection.queries[initial_queries:]
            self._audit_queries(queries, request._audit_context)

        return response

    def _audit_queries(self, queries, context):
        """
        Audit a list of queries.

        Filters out non-critical queries and logs important ones.
        """
        for query_dict in queries:
            sql = query_dict['sql']
            execution_time = float(query_dict['time'])

            # Analyze query
            analysis = self.query_analyzer.analyze(sql)

            # Skip if not audit-worthy
            if not analysis['requires_audit']:
                continue

            # Create audit log entry
            try:
                QueryAuditLog.objects.create(
                    # Query information
                    sql_query=sql,
                    query_type=analysis['query_type'],
                    tables_accessed=analysis['tables'],
                    rows_affected=analysis.get('rows_affected', 0),
                    execution_time=execution_time,

                    # User context
                    user_id=context['user_id'],
                    user_email=context['user_email'],
                    ip_address=context['ip_address'],

                    # Request context
                    request_path=context['path'],
                    request_method=context['method'],

                    # Classification
                    is_sensitive=analysis['is_sensitive'],
                    risk_level=analysis['risk_level'],
                )
            except Exception as e:
                logger.error(f'Failed to create audit log: {e}', exc_info=True)
                # Never fail request due to audit logging errors

    def _get_client_ip(self, request):
        """Extract client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
```

---

### 2. Query Analyzer Service

**File:** `apps/audit/services/query_analyzer.py`

```python
"""
SQL Query Analysis Service
Parses and classifies SQL queries for auditing
"""

import re
from typing import Dict, List


class QueryAnalyzer:
    """
    Analyzes SQL queries to determine:
    - Query type (SELECT, INSERT, UPDATE, DELETE, etc.)
    - Tables accessed
    - Whether query touches sensitive data
    - Risk level
    """

    # Sensitive tables that require audit
    SENSITIVE_TABLES = {
        'authentication_user',
        'authentication_tokenblacklist',
        'clients_client',
        'reports_report',
        'reports_csvupload',
    }

    # Queries that always require audit
    CRITICAL_QUERY_TYPES = {
        'INSERT', 'UPDATE', 'DELETE',
        'DROP', 'CREATE', 'ALTER',
        'GRANT', 'REVOKE'
    }

    def analyze(self, sql: str) -> Dict:
        """
        Analyze SQL query and return classification.

        Returns:
        {
            'query_type': str,
            'tables': List[str],
            'is_sensitive': bool,
            'requires_audit': bool,
            'risk_level': int (0-10),
            'rows_affected': int (if available)
        }
        """
        # Normalize SQL
        sql = sql.strip()

        # Determine query type
        query_type = self._extract_query_type(sql)

        # Extract tables
        tables = self._extract_tables(sql)

        # Check sensitivity
        is_sensitive = self._is_sensitive_query(tables, query_type)

        # Calculate risk level
        risk_level = self._calculate_risk_level(query_type, tables)

        # Determine if audit required
        requires_audit = (
            query_type in self.CRITICAL_QUERY_TYPES or
            is_sensitive or
            risk_level >= 5
        )

        return {
            'query_type': query_type,
            'tables': tables,
            'is_sensitive': is_sensitive,
            'requires_audit': requires_audit,
            'risk_level': risk_level,
        }

    def _extract_query_type(self, sql: str) -> str:
        """Extract query type (SELECT, INSERT, etc.)."""
        # Match first SQL keyword
        match = re.match(r'^\s*(\w+)', sql, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return 'UNKNOWN'

    def _extract_tables(self, sql: str) -> List[str]:
        """
        Extract table names from SQL query.

        This is a simplified implementation. For production,
        consider using a proper SQL parser like sqlparse.
        """
        tables = []

        # Pattern for FROM clause
        from_pattern = r'\bFROM\s+["`]?(\w+)["`]?'
        tables.extend(re.findall(from_pattern, sql, re.IGNORECASE))

        # Pattern for JOIN clauses
        join_pattern = r'\bJOIN\s+["`]?(\w+)["`]?'
        tables.extend(re.findall(join_pattern, sql, re.IGNORECASE))

        # Pattern for INTO clause (INSERT)
        into_pattern = r'\bINTO\s+["`]?(\w+)["`]?'
        tables.extend(re.findall(into_pattern, sql, re.IGNORECASE))

        # Pattern for UPDATE
        update_pattern = r'^\s*UPDATE\s+["`]?(\w+)["`]?'
        tables.extend(re.findall(update_pattern, sql, re.IGNORECASE))

        # Remove duplicates and return
        return list(set(tables))

    def _is_sensitive_query(self, tables: List[str], query_type: str) -> bool:
        """Determine if query accesses sensitive data."""
        # Check if any table is in sensitive list
        for table in tables:
            if table.lower() in self.SENSITIVE_TABLES:
                return True

        # Modification queries are always sensitive
        if query_type in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER']:
            return True

        return False

    def _calculate_risk_level(self, query_type: str, tables: List[str]) -> int:
        """
        Calculate risk level (0-10).

        Factors:
        - Query type (DDL/DML more risky)
        - Table sensitivity
        - Number of tables
        """
        risk = 0

        # Base risk by query type
        if query_type in ['DROP', 'TRUNCATE']:
            risk += 10  # Maximum risk
        elif query_type in ['DELETE', 'ALTER']:
            risk += 7
        elif query_type in ['UPDATE', 'INSERT']:
            risk += 5
        elif query_type == 'SELECT':
            risk += 2

        # Add risk for sensitive tables
        sensitive_count = sum(1 for t in tables if t.lower() in self.SENSITIVE_TABLES)
        risk += sensitive_count * 2

        # Cap at 10
        return min(risk, 10)
```

---

### 3. Audit Log Model

**File:** `apps/audit/models.py`

```python
"""
Database audit log models
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField

User = get_user_model()


class QueryAuditLog(models.Model):
    """
    Comprehensive audit log for database queries.

    Stores:
    - Query details (SQL, type, tables)
    - User context (who executed it)
    - Request context (from where)
    - Performance metrics
    - Classification (sensitivity, risk)
    """

    QUERY_TYPES = [
        ('SELECT', 'Select'),
        ('INSERT', 'Insert'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('CREATE', 'Create'),
        ('ALTER', 'Alter'),
        ('DROP', 'Drop'),
        ('GRANT', 'Grant'),
        ('REVOKE', 'Revoke'),
        ('OTHER', 'Other'),
    ]

    RISK_LEVELS = [
        (0, 'None'),
        (2, 'Very Low'),
        (4, 'Low'),
        (6, 'Medium'),
        (8, 'High'),
        (10, 'Critical'),
    ]

    # Query information
    sql_query = models.TextField()
    query_type = models.CharField(max_length=20, choices=QUERY_TYPES, db_index=True)
    tables_accessed = ArrayField(models.CharField(max_length=100), default=list)
    rows_affected = models.IntegerField(default=0)
    execution_time = models.FloatField(help_text='Execution time in seconds')

    # User context
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True
    )
    user_email = models.EmailField(blank=True)
    ip_address = models.GenericIPAddressField()

    # Request context
    request_path = models.CharField(max_length=500)
    request_method = models.CharField(max_length=10)

    # Classification
    is_sensitive = models.BooleanField(default=False, db_index=True)
    risk_level = models.IntegerField(choices=RISK_LEVELS, db_index=True)

    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    session_id = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'audit_query_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['query_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['is_sensitive', 'risk_level']),
            models.Index(fields=['tables_accessed'], name='idx_tables_gin'),
        ]

    def __str__(self):
        return f'{self.query_type} by {self.user_email or "Anonymous"} at {self.timestamp}'


class DataAccessLog(models.Model):
    """
    Simplified access log for specific sensitive data access.

    Focused on user-initiated data views (reports, client data, etc.)
    rather than low-level queries.
    """

    ACCESS_TYPES = [
        ('VIEW', 'View'),
        ('DOWNLOAD', 'Download'),
        ('EXPORT', 'Export'),
        ('PRINT', 'Print'),
    ]

    # What was accessed
    resource_type = models.CharField(max_length=50)  # 'report', 'client', 'user'
    resource_id = models.IntegerField()
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)

    # Who accessed it
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    ip_address = models.GenericIPAddressField()

    # When and where
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user_agent = models.TextField(blank=True)

    # Additional context
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'audit_data_access_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['user', 'timestamp']),
        ]

    def __str__(self):
        return f'{self.user.email} {self.access_type} {self.resource_type}:{self.resource_id}'
```

---

### 4. Settings Configuration

**File:** `azure_advisor_reports/settings.py`

```python
# ============================================================================
# DATABASE QUERY AUDITING CONFIGURATION
# ============================================================================

# Enable/disable query auditing
DATABASE_AUDITING_ENABLED = config('DATABASE_AUDITING_ENABLED', default=False, cast=bool)

# Audit retention period (days)
AUDIT_RETENTION_DAYS = 365  # 1 year (adjust based on compliance requirements)

# Archive old audits instead of deleting
AUDIT_ARCHIVE_ENABLED = True
AUDIT_ARCHIVE_AFTER_DAYS = 90  # Move to archive after 90 days

# Performance settings
AUDIT_ASYNC_ENABLED = True  # Write audit logs asynchronously
AUDIT_BATCH_SIZE = 100  # Batch audit writes for performance

# Excluded queries (system/health checks)
AUDIT_EXCLUDED_PATHS = [
    '/health/',
    '/api/health/',
    '/admin/jsi18n/',
]

# Excluded query patterns
AUDIT_EXCLUDED_QUERY_PATTERNS = [
    r'^SELECT.*django_session',  # Session queries
    r'^SELECT.*django_migrations',  # Migration tracking
]

# Alert thresholds
AUDIT_ALERT_ON_HIGH_RISK = True  # Alert on risk_level >= 8
AUDIT_ALERT_ON_BULK_DELETE = True  # Alert on DELETE with rows_affected > 100

# Logging configuration
LOGGING = {
    # ... existing config ...
    'loggers': {
        'audit.database': {
            'handlers': ['audit_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'handlers': {
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'audit_database.log'),
            'maxBytes': 52428800,  # 50MB
            'backupCount': 10,
            'formatter': 'detailed',
        },
    },
}
```

---

### 5. Audit Report Views

**File:** `apps/audit/views.py`

```python
"""
Audit report views for security team
"""

from django.views.generic import ListView, DetailView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.db.models import Count, Q
from datetime import timedelta
from django.utils import timezone
from .models import QueryAuditLog, DataAccessLog


@method_decorator(staff_member_required, name='dispatch')
class AuditDashboardView(ListView):
    """Dashboard showing audit statistics."""

    template_name = 'audit/dashboard.html'
    model = QueryAuditLog

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Last 30 days
        last_30_days = timezone.now() - timedelta(days=30)

        # Query statistics
        context['total_queries'] = QueryAuditLog.objects.filter(
            timestamp__gte=last_30_days
        ).count()

        context['sensitive_queries'] = QueryAuditLog.objects.filter(
            timestamp__gte=last_30_days,
            is_sensitive=True
        ).count()

        context['high_risk_queries'] = QueryAuditLog.objects.filter(
            timestamp__gte=last_30_days,
            risk_level__gte=8
        ).count()

        # Most active users
        context['top_users'] = (
            QueryAuditLog.objects
            .filter(timestamp__gte=last_30_days)
            .values('user_email')
            .annotate(query_count=Count('id'))
            .order_by('-query_count')[:10]
        )

        # Most accessed tables
        context['top_tables'] = (
            QueryAuditLog.objects
            .filter(timestamp__gte=last_30_days)
            .values('tables_accessed')
            .annotate(access_count=Count('id'))
            .order_by('-access_count')[:10]
        )

        # Recent high-risk queries
        context['recent_high_risk'] = (
            QueryAuditLog.objects
            .filter(risk_level__gte=8)
            .order_by('-timestamp')[:20]
        )

        return context


@method_decorator(staff_member_required, name='dispatch')
class UserAuditTrailView(ListView):
    """View all queries executed by a specific user."""

    template_name = 'audit/user_trail.html'
    model = QueryAuditLog
    paginate_by = 50

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return QueryAuditLog.objects.filter(user_id=user_id).order_by('-timestamp')


@method_decorator(staff_member_required, name='dispatch')
class SensitiveDataAccessView(ListView):
    """View all access to sensitive data."""

    template_name = 'audit/sensitive_access.html'
    model = DataAccessLog
    paginate_by = 50

    def get_queryset(self):
        return DataAccessLog.objects.all().order_by('-timestamp')
```

---

## Compliance Reports

### GDPR Article 30 Report

```python
# apps/audit/reports/gdpr_article_30.py

def generate_gdpr_article_30_report(start_date, end_date):
    """
    Generate GDPR Article 30 compliance report.

    Records of processing activities.
    """

    report = {
        'period': {
            'start': start_date,
            'end': end_date,
        },
        'processing_activities': []
    }

    # Personal data access
    personal_data_queries = QueryAuditLog.objects.filter(
        timestamp__range=(start_date, end_date),
        tables_accessed__contains=['authentication_user']
    )

    report['processing_activities'].append({
        'activity': 'User Authentication and Access Control',
        'purpose': 'User management and authentication',
        'data_categories': ['Email', 'Name', 'Role'],
        'recipients': 'Internal application',
        'retention_period': '365 days',
        'security_measures': 'Encryption at rest, audit logging',
        'access_count': personal_data_queries.count(),
    })

    # Client data access
    client_data_queries = QueryAuditLog.objects.filter(
        timestamp__range=(start_date, end_date),
        tables_accessed__contains=['clients_client']
    )

    report['processing_activities'].append({
        'activity': 'Client Data Management',
        'purpose': 'Azure advisory services',
        'data_categories': ['Company name', 'Contact information'],
        'recipients': 'Authorized users',
        'retention_period': '365 days',
        'security_measures': 'Role-based access control, audit logging',
        'access_count': client_data_queries.count(),
    })

    return report
```

---

## Performance Optimization

### Async Audit Writing

```python
# apps/audit/tasks.py

from celery import shared_task
from .models import QueryAuditLog


@shared_task
def write_audit_log_async(audit_data):
    """
    Write audit log asynchronously to avoid blocking requests.

    Usage:
    write_audit_log_async.delay({
        'sql_query': sql,
        'query_type': 'SELECT',
        # ... other fields
    })
    """
    try:
        QueryAuditLog.objects.create(**audit_data)
    except Exception as e:
        logger.error(f'Failed to write audit log: {e}', exc_info=True)


@shared_task
def cleanup_old_audit_logs():
    """
    Celery task to cleanup old audit logs based on retention policy.

    Schedule: Run daily
    """
    from django.conf import settings
    from datetime import timedelta
    from django.utils import timezone

    retention_days = settings.AUDIT_RETENTION_DAYS
    cutoff_date = timezone.now() - timedelta(days=retention_days)

    deleted_count = QueryAuditLog.objects.filter(
        timestamp__lt=cutoff_date
    ).delete()[0]

    logger.info(f'Cleaned up {deleted_count} old audit log entries')

    return deleted_count
```

### Database Partitioning

```sql
-- Partition audit table by month for better performance
-- PostgreSQL 11+

CREATE TABLE audit_query_logs_2025_11 PARTITION OF audit_query_logs
FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE audit_query_logs_2025_12 PARTITION OF audit_query_logs
FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- Automatically create partitions with pg_partman extension
```

---

## Security Considerations

### 1. Audit Log Integrity

```python
# Prevent tampering with audit logs
class QueryAuditLog(models.Model):
    # ... fields ...

    # Cryptographic hash of log entry
    integrity_hash = models.CharField(max_length=64, editable=False)

    def save(self, *args, **kwargs):
        if not self.pk:  # New record
            # Calculate hash of all fields
            self.integrity_hash = self._calculate_hash()
        super().save(*args, **kwargs)

    def _calculate_hash(self):
        import hashlib
        import json

        data = {
            'sql_query': self.sql_query,
            'user_email': self.user_email,
            'timestamp': self.timestamp.isoformat(),
            # ... include all relevant fields
        }

        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

    def verify_integrity(self):
        """Verify log entry hasn't been tampered with."""
        expected_hash = self._calculate_hash()
        return self.integrity_hash == expected_hash
```

### 2. Audit Log Access Control

```python
# Only security admins can view audit logs
class AuditLogPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.is_staff and
            request.user.has_perm('audit.view_queryauditlog')
        )
```

### 3. Sensitive Data Masking

```python
# Mask sensitive data in audit logs
def mask_sensitive_sql(sql):
    """Mask potential passwords/secrets in SQL."""

    # Mask password fields
    sql = re.sub(
        r"(password\s*=\s*['\"])(.*?)(['\"])",
        r"\1***REDACTED***\3",
        sql,
        flags=re.IGNORECASE
    )

    # Mask credit card numbers
    sql = re.sub(
        r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        '****-****-****-****',
        sql
    )

    return sql
```

---

## Monitoring and Alerts

```python
# apps/audit/monitoring.py

def check_audit_anomalies():
    """
    Check for anomalous audit patterns.

    Run periodically (e.g., every hour).
    """
    from datetime import timedelta
    from django.utils import timezone

    last_hour = timezone.now() - timedelta(hours=1)

    # Check for excessive data access by single user
    from django.db.models import Count

    heavy_users = (
        QueryAuditLog.objects
        .filter(timestamp__gte=last_hour)
        .values('user_email')
        .annotate(query_count=Count('id'))
        .filter(query_count__gt=1000)  # >1000 queries/hour
    )

    for user in heavy_users:
        send_alert(
            f"Excessive database activity detected: "
            f"{user['user_email']} executed {user['query_count']} queries in last hour"
        )

    # Check for bulk deletions
    bulk_deletes = QueryAuditLog.objects.filter(
        timestamp__gte=last_hour,
        query_type='DELETE',
        rows_affected__gt=100
    )

    if bulk_deletes.exists():
        send_alert(
            f"Bulk deletion detected: {bulk_deletes.count()} large DELETE operations"
        )
```

---

## Testing

```python
# tests/audit/test_query_auditing.py

import pytest
from apps.audit.models import QueryAuditLog


@pytest.mark.django_db
class TestQueryAuditing:

    def test_query_logged(self, client, authenticated_user):
        """Test that queries are logged."""
        # Execute request that triggers DB query
        response = client.get('/api/v1/reports/')

        # Verify audit log created
        assert QueryAuditLog.objects.filter(
            user=authenticated_user,
            query_type='SELECT'
        ).exists()


    def test_sensitive_query_flagged(self, client, authenticated_user):
        """Test that sensitive queries are flagged."""
        # Modify user data
        authenticated_user.first_name = 'NewName'
        authenticated_user.save()

        # Verify logged as sensitive
        audit_log = QueryAuditLog.objects.filter(
            query_type='UPDATE',
            tables_accessed__contains=['authentication_user']
        ).latest('timestamp')

        assert audit_log.is_sensitive is True
        assert audit_log.risk_level >= 5


    def test_audit_retention(self):
        """Test audit log cleanup task."""
        from apps.audit.tasks import cleanup_old_audit_logs
        from datetime import timedelta
        from django.utils import timezone

        # Create old audit log
        old_log = QueryAuditLog.objects.create(
            sql_query='SELECT * FROM test',
            query_type='SELECT',
            timestamp=timezone.now() - timedelta(days=400)
        )

        # Run cleanup
        cleanup_old_audit_logs()

        # Verify old log deleted
        assert not QueryAuditLog.objects.filter(id=old_log.id).exists()
```

---

## Deployment Checklist

- [ ] Create audit database tables
- [ ] Configure retention policies
- [ ] Set up audit log rotation
- [ ] Create audit dashboard
- [ ] Train security team on audit reports
- [ ] Test compliance report generation
- [ ] Set up monitoring alerts
- [ ] Document audit procedures
- [ ] Schedule regular audit reviews
- [ ] Compliance certification audit

---

## Conclusion

Database Query Auditing is essential for compliance and security monitoring. It provides comprehensive visibility into data access patterns and enables forensic analysis of security incidents.

**Recommendation:** Implement before pursuing compliance certifications (GDPR, HIPAA, SOX).

**Priority:** MEDIUM (Compliance-driven)
**Effort:** 12 hours
**Value:** HIGH (Required for compliance)

---

## References

1. **GDPR Article 30 - Records of Processing**
   https://gdpr-info.eu/art-30-gdpr/

2. **NIST SP 800-92 - Guide to Computer Security Log Management**
   https://csrc.nist.gov/publications/detail/sp/800-92/final

3. **PCI DSS Requirement 10 - Audit Trails**
   https://www.pcisecuritystandards.org/

---

**Document Status:** ✅ DESIGN COMPLETE - AWAITING IMPLEMENTATION
**Next Steps:** Implement when compliance certification required
**Contact:** Security Team (security@azurereportsadvisor.com)

---

**Last Updated:** November 5, 2025
**Version:** 1.0
**Classification:** INTERNAL - COMPLIANCE DOCUMENTATION
