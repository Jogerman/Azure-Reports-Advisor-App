"""
Standalone test for encryption module - can run without full Django setup.

This is a simplified test that can verify the encryption module works
before running the full test suite.
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Minimal Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings.base')

import django
from django.conf import settings

# Configure minimal settings if not already configured
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key-for-encryption-testing-12345678901234567890',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
    )

django.setup()

# Now import and test
from apps.core.encryption import CredentialEncryption, encrypt_credential, decrypt_credential


def test_basic_encryption():
    """Test basic encryption/decryption."""
    print("Testing basic encryption...")
    original = "my-secret-value"
    encrypted = CredentialEncryption.encrypt(original)
    decrypted = CredentialEncryption.decrypt(encrypted)
    assert decrypted == original, f"Expected {original}, got {decrypted}"
    print("✓ Basic encryption works")


def test_empty_values():
    """Test empty value handling."""
    print("Testing empty values...")
    assert CredentialEncryption.encrypt("") == b''
    assert CredentialEncryption.decrypt(b'') == ''
    assert CredentialEncryption.encrypt(None) == b''
    assert CredentialEncryption.decrypt(None) == ''
    print("✓ Empty values handled correctly")


def test_non_determinism():
    """Test that same value produces different ciphertext."""
    print("Testing non-determinism...")
    value = "test-value"
    encrypted1 = CredentialEncryption.encrypt(value)
    encrypted2 = CredentialEncryption.encrypt(value)
    assert encrypted1 != encrypted2, "Encryption should be non-deterministic"

    decrypted1 = CredentialEncryption.decrypt(encrypted1)
    decrypted2 = CredentialEncryption.decrypt(encrypted2)
    assert decrypted1 == value
    assert decrypted2 == value
    print("✓ Non-deterministic encryption works")


def test_convenience_functions():
    """Test convenience functions."""
    print("Testing convenience functions...")
    original = "test-credential"
    encrypted = encrypt_credential(original)
    decrypted = decrypt_credential(encrypted)
    assert decrypted == original
    print("✓ Convenience functions work")


def test_invalid_data():
    """Test invalid data handling."""
    print("Testing invalid data handling...")
    try:
        CredentialEncryption.decrypt(b'invalid-encrypted-data')
        assert False, "Should have raised exception"
    except Exception as e:
        print(f"✓ Invalid data raises exception: {type(e).__name__}")


def test_unicode():
    """Test unicode support."""
    print("Testing unicode...")
    unicode_value = "🔐 Secret™ データ"
    encrypted = CredentialEncryption.encrypt(unicode_value)
    decrypted = CredentialEncryption.decrypt(encrypted)
    assert decrypted == unicode_value
    print("✓ Unicode works")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Running Standalone Encryption Tests")
    print("="*60 + "\n")

    tests = [
        test_basic_encryption,
        test_empty_values,
        test_non_determinism,
        test_convenience_functions,
        test_invalid_data,
        test_unicode,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} FAILED: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    if failed > 0:
        sys.exit(1)
