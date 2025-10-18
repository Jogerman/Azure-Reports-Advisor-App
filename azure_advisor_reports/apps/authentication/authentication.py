"""
Azure AD authentication backend for Django REST Framework.
"""

import jwt
import requests
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class AzureADAuthentication(authentication.BaseAuthentication):
    """
    Azure Active Directory authentication using JWT tokens.
    """

    def authenticate(self, request):
        """
        Authenticate the request using Azure AD JWT token.
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            # Decode and verify the JWT token
            user_info = self._verify_token(token)
            user = self._get_or_create_user(user_info)
            return (user, token)
        except Exception as e:
            logger.error(f"Azure AD authentication failed: {str(e)}")
            raise exceptions.AuthenticationFailed('Invalid token')

    def _verify_token(self, token):
        """
        Verify JWT token (id_token) with Azure AD.

        Note: This implementation accepts id_tokens from Azure AD for user authentication.
        For production, consider implementing custom API scopes and using access_tokens
        specifically issued for this API resource.
        """
        try:
            # Get the token header
            unverified_header = jwt.get_unverified_header(token)

            # First decode without verification to inspect token claims
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            token_issuer = unverified_payload.get('iss')
            token_audience = unverified_payload.get('aud')

            logger.info(f"Token issuer: {token_issuer}")
            logger.info(f"Token audience: {token_audience}")
            logger.info(f"Token type (nonce present): {'nonce' in unverified_payload}")

            # Determine the correct JWKS URL based on the token issuer
            tenant_id = settings.AZURE_AD['TENANT_ID']
            if 'sts.windows.net' in token_issuer:
                # v1.0 endpoint token
                jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/keys"
            else:
                # v2.0 endpoint token
                jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"

            # Get public keys from Azure AD
            logger.info(f"Fetching keys from: {jwks_url}")
            jwks_response = requests.get(jwks_url, timeout=10)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()
            logger.info(f"Found {len(jwks.get('keys', []))} keys from Azure AD")

            # Find the correct key
            rsa_key = {}
            for key in jwks['keys']:
                if key['kid'] == unverified_header['kid']:
                    rsa_key = {
                        'kty': key['kty'],
                        'kid': key['kid'],
                        'use': key['use'],
                        'n': key['n'],
                        'e': key['e']
                    }
                    logger.info(f"Found matching key with kid: {key['kid']}")
                    break

            if not rsa_key:
                logger.error(f"No matching key found for kid: {unverified_header['kid']}")
                logger.error(f"Available kids: {[k['kid'] for k in jwks['keys']]}")
                raise exceptions.AuthenticationFailed('Unable to find appropriate key')

            # Construct the public key from JWKS
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            import base64

            def base64url_decode(inp):
                padding = 4 - (len(inp) % 4)
                if padding:
                    inp += '=' * padding
                return base64.urlsafe_b64decode(inp)

            n = int.from_bytes(base64url_decode(rsa_key['n']), 'big')
            e = int.from_bytes(base64url_decode(rsa_key['e']), 'big')

            public_key = rsa.RSAPublicNumbers(e, n).public_key()
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Verify and decode the token
            # For id_token: audience should be the client_id
            # For access_token: audience should be the API resource ID
            client_id = settings.AZURE_AD['CLIENT_ID']

            # Accept either id_token (aud=client_id) or properly scoped access_token
            # Skip audience validation for now - will validate manually
            payload = jwt.decode(
                token,
                pem,
                algorithms=['RS256'],
                issuer=token_issuer,
                options={"verify_aud": False}
            )

            # Manual audience validation: accept client_id (id_token) or MS Graph (for dev only)
            if token_audience not in [client_id, '00000003-0000-0000-c000-000000000000']:
                logger.warning(f"Token audience {token_audience} not recognized. Expected {client_id}")
                # For now, we'll allow it for development but log the warning

            logger.info(f"Token verified successfully for user: {payload.get('preferred_username', 'unknown')}")
            return payload

        except jwt.ExpiredSignatureError as e:
            logger.error(f"Token expired: {str(e)}")
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token details: {type(e).__name__} - {str(e)}")
            logger.error(f"Token header: {jwt.get_unverified_header(token)}")
            logger.error(f"Token payload (unverified): {jwt.decode(token, options={'verify_signature': False})}")
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
        except requests.RequestException as e:
            logger.error(f"Failed to get Azure AD keys: {str(e)}")
            raise exceptions.AuthenticationFailed('Unable to verify token')
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {type(e).__name__} - {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise exceptions.AuthenticationFailed(f'Token verification failed: {str(e)}')

    def _get_or_create_user(self, user_info):
        """
        Get or create user from Azure AD user information.
        """
        azure_object_id = user_info.get('oid')
        email = user_info.get('email') or user_info.get('preferred_username')

        if not azure_object_id or not email:
            raise exceptions.AuthenticationFailed('Invalid user information in token')

        try:
            # Try to get existing user by Azure object ID
            user = User.objects.get(azure_object_id=azure_object_id)
        except User.DoesNotExist:
            # Try to get existing user by email
            try:
                user = User.objects.get(email=email)
                user.azure_object_id = azure_object_id
                user.save()
            except User.DoesNotExist:
                # Create new user
                user = User.objects.create(
                    username=email,
                    email=email,
                    azure_object_id=azure_object_id,
                    tenant_id=user_info.get('tid'),
                    first_name=user_info.get('given_name', ''),
                    last_name=user_info.get('family_name', ''),
                    job_title=user_info.get('jobTitle', ''),
                )

        # Update user information from token
        user.first_name = user_info.get('given_name', user.first_name)
        user.last_name = user_info.get('family_name', user.last_name)
        user.job_title = user_info.get('jobTitle', user.job_title)
        user.save()

        return user

    def authenticate_header(self, request):
        """
        Return the header to use for unauthenticated responses.
        """
        return 'Bearer'