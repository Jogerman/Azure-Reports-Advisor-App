"""
Django settings for azure_advisor_reports project.

Generated for Django 4.2.7

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

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

# Use SQLite for testing to avoid PostgreSQL dependency
if 'test' in sys.argv or 'pytest' in sys.modules:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    # Try DATABASE_URL first (for production), fallback to individual vars (for local dev)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        DATABASES = {
            'default': dj_database_url.parse(database_url)
        }
    else:
        # Fallback to individual env vars
        # Try os.environ first, then config (for local .env file)
        db_name = os.environ.get('DB_NAME')
        if not db_name:
            try:
                db_name = config('DB_NAME', default='azure_advisor_reports')
            except Exception as e:
                print(f"WARNING: config('DB_NAME') failed: {e}")
                db_name = 'azure_advisor_reports'

        db_user = os.environ.get('DB_USER')
        if not db_user:
            try:
                db_user = config('DB_USER', default='postgres')
            except Exception as e:
                print(f"WARNING: config('DB_USER') failed: {e}")
                db_user = 'postgres'

        db_password = os.environ.get('DB_PASSWORD')
        if not db_password:
            try:
                db_password = config('DB_PASSWORD', default='postgres')
            except Exception as e:
                print(f"WARNING: config('DB_PASSWORD') failed: {e}")
                db_password = 'postgres'

        db_host = os.environ.get('DB_HOST')
        if not db_host:
            try:
                db_host = config('DB_HOST', default='localhost')
            except Exception as e:
                print(f"WARNING: config('DB_HOST') failed: {e}")
                db_host = 'localhost'

        db_port = os.environ.get('DB_PORT')
        if not db_port:
            try:
                db_port = config('DB_PORT', default='5432')
            except Exception as e:
                print(f"WARNING: config('DB_PORT') failed: {e}")
                db_port = '5432'

        # Debug logging for database configuration
        print(f"DATABASE CONFIG - Name: {db_name}, User: {db_user}, Host: {db_host}, Port: {db_port}")
        print(f"DATABASE CONFIG - Password set: {bool(db_password)}")

        # Ensure all values are strings and not None
        if not all([db_name, db_user, db_password, db_host, db_port]):
            print(f"ERROR: Missing database configuration!")
            print(f"  DB_NAME: {db_name}")
            print(f"  DB_USER: {db_user}")
            print(f"  DB_PASSWORD: {'SET' if db_password else 'NOT SET'}")
            print(f"  DB_HOST: {db_host}")
            print(f"  DB_PORT: {db_port}")
            # Don't fail, use defaults
            db_name = db_name or 'azure_advisor_reports'
            db_user = db_user or 'postgres'
            db_password = db_password or 'postgres'
            db_host = db_host or 'localhost'
            db_port = db_port or '5432'

        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': str(db_name),
                'USER': str(db_user),
                'PASSWORD': str(db_password),
                'HOST': str(db_host),
                'PORT': str(db_port),
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

# Azure AD Configuration
AZURE_AD = {
    'CLIENT_ID': config('AZURE_CLIENT_ID', default=''),
    'CLIENT_SECRET': config('AZURE_CLIENT_SECRET', default=''),
    'TENANT_ID': config('AZURE_TENANT_ID', default=''),
    'REDIRECT_URI': config('AZURE_REDIRECT_URI', default='http://localhost:3000'),
    'SCOPE': ['openid', 'profile', 'email'],
    'AUTHORITY': f"https://login.microsoftonline.com/{config('AZURE_TENANT_ID', default='')}",
}

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Cache Configuration
if 'test' in sys.argv or 'pytest' in sys.modules:
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
            'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
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

# CSV Upload and Validation Settings
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB maximum file size
ALLOWED_CSV_EXTENSIONS = ['.csv', '.CSV']  # Allowed file extensions
CSV_MAX_ROWS = 10000  # Maximum number of rows in CSV
CSV_ENCODING_OPTIONS = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'windows-1252']  # Encoding options to try

# Logging Configuration
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
# PDF_ENGINE: Choose the PDF generation engine
#   - 'playwright': Use Playwright headless browser (modern, supports Chart.js)
#   - 'weasyprint': Use WeasyPrint (legacy, limited CSS support)
PDF_ENGINE = config('PDF_ENGINE', default='playwright').lower()

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