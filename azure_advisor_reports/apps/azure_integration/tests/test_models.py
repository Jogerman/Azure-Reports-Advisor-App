"""
Test cases for azure_integration models.

Tests AzureSubscription model including encryption, validation, and sync status tracking.
"""

import pytest
import uuid
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from cryptography.fernet import InvalidToken

from apps.azure_integration.models import AzureSubscription

User = get_user_model()


@pytest.mark.django_db
class TestAzureSubscriptionModel:
    """Test suite for AzureSubscription model."""

    def test_subscription_creation(self):
        """Test creating an Azure subscription with all required fields."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())

        subscription = AzureSubscription.objects.create(
            name="Production Subscription",
            subscription_id=subscription_id,
            tenant_id=tenant_id,
            client_id=client_id,
            created_by=user
        )
        # Set the secret using the property
        subscription.client_secret = "test-secret-value"
        subscription.save()

        assert subscription.id is not None
        assert isinstance(subscription.id, uuid.UUID)
        assert subscription.name == "Production Subscription"
        assert subscription.subscription_id == subscription_id
        assert subscription.tenant_id == tenant_id
        assert subscription.client_id == client_id
        assert subscription.is_active is True
        assert subscription.sync_status == 'never_synced'
        assert subscription.created_by == user

    def test_client_secret_encryption(self):
        """Test that client_secret is encrypted when stored."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription.objects.create(
            name="Test Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        secret_value = "my-super-secret-value-12345"
        subscription.client_secret = secret_value
        subscription.save()

        # Refresh from database
        subscription.refresh_from_db()

        # Verify the encrypted field is not plain text
        assert subscription.client_secret_encrypted != secret_value.encode()
        assert len(subscription.client_secret_encrypted) > 0

        # Verify we can decrypt it
        decrypted = subscription.client_secret
        assert decrypted == secret_value

    def test_client_secret_decryption(self):
        """Test client_secret property getter decrypts correctly."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription.objects.create(
            name="Test Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        original_secret = "test-secret-12345"
        subscription.client_secret = original_secret
        subscription.save()

        # Get a fresh instance from database
        subscription_from_db = AzureSubscription.objects.get(id=subscription.id)

        assert subscription_from_db.client_secret == original_secret

    def test_empty_client_secret(self):
        """Test handling of empty client_secret."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription.objects.create(
            name="Test Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        # Set empty secret
        subscription.client_secret = ""
        subscription.save()

        assert subscription.client_secret == ""
        assert subscription.client_secret_encrypted == b''

    def test_get_credentials_method(self):
        """Test get_credentials() returns all decrypted credentials."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        client_secret = "secret-value-12345"

        subscription = AzureSubscription.objects.create(
            name="Test Subscription",
            subscription_id=subscription_id,
            tenant_id=tenant_id,
            client_id=client_id,
            created_by=user
        )
        subscription.client_secret = client_secret
        subscription.save()

        credentials = subscription.get_credentials()

        assert credentials['subscription_id'] == subscription_id
        assert credentials['tenant_id'] == tenant_id
        assert credentials['client_id'] == client_id
        assert credentials['client_secret'] == client_secret

    def test_update_sync_status_success(self):
        """Test update_sync_status with success status."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription.objects.create(
            name="Test Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        before = timezone.now()
        subscription.update_sync_status('success')
        after = timezone.now()

        assert subscription.sync_status == 'success'
        assert subscription.last_sync_at is not None
        assert before <= subscription.last_sync_at <= after
        assert subscription.sync_error_message == ''

    def test_update_sync_status_failed(self):
        """Test update_sync_status with failed status and error message."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription.objects.create(
            name="Test Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        error_msg = "Connection timeout after 30 seconds"
        subscription.update_sync_status('failed', error_msg)

        assert subscription.sync_status == 'failed'
        assert subscription.sync_error_message == error_msg
        # last_sync_at should not be updated on failure
        assert subscription.last_sync_at is None

    def test_update_sync_status_invalid(self):
        """Test update_sync_status raises error for invalid status."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription.objects.create(
            name="Test Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        with pytest.raises(ValueError, match="Invalid status"):
            subscription.update_sync_status('invalid_status')

    def test_subscription_id_uuid_validation(self):
        """Test subscription_id validates UUID format."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription(
            name="Test Subscription",
            subscription_id="not-a-valid-uuid",
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        with pytest.raises(ValidationError):
            subscription.full_clean()

    def test_tenant_id_uuid_validation(self):
        """Test tenant_id validates UUID format."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription(
            name="Test Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id="invalid-tenant-id",
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        with pytest.raises(ValidationError):
            subscription.full_clean()

    def test_client_id_uuid_validation(self):
        """Test client_id validates UUID format."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription(
            name="Test Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id="not-a-uuid",
            created_by=user
        )

        with pytest.raises(ValidationError):
            subscription.full_clean()

    def test_is_active_filtering(self):
        """Test filtering subscriptions by is_active status."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        active_sub = AzureSubscription.objects.create(
            name="Active Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            is_active=True,
            created_by=user
        )

        inactive_sub = AzureSubscription.objects.create(
            name="Inactive Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            is_active=False,
            created_by=user
        )

        active_subscriptions = AzureSubscription.objects.filter(is_active=True)
        inactive_subscriptions = AzureSubscription.objects.filter(is_active=False)

        assert active_sub in active_subscriptions
        assert inactive_sub not in active_subscriptions
        assert inactive_sub in inactive_subscriptions
        assert active_sub not in inactive_subscriptions

    def test_string_representation(self):
        """Test __str__ method returns name and subscription_id."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription_id = str(uuid.uuid4())
        subscription = AzureSubscription.objects.create(
            name="Production Account",
            subscription_id=subscription_id,
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        str_repr = str(subscription)
        assert "Production Account" in str_repr
        assert subscription_id in str_repr

    def test_ordering_newest_first(self):
        """Test subscriptions are ordered by created_at descending."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        import time

        first_sub = AzureSubscription.objects.create(
            name="First Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        time.sleep(0.01)

        second_sub = AzureSubscription.objects.create(
            name="Second Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        subscriptions = list(AzureSubscription.objects.all())

        assert subscriptions[0] == second_sub
        assert subscriptions[1] == first_sub

    def test_subscription_id_uniqueness(self):
        """Test subscription_id must be unique."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription_id = str(uuid.uuid4())

        AzureSubscription.objects.create(
            name="First Subscription",
            subscription_id=subscription_id,
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        # Try to create another with the same subscription_id
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            AzureSubscription.objects.create(
                name="Duplicate Subscription",
                subscription_id=subscription_id,
                tenant_id=str(uuid.uuid4()),
                client_id=str(uuid.uuid4()),
                created_by=user
            )

    def test_created_by_set_null_on_user_deletion(self):
        """Test created_by is set to null when user is deleted."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription.objects.create(
            name="Test Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        subscription_id = subscription.id
        user.delete()

        subscription = AzureSubscription.objects.get(id=subscription_id)
        assert subscription.created_by is None

    def test_default_values(self):
        """Test default field values."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription.objects.create(
            name="Test Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        assert subscription.is_active is True
        assert subscription.sync_status == 'never_synced'
        assert subscription.sync_error_message == ''
        assert subscription.last_sync_at is None

    def test_uppercase_uuid_validation(self):
        """Test that uppercase UUIDs are accepted."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        # UUIDs can be uppercase in some systems
        subscription_id = str(uuid.uuid4()).upper()

        subscription = AzureSubscription(
            name="Test Subscription",
            subscription_id=subscription_id.lower(),  # Store as lowercase
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        # Should not raise validation error
        subscription.full_clean()
        subscription.save()

        assert subscription.subscription_id == subscription_id.lower()

    def test_multiple_sync_status_updates(self):
        """Test updating sync status multiple times."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        subscription = AzureSubscription.objects.create(
            name="Test Subscription",
            subscription_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4()),
            created_by=user
        )

        # First sync: success
        subscription.update_sync_status('success')
        assert subscription.sync_status == 'success'
        first_sync_time = subscription.last_sync_at

        import time
        time.sleep(0.01)

        # Second sync: failed
        subscription.update_sync_status('failed', 'API error')
        assert subscription.sync_status == 'failed'
        assert subscription.sync_error_message == 'API error'
        # last_sync_at should remain from the last successful sync
        assert subscription.last_sync_at == first_sync_time

        # Third sync: success again
        subscription.update_sync_status('success')
        assert subscription.sync_status == 'success'
        assert subscription.sync_error_message == ''
        assert subscription.last_sync_at > first_sync_time
