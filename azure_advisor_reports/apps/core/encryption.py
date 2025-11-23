"""
Shared encryption utilities for securely storing sensitive credentials.

This module provides a centralized encryption service used across multiple apps
including cost_monitoring and azure_integration. Uses Fernet symmetric encryption
from the cryptography library with keys derived from Django's SECRET_KEY.

Security Features:
    - AES-128 encryption in CBC mode with PKCS7 padding (via Fernet)
    - PBKDF2HMAC key derivation with SHA256
    - 100,000 iterations for key strengthening
    - Base64 URL-safe encoding
    - Non-deterministic encryption (different outputs for same input)

Example:
    >>> from apps.core.encryption import encrypt_credential, decrypt_credential
    >>> encrypted = encrypt_credential('my-secret-token')
    >>> decrypted = decrypt_credential(encrypted)
    >>> assert decrypted == 'my-secret-token'
"""

import base64
import logging
from typing import Optional

from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


logger = logging.getLogger(__name__)


class CredentialEncryption:
    """
    Handles encryption and decryption of sensitive credentials.

    This class provides secure symmetric encryption using Fernet, which is built
    on top of AES in CBC mode with PKCS7 padding. The encryption key is derived
    from Django's SECRET_KEY using PBKDF2HMAC with SHA256.

    Thread-safety: This class uses class-level caching of the Fernet instance.
    The Fernet instance itself is thread-safe once created.

    Attributes:
        _fernet (Fernet): Cached Fernet cipher instance
        _salt (bytes): Static salt for key derivation (ensures consistency)
    """

    _fernet: Optional[Fernet] = None
    _salt = b'azure_advisor_shared_encryption_salt'

    @classmethod
    def _get_fernet(cls) -> Fernet:
        """
        Get or create Fernet cipher instance.

        Uses Django's SECRET_KEY to derive a 32-byte encryption key via PBKDF2HMAC.
        The instance is cached at class level for performance.

        Returns:
            Fernet: Configured Fernet cipher instance

        Raises:
            ValueError: If SECRET_KEY is not configured
            TypeError: If SECRET_KEY is not a string

        Note:
            The static salt ensures that the same SECRET_KEY always produces
            the same encryption key, which is necessary for decryption.
        """
        if cls._fernet is None:
            if not hasattr(settings, 'SECRET_KEY') or not settings.SECRET_KEY:
                raise ValueError("Django SECRET_KEY must be configured for encryption")

            # Derive a 32-byte key from Django's SECRET_KEY using PBKDF2HMAC
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=cls._salt,
                iterations=100000,  # OWASP recommended minimum
                backend=default_backend()
            )

            try:
                key = base64.urlsafe_b64encode(
                    kdf.derive(settings.SECRET_KEY.encode('utf-8'))
                )
                cls._fernet = Fernet(key)
                logger.debug("Fernet cipher instance initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Fernet cipher: {str(e)}")
                raise

        return cls._fernet

    @classmethod
    def encrypt(cls, value: str) -> bytes:
        """
        Encrypt a string value.

        The encryption is non-deterministic - encrypting the same value twice
        will produce different ciphertext due to Fernet's use of a random IV.

        Args:
            value: Plain text string to encrypt

        Returns:
            bytes: Encrypted data as bytes. Returns empty bytes for empty input.

        Raises:
            ValueError: If SECRET_KEY is not configured
            TypeError: If value is not a string
            Exception: For other encryption errors

        Example:
            >>> encrypted = CredentialEncryption.encrypt('my-secret-value')
            >>> type(encrypted)
            <class 'bytes'>
            >>> len(encrypted) > 0
            True
        """
        if not value:
            logger.debug("Empty value provided for encryption, returning empty bytes")
            return b''

        if not isinstance(value, str):
            raise TypeError(f"Value must be a string, got {type(value).__name__}")

        try:
            fernet = cls._get_fernet()
            encrypted_data = fernet.encrypt(value.encode('utf-8'))
            logger.debug(f"Successfully encrypted value of length {len(value)}")
            return encrypted_data
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}", exc_info=True)
            raise

    @classmethod
    def decrypt(cls, encrypted_value: bytes) -> str:
        """
        Decrypt an encrypted value.

        Args:
            encrypted_value: Encrypted bytes (output from encrypt method)

        Returns:
            str: Decrypted plain text string. Returns empty string for empty input.

        Raises:
            ValueError: If SECRET_KEY is not configured
            InvalidToken: If encrypted_value is corrupted or was encrypted with different key
            TypeError: If encrypted_value is not bytes
            Exception: For other decryption errors

        Example:
            >>> encrypted = CredentialEncryption.encrypt('my-secret')
            >>> decrypted = CredentialEncryption.decrypt(encrypted)
            >>> decrypted
            'my-secret'
        """
        if not encrypted_value:
            logger.debug("Empty value provided for decryption, returning empty string")
            return ''

        if not isinstance(encrypted_value, bytes):
            raise TypeError(
                f"Encrypted value must be bytes, got {type(encrypted_value).__name__}"
            )

        try:
            fernet = cls._get_fernet()
            decrypted_data = fernet.decrypt(encrypted_value).decode('utf-8')
            logger.debug(f"Successfully decrypted value to length {len(decrypted_data)}")
            return decrypted_data
        except InvalidToken as e:
            logger.error(
                "Invalid token error during decryption. "
                "Data may be corrupted or encrypted with different key."
            )
            raise
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}", exc_info=True)
            raise

    @classmethod
    def rotate_key(
        cls,
        old_secret_key: str,
        new_secret_key: str,
        encrypted_value: bytes
    ) -> bytes:
        """
        Re-encrypt a value with a new SECRET_KEY.

        This is used when rotating Django's SECRET_KEY. It decrypts the value
        using the old key and re-encrypts it with the new key.

        Args:
            old_secret_key: Previous Django SECRET_KEY used for encryption
            new_secret_key: New Django SECRET_KEY to use for re-encryption
            encrypted_value: Value encrypted with the old key

        Returns:
            bytes: Value re-encrypted with the new key

        Raises:
            ValueError: If either key is empty or invalid
            InvalidToken: If encrypted_value cannot be decrypted with old key
            Exception: For other rotation errors

        Warning:
            This temporarily modifies settings.SECRET_KEY. Use with caution
            in multi-threaded environments.

        Example:
            >>> original = "secret-data"
            >>> encrypted_old = CredentialEncryption.encrypt(original)
            >>> # Assume SECRET_KEY changes
            >>> encrypted_new = CredentialEncryption.rotate_key(
            ...     old_secret_key="old-key-here",
            ...     new_secret_key="new-key-here",
            ...     encrypted_value=encrypted_old
            ... )
        """
        if not old_secret_key or not new_secret_key:
            raise ValueError("Both old and new secret keys must be provided")

        if not encrypted_value:
            logger.warning("Empty encrypted value provided for key rotation")
            return b''

        # Save original settings
        original_secret = settings.SECRET_KEY
        original_fernet = cls._fernet

        try:
            # Step 1: Decrypt with old key
            settings.SECRET_KEY = old_secret_key
            cls._fernet = None  # Force recreation with old key
            logger.info("Decrypting value with old secret key")
            decrypted = cls.decrypt(encrypted_value)

            # Step 2: Encrypt with new key
            settings.SECRET_KEY = new_secret_key
            cls._fernet = None  # Force recreation with new key
            logger.info("Re-encrypting value with new secret key")
            re_encrypted = cls.encrypt(decrypted)

            logger.info("Key rotation completed successfully")
            return re_encrypted

        except Exception as e:
            logger.error(f"Key rotation failed: {str(e)}", exc_info=True)
            raise

        finally:
            # Always restore original settings
            settings.SECRET_KEY = original_secret
            cls._fernet = original_fernet
            logger.debug("Restored original SECRET_KEY and Fernet instance")

    @classmethod
    def reset_cipher(cls) -> None:
        """
        Reset the cached Fernet cipher instance.

        Useful for testing or when SECRET_KEY has been changed externally.
        The cipher will be recreated on next use.
        """
        cls._fernet = None
        logger.debug("Fernet cipher instance reset")


# Convenience functions for backward compatibility and simpler imports
def encrypt_credential(value: str) -> bytes:
    """
    Convenience function to encrypt a credential.

    Args:
        value: Plain text string to encrypt

    Returns:
        bytes: Encrypted data

    Example:
        >>> from apps.core.encryption import encrypt_credential
        >>> encrypted = encrypt_credential('my-token')
    """
    return CredentialEncryption.encrypt(value)


def decrypt_credential(encrypted_value: bytes) -> str:
    """
    Convenience function to decrypt a credential.

    Args:
        encrypted_value: Encrypted bytes

    Returns:
        str: Decrypted plain text

    Example:
        >>> from apps.core.encryption import decrypt_credential
        >>> decrypted = decrypt_credential(encrypted_bytes)
    """
    return CredentialEncryption.decrypt(encrypted_value)
