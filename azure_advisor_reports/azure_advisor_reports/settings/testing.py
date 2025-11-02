"""
Django testing settings for azure_advisor_reports project.

This file is used exclusively for running tests (pytest, Django test runner).
It uses SQLite in-memory database and simplified configuration for fast test execution.

Usage:
    pytest --ds=azure_advisor_reports.settings.testing
    python manage.py test --settings=azure_advisor_reports.settings.testing
"""

from .base import *

# ============================================================================
# SECURITY SETTINGS
# ============================================================================

SECRET_KEY = 'test-secret-key-not-for-production'
DEBUG = True
ALLOWED_HOSTS = ['*']

# ============================================================================
# DATABASE CONFIGURATION - SQLite for Testing
# ============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'ATOMIC_REQUESTS': True,
    }
}

# ============================================================================
# CACHE CONFIGURATION - Local Memory Cache for Testing
# ============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# ============================================================================
# CELERY CONFIGURATION - Eager Execution for Testing
# ============================================================================

# Execute tasks synchronously (no broker needed)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Use in-memory broker for tests
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# ============================================================================
# EMAIL CONFIGURATION - Console Backend for Testing
# ============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ============================================================================
# PASSWORD HASHING - Fast Hasher for Testing
# ============================================================================

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# ============================================================================
# LOGGING CONFIGURATION - Minimal Logging for Tests
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'console': {
            'level': 'CRITICAL',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'CRITICAL',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'CRITICAL',
            'propagate': False,
        },
    },
}

# ============================================================================
# STORAGE CONFIGURATION - Local Storage for Testing
# ============================================================================

# Use local file storage instead of Azure Blob Storage
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# ============================================================================
# SECURITY SETTINGS - Disabled for Testing
# ============================================================================

# Disable security features that slow down tests
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ============================================================================
# CORS SETTINGS - Permissive for Testing
# ============================================================================

CORS_ALLOWED_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
CORS_ALLOW_CREDENTIALS = True

# ============================================================================
# ADDITIONAL TEST SETTINGS
# ============================================================================

# Disable migrations for faster test database creation
# Uncomment if you want to use --nomigrations for faster tests
# class DisableMigrations:
#     def __contains__(self, item):
#         return True
#     def __getitem__(self, item):
#         return None
# MIGRATION_MODULES = DisableMigrations()

# Disable whitenoise for tests (faster)
MIDDLEWARE = [m for m in MIDDLEWARE if 'whitenoise' not in m.lower()]
