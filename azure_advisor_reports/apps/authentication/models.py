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