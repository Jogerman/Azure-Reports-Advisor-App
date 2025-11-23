"""
Models for Azure Integration app.

This module defines the AzureSubscription model for securely storing
Azure credentials and tracking synchronization status.
"""

import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from apps.core.encryption import encrypt_credential, decrypt_credential


# UUID validator for Azure IDs
uuid_validator = RegexValidator(
    regex=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    message='Enter a valid UUID.',
    code='invalid_uuid'
)


class AzureSubscription(models.Model):
    """
    Azure Subscription credentials for direct API integration.

    Stores encrypted Azure Service Principal credentials for authenticating
    with Azure APIs to fetch Advisor recommendations.

    Security:
        - client_secret is stored encrypted using Fernet encryption
        - Uses shared encryption module from apps.core.encryption
        - Encryption key derived from Django SECRET_KEY

    Sync Status:
        - never_synced: Initial state, no API fetch attempted
        - success: Last sync completed successfully
        - failed: Last sync failed (see sync_error_message for details)
    """

    SYNC_STATUS_CHOICES = [
        ('never_synced', 'Never Synced'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Client relationship
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='azure_subscriptions',
        help_text="Client that owns this Azure subscription"
    )

    # User-friendly identification
    name = models.CharField(
        max_length=200,
        help_text="User-friendly name for this subscription (e.g., 'Production Account')"
    )

    # Azure credentials (all UUIDs)
    subscription_id = models.CharField(
        max_length=36,
        unique=True,
        validators=[uuid_validator],
        help_text="Azure Subscription ID (UUID format)"
    )

    tenant_id = models.CharField(
        max_length=36,
        validators=[uuid_validator],
        help_text="Azure Tenant ID (UUID format)"
    )

    azure_client_id = models.CharField(
        max_length=36,
        validators=[uuid_validator],
        help_text="Azure Service Principal Client ID (UUID format)"
    )

    # Encrypted secret storage
    client_secret_encrypted = models.BinaryField(
        help_text="Encrypted client secret (stored using Fernet encryption)"
    )

    # Status and tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this subscription is active for syncing"
    )

    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default='never_synced',
        help_text="Status of the last synchronization attempt"
    )

    sync_error_message = models.TextField(
        blank=True,
        help_text="Error message from last failed sync"
    )

    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last successful API sync"
    )

    # Audit fields
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='azure_subscriptions',
        help_text="User who added this subscription"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'azure_subscriptions'
        ordering = ['-created_at']
        verbose_name = 'Azure Subscription'
        verbose_name_plural = 'Azure Subscriptions'
        indexes = [
            models.Index(fields=['subscription_id']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_sync_at']),
            models.Index(fields=['sync_status']),
        ]

    def __str__(self):
        """String representation showing name and subscription ID."""
        return f"{self.name} ({self.subscription_id})"

    @property
    def client_secret(self):
        """
        Decrypt and return the client secret.

        Returns:
            str: Decrypted client secret

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        if not self.client_secret_encrypted:
            return ''
        return decrypt_credential(self.client_secret_encrypted)

    @client_secret.setter
    def client_secret(self, value):
        """
        Encrypt and store the client secret.

        Args:
            value (str): Plain text client secret to encrypt
        """
        if value:
            self.client_secret_encrypted = encrypt_credential(value)
        else:
            self.client_secret_encrypted = b''

    def get_credentials(self):
        """
        Get all credentials as a dictionary with decrypted secret.

        Returns:
            dict: Dictionary containing:
                - tenant_id (str)
                - client_id (str)
                - client_secret (str) - decrypted
                - subscription_id (str)

        Example:
            >>> subscription = AzureSubscription.objects.get(name='Production')
            >>> creds = subscription.get_credentials()
            >>> # Use creds with Azure SDK
            >>> credential = ClientSecretCredential(
            ...     tenant_id=creds['tenant_id'],
            ...     client_id=creds['client_id'],
            ...     client_secret=creds['client_secret']
            ... )
        """
        return {
            'tenant_id': self.tenant_id,
            'client_id': self.azure_client_id,
            'client_secret': self.client_secret,  # Uses property to decrypt
            'subscription_id': self.subscription_id,
        }

    def update_sync_status(self, status, error_message=None):
        """
        Update the synchronization status.

        Args:
            status (str): One of 'success' or 'failed'
            error_message (str, optional): Error details if status is 'failed'

        Raises:
            ValueError: If status is not valid

        Example:
            >>> subscription.update_sync_status('success')
            >>> subscription.update_sync_status('failed', 'Connection timeout')
        """
        if status not in ['success', 'failed']:
            raise ValueError(f"Invalid status: {status}. Must be 'success' or 'failed'")

        self.sync_status = status

        if status == 'success':
            self.last_sync_at = timezone.now()
            self.sync_error_message = ''
        elif status == 'failed':
            self.sync_error_message = error_message or 'Unknown error'

        self.save(update_fields=['sync_status', 'last_sync_at', 'sync_error_message'])
