"""
Encryption utilities for securely storing Azure credentials.

Uses Fernet symmetric encryption from cryptography library.
"""

import base64
import logging
from django.conf import settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class CredentialEncryption:
    """
    Handles encryption and decryption of sensitive Azure credentials.

    Uses Fernet (symmetric encryption) with a key derived from Django's SECRET_KEY.
    """

    _fernet = None

    @classmethod
    def _get_fernet(cls):
        """
        Get or create Fernet cipher instance.

        Uses Django's SECRET_KEY to derive an encryption key.
        """
        if cls._fernet is None:
            # Derive a 32-byte key from Django's SECRET_KEY
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'azure_cost_monitoring_salt',  # Static salt for consistency
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(
                kdf.derive(settings.SECRET_KEY.encode())
            )
            cls._fernet = Fernet(key)

        return cls._fernet

    @classmethod
    def encrypt(cls, value: str) -> bytes:
        """
        Encrypt a string value.

        Args:
            value: Plain text string to encrypt

        Returns:
            Encrypted bytes

        Example:
            >>> encrypted = CredentialEncryption.encrypt('my-secret-value')
            >>> type(encrypted)
            <class 'bytes'>
        """
        if not value:
            return b''

        try:
            fernet = cls._get_fernet()
            return fernet.encrypt(value.encode())
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            raise

    @classmethod
    def decrypt(cls, encrypted_value: bytes) -> str:
        """
        Decrypt an encrypted value.

        Args:
            encrypted_value: Encrypted bytes

        Returns:
            Decrypted string

        Example:
            >>> encrypted = CredentialEncryption.encrypt('my-secret')
            >>> decrypted = CredentialEncryption.decrypt(encrypted)
            >>> decrypted
            'my-secret'
        """
        if not encrypted_value:
            return ''

        try:
            fernet = cls._get_fernet()
            return fernet.decrypt(encrypted_value).decode()
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            raise

    @classmethod
    def rotate_key(cls, old_secret_key: str, new_secret_key: str, encrypted_value: bytes) -> bytes:
        """
        Re-encrypt a value with a new SECRET_KEY.

        Used when rotating Django's SECRET_KEY.

        Args:
            old_secret_key: Previous Django SECRET_KEY
            new_secret_key: New Django SECRET_KEY
            encrypted_value: Value encrypted with old key

        Returns:
            Value re-encrypted with new key
        """
        # Temporarily use old key to decrypt
        original_secret = settings.SECRET_KEY
        settings.SECRET_KEY = old_secret_key
        cls._fernet = None  # Reset cipher

        try:
            # Decrypt with old key
            decrypted = cls.decrypt(encrypted_value)

            # Switch to new key and encrypt
            settings.SECRET_KEY = new_secret_key
            cls._fernet = None  # Reset cipher

            return cls.encrypt(decrypted)
        finally:
            # Restore original key
            settings.SECRET_KEY = original_secret
            cls._fernet = None


# Convenience functions
encrypt_credential = CredentialEncryption.encrypt
decrypt_credential = CredentialEncryption.decrypt
