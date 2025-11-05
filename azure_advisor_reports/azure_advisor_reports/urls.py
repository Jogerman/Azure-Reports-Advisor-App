"""
URL configuration for azure_advisor_reports project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from apps.authentication.views import UserViewSet

# Create main router for API endpoints
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API v1 routes
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/clients/', include('apps.clients.urls')),
    path('api/v1/reports/', include('apps.reports.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),

    # Health check endpoint
    path('health/', include('apps.core.urls')),
    path('api/health/', include('apps.core.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers for production (when DEBUG=False)
# These handlers prevent exposure of sensitive information in error responses
handler400 = 'azure_advisor_reports.error_handlers.handler400'
handler403 = 'azure_advisor_reports.error_handlers.handler403'
handler404 = 'azure_advisor_reports.error_handlers.handler404'
handler500 = 'azure_advisor_reports.error_handlers.handler500'