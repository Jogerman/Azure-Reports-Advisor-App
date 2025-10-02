"""
Test cases for authentication permissions
Tests all permission classes in apps.authentication.permissions
"""

import pytest
from unittest.mock import Mock
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model

from apps.authentication.permissions import (
    IsAuthenticated,
    IsAdmin,
    IsManager,
    IsAnalyst,
    IsViewer,
    CanManageClients,
    CanManageReports,
    CanViewAnalytics,
    IsOwnerOrReadOnly,
    IsSuperUser,
    RoleBasedPermission,
)

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestIsAuthenticatedPermission:
    """Test suite for IsAuthenticated permission"""

    def test_authenticated_user_has_permission(self, user):
        """Test that authenticated user has permission"""
        request = Mock()
        request.user = user

        permission = IsAuthenticated()
        assert permission.has_permission(request, None) is True

    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated user is denied"""
        request = Mock()
        request.user = None

        permission = IsAuthenticated()
        assert permission.has_permission(request, None) is False

    def test_anonymous_user_denied(self):
        """Test that anonymous user is denied"""
        from django.contrib.auth.models import AnonymousUser

        request = Mock()
        request.user = AnonymousUser()

        permission = IsAuthenticated()
        assert permission.has_permission(request, None) is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestIsAdminPermission:
    """Test suite for IsAdmin permission"""

    def test_admin_user_has_permission(self, admin_user):
        """Test that admin user has permission"""
        request = Mock()
        request.user = admin_user

        permission = IsAdmin()
        assert permission.has_permission(request, None) is True

    def test_superuser_has_permission(self, user):
        """Test that superuser has permission"""
        user.is_superuser = True
        user.save()

        request = Mock()
        request.user = user

        permission = IsAdmin()
        assert permission.has_permission(request, None) is True

    def test_non_admin_user_denied(self, manager_user):
        """Test that non-admin user is denied"""
        request = Mock()
        request.user = manager_user

        permission = IsAdmin()
        assert permission.has_permission(request, None) is False

    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated user is denied"""
        request = Mock()
        request.user = None

        permission = IsAdmin()
        assert permission.has_permission(request, None) is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestIsManagerPermission:
    """Test suite for IsManager permission"""

    def test_manager_user_has_permission(self, manager_user):
        """Test that manager user has permission"""
        request = Mock()
        request.user = manager_user

        permission = IsManager()
        assert permission.has_permission(request, None) is True

    def test_admin_user_has_permission(self, admin_user):
        """Test that admin user has permission (higher role)"""
        request = Mock()
        request.user = admin_user

        permission = IsManager()
        assert permission.has_permission(request, None) is True

    def test_analyst_user_denied(self, analyst_user):
        """Test that analyst user is denied"""
        request = Mock()
        request.user = analyst_user

        permission = IsManager()
        assert permission.has_permission(request, None) is False

    def test_viewer_user_denied(self, viewer_user):
        """Test that viewer user is denied"""
        request = Mock()
        request.user = viewer_user

        permission = IsManager()
        assert permission.has_permission(request, None) is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestIsAnalystPermission:
    """Test suite for IsAnalyst permission"""

    def test_analyst_user_has_permission(self, analyst_user):
        """Test that analyst user has permission"""
        request = Mock()
        request.user = analyst_user

        permission = IsAnalyst()
        assert permission.has_permission(request, None) is True

    def test_manager_user_has_permission(self, manager_user):
        """Test that manager user has permission (higher role)"""
        request = Mock()
        request.user = manager_user

        permission = IsAnalyst()
        assert permission.has_permission(request, None) is True

    def test_admin_user_has_permission(self, admin_user):
        """Test that admin user has permission (higher role)"""
        request = Mock()
        request.user = admin_user

        permission = IsAnalyst()
        assert permission.has_permission(request, None) is True

    def test_viewer_user_denied(self, viewer_user):
        """Test that viewer user is denied"""
        request = Mock()
        request.user = viewer_user

        permission = IsAnalyst()
        assert permission.has_permission(request, None) is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestIsViewerPermission:
    """Test suite for IsViewer permission"""

    def test_all_roles_have_permission(self, viewer_user, analyst_user, manager_user, admin_user):
        """Test that all authenticated users have permission"""
        permission = IsViewer()

        for test_user in [viewer_user, analyst_user, manager_user, admin_user]:
            request = Mock()
            request.user = test_user
            assert permission.has_permission(request, None) is True

    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated user is denied"""
        request = Mock()
        request.user = None

        permission = IsViewer()
        assert permission.has_permission(request, None) is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestCanManageClientsPermission:
    """Test suite for CanManageClients permission"""

    def test_read_operations_allowed_for_all_authenticated_users(self, viewer_user):
        """Test that all authenticated users can read clients"""
        request = Mock()
        request.user = viewer_user
        request.method = 'GET'

        permission = CanManageClients()
        assert permission.has_permission(request, None) is True

    def test_create_allowed_for_manager(self, manager_user):
        """Test that manager can create clients"""
        request = Mock()
        request.user = manager_user
        request.method = 'POST'

        permission = CanManageClients()
        assert permission.has_permission(request, None) is True

    def test_create_denied_for_analyst(self, analyst_user):
        """Test that analyst cannot create clients"""
        request = Mock()
        request.user = analyst_user
        request.method = 'POST'

        permission = CanManageClients()
        assert permission.has_permission(request, None) is False

    def test_update_allowed_for_manager(self, manager_user):
        """Test that manager can update clients"""
        request = Mock()
        request.user = manager_user
        request.method = 'PUT'

        permission = CanManageClients()
        assert permission.has_permission(request, None) is True

    def test_patch_allowed_for_manager(self, manager_user):
        """Test that manager can patch clients"""
        request = Mock()
        request.user = manager_user
        request.method = 'PATCH'

        permission = CanManageClients()
        assert permission.has_permission(request, None) is True

    def test_delete_allowed_for_admin(self, admin_user):
        """Test that admin can delete clients"""
        request = Mock()
        request.user = admin_user
        request.method = 'DELETE'

        permission = CanManageClients()
        assert permission.has_permission(request, None) is True

    def test_delete_denied_for_manager(self, manager_user):
        """Test that manager cannot delete clients"""
        request = Mock()
        request.user = manager_user
        request.method = 'DELETE'

        permission = CanManageClients()
        assert permission.has_permission(request, None) is False

    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated user is denied"""
        request = Mock()
        request.user = None
        request.method = 'GET'

        permission = CanManageClients()
        assert permission.has_permission(request, None) is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestCanManageReportsPermission:
    """Test suite for CanManageReports permission"""

    def test_read_allowed_for_all_authenticated_users(self, viewer_user):
        """Test that all authenticated users can read reports"""
        request = Mock()
        request.user = viewer_user
        request.method = 'GET'

        permission = CanManageReports()
        assert permission.has_permission(request, None) is True

    def test_create_allowed_for_analyst(self, analyst_user):
        """Test that analyst can create reports"""
        request = Mock()
        request.user = analyst_user
        request.method = 'POST'

        permission = CanManageReports()
        assert permission.has_permission(request, None) is True

    def test_create_denied_for_viewer(self, viewer_user):
        """Test that viewer cannot create reports"""
        request = Mock()
        request.user = viewer_user
        request.method = 'POST'

        permission = CanManageReports()
        assert permission.has_permission(request, None) is False

    def test_update_requires_analyst_role(self, analyst_user):
        """Test that analyst can update reports"""
        request = Mock()
        request.user = analyst_user
        request.method = 'PUT'

        permission = CanManageReports()
        assert permission.has_permission(request, None) is True

    def test_object_level_permission_owner_can_edit(self, analyst_user):
        """Test that report owner can edit their own report"""
        request = Mock()
        request.user = analyst_user
        request.method = 'PUT'

        # Mock report object
        report = Mock()
        report.created_by = analyst_user

        permission = CanManageReports()
        assert permission.has_object_permission(request, None, report) is True

    def test_object_level_permission_non_owner_analyst_denied(self, analyst_user, manager_user):
        """Test that analyst cannot edit other's reports"""
        request = Mock()
        request.user = analyst_user
        request.method = 'PUT'

        # Mock report created by someone else
        report = Mock()
        report.created_by = manager_user

        permission = CanManageReports()
        assert permission.has_object_permission(request, None, report) is False

    def test_object_level_permission_manager_can_edit_any(self, manager_user, analyst_user):
        """Test that manager can edit any report"""
        request = Mock()
        request.user = manager_user
        request.method = 'PUT'

        # Mock report created by analyst
        report = Mock()
        report.created_by = analyst_user

        permission = CanManageReports()
        assert permission.has_object_permission(request, None, report) is True

    def test_object_level_permission_read_allowed_for_all(self, viewer_user):
        """Test that all users can read any report"""
        request = Mock()
        request.user = viewer_user
        request.method = 'GET'

        report = Mock()

        permission = CanManageReports()
        assert permission.has_object_permission(request, None, report) is True


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestCanViewAnalyticsPermission:
    """Test suite for CanViewAnalytics permission"""

    def test_all_authenticated_users_can_view_analytics(self, viewer_user, analyst_user, manager_user, admin_user):
        """Test that all authenticated users can view analytics"""
        permission = CanViewAnalytics()

        for test_user in [viewer_user, analyst_user, manager_user, admin_user]:
            request = Mock()
            request.user = test_user
            assert permission.has_permission(request, None) is True

    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated user cannot view analytics"""
        request = Mock()
        request.user = None

        permission = CanViewAnalytics()
        assert permission.has_permission(request, None) is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestIsOwnerOrReadOnlyPermission:
    """Test suite for IsOwnerOrReadOnly permission"""

    def test_read_allowed_for_all(self, user):
        """Test that read operations are allowed for all"""
        request = Mock()
        request.user = user
        request.method = 'GET'

        obj = Mock()

        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, obj) is True

    def test_owner_can_edit_via_created_by(self, user):
        """Test that owner can edit via created_by field"""
        request = Mock()
        request.user = user
        request.method = 'PUT'

        obj = Mock()
        obj.created_by = user
        obj.owner = None

        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, obj) is True

    def test_owner_can_edit_via_owner(self, user):
        """Test that owner can edit via owner field"""
        request = Mock()
        request.user = user
        request.method = 'PUT'

        obj = Mock()
        obj.created_by = None
        obj.owner = user

        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, obj) is True

    def test_non_owner_cannot_edit(self, user, admin_user):
        """Test that non-owner cannot edit"""
        request = Mock()
        request.user = user
        request.method = 'PUT'

        obj = Mock()
        obj.created_by = admin_user
        obj.owner = None

        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, obj) is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestIsSuperUserPermission:
    """Test suite for IsSuperUser permission"""

    def test_superuser_has_permission(self, user):
        """Test that superuser has permission"""
        user.is_superuser = True
        user.save()

        request = Mock()
        request.user = user

        permission = IsSuperUser()
        assert permission.has_permission(request, None) is True

    def test_regular_user_denied(self, user):
        """Test that regular user is denied"""
        request = Mock()
        request.user = user

        permission = IsSuperUser()
        assert permission.has_permission(request, None) is False

    def test_admin_role_without_superuser_flag_denied(self, admin_user):
        """Test that admin role without superuser flag is denied"""
        admin_user.is_superuser = False
        admin_user.save()

        request = Mock()
        request.user = admin_user

        permission = IsSuperUser()
        assert permission.has_permission(request, None) is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestRoleBasedPermission:
    """Test suite for RoleBasedPermission"""

    def test_default_required_role_is_viewer(self, viewer_user):
        """Test that default required role is viewer"""
        request = Mock()
        request.user = viewer_user

        view = Mock()
        # No required_role attribute

        permission = RoleBasedPermission()
        assert permission.has_permission(request, view) is True

    def test_custom_required_role(self, manager_user):
        """Test with custom required role"""
        request = Mock()
        request.user = manager_user

        view = Mock()
        view.required_role = 'manager'

        permission = RoleBasedPermission()
        assert permission.has_permission(request, view) is True

    def test_insufficient_role_denied(self, analyst_user):
        """Test that user with insufficient role is denied"""
        request = Mock()
        request.user = analyst_user

        view = Mock()
        view.required_role = 'manager'

        permission = RoleBasedPermission()
        assert permission.has_permission(request, view) is False

    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated user is denied"""
        request = Mock()
        request.user = None

        view = Mock()
        view.required_role = 'viewer'

        permission = RoleBasedPermission()
        assert permission.has_permission(request, view) is False


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.permissions
class TestPermissionIntegration:
    """Integration tests for permission combinations"""

    def test_multiple_permissions_all_pass(self, admin_user):
        """Test that user passes multiple permission checks"""
        request = Mock()
        request.user = admin_user

        permissions = [IsAuthenticated(), IsAdmin(), IsManager(), IsAnalyst()]

        for permission in permissions:
            assert permission.has_permission(request, None) is True

    def test_multiple_permissions_one_fails(self, analyst_user):
        """Test that user fails when one permission denies"""
        request = Mock()
        request.user = analyst_user

        # Analyst should pass first two, fail on IsManager
        assert IsAuthenticated().has_permission(request, None) is True
        assert IsAnalyst().has_permission(request, None) is True
        assert IsManager().has_permission(request, None) is False

    def test_permission_hierarchy_enforcement(self, viewer_user, analyst_user, manager_user, admin_user):
        """Test that permission hierarchy is correctly enforced"""
        users_and_permissions = [
            (viewer_user, [IsViewer()]),
            (analyst_user, [IsViewer(), IsAnalyst()]),
            (manager_user, [IsViewer(), IsAnalyst(), IsManager()]),
            (admin_user, [IsViewer(), IsAnalyst(), IsManager(), IsAdmin()]),
        ]

        for test_user, allowed_permissions in users_and_permissions:
            request = Mock()
            request.user = test_user

            for permission in allowed_permissions:
                assert permission.has_permission(request, None) is True, \
                    f"{test_user.role} should have {permission.__class__.__name__}"
