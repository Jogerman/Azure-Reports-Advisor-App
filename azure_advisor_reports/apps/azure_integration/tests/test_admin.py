"""
Test cases for azure_integration admin interface.

Tests admin registration, forms, display fields, and actions.
"""

import pytest
import uuid
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from apps.azure_integration.models import AzureSubscription
from apps.azure_integration.admin import AzureSubscriptionAdmin, AzureSubscriptionAdminForm

User = get_user_model()


@pytest.mark.django_db
class TestAzureSubscriptionAdmin:
    """Test suite for AzureSubscription admin."""

    def test_admin_registration(self):
        """Test that AzureSubscription is registered in admin."""
        from django.contrib import admin
        assert AzureSubscription in admin.site._registry

    def test_list_display_fields(self):
        """Test that all expected fields are in list_display."""
        admin_instance = AzureSubscriptionAdmin(AzureSubscription, AdminSite())

        expected_fields = [
            'name',
            'subscription_id',
            'is_active_display',
            'sync_status_display',
            'last_sync_at',
            'created_at',
        ]

        for field in expected_fields:
            assert field in admin_instance.list_display

    def test_list_filter_fields(self):
        """Test that all expected fields are in list_filter."""
        admin_instance = AzureSubscriptionAdmin(AzureSubscription, AdminSite())

        expected_filters = ['is_active', 'sync_status', 'created_at']

        for filter_field in expected_filters:
            assert filter_field in admin_instance.list_filter

    def test_search_fields(self):
        """Test that search fields are configured correctly."""
        admin_instance = AzureSubscriptionAdmin(AzureSubscription, AdminSite())

        expected_search = ['name', 'subscription_id', 'tenant_id']

        for search_field in expected_search:
            assert search_field in admin_instance.search_fields

    def test_readonly_fields(self):
        """Test that sensitive/audit fields are readonly."""
        admin_instance = AzureSubscriptionAdmin(AzureSubscription, AdminSite())

        expected_readonly = [
            'id',
            'created_at',
            'updated_at',
            'last_sync_at',
            'sync_status',
            'sync_error_message',
            'created_by',
        ]

        for readonly_field in expected_readonly:
            assert readonly_field in admin_instance.readonly_fields

    def test_is_active_display_method(self):
        """Test is_active_display method shows correct status."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        active_sub = AzureSubscription.objects.create(
            name="Active Sub",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            is_active=True,
            created_by=user
        )

        inactive_sub = AzureSubscription.objects.create(
            name="Inactive Sub",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            is_active=False,
            created_by=user
        )

        admin_instance = AzureSubscriptionAdmin(AzureSubscription, AdminSite())

        active_display = admin_instance.is_active_display(active_sub)
        inactive_display = admin_instance.is_active_display(inactive_sub)

        assert "Active" in str(active_display)
        assert "green" in str(active_display)
        assert "Inactive" in str(inactive_display)
        assert "red" in str(inactive_display)

    def test_sync_status_display_method(self):
        """Test sync_status_display method shows correct status."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        never_synced = AzureSubscription.objects.create(
            name="Never Synced",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            sync_status='never_synced',
            created_by=user
        )

        success_sub = AzureSubscription.objects.create(
            name="Success Sub",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            sync_status='success',
            created_by=user
        )

        failed_sub = AzureSubscription.objects.create(
            name="Failed Sub",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            sync_status='failed',
            created_by=user
        )

        admin_instance = AzureSubscriptionAdmin(AzureSubscription, AdminSite())

        never_display = admin_instance.sync_status_display(never_synced)
        success_display = admin_instance.sync_status_display(success_sub)
        failed_display = admin_instance.sync_status_display(failed_sub)

        assert "gray" in str(never_display)
        assert "green" in str(success_display)
        assert "red" in str(failed_display)

    def test_mark_as_active_action(self):
        """Test mark_as_active admin action."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        sub1 = AzureSubscription.objects.create(
            name="Sub 1",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            is_active=False,
            created_by=user
        )

        sub2 = AzureSubscription.objects.create(
            name="Sub 2",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            is_active=False,
            created_by=user
        )

        admin_instance = AzureSubscriptionAdmin(AzureSubscription, AdminSite())
        factory = RequestFactory()
        request = factory.get('/')
        request.user = user

        queryset = AzureSubscription.objects.filter(id__in=[sub1.id, sub2.id])
        admin_instance.mark_as_active(request, queryset)

        sub1.refresh_from_db()
        sub2.refresh_from_db()

        assert sub1.is_active is True
        assert sub2.is_active is True

    def test_mark_as_inactive_action(self):
        """Test mark_as_inactive admin action."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        sub1 = AzureSubscription.objects.create(
            name="Sub 1",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            is_active=True,
            created_by=user
        )

        sub2 = AzureSubscription.objects.create(
            name="Sub 2",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            is_active=True,
            created_by=user
        )

        admin_instance = AzureSubscriptionAdmin(AzureSubscription, AdminSite())
        factory = RequestFactory()
        request = factory.get('/')
        request.user = user

        queryset = AzureSubscription.objects.filter(id__in=[sub1.id, sub2.id])
        admin_instance.mark_as_inactive(request, queryset)

        sub1.refresh_from_db()
        sub2.refresh_from_db()

        assert sub1.is_active is False
        assert sub2.is_active is False


@pytest.mark.django_db
class TestAzureSubscriptionAdminForm:
    """Test suite for AzureSubscription admin form."""

    def test_form_excludes_encrypted_field(self):
        """Test that client_secret_encrypted is excluded from form."""
        form = AzureSubscriptionAdminForm()
        assert 'client_secret_encrypted' not in form.fields

    def test_form_has_client_secret_field(self):
        """Test that client_secret field is present."""
        form = AzureSubscriptionAdminForm()
        assert 'client_secret' in form.fields

    def test_form_client_secret_is_password_input(self):
        """Test that client_secret uses PasswordInput widget."""
        form = AzureSubscriptionAdminForm()
        from django.forms.widgets import PasswordInput
        assert isinstance(form.fields['client_secret'].widget, PasswordInput)

    def test_form_save_encrypts_secret(self):
        """Test that saving form encrypts the client_secret."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        form_data = {
            'name': 'Test Subscription',
            'subscription_id': str(uuid.uuid4()),
            'tenant_id': str(uuid.uuid4()),
            'client_id': str(uuid.uuid4()),
            'client_secret': 'my-secret-value',
            'is_active': True,
            'created_by': user.id,
        }

        form = AzureSubscriptionAdminForm(data=form_data)
        assert form.is_valid(), form.errors

        subscription = form.save(commit=False)
        subscription.created_by = user
        subscription.save()

        # Verify secret is encrypted
        assert subscription.client_secret_encrypted != b''
        assert subscription.client_secret == 'my-secret-value'

    def test_form_new_instance_requires_secret(self):
        """Test that client_secret is required for new instances."""
        form = AzureSubscriptionAdminForm()
        assert form.fields['client_secret'].required is True

    def test_form_existing_instance_secret_optional(self):
        """Test that client_secret is optional for existing instances."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription.objects.create(
            name="Existing Sub",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )
        subscription.client_secret = "original-secret"
        subscription.save()

        # Create form with existing instance
        form = AzureSubscriptionAdminForm(instance=subscription)
        assert form.fields['client_secret'].required is False

    def test_form_update_without_changing_secret(self):
        """Test updating subscription without changing secret."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription.objects.create(
            name="Test Sub",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )
        original_secret = "original-secret-value"
        subscription.client_secret = original_secret
        subscription.save()

        original_encrypted = subscription.client_secret_encrypted

        # Update form without providing new secret
        form_data = {
            'name': 'Updated Name',
            'subscription_id': subscription.subscription_id,
            'tenant_id': subscription.tenant_id,
            'client_id': subscription.client_id,
            'client_secret': '',  # Empty to keep existing
            'is_active': True,
            'created_by': user.id,
        }

        form = AzureSubscriptionAdminForm(data=form_data, instance=subscription)
        assert form.is_valid(), form.errors

        updated_subscription = form.save()

        # Name should be updated
        assert updated_subscription.name == 'Updated Name'

        # Secret should remain unchanged
        assert updated_subscription.client_secret_encrypted == original_encrypted
        assert updated_subscription.client_secret == original_secret

    def test_form_update_with_new_secret(self):
        """Test updating subscription with new secret."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription.objects.create(
            name="Test Sub",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )
        subscription.client_secret = "original-secret"
        subscription.save()

        original_encrypted = subscription.client_secret_encrypted

        # Update with new secret
        new_secret = "new-secret-value"
        form_data = {
            'name': subscription.name,
            'subscription_id': subscription.subscription_id,
            'tenant_id': subscription.tenant_id,
            'client_id': subscription.client_id,
            'client_secret': new_secret,
            'is_active': True,
            'created_by': user.id,
        }

        form = AzureSubscriptionAdminForm(data=form_data, instance=subscription)
        assert form.is_valid(), form.errors

        updated_subscription = form.save()

        # Secret should be updated
        assert updated_subscription.client_secret_encrypted != original_encrypted
        assert updated_subscription.client_secret == new_secret
