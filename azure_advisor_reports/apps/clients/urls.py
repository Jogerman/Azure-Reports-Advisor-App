"""
URL configuration for clients app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, ClientContactViewSet, ClientNoteViewSet

app_name = 'clients'

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'', ClientViewSet, basename='client')
router.register(r'contacts', ClientContactViewSet, basename='client-contact')
router.register(r'notes', ClientNoteViewSet, basename='client-note')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]