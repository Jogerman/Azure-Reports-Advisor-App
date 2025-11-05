"""
Security Tests for Rate Limiting and Progressive Lockout

Tests validate that:
1. Rate limiting is properly enforced on authentication endpoints
2. Progressive lockout is implemented correctly
3. Successful login clears failed attempt counters
4. Token refresh endpoint is rate limited
5. Security logging captures rate limiting events
"""

import pytest
from django.test import TestCase, Client
from django.core.cache import cache
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from rest_framework import status

User = get_user_model()


class RateLimitingTestCase(TestCase):
    """Test suite for rate limiting on authentication endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        cache.clear()

        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            role='analyst'
        )

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    @patch('apps.authentication.views.AzureADService')
    def test_rate_limiting_on_login(self, mock_azure_service):
        """Rate limiting should block after 5 failed attempts per minute."""
        # Mock Azure AD service to return invalid token
        mock_service_instance = MagicMock()
        mock_service_instance.validate_token.return_value = (False, None)
        mock_azure_service.return_value = mock_service_instance

        # Make 5 failed login attempts
        for i in range(5):
            response = self.client.post(
                '/api/v1/auth/login/',
                {'access_token': 'invalid_token'},
                content_type='application/json'
            )
            # First 5 should return 401 (unauthorized)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 6th attempt should be rate limited (429)
        response = self.client.post(
            '/api/v1/auth/login/',
            {'access_token': 'invalid_token'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch('apps.authentication.views.AzureADService')
    def test_progressive_lockout_5_failures(self, mock_azure_service):
        """After 5 failures, IP should be locked out for 15 minutes."""
        # Mock Azure AD service to return invalid token
        mock_service_instance = MagicMock()
        mock_service_instance.validate_token.return_value = (False, None)
        mock_azure_service.return_value = mock_service_instance

        # Make 5 failed login attempts
        for i in range(5):
            response = self.client.post(
                '/api/v1/auth/login/',
                {'access_token': 'invalid_token'},
                content_type='application/json',
                REMOTE_ADDR='192.168.1.100'
            )

        # Check that lockout is in effect
        lockout_key = 'auth_lockout:192.168.1.100'
        lockout_until = cache.get(lockout_key)
        self.assertIsNotNone(lockout_until, "Lockout should be set after 5 failures")

        # Verify lockout message
        response = self.client.post(
            '/api/v1/auth/login/',
            {'access_token': 'invalid_token'},
            content_type='application/json',
            REMOTE_ADDR='192.168.1.100'
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('locked', response.json().get('error', '').lower())

    @patch('apps.authentication.views.AzureADService')
    def test_progressive_lockout_10_failures(self, mock_azure_service):
        """After 10 failures, IP should be locked out for 1 hour."""
        # Mock Azure AD service to return invalid token
        mock_service_instance = MagicMock()
        mock_service_instance.validate_token.return_value = (False, None)
        mock_azure_service.return_value = mock_service_instance

        # Make 10 failed login attempts
        for i in range(10):
            # Clear rate limit but not failure counter
            cache.delete('rl:ip:192.168.1.101')
            response = self.client.post(
                '/api/v1/auth/login/',
                {'access_token': 'invalid_token'},
                content_type='application/json',
                REMOTE_ADDR='192.168.1.101'
            )

        # Check that lockout is in effect
        lockout_key = 'auth_lockout:192.168.1.101'
        lockout_until = cache.get(lockout_key)
        self.assertIsNotNone(lockout_until, "Lockout should be set after 10 failures")

    @patch('apps.authentication.views.AzureADService')
    def test_successful_login_clears_failed_attempts(self, mock_azure_service):
        """Successful login should clear the failed attempt counter."""
        # Mock Azure AD service to return valid token
        mock_service_instance = MagicMock()
        mock_service_instance.validate_token.return_value = (
            True,
            {
                'id': 'test-azure-id',
                'mail': 'test@example.com',
                'userPrincipalName': 'test@example.com',
                'givenName': 'Test',
                'surname': 'User',
                'displayName': 'Test User'
            }
        )
        mock_service_instance.create_or_update_user.return_value = self.user
        mock_azure_service.return_value = mock_service_instance

        ip = '192.168.1.102'

        # First, make some failed attempts
        mock_service_instance.validate_token.return_value = (False, None)
        for i in range(3):
            cache.delete('rl:ip:' + ip)
            self.client.post(
                '/api/v1/auth/login/',
                {'access_token': 'invalid_token'},
                content_type='application/json',
                REMOTE_ADDR=ip
            )

        # Verify failures are tracked
        failure_key = f'auth_failures:{ip}'
        failures = cache.get(failure_key)
        self.assertEqual(failures, 3, "Should have 3 failed attempts")

        # Now make a successful login
        mock_service_instance.validate_token.return_value = (
            True,
            {
                'id': 'test-azure-id',
                'mail': 'test@example.com',
                'userPrincipalName': 'test@example.com',
                'givenName': 'Test',
                'surname': 'User',
                'displayName': 'Test User'
            }
        )

        cache.delete('rl:ip:' + ip)
        response = self.client.post(
            '/api/v1/auth/login/',
            {'access_token': 'valid_token'},
            content_type='application/json',
            REMOTE_ADDR=ip
        )

        # Verify successful login
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify failures are cleared
        failures = cache.get(failure_key)
        self.assertIsNone(failures, "Failed attempts should be cleared after successful login")

    def test_rate_limiting_on_token_refresh(self):
        """Token refresh should be rate limited to 30 requests per hour."""
        # Make 30 requests (should all succeed or fail for other reasons, but not rate limit)
        for i in range(30):
            cache.delete('rl:ip:192.168.1.103')
            response = self.client.post(
                '/api/v1/auth/refresh/',
                {'refresh_token': 'invalid_token'},
                content_type='application/json',
                REMOTE_ADDR='192.168.1.103'
            )
            # Should get 401 (invalid token), not 429 (rate limited)
            self.assertIn(
                response.status_code,
                [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED],
                f"Request {i+1} should not be rate limited"
            )

        # 31st request should be rate limited
        response = self.client.post(
            '/api/v1/auth/refresh/',
            {'refresh_token': 'invalid_token'},
            content_type='application/json',
            REMOTE_ADDR='192.168.1.103'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
            "31st request should be rate limited"
        )

    @patch('apps.authentication.views.AzureADService')
    def test_different_ips_have_separate_rate_limits(self, mock_azure_service):
        """Different IP addresses should have independent rate limit counters."""
        # Mock Azure AD service to return invalid token
        mock_service_instance = MagicMock()
        mock_service_instance.validate_token.return_value = (False, None)
        mock_azure_service.return_value = mock_service_instance

        # IP 1: Make 5 failed attempts (should trigger rate limit)
        for i in range(5):
            response = self.client.post(
                '/api/v1/auth/login/',
                {'access_token': 'invalid_token'},
                content_type='application/json',
                REMOTE_ADDR='192.168.1.10'
            )

        # IP 1: Next request should be rate limited
        response = self.client.post(
            '/api/v1/auth/login/',
            {'access_token': 'invalid_token'},
            content_type='application/json',
            REMOTE_ADDR='192.168.1.10'
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # IP 2: Should still be able to make requests
        response = self.client.post(
            '/api/v1/auth/login/',
            {'access_token': 'invalid_token'},
            content_type='application/json',
            REMOTE_ADDR='192.168.1.20'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Different IP should not be rate limited"
        )


class SecurityLoggingTestCase(TestCase):
    """Test suite for security event logging."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        cache.clear()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    @patch('apps.authentication.views.security_logger')
    @patch('apps.authentication.views.AzureADService')
    def test_failed_login_is_logged(self, mock_azure_service, mock_security_logger):
        """Failed login attempts should be logged to security logger."""
        # Mock Azure AD service to return invalid token
        mock_service_instance = MagicMock()
        mock_service_instance.validate_token.return_value = (False, None)
        mock_azure_service.return_value = mock_service_instance

        # Attempt failed login
        response = self.client.post(
            '/api/v1/auth/login/',
            {'access_token': 'invalid_token'},
            content_type='application/json',
            REMOTE_ADDR='192.168.1.200'
        )

        # Verify security logger was called
        self.assertTrue(
            mock_security_logger.warning.called or mock_security_logger.info.called,
            "Security logger should be called for failed login"
        )

    @patch('apps.authentication.views.security_logger')
    @patch('apps.authentication.views.AzureADService')
    def test_lockout_is_logged(self, mock_azure_service, mock_security_logger):
        """IP lockout events should be logged with severity ERROR."""
        # Mock Azure AD service to return invalid token
        mock_service_instance = MagicMock()
        mock_service_instance.validate_token.return_value = (False, None)
        mock_azure_service.return_value = mock_service_instance

        # Make 5 failed attempts to trigger lockout
        for i in range(5):
            cache.delete('rl:ip:192.168.1.201')
            response = self.client.post(
                '/api/v1/auth/login/',
                {'access_token': 'invalid_token'},
                content_type='application/json',
                REMOTE_ADDR='192.168.1.201'
            )

        # Verify ERROR level logging for lockout
        # Check if security_logger.error was called
        error_calls = [
            call for call in mock_security_logger.error.call_args_list
            if 'locked out' in str(call).lower()
        ]
        self.assertTrue(
            len(error_calls) > 0,
            "Security logger should log lockout with ERROR level"
        )
