"""
WSGI config for azure_advisor_reports project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Default to production settings for WSGI deployment (Azure Container Apps)
# Can be overridden by setting DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings.production')

application = get_wsgi_application()