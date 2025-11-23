"""
Role-Based Access Control (RBAC) System

Comprehensive permission system with role-based access control,
resource-level permissions, and audit logging.
"""

from rest_framework import permissions
from rest_framework.request import Request
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Role Definitions
# =============================================================================

class UserRole:
    """User role constants"""
    ADMIN = 'admin'
    MANAGER = 'manager'
    ANALYST = 'analyst'
    VIEWER = 'viewer'

    CHOICES = [
        (ADMIN, 'Administrator'),
        (MANAGER, 'Manager'),
        (ANALYST, 'Analyst'),
        (VIEWER, 'Viewer'),
    ]

    # Role hierarchy (higher number = more permissions)
    HIERARCHY = {
        ADMIN: 4,
        MANAGER: 3,
        ANALYST: 2,
        VIEWER: 1,
    }


# =============================================================================
# Resource Permissions
# =============================================================================

class ResourcePermission:
    """Resource-level permission constants"""

    # Client permissions
    VIEW_CLIENT = 'view_client'
    ADD_CLIENT = 'add_client'
    CHANGE_CLIENT = 'change_client'
    DELETE_CLIENT = 'delete_client'

    # Report permissions
    VIEW_REPORT = 'view_report'
    ADD_REPORT = 'add_report'
    CHANGE_REPORT = 'change_report'
    DELETE_REPORT = 'delete_report'
    DOWNLOAD_REPORT = 'download_report'
    GENERATE_REPORT = 'generate_report'

    # User permissions
    VIEW_USER = 'view_user'
    ADD_USER = 'add_user'
    CHANGE_USER = 'change_user'
    DELETE_USER = 'delete_user'
    CHANGE_USER_ROLE = 'change_user_role'

    # Audit permissions
    VIEW_AUDIT_LOG = 'view_audit_log'
    EXPORT_AUDIT_LOG = 'export_audit_log'

    # Analytics permissions
    VIEW_ANALYTICS = 'view_analytics'
    EXPORT_ANALYTICS = 'export_analytics'

    # System permissions
    MANAGE_SETTINGS = 'manage_settings'
    VIEW_SYSTEM_HEALTH = 'view_system_health'


# =============================================================================
# Role Permission Matrix
# =============================================================================

ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        # Full access to everything
        ResourcePermission.VIEW_CLIENT,
        ResourcePermission.ADD_CLIENT,
        ResourcePermission.CHANGE_CLIENT,
        ResourcePermission.DELETE_CLIENT,
        ResourcePermission.VIEW_REPORT,
        ResourcePermission.ADD_REPORT,
        ResourcePermission.CHANGE_REPORT,
        ResourcePermission.DELETE_REPORT,
        ResourcePermission.DOWNLOAD_REPORT,
        ResourcePermission.GENERATE_REPORT,
        ResourcePermission.VIEW_USER,
        ResourcePermission.ADD_USER,
        ResourcePermission.CHANGE_USER,
        ResourcePermission.DELETE_USER,
        ResourcePermission.CHANGE_USER_ROLE,
        ResourcePermission.VIEW_AUDIT_LOG,
        ResourcePermission.EXPORT_AUDIT_LOG,
        ResourcePermission.VIEW_ANALYTICS,
        ResourcePermission.EXPORT_ANALYTICS,
        ResourcePermission.MANAGE_SETTINGS,
        ResourcePermission.VIEW_SYSTEM_HEALTH,
    ],

    UserRole.MANAGER: [
        # Can manage clients and reports, view analytics
        ResourcePermission.VIEW_CLIENT,
        ResourcePermission.ADD_CLIENT,
        ResourcePermission.CHANGE_CLIENT,
        ResourcePermission.VIEW_REPORT,
        ResourcePermission.ADD_REPORT,
        ResourcePermission.CHANGE_REPORT,
        ResourcePermission.DELETE_REPORT,
        ResourcePermission.DOWNLOAD_REPORT,
        ResourcePermission.GENERATE_REPORT,
        ResourcePermission.VIEW_USER,
        ResourcePermission.VIEW_AUDIT_LOG,
        ResourcePermission.VIEW_ANALYTICS,
        ResourcePermission.EXPORT_ANALYTICS,
    ],

    UserRole.ANALYST: [
        # Can view and create reports
        ResourcePermission.VIEW_CLIENT,
        ResourcePermission.VIEW_REPORT,
        ResourcePermission.ADD_REPORT,
        ResourcePermission.DOWNLOAD_REPORT,
        ResourcePermission.GENERATE_REPORT,
        ResourcePermission.VIEW_ANALYTICS,
    ],

    UserRole.VIEWER: [
        # Read-only access
        ResourcePermission.VIEW_CLIENT,
        ResourcePermission.VIEW_REPORT,
        ResourcePermission.DOWNLOAD_REPORT,
        ResourcePermission.VIEW_ANALYTICS,
    ],
}


# =============================================================================
# Permission Checking Functions
# =============================================================================

def has_role(user, role: str) -> bool:
    """
    Check if user has a specific role

    Args:
        user: User instance
        role: Role name

    Returns:
        True if user has the role
    """
    if not user or not user.is_authenticated:
        return False

    return getattr(user, 'role', None) == role


def has_permission(user, permission: str) -> bool:
    """
    Check if user has a specific permission

    Args:
        user: User instance
        permission: Permission name

    Returns:
        True if user has the permission

    Example:
        if has_permission(request.user, ResourcePermission.DELETE_CLIENT):
            # Allow deletion
    """
    if not user or not user.is_authenticated:
        return False

    # Superusers have all permissions
    if user.is_superuser:
        return True

    # Check role-based permissions
    user_role = getattr(user, 'role', None)
    if user_role in ROLE_PERMISSIONS:
        return permission in ROLE_PERMISSIONS[user_role]

    return False


def has_any_permission(user, permissions: list) -> bool:
    """
    Check if user has any of the specified permissions

    Args:
        user: User instance
        permissions: List of permission names

    Returns:
        True if user has at least one permission
    """
    return any(has_permission(user, perm) for perm in permissions)


def has_all_permissions(user, permissions: list) -> bool:
    """
    Check if user has all specified permissions

    Args:
        user: User instance
        permissions: List of permission names

    Returns:
        True if user has all permissions
    """
    return all(has_permission(user, perm) for perm in permissions)


def get_user_permissions(user) -> list:
    """
    Get all permissions for a user

    Args:
        user: User instance

    Returns:
        List of permission names
    """
    if not user or not user.is_authenticated:
        return []

    if user.is_superuser:
        # Superusers have all permissions
        all_perms = set()
        for perms in ROLE_PERMISSIONS.values():
            all_perms.update(perms)
        return list(all_perms)

    user_role = getattr(user, 'role', None)
    return ROLE_PERMISSIONS.get(user_role, [])


def can_manage_user(current_user, target_user) -> bool:
    """
    Check if current user can manage target user

    Rules:
    - Admins can manage everyone
    - Managers can manage analysts and viewers
    - Users cannot manage themselves (role changes)
    - Cannot promote users to higher role than own role

    Args:
        current_user: User performing the action
        target_user: User being managed

    Returns:
        True if current user can manage target user
    """
    if not current_user or not current_user.is_authenticated:
        return False

    if current_user.is_superuser:
        return True

    # Cannot manage yourself for role changes
    if current_user.id == target_user.id:
        return False

    current_role = getattr(current_user, 'role', None)
    target_role = getattr(target_user, 'role', None)

    current_level = UserRole.HIERARCHY.get(current_role, 0)
    target_level = UserRole.HIERARCHY.get(target_role, 0)

    # Can only manage users with lower role
    return current_level > target_level


# =============================================================================
# DRF Permission Classes
# =============================================================================

class IsAuthenticated(permissions.BasePermission):
    """
    Allow access only to authenticated users
    """

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)


class IsAdmin(permissions.BasePermission):
    """
    Allow access only to administrators
    """

    def has_permission(self, request: Request, view) -> bool:
        return bool(
            request.user and
            request.user.is_authenticated and
            has_role(request.user, UserRole.ADMIN)
        )


class IsManager(permissions.BasePermission):
    """
    Allow access to managers and above
    """

    def has_permission(self, request: Request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        user_role = getattr(request.user, 'role', None)
        role_level = UserRole.HIERARCHY.get(user_role, 0)
        manager_level = UserRole.HIERARCHY.get(UserRole.MANAGER, 0)

        return role_level >= manager_level


class IsAnalyst(permissions.BasePermission):
    """
    Allow access to analysts and above
    """

    def has_permission(self, request: Request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        user_role = getattr(request.user, 'role', None)
        role_level = UserRole.HIERARCHY.get(user_role, 0)
        analyst_level = UserRole.HIERARCHY.get(UserRole.ANALYST, 0)

        return role_level >= analyst_level


class HasResourcePermission(permissions.BasePermission):
    """
    Check if user has specific resource permission

    Usage in ViewSet:
        permission_classes = [HasResourcePermission]
        permission_required = ResourcePermission.VIEW_CLIENT
    """

    def has_permission(self, request: Request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        # Get required permission from view
        required_permission = getattr(view, 'permission_required', None)

        if not required_permission:
            # No specific permission required, allow if authenticated
            return True

        return has_permission(request.user, required_permission)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Allow owners to edit, others to read only
    """

    def has_object_permission(self, request: Request, view, obj) -> bool:
        # Read permissions allowed for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for owner
        return obj.created_by == request.user


class IsOwnerOrManager(permissions.BasePermission):
    """
    Allow owners and managers to access
    """

    def has_object_permission(self, request: Request, view, obj) -> bool:
        # Managers have full access
        if has_role(request.user, UserRole.MANAGER) or has_role(request.user, UserRole.ADMIN):
            return True

        # Owners have access to their own objects
        return obj.created_by == request.user


# =============================================================================
# Permission Decorators
# =============================================================================

from functools import wraps
from django.core.exceptions import PermissionDenied


def require_permission(permission: str):
    """
    Decorator to require specific permission for a view function

    Usage:
        @require_permission(ResourcePermission.DELETE_CLIENT)
        def delete_client(request, client_id):
            # Only users with delete_client permission can access
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not has_permission(request.user, permission):
                logger.warning(
                    f'Permission denied for {request.user.username}: '
                    f'required {permission}'
                )
                raise PermissionDenied(
                    f'You do not have permission: {permission}'
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_role(role: str):
    """
    Decorator to require specific role for a view function

    Usage:
        @require_role(UserRole.ADMIN)
        def admin_dashboard(request):
            # Only admins can access
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not has_role(request.user, role):
                logger.warning(
                    f'Access denied for {request.user.username}: '
                    f'required role {role}'
                )
                raise PermissionDenied(
                    f'You must be a {role} to access this resource'
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# Permission Utilities
# =============================================================================

def get_accessible_clients(user):
    """
    Get clients accessible to user based on permissions

    Args:
        user: User instance

    Returns:
        QuerySet of accessible clients
    """
    from apps.clients.models import Client

    if not user or not user.is_authenticated:
        return Client.objects.none()

    # Admins and managers see all clients
    if has_role(user, UserRole.ADMIN) or has_role(user, UserRole.MANAGER):
        return Client.objects.all()

    # Analysts and viewers see clients they have reports for
    return Client.objects.filter(
        reports__created_by=user
    ).distinct()


def get_accessible_reports(user):
    """
    Get reports accessible to user based on permissions

    Args:
        user: User instance

    Returns:
        QuerySet of accessible reports
    """
    from apps.reports.models import Report

    if not user or not user.is_authenticated:
        return Report.objects.none()

    # Admins and managers see all reports
    if has_role(user, UserRole.ADMIN) or has_role(user, UserRole.MANAGER):
        return Report.objects.all()

    # Analysts and viewers see only their own reports
    return Report.objects.filter(created_by=user)


def filter_by_permissions(user, queryset, permission: str):
    """
    Filter queryset based on user permissions

    Args:
        user: User instance
        queryset: Django QuerySet
        permission: Permission to check

    Returns:
        Filtered QuerySet
    """
    if not has_permission(user, permission):
        return queryset.none()

    return queryset
