"""
Django base settings for azure_advisor_reports project.

This file contains settings common to all environments.
Environment-specific settings should be in development.py, staging.py, or production.py
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

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
    'django_celery_beat',
    'django_celery_results',
    'drf_spectacular',  # OpenAPI schema generation
]

LOCAL_APPS = [
    'apps.core',
    'apps.authentication',
    'apps.clients',
    'apps.azure_integration',
    'apps.reports',
    'apps.analytics',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'azure_advisor_reports.middleware.SecurityHeadersMiddleware',  # Custom security headers for Azure AD
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static file serving
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

# Use WhiteNoise for static file compression and caching
# Using CompressedStaticFilesStorage instead of CompressedManifestStaticFilesStorage
# to avoid strict manifest mode failures for dynamically referenced files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

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
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'azure_api': '100/hour',  # Azure API operations
        'azure_connection_test': '20/hour',  # Connection tests
        'azure_sync': '50/hour',  # Sync operations
        'report_creation': '100/day',  # Report creation
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',  # OpenAPI schema generation
}

# drf-spectacular settings for API documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Azure Advisor Reports API',
    'DESCRIPTION': 'REST API for managing Azure Advisor reports with dual data sources (CSV upload and Azure API integration)',
    'VERSION': '2.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/v1',
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
}

# Celery Configuration (base settings)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
FILE_UPLOAD_PERMISSIONS = 0o644

# CSV Upload and Validation Settings
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB maximum file size
ALLOWED_CSV_EXTENSIONS = ['.csv', '.CSV']  # Allowed file extensions
CSV_MAX_ROWS = 20000  # Maximum number of rows in CSV (increased from 10,000)
CSV_ENCODING_OPTIONS = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'windows-1252']  # Encoding options to try

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
}

# WeasyPrint PDF Settings (legacy, for backwards compatibility)
WEASYPRINT_PDF_OPTIONS = {
    'presentational_hints': True,
    'optimize_images': True,
}
