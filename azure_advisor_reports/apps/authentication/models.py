"""
Authentication models for user profiles and Azure AD integration.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Extended user model with Azure AD integration and role-based access control.
    """
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('analyst', 'Analyst'),
        ('viewer', 'Viewer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    azure_object_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    tenant_id = models.CharField(max_length=255, null=True, blank=True)

    # Role-based access control
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='analyst',
        help_text="User role for permission management"
    )

    # Profile information
    job_title = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'auth_user_extended'
        indexes = [
            models.Index(fields=['azure_object_id']),
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active', 'role']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class UserSession(models.Model):
    """
    Track user sessions for security monitoring.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'auth_user_session'

    def __str__(self):
        return f"Session for {self.user.email} from {self.ip_address}"


class TokenBlacklist(models.Model):
    """
    Track JWT tokens for revocation and blacklisting.

    This model stores JWT tokens with their unique JTI (JWT ID) to enable
    token revocation and blacklisting. Tokens can be revoked during logout,
    password changes, or security incidents. Expired tokens are periodically
    cleaned up to maintain database performance.

    Security Features:
    - Unique JTI ensures each token is trackable
    - is_revoked flag enables immediate token invalidation
    - expires_at enables automatic cleanup of old tokens
    - Database indexes optimize blacklist checks for performance
    """
    TOKEN_TYPE_CHOICES = [
        ('access', 'Access Token'),
        ('refresh', 'Refresh Token'),
    ]

    jti = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="JWT ID - unique identifier for this token"
    )
    token_type = models.CharField(
        max_length=10,
        choices=TOKEN_TYPE_CHOICES,
        help_text="Type of token (access or refresh)"
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='jwt_tokens',
        help_text="User who owns this token"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the token was created"
    )
    expires_at = models.DateTimeField(
        help_text="When the token expires"
    )
    is_revoked = models.BooleanField(
        default=False,
        help_text="Whether the token has been revoked"
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the token was revoked"
    )
    revoked_reason = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reason for token revocation (logout, security, etc.)"
    )

    class Meta:
        db_table = 'auth_token_blacklist'
        indexes = [
            models.Index(fields=['jti', 'is_revoked'], name='idx_jti_revoked'),
            models.Index(fields=['expires_at'], name='idx_expires_at'),
            models.Index(fields=['user', 'token_type'], name='idx_user_token_type'),
            models.Index(fields=['created_at'], name='idx_created_at'),
        ]
        ordering = ['-created_at']
        verbose_name = 'Token Blacklist Entry'
        verbose_name_plural = 'Token Blacklist Entries'

    def __str__(self):
        status = 'Revoked' if self.is_revoked else 'Active'
        return f"{self.get_token_type_display()} for {self.user.email} - {status}"

    @classmethod
    def cleanup_expired(cls):
        """
        Remove expired tokens from database.

        This method should be called periodically (via cron or Celery task)
        to remove tokens that have expired and are no longer needed for
        blacklist checks.

        Returns:
            int: Number of tokens deleted
        """
        from django.utils import timezone
        deleted_count, _ = cls.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()
        return deleted_count

    @classmethod
    def revoke_user_tokens(cls, user, reason='security'):
        """
        Revoke all active tokens for a specific user.

        This is useful when a user's account is compromised or when
        a password is changed.

        Args:
            user: User instance
            reason: Reason for revocation (default: 'security')

        Returns:
            int: Number of tokens revoked
        """
        from django.utils import timezone
        count = cls.objects.filter(
            user=user,
            is_revoked=False
        ).update(
            is_revoked=True,
            revoked_at=timezone.now(),
            revoked_reason=reason
        )
        return count

    def revoke(self, reason='manual'):
        """
        Revoke this specific token.

        Args:
            reason: Reason for revocation (default: 'manual')
        """
        from django.utils import timezone
        self.is_revoked = True
        self.revoked_at = timezone.now()
        self.revoked_reason = reason
        self.save(update_fields=['is_revoked', 'revoked_at', 'revoked_reason'])