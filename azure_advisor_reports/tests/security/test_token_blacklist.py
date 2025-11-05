"""
Comprehensive tests for JWT Token Blacklisting implementation.

This test suite validates:
- Token generation with JTI
- Token validation with blacklist checking
- Token revocation (logout)
- Cleanup of expired tokens
- Performance of blacklist queries
- Security edge cases

Tests cover OWASP recommendations for session management and token handling.
"""

import uuid
import jwt
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.core.management import call_command
from io import StringIO
from unittest.mock import patch

from apps.authentication.models import TokenBlacklist
from apps.authentication.services import JWTService

User = get_user_model()


class TokenBlacklistModelTestCase(TestCase):
    """Test the TokenBlacklist model functionality."""

    def setUp(self):
        """Set up test user for each test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )

    def test_create_token_blacklist_entry(self):
        """Test creating a token blacklist entry."""
        jti = str(uuid.uuid4())
        expires_at = timezone.now() + timedelta(minutes=15)

        token = TokenBlacklist.objects.create(
            jti=jti,
            token_type='access',
            user=self.user,
            expires_at=expires_at
        )

        self.assertEqual(token.jti, jti)
        self.assertEqual(token.token_type, 'access')
        self.assertEqual(token.user, self.user)
        self.assertFalse(token.is_revoked)
        self.assertIsNone(token.revoked_at)
        self.assertEqual(token.revoked_reason, '')

    def test_token_blacklist_str_representation(self):
        """Test string representation of TokenBlacklist."""
        jti = str(uuid.uuid4())
        token = TokenBlacklist.objects.create(
            jti=jti,
            token_type='access',
            user=self.user,
            expires_at=timezone.now() + timedelta(minutes=15)
        )

        expected = f"Access Token for {self.user.email} - Active"
        self.assertEqual(str(token), expected)

    def test_revoke_token_instance_method(self):
        """Test revoking a token using instance method."""
        jti = str(uuid.uuid4())
        token = TokenBlacklist.objects.create(
            jti=jti,
            token_type='access',
            user=self.user,
            expires_at=timezone.now() + timedelta(minutes=15)
        )

        self.assertFalse(token.is_revoked)

        token.revoke(reason='test_revocation')

        self.assertTrue(token.is_revoked)
        self.assertIsNotNone(token.revoked_at)
        self.assertEqual(token.revoked_reason, 'test_revocation')

    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens."""
        # Create expired token
        expired_jti = str(uuid.uuid4())
        TokenBlacklist.objects.create(
            jti=expired_jti,
            token_type='access',
            user=self.user,
            expires_at=timezone.now() - timedelta(hours=1)
        )

        # Create active token
        active_jti = str(uuid.uuid4())
        TokenBlacklist.objects.create(
            jti=active_jti,
            token_type='access',
            user=self.user,
            expires_at=timezone.now() + timedelta(minutes=15)
        )

        self.assertEqual(TokenBlacklist.objects.count(), 2)

        # Clean up expired tokens
        deleted_count = TokenBlacklist.cleanup_expired()

        self.assertEqual(deleted_count, 1)
        self.assertEqual(TokenBlacklist.objects.count(), 1)
        self.assertTrue(TokenBlacklist.objects.filter(jti=active_jti).exists())
        self.assertFalse(TokenBlacklist.objects.filter(jti=expired_jti).exists())

    def test_revoke_user_tokens(self):
        """Test revoking all tokens for a user."""
        # Create multiple tokens for user
        for i in range(3):
            TokenBlacklist.objects.create(
                jti=str(uuid.uuid4()),
                token_type='access',
                user=self.user,
                expires_at=timezone.now() + timedelta(minutes=15)
            )

        self.assertEqual(
            TokenBlacklist.objects.filter(user=self.user, is_revoked=False).count(),
            3
        )

        # Revoke all user tokens
        count = TokenBlacklist.revoke_user_tokens(self.user, reason='security_test')

        self.assertEqual(count, 3)
        self.assertEqual(
            TokenBlacklist.objects.filter(user=self.user, is_revoked=True).count(),
            3
        )

    def test_token_blacklist_unique_jti(self):
        """Test that JTI is unique in database."""
        jti = str(uuid.uuid4())

        TokenBlacklist.objects.create(
            jti=jti,
            token_type='access',
            user=self.user,
            expires_at=timezone.now() + timedelta(minutes=15)
        )

        # Try to create another token with same JTI
        with self.assertRaises(Exception):  # Should raise IntegrityError
            TokenBlacklist.objects.create(
                jti=jti,
                token_type='refresh',
                user=self.user,
                expires_at=timezone.now() + timedelta(days=1)
            )


class JWTServiceTokenGenerationTestCase(TestCase):
    """Test JWT token generation with JTI and reduced lifetimes."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )

    def test_generate_token_creates_jti(self):
        """Test that generated tokens include JTI."""
        tokens = JWTService.generate_token(self.user)

        self.assertIn('access_token', tokens)
        self.assertIn('refresh_token', tokens)

        # Decode and verify JTI
        access_payload = jwt.decode(
            tokens['access_token'],
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        refresh_payload = jwt.decode(
            tokens['refresh_token'],
            settings.SECRET_KEY,
            algorithms=['HS256']
        )

        self.assertIn('jti', access_payload)
        self.assertIn('jti', refresh_payload)
        self.assertIsNotNone(access_payload['jti'])
        self.assertIsNotNone(refresh_payload['jti'])
        self.assertNotEqual(access_payload['jti'], refresh_payload['jti'])

    def test_generate_token_stores_in_database(self):
        """Test that generated tokens are stored in database."""
        initial_count = TokenBlacklist.objects.count()

        tokens = JWTService.generate_token(self.user)

        # Decode to get JTIs
        access_payload = jwt.decode(
            tokens['access_token'],
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        refresh_payload = jwt.decode(
            tokens['refresh_token'],
            settings.SECRET_KEY,
            algorithms=['HS256']
        )

        # Check database entries were created
        self.assertEqual(TokenBlacklist.objects.count(), initial_count + 2)

        access_token_record = TokenBlacklist.objects.get(jti=access_payload['jti'])
        self.assertEqual(access_token_record.token_type, 'access')
        self.assertEqual(access_token_record.user, self.user)
        self.assertFalse(access_token_record.is_revoked)

        refresh_token_record = TokenBlacklist.objects.get(jti=refresh_payload['jti'])
        self.assertEqual(refresh_token_record.token_type, 'refresh')
        self.assertEqual(refresh_token_record.user, self.user)
        self.assertFalse(refresh_token_record.is_revoked)

    def test_token_lifetime_is_reduced(self):
        """Test that token lifetimes are reduced (access: 15min, refresh: 1 day)."""
        tokens = JWTService.generate_token(self.user)

        # Check expires_in matches reduced lifetime
        self.assertEqual(tokens['expires_in'], 900)  # 15 minutes = 900 seconds

        # Decode and check expiration times
        access_payload = jwt.decode(
            tokens['access_token'],
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        refresh_payload = jwt.decode(
            tokens['refresh_token'],
            settings.SECRET_KEY,
            algorithms=['HS256']
        )

        access_exp = datetime.utcfromtimestamp(access_payload['exp'])
        access_iat = datetime.utcfromtimestamp(access_payload['iat'])
        access_lifetime = (access_exp - access_iat).total_seconds()

        refresh_exp = datetime.utcfromtimestamp(refresh_payload['exp'])
        refresh_iat = datetime.utcfromtimestamp(refresh_payload['iat'])
        refresh_lifetime = (refresh_exp - refresh_iat).total_seconds()

        # Allow 1 second tolerance
        self.assertAlmostEqual(access_lifetime, 900, delta=1)  # 15 minutes
        self.assertAlmostEqual(refresh_lifetime, 86400, delta=1)  # 1 day


class JWTServiceTokenValidationTestCase(TestCase):
    """Test JWT token validation with blacklist checking."""

    def setUp(self):
        """Set up test user and generate tokens."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        self.tokens = JWTService.generate_token(self.user)

    def test_validate_active_token(self):
        """Test validating an active (non-revoked) token."""
        is_valid, payload = JWTService.validate_token(
            self.tokens['access_token'],
            token_type='access'
        )

        self.assertTrue(is_valid)
        self.assertIsNotNone(payload)
        self.assertEqual(payload['email'], self.user.email)
        self.assertIn('jti', payload)

    def test_validate_revoked_token(self):
        """Test that revoked tokens are rejected."""
        # Decode to get JTI
        access_payload = jwt.decode(
            self.tokens['access_token'],
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        jti = access_payload['jti']

        # Revoke the token
        JWTService.revoke_token(jti, reason='test')

        # Try to validate revoked token
        is_valid, payload = JWTService.validate_token(
            self.tokens['access_token'],
            token_type='access'
        )

        self.assertFalse(is_valid)
        self.assertIsNone(payload)

    def test_validate_token_without_jti(self):
        """Test that tokens without JTI are rejected."""
        # Create token without JTI
        old_payload = {
            'user_id': str(self.user.id),
            'email': self.user.email,
            'role': self.user.role,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'type': 'access'
            # Note: no 'jti' field
        }

        old_token = jwt.encode(old_payload, settings.SECRET_KEY, algorithm='HS256')

        # Validation should fail
        is_valid, payload = JWTService.validate_token(old_token, token_type='access')

        self.assertFalse(is_valid)
        self.assertIsNone(payload)

    def test_validate_token_not_in_database(self):
        """Test that tokens not in database are rejected (forgery protection)."""
        # Create a valid JWT but don't store in database
        forged_payload = {
            'user_id': str(self.user.id),
            'email': self.user.email,
            'role': self.user.role,
            'jti': str(uuid.uuid4()),  # Random JTI not in database
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'type': 'access'
        }

        forged_token = jwt.encode(forged_payload, settings.SECRET_KEY, algorithm='HS256')

        # Validation should fail
        is_valid, payload = JWTService.validate_token(forged_token, token_type='access')

        self.assertFalse(is_valid)
        self.assertIsNone(payload)

    def test_validate_expired_token(self):
        """Test that expired tokens are rejected."""
        # Create expired token
        expired_jti = str(uuid.uuid4())
        expired_payload = {
            'user_id': str(self.user.id),
            'email': self.user.email,
            'role': self.user.role,
            'jti': expired_jti,
            'exp': datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            'iat': datetime.utcnow() - timedelta(hours=2),
            'type': 'access'
        }

        # Store in database
        TokenBlacklist.objects.create(
            jti=expired_jti,
            token_type='access',
            user=self.user,
            expires_at=timezone.now() - timedelta(hours=1)
        )

        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm='HS256')

        # Validation should fail
        is_valid, payload = JWTService.validate_token(expired_token, token_type='access')

        self.assertFalse(is_valid)
        self.assertIsNone(payload)

    def test_validate_wrong_token_type(self):
        """Test that token type mismatch is rejected."""
        # Try to validate access token as refresh token
        is_valid, payload = JWTService.validate_token(
            self.tokens['access_token'],
            token_type='refresh'
        )

        self.assertFalse(is_valid)
        self.assertIsNone(payload)


class JWTServiceTokenRevocationTestCase(TestCase):
    """Test token revocation functionality."""

    def setUp(self):
        """Set up test user and generate tokens."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        self.tokens = JWTService.generate_token(self.user)

    def test_revoke_single_token(self):
        """Test revoking a single token by JTI."""
        # Decode to get JTI
        access_payload = jwt.decode(
            self.tokens['access_token'],
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        jti = access_payload['jti']

        # Verify token is active
        token_record = TokenBlacklist.objects.get(jti=jti)
        self.assertFalse(token_record.is_revoked)

        # Revoke token
        success = JWTService.revoke_token(jti, reason='test_revocation')

        self.assertTrue(success)

        # Verify token is revoked
        token_record.refresh_from_db()
        self.assertTrue(token_record.is_revoked)
        self.assertEqual(token_record.revoked_reason, 'test_revocation')
        self.assertIsNotNone(token_record.revoked_at)

    def test_revoke_all_user_tokens(self):
        """Test revoking all tokens for a user."""
        # Generate additional tokens
        additional_tokens = JWTService.generate_token(self.user)

        # Verify user has active tokens
        active_count = TokenBlacklist.objects.filter(
            user=self.user,
            is_revoked=False
        ).count()
        self.assertGreater(active_count, 0)

        # Revoke all user tokens
        revoked_count = JWTService.revoke_all_user_tokens(self.user, reason='security_incident')

        self.assertEqual(revoked_count, active_count)

        # Verify all tokens are revoked
        remaining_active = TokenBlacklist.objects.filter(
            user=self.user,
            is_revoked=False
        ).count()
        self.assertEqual(remaining_active, 0)

    def test_revoke_nonexistent_token(self):
        """Test revoking a token that doesn't exist."""
        fake_jti = str(uuid.uuid4())

        success = JWTService.revoke_token(fake_jti, reason='test')

        self.assertFalse(success)


class LogoutViewTestCase(TestCase):
    """Test logout functionality with token revocation."""

    def setUp(self):
        """Set up test user and authenticate."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        self.tokens = JWTService.generate_token(self.user)

    def test_logout_revokes_access_token(self):
        """Test that logout revokes the access token."""
        from rest_framework.test import APIClient

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access_token"]}')

        # Decode to get JTI before logout
        access_payload = jwt.decode(
            self.tokens['access_token'],
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        access_jti = access_payload['jti']

        # Perform logout
        response = client.post('/api/v1/auth/logout/')

        # Check response
        self.assertEqual(response.status_code, 200)

        # Verify token is revoked
        token_record = TokenBlacklist.objects.get(jti=access_jti)
        self.assertTrue(token_record.is_revoked)
        self.assertEqual(token_record.revoked_reason, 'logout')

    def test_logout_revokes_both_tokens(self):
        """Test that logout revokes both access and refresh tokens."""
        from rest_framework.test import APIClient

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access_token"]}')

        # Decode to get JTIs
        access_payload = jwt.decode(
            self.tokens['access_token'],
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        refresh_payload = jwt.decode(
            self.tokens['refresh_token'],
            settings.SECRET_KEY,
            algorithms=['HS256']
        )

        # Perform logout with refresh token
        response = client.post(
            '/api/v1/auth/logout/',
            {'refresh_token': self.tokens['refresh_token']}
        )

        self.assertEqual(response.status_code, 200)

        # Verify both tokens are revoked
        access_token_record = TokenBlacklist.objects.get(jti=access_payload['jti'])
        refresh_token_record = TokenBlacklist.objects.get(jti=refresh_payload['jti'])

        self.assertTrue(access_token_record.is_revoked)
        self.assertTrue(refresh_token_record.is_revoked)


class CleanupCommandTestCase(TransactionTestCase):
    """Test the cleanup_expired_tokens management command."""

    def setUp(self):
        """Set up test user and tokens."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )

    def test_cleanup_command_removes_expired_tokens(self):
        """Test that cleanup command removes expired tokens."""
        # Create expired tokens
        for i in range(3):
            TokenBlacklist.objects.create(
                jti=str(uuid.uuid4()),
                token_type='access',
                user=self.user,
                expires_at=timezone.now() - timedelta(hours=1)
            )

        # Create active tokens
        for i in range(2):
            TokenBlacklist.objects.create(
                jti=str(uuid.uuid4()),
                token_type='access',
                user=self.user,
                expires_at=timezone.now() + timedelta(minutes=15)
            )

        self.assertEqual(TokenBlacklist.objects.count(), 5)

        # Run cleanup command
        out = StringIO()
        call_command('cleanup_expired_tokens', stdout=out)

        # Verify expired tokens were removed
        self.assertEqual(TokenBlacklist.objects.count(), 2)

        output = out.getvalue()
        self.assertIn('3 expired tokens', output)
        self.assertIn('Successfully deleted', output)

    def test_cleanup_command_dry_run(self):
        """Test cleanup command with --dry-run flag."""
        # Create expired token
        TokenBlacklist.objects.create(
            jti=str(uuid.uuid4()),
            token_type='access',
            user=self.user,
            expires_at=timezone.now() - timedelta(hours=1)
        )

        initial_count = TokenBlacklist.objects.count()

        # Run cleanup with dry-run
        out = StringIO()
        call_command('cleanup_expired_tokens', '--dry-run', stdout=out)

        # Verify no tokens were deleted
        self.assertEqual(TokenBlacklist.objects.count(), initial_count)

        output = out.getvalue()
        self.assertIn('DRY RUN', output)
        self.assertIn('Would delete', output)


class TokenBlacklistPerformanceTestCase(TestCase):
    """Test performance of blacklist queries with indexes."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )

    def test_blacklist_check_performance_with_many_tokens(self):
        """Test that blacklist checks remain fast with many tokens."""
        # Create many tokens (simulating production scenario)
        for i in range(100):
            TokenBlacklist.objects.create(
                jti=str(uuid.uuid4()),
                token_type='access' if i % 2 == 0 else 'refresh',
                user=self.user,
                expires_at=timezone.now() + timedelta(minutes=15)
            )

        # Generate a new token
        tokens = JWTService.generate_token(self.user)

        # Time the validation (should be fast due to indexes)
        import time
        start = time.time()

        is_valid, payload = JWTService.validate_token(
            tokens['access_token'],
            token_type='access'
        )

        elapsed = time.time() - start

        self.assertTrue(is_valid)
        self.assertLess(elapsed, 0.1)  # Should complete in < 100ms
