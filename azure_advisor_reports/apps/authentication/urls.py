"""
URL configuration for authentication app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'authentication'

# Router for user management viewset
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    # Azure AD authentication
    path('login/', views.AzureADLoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', views.TokenRefreshView.as_view(), name='token-refresh'),

    # Current user profile
    path('user/', views.CurrentUserView.as_view(), name='current-user'),

    # User management (admin only)
    path('', include(router.urls)),
]