"""
Custom permission classes for role-based access control (RBAC).
"""

from rest_framework import permissions
from .services import RoleService


class IsAuthenticated(permissions.BasePermission):
    """
    Permission to ensure user is authenticated.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsAdmin(permissions.BasePermission):
    """
    Permission to ensure user has admin role.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            RoleService.can_manage_users(request.user)
        )


class IsManager(permissions.BasePermission):
    """
    Permission to ensure user has manager role or higher.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            RoleService.has_permission(request.user, 'manager')
        )


class IsAnalyst(permissions.BasePermission):
    """
    Permission to ensure user has analyst role or higher.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            RoleService.has_permission(request.user, 'analyst')
        )


class IsViewer(permissions.BasePermission):
    """
    Permission to ensure user has viewer role or higher (essentially any authenticated user).
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            RoleService.has_permission(request.user, 'viewer')
        )


class CanManageClients(permissions.BasePermission):
    """
    Permission for client management operations.
    - Read: All authenticated users
    - Create: Manager and above
    - Update: Manager and above
    - Delete: Admin only
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Create and update require manager role
        if request.method in ['POST', 'PUT', 'PATCH']:
            return RoleService.can_create_clients(request.user)

        # Delete requires admin role
        if request.method == 'DELETE':
            return RoleService.can_delete_clients(request.user)

        return False


class CanManageReports(permissions.BasePermission):
    """
    Permission for report management operations.
    - Read: All authenticated users
    - Create: Analyst and above
    - Update: Analyst and above (own reports) or Manager (all reports)
    - Delete: Manager and above
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return RoleService.can_view_reports(request.user)

        # Create requires analyst role
        if request.method == 'POST':
            return RoleService.can_generate_reports(request.user)

        # Update and delete require analyst role (object-level permission in has_object_permission)
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return RoleService.can_generate_reports(request.user)

        return False

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check for reports.
        """
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Managers and admins can modify any report
        if RoleService.has_permission(request.user, 'manager'):
            return True

        # Analysts can only modify their own reports
        if RoleService.has_permission(request.user, 'analyst'):
            return obj.created_by == request.user

        return False


class CanViewAnalytics(permissions.BasePermission):
    """
    Permission for viewing analytics dashboard.
    All authenticated users can view analytics.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission to allow owners to edit objects, others to read only.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        # Assumes the object has a `created_by` or `owner` field
        owner_field = getattr(obj, 'created_by', None) or getattr(obj, 'owner', None)
        return owner_field == request.user


class IsSuperUser(permissions.BasePermission):
    """
    Permission to ensure user is a superuser.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )


class RoleBasedPermission(permissions.BasePermission):
    """
    Generic role-based permission class.
    Views can specify required_role attribute.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        required_role = getattr(view, 'required_role', 'viewer')
        return RoleService.has_permission(request.user, required_role)