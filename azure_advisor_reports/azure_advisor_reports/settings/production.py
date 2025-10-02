"""
Production settings for azure_advisor_reports project.

This file contains settings specific to the production environment.
"""

from .base import *
from decouple import config
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Production allowed hosts (should be set via environment variable)
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_PRELOAD = True
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS and security headers
USE_TLS = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Session security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600  # 1 hour

# CSRF security
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_USE_SESSIONS = True

# CORS settings for production (restrictive)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)
CORS_ALLOW_CREDENTIALS = True

# Database settings for production
DATABASES['default'].update({
    'OPTIONS': {
        'sslmode': 'require',
        'connect_timeout': 10,
    },
    'CONN_MAX_AGE': 600,  # 10 minutes
})

# Production file storage (Azure Blob Storage)
if config('AZURE_STORAGE_CONNECTION_STRING', default=''):
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    AZURE_CONNECTION_STRING = config('AZURE_STORAGE_CONNECTION_STRING')
    AZURE_CONTAINER = config('AZURE_CONTAINER', default='media')
    AZURE_CUSTOM_DOMAIN = config('AZURE_CUSTOM_DOMAIN', default=None)

# Static files storage for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Email settings for production
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend'
)

if 'smtp' in EMAIL_BACKEND.lower():
    EMAIL_HOST = config('EMAIL_HOST')
    EMAIL_PORT = config('EMAIL_PORT', cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)

# Celery settings for production
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_WORKER_CONCURRENCY = config('CELERY_WORKER_CONCURRENCY', default=4, cast=int)
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes

# Cache settings for production
CACHES['default'].update({
    'TIMEOUT': 3600,  # 1 hour default
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        'CONNECTION_POOL_KWARGS': {
            'max_connections': 50,
            'retry_on_timeout': True,
        },
        'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
    },
})

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "{levelname}", "time": "{asctime}", "module": "{module}", "message": "{message}"}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'production.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'error.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Sentry configuration for error tracking
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_spans=True,
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,
                propagate_traces=True,
            ),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        send_default_pii=False,
        attach_stacktrace=True,
        environment=config('DJANGO_ENVIRONMENT', default='production'),
    )

# Application Insights integration
APPINSIGHTS_INSTRUMENTATION_KEY = config('APPINSIGHTS_INSTRUMENTATION_KEY', default='')
if APPINSIGHTS_INSTRUMENTATION_KEY:
    INSTALLED_APPS += ['applicationinsights.django']
    MIDDLEWARE += ['applicationinsights.django.ApplicationInsightsMiddleware']
    APPLICATION_INSIGHTS = {
        'ikey': APPINSIGHTS_INSTRUMENTATION_KEY,
    }

# Performance optimizations
CONN_MAX_AGE = 600  # Database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = CONN_MAX_AGE

# File upload restrictions for production
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Admin security
ADMIN_URL = config('ADMIN_URL', default='admin/')

# Rate limiting (if implemented)
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Backup configuration
BACKUP_ENABLED = config('BACKUP_ENABLED', default=True, cast=bool)
BACKUP_RETENTION_DAYS = config('BACKUP_RETENTION_DAYS', default=30, cast=int)

# Health check settings
HEALTH_CHECK_ENABLED = True
HEALTH_CHECK_URL = 'health/'

# Monitoring settings
MONITORING_ENABLED = True
METRICS_COLLECTION_INTERVAL = 60  # seconds

# Content Security Policy (if django-csp is installed)
CSP_DEFAULT_SRC = ["'self'"]
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'"]
CSP_SCRIPT_SRC = ["'self'"]
CSP_IMG_SRC = ["'self'", "data:", "https:"]
CSP_FONT_SRC = ["'self'", "https:"]
CSP_CONNECT_SRC = ["'self'"]
CSP_FRAME_SRC = ["'none'"]
CSP_OBJECT_SRC = ["'none'"]
CSP_BASE_URI = ["'self'"]
CSP_FORM_ACTION = ["'self'"]