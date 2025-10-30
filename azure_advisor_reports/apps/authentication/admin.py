"""
Django admin configuration for authentication.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.contrib import messages

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

    actions = [
        'assign_admin_role',
        'assign_manager_role',
        'assign_analyst_role',
        'assign_viewer_role',
        'activate_users',
        'deactivate_users',
        'grant_staff_access',
        'revoke_staff_access',
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

    # ========================================================================
    # ADMIN ACTIONS for Bulk Permission Management
    # ========================================================================

    def _assign_role_and_group(self, request, queryset, role, group_name):
        """Helper method to assign role and permission group."""
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            self.message_user(
                request,
                f'Permission group "{group_name}" not found. Run "python manage.py init_permissions" first.',
                level=messages.ERROR
            )
            return

        updated_count = 0
        for user in queryset:
            # Update role
            user.role = role
            user.save()

            # Clear existing permission groups and add the new one
            user.groups.clear()
            user.groups.add(group)
            updated_count += 1

        self.message_user(
            request,
            f'Successfully assigned {group_name} role to {updated_count} user(s).',
            level=messages.SUCCESS
        )

    @admin.action(description='Assign Administrator role (full access)')
    def assign_admin_role(self, request, queryset):
        """Assign Administrator role and permissions."""
        self._assign_role_and_group(request, queryset, 'admin', 'Administrator')

    @admin.action(description='Assign Manager role')
    def assign_manager_role(self, request, queryset):
        """Assign Manager role and permissions."""
        self._assign_role_and_group(request, queryset, 'manager', 'Manager')

    @admin.action(description='Assign Analyst role')
    def assign_analyst_role(self, request, queryset):
        """Assign Analyst role and permissions."""
        self._assign_role_and_group(request, queryset, 'analyst', 'Analyst')

    @admin.action(description='Assign Viewer role (read-only)')
    def assign_viewer_role(self, request, queryset):
        """Assign Viewer role and permissions."""
        self._assign_role_and_group(request, queryset, 'viewer', 'Viewer')

    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        """Activate user accounts."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'Successfully activated {updated} user(s).',
            level=messages.SUCCESS
        )

    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        """Deactivate user accounts."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Successfully deactivated {updated} user(s).',
            level=messages.WARNING
        )

    @admin.action(description='Grant Django admin access')
    def grant_staff_access(self, request, queryset):
        """Grant staff access for Django admin."""
        updated = queryset.update(is_staff=True)
        self.message_user(
            request,
            f'Successfully granted staff access to {updated} user(s).',
            level=messages.SUCCESS
        )

    @admin.action(description='Revoke Django admin access')
    def revoke_staff_access(self, request, queryset):
        """Revoke staff access from Django admin."""
        # Don't revoke from superusers
        queryset = queryset.filter(is_superuser=False)
        updated = queryset.update(is_staff=False)
        self.message_user(
            request,
            f'Successfully revoked staff access from {updated} user(s).',
            level=messages.WARNING
        )


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