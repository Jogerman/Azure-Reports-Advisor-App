"""
Django production settings for azure_advisor_reports project.

This file contains all production-specific settings including security hardening,
Azure service configuration, and performance optimizations.

IMPORTANT: All sensitive values must be set via environment variables.
"""

from .base import *
from decouple import config
import dj_database_url

# ============================================================================
# SECURITY SETTINGS
# ============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Allowed hosts - must be configured for production
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Security middleware settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 24 hours

# CSRF security
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)

# Browser security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS settings (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security Policy (optional but recommended)
# CSP_DEFAULT_SRC = ("'self'",)
# CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
# CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
# CSP_IMG_SRC = ("'self'", "data:", "https:")

# ============================================================================
# CORS CONFIGURATION
# ============================================================================

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ============================================================================
# DATABASE CONFIGURATION - Azure PostgreSQL
# ============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': 'require',  # Required for Azure PostgreSQL
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 600,  # Connection pooling (10 minutes)
        'ATOMIC_REQUESTS': True,  # Wrap each request in a transaction
    }
}

# ============================================================================
# CACHE CONFIGURATION - Azure Redis
# ============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': config('REDIS_PASSWORD', default=''),
            'SSL': True,
            'SSL_CERT_REQS': None,  # Azure Redis uses SSL
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,  # Don't crash on cache failures
        },
        'KEY_PREFIX': 'azure_advisor_reports_prod',
        'TIMEOUT': 900,  # 15 minutes default
    }
}

# Celery broker - use Redis
CELERY_BROKER_URL = config('REDIS_URL')
CELERY_RESULT_BACKEND = config('REDIS_URL')
CELERY_BROKER_USE_SSL = {
    'ssl_cert_reqs': None  # Azure Redis SSL configuration
}
CELERY_REDIS_BACKEND_USE_SSL = {
    'ssl_cert_reqs': None
}

# ============================================================================
# STATIC FILES - Azure Blob Storage
# ============================================================================

# Use Azure Blob Storage for static files in production
DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
STATICFILES_STORAGE = 'storages.backends.azure_storage.AzureStorage'

AZURE_ACCOUNT_NAME = config('AZURE_STORAGE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = config('AZURE_STORAGE_ACCOUNT_KEY')
AZURE_CONTAINER = config('AZURE_STORAGE_CONTAINER', default='static')
AZURE_CUSTOM_DOMAIN = f'{AZURE_ACCOUNT_NAME}.blob.core.windows.net'
AZURE_SSL = True

# Override static URL to use Azure Blob Storage
STATIC_URL = f'https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER}/static/'
MEDIA_URL = f'https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER}/media/'

# ============================================================================
# AZURE AD CONFIGURATION
# ============================================================================

AZURE_AD = {
    'CLIENT_ID': config('AZURE_CLIENT_ID'),
    'CLIENT_SECRET': config('AZURE_CLIENT_SECRET'),
    'TENANT_ID': config('AZURE_TENANT_ID'),
    'REDIRECT_URI': config('AZURE_REDIRECT_URI'),
    'SCOPE': ['openid', 'profile', 'email'],
    'AUTHORITY': f"https://login.microsoftonline.com/{config('AZURE_TENANT_ID')}",
}

# ============================================================================
# LOGGING CONFIGURATION - Application Insights
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'production.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'azure': {
            'level': 'INFO',
            'class': 'opencensus.ext.azure.log_exporter.AzureLogHandler',
            'connection_string': config('APPLICATIONINSIGHTS_CONNECTION_STRING', default=''),
        },
        'azure_errors': {
            'level': 'ERROR',
            'class': 'opencensus.ext.azure.log_exporter.AzureLogHandler',
            'connection_string': config('APPLICATIONINSIGHTS_CONNECTION_STRING', default=''),
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
            'include_html': True,
        },
    },
    'root': {
        'handlers': ['console', 'file', 'azure'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'azure'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file', 'azure_errors', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'file', 'azure_errors', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file', 'azure'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file', 'azure'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================================================
# EMAIL CONFIGURATION (for error notifications)
# ============================================================================

# Configure these if you want email notifications for errors
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
# EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
# DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@azureadvisorreports.com')
# SERVER_EMAIL = config('SERVER_EMAIL', default='server@azureadvisorreports.com')

# Admin email addresses for error notifications
# ADMINS = [
#     ('Admin Name', 'admin@example.com'),
# ]
# MANAGERS = ADMINS

# ============================================================================
# RATE LIMITING - Production
# ============================================================================

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/hour',
    'user': '1000/hour',
    'report_generation': '10/hour',  # Limit report generation
    'csv_upload': '20/hour',  # Limit CSV uploads
}

# ============================================================================
# MONITORING & PERFORMANCE
# ============================================================================

# Application Insights instrumentation key
APPLICATIONINSIGHTS_CONNECTION_STRING = config(
    'APPLICATIONINSIGHTS_CONNECTION_STRING',
    default=''
)

# Enable slow query logging
# LOGGING['loggers']['django.db.backends'] = {
#     'handlers': ['console', 'azure'],
#     'level': 'DEBUG',
#     'propagate': False,
# }

# Data upload size limits (production)
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB

# ============================================================================
# CELERY - Production Settings
# ============================================================================

# Celery task result expiration (7 days)
CELERY_RESULT_EXPIRES = 604800

# Task compression
CELERY_TASK_COMPRESSION = 'gzip'
CELERY_RESULT_COMPRESSION = 'gzip'

# Worker settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# ============================================================================
# ADDITIONAL SECURITY SETTINGS
# ============================================================================

# Prevent clickjacking
X_FRAME_OPTIONS = 'DENY'

# Force password change for inactive accounts (optional)
# PASSWORD_HASHERS = [
#     'django.contrib.auth.hashers.Argon2PasswordHasher',
#     'django.contrib.auth.hashers.PBKDF2PasswordHasher',
#     'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
#     'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
# ]

# Session security
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ============================================================================
# GZIP COMPRESSION
# ============================================================================

# Add GZip middleware (should be first in MIDDLEWARE)
MIDDLEWARE = ['django.middleware.gzip.GZipMiddleware'] + MIDDLEWARE

# ============================================================================
# PRODUCTION CHECKLIST SETTINGS
# ============================================================================

# These settings should be verified before deployment:
# 1. SECRET_KEY is set to a strong random value
# 2. DEBUG is False
# 3. ALLOWED_HOSTS is set correctly
# 4. All Azure credentials are configured
# 5. HTTPS is enforced
# 6. Database backups are configured
# 7. Application Insights is configured
# 8. Redis cache is accessible
# 9. Blob storage is configured
# 10. Celery workers are running

# Run Django's system check for production readiness:
# python manage.py check --deploy --settings=azure_advisor_reports.settings.production
