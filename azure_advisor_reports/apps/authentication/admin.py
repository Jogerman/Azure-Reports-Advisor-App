"""
Django admin configuration for authentication.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import User, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username',
        'email',
        'full_name',
        'role',
        'job_title',
        'department',
        'is_active',
        'is_staff',
        'last_login',
        'created_at'
    ]
    list_filter = [
        'role',
        'is_active',
        'is_staff',
        'is_superuser',
        'department',
        'created_at',
        'last_login'
    ]
    search_fields = [
        'username',
        'email',
        'first_name',
        'last_name',
        'azure_object_id'
    ]
    readonly_fields = [
        'id',
        'azure_object_id',
        'tenant_id',
        'created_at',
        'last_login_ip',
        'date_joined'
    ]

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal info', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'job_title',
                'department',
                'phone_number'
            )
        }),
        ('Azure AD Integration', {
            'fields': (
                'azure_object_id',
                'tenant_id',
            )
        }),
        ('Role & Permissions', {
            'fields': (
                'role',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            ),
        }),
        ('Important dates', {
            'fields': (
                'last_login',
                'last_login_ip',
                'date_joined',
                'created_at'
            )
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'first_name',
                'last_name',
                'password1',
                'password2'
            ),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'ip_address',
        'is_active',
        'created_at',
        'last_activity',
        'session_duration'
    ]
    list_filter = [
        'is_active',
        'created_at',
        'last_activity'
    ]
    search_fields = [
        'user__username',
        'user__email',
        'ip_address',
        'session_key'
    ]
    readonly_fields = [
        'id',
        'session_key',
        'user_agent',
        'created_at',
        'last_activity',
        'session_duration'
    ]

    fieldsets = (
        ('Session Information', {
            'fields': (
                'user',
                'session_key',
                'is_active',
            )
        }),
        ('Client Information', {
            'fields': (
                'ip_address',
                'user_agent',
            )
        }),
        ('Timing', {
            'fields': (
                'created_at',
                'last_activity',
                'session_duration',
            )
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )

    def session_duration(self, obj):
        if obj.created_at and obj.last_activity:
            duration = obj.last_activity - obj.created_at
            hours = duration.total_seconds() // 3600
            minutes = (duration.total_seconds() % 3600) // 60
            return f"{int(hours)}h {int(minutes)}m"
        return "-"
    session_duration.short_description = 'Duration'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def has_add_permission(self, request):
        return False  # Prevent manual creation of sessions

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can modify sessions