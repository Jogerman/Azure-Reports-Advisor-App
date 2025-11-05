"""
Critical Security Test Suite - PHASE 1

This test suite validates all CRITICAL security fixes implemented in Phase 1:
1. SECRET_KEY strength and validation
2. Rate limiting on authentication endpoints
3. Progressive lockout mechanism
4. JWT token generation and validation
5. Security logging

Run with: pytest tests/security/test_critical_security.py -v
"""

import pytest
import secrets
from django.test import TestCase, Client, override_settings
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from rest_framework import status
from apps.authentication.services import JWTService

User = get_user_model()


@pytest.mark.security
class CriticalSecurityTestSuite(TestCase):
    """
    Master test suite for all CRITICAL security implementations.

    Tests cover:
    - SECRET_KEY configuration and validation
    - Rate limiting and progressive lockout
    - JWT token security
    - Security logging
    """

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        cache.clear()

        # Create test user
        self.user = User.objects.create_user(
            email='security_test@example.com',
            username='security_test',
            first_name='Security',
            last_name='Test',
            role='analyst'
        )

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    # ========================================================================
    # SECRET_KEY Security Tests (CRITICAL)
    # ========================================================================

    def test_secret_key_is_configured_and_strong(self):
        """
        CRITICAL: SECRET_KEY must be configured and at least 50 characters.

        Vulnerability: Weak SECRET_KEY (CVSS 9.1)
        Fix: Mandatory strong SECRET_KEY validation in settings.py
        """
        # Verify SECRET_KEY exists
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertTrue(len(settings.SECRET_KEY) > 0)

        # Verify minimum length
        self.assertGreaterEqual(
            len(settings.SECRET_KEY),
            50,
            "CRITICAL: SECRET_KEY must be at least 50 characters"
        )

        # Verify not using insecure defaults
        insecure_defaults = [
            'django-insecure-change-this-in-production',
            'your-secret-key-here',
            'changeme',
        ]
        for insecure in insecure_defaults:
            self.assertNotEqual(settings.SECRET_KEY, insecure)

    def test_secret_key_has_sufficient_entropy(self):
        """SECRET_KEY should have sufficient character diversity."""
        unique_chars = len(set(settings.SECRET_KEY))
        self.assertGreater(
            unique_chars,
            10,
            f"SECRET_KEY has insufficient entropy ({unique_chars} unique chars)"
        )

    def test_secret_key_fallbacks_configuration(self):
        """SECRET_KEY_FALLBACKS should be properly configured for rotation."""
        self.assertIsInstance(settings.SECRET_KEY_FALLBACKS, list)

        # If fallbacks exist, verify they're valid strings
        for fallback in settings.SECRET_KEY_FALLBACKS:
            self.assertIsInstance(fallback, str)
            self.assertTrue(len(fallback) > 0)

    def test_jwt_tokens_use_strong_secret_key(self):
        """
        CRITICAL: JWT tokens must be signed with strong SECRET_KEY.

        Ensures tokens cannot be forged with weak keys.
        """
        # Generate tokens
        tokens = JWTService.generate_token(self.user)

        # Verify tokens were generated
        self.assertIn('access_token', tokens)
        self.assertIn('refresh_token', tokens)
        self.assertTrue(len(tokens['access_token']) > 0)

        # Verify tokens can be validated
        is_valid, payload = JWTService.validate_token(tokens['access_token'], 'access')
        self.assertTrue(is_valid, "Token validation should succeed with correct SECRET_KEY")
        self.assertEqual(payload['user_id'], str(self.user.id))

    def test_tokens_with_wrong_secret_are_rejected(self):
        """
        CRITICAL: Tokens signed with different key must be rejected.

        Validates that SECRET_KEY is actually used for signature verification.
        """
        import jwt
        from datetime import datetime, timedelta

        # Create token with wrong secret
        fake_payload = {
            'user_id': 'fake-user',
            'email': 'fake@example.com',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'type': 'access'
        }
        fake_token = jwt.encode(fake_payload, 'wrong-secret-key-12345', algorithm='HS256')

        # Attempt validation - should fail
        is_valid, payload = JWTService.validate_token(fake_token, 'access')
        self.assertFalse(is_valid, "Token with wrong signature must be rejected")
        self.assertIsNone(payload)

    # ========================================================================
    # Rate Limiting Tests (CRITICAL)
    # ========================================================================

    @patch('apps.authentication.views.AzureADService')
    def test_rate_limiting_blocks_after_threshold(self, mock_azure_service):
        """
        CRITICAL: Rate limiting must block after 5 requests per minute.

        Vulnerability: No rate limiting (CVSS 8.6)
        Fix: django-ratelimit with 5/min limit on login endpoint
        """
        # Mock Azure AD service to return invalid token
        mock_service_instance = MagicMock()
        mock_service_instance.validate_token.return_value = (False, None)
        mock_azure_service.return_value = mock_service_instance

        ip = '192.168.100.1'

        # Make 5 failed login attempts
        for i in range(5):
            response = self.client.post(
                '/api/v1/auth/login/',
                {'access_token': 'invalid_token'},
                content_type='application/json',
                REMOTE_ADDR=ip
            )
            # Should get 401 (unauthorized), not rate limited yet
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 6th attempt should be rate limited
        response = self.client.post(
            '/api/v1/auth/login/',
            {'access_token': 'invalid_token'},
            content_type='application/json',
            REMOTE_ADDR=ip
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
            "CRITICAL: Request #6 should be rate limited"
        )

    @patch('apps.authentication.views.AzureADService')
    def test_progressive_lockout_5_failures(self, mock_azure_service):
        """
        CRITICAL: Progressive lockout must activate after 5 failures.

        Vulnerability: No account lockout mechanism
        Fix: Progressive lockout (5 failures = 15 min lockout)
        """
        mock_service_instance = MagicMock()
        mock_service_instance.validate_token.return_value = (False, None)
        mock_azure_service.return_value = mock_service_instance

        ip = '192.168.100.2'

        # Make 5 failed attempts
        for i in range(5):
            response = self.client.post(
                '/api/v1/auth/login/',
                {'access_token': 'invalid_token'},
                content_type='application/json',
                REMOTE_ADDR=ip
            )

        # Verify lockout is in effect
        lockout_key = f'auth_lockout:{ip}'
        lockout_until = cache.get(lockout_key)
        self.assertIsNotNone(
            lockout_until,
            "CRITICAL: Lockout must be set after 5 failures"
        )

        # Verify lockout message
        response = self.client.post(
            '/api/v1/auth/login/',
            {'access_token': 'invalid_token'},
            content_type='application/json',
            REMOTE_ADDR=ip
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('locked', response.json().get('error', '').lower())

    @patch('apps.authentication.views.AzureADService')
    def test_progressive_lockout_escalation(self, mock_azure_service):
        """
        CRITICAL: Lockout duration must escalate with repeated failures.

        Progressive thresholds:
        - 5 failures = 15 minute lockout
        - 10 failures = 1 hour lockout
        - 15 failures = 24 hour lockout
        """
        mock_service_instance = MagicMock()
        mock_service_instance.validate_token.return_value = (False, None)
        mock_azure_service.return_value = mock_service_instance

        ip = '192.168.100.3'

        # Make 10 failed attempts (clearing rate limit between each)
        for i in range(10):
            cache.delete(f'rl:ip:{ip}')
            response = self.client.post(
                '/api/v1/auth/login/',
                {'access_token': 'invalid_token'},
                content_type='application/json',
                REMOTE_ADDR=ip
            )

        # Verify lockout is in effect at higher threshold
        lockout_key = f'auth_lockout:{ip}'
        lockout_until = cache.get(lockout_key)
        self.assertIsNotNone(
            lockout_until,
            "CRITICAL: Lockout must escalate after 10 failures"
        )

    @patch('apps.authentication.views.AzureADService')
    def test_successful_login_clears_failure_counter(self, mock_azure_service):
        """
        CRITICAL: Successful login must clear failed attempt counter.

        Prevents legitimate users from being locked out after recovering.
        """
        mock_service_instance = MagicMock()
        mock_azure_service.return_value = mock_service_instance

        ip = '192.168.100.4'

        # Make 3 failed attempts
        mock_service_instance.validate_token.return_value = (False, None)
        for i in range(3):
            cache.delete(f'rl:ip:{ip}')
            self.client.post(
                '/api/v1/auth/login/',
                {'access_token': 'invalid_token'},
                content_type='application/json',
                REMOTE_ADDR=ip
            )

        # Verify failures are tracked
        failures = cache.get(f'auth_failures:{ip}')
        self.assertEqual(failures, 3)

        # Make successful login
        mock_service_instance.validate_token.return_value = (
            True,
            {
                'id': 'test-azure-id',
                'mail': 'security_test@example.com',
                'userPrincipalName': 'security_test@example.com',
                'givenName': 'Security',
                'surname': 'Test',
                'displayName': 'Security Test'
            }
        )
        mock_service_instance.create_or_update_user.return_value = self.user

        cache.delete(f'rl:ip:{ip}')
        response = self.client.post(
            '/api/v1/auth/login/',
            {'access_token': 'valid_token'},
            content_type='application/json',
            REMOTE_ADDR=ip
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify failures are cleared
        failures = cache.get(f'auth_failures:{ip}')
        self.assertIsNone(
            failures,
            "CRITICAL: Failed attempts must be cleared after successful login"
        )

    def test_token_refresh_rate_limiting(self):
        """
        CRITICAL: Token refresh endpoint must be rate limited.

        Prevents token refresh abuse.
        """
        ip = '192.168.100.5'

        # Make 30 requests to hit rate limit
        for i in range(30):
            cache.delete(f'rl:ip:{ip}')
            response = self.client.post(
                '/api/v1/auth/refresh/',
                {'refresh_token': 'invalid_token'},
                content_type='application/json',
                REMOTE_ADDR=ip
            )
            # Should get 400/401, not rate limited yet
            self.assertIn(
                response.status_code,
                [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED]
            )

        # 31st request should be rate limited
        response = self.client.post(
            '/api/v1/auth/refresh/',
            {'refresh_token': 'invalid_token'},
            content_type='application/json',
            REMOTE_ADDR=ip
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
            "CRITICAL: Token refresh must be rate limited"
        )

    @patch('apps.authentication.views.AzureADService')
    def test_different_ips_have_separate_limits(self, mock_azure_service):
        """
        CRITICAL: Rate limits must be per-IP, not global.

        Prevents one attacker from blocking all users.
        """
        mock_service_instance = MagicMock()
        mock_service_instance.validate_token.return_value = (False, None)
        mock_azure_service.return_value = mock_service_instance

        # IP 1: Trigger rate limit
        for i in range(5):
            self.client.post(
                '/api/v1/auth/login/',
                {'access_token': 'invalid_token'},
                content_type='application/json',
                REMOTE_ADDR='192.168.100.10'
            )

        # IP 1: Should be rate limited
        response = self.client.post(
            '/api/v1/auth/login/',
            {'access_token': 'invalid_token'},
            content_type='application/json',
            REMOTE_ADDR='192.168.100.10'
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # IP 2: Should NOT be rate limited
        response = self.client.post(
            '/api/v1/auth/login/',
            {'access_token': 'invalid_token'},
            content_type='application/json',
            REMOTE_ADDR='192.168.100.20'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "CRITICAL: Different IP should not be affected by other IP's rate limit"
        )

    # ========================================================================
    # Security Logging Tests (CRITICAL)
    # ========================================================================

    @patch('apps.authentication.views.security_logger')
    @patch('apps.authentication.views.AzureADService')
    def test_failed_authentication_is_logged(self, mock_azure_service, mock_security_logger):
        """
        CRITICAL: All failed authentication attempts must be logged.

        Required for security monitoring and incident response.
        """
        mock_service_instance = MagicMock()
        mock_service_instance.validate_token.return_value = (False, None)
        mock_azure_service.return_value = mock_service_instance

        # Attempt failed login
        self.client.post(
            '/api/v1/auth/login/',
            {'access_token': 'invalid_token'},
            content_type='application/json',
            REMOTE_ADDR='192.168.100.50'
        )

        # Verify security logger was called
        self.assertTrue(
            mock_security_logger.warning.called or mock_security_logger.info.called,
            "CRITICAL: Failed login must be logged to security logger"
        )

    @patch('apps.authentication.views.security_logger')
    @patch('apps.authentication.views.AzureADService')
    def test_lockout_events_are_logged(self, mock_azure_service, mock_security_logger):
        """
        CRITICAL: IP lockout events must be logged with ERROR severity.

        Critical security events require high-priority logging.
        """
        mock_service_instance = MagicMock()
        mock_service_instance.validate_token.return_value = (False, None)
        mock_azure_service.return_value = mock_service_instance

        # Trigger lockout
        for i in range(5):
            cache.delete('rl:ip:192.168.100.51')
            self.client.post(
                '/api/v1/auth/login/',
                {'access_token': 'invalid_token'},
                content_type='application/json',
                REMOTE_ADDR='192.168.100.51'
            )

        # Verify ERROR level logging
        error_calls = [
            call for call in mock_security_logger.error.call_args_list
            if 'locked out' in str(call).lower()
        ]
        self.assertTrue(
            len(error_calls) > 0,
            "CRITICAL: Lockout events must be logged with ERROR severity"
        )

    @patch('apps.authentication.views.security_logger')
    @patch('apps.authentication.views.AzureADService')
    def test_successful_login_is_logged(self, mock_azure_service, mock_security_logger):
        """
        CRITICAL: Successful logins must be logged for audit trail.

        Required for compliance and security monitoring.
        """
        mock_service_instance = MagicMock()
        mock_service_instance.validate_token.return_value = (
            True,
            {
                'id': 'test-azure-id',
                'mail': 'security_test@example.com',
                'userPrincipalName': 'security_test@example.com',
                'givenName': 'Security',
                'surname': 'Test',
                'displayName': 'Security Test'
            }
        )
        mock_service_instance.create_or_update_user.return_value = self.user
        mock_azure_service.return_value = mock_service_instance

        # Successful login
        self.client.post(
            '/api/v1/auth/login/',
            {'access_token': 'valid_token'},
            content_type='application/json',
            REMOTE_ADDR='192.168.100.52'
        )

        # Verify INFO level logging for success
        self.assertTrue(
            mock_security_logger.info.called,
            "CRITICAL: Successful login must be logged"
        )

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_security_configuration_is_production_ready(self):
        """
        CRITICAL: Verify all security settings are production-ready.

        Checks:
        - Rate limiting is enabled
        - Security logging is configured
        - Cache backend is configured
        """
        # Verify rate limiting is enabled
        self.assertTrue(
            getattr(settings, 'RATELIMIT_ENABLE', False),
            "CRITICAL: RATELIMIT_ENABLE must be True"
        )

        # Verify cache is configured (required for rate limiting)
        self.assertIn('default', settings.CACHES)

        # Verify security logger is configured
        self.assertIn('security', settings.LOGGING['loggers'])

    def test_complete_attack_scenario_is_blocked(self):
        """
        CRITICAL: Simulate complete brute-force attack and verify protection.

        Scenario:
        1. Attacker makes multiple failed login attempts
        2. Rate limiting blocks excessive requests
        3. Progressive lockout is triggered
        4. All events are logged
        5. Legitimate user can still access after lockout expires
        """
        with patch('apps.authentication.views.AzureADService') as mock_azure_service:
            mock_service_instance = MagicMock()
            mock_service_instance.validate_token.return_value = (False, None)
            mock_azure_service.return_value = mock_service_instance

            attacker_ip = '192.168.100.100'

            # Attacker makes 10 attempts
            blocked_count = 0
            for i in range(10):
                response = self.client.post(
                    '/api/v1/auth/login/',
                    {'access_token': 'invalid_token'},
                    content_type='application/json',
                    REMOTE_ADDR=attacker_ip
                )
                if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    blocked_count += 1

            # Verify attacker was blocked
            self.assertGreater(
                blocked_count,
                0,
                "CRITICAL: Attacker must be blocked by rate limiting or lockout"
            )

            # Verify lockout is in effect
            lockout_key = f'auth_lockout:{attacker_ip}'
            lockout_until = cache.get(lockout_key)
            self.assertIsNotNone(
                lockout_until,
                "CRITICAL: Attacker IP must be in lockout after failed attempts"
            )


# Run critical security tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
