"""
Django REST Framework serializers for Azure Integration.

This module provides serializers for AzureSubscription model with support for:
- Secure credential handling (encryption/decryption)
- Comprehensive validation
- Separate serializers for different operations (list, create, update)
"""

from rest_framework import serializers
from apps.azure_integration.models import AzureSubscription
from apps.authentication.serializers import UserListSerializer
from apps.azure_integration.validators import (
    validate_uuid_format,
    validate_subscription_id,
    validate_client_secret,
)


class AzureSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for listing and retrieving Azure subscriptions.

    This is a read-only serializer that exposes all subscription details
    except the encrypted client secret for security.

    Fields:
        - All model fields except client_secret_encrypted (security)
        - created_by: Nested user representation with id, username, full_name
        - All timestamp fields for auditing
    """

    created_by = UserListSerializer(read_only=True)
    client_id_field = serializers.UUIDField(source='client.id', read_only=True)
    client_name = serializers.CharField(source='client.company_name', read_only=True)

    class Meta:
        model = AzureSubscription
        fields = [
            'id',
            'client',
            'client_id_field',
            'client_name',
            'name',
            'subscription_id',
            'tenant_id',
            'azure_client_id',
            'is_active',
            'sync_status',
            'sync_error_message',
            'last_sync_at',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'client_id_field',
            'client_name',
            'sync_status',
            'sync_error_message',
            'last_sync_at',
            'created_by',
            'created_at',
            'updated_at',
        ]

    def validate_subscription_id(self, value):
        """Validate subscription ID format."""
        return validate_uuid_format(value)

    def validate_tenant_id(self, value):
        """Validate tenant ID format."""
        return validate_uuid_format(value)

    def validate_azure_client_id(self, value):
        """Validate Azure client ID format."""
        return validate_uuid_format(value)

    def validate_name(self, value):
        """Validate subscription name."""
        if not value or not value.strip():
            raise serializers.ValidationError('Name cannot be empty.')

        if len(value) > 200:
            raise serializers.ValidationError('Name cannot exceed 200 characters.')

        return value.strip()


class AzureSubscriptionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new Azure subscriptions.

    Handles secure credential collection and encryption. The client_secret
    field is write-only and will be encrypted before storage.

    Required Fields:
        - name: User-friendly subscription name
        - subscription_id: Azure subscription UUID
        - tenant_id: Azure tenant UUID
        - client_id: Service principal client UUID
        - client_secret: Service principal secret (write-only, encrypted on save)

    Optional Fields:
        - is_active: Whether subscription is active (default: True)
    """

    client_secret = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Azure Service Principal client secret (will be encrypted)'
    )

    class Meta:
        model = AzureSubscription
        fields = [
            'client',
            'name',
            'subscription_id',
            'tenant_id',
            'azure_client_id',
            'client_secret',
            'is_active',
        ]

    def validate_name(self, value):
        """Validate subscription name."""
        if not value or not value.strip():
            raise serializers.ValidationError('Name is required.')

        value = value.strip()

        if len(value) < 1:
            raise serializers.ValidationError('Name must be at least 1 character.')

        if len(value) > 200:
            raise serializers.ValidationError('Name cannot exceed 200 characters.')

        return value

    def validate_subscription_id(self, value):
        """
        Validate subscription ID format and uniqueness.

        Uses custom validator that checks UUID format and ensures
        no duplicate subscription IDs exist (case-insensitive).
        """
        return validate_subscription_id(value)

    def validate_tenant_id(self, value):
        """Validate tenant ID UUID format."""
        return validate_uuid_format(value)

    def validate_azure_client_id(self, value):
        """Validate Azure client ID UUID format."""
        return validate_uuid_format(value)

    def validate_client_secret(self, value):
        """
        Validate client secret meets security requirements.

        Requirements:
        - Minimum 20 characters
        - Maximum 200 characters
        - No spaces (prevents copy-paste errors)
        """
        return validate_client_secret(value)

    def create(self, validated_data):
        """
        Create AzureSubscription with encrypted client secret.

        The client_secret is automatically encrypted via the model's
        property setter before storage. The created_by field is set
        from the request user.

        Args:
            validated_data: Validated data from serializer

        Returns:
            AzureSubscription: Created subscription instance

        Note:
            Encryption happens transparently via model property.
            Plain text secret is never stored in database.
        """
        # Extract client_secret before creating instance
        client_secret = validated_data.pop('client_secret')

        # Create instance (without secret)
        subscription = AzureSubscription(**validated_data)

        # Set encrypted secret via property
        subscription.client_secret = client_secret

        # Set created_by from request context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            subscription.created_by = request.user

        subscription.save()
        return subscription


class AzureSubscriptionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Azure subscriptions.

    Allows updating most fields while protecting subscription_id from changes.
    The client_secret is optional - only updated if provided.

    Updatable Fields:
        - name: Subscription name
        - is_active: Active status
        - tenant_id: Tenant ID (optional)
        - client_id: Client ID (optional)
        - client_secret: Client secret (optional, write-only, re-encrypted)

    Read-Only Fields:
        - subscription_id: Cannot be changed after creation
        - All sync status and audit fields
    """

    client_secret = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        style={'input_type': 'password'},
        help_text='New client secret (optional, will be re-encrypted if provided)'
    )

    class Meta:
        model = AzureSubscription
        fields = [
            'name',
            'tenant_id',
            'azure_client_id',
            'client_secret',
            'is_active',
        ]

    def validate_name(self, value):
        """Validate subscription name."""
        if not value or not value.strip():
            raise serializers.ValidationError('Name cannot be empty.')

        value = value.strip()

        if len(value) > 200:
            raise serializers.ValidationError('Name cannot exceed 200 characters.')

        return value

    def validate_tenant_id(self, value):
        """Validate tenant ID UUID format."""
        return validate_uuid_format(value)

    def validate_azure_client_id(self, value):
        """Validate Azure client ID UUID format."""
        return validate_uuid_format(value)

    def validate_client_secret(self, value):
        """
        Validate client secret if provided.

        Same security requirements as creation:
        - Minimum 20 characters
        - Maximum 200 characters
        - No spaces
        """
        return validate_client_secret(value)

    def update(self, instance, validated_data):
        """
        Update AzureSubscription instance.

        If client_secret is provided, it will be re-encrypted with the
        new value. Other fields are updated normally.

        Args:
            instance: Existing AzureSubscription instance
            validated_data: Validated update data

        Returns:
            AzureSubscription: Updated subscription instance

        Note:
            - subscription_id cannot be changed (not in fields)
            - client_secret is re-encrypted if provided
            - If secret not provided, existing encrypted secret remains
        """
        # Extract client_secret if provided
        client_secret = validated_data.pop('client_secret', None)

        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Re-encrypt secret if new one provided
        if client_secret:
            instance.client_secret = client_secret  # Uses property setter

        instance.save()
        return instance


class AzureSubscriptionListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing Azure subscriptions.

    Provides minimal fields for list views to improve performance.
    """

    created_by_name = serializers.SerializerMethodField()
    client_name = serializers.CharField(source='client.company_name', read_only=True)

    class Meta:
        model = AzureSubscription
        fields = [
            'id',
            'client',
            'client_name',
            'name',
            'subscription_id',
            'is_active',
            'sync_status',
            'last_sync_at',
            'created_by_name',
            'created_at',
        ]
        read_only_fields = '__all__'

    def get_created_by_name(self, obj):
        """Get full name of creator."""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None
