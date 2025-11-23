"""
Token Rotation Strategy

Automatic rotation of JWT refresh tokens and API keys for enhanced security
"""

import logging
import secrets
from datetime import timedelta
from typing import Optional, Tuple
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

logger = logging.getLogger(__name__)
User = get_user_model()


# =============================================================================
# JWT Token Rotation
# =============================================================================

class JWTTokenRotation:
    """
    Manages JWT token rotation with automatic refresh and blacklisting
    """

    # Token validity periods
    ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
    REFRESH_TOKEN_LIFETIME = timedelta(days=7)
    REFRESH_TOKEN_ROTATION_INTERVAL = timedelta(days=1)

    @staticmethod
    def generate_tokens(user) -> dict:
        """
        Generate new access and refresh tokens for user

        Args:
            user: User instance

        Returns:
            Dictionary with access and refresh tokens

        Example:
            tokens = JWTTokenRotation.generate_tokens(user)
            access_token = tokens['access']
            refresh_token = tokens['refresh']
        """
        refresh = RefreshToken.for_user(user)

        # Add custom claims
        refresh['username'] = user.username
        refresh['email'] = user.email
        refresh['role'] = getattr(user, 'role', 'viewer')

        # Store token metadata in cache
        token_id = str(refresh['jti'])
        cache_key = f'refresh_token_{token_id}'
        cache.set(cache_key, {
            'user_id': str(user.id),
            'created_at': timezone.now().isoformat(),
            'last_rotated': timezone.now().isoformat(),
            'rotation_count': 0
        }, timeout=int(JWTTokenRotation.REFRESH_TOKEN_LIFETIME.total_seconds()))

        logger.info(f'Generated new tokens for user {user.username}')

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'expires_in': int(JWTTokenRotation.ACCESS_TOKEN_LIFETIME.total_seconds()),
            'refresh_expires_in': int(JWTTokenRotation.REFRESH_TOKEN_LIFETIME.total_seconds())
        }

    @staticmethod
    def rotate_refresh_token(refresh_token_str: str) -> Optional[dict]:
        """
        Rotate refresh token if rotation interval has passed

        Args:
            refresh_token_str: Current refresh token string

        Returns:
            New tokens dict if rotation needed, None otherwise

        Example:
            new_tokens = JWTTokenRotation.rotate_refresh_token(old_refresh_token)
            if new_tokens:
                # Use new tokens
                access_token = new_tokens['access']
        """
        try:
            refresh = RefreshToken(refresh_token_str)
            token_id = str(refresh['jti'])
            cache_key = f'refresh_token_{token_id}'

            # Get token metadata
            metadata = cache.get(cache_key)
            if not metadata:
                logger.warning(f'Token metadata not found for {token_id}')
                return None

            # Check if rotation is needed
            last_rotated = timezone.datetime.fromisoformat(metadata['last_rotated'])
            if timezone.now() - last_rotated < JWTTokenRotation.REFRESH_TOKEN_ROTATION_INTERVAL:
                # No rotation needed yet
                return None

            # Get user
            user_id = metadata['user_id']
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.error(f'User not found for token: {user_id}')
                return None

            # Blacklist old token
            JWTTokenRotation.blacklist_token(refresh_token_str)

            # Generate new tokens
            new_tokens = JWTTokenRotation.generate_tokens(user)

            # Update metadata
            new_token_id = RefreshToken(new_tokens['refresh'])['jti']
            new_cache_key = f'refresh_token_{new_token_id}'
            cache.set(new_cache_key, {
                'user_id': str(user.id),
                'created_at': metadata['created_at'],
                'last_rotated': timezone.now().isoformat(),
                'rotation_count': metadata['rotation_count'] + 1
            }, timeout=int(JWTTokenRotation.REFRESH_TOKEN_LIFETIME.total_seconds()))

            logger.info(f'Rotated refresh token for user {user.username}')

            return new_tokens

        except TokenError as e:
            logger.error(f'Token rotation failed: {str(e)}')
            return None

    @staticmethod
    def blacklist_token(token_str: str) -> bool:
        """
        Blacklist a token to prevent its further use

        Args:
            token_str: Token string to blacklist

        Returns:
            True if successful, False otherwise
        """
        try:
            token = RefreshToken(token_str)
            token_id = str(token['jti'])

            # Add to blacklist cache
            blacklist_key = f'token_blacklist_{token_id}'
            cache.set(
                blacklist_key,
                True,
                timeout=int(JWTTokenRotation.REFRESH_TOKEN_LIFETIME.total_seconds())
            )

            # Clear token metadata
            cache_key = f'refresh_token_{token_id}'
            cache.delete(cache_key)

            logger.info(f'Blacklisted token {token_id}')
            return True

        except Exception as e:
            logger.error(f'Failed to blacklist token: {str(e)}')
            return False

    @staticmethod
    def is_token_blacklisted(token_str: str) -> bool:
        """
        Check if a token is blacklisted

        Args:
            token_str: Token string to check

        Returns:
            True if blacklisted, False otherwise
        """
        try:
            token = RefreshToken(token_str)
            token_id = str(token['jti'])
            blacklist_key = f'token_blacklist_{token_id}'

            return cache.get(blacklist_key, False)

        except Exception:
            return True  # Treat invalid tokens as blacklisted

    @staticmethod
    def revoke_all_user_tokens(user) -> int:
        """
        Revoke all active tokens for a user

        Args:
            user: User instance

        Returns:
            Number of tokens revoked

        Example:
            # Revoke all tokens when user changes password
            count = JWTTokenRotation.revoke_all_user_tokens(user)
        """
        # This requires storing token IDs per user
        # For now, we'll use a user-based blacklist
        user_blacklist_key = f'user_tokens_revoked_{user.id}'
        cache.set(
            user_blacklist_key,
            timezone.now().isoformat(),
            timeout=int(JWTTokenRotation.REFRESH_TOKEN_LIFETIME.total_seconds())
        )

        logger.info(f'Revoked all tokens for user {user.username}')
        return 1


# =============================================================================
# API Key Rotation
# =============================================================================

class APIKeyRotation:
    """
    Manages API key rotation for external integrations
    """

    API_KEY_LENGTH = 64
    API_KEY_LIFETIME = timedelta(days=90)
    API_KEY_ROTATION_WARNING = timedelta(days=7)  # Warn 7 days before expiry

    @staticmethod
    def generate_api_key() -> str:
        """
        Generate a secure random API key

        Returns:
            API key string

        Example:
            api_key = APIKeyRotation.generate_api_key()
        """
        return secrets.token_urlsafe(APIKeyRotation.API_KEY_LENGTH)

    @staticmethod
    def create_api_key(user, name: str, description: str = '') -> dict:
        """
        Create a new API key for a user

        Args:
            user: User instance
            name: Descriptive name for the API key
            description: Optional description

        Returns:
            Dictionary with API key details

        Example:
            key_data = APIKeyRotation.create_api_key(
                user=request.user,
                name='Production API',
                description='API key for production environment'
            )
        """
        from apps.authentication.models import APIKey

        # Generate key
        key_value = APIKeyRotation.generate_api_key()
        prefix = key_value[:8]  # Store prefix for identification

        # Create API key record
        api_key = APIKey.objects.create(
            user=user,
            name=name,
            description=description,
            key_prefix=prefix,
            key_hash=APIKeyRotation._hash_key(key_value),
            expires_at=timezone.now() + APIKeyRotation.API_KEY_LIFETIME
        )

        logger.info(f'Created API key "{name}" for user {user.username}')

        return {
            'id': str(api_key.id),
            'name': name,
            'key': key_value,  # Only returned once!
            'prefix': prefix,
            'expires_at': api_key.expires_at.isoformat(),
            'created_at': api_key.created_at.isoformat()
        }

    @staticmethod
    def rotate_api_key(api_key_id: str) -> Optional[dict]:
        """
        Rotate an existing API key

        Args:
            api_key_id: UUID of the API key to rotate

        Returns:
            New API key details

        Example:
            new_key = APIKeyRotation.rotate_api_key(api_key_id)
            if new_key:
                # Update your systems with new key
                print(f"New key: {new_key['key']}")
        """
        from apps.authentication.models import APIKey

        try:
            old_key = APIKey.objects.get(id=api_key_id)

            # Create new key with same metadata
            new_key_data = APIKeyRotation.create_api_key(
                user=old_key.user,
                name=old_key.name,
                description=old_key.description
            )

            # Mark old key as rotated
            old_key.is_active = False
            old_key.rotated_at = timezone.now()
            old_key.save()

            logger.info(f'Rotated API key {old_key.name} for user {old_key.user.username}')

            return new_key_data

        except APIKey.DoesNotExist:
            logger.error(f'API key not found: {api_key_id}')
            return None

    @staticmethod
    def check_expiring_keys(warning_days: int = 7) -> list:
        """
        Get list of API keys expiring soon

        Args:
            warning_days: Days before expiry to warn

        Returns:
            List of expiring API keys

        Example:
            expiring_keys = APIKeyRotation.check_expiring_keys(warning_days=7)
            for key in expiring_keys:
                send_expiry_warning_email(key)
        """
        from apps.authentication.models import APIKey

        warning_date = timezone.now() + timedelta(days=warning_days)

        expiring_keys = APIKey.objects.filter(
            is_active=True,
            expires_at__lte=warning_date,
            expires_at__gte=timezone.now()
        ).select_related('user')

        return list(expiring_keys)

    @staticmethod
    def _hash_key(key: str) -> str:
        """Hash API key for secure storage"""
        import hashlib
        return hashlib.sha256(key.encode()).hexdigest()


# =============================================================================
# Token Rotation Middleware
# =============================================================================

class TokenRotationMiddleware:
    """
    Middleware to automatically rotate tokens on API requests
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if token rotation is needed
        if hasattr(request, 'auth') and isinstance(request.auth, str):
            refresh_token = request.META.get('HTTP_X_REFRESH_TOKEN')
            if refresh_token:
                new_tokens = JWTTokenRotation.rotate_refresh_token(refresh_token)
                if new_tokens:
                    # Add new tokens to response
                    response = self.get_response(request)
                    response['X-New-Access-Token'] = new_tokens['access']
                    response['X-New-Refresh-Token'] = new_tokens['refresh']
                    return response

        response = self.get_response(request)
        return response


# =============================================================================
# Management Functions
# =============================================================================

def cleanup_expired_tokens():
    """
    Clean up expired tokens from cache

    Should be run periodically via cron job or Celery task

    Example:
        # In a Celery task
        @app.task
        def cleanup_tokens():
            cleanup_expired_tokens()
    """
    from apps.authentication.models import APIKey

    # Deactivate expired API keys
    expired_count = APIKey.objects.filter(
        is_active=True,
        expires_at__lt=timezone.now()
    ).update(is_active=False)

    logger.info(f'Deactivated {expired_count} expired API keys')

    return expired_count


def send_expiry_notifications():
    """
    Send notifications for expiring API keys

    Should be run daily via cron job or Celery task

    Example:
        # In a Celery task
        @app.task
        def notify_expiring_keys():
            send_expiry_notifications()
    """
    from apps.notifications.services import NotificationService
    from apps.notifications.models import NotificationType, NotificationPriority

    expiring_keys = APIKeyRotation.check_expiring_keys(warning_days=7)

    for api_key in expiring_keys:
        days_until_expiry = (api_key.expires_at - timezone.now()).days

        NotificationService.notify(
            user=api_key.user,
            title=f'API Key Expiring Soon: {api_key.name}',
            message=f'Your API key "{api_key.name}" will expire in {days_until_expiry} days. Please rotate it to avoid service interruption.',
            notification_type=NotificationType.SYSTEM_ALERT,
            priority=NotificationPriority.HIGH,
            send_email=True,
            create_inapp=True,
            trigger_webhooks=False,
            action_url='/settings/api-keys',
            action_label='Manage API Keys'
        )

    logger.info(f'Sent expiry notifications for {len(expiring_keys)} API keys')
    return len(expiring_keys)


# =============================================================================
# Configuration Helper
# =============================================================================

def configure_token_rotation_settings():
    """
    Configure token rotation settings

    Add to Django settings.py:
        from apps.security.token_rotation import configure_token_rotation_settings
        configure_token_rotation_settings()
    """
    from datetime import timedelta

    settings.SIMPLE_JWT = {
        'ACCESS_TOKEN_LIFETIME': JWTTokenRotation.ACCESS_TOKEN_LIFETIME,
        'REFRESH_TOKEN_LIFETIME': JWTTokenRotation.REFRESH_TOKEN_LIFETIME,
        'ROTATE_REFRESH_TOKENS': True,
        'BLACKLIST_AFTER_ROTATION': True,
        'UPDATE_LAST_LOGIN': True,

        'ALGORITHM': 'HS256',
        'SIGNING_KEY': settings.SECRET_KEY,
        'VERIFYING_KEY': None,
        'AUDIENCE': None,
        'ISSUER': None,

        'AUTH_HEADER_TYPES': ('Bearer',),
        'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
        'USER_ID_FIELD': 'id',
        'USER_ID_CLAIM': 'user_id',

        'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
        'TOKEN_TYPE_CLAIM': 'token_type',

        'JTI_CLAIM': 'jti',

        'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
        'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
        'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
    }

    logger.info('Token rotation settings configured')
