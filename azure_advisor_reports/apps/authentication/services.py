"""
Authentication services for Azure AD integration and token management.

This module provides services for:
- Azure AD token validation
- User creation and updates from Azure AD profiles
- JWT token generation for API access
- Role-based access control helpers
"""

import logging
import uuid
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from msal import ConfidentialClientApplication, PublicClientApplication
import requests

User = get_user_model()
logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')


class AzureADService:
    """
    Service for handling Azure AD authentication and user profile management.
    """

    def __init__(self):
        self.client_id = settings.AZURE_AD.get('CLIENT_ID')
        self.client_secret = settings.AZURE_AD.get('CLIENT_SECRET')
        self.tenant_id = settings.AZURE_AD.get('TENANT_ID')
        self.authority = settings.AZURE_AD.get('AUTHORITY')
        self.scope = settings.AZURE_AD.get('SCOPE', ['openid', 'profile', 'email'])

    def get_msal_app(self) -> ConfidentialClientApplication:
        """
        Initialize and return MSAL confidential client application.
        """
        return ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )

    def validate_token(self, access_token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate Azure AD token (both idToken and accessToken).

        This method validates the token by verifying its JWT signature using Azure AD's
        public keys, then extracts user information from the token claims.

        Args:
            access_token: The Azure AD token (idToken or accessToken) to validate

        Returns:
            Tuple of (is_valid, user_info_dict or None)
        """
        try:
            # Get Microsoft's public signing keys (JWKS)
            jwks_uri = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"

            # Check cache first
            cache_key = f"azure_ad_jwks_{self.tenant_id}"
            jwks = cache.get(cache_key)

            if not jwks:
                logger.info("Fetching Azure AD JWKS keys...")
                response = requests.get(jwks_uri, timeout=10)
                response.raise_for_status()
                jwks = response.json()
                cache.set(cache_key, jwks, 3600)  # Cache for 1 hour

            # Get the key ID from token header
            unverified_header = jwt.get_unverified_header(access_token)
            kid = unverified_header.get('kid')

            if not kid:
                logger.error("Token missing 'kid' (key ID) in header")
                return False, None

            # Find the matching public key from JWKS
            rsa_key = None
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    rsa_key = key
                    break

            if not rsa_key:
                logger.error(f"Unable to find matching public key for kid: {kid}")
                return False, None

            # Convert JWK to PEM format for PyJWT
            from jwt.algorithms import RSAAlgorithm
            import json

            public_key = RSAAlgorithm.from_jwk(json.dumps(rsa_key))

            # Decode and validate the token with full signature verification
            # Note: audience validation for idToken uses the client_id
            decoded_token = jwt.decode(
                access_token,
                key=public_key,
                algorithms=['RS256'],
                audience=self.client_id,  # idToken audience is the client_id
                issuer=f"https://login.microsoftonline.com/{self.tenant_id}/v2.0",
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_aud': True,
                    'verify_iss': True,
                }
            )

            # Extract user information from token claims
            # Both idToken and accessToken contain these claims
            user_info = {
                'id': decoded_token.get('oid') or decoded_token.get('sub'),  # Azure AD Object ID
                'mail': decoded_token.get('email') or decoded_token.get('preferred_username') or decoded_token.get('upn'),
                'userPrincipalName': decoded_token.get('preferred_username') or decoded_token.get('upn'),
                'givenName': decoded_token.get('given_name', ''),
                'surname': decoded_token.get('family_name', ''),
                'displayName': decoded_token.get('name', ''),
            }

            # Ensure we have at least an email/UPN for user identification
            if not user_info.get('mail'):
                logger.error("Token missing email/UPN claim")
                return False, None

            logger.info(f"Successfully validated token for user: {user_info.get('mail')}")
            return True, user_info

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return False, None
        except jwt.InvalidAudienceError as e:
            logger.warning(f"Token audience validation failed: {str(e)}")
            return False, None
        except jwt.InvalidIssuerError as e:
            logger.warning(f"Token issuer validation failed: {str(e)}")
            return False, None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            return False, None
        except requests.RequestException as e:
            logger.error(f"Request error fetching JWKS: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}")
            logger.exception(e)  # Log full stack trace for debugging
            return False, None

    def create_or_update_user(self, azure_user_info: Dict) -> Optional[User]:
        """
        Create or update user from Azure AD profile information.

        Args:
            azure_user_info: Dictionary containing Azure AD user profile

        Returns:
            User instance or None if creation/update fails
        """
        try:
            azure_object_id = azure_user_info.get('id')
            email = azure_user_info.get('mail') or azure_user_info.get('userPrincipalName')

            if not azure_object_id or not email:
                logger.error("Missing required user information from Azure AD")
                return None

            # Try to find existing user by Azure AD object ID
            user, created = User.objects.get_or_create(
                azure_object_id=azure_object_id,
                defaults={
                    'email': email,
                    'username': email.split('@')[0],  # Use email prefix as username
                    'first_name': azure_user_info.get('givenName', ''),
                    'last_name': azure_user_info.get('surname', ''),
                    'is_active': True,
                }
            )

            # Update user information if it already exists
            if not created:
                user.email = email
                user.first_name = azure_user_info.get('givenName', user.first_name)
                user.last_name = azure_user_info.get('surname', user.last_name)
                user.job_title = azure_user_info.get('jobTitle', user.job_title)
                user.department = azure_user_info.get('department', user.department)
                user.phone_number = azure_user_info.get('mobilePhone', user.phone_number)
                user.last_login = timezone.now()
                user.save()

                logger.info(f"Updated existing user: {user.email}")
            else:
                # Set default role for new users
                user.role = 'analyst'  # Default role
                user.save()
                logger.info(f"Created new user: {user.email}")

            return user

        except Exception as e:
            logger.error(f"Error creating/updating user: {str(e)}")
            return None

    def get_user_profile(self, access_token: str) -> Optional[Dict]:
        """
        Fetch user profile from Microsoft Graph API.

        Args:
            access_token: Valid Azure AD access token

        Returns:
            Dictionary with user profile information or None
        """
        try:
            graph_url = "https://graph.microsoft.com/v1.0/me"
            headers = {'Authorization': f'Bearer {access_token}'}

            response = requests.get(graph_url, headers=headers, timeout=10)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            logger.error(f"Error fetching user profile: {str(e)}")
            return None


class JWTService:
    """
    Service for generating and validating JWT tokens for API access with blacklisting support.

    Security Features:
    - Reduced token lifetimes (access: 15 minutes, refresh: 1 day)
    - JWT ID (JTI) for token tracking and revocation
    - Token blacklist checking during validation
    - Automatic token storage in database for audit trail
    """

    # Reduced token lifetimes for enhanced security
    ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)  # Was 1 hour, now 15 minutes
    REFRESH_TOKEN_LIFETIME = timedelta(days=1)     # Was 7 days, now 1 day

    @staticmethod
    def generate_token(user: User) -> Dict[str, str]:
        """
        Generate JWT access and refresh tokens with JTI for blacklisting.

        Each token is assigned a unique JTI (JWT ID) and stored in the database
        for tracking and revocation capabilities. Tokens have reduced lifetimes
        for enhanced security.

        Args:
            user: User instance

        Returns:
            Dictionary with 'access_token', 'refresh_token', 'expires_in', 'token_type'
        """
        try:
            # Generate unique token IDs
            access_jti = str(uuid.uuid4())
            refresh_jti = str(uuid.uuid4())

            now = datetime.utcnow()
            access_exp = now + JWTService.ACCESS_TOKEN_LIFETIME
            refresh_exp = now + JWTService.REFRESH_TOKEN_LIFETIME

            # Access token payload
            access_payload = {
                'user_id': str(user.id),
                'email': user.email,
                'role': user.role,
                'jti': access_jti,
                'exp': access_exp,
                'iat': now,
                'type': 'access'
            }

            # Refresh token payload
            refresh_payload = {
                'user_id': str(user.id),
                'jti': refresh_jti,
                'exp': refresh_exp,
                'iat': now,
                'type': 'refresh'
            }

            # Store tokens in database for tracking/revocation
            from .models import TokenBlacklist

            TokenBlacklist.objects.create(
                jti=access_jti,
                token_type='access',
                user=user,
                expires_at=access_exp
            )

            TokenBlacklist.objects.create(
                jti=refresh_jti,
                token_type='refresh',
                user=user,
                expires_at=refresh_exp
            )

            # Encode tokens
            access_token = jwt.encode(
                access_payload,
                settings.SECRET_KEY,
                algorithm='HS256'
            )

            refresh_token = jwt.encode(
                refresh_payload,
                settings.SECRET_KEY,
                algorithm='HS256'
            )

            logger.info(f"Generated JWT tokens for user: {user.email} (access expires in {JWTService.ACCESS_TOKEN_LIFETIME})")

            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': int(JWTService.ACCESS_TOKEN_LIFETIME.total_seconds()),
                'token_type': 'Bearer'
            }

        except Exception as e:
            logger.error(f"Error generating JWT token: {str(e)}")
            raise

    @staticmethod
    def validate_token(token: str, token_type: str = 'access') -> Tuple[bool, Optional[Dict]]:
        """
        Validate JWT token with blacklist checking.

        This method performs comprehensive token validation:
        1. Decodes the JWT and validates signature
        2. Checks token type matches expected type
        3. Verifies token has not been revoked (blacklist check)
        4. Ensures token exists in database (prevents forged tokens with valid JTI)

        Args:
            token: JWT token string
            token_type: Type of token ('access' or 'refresh')

        Returns:
            Tuple of (is_valid, payload_dict or None)
        """
        try:
            # Decode and validate JWT signature
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )

            # Verify token type
            if payload.get('type') != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
                return False, None

            # Check if token is blacklisted
            jti = payload.get('jti')
            if jti:
                from .models import TokenBlacklist

                try:
                    token_record = TokenBlacklist.objects.get(jti=jti)

                    # Check if token has been revoked
                    if token_record.is_revoked:
                        security_logger.warning(
                            f"Rejected revoked token {jti[:8]}... for user {payload.get('email')} "
                            f"(reason: {token_record.revoked_reason})"
                        )
                        return False, None

                    logger.debug(f"Token {jti[:8]}... validated successfully")

                except TokenBlacklist.DoesNotExist:
                    # Token not found in database - could be forged or database issue
                    security_logger.error(
                        f"Token {jti[:8]}... not found in database - potential forgery attempt"
                    )
                    return False, None
            else:
                # No JTI in token - old format or invalid
                logger.warning("Token missing JTI claim - rejecting for security")
                return False, None

            return True, payload

        except jwt.ExpiredSignatureError:
            logger.debug("JWT token has expired")
            return False, None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Error validating JWT token: {str(e)}")
            return False, None

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Generate new access token using refresh token.

        Creates a new access token with a new JTI and stores it in the database.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dictionary with new 'access_token' or None
        """
        is_valid, payload = JWTService.validate_token(refresh_token, token_type='refresh')

        if not is_valid or not payload:
            return None

        try:
            user = User.objects.get(id=payload['user_id'])

            # Generate new access token with new JTI
            access_jti = str(uuid.uuid4())
            now = datetime.utcnow()
            access_exp = now + JWTService.ACCESS_TOKEN_LIFETIME

            access_payload = {
                'user_id': str(user.id),
                'email': user.email,
                'role': user.role,
                'jti': access_jti,
                'exp': access_exp,
                'iat': now,
                'type': 'access'
            }

            # Store new access token in database
            from .models import TokenBlacklist

            TokenBlacklist.objects.create(
                jti=access_jti,
                token_type='access',
                user=user,
                expires_at=access_exp
            )

            access_token = jwt.encode(
                access_payload,
                settings.SECRET_KEY,
                algorithm='HS256'
            )

            logger.info(f"Refreshed access token for user: {user.email}")

            return {
                'access_token': access_token,
                'expires_in': int(JWTService.ACCESS_TOKEN_LIFETIME.total_seconds()),
                'token_type': 'Bearer'
            }

        except User.DoesNotExist:
            logger.error(f"User not found for refresh token: {payload.get('user_id')}")
            return None
        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            return None

    @staticmethod
    def revoke_token(jti: str, reason: str = 'logout') -> bool:
        """
        Revoke a specific token by its JTI.

        Args:
            jti: JWT ID to revoke
            reason: Reason for revocation (default: 'logout')

        Returns:
            bool: True if token was revoked, False if not found
        """
        from .models import TokenBlacklist

        try:
            token = TokenBlacklist.objects.get(jti=jti)

            if not token.is_revoked:
                token.revoke(reason=reason)
                security_logger.info(
                    f"Token {jti[:8]}... revoked for user {token.user.email} (reason: {reason})"
                )
                return True
            else:
                logger.debug(f"Token {jti[:8]}... already revoked")
                return True

        except TokenBlacklist.DoesNotExist:
            logger.warning(f"Attempted to revoke non-existent token {jti[:8]}...")
            return False
        except Exception as e:
            logger.error(f"Error revoking token {jti[:8]}...: {str(e)}")
            return False

    @staticmethod
    def revoke_all_user_tokens(user, reason: str = 'security') -> int:
        """
        Revoke all active tokens for a specific user.

        This is useful for:
        - Password changes
        - Account compromise
        - Administrative actions
        - Security incidents

        Args:
            user: User instance
            reason: Reason for revocation (default: 'security')

        Returns:
            int: Number of tokens revoked
        """
        from .models import TokenBlacklist

        try:
            count = TokenBlacklist.revoke_user_tokens(user, reason=reason)
            security_logger.warning(
                f"Revoked {count} tokens for user {user.email} (reason: {reason})"
            )
            return count

        except Exception as e:
            logger.error(f"Error revoking all tokens for user {user.email}: {str(e)}")
            return 0


class RoleService:
    """
    Service for role-based access control (RBAC) helpers.
    """

    # Define role hierarchy (higher number = more permissions)
    ROLE_HIERARCHY = {
        'viewer': 1,
        'analyst': 2,
        'manager': 3,
        'admin': 4
    }

    @classmethod
    def has_permission(cls, user: User, required_role: str) -> bool:
        """
        Check if user has required role or higher.

        Args:
            user: User instance
            required_role: Minimum required role

        Returns:
            Boolean indicating if user has sufficient permissions
        """
        if user.is_superuser:
            return True

        user_level = cls.ROLE_HIERARCHY.get(user.role, 0)
        required_level = cls.ROLE_HIERARCHY.get(required_role, 0)

        return user_level >= required_level

    @classmethod
    def can_manage_users(cls, user: User) -> bool:
        """Check if user can manage other users (admin only)."""
        return user.is_superuser or user.role == 'admin'

    @classmethod
    def can_create_clients(cls, user: User) -> bool:
        """Check if user can create clients (manager and above)."""
        return cls.has_permission(user, 'manager')

    @classmethod
    def can_generate_reports(cls, user: User) -> bool:
        """Check if user can generate reports (analyst and above)."""
        return cls.has_permission(user, 'analyst')

    @classmethod
    def can_view_reports(cls, user: User) -> bool:
        """Check if user can view reports (all authenticated users)."""
        return cls.has_permission(user, 'viewer')

    @classmethod
    def can_delete_clients(cls, user: User) -> bool:
        """Check if user can delete clients (admin only)."""
        return cls.can_manage_users(user)