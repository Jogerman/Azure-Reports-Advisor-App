# Phase 3 Completion Summary - Security & Notifications

**Date Completed:** November 11, 2025
**Status:** ✅ Complete

---

## Executive Summary

Phase 3 focused on implementing advanced security features and a comprehensive notification system. All critical security enhancements have been implemented, including Azure Key Vault integration, role-based access control (RBAC), token rotation strategies, virus scanning, and a multi-channel notification system.

**Key Achievements:**
- 🔐 **Azure Key Vault Integration** - Secure secrets management
- 👥 **RBAC System** - Four-tier role hierarchy with granular permissions
- 🔄 **Token Rotation** - Automatic JWT and API key rotation
- 🛡️ **Virus Scanning** - ClamAV and Azure Defender integration
- 📧 **Notification System** - Email, webhooks, and in-app notifications

---

## Table of Contents

1. [Azure Key Vault Integration](#1-azure-key-vault-integration)
2. [Role-Based Access Control (RBAC)](#2-role-based-access-control-rbac)
3. [Notification System](#3-notification-system)
4. [Token Rotation Strategy](#4-token-rotation-strategy)
5. [Virus Scanning](#5-virus-scanning)
6. [Files Created](#6-files-created)
7. [Database Migrations Required](#7-database-migrations-required)
8. [Configuration Required](#8-configuration-required)
9. [Testing Recommendations](#9-testing-recommendations)
10. [Next Steps](#10-next-steps)

---

## 1. Azure Key Vault Integration

### Overview
Implemented secure secrets management using Azure Key Vault, eliminating the need to store sensitive credentials in environment variables or configuration files.

### Implementation Details

**File:** `apps/security/key_vault.py` (412 lines)

**Key Features:**
- ✅ DefaultAzureCredential for flexible authentication
- ✅ LRU caching for improved performance
- ✅ Redis-based caching with 5-minute TTL
- ✅ Secret rotation support
- ✅ Pre-configured secrets for common services
- ✅ Context manager for batch secret operations

**Main Functions:**
```python
# Get a secret
db_password = get_secret('database-password')

# Set a secret
set_secret('api-key', 'new-secret-value')

# Rotate a secret
rotate_secret('api-key', 'new-rotated-value')

# Context manager
with SecretManager() as sm:
    db_pass = sm.get('database-password')
    redis_pass = sm.get('redis-password')
```

**Pre-configured Secrets:**
- Database configuration (username, password, host)
- Azure AD configuration (client ID, secret, tenant)
- Storage configuration (account name, key, connection string)
- Redis configuration (password, host)
- Application Insights (connection string, instrumentation key)
- Email configuration (SMTP password, API key)

**Configuration Helper:**
```python
# In settings.py
from apps.security.key_vault import configure_from_key_vault

config = configure_from_key_vault({
    'DATABASE_PASSWORD': 'database-password',
    'SECRET_KEY': 'django-secret-key',
    'REDIS_PASSWORD': 'redis-password',
})

DATABASES['default']['PASSWORD'] = config['DATABASE_PASSWORD']
```

### Security Benefits
- ✅ Secrets stored in Azure Key Vault, not in code
- ✅ Automatic rotation support
- ✅ Audit logging of secret access
- ✅ Managed Identity authentication in Azure
- ✅ Encryption at rest and in transit

---

## 2. Role-Based Access Control (RBAC)

### Overview
Comprehensive RBAC system with four-tier role hierarchy and granular resource-level permissions.

### Implementation Details

**File:** `apps/security/permissions.py` (530 lines)

**Role Hierarchy:**
1. **Admin (Level 4)** - Full system access
2. **Manager (Level 3)** - Manage clients, reports, view analytics
3. **Analyst (Level 2)** - Create and view reports
4. **Viewer (Level 1)** - Read-only access

**Resource Permissions:**
```python
# Client permissions
VIEW_CLIENT, ADD_CLIENT, CHANGE_CLIENT, DELETE_CLIENT

# Report permissions
VIEW_REPORT, ADD_REPORT, CHANGE_REPORT, DELETE_REPORT
DOWNLOAD_REPORT, GENERATE_REPORT

# User permissions
VIEW_USER, ADD_USER, CHANGE_USER, DELETE_USER
CHANGE_USER_ROLE

# Audit permissions
VIEW_AUDIT_LOG, EXPORT_AUDIT_LOG

# Analytics permissions
VIEW_ANALYTICS, EXPORT_ANALYTICS

# System permissions
MANAGE_SETTINGS, VIEW_SYSTEM_HEALTH
```

**Usage Examples:**

1. **Function-based permission check:**
```python
from apps.security.permissions import has_permission, ResourcePermission

if has_permission(request.user, ResourcePermission.DELETE_CLIENT):
    # Allow deletion
    client.delete()
```

2. **Decorator:**
```python
from apps.security.permissions import require_permission

@require_permission(ResourcePermission.DELETE_CLIENT)
def delete_client(request, client_id):
    # Only users with delete_client permission can access
    pass
```

3. **DRF Permission Classes:**
```python
from apps.security.permissions import IsManager, HasResourcePermission

class ClientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManager]
    # Only managers and admins can access
```

4. **Object-level permissions:**
```python
from apps.security.permissions import IsOwnerOrManager

class ReportViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrManager]
    # Owners and managers can access
```

**Permission Matrix:**

| Permission | Admin | Manager | Analyst | Viewer |
|-----------|-------|---------|---------|--------|
| View Clients | ✅ | ✅ | ✅ | ✅ |
| Add Clients | ✅ | ✅ | ❌ | ❌ |
| Delete Clients | ✅ | ❌ | ❌ | ❌ |
| Generate Reports | ✅ | ✅ | ✅ | ❌ |
| Delete Reports | ✅ | ✅ | ❌ | ❌ |
| Manage Users | ✅ | ❌ | ❌ | ❌ |
| View Audit Logs | ✅ | ✅ | ❌ | ❌ |
| Manage Settings | ✅ | ❌ | ❌ | ❌ |

---

## 3. Notification System

### Overview
Multi-channel notification system supporting email, webhooks, and in-app notifications with automatic triggering based on system events.

### Implementation Details

**Files Created:**
- `apps/notifications/models.py` (283 lines) - Data models
- `apps/notifications/services.py` (573 lines) - Business logic
- `apps/notifications/serializers.py` (210 lines) - REST API serializers
- `apps/notifications/views.py` (445 lines) - REST API endpoints
- `apps/notifications/urls.py` (24 lines) - URL routing
- `apps/notifications/admin.py` (350 lines) - Admin interface
- `apps/notifications/signals.py` (250 lines) - Automatic triggers
- `apps/notifications/management/commands/send_notification.py` (165 lines)
- `apps/notifications/management/commands/cleanup_notifications.py` (140 lines)

### Features

#### 3.1 Email Notifications

**Models:**
- EmailNotification - Tracks email sending with delivery status
- Open/click tracking support
- Retry mechanism for failed deliveries

**Usage:**
```python
from apps.notifications.services import EmailService

# Send basic email
EmailService.send_email(
    to_email='user@example.com',
    subject='Report Ready',
    message='Your report is ready',
    html_message='<h1>Your report is ready</h1>'
)

# Send template-based email
EmailService.send_template_email(
    to_email='user@example.com',
    subject='Report Ready',
    template_name='emails/report_completed',
    context={'report': report, 'user': user}
)

# Send report completed email
EmailService.send_report_completed_email(report, user)
```

#### 3.2 Webhook System

**Models:**
- Webhook - Configuration for webhook endpoints
- WebhookDelivery - Delivery logs with retry tracking

**Features:**
- ✅ HMAC signature generation for security
- ✅ Event-based triggering
- ✅ Automatic retry on failure
- ✅ Auto-disable after max failures
- ✅ Delivery history tracking
- ✅ Response time monitoring

**Usage:**
```python
from apps.notifications.services import WebhookService

# Trigger webhook
WebhookService.trigger_webhook(
    event_type='report.completed',
    payload={
        'report_id': str(report.id),
        'client_name': report.client.company_name,
        'timestamp': timezone.now().isoformat()
    }
)

# Verify webhook signature (in receiving server)
is_valid = WebhookService.verify_signature(
    payload=request_data,
    signature=request.headers['X-Webhook-Signature'],
    secret='your-webhook-secret'
)
```

**Webhook Configuration:**
```python
# Create webhook via API
POST /api/notifications/webhooks/
{
    "name": "Slack Integration",
    "url": "https://hooks.slack.com/services/...",
    "secret": "your-secret-key",
    "events": ["report.completed", "report.failed"],
    "method": "POST"
}
```

#### 3.3 In-App Notifications

**Features:**
- ✅ Real-time notifications
- ✅ Read/unread tracking
- ✅ Action buttons with URLs
- ✅ Priority levels
- ✅ Bulk mark as read

**Usage:**
```python
from apps.notifications.services import InAppNotificationService

# Create notification
InAppNotificationService.create_notification(
    user=request.user,
    title='Report Ready',
    message='Your report is ready to download',
    notification_type='report_completed',
    action_url='/reports/123',
    action_label='View Report'
)

# Get unread count
count = InAppNotificationService.get_unread_count(request.user)

# Mark all as read
InAppNotificationService.mark_all_as_read(request.user)
```

#### 3.4 Unified Notification Service

Send notifications across all channels from a single call:

```python
from apps.notifications.services import NotificationService

NotificationService.notify(
    user=request.user,
    title='Report Ready',
    message='Your report is ready',
    notification_type='report_completed',
    send_email=True,
    create_inapp=True,
    trigger_webhooks=True,
    action_url='/reports/123',
    action_label='View Report',
    email_template='emails/report_completed',
    email_context={'report': report},
    webhook_payload={'report_id': str(report.id)}
)
```

### REST API Endpoints

```
# Email Notifications
GET    /api/notifications/emails/              - List emails
GET    /api/notifications/emails/{id}/         - Get email
POST   /api/notifications/emails/{id}/retry/   - Retry failed email

# Webhooks
GET    /api/notifications/webhooks/                  - List webhooks
POST   /api/notifications/webhooks/                  - Create webhook
GET    /api/notifications/webhooks/{id}/             - Get webhook
PUT    /api/notifications/webhooks/{id}/             - Update webhook
DELETE /api/notifications/webhooks/{id}/             - Delete webhook
POST   /api/notifications/webhooks/{id}/test/        - Test webhook
POST   /api/notifications/webhooks/{id}/activate/    - Activate webhook
POST   /api/notifications/webhooks/{id}/deactivate/  - Deactivate webhook
GET    /api/notifications/webhooks/{id}/deliveries/  - Get delivery history

# Webhook Deliveries
GET    /api/notifications/webhook-deliveries/     - List deliveries
GET    /api/notifications/webhook-deliveries/{id}/ - Get delivery

# In-App Notifications
GET    /api/notifications/inapp/                - List notifications
GET    /api/notifications/inapp/unread_count/   - Get unread count
POST   /api/notifications/inapp/{id}/mark_read/ - Mark as read
POST   /api/notifications/inapp/mark_all_read/  - Mark all as read
DELETE /api/notifications/inapp/clear_read/     - Delete read notifications

# Unified API
POST   /api/notifications/send/  - Send notification
GET    /api/notifications/stats/ - Get statistics
```

### Automatic Notification Triggers

Notifications are automatically sent when:

1. **Report Completed** - Email + In-app + Webhook
2. **Report Failed** - Email + In-app + Webhook
3. **CSV Processed** - In-app + Webhook
4. **CSV Failed** - In-app + Webhook
5. **User Created** - Welcome email + In-app

### Management Commands

```bash
# Send notification to specific user
python manage.py send_notification \
    --user-id <uuid> \
    --title "Alert" \
    --message "Your message" \
    --priority high

# Send to all admins
python manage.py send_notification \
    --all-admins \
    --title "System Alert" \
    --message "Maintenance window scheduled"

# Clean up old notifications
python manage.py cleanup_notifications --days 90
python manage.py cleanup_notifications --days 30 --dry-run
```

---

## 4. Token Rotation Strategy

### Overview
Automatic rotation of JWT refresh tokens and API keys for enhanced security.

### Implementation Details

**File:** `apps/security/token_rotation.py` (550 lines)

### Features

#### 4.1 JWT Token Rotation

**Configuration:**
```python
# Token lifetimes
ACCESS_TOKEN_LIFETIME = 15 minutes
REFRESH_TOKEN_LIFETIME = 7 days
REFRESH_TOKEN_ROTATION_INTERVAL = 1 day
```

**Usage:**
```python
from apps.security.token_rotation import JWTTokenRotation

# Generate tokens
tokens = JWTTokenRotation.generate_tokens(user)
access_token = tokens['access']
refresh_token = tokens['refresh']

# Rotate refresh token
new_tokens = JWTTokenRotation.rotate_refresh_token(old_refresh_token)

# Blacklist token
JWTTokenRotation.blacklist_token(token_str)

# Revoke all user tokens (e.g., on password change)
JWTTokenRotation.revoke_all_user_tokens(user)
```

**Automatic Rotation:**
The `TokenRotationMiddleware` automatically rotates tokens on API requests when the rotation interval has passed.

```python
# In settings.py
MIDDLEWARE = [
    ...
    'apps.security.token_rotation.TokenRotationMiddleware',
]
```

#### 4.2 API Key Rotation

**Model:** `APIKey` in `apps/authentication/models.py`

**Features:**
- ✅ Secure random key generation (64 bytes)
- ✅ SHA256 hashing for storage
- ✅ Key prefix for identification
- ✅ Automatic expiration (90 days)
- ✅ Rotation tracking
- ✅ Last used tracking
- ✅ Expiry notifications

**Usage:**
```python
from apps.security.token_rotation import APIKeyRotation

# Create API key
key_data = APIKeyRotation.create_api_key(
    user=request.user,
    name='Production API',
    description='API key for production environment'
)
# key_data['key'] contains the actual key (only shown once!)

# Rotate API key
new_key = APIKeyRotation.rotate_api_key(api_key_id)

# Check expiring keys
expiring_keys = APIKeyRotation.check_expiring_keys(warning_days=7)
```

**Automatic Cleanup:**
```python
from apps.security.token_rotation import cleanup_expired_tokens, send_expiry_notifications

# Cleanup (run daily via cron/Celery)
cleanup_expired_tokens()

# Send expiry notifications (run daily)
send_expiry_notifications()
```

### Management Command

```bash
# Run all rotation tasks
python manage.py rotate_tokens --all

# Cleanup expired tokens
python manage.py rotate_tokens --cleanup

# Check expiring keys
python manage.py rotate_tokens --check-expiring --warning-days 7

# Send expiry notifications
python manage.py rotate_tokens --notify-expiring
```

### Security Benefits

- ✅ Automatic token rotation reduces exposure window
- ✅ Blacklisting prevents token reuse
- ✅ API key expiration enforces regular rotation
- ✅ Proactive expiry notifications prevent service interruption
- ✅ Secure key generation using secrets module
- ✅ Hashed storage prevents key exposure

---

## 5. Virus Scanning

### Overview
File upload virus scanning using ClamAV or Azure Defender for Storage.

### Implementation Details

**File:** `apps/security/virus_scanning.py` (580 lines)

### Features

#### 5.1 Scanner Support

**ClamAV Scanner:**
- Uses pyclamd library
- Scans files and streams
- Fast local scanning
- Pattern-based detection

**Azure Defender Scanner:**
- Cloud-based scanning
- Integrated with Azure Storage
- Asynchronous scanning
- Advanced threat detection

#### 5.2 Scanning Features

- ✅ File size limits (default: 100 MB)
- ✅ Result caching (24 hours for clean files)
- ✅ SHA256 file hashing
- ✅ Automatic quarantine of infected files
- ✅ Scan duration tracking
- ✅ Django form validator integration

### Usage

#### Basic File Scanning

```python
from apps.security.virus_scanning import VirusScanner

# Scan a file
result = VirusScanner.scan_file('/path/to/file.pdf')

if result.is_infected:
    print(f'Threat detected: {result.threat_name}')
else:
    print('File is clean')
```

#### Scan Uploaded File

```python
# In a Django view
from apps.security.virus_scanning import VirusScanner

def handle_upload(request):
    uploaded_file = request.FILES['file']
    result = VirusScanner.scan_upload(uploaded_file)

    if result.is_infected:
        return JsonResponse({
            'error': f'Virus detected: {result.threat_name}'
        }, status=400)

    # Process clean file
    ...
```

#### Django Form Validator

```python
from apps.security.virus_scanning import validate_uploaded_file

class UploadForm(forms.Form):
    file = forms.FileField(validators=[validate_uploaded_file])
```

#### DRF Integration

```python
from apps.security.virus_scanning import VirusScanner
from rest_framework import serializers

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        result = VirusScanner.scan_upload(value)
        if result.is_infected:
            raise serializers.ValidationError(
                f'Virus detected: {result.threat_name}'
            )
        return value
```

### Configuration

```python
# In settings.py

# Scanner type: 'clamav', 'azure_defender', 'disabled'
VIRUS_SCANNER_TYPE = 'clamav'

# ClamAV settings
CLAMAV_SOCKET = '/var/run/clamav/clamd.ctl'
CLAMAV_HOST = 'localhost'
CLAMAV_PORT = 3310

# File size limits (100 MB)
MAX_VIRUS_SCAN_SIZE = 100 * 1024 * 1024

# Cache settings
CACHE_CLEAN_FILES = True
CLEAN_FILE_CACHE_TIMEOUT = 3600 * 24  # 24 hours

# Quarantine settings
QUARANTINE_INFECTED_FILES = True
QUARANTINE_DIR = '/tmp/quarantine'
```

### Installation

**ClamAV (Linux):**
```bash
# Install ClamAV
sudo apt-get update
sudo apt-get install clamav clamav-daemon

# Update virus definitions
sudo freshclam

# Start daemon
sudo systemctl start clamav-daemon
sudo systemctl enable clamav-daemon

# Install Python library
pip install pyclamd
```

**Azure Defender:**
```bash
# Install Azure SDK
pip install azure-storage-blob

# Enable Azure Defender for Storage in Azure Portal
# Storage Account > Security + networking > Microsoft Defender for Cloud
```

### Security Benefits

- ✅ Prevents malware upload
- ✅ Automatic quarantine of threats
- ✅ Scan result caching reduces overhead
- ✅ Multiple scanner support
- ✅ Integration with Django forms and DRF

---

## 6. Files Created

### Security Module

```
apps/security/
├── key_vault.py                    (412 lines) ✅
├── permissions.py                  (530 lines) ✅
├── token_rotation.py              (550 lines) ✅
├── virus_scanning.py              (580 lines) ✅
└── management/
    └── commands/
        └── rotate_tokens.py        (95 lines) ✅
```

### Notifications Module

```
apps/notifications/
├── __init__.py                     (2 lines) ✅
├── models.py                       (283 lines) ✅
├── services.py                     (573 lines) ✅
├── serializers.py                  (210 lines) ✅
├── views.py                        (445 lines) ✅
├── urls.py                         (24 lines) ✅
├── admin.py                        (350 lines) ✅
├── signals.py                      (250 lines) ✅
├── apps.py                         (16 lines) ✅
└── management/
    └── commands/
        ├── send_notification.py    (165 lines) ✅
        └── cleanup_notifications.py (140 lines) ✅
```

### Authentication Updates

```
azure_advisor_reports/apps/authentication/
└── models.py                       (+ 111 lines APIKey model) ✅
```

**Total:** 15 new files + 1 updated file
**Total Lines:** ~4,736 lines of production code

---

## 7. Database Migrations Required

### New Models to Migrate

1. **Notifications App:**
   - EmailNotification
   - Webhook
   - WebhookDelivery
   - InAppNotification

2. **Authentication App:**
   - APIKey (added to existing models.py)

### Migration Commands

```bash
# Create migrations
python manage.py makemigrations notifications
python manage.py makemigrations authentication

# Apply migrations
python manage.py migrate notifications
python manage.py migrate authentication

# Verify migrations
python manage.py showmigrations notifications
python manage.py showmigrations authentication
```

### Expected Tables

```
# Notifications
- email_notifications
- webhooks
- webhook_deliveries
- inapp_notifications

# Authentication
- auth_api_key
```

---

## 8. Configuration Required

### 8.1 Django Settings

Add to `settings.py`:

```python
# ============================================================================
# Phase 3: Security & Notifications Configuration
# ============================================================================

# Installed Apps
INSTALLED_APPS = [
    ...
    'apps.notifications',
    'apps.security',
]

# ============================================================================
# Azure Key Vault
# ============================================================================

AZURE_KEY_VAULT_URL = os.getenv('AZURE_KEY_VAULT_URL', '')

# ============================================================================
# Virus Scanning
# ============================================================================

# Scanner type: 'clamav', 'azure_defender', 'disabled'
VIRUS_SCANNER_TYPE = os.getenv('VIRUS_SCANNER_TYPE', 'clamav')

# ClamAV settings
CLAMAV_SOCKET = '/var/run/clamav/clamd.ctl'
CLAMAV_HOST = 'localhost'
CLAMAV_PORT = 3310

# File size limits (100 MB)
MAX_VIRUS_SCAN_SIZE = 100 * 1024 * 1024

# Quarantine settings
QUARANTINE_INFECTED_FILES = True
QUARANTINE_DIR = os.path.join(BASE_DIR, 'quarantine')

# ============================================================================
# Email Configuration
# ============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@example.com')

# Frontend URL for email links
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# ============================================================================
# JWT Token Configuration
# ============================================================================

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ============================================================================
# Middleware
# ============================================================================

MIDDLEWARE = [
    ...
    'apps.security.token_rotation.TokenRotationMiddleware',
]
```

### 8.2 URL Configuration

Add to `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    ...
    path('api/notifications/', include('apps.notifications.urls')),
]
```

### 8.3 Environment Variables

```bash
# Azure Key Vault
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@example.com

# Frontend URL
FRONTEND_URL=https://your-app.azurewebsites.net

# Virus Scanning
VIRUS_SCANNER_TYPE=clamav

# Optional: Azure Storage for Defender
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
```

### 8.4 Azure Resources

1. **Azure Key Vault:**
   ```bash
   # Create Key Vault
   az keyvault create \
     --name your-keyvault \
     --resource-group your-rg \
     --location eastus

   # Grant access
   az keyvault set-policy \
     --name your-keyvault \
     --object-id <app-identity-object-id> \
     --secret-permissions get list set delete
   ```

2. **Azure Defender for Storage:**
   ```bash
   # Enable Defender
   az security pricing create \
     --name StorageAccounts \
     --tier standard
   ```

### 8.5 Cron Jobs / Celery Tasks

Set up scheduled tasks for:

```python
# Celery tasks (recommended)
from celery import shared_task

@shared_task
def cleanup_expired_tokens():
    from apps.security.token_rotation import cleanup_expired_tokens
    cleanup_expired_tokens()

@shared_task
def send_expiry_notifications():
    from apps.security.token_rotation import send_expiry_notifications
    send_expiry_notifications()

@shared_task
def cleanup_old_notifications():
    from apps.notifications.management.commands.cleanup_notifications import Command
    Command().handle(days=90, dry_run=False)

# Celery beat schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-tokens-daily': {
        'task': 'cleanup_expired_tokens',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM daily
    },
    'notify-expiring-keys-daily': {
        'task': 'send_expiry_notifications',
        'schedule': crontab(hour=9, minute=0),  # 9:00 AM daily
    },
    'cleanup-notifications-weekly': {
        'task': 'cleanup_old_notifications',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Sundays at 3:00 AM
    },
}
```

Or use cron:

```bash
# Add to crontab
0 2 * * * cd /path/to/project && python manage.py rotate_tokens --cleanup
0 9 * * * cd /path/to/project && python manage.py rotate_tokens --notify-expiring
0 3 * * 0 cd /path/to/project && python manage.py cleanup_notifications --days 90
```

---

## 9. Testing Recommendations

### 9.1 Unit Tests

Create tests for:

```python
# test_key_vault.py
- Test get_secret() with mock Key Vault
- Test set_secret() and rotate_secret()
- Test caching behavior
- Test error handling

# test_permissions.py
- Test has_permission() for all roles
- Test permission decorators
- Test DRF permission classes
- Test role hierarchy

# test_notifications.py
- Test email sending
- Test webhook triggers
- Test HMAC signature generation
- Test in-app notifications
- Test unified notification service

# test_token_rotation.py
- Test JWT token generation
- Test token rotation
- Test token blacklisting
- Test API key creation and rotation

# test_virus_scanning.py
- Test file scanning with mock scanner
- Test result caching
- Test quarantine functionality
- Test Django validator
```

### 9.2 Integration Tests

```python
# Test notification flow
1. Create report
2. Verify email sent
3. Verify in-app notification created
4. Verify webhook triggered

# Test RBAC enforcement
1. Create users with different roles
2. Attempt operations
3. Verify permission checks
4. Test object-level permissions

# Test token rotation
1. Generate tokens
2. Wait for rotation interval
3. Use refresh token
4. Verify new tokens issued
5. Verify old token blacklisted
```

### 9.3 Manual Testing

```bash
# Test Key Vault
curl -X GET http://localhost:8000/api/health/ \
  -H "Authorization: Bearer $TOKEN"

# Test notifications
python manage.py send_notification \
  --username testuser \
  --title "Test" \
  --message "Test message"

# Test virus scanning
curl -X POST http://localhost:8000/api/reports/upload-csv/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.csv"

# Test webhook
curl -X POST http://localhost:8000/api/notifications/webhooks/test/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"webhook_id": "uuid"}'
```

---

## 10. Next Steps

### 10.1 Immediate Tasks

1. **Run Migrations:**
   ```bash
   python manage.py makemigrations notifications authentication
   python manage.py migrate
   ```

2. **Configure Services:**
   - Set up Azure Key Vault
   - Configure email settings
   - Install and configure ClamAV or Azure Defender

3. **Update Settings:**
   - Add new apps to INSTALLED_APPS
   - Configure JWT settings
   - Add notification URLs

4. **Create Email Templates:**
   ```
   templates/emails/
   ├── report_completed.html
   ├── report_completed.txt
   ├── report_failed.html
   ├── report_failed.txt
   ├── welcome.html
   └── welcome.txt
   ```

5. **Set Up Scheduled Tasks:**
   - Configure Celery beat or cron jobs
   - Test scheduled task execution

### 10.2 Integration with Existing Code

1. **Update CSV Upload View:**
   ```python
   from apps.security.virus_scanning import VirusScanner

   def upload_csv(request):
       uploaded_file = request.FILES['file']

       # Scan file
       scan_result = VirusScanner.scan_upload(uploaded_file)
       if scan_result.is_infected:
           return JsonResponse({
               'error': f'Virus detected: {scan_result.threat_name}'
           }, status=400)

       # Process file
       ...
   ```

2. **Update Authentication Views:**
   ```python
   from apps.security.token_rotation import JWTTokenRotation

   class LoginView(APIView):
       def post(self, request):
           # Authenticate user
           user = authenticate(...)

           # Generate tokens
           tokens = JWTTokenRotation.generate_tokens(user)

           return Response(tokens)
   ```

3. **Update ViewSets with Permissions:**
   ```python
   from apps.security.permissions import IsManager, ResourcePermission

   class ClientViewSet(viewsets.ModelViewSet):
       permission_classes = [IsManager]
       queryset = Client.objects.all()
   ```

### 10.3 Documentation Tasks

1. **Create API Documentation:**
   - Document notification endpoints
   - Document webhook payload formats
   - Document permission requirements

2. **Create User Guides:**
   - How to manage webhooks
   - How to generate API keys
   - How to configure notifications

3. **Create Admin Guide:**
   - Key Vault setup instructions
   - ClamAV installation guide
   - Scheduled task configuration

### 10.4 Testing Tasks

1. **Write Unit Tests:**
   - Security module tests (80% coverage target)
   - Notification module tests (80% coverage target)

2. **Write Integration Tests:**
   - End-to-end notification flow
   - Permission enforcement
   - Token rotation flow

3. **Security Testing:**
   - Penetration testing for RBAC
   - Test token blacklisting
   - Test virus scanning bypass attempts

### 10.5 Deployment Preparation

1. **Create Deployment Checklist:**
   - [ ] Azure Key Vault configured
   - [ ] Email service configured
   - [ ] ClamAV installed or Azure Defender enabled
   - [ ] Migrations applied
   - [ ] Environment variables set
   - [ ] Scheduled tasks configured
   - [ ] Email templates created
   - [ ] Webhook endpoints tested
   - [ ] Security scan passed
   - [ ] Load testing completed

2. **Update Bicep Templates:**
   - Add Key Vault resource
   - Add Managed Identity
   - Add Defender for Storage
   - Add environment variables

3. **Create Rollback Plan:**
   - Document migration rollback steps
   - Backup notification data
   - Test rollback procedures

---

## Summary

Phase 3 has successfully implemented comprehensive security and notification features:

### ✅ Completed Features

1. **Azure Key Vault Integration** (412 lines)
   - Secure secrets management
   - Automatic rotation support
   - Caching for performance

2. **RBAC System** (530 lines)
   - Four-tier role hierarchy
   - Granular permissions
   - DRF integration

3. **Notification System** (2,450 lines)
   - Email notifications
   - Webhook system with HMAC
   - In-app notifications
   - Automatic triggers
   - REST API
   - Admin interface

4. **Token Rotation** (550 lines)
   - JWT token rotation
   - API key rotation
   - Expiry notifications
   - Automatic cleanup

5. **Virus Scanning** (580 lines)
   - ClamAV support
   - Azure Defender support
   - Result caching
   - Automatic quarantine

### 📊 Statistics

- **Total Files Created:** 15 files
- **Total Files Updated:** 1 file
- **Total Lines of Code:** ~4,736 lines
- **New Database Tables:** 5 tables
- **REST API Endpoints:** 20+ endpoints
- **Management Commands:** 3 commands

### 🎯 Impact

- **Security:** Enhanced with multi-layered protection
- **User Experience:** Proactive notifications
- **Compliance:** Audit trail and access control
- **Integration:** Webhook support for external systems
- **Reliability:** Automatic token rotation and virus scanning

### 📝 Next Phase

With Phase 3 complete, all major features have been implemented. The next steps are:

1. **Testing & Quality Assurance:**
   - Comprehensive test suite
   - Load testing
   - Security audit

2. **Deployment:**
   - Production deployment
   - Monitoring setup
   - Performance optimization

3. **Documentation:**
   - Complete user documentation
   - Admin guides
   - API documentation

---

**Phase 3 Status:** ✅ **COMPLETE**
**Ready for:** Testing, Integration, and Deployment
