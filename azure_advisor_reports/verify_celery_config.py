#!/usr/bin/env python
"""
Celery Configuration Verification Script

This script verifies that Celery workers can properly access Django settings
and database configuration. Run this before deploying to production.

Usage:
    # Set production environment
    export DJANGO_ENVIRONMENT=production
    export DATABASE_URL=postgresql://user:pass@host:5432/dbname

    # Run verification
    python verify_celery_config.py
"""

import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
django.setup()

from django.conf import settings
from django.db import connection


def verify_settings_module():
    """Verify the correct settings module is loaded."""
    print("\n" + "="*80)
    print("SETTINGS MODULE VERIFICATION")
    print("="*80)

    settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'NOT SET')
    environment = os.environ.get('DJANGO_ENVIRONMENT', 'NOT SET')

    print(f"DJANGO_SETTINGS_MODULE: {settings_module}")
    print(f"DJANGO_ENVIRONMENT: {environment}")

    if environment == 'production' and 'production' not in settings_module.lower():
        print("⚠️  WARNING: DJANGO_ENVIRONMENT=production but not using production settings!")
        return False
    elif environment != 'production' and 'production' in settings_module.lower():
        print("⚠️  WARNING: Using production settings but DJANGO_ENVIRONMENT != production!")
        return False
    else:
        print("✅ Settings module matches environment")
        return True


def verify_database_config():
    """Verify database configuration is correct."""
    print("\n" + "="*80)
    print("DATABASE CONFIGURATION VERIFICATION")
    print("="*80)

    try:
        db_config = settings.DATABASES.get('default', {})

        if not db_config:
            print("❌ DATABASES['default'] is empty or not configured!")
            return False

        engine = db_config.get('ENGINE', 'NOT SET')
        name = db_config.get('NAME', 'NOT SET')
        user = db_config.get('USER', 'NOT SET')
        host = db_config.get('HOST', 'NOT SET')
        port = db_config.get('PORT', 'NOT SET')

        print(f"Database Engine: {engine}")
        print(f"Database Name: {name}")
        print(f"Database User: {user}")
        print(f"Database Host: {host}")
        print(f"Database Port: {port}")

        # Check for SQLite (should not be used in production)
        if 'sqlite' in engine.lower():
            if os.environ.get('DJANGO_ENVIRONMENT') == 'production':
                print("❌ ERROR: Using SQLite in production! Should use PostgreSQL!")
                return False
            else:
                print("⚠️  Using SQLite (acceptable for development/testing)")
                return True

        # Check for PostgreSQL
        if 'postgresql' not in engine.lower():
            print(f"⚠️  WARNING: Not using PostgreSQL (engine: {engine})")

        # Check that all required fields are set
        if not all([engine, name, user, host]):
            print("❌ ERROR: Missing required database configuration!")
            print(f"   ENGINE: {'✓' if engine != 'NOT SET' else '✗'}")
            print(f"   NAME: {'✓' if name != 'NOT SET' else '✗'}")
            print(f"   USER: {'✓' if user != 'NOT SET' else '✗'}")
            print(f"   HOST: {'✓' if host != 'NOT SET' else '✗'}")
            return False

        print("✅ Database configuration is complete")
        return True

    except Exception as e:
        print(f"❌ ERROR accessing database configuration: {e}")
        return False


def verify_database_connection():
    """Verify database connection works."""
    print("\n" + "="*80)
    print("DATABASE CONNECTION TEST")
    print("="*80)

    try:
        # Test connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ Database connection successful!")
            print(f"   Database version: {version[:80]}")
        return True

    except Exception as e:
        print(f"❌ ERROR: Cannot connect to database!")
        print(f"   {type(e).__name__}: {e}")
        return False


def verify_celery_config():
    """Verify Celery configuration."""
    print("\n" + "="*80)
    print("CELERY CONFIGURATION VERIFICATION")
    print("="*80)

    broker_url = getattr(settings, 'CELERY_BROKER_URL', 'NOT SET')
    result_backend = getattr(settings, 'CELERY_RESULT_BACKEND', 'NOT SET')

    print(f"Broker URL: {broker_url[:50]}...")
    print(f"Result Backend: {result_backend[:50]}...")

    if broker_url == 'NOT SET' or result_backend == 'NOT SET':
        print("❌ ERROR: Celery broker or result backend not configured!")
        return False

    print("✅ Celery configuration is present")
    return True


def check_pytest_in_modules():
    """Check if pytest is in sys.modules (the dangerous condition)."""
    print("\n" + "="*80)
    print("PYTEST MODULE CHECK (DANGER ZONE)")
    print("="*80)

    pytest_loaded = 'pytest' in sys.modules

    print(f"'pytest' in sys.modules: {pytest_loaded}")

    if pytest_loaded:
        print("⚠️  WARNING: pytest is loaded in sys.modules!")
        print("   This would have caused database config to fail in the old code.")
        print("   Verify that database config is STILL PostgreSQL (not SQLite).")

        # Verify database is still PostgreSQL
        engine = settings.DATABASES['default'].get('ENGINE', '')
        if 'sqlite' in engine.lower():
            print("❌ CRITICAL: Database switched to SQLite because pytest is loaded!")
            print("   This is the BUG we're trying to fix!")
            return False
        else:
            print("✅ Database is still PostgreSQL despite pytest being loaded (fix working!)")
    else:
        print("✅ pytest is not loaded (ideal state)")

    return True


def main():
    """Run all verification checks."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "CELERY CONFIGURATION VERIFIER" + " "*29 + "║")
    print("╚" + "="*78 + "╝")

    results = []

    # Run all checks
    results.append(("Settings Module", verify_settings_module()))
    results.append(("Database Config", verify_database_config()))
    results.append(("Database Connection", verify_database_connection()))
    results.append(("Celery Config", verify_celery_config()))
    results.append(("Pytest Module Check", check_pytest_in_modules()))

    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)

    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name:.<50} {status}")

    print("="*80)

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n✅ ALL CHECKS PASSED - Celery configuration is correct!")
        print("\nYou can safely deploy this to production.")
        return 0
    else:
        print("\n❌ SOME CHECKS FAILED - Review the errors above!")
        print("\nDo NOT deploy until all checks pass.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
