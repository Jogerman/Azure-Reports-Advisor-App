"""
Development settings for azure_advisor_reports project.

This file contains settings specific to the development environment.
"""

from .base import *
from decouple import config

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allowed hosts for development
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Development-specific apps
INSTALLED_APPS += [
    'django_extensions',
]

# Enable debug toolbar if requested
if config('ENABLE_DEBUG_TOOLBAR', default=False, cast=bool):
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

    # Debug toolbar configuration
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
        'SHOW_TEMPLATE_CONTEXT': True,
    }

    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]

# CORS settings for development (more permissive)
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=True, cast=bool)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
]

# Email backend for development (console output)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery settings for development
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=False, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = config('CELERY_TASK_EAGER_PROPAGATES', default=True, cast=bool)

# Logging Configuration for Development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'colored': {
            'format': '{levelname} {asctime} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'development.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Reduce noise from some third-party libraries
        'urllib3': {
            'level': 'WARNING',
        },
        'requests': {
            'level': 'WARNING',
        },
    },
}

# Disable password validation for development (optional)
AUTH_PASSWORD_VALIDATORS = []

# Development database optimizations
DATABASES['default'].update({
    'OPTIONS': {
        'sslmode': 'prefer',  # Less strict SSL for local development
    },
    'CONN_MAX_AGE': 60,  # Keep connections alive for 60 seconds
})

# Development cache settings (use dummy cache if Redis not available)
try:
    import redis
    redis.Redis.from_url(CACHES['default']['LOCATION']).ping()
except:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

# Development file storage (local filesystem)
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Security settings (relaxed for development)
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_SECONDS = 0
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Django Extensions settings
if 'django_extensions' in INSTALLED_APPS:
    SHELL_PLUS = 'ipython'
    SHELL_PLUS_PRE_IMPORTS = [
        ('apps.authentication.models', 'User'),
        ('apps.clients.models', 'Client'),
        ('apps.reports.models', 'Report', 'Recommendation'),
    ]

# Override any production-specific settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB for development testing
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB for development testing