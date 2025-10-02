"""
Authentication services for Azure AD integration and token management.

This module provides services for:
- Azure AD token validation
- User creation and updates from Azure AD profiles
- JWT token generation for API access
- Role-based access control helpers
"""

import logging
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
        Validate Azure AD access token.

        Args:
            access_token: The Azure AD access token to validate

        Returns:
            Tuple of (is_valid, user_info_dict or None)
        """
        try:
            # Get Microsoft's public signing keys
            jwks_uri = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"

            # Check cache first
            cache_key = f"azure_ad_jwks_{self.tenant_id}"
            jwks = cache.get(cache_key)

            if not jwks:
                response = requests.get(jwks_uri, timeout=10)
                response.raise_for_status()
                jwks = response.json()
                cache.set(cache_key, jwks, 3600)  # Cache for 1 hour

            # Decode and validate token
            # Note: For production, implement full JWT validation with public key
            unverified_header = jwt.get_unverified_header(access_token)

            # Get user info from Microsoft Graph API
            graph_url = "https://graph.microsoft.com/v1.0/me"
            headers = {'Authorization': f'Bearer {access_token}'}

            response = requests.get(graph_url, headers=headers, timeout=10)

            if response.status_code == 200:
                user_info = response.json()
                logger.info(f"Successfully validated token for user: {user_info.get('mail')}")
                return True, user_info
            else:
                logger.warning(f"Token validation failed: {response.status_code}")
                return False, None

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return False, None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            return False, None
        except requests.RequestException as e:
            logger.error(f"Request error during token validation: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}")
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
    Service for generating and validating JWT tokens for API access.
    """

    @staticmethod
    def generate_token(user: User) -> Dict[str, str]:
        """
        Generate JWT access and refresh tokens for a user.

        Args:
            user: User instance

        Returns:
            Dictionary with 'access_token' and 'refresh_token'
        """
        try:
            # Access token (expires in 1 hour)
            access_payload = {
                'user_id': str(user.id),
                'email': user.email,
                'role': user.role,
                'exp': datetime.utcnow() + timedelta(hours=1),
                'iat': datetime.utcnow(),
                'type': 'access'
            }

            access_token = jwt.encode(
                access_payload,
                settings.SECRET_KEY,
                algorithm='HS256'
            )

            # Refresh token (expires in 7 days)
            refresh_payload = {
                'user_id': str(user.id),
                'exp': datetime.utcnow() + timedelta(days=7),
                'iat': datetime.utcnow(),
                'type': 'refresh'
            }

            refresh_token = jwt.encode(
                refresh_payload,
                settings.SECRET_KEY,
                algorithm='HS256'
            )

            logger.info(f"Generated JWT tokens for user: {user.email}")

            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': 3600,  # 1 hour
                'token_type': 'Bearer'
            }

        except Exception as e:
            logger.error(f"Error generating JWT token: {str(e)}")
            raise

    @staticmethod
    def validate_token(token: str, token_type: str = 'access') -> Tuple[bool, Optional[Dict]]:
        """
        Validate JWT token.

        Args:
            token: JWT token string
            token_type: Type of token ('access' or 'refresh')

        Returns:
            Tuple of (is_valid, payload_dict or None)
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )

            # Verify token type
            if payload.get('type') != token_type:
                logger.warning(f"Invalid token type. Expected {token_type}, got {payload.get('type')}")
                return False, None

            return True, payload

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return False, None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Error validating JWT token: {str(e)}")
            return False, None

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Generate new access token using refresh token.

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

            # Generate new access token
            access_payload = {
                'user_id': str(user.id),
                'email': user.email,
                'role': user.role,
                'exp': datetime.utcnow() + timedelta(hours=1),
                'iat': datetime.utcnow(),
                'type': 'access'
            }

            access_token = jwt.encode(
                access_payload,
                settings.SECRET_KEY,
                algorithm='HS256'
            )

            return {
                'access_token': access_token,
                'expires_in': 3600,
                'token_type': 'Bearer'
            }

        except User.DoesNotExist:
            logger.error(f"User not found for refresh token: {payload.get('user_id')}")
            return None
        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            return None


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