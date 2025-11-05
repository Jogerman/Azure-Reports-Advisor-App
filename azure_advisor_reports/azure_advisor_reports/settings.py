"""
Django settings for azure_advisor_reports project.

Generated for Django 4.2.7

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
import sys
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# SECRET_KEY Configuration - CRITICAL SECURITY
# ============================================================================
# SECURITY WARNING: SECRET_KEY must be set in environment variables
# Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(50))'

# Remove default - force SECRET_KEY to be set
try:
    SECRET_KEY = config('SECRET_KEY')
except Exception:
    raise ValueError(
        "SECRET_KEY must be set in environment variables. "
        "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(50))'"
    )

# Validate SECRET_KEY strength
# Skip validation only for Django management commands that don't need security
MANAGEMENT_COMMANDS_SKIP_VALIDATION = ['migrate', 'makemigrations', 'collectstatic', 'showmigrations', 'sqlmigrate']
should_validate_secret = not any(cmd in sys.argv for cmd in MANAGEMENT_COMMANDS_SKIP_VALIDATION)

if should_validate_secret:
    if SECRET_KEY == 'django-insecure-change-this-in-production':
        raise ValueError(
            "Default SECRET_KEY detected. This is a critical security vulnerability. "
            "Set a cryptographically secure SECRET_KEY in environment variables."
        )

    if len(SECRET_KEY) < 50:
        raise ValueError(
            f"SECRET_KEY must be at least 50 characters long (current: {len(SECRET_KEY)}). "
            "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(50))'"
        )

# Add secret rotation support
# Multiple keys can be specified for zero-downtime rotation
# Format: FALLBACK_KEY_1,FALLBACK_KEY_2,...
SECRET_KEY_FALLBACKS = config(
    'SECRET_KEY_FALLBACKS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)

# SECURITY WARNING: don't run with debug turned on in production!
# Read DEBUG from environment - default to False in production
DEBUG = config('DEBUG', default='True', cast=lambda x: x.lower() in ('true', '1', 'yes', 'on'))

# Force DEBUG to False if DJANGO_ENVIRONMENT is production
if os.environ.get('DJANGO_ENVIRONMENT', '').lower() == 'production':
    DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Additional CSRF configuration for production
if not DEBUG:
    # Ensure Azure Container Apps URLs are always trusted in production
    production_origins = [
        'https://advisor-reports-backend.nicefield-788f351e.eastus.azurecontainerapps.io',
        'https://advisor-reports-frontend.nicefield-788f351e.eastus.azurecontainerapps.io',
    ]
    # Merge with existing trusted origins (avoid duplicates)
    CSRF_TRUSTED_ORIGINS = list(set(CSRF_TRUSTED_ORIGINS + production_origins))

# Custom User Model
AUTH_USER_MODEL = 'authentication.User'

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'django_filters',
    # Celery apps disabled for testing to avoid dependency issues
    # 'django_celery_beat',
    # 'django_celery_results',
]

LOCAL_APPS = [
    'apps.core',
    'apps.authentication',
    'apps.clients',
    'apps.reports',
    'apps.analytics',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'azure_advisor_reports.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'azure_advisor_reports.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
import sys

# IMPORTANT: Only use SQLite for actual test execution via pytest command
# NEVER use 'pytest' in sys.modules check - it's unreliable and causes Celery failures!
# The sys.modules check can randomly trigger in production when pytest is imported by dependencies
if 'test' in sys.argv:
    # Only when explicitly running: python manage.py test
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    # Normal operation: Use PostgreSQL (production/development) or environment-based config
    # Try DATABASE_URL first (for production), fallback to individual vars (for local dev)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        DATABASES = {
            'default': dj_database_url.parse(database_url)
        }
    else:
        # Fallback to individual env vars with safe retrieval
        # Priority: os.environ > config() > default
        # This approach ensures Celery workers (which may have issues with config())
        # will always work if environment variables are set in Azure Container Apps
        def get_db_config(key, default):
            """Safely get database config with proper fallback chain."""
            # First check os.environ directly (works in all contexts)
            value = os.environ.get(key)
            if value is not None:
                return value
            # Try config() for local development with .env files
            try:
                return config(key, default=default)
            except Exception:
                # If config() fails (e.g., in Celery workers), use default
                return default

        db_name = get_db_config('DB_NAME', 'azure_advisor_reports')
        db_user = get_db_config('DB_USER', 'postgres')
        db_password = get_db_config('DB_PASSWORD', 'postgres')
        db_host = get_db_config('DB_HOST', 'localhost')
        db_port = get_db_config('DB_PORT', '5432')

        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': db_name,
                'USER': db_user,
                'PASSWORD': db_password,
                'HOST': db_host,
                'PORT': db_port,
            }
        }

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.authentication.authentication.JWTAuthentication',  # Backend-generated JWT tokens (primary)
        'apps.authentication.authentication.AzureADAuthentication',  # Azure AD tokens (for login)
        'rest_framework.authentication.SessionAuthentication',  # Django session (fallback)
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FileUploadParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}

# Log the configured authentication classes to verify settings are loaded
import logging
settings_logger = logging.getLogger('django.settings')
settings_logger.critical("=" * 80)
settings_logger.critical(f"REST_FRAMEWORK DEFAULT_AUTHENTICATION_CLASSES configured:")
for idx, auth_class in enumerate(REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'], 1):
    settings_logger.critical(f"  {idx}. {auth_class}")
settings_logger.critical("=" * 80)

# CORS Settings
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

CORS_ALLOW_CREDENTIALS = True

# Azure AD Configuration (Security Enhanced)
AZURE_AD = {
    'CLIENT_ID': config('AZURE_CLIENT_ID', default=''),
    'CLIENT_SECRET': config('AZURE_CLIENT_SECRET', default=''),
    'TENANT_ID': config('AZURE_TENANT_ID', default=''),
    'REDIRECT_URI': config('AZURE_REDIRECT_URI', default='http://localhost:3000'),
    'SCOPE': ['openid', 'profile', 'email'],
    'AUTHORITY': f"https://login.microsoftonline.com/{config('AZURE_TENANT_ID', default='')}",
    'REQUIRE_ID_TOKEN': config('AZURE_REQUIRE_ID_TOKEN', default=True, cast=bool),
}

# Validate Azure AD configuration on startup (non-management commands)
if should_validate_secret and not all([AZURE_AD['CLIENT_ID'], AZURE_AD['TENANT_ID']]):
    logger.warning("Azure AD configuration incomplete - authentication will fail")

# Celery Configuration
# Use same safe config pattern for Celery workers
def get_celery_config(key, default):
    """Safely get Celery config with proper fallback chain."""
    value = os.environ.get(key)
    if value is not None:
        return value
    try:
        return config(key, default=default)
    except Exception:
        return default

CELERY_BROKER_URL = get_celery_config('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = get_celery_config('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Cache Configuration
# IMPORTANT: Only use dummy cache for actual test execution
# NEVER use 'pytest' in sys.modules - it causes Celery failures!
if 'test' in sys.argv:
    # Use dummy cache for testing (no Redis dependency)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-cache',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': get_celery_config('REDIS_URL', 'redis://localhost:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'azure_advisor_reports',
            'TIMEOUT': 300,  # 5 minutes default
        }
    }

# Azure Storage Configuration
AZURE_ACCOUNT_NAME = config('AZURE_ACCOUNT_NAME', default='')
AZURE_ACCOUNT_KEY = config('AZURE_ACCOUNT_KEY', default='')
AZURE_CONTAINER = config('AZURE_CONTAINER', default='reports')

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
FILE_UPLOAD_PERMISSIONS = 0o644

# CSV Upload and Validation Settings (Security Enhanced)
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB maximum file size
ALLOWED_CSV_EXTENSIONS = ['.csv']  # Allowed file extensions (lowercase only for security)
ALLOWED_CSV_MIMETYPES = ['text/csv', 'application/csv', 'text/plain', 'application/vnd.ms-excel', 'text/x-csv']
CSV_MAX_ROWS = 100000  # Maximum number of rows in CSV (increased for large datasets)
CSV_MAX_CELL_SIZE = 10000  # Maximum characters per cell (prevents DoS)
CSV_ENCODING_OPTIONS = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'windows-1252']  # Encoding options to try

# ============================================================================
# Logging Configuration - Security Enhanced
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
        'security': {
            'format': '{levelname} {asctime} {module} {message}',
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
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'security',
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
        'security': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# ============================================================================
# Rate Limiting Configuration - CRITICAL SECURITY
# ============================================================================
# django-ratelimit is already installed in requirements.txt
RATELIMIT_ENABLE = config('RATELIMIT_ENABLE', default=True, cast=bool)
RATELIMIT_USE_CACHE = 'default'

# Custom 429 handler for rate limiting
# Will be implemented in apps.core.views.ratelimit_error
# RATELIMIT_VIEW = 'apps.core.views.ratelimit_error'

# Security Settings
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'

# Development Settings
if DEBUG:
    INSTALLED_APPS += ['django_extensions']

# Create logs directory
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# ============================================================================
# PDF Generation Settings
# ============================================================================
# PDF generation uses a dual-engine approach with automatic fallback:
#   1. PRIMARY: Playwright headless browser (modern, supports Chart.js, best quality)
#   2. FALLBACK: WeasyPrint (legacy, limited CSS but reliable)
#
# The system will automatically try Playwright first, and if it fails,
# will fall back to WeasyPrint to ensure PDF generation always succeeds.
#
# Note: PDF_ENGINE setting is deprecated but kept for backward compatibility
PDF_ENGINE = config('PDF_ENGINE', default='playwright').lower()  # Deprecated: now uses auto-fallback

# Playwright PDF Settings
PLAYWRIGHT_PDF_OPTIONS = {
    'format': 'A4',
    'print_background': True,  # Python Playwright uses snake_case
    'display_header_footer': True,
    'margin': {
        'top': '25mm',
        'right': '15mm',
        'bottom': '25mm',
        'left': '15mm',
    },
    'prefer_css_page_size': False,
    'timeout': 30000,  # 30 seconds timeout
}

# PDF Generation Features
PDF_WAIT_FOR_CHARTS = config('PDF_WAIT_FOR_CHARTS', default=True, cast=bool)
PDF_WAIT_FOR_FONTS = config('PDF_WAIT_FOR_FONTS', default=True, cast=bool)
PDF_HEADLESS_BROWSER = config('PDF_HEADLESS_BROWSER', default=True, cast=bool)