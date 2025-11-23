"""
Azure Key Vault Integration for Secrets Management

This module provides secure secret management using Azure Key Vault,
eliminating the need to store sensitive credentials in environment variables.
"""

import logging
from typing import Optional, Dict, Any
from functools import lru_cache
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Global Key Vault client
_key_vault_client = None


def get_key_vault_client():
    """
    Get or create the Azure Key Vault client

    Returns:
        SecretClient instance or None if Key Vault is not configured
    """
    global _key_vault_client

    if _key_vault_client is None:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient

            # Get Key Vault URL from settings
            key_vault_url = getattr(settings, 'AZURE_KEY_VAULT_URL', None)

            if not key_vault_url:
                logger.warning(
                    'Azure Key Vault URL not configured. '
                    'Set AZURE_KEY_VAULT_URL in settings or environment.'
                )
                return None

            # Use DefaultAzureCredential for authentication
            # This supports multiple authentication methods in order:
            # 1. Environment variables (for local development)
            # 2. Managed Identity (for Azure deployments)
            # 3. Azure CLI credentials
            # 4. Visual Studio Code credentials
            credential = DefaultAzureCredential()

            _key_vault_client = SecretClient(
                vault_url=key_vault_url,
                credential=credential
            )

            logger.info(f'Azure Key Vault client initialized: {key_vault_url}')

        except ImportError:
            logger.error(
                'Azure Key Vault libraries not installed. '
                'Run: pip install azure-identity azure-keyvault-secrets'
            )
            return None
        except Exception as e:
            logger.error(f'Failed to initialize Azure Key Vault client: {str(e)}')
            return None

    return _key_vault_client


@lru_cache(maxsize=128)
def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve a secret from Azure Key Vault

    Args:
        secret_name: Name of the secret in Key Vault
        default: Default value if secret not found

    Returns:
        Secret value or default

    Example:
        db_password = get_secret('database-password')
        api_key = get_secret('external-api-key', default='fallback-key')
    """
    # Try to get from cache first (short TTL for security)
    cache_key = f'keyvault_secret_{secret_name}'
    cached_value = cache.get(cache_key)

    if cached_value is not None:
        return cached_value

    client = get_key_vault_client()

    if client is None:
        logger.warning(f'Key Vault not available, using default for {secret_name}')
        return default

    try:
        secret = client.get_secret(secret_name)
        value = secret.value

        # Cache for 5 minutes (balance between performance and security)
        cache.set(cache_key, value, timeout=300)

        logger.debug(f'Retrieved secret: {secret_name}')
        return value

    except Exception as e:
        logger.error(f'Failed to retrieve secret {secret_name}: {str(e)}')
        return default


def get_secrets(secret_names: list) -> Dict[str, str]:
    """
    Retrieve multiple secrets from Azure Key Vault

    Args:
        secret_names: List of secret names

    Returns:
        Dictionary mapping secret names to values

    Example:
        secrets = get_secrets(['database-password', 'redis-password'])
        db_pass = secrets.get('database-password')
    """
    return {
        name: get_secret(name)
        for name in secret_names
    }


def set_secret(secret_name: str, secret_value: str) -> bool:
    """
    Store a secret in Azure Key Vault

    Args:
        secret_name: Name of the secret
        secret_value: Value to store

    Returns:
        True if successful, False otherwise

    Example:
        set_secret('new-api-key', 'secret-value-here')
    """
    client = get_key_vault_client()

    if client is None:
        logger.error('Key Vault not available, cannot set secret')
        return False

    try:
        client.set_secret(secret_name, secret_value)

        # Invalidate cache
        cache_key = f'keyvault_secret_{secret_name}'
        cache.delete(cache_key)

        logger.info(f'Secret set successfully: {secret_name}')
        return True

    except Exception as e:
        logger.error(f'Failed to set secret {secret_name}: {str(e)}')
        return False


def delete_secret(secret_name: str) -> bool:
    """
    Delete a secret from Azure Key Vault

    Note: Deleted secrets can be recovered within retention period

    Args:
        secret_name: Name of the secret to delete

    Returns:
        True if successful, False otherwise
    """
    client = get_key_vault_client()

    if client is None:
        logger.error('Key Vault not available, cannot delete secret')
        return False

    try:
        poller = client.begin_delete_secret(secret_name)
        deleted_secret = poller.result()

        # Invalidate cache
        cache_key = f'keyvault_secret_{secret_name}'
        cache.delete(cache_key)

        logger.info(f'Secret deleted: {secret_name}')
        return True

    except Exception as e:
        logger.error(f'Failed to delete secret {secret_name}: {str(e)}')
        return False


def list_secrets() -> list:
    """
    List all secret names in the Key Vault

    Returns:
        List of secret names

    Example:
        secret_names = list_secrets()
        for name in secret_names:
            print(name)
    """
    client = get_key_vault_client()

    if client is None:
        logger.error('Key Vault not available, cannot list secrets')
        return []

    try:
        secret_properties = client.list_properties_of_secrets()
        return [prop.name for prop in secret_properties]

    except Exception as e:
        logger.error(f'Failed to list secrets: {str(e)}')
        return []


def rotate_secret(secret_name: str, new_value: str) -> bool:
    """
    Rotate a secret by creating a new version

    Args:
        secret_name: Name of the secret to rotate
        new_value: New secret value

    Returns:
        True if successful, False otherwise

    Example:
        # Rotate API key
        new_key = generate_api_key()
        rotate_secret('external-api-key', new_key)
    """
    return set_secret(secret_name, new_value)


class SecretManager:
    """
    Context manager for working with secrets

    Usage:
        with SecretManager() as sm:
            db_pass = sm.get('database-password')
            api_key = sm.get('api-key')
    """

    def __init__(self):
        self.client = None
        self._secrets_cache = {}

    def __enter__(self):
        self.client = get_key_vault_client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._secrets_cache.clear()
        return False

    def get(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret"""
        if secret_name in self._secrets_cache:
            return self._secrets_cache[secret_name]

        value = get_secret(secret_name, default)
        self._secrets_cache[secret_name] = value
        return value

    def get_many(self, secret_names: list) -> Dict[str, str]:
        """Get multiple secrets"""
        return {name: self.get(name) for name in secret_names}


# =============================================================================
# Configuration Helper
# =============================================================================

def configure_from_key_vault(secret_mapping: Dict[str, str]) -> Dict[str, Any]:
    """
    Configure application settings from Key Vault

    Args:
        secret_mapping: Mapping of setting names to Key Vault secret names
                       {'SETTING_NAME': 'key-vault-secret-name'}

    Returns:
        Dictionary of configuration values

    Example:
        config = configure_from_key_vault({
            'DATABASE_PASSWORD': 'database-password',
            'SECRET_KEY': 'django-secret-key',
            'REDIS_PASSWORD': 'redis-password',
        })

        DATABASES['default']['PASSWORD'] = config['DATABASE_PASSWORD']
    """
    config = {}

    for setting_name, secret_name in secret_mapping.items():
        value = get_secret(secret_name)
        if value:
            config[setting_name] = value
        else:
            logger.warning(f'Secret not found for {setting_name}: {secret_name}')

    return config


# =============================================================================
# Common Secrets Helper
# =============================================================================

class SecretsConfig:
    """
    Pre-configured secrets for common use cases
    """

    @staticmethod
    def get_database_config() -> Dict[str, str]:
        """Get database configuration from Key Vault"""
        return {
            'password': get_secret('database-password'),
            'username': get_secret('database-username'),
            'host': get_secret('database-host'),
        }

    @staticmethod
    def get_azure_ad_config() -> Dict[str, str]:
        """Get Azure AD configuration from Key Vault"""
        return {
            'client_id': get_secret('azure-ad-client-id'),
            'client_secret': get_secret('azure-ad-client-secret'),
            'tenant_id': get_secret('azure-ad-tenant-id'),
        }

    @staticmethod
    def get_storage_config() -> Dict[str, str]:
        """Get Azure Storage configuration from Key Vault"""
        return {
            'account_name': get_secret('storage-account-name'),
            'account_key': get_secret('storage-account-key'),
            'connection_string': get_secret('storage-connection-string'),
        }

    @staticmethod
    def get_redis_config() -> Dict[str, str]:
        """Get Redis configuration from Key Vault"""
        return {
            'password': get_secret('redis-password'),
            'host': get_secret('redis-host'),
        }

    @staticmethod
    def get_application_insights_config() -> Dict[str, str]:
        """Get Application Insights configuration from Key Vault"""
        return {
            'connection_string': get_secret('appinsights-connection-string'),
            'instrumentation_key': get_secret('appinsights-instrumentation-key'),
        }

    @staticmethod
    def get_email_config() -> Dict[str, str]:
        """Get email configuration from Key Vault"""
        return {
            'smtp_password': get_secret('email-smtp-password'),
            'api_key': get_secret('email-api-key'),
        }


# =============================================================================
# Initialization Helper
# =============================================================================

def initialize_key_vault():
    """
    Initialize Key Vault connection on application startup

    Call this from Django's AppConfig.ready() method
    """
    client = get_key_vault_client()

    if client:
        logger.info('Azure Key Vault initialized successfully')

        # Pre-fetch critical secrets
        critical_secrets = [
            'database-password',
            'django-secret-key',
        ]

        for secret_name in critical_secrets:
            try:
                get_secret(secret_name)
            except Exception as e:
                logger.error(f'Failed to pre-fetch critical secret {secret_name}: {str(e)}')
    else:
        logger.warning('Azure Key Vault not configured - using environment variables')
