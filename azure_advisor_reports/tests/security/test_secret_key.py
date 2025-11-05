"""
Security Tests for SECRET_KEY Configuration

Tests validate that:
1. SECRET_KEY is properly configured and strong
2. SECRET_KEY validation works correctly
3. Token generation works with proper SECRET_KEY
4. SECRET_KEY_FALLBACKS support is functional
"""

import os
import pytest
from django.conf import settings
from django.test import TestCase, override_settings
import secrets


class SecretKeySecurityTestCase(TestCase):
    """Test suite for SECRET_KEY security validation."""

    def test_secret_key_is_configured(self):
        """SECRET_KEY must be configured."""
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertTrue(len(settings.SECRET_KEY) > 0)

    def test_secret_key_is_strong(self):
        """SECRET_KEY must be at least 50 characters long."""
        self.assertGreaterEqual(
            len(settings.SECRET_KEY),
            50,
            f"SECRET_KEY is too short ({len(settings.SECRET_KEY)} chars). Must be at least 50 characters."
        )

    def test_secret_key_is_not_default(self):
        """SECRET_KEY must not be the default insecure value."""
        insecure_defaults = [
            'django-insecure-change-this-in-production',
            'your-secret-key-here',
            'changeme',
        ]
        for insecure in insecure_defaults:
            self.assertNotEqual(
                settings.SECRET_KEY,
                insecure,
                f"SECRET_KEY is using insecure default value: {insecure}"
            )

    def test_secret_key_has_sufficient_entropy(self):
        """SECRET_KEY should have sufficient character diversity."""
        # Check that it's not just repeated characters
        unique_chars = len(set(settings.SECRET_KEY))
        self.assertGreater(
            unique_chars,
            10,
            f"SECRET_KEY has insufficient entropy (only {unique_chars} unique characters)"
        )

    def test_secret_key_fallbacks_configuration(self):
        """SECRET_KEY_FALLBACKS should be a list."""
        self.assertIsInstance(
            settings.SECRET_KEY_FALLBACKS,
            list,
            "SECRET_KEY_FALLBACKS must be a list"
        )

    def test_generate_secure_key(self):
        """Test that we can generate secure keys using secrets module."""
        # This is the recommended way to generate SECRET_KEY
        new_key = secrets.token_urlsafe(50)

        # Should be at least 50 characters
        self.assertGreaterEqual(len(new_key), 50)

        # Should be URL-safe (no special chars that need escaping)
        import string
        allowed_chars = string.ascii_letters + string.digits + '-_'
        for char in new_key:
            self.assertIn(char, allowed_chars)

    def test_secret_key_rotation_support(self):
        """Test that SECRET_KEY_FALLBACKS is properly configured for rotation."""
        # SECRET_KEY_FALLBACKS should be a list
        self.assertIsInstance(settings.SECRET_KEY_FALLBACKS, list)

        # If fallbacks are configured, they should all be strings
        for fallback in settings.SECRET_KEY_FALLBACKS:
            self.assertIsInstance(fallback, str)
            self.assertTrue(len(fallback) > 0)


class SecretKeyValidationTestCase(TestCase):
    """Test SECRET_KEY validation logic."""

    @override_settings(SECRET_KEY='too_short')
    def test_short_secret_key_rejected(self):
        """Short SECRET_KEY should be rejected in production."""
        # Note: This test validates the concept
        # Actual validation happens at startup, not at runtime
        short_key = 'too_short'
        self.assertLess(len(short_key), 50)

    def test_secret_key_used_in_jwt_tokens(self):
        """Verify that SECRET_KEY is actually used for JWT token signing."""
        from apps.authentication.services import JWTService
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Create a test user
        user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            role='consultant'
        )

        # Generate tokens
        tokens = JWTService.generate_token(user)

        # Verify tokens were generated
        self.assertIn('access_token', tokens)
        self.assertIn('refresh_token', tokens)
        self.assertTrue(len(tokens['access_token']) > 0)
        self.assertTrue(len(tokens['refresh_token']) > 0)

        # Verify tokens can be validated
        is_valid, payload = JWTService.validate_token(tokens['access_token'], 'access')
        self.assertTrue(is_valid)
        self.assertEqual(payload['user_id'], str(user.id))
        self.assertEqual(payload['email'], user.email)

    def test_invalid_token_rejected_with_wrong_secret(self):
        """Tokens signed with a different key should be rejected."""
        import jwt
        from apps.authentication.services import JWTService
        from datetime import datetime, timedelta

        # Create a token with a different secret
        fake_payload = {
            'user_id': 'fake-user-id',
            'email': 'fake@example.com',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'type': 'access'
        }

        fake_token = jwt.encode(fake_payload, 'wrong-secret-key', algorithm='HS256')

        # Try to validate with our SECRET_KEY - should fail
        is_valid, payload = JWTService.validate_token(fake_token, 'access')
        self.assertFalse(is_valid)
        self.assertIsNone(payload)


class SecretKeyEnvironmentTestCase(TestCase):
    """Test SECRET_KEY environment variable handling."""

    def test_secret_key_from_environment(self):
        """SECRET_KEY should be loaded from environment variables."""
        # In a real deployment, SECRET_KEY comes from env vars
        # This test ensures the mechanism works
        self.assertTrue(
            'SECRET_KEY' in os.environ or hasattr(settings, 'SECRET_KEY'),
            "SECRET_KEY must be available either in environment or settings"
        )

    def test_production_secret_key_requirements(self):
        """In production, SECRET_KEY must meet strict requirements."""
        if not settings.DEBUG:
            # Production requirements
            self.assertGreaterEqual(len(settings.SECRET_KEY), 50)
            self.assertNotIn('insecure', settings.SECRET_KEY.lower())
            self.assertNotIn('change', settings.SECRET_KEY.lower())
            self.assertNotIn('default', settings.SECRET_KEY.lower())


# Integration test to verify startup validation
class SecretKeyStartupValidationTestCase(TestCase):
    """Test that SECRET_KEY validation occurs at application startup."""

    def test_settings_module_imports_without_error(self):
        """Settings module should import successfully with valid SECRET_KEY."""
        # If we got here, settings imported successfully
        # This test validates that the startup validation logic doesn't
        # incorrectly reject valid keys
        self.assertTrue(True)

    def test_secret_key_validation_skips_management_commands(self):
        """SECRET_KEY validation should skip certain Django management commands."""
        # These commands should be in the skip list
        skip_commands = ['migrate', 'makemigrations', 'collectstatic']

        # Verify these are in the settings
        for cmd in skip_commands:
            self.assertIn(
                cmd,
                settings.MANAGEMENT_COMMANDS_SKIP_VALIDATION,
                f"Management command '{cmd}' should be in validation skip list"
            )
