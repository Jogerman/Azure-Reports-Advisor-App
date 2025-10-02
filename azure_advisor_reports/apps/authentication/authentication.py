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
        Verify JWT token with Azure AD.
        """
        # Get Azure AD public keys for token verification
        jwks_url = f"https://login.microsoftonline.com/{settings.AZURE_AD['TENANT_ID']}/discovery/v2.0/keys"

        try:
            # Get the token header
            unverified_header = jwt.get_unverified_header(token)

            # Get public keys from Azure AD
            jwks_response = requests.get(jwks_url, timeout=10)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()

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
                    break

            if not rsa_key:
                raise exceptions.AuthenticationFailed('Unable to find appropriate key')

            # Construct the key
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
            audience = settings.AZURE_AD['CLIENT_ID']
            issuer = f"https://login.microsoftonline.com/{settings.AZURE_AD['TENANT_ID']}/v2.0"

            payload = jwt.decode(
                token,
                pem,
                algorithms=['RS256'],
                audience=audience,
                issuer=issuer
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
        except requests.RequestException as e:
            logger.error(f"Failed to get Azure AD keys: {str(e)}")
            raise exceptions.AuthenticationFailed('Unable to verify token')

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