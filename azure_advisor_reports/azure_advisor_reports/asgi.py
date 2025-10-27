"""
ASGI config for azure_advisor_reports project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Default to production settings for ASGI deployment (Azure Container Apps)
# Can be overridden by setting DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings.production')

application = get_asgi_application()