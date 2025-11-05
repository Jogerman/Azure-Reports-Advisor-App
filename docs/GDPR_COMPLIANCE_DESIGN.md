# GDPR Compliance Implementation - Design Document
**Phase 4, Task 4.8 - Future Implementation**
**Date:** November 5, 2025
**Status:** DESIGN PROPOSAL
**Estimated Effort:** 40 hours
**Classification:** LEGAL COMPLIANCE - CRITICAL

## Executive Summary

The General Data Protection Regulation (GDPR) is a comprehensive EU privacy law that imposes strict requirements on how organizations collect, process, store, and protect personal data. Non-compliance can result in **fines up to €20 million or 4% of global annual revenue**, whichever is higher.

This document outlines the technical implementation required to achieve GDPR compliance for the Azure Reports Advisor application.

**Scope:** Personal data of EU residents (customers, users, contacts)
**Enforcement Date:** May 25, 2018 (already in effect)
**Penalty Risk:** HIGH
**Implementation Priority:** CRITICAL (if serving EU customers)

---

## GDPR Core Principles

### 1. Lawfulness, Fairness, and Transparency (Article 5.1.a)
- **Requirement:** Process data lawfully, fairly, and transparently
- **Implementation:** Privacy notices, consent mechanisms, audit trails

### 2. Purpose Limitation (Article 5.1.b)
- **Requirement:** Collect data for specified, explicit, and legitimate purposes
- **Implementation:** Document processing purposes, prevent secondary use

### 3. Data Minimization (Article 5.1.c)
- **Requirement:** Collect only necessary data
- **Implementation:** Review data collection, remove unnecessary fields

### 4. Accuracy (Article 5.1.d)
- **Requirement:** Keep data accurate and up-to-date
- **Implementation:** Data update mechanisms, accuracy verification

### 5. Storage Limitation (Article 5.1.e)
- **Requirement:** Retain data only as long as necessary
- **Implementation:** Automated data retention and deletion policies

### 6. Integrity and Confidentiality (Article 5.1.f)
- **Requirement:** Secure data against unauthorized access
- **Implementation:** Encryption, access controls, security monitoring

### 7. Accountability (Article 5.2)
- **Requirement:** Demonstrate compliance
- **Implementation:** Documentation, audit logs, compliance reports

---

## Personal Data Inventory

### Data Subjects
- **Users** - Application users (employees, administrators)
- **Clients** - Azure customers using advisory services
- **Contacts** - Client contacts and representatives

### Personal Data Categories

| Data Category | Example Fields | Legal Basis | Retention Period |
|--------------|----------------|-------------|------------------|
| **Identity Data** | Name, email, user ID | Contract, Legitimate Interest | Account lifetime + 1 year |
| **Contact Data** | Email, phone number | Contract | Account lifetime + 1 year |
| **Authentication Data** | Password hash, JWT tokens | Contract, Security | Session duration |
| **Activity Data** | Login timestamps, IP addresses | Legitimate Interest, Security | 90 days |
| **Usage Data** | Reports generated, API calls | Legitimate Interest | 1 year |
| **Technical Data** | Browser type, device info | Legitimate Interest | Session duration |

### Special Categories (Article 9)
- **Health Data** - NOT COLLECTED
- **Biometric Data** - NOT COLLECTED
- **Genetic Data** - NOT COLLECTED
- **Political Opinions** - NOT COLLECTED

**Status:** No special category data processed ✅

---

## GDPR Rights Implementation

### Article 15: Right of Access (Subject Access Request)

**Implementation:** API endpoint to retrieve all personal data

```python
# apps/gdpr/views.py

from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from apps.gdpr.services.data_export import PersonalDataExporter

User = get_user_model()


class SubjectAccessRequestView(views.APIView):
    """
    GDPR Article 15 - Right of Access

    Allows users to retrieve all personal data the organization holds about them.

    Request must be authenticated with user's credentials.
    Response provided within 30 days (1 month).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Export all personal data for authenticated user.

        Returns ZIP file containing:
        - User profile data (JSON)
        - Activity logs (CSV)
        - Generated reports metadata (JSON)
        - Audit trail (CSV)
        """
        user = request.user
        exporter = PersonalDataExporter(user)

        try:
            # Generate comprehensive data export
            export_data = exporter.export_all_data()

            return Response({
                'status': 'success',
                'message': 'Your personal data export has been prepared',
                'data': export_data,
                'export_timestamp': timezone.now().isoformat(),
                'format': 'JSON',
                'instructions': 'This export contains all personal data we hold about you.'
            })

        except Exception as e:
            logger.error(f'SAR export failed for user {user.id}: {e}', exc_info=True)
            return Response({
                'error': 'Failed to generate data export',
                'message': 'Please contact support if this issue persists.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

**Data Export Service:**

```python
# apps/gdpr/services/data_export.py

import json
from typing import Dict
from django.utils import timezone


class PersonalDataExporter:
    """
    Export all personal data for a user.

    Implements GDPR Article 15 (Right of Access).
    """

    def __init__(self, user):
        self.user = user

    def export_all_data(self) -> Dict:
        """
        Export all personal data in structured format.

        Returns dictionary with all user data.
        """
        return {
            'user_profile': self._export_user_profile(),
            'authentication_history': self._export_auth_history(),
            'activity_logs': self._export_activity_logs(),
            'reports': self._export_reports_data(),
            'clients': self._export_client_data(),
            'audit_trail': self._export_audit_trail(),
            'consent_records': self._export_consent_records(),
        }

    def _export_user_profile(self) -> Dict:
        """Export user profile data."""
        return {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'is_active': self.user.is_active,
            'date_joined': self.user.date_joined.isoformat(),
            'last_login': self.user.last_login.isoformat() if self.user.last_login else None,
        }

    def _export_auth_history(self) -> list:
        """Export authentication history."""
        # TODO: Implement authentication log model
        return []

    def _export_activity_logs(self) -> list:
        """Export activity logs."""
        from apps.audit.models import DataAccessLog

        logs = DataAccessLog.objects.filter(user=self.user).order_by('-timestamp')

        return [
            {
                'timestamp': log.timestamp.isoformat(),
                'action': log.access_type,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'ip_address': log.ip_address,
            }
            for log in logs
        ]

    def _export_reports_data(self) -> list:
        """Export reports created by user."""
        from apps.reports.models import Report

        reports = Report.objects.filter(created_by=self.user)

        return [
            {
                'id': report.id,
                'title': report.title,
                'created_at': report.created_at.isoformat(),
                'report_type': report.report_type,
                'status': report.status,
            }
            for report in reports
        ]

    def _export_client_data(self) -> list:
        """Export client associations."""
        from apps.clients.models import Client

        # Only export client IDs and names (not full client data)
        # User may not have rights to all client data
        clients = Client.objects.filter(created_by=self.user)

        return [
            {
                'id': client.id,
                'name': client.name,
                'created_at': client.created_at.isoformat(),
            }
            for client in clients
        ]

    def _export_audit_trail(self) -> list:
        """Export audit trail for user's actions."""
        from apps.audit.models import QueryAuditLog

        audit_logs = QueryAuditLog.objects.filter(user=self.user).order_by('-timestamp')

        return [
            {
                'timestamp': log.timestamp.isoformat(),
                'action': log.query_type,
                'tables': log.tables_accessed,
                'ip_address': log.ip_address,
            }
            for log in audit_logs
        ]

    def _export_consent_records(self) -> list:
        """Export consent records."""
        from apps.gdpr.models import ConsentRecord

        consents = ConsentRecord.objects.filter(user=self.user).order_by('-timestamp')

        return [
            {
                'consent_type': consent.consent_type,
                'granted': consent.granted,
                'timestamp': consent.timestamp.isoformat(),
                'version': consent.privacy_policy_version,
            }
            for consent in consents
        ]
```

---

### Article 16: Right to Rectification

**Implementation:** Allow users to update personal data

```python
class PersonalDataUpdateView(views.APIView):
    """
    GDPR Article 16 - Right to Rectification

    Allow users to update their personal data.
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        """Update user's personal data."""
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            # Log the update for audit trail
            log_personal_data_update(user, request.data.keys())

            return Response({
                'status': 'success',
                'message': 'Personal data updated successfully'
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

---

### Article 17: Right to Erasure ("Right to be Forgotten")

**Implementation:** Complete data deletion mechanism

```python
# apps/gdpr/services/data_deletion.py

from django.db import transaction
import logging

logger = logging.getLogger('gdpr.deletion')


class PersonalDataEraser:
    """
    Implements GDPR Article 17 (Right to Erasure).

    Permanently deletes all personal data for a user.
    """

    def __init__(self, user):
        self.user = user

    @transaction.atomic
    def erase_all_data(self, reason: str = 'User request'):
        """
        Permanently delete all personal data.

        CAUTION: This operation is irreversible!

        Steps:
        1. Export data for final backup (legal requirement)
        2. Anonymize or delete related records
        3. Delete user account
        4. Log deletion in compliance log
        """
        user_id = self.user.id
        user_email = self.user.email

        logger.info(f'Starting data erasure for user {user_id} ({user_email})')

        try:
            # Step 1: Create final backup
            final_export = PersonalDataExporter(self.user).export_all_data()
            self._archive_final_export(final_export)

            # Step 2: Anonymize related records (preserve referential integrity)
            self._anonymize_reports()
            self._anonymize_clients()
            self._anonymize_audit_logs()

            # Step 3: Delete personal data
            self._delete_authentication_data()
            self._delete_activity_logs()
            self._delete_consent_records()

            # Step 4: Delete user account
            self.user.delete()

            # Step 5: Log deletion
            self._log_deletion(user_id, user_email, reason)

            logger.info(f'Data erasure completed for user {user_id}')

            return {
                'status': 'success',
                'message': f'All personal data for user {user_email} has been permanently deleted',
                'deleted_at': timezone.now().isoformat(),
                'user_id': user_id,
            }

        except Exception as e:
            logger.error(f'Data erasure failed for user {user_id}: {e}', exc_info=True)
            raise

    def _anonymize_reports(self):
        """Anonymize reports created by user (don't delete - may be needed)."""
        from apps.reports.models import Report

        Report.objects.filter(created_by=self.user).update(
            created_by=None,
            # Optionally add flag
            creator_anonymized=True
        )

    def _anonymize_clients(self):
        """Anonymize client records."""
        from apps.clients.models import Client

        Client.objects.filter(created_by=self.user).update(
            created_by=None,
            creator_anonymized=True
        )

    def _anonymize_audit_logs(self):
        """Anonymize audit logs (keep for compliance, but remove PII)."""
        from apps.audit.models import QueryAuditLog

        QueryAuditLog.objects.filter(user=self.user).update(
            user=None,
            user_email='[DELETED USER]',
            # Keep ip_address for security analysis
        )

    def _delete_authentication_data(self):
        """Delete authentication tokens and sessions."""
        from apps.authentication.models import TokenBlacklist

        # Revoke all tokens
        # (Tokens will naturally expire, but blacklist for immediate effect)
        TokenBlacklist.objects.filter(user=self.user).delete()

        # Clear sessions
        from django.contrib.sessions.models import Session
        # Delete all sessions for this user
        # (Implementation depends on session backend)

    def _delete_activity_logs(self):
        """Delete activity logs."""
        from apps.audit.models import DataAccessLog

        DataAccessLog.objects.filter(user=self.user).delete()

    def _delete_consent_records(self):
        """Delete consent records."""
        from apps.gdpr.models import ConsentRecord

        ConsentRecord.objects.filter(user=self.user).delete()

    def _archive_final_export(self, export_data):
        """Archive final export for compliance (keep for limited time)."""
        from apps.gdpr.models import DeletionArchive

        DeletionArchive.objects.create(
            user_id=self.user.id,
            user_email=self.user.email,
            export_data=export_data,
            deletion_timestamp=timezone.now(),
            # Auto-delete after 30 days (compliance requirement)
            expires_at=timezone.now() + timedelta(days=30)
        )

    def _log_deletion(self, user_id, user_email, reason):
        """Log deletion in permanent compliance log."""
        from apps.gdpr.models import DeletionLog

        DeletionLog.objects.create(
            user_id=user_id,
            user_email=user_email,
            deletion_reason=reason,
            deletion_timestamp=timezone.now(),
            # This log is NEVER deleted (compliance requirement)
        )
```

**Deletion Request View:**

```python
class DataDeletionRequestView(views.APIView):
    """
    GDPR Article 17 - Right to Erasure

    Request permanent deletion of all personal data.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Request data deletion.

        User must confirm by providing their password.
        Deletion happens after 30-day grace period (optional).
        """
        user = request.user
        password = request.data.get('password')

        # Verify password
        if not user.check_password(password):
            return Response({
                'error': 'Invalid password'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create deletion request
        from apps.gdpr.models import DeletionRequest

        deletion_request = DeletionRequest.objects.create(
            user=user,
            requested_at=timezone.now(),
            scheduled_for=timezone.now() + timedelta(days=30),  # Grace period
            reason=request.data.get('reason', 'User request'),
            status='PENDING'
        )

        # Send confirmation email
        send_deletion_confirmation_email(user, deletion_request)

        return Response({
            'status': 'success',
            'message': 'Your data deletion request has been received',
            'scheduled_deletion': deletion_request.scheduled_for.isoformat(),
            'cancellation_deadline': (timezone.now() + timedelta(days=30)).isoformat(),
            'instructions': 'You can cancel this request within 30 days by logging in.'
        })

    def delete(self, request):
        """
        Cancel pending deletion request.
        """
        user = request.user

        deletion_request = DeletionRequest.objects.filter(
            user=user,
            status='PENDING'
        ).first()

        if not deletion_request:
            return Response({
                'error': 'No pending deletion request found'
            }, status=status.HTTP_404_NOT_FOUND)

        deletion_request.status = 'CANCELLED'
        deletion_request.cancelled_at = timezone.now()
        deletion_request.save()

        return Response({
            'status': 'success',
            'message': 'Deletion request cancelled'
        })
```

---

### Article 18: Right to Restriction of Processing

**Implementation:** Temporarily restrict data processing

```python
# apps/gdpr/models.py

class ProcessingRestriction(models.Model):
    """
    GDPR Article 18 - Restriction of Processing

    User can request temporary restriction of their data processing.
    """

    RESTRICTION_REASONS = [
        ('ACCURACY', 'User contests accuracy of data'),
        ('UNLAWFUL', 'Processing is unlawful'),
        ('NO_LONGER_NEEDED', 'Organization no longer needs data'),
        ('OBJECTION', 'User objected to processing'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, choices=RESTRICTION_REASONS)
    requested_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'gdpr_processing_restrictions'

    def __str__(self):
        return f'Processing restriction for {self.user.email} - {self.reason}'


# Enforce restriction in queries
def get_user_data(user):
    """Check if processing is restricted before accessing data."""
    if ProcessingRestriction.objects.filter(user=user, active=True).exists():
        raise ProcessingRestrictedError(
            'Processing of this user\'s data is currently restricted'
        )

    # Proceed with data access
    return user.get_personal_data()
```

---

### Article 20: Right to Data Portability

**Implementation:** Export data in machine-readable format

```python
class DataPortabilityView(views.APIView):
    """
    GDPR Article 20 - Right to Data Portability

    Export personal data in structured, machine-readable format (JSON).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Export data in JSON format for portability.

        Includes only data provided by user or generated with their consent.
        Does not include derived/inferred data.
        """
        user = request.user
        exporter = PersonalDataExporter(user)

        portable_data = {
            'format': 'JSON',
            'version': '1.0',
            'generated_at': timezone.now().isoformat(),
            'data_controller': 'Azure Reports Advisor',
            'data_subject': {
                'email': user.email,
                'user_id': user.id,
            },
            'data': exporter.export_portable_data()  # Only portable data
        }

        return Response(portable_data)
```

---

### Article 21: Right to Object

**Implementation:** Allow users to object to processing

```python
class ProcessingObjectionView(views.APIView):
    """
    GDPR Article 21 - Right to Object

    Allow users to object to certain types of processing.
    """
    permission_classes = [permissions.IsAuthenticated]

    OBJECTION_TYPES = [
        'MARKETING',  # Object to marketing communications
        'PROFILING',  # Object to automated profiling
        'ANALYTICS',  # Object to usage analytics
    ]

    def post(self, request):
        """
        Record processing objection.

        User can object to:
        - Marketing communications
        - Automated profiling
        - Usage analytics
        """
        user = request.user
        objection_type = request.data.get('objection_type')

        if objection_type not in self.OBJECTION_TYPES:
            return Response({
                'error': 'Invalid objection type',
                'valid_types': self.OBJECTION_TYPES
            }, status=status.HTTP_400_BAD_REQUEST)

        # Record objection
        from apps.gdpr.models import ProcessingObjection

        ProcessingObjection.objects.create(
            user=user,
            objection_type=objection_type,
            timestamp=timezone.now()
        )

        # Immediately stop objected processing
        self._enforce_objection(user, objection_type)

        return Response({
            'status': 'success',
            'message': f'Your objection to {objection_type} has been recorded'
        })

    def _enforce_objection(self, user, objection_type):
        """Enforce processing objection immediately."""
        if objection_type == 'MARKETING':
            # Unsubscribe from marketing
            user.profile.marketing_consent = False
            user.profile.save()

        elif objection_type == 'ANALYTICS':
            # Disable analytics tracking
            user.profile.analytics_consent = False
            user.profile.save()
```

---

## Consent Management

**Article 7: Conditions for Consent**

```python
# apps/gdpr/models.py

class ConsentRecord(models.Model):
    """
    GDPR Article 7 - Consent Management

    Track consent for different processing activities.
    """

    CONSENT_TYPES = [
        ('TERMS_OF_SERVICE', 'Terms of Service'),
        ('PRIVACY_POLICY', 'Privacy Policy'),
        ('MARKETING', 'Marketing Communications'),
        ('ANALYTICS', 'Usage Analytics'),
        ('COOKIES', 'Cookie Usage'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    consent_type = models.CharField(max_length=50, choices=CONSENT_TYPES)
    granted = models.BooleanField()  # True = consent given, False = consent withdrawn
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Consent must be specific and informed
    purpose = models.TextField()  # Clear description of what consent is for
    privacy_policy_version = models.CharField(max_length=20)  # Version user consented to

    # Consent must be freely given
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'gdpr_consent_records'
        ordering = ['-timestamp']

    def __str__(self):
        action = 'granted' if self.granted else 'withdrawn'
        return f'{self.user.email} {action} {self.consent_type} consent'


# Enforce consent before processing
def can_send_marketing_email(user):
    """Check if user has consented to marketing."""
    latest_consent = ConsentRecord.objects.filter(
        user=user,
        consent_type='MARKETING'
    ).order_by('-timestamp').first()

    return latest_consent and latest_consent.granted
```

---

## Data Retention Policy

**Article 5.1.e: Storage Limitation**

```python
# apps/gdpr/services/data_retention.py

from datetime import timedelta
from django.utils import timezone
from celery import shared_task


class DataRetentionPolicy:
    """
    Automated data retention and deletion policies.

    Implements GDPR Article 5.1.e (Storage Limitation).
    """

    RETENTION_PERIODS = {
        'user_accounts': timedelta(days=365),  # 1 year after account closure
        'audit_logs': timedelta(days=365),  # 1 year
        'activity_logs': timedelta(days=90),  # 90 days
        'authentication_logs': timedelta(days=90),  # 90 days
        'reports': timedelta(days=730),  # 2 years
        'deleted_user_archives': timedelta(days=30),  # 30 days
    }

    @staticmethod
    @shared_task
    def cleanup_expired_data():
        """
        Celery task to cleanup expired data based on retention policy.

        Schedule: Run daily at 2 AM
        """
        logger.info('Starting automated data retention cleanup')

        # Cleanup inactive user accounts
        DataRetentionPolicy._cleanup_inactive_accounts()

        # Cleanup old audit logs
        DataRetentionPolicy._cleanup_audit_logs()

        # Cleanup old activity logs
        DataRetentionPolicy._cleanup_activity_logs()

        # Cleanup deletion archives
        DataRetentionPolicy._cleanup_deletion_archives()

        logger.info('Data retention cleanup completed')

    @staticmethod
    def _cleanup_inactive_accounts():
        """Delete accounts that have been inactive for retention period."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        cutoff_date = timezone.now() - DataRetentionPolicy.RETENTION_PERIODS['user_accounts']

        inactive_users = User.objects.filter(
            is_active=False,
            last_login__lt=cutoff_date
        )

        for user in inactive_users:
            logger.info(f'Auto-deleting inactive user {user.email} (last login: {user.last_login})')

            # Use proper deletion service
            eraser = PersonalDataEraser(user)
            eraser.erase_all_data(reason='Automated retention policy')

    @staticmethod
    def _cleanup_audit_logs():
        """Delete audit logs older than retention period."""
        from apps.audit.models import QueryAuditLog

        cutoff_date = timezone.now() - DataRetentionPolicy.RETENTION_PERIODS['audit_logs']

        deleted_count = QueryAuditLog.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()[0]

        logger.info(f'Deleted {deleted_count} expired audit logs')

    @staticmethod
    def _cleanup_activity_logs():
        """Delete activity logs older than retention period."""
        from apps.audit.models import DataAccessLog

        cutoff_date = timezone.now() - DataRetentionPolicy.RETENTION_PERIODS['activity_logs']

        deleted_count = DataAccessLog.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()[0]

        logger.info(f'Deleted {deleted_count} expired activity logs')

    @staticmethod
    def _cleanup_deletion_archives():
        """Delete deletion archives after 30 days."""
        from apps.gdpr.models import DeletionArchive

        cutoff_date = timezone.now() - DataRetentionPolicy.RETENTION_PERIODS['deleted_user_archives']

        deleted_count = DeletionArchive.objects.filter(
            expires_at__lt=cutoff_date
        ).delete()[0]

        logger.info(f'Deleted {deleted_count} expired deletion archives')
```

---

## Privacy by Design (Article 25)

### Data Protection Impact Assessment (DPIA)

```markdown
# Data Protection Impact Assessment (DPIA)
## Azure Reports Advisor Application

### 1. Nature, Scope, Context, and Purposes
- **Purpose:** Azure advisory and reporting services
- **Data Processed:** User accounts, client data, reports
- **Data Subjects:** Employees, customers
- **Scale:** [X] users, [Y] reports/month

### 2. Necessity and Proportionality
- **Necessity:** User accounts necessary for access control
- **Minimization:** Only collect email, name, role
- **Alternatives Considered:** Anonymous access (rejected - need for audit trail)

### 3. Risks to Data Subjects
| Risk | Likelihood | Severity | Mitigation |
|------|-----------|----------|------------|
| Unauthorized access | Medium | High | Implement authentication, rate limiting |
| Data breach | Low | High | Encryption at rest and in transit |
| Account hijacking | Medium | Medium | MFA, token expiration |

### 4. Measures to Address Risks
- Encryption (TLS 1.3, AES-256)
- Access controls (RBAC)
- Audit logging
- Regular security updates
- Incident response plan

### 5. Conclusion
**Risk Level:** MEDIUM
**Approval:** Proceed with additional safeguards
**Review Date:** 2026-11-05
```

---

## Breach Notification (Article 33-34)

```python
# apps/gdpr/services/breach_notification.py

class BreachNotificationService:
    """
    GDPR Article 33-34: Data Breach Notification

    Requirements:
    - Notify supervisory authority within 72 hours
    - Notify affected data subjects if high risk
    """

    @staticmethod
    def report_breach(breach_details):
        """
        Report data breach to supervisory authority and affected individuals.

        Article 33: Notification to authority within 72 hours
        Article 34: Notification to data subjects if high risk
        """
        from apps.gdpr.models import DataBreach

        # Create breach record
        breach = DataBreach.objects.create(
            detected_at=timezone.now(),
            description=breach_details['description'],
            affected_records=breach_details['affected_records'],
            data_categories=breach_details['data_categories'],
            risk_level=breach_details['risk_level'],
        )

        # Notify supervisory authority (within 72 hours)
        if breach.risk_level in ['HIGH', 'CRITICAL']:
            BreachNotificationService._notify_supervisory_authority(breach)

        # Notify affected individuals (if high risk)
        if breach.risk_level == 'CRITICAL':
            BreachNotificationService._notify_affected_individuals(breach)

        return breach

    @staticmethod
    def _notify_supervisory_authority(breach):
        """
        Notify relevant supervisory authority (DPA).

        For EU: Contact appropriate Data Protection Authority
        """
        logger.critical(f'DATA BREACH: {breach.description}')

        # Send formal notification to DPA
        # Include:
        # - Nature of breach
        # - Categories and approximate number of data subjects
        # - Categories and approximate number of records
        # - Likely consequences
        # - Measures taken or proposed

        send_mail(
            subject='URGENT: Data Breach Notification',
            message=f'''
            A data breach has been detected:

            Description: {breach.description}
            Detected: {breach.detected_at}
            Affected Records: {breach.affected_records}
            Risk Level: {breach.risk_level}

            Detailed report attached.
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DPA_CONTACT_EMAIL],
        )

    @staticmethod
    def _notify_affected_individuals(breach):
        """
        Notify affected data subjects about the breach.

        Required when breach results in high risk to rights and freedoms.
        """
        # Get affected users
        affected_users = User.objects.filter(
            # Logic to identify affected users based on breach
        )

        for user in affected_users:
            send_mail(
                subject='Important Security Notification',
                message=f'''
                Dear {user.first_name},

                We are writing to inform you of a security incident that may have affected your personal data.

                What happened: {breach.description}
                When: {breach.detected_at}
                What data: {breach.data_categories}

                What we're doing:
                - [List of remediation steps]

                What you should do:
                - Change your password
                - Monitor your account for suspicious activity
                - Contact us if you have concerns

                We sincerely apologize for this incident.

                Best regards,
                Azure Reports Advisor Security Team
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
```

---

## Compliance Checklist

### Technical Measures
- [ ] Data encryption (at rest and in transit)
- [ ] Access controls and authentication
- [ ] Audit logging
- [ ] Data minimization
- [ ] Pseudonymization where possible
- [ ] Regular security updates

### Organizational Measures
- [ ] Privacy Policy published
- [ ] Data Protection Officer (DPO) appointed
- [ ] Data Processing Agreements with third parties
- [ ] Employee training on GDPR
- [ ] Incident response plan
- [ ] Regular compliance audits

### Rights Implementation
- [ ] Right of access (Article 15)
- [ ] Right to rectification (Article 16)
- [ ] Right to erasure (Article 17)
- [ ] Right to restriction (Article 18)
- [ ] Right to data portability (Article 20)
- [ ] Right to object (Article 21)

### Documentation
- [ ] Records of processing activities (Article 30)
- [ ] Data Protection Impact Assessment (Article 35)
- [ ] Consent records
- [ ] Retention policies
- [ ] Breach notification procedures

---

## Penalties for Non-Compliance

| Violation | Maximum Fine | Examples |
|-----------|--------------|----------|
| **Tier 1** | €10M or 2% revenue | Insufficient data security, lack of DPIA |
| **Tier 2** | €20M or 4% revenue | No legal basis for processing, violating data subject rights |

**Recent Fines:**
- Amazon: €746 million (2021)
- WhatsApp: €225 million (2021)
- Google: €90 million (2020)

---

## Implementation Timeline

### Phase 1: Foundation (Weeks 1-2)
- [ ] Conduct data inventory
- [ ] Document processing activities
- [ ] Implement consent management
- [ ] Create privacy policy

### Phase 2: Rights Implementation (Weeks 3-4)
- [ ] Implement Subject Access Request endpoint
- [ ] Implement data deletion mechanism
- [ ] Implement data portability export
- [ ] Create user rights portal

### Phase 3: Security & Compliance (Weeks 5-6)
- [ ] Implement audit logging
- [ ] Set up data retention policies
- [ ] Create breach notification procedures
- [ ] Conduct DPIA

### Phase 4: Testing & Documentation (Weeks 7-8)
- [ ] Test all GDPR workflows
- [ ] Employee training
- [ ] Compliance documentation
- [ ] External audit (optional)

---

## Conclusion

GDPR compliance is a **legal requirement** for processing EU residents' personal data. Non-compliance can result in significant fines and reputational damage.

**Recommendation:** Implement BEFORE serving EU customers.

**Priority:** CRITICAL (if serving EU market)
**Effort:** 40 hours
**Value:** ESSENTIAL (legal requirement)
**Risk of Non-Compliance:** Fines up to €20M or 4% revenue

---

## References

1. **GDPR Official Text**
   https://gdpr-info.eu/

2. **ICO Guide to GDPR**
   https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/

3. **EDPB Guidelines**
   https://edpb.europa.eu/our-work-tools/general-guidance_en

4. **GDPR Checklist**
   https://gdpr.eu/checklist/

---

**Document Status:** ✅ DESIGN COMPLETE - REQUIRES LEGAL REVIEW
**Next Steps:** Legal review → Implementation → Compliance audit
**Contact:** Legal Team & DPO (dpo@azurereportsadvisor.com)

---

**Last Updated:** November 5, 2025
**Version:** 1.0
**Classification:** LEGAL COMPLIANCE - CONFIDENTIAL
