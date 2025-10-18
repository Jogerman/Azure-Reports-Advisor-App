"""
Django development settings for azure_advisor_reports project.

This file contains all development-specific settings.
Use this for local development only.
"""

from .base import *
from decouple import config

# ============================================================================
# BASIC SETTINGS
# ============================================================================

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

DEBUG = True

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

import sys

# Use SQLite for testing to avoid PostgreSQL dependency
if 'test' in sys.argv or 'pytest' in sys.modules:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='azure_advisor_reports'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'azure_advisor_reports_dev',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# ============================================================================
# CELERY CONFIGURATION
# ============================================================================

CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')

# ============================================================================
# CORS CONFIGURATION
# ============================================================================

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
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
# AZURE AD CONFIGURATION
# ============================================================================

AZURE_AD = {
    'CLIENT_ID': config('AZURE_CLIENT_ID', default=''),
    'CLIENT_SECRET': config('AZURE_CLIENT_SECRET', default=''),
    'TENANT_ID': config('AZURE_TENANT_ID', default=''),
    'REDIRECT_URI': config('AZURE_REDIRECT_URI', default='http://localhost:3000'),
    'SCOPE': ['openid', 'profile', 'email'],
    'AUTHORITY': f"https://login.microsoftonline.com/{config('AZURE_TENANT_ID', default='')}",
}

# ============================================================================
# AZURE STORAGE CONFIGURATION
# ============================================================================

AZURE_ACCOUNT_NAME = config('AZURE_ACCOUNT_NAME', default='')
AZURE_ACCOUNT_KEY = config('AZURE_ACCOUNT_KEY', default='')
AZURE_CONTAINER = config('AZURE_CONTAINER', default='reports')

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

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
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
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
    },
}

# ============================================================================
# DEVELOPMENT TOOLS
# ============================================================================

# Add development-specific apps
INSTALLED_APPS += [
    'django_extensions',
]

# Disable Celery beat for local development (optional)
# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_TASK_EAGER_PROPAGATES = True

# ============================================================================
# DEBUG TOOLBAR (Optional)
# ============================================================================

# Temporarily disabled due to namespace issues
# if DEBUG:
#     INSTALLED_APPS += ['debug_toolbar']
#     MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
#     INTERNAL_IPS = ['127.0.0.1', 'localhost']
#
#     DEBUG_TOOLBAR_CONFIG = {
#         'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
#     }
