"""
Comprehensive tests for Azure Integration serializers.

Tests cover:
- AzureSubscription serializers (list, create, update)
- UUID validation
- Client secret validation
- Encryption handling
- Error cases and edge conditions
"""

import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError

from apps.azure_integration.models import AzureSubscription
from apps.azure_integration.serializers import (
    AzureSubscriptionSerializer,
    AzureSubscriptionCreateSerializer,
    AzureSubscriptionUpdateSerializer,
    AzureSubscriptionListSerializer,
)
from apps.azure_integration.validators import (
    validate_uuid_format,
    validate_subscription_id,
    validate_client_secret,
)

User = get_user_model()


class AzureSubscriptionSerializerTestCase(TestCase):
    """Tests for AzureSubscriptionSerializer (read-only listing)."""

    def setUp(self):
        """Set up test user and subscription."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.subscription = AzureSubscription.objects.create(
            name='Test Subscription',
            subscription_id='550e8400-e29b-41d4-a716-446655440000',
            tenant_id='660e8400-e29b-41d4-a716-446655440000',
            client_id='770e8400-e29b-41d4-a716-446655440000',
            created_by=self.user,
        )
        self.subscription.client_secret = 'test_secret_1234567890123456789012345'
        self.subscription.save()

    def test_serialization_excludes_encrypted_secret(self):
        """Test that client_secret_encrypted is never exposed."""
        serializer = AzureSubscriptionSerializer(self.subscription)
        data = serializer.data

        self.assertNotIn('client_secret', data)
        self.assertNotIn('client_secret_encrypted', data)

    def test_serialization_includes_all_fields(self):
        """Test that all expected fields are included."""
        serializer = AzureSubscriptionSerializer(self.subscription)
        data = serializer.data

        expected_fields = {
            'id', 'name', 'subscription_id', 'tenant_id', 'client_id',
            'is_active', 'sync_status', 'sync_error_message', 'last_sync_at',
            'created_by', 'created_at', 'updated_at'
        }

        self.assertEqual(set(data.keys()), expected_fields)

    def test_created_by_nested_serialization(self):
        """Test that created_by is properly nested with user details."""
        serializer = AzureSubscriptionSerializer(self.subscription)
        data = serializer.data

        self.assertIn('created_by', data)
        self.assertEqual(data['created_by']['id'], str(self.user.id))
        self.assertEqual(data['created_by']['username'], 'testuser')
        self.assertEqual(data['created_by']['email'], 'test@example.com')

    def test_uuid_validation_on_read(self):
        """Test UUID format validation on subscription_id."""
        serializer = AzureSubscriptionSerializer(data={
            'subscription_id': 'invalid-uuid',
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('subscription_id', serializer.errors)


class AzureSubscriptionCreateSerializerTestCase(TestCase):
    """Tests for AzureSubscriptionCreateSerializer."""

    def setUp(self):
        """Set up test user and request factory."""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.valid_data = {
            'name': 'Production Subscription',
            'subscription_id': '550e8400-e29b-41d4-a716-446655440000',
            'tenant_id': '660e8400-e29b-41d4-a716-446655440000',
            'client_id': '770e8400-e29b-41d4-a716-446655440000',
            'client_secret': 'valid_secret_1234567890123456789012345',
            'is_active': True,
        }

    def test_successful_creation(self):
        """Test successful subscription creation with valid data."""
        request = self.factory.post('/api/subscriptions/')
        request.user = self.user

        serializer = AzureSubscriptionCreateSerializer(
            data=self.valid_data,
            context={'request': request}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()

        self.assertEqual(subscription.name, 'Production Subscription')
        self.assertEqual(subscription.subscription_id, '550e8400-e29b-41d4-a716-446655440000')
        self.assertEqual(subscription.created_by, self.user)
        self.assertTrue(subscription.is_active)

        # Verify secret is encrypted
        self.assertIsNotNone(subscription.client_secret_encrypted)
        # Verify secret can be decrypted
        self.assertEqual(subscription.client_secret, 'valid_secret_1234567890123456789012345')

    def test_creation_with_invalid_uuid_format(self):
        """Test creation fails with invalid UUID format."""
        data = self.valid_data.copy()
        data['subscription_id'] = 'not-a-uuid'

        serializer = AzureSubscriptionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('subscription_id', serializer.errors)

    def test_creation_with_duplicate_subscription_id(self):
        """Test creation fails with duplicate subscription_id."""
        # Create first subscription
        AzureSubscription.objects.create(
            name='Existing',
            subscription_id='550e8400-e29b-41d4-a716-446655440000',
            tenant_id='660e8400-e29b-41d4-a716-446655440000',
            client_id='770e8400-e29b-41d4-a716-446655440000',
        )

        # Try to create duplicate
        serializer = AzureSubscriptionCreateSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('subscription_id', serializer.errors)

    def test_creation_with_short_client_secret(self):
        """Test creation fails with client_secret < 20 characters."""
        data = self.valid_data.copy()
        data['client_secret'] = 'short'  # Only 5 characters

        serializer = AzureSubscriptionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('client_secret', serializer.errors)

    def test_creation_with_long_client_secret(self):
        """Test creation fails with client_secret > 200 characters."""
        data = self.valid_data.copy()
        data['client_secret'] = 'x' * 201  # 201 characters

        serializer = AzureSubscriptionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('client_secret', serializer.errors)

    def test_creation_with_secret_containing_spaces(self):
        """Test creation fails with client_secret containing spaces."""
        data = self.valid_data.copy()
        data['client_secret'] = 'secret with spaces 1234567890'

        serializer = AzureSubscriptionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('client_secret', serializer.errors)

    def test_creation_with_empty_name(self):
        """Test creation fails with empty name."""
        data = self.valid_data.copy()
        data['name'] = ''

        serializer = AzureSubscriptionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_creation_with_name_exceeding_max_length(self):
        """Test creation fails with name > 200 characters."""
        data = self.valid_data.copy()
        data['name'] = 'x' * 201

        serializer = AzureSubscriptionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_is_active_defaults_to_true(self):
        """Test is_active defaults to True if not provided."""
        data = self.valid_data.copy()
        del data['is_active']

        request = self.factory.post('/api/subscriptions/')
        request.user = self.user

        serializer = AzureSubscriptionCreateSerializer(
            data=data,
            context={'request': request}
        )

        self.assertTrue(serializer.is_valid())
        subscription = serializer.save()
        self.assertTrue(subscription.is_active)

    def test_created_by_set_from_request_user(self):
        """Test created_by is automatically set from request.user."""
        request = self.factory.post('/api/subscriptions/')
        request.user = self.user

        serializer = AzureSubscriptionCreateSerializer(
            data=self.valid_data,
            context={'request': request}
        )

        self.assertTrue(serializer.is_valid())
        subscription = serializer.save()
        self.assertEqual(subscription.created_by, self.user)

    def test_uuid_normalization_to_lowercase(self):
        """Test UUIDs are normalized to lowercase."""
        data = self.valid_data.copy()
        data['subscription_id'] = '550E8400-E29B-41D4-A716-446655440000'  # Uppercase

        request = self.factory.post('/api/subscriptions/')
        request.user = self.user

        serializer = AzureSubscriptionCreateSerializer(
            data=data,
            context={'request': request}
        )

        self.assertTrue(serializer.is_valid())
        subscription = serializer.save()
        self.assertEqual(subscription.subscription_id, '550e8400-e29b-41d4-a716-446655440000')


class AzureSubscriptionUpdateSerializerTestCase(TestCase):
    """Tests for AzureSubscriptionUpdateSerializer."""

    def setUp(self):
        """Set up test subscription."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.subscription = AzureSubscription.objects.create(
            name='Original Name',
            subscription_id='550e8400-e29b-41d4-a716-446655440000',
            tenant_id='660e8400-e29b-41d4-a716-446655440000',
            client_id='770e8400-e29b-41d4-a716-446655440000',
            created_by=self.user,
        )
        self.subscription.client_secret = 'original_secret_12345678901234567890'
        self.subscription.save()

    def test_update_name_only(self):
        """Test updating only the name field."""
        serializer = AzureSubscriptionUpdateSerializer(
            self.subscription,
            data={'name': 'Updated Name'},
            partial=True
        )

        self.assertTrue(serializer.is_valid())
        subscription = serializer.save()

        self.assertEqual(subscription.name, 'Updated Name')
        # Verify secret remains unchanged
        self.assertEqual(subscription.client_secret, 'original_secret_12345678901234567890')

    def test_update_with_new_secret(self):
        """Test updating with new client_secret re-encrypts it."""
        new_secret = 'new_secret_123456789012345678901234567890'

        serializer = AzureSubscriptionUpdateSerializer(
            self.subscription,
            data={'client_secret': new_secret},
            partial=True
        )

        self.assertTrue(serializer.is_valid())
        subscription = serializer.save()

        # Verify secret was re-encrypted and can be decrypted
        self.assertEqual(subscription.client_secret, new_secret)
        self.assertNotEqual(
            subscription.client_secret_encrypted,
            'new_secret_123456789012345678901234567890'  # Should be encrypted
        )

    def test_update_without_secret_preserves_existing(self):
        """Test update without client_secret preserves existing encrypted secret."""
        original_encrypted = self.subscription.client_secret_encrypted

        serializer = AzureSubscriptionUpdateSerializer(
            self.subscription,
            data={'name': 'New Name'},
            partial=True
        )

        self.assertTrue(serializer.is_valid())
        subscription = serializer.save()

        # Secret should remain unchanged
        self.assertEqual(subscription.client_secret_encrypted, original_encrypted)
        self.assertEqual(subscription.client_secret, 'original_secret_12345678901234567890')

    def test_update_is_active_status(self):
        """Test updating is_active status."""
        serializer = AzureSubscriptionUpdateSerializer(
            self.subscription,
            data={'is_active': False},
            partial=True
        )

        self.assertTrue(serializer.is_valid())
        subscription = serializer.save()
        self.assertFalse(subscription.is_active)

    def test_update_tenant_and_client_id(self):
        """Test updating tenant_id and client_id."""
        data = {
            'tenant_id': '880e8400-e29b-41d4-a716-446655440000',
            'client_id': '990e8400-e29b-41d4-a716-446655440000',
        }

        serializer = AzureSubscriptionUpdateSerializer(
            self.subscription,
            data=data,
            partial=True
        )

        self.assertTrue(serializer.is_valid())
        subscription = serializer.save()

        self.assertEqual(subscription.tenant_id, '880e8400-e29b-41d4-a716-446655440000')
        self.assertEqual(subscription.client_id, '990e8400-e29b-41d4-a716-446655440000')

    def test_subscription_id_cannot_be_changed(self):
        """Test subscription_id is not in updatable fields."""
        serializer = AzureSubscriptionUpdateSerializer(
            self.subscription,
            data={'subscription_id': '999e8400-e29b-41d4-a716-446655440000'},
            partial=True
        )

        # Field should be ignored (not cause error)
        self.assertTrue(serializer.is_valid())
        subscription = serializer.save()

        # subscription_id should remain unchanged
        self.assertEqual(subscription.subscription_id, '550e8400-e29b-41d4-a716-446655440000')

    def test_update_with_invalid_secret(self):
        """Test update fails with invalid client_secret."""
        serializer = AzureSubscriptionUpdateSerializer(
            self.subscription,
            data={'client_secret': 'short'},  # Too short
            partial=True
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('client_secret', serializer.errors)


class ValidatorTestCase(TestCase):
    """Tests for custom validators."""

    def test_validate_uuid_format_with_valid_uuid(self):
        """Test UUID validation with valid UUIDs."""
        valid_uuids = [
            '550e8400-e29b-41d4-a716-446655440000',
            '550E8400-E29B-41D4-A716-446655440000',  # Uppercase
            '550e8400e29b41d4a716446655440000',  # No hyphens
        ]

        for uuid_str in valid_uuids:
            result = validate_uuid_format(uuid_str)
            self.assertIsNotNone(result)
            self.assertEqual(result, uuid_str.lower())

    def test_validate_uuid_format_with_invalid_uuid(self):
        """Test UUID validation with invalid formats."""
        invalid_uuids = [
            'not-a-uuid',
            '550e8400',  # Too short
            '550e8400-e29b-41d4-a716',  # Incomplete
            'ggge8400-e29b-41d4-a716-446655440000',  # Invalid characters
            '',  # Empty
        ]

        for uuid_str in invalid_uuids:
            with self.assertRaises(ValidationError):
                validate_uuid_format(uuid_str)

    def test_validate_subscription_id_uniqueness(self):
        """Test subscription_id uniqueness check."""
        # Create existing subscription
        AzureSubscription.objects.create(
            name='Existing',
            subscription_id='550e8400-e29b-41d4-a716-446655440000',
            tenant_id='660e8400-e29b-41d4-a716-446655440000',
            client_id='770e8400-e29b-41d4-a716-446655440000',
        )

        # Try to validate duplicate (case-insensitive)
        with self.assertRaises(ValidationError) as context:
            validate_subscription_id('550E8400-E29B-41D4-A716-446655440000')

        self.assertIn('already exists', str(context.exception))

    def test_validate_client_secret_length(self):
        """Test client_secret length validation."""
        # Too short
        with self.assertRaises(ValidationError) as context:
            validate_client_secret('short')
        self.assertIn('at least 20 characters', str(context.exception))

        # Too long
        with self.assertRaises(ValidationError) as context:
            validate_client_secret('x' * 201)
        self.assertIn('cannot exceed 200 characters', str(context.exception))

        # Valid length
        result = validate_client_secret('valid_secret_1234567890123456789012345')
        self.assertEqual(result, 'valid_secret_1234567890123456789012345')

    def test_validate_client_secret_no_spaces(self):
        """Test client_secret rejects spaces."""
        with self.assertRaises(ValidationError) as context:
            validate_client_secret('secret with spaces 1234567890')
        self.assertIn('cannot contain spaces', str(context.exception))


class AzureSubscriptionListSerializerTestCase(TestCase):
    """Tests for AzureSubscriptionListSerializer (lightweight)."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.subscription = AzureSubscription.objects.create(
            name='Test Subscription',
            subscription_id='550e8400-e29b-41d4-a716-446655440000',
            tenant_id='660e8400-e29b-41d4-a716-446655440000',
            client_id='770e8400-e29b-41d4-a716-446655440000',
            created_by=self.user,
        )

    def test_list_serialization_minimal_fields(self):
        """Test list serializer includes only minimal fields."""
        serializer = AzureSubscriptionListSerializer(self.subscription)
        data = serializer.data

        expected_fields = {
            'id', 'name', 'subscription_id', 'is_active',
            'sync_status', 'last_sync_at', 'created_by_name', 'created_at'
        }

        self.assertEqual(set(data.keys()), expected_fields)

    def test_created_by_name_formatting(self):
        """Test created_by_name returns full name or username."""
        serializer = AzureSubscriptionListSerializer(self.subscription)
        data = serializer.data

        self.assertEqual(data['created_by_name'], 'Test User')

        # Test with user without full name
        user2 = User.objects.create_user(username='noname', email='no@example.com')
        sub2 = AzureSubscription.objects.create(
            name='Sub 2',
            subscription_id='660e8400-e29b-41d4-a716-446655440000',
            tenant_id='770e8400-e29b-41d4-a716-446655440000',
            client_id='880e8400-e29b-41d4-a716-446655440000',
            created_by=user2,
        )

        serializer2 = AzureSubscriptionListSerializer(sub2)
        data2 = serializer2.data
        self.assertEqual(data2['created_by_name'], 'noname')
