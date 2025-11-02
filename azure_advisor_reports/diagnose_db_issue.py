#!/usr/bin/env python
"""
Deep diagnostic script to identify why Django is loading with dummy database backend
despite DATABASE_URL being set correctly.
"""

import os
import sys
from pathlib import Path

print("=" * 80)
print("DJANGO DATABASE CONFIGURATION DIAGNOSTIC TOOL")
print("=" * 80)

# Add the project to the path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("\n1. ENVIRONMENT VARIABLES CHECK")
print("-" * 80)
database_url = os.environ.get('DATABASE_URL')
print(f"DATABASE_URL exists: {database_url is not None}")
if database_url:
    # Mask password for security
    masked_url = database_url.split('@')[0].split(':')[:-1]
    print(f"DATABASE_URL value (masked): {':'.join(masked_url)}:****@...")
    print(f"DATABASE_URL length: {len(database_url)}")
else:
    print("DATABASE_URL: NOT SET")

print(f"\nDJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE', 'NOT SET')}")
print(f"DJANGO_ENVIRONMENT: {os.environ.get('DJANGO_ENVIRONMENT', 'NOT SET')}")

print("\n2. SETTINGS MODULE DETECTION")
print("-" * 80)
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
print(f"Settings module to be loaded: {settings_module}")

# Check if it's a split settings structure
if 'settings' in settings_module:
    parts = settings_module.split('.')
    print(f"Settings structure: {' -> '.join(parts)}")

print("\n3. PYTHON PATH CHECK")
print("-" * 80)
print(f"Current working directory: {os.getcwd()}")
print(f"Base directory: {BASE_DIR}")
print(f"Python version: {sys.version}")
print(f"Python path entries ({len(sys.path)}):")
for i, path in enumerate(sys.path[:5], 1):
    print(f"  {i}. {path}")

print("\n4. CHECKING FOR .env FILES")
print("-" * 80)
env_files = [
    BASE_DIR / '.env',
    BASE_DIR.parent / '.env',
    BASE_DIR / 'azure_advisor_reports' / '.env',
]
for env_file in env_files:
    exists = env_file.exists()
    print(f"  {env_file}: {'EXISTS' if exists else 'NOT FOUND'}")
    if exists:
        with open(env_file, 'r') as f:
            lines = f.readlines()
            has_database_url = any('DATABASE_URL' in line and not line.strip().startswith('#') for line in lines)
            print(f"    - Contains DATABASE_URL: {has_database_url}")

print("\n5. TESTING dj_database_url PARSING")
print("-" * 80)
try:
    import dj_database_url
    print("dj_database_url module: INSTALLED")

    if database_url:
        parsed = dj_database_url.parse(database_url)
        print(f"Parsed database config:")
        print(f"  ENGINE: {parsed.get('ENGINE')}")
        print(f"  NAME: {parsed.get('NAME')}")
        print(f"  USER: {parsed.get('USER')}")
        print(f"  HOST: {parsed.get('HOST')}")
        print(f"  PORT: {parsed.get('PORT')}")
    else:
        print("Cannot parse - DATABASE_URL not set")
except ImportError:
    print("dj_database_url module: NOT INSTALLED")

print("\n6. CHECKING sys.argv AND pytest")
print("-" * 80)
print(f"sys.argv: {sys.argv}")
print(f"'test' in sys.argv: {'test' in sys.argv}")
print(f"'pytest' in sys.modules: {'pytest' in sys.modules}")

print("\n7. ATTEMPTING TO LOAD DJANGO SETTINGS")
print("-" * 80)
try:
    # Set the settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

    # Import Django
    import django
    print(f"Django version: {django.get_version()}")

    # Setup Django
    django.setup()
    print("Django setup: SUCCESS")

    # Import settings
    from django.conf import settings

    # Check DATABASES configuration
    print(f"\nDATABASES configuration:")
    databases = settings.DATABASES
    default_db = databases.get('default', {})

    print(f"  ENGINE: {default_db.get('ENGINE')}")
    print(f"  NAME: {default_db.get('NAME')}")
    print(f"  USER: {default_db.get('USER')}")
    print(f"  HOST: {default_db.get('HOST')}")
    print(f"  PORT: {default_db.get('PORT')}")

    # Check if it's the dummy backend
    if default_db.get('ENGINE') == 'django.db.backends.dummy':
        print("\n" + "!" * 80)
        print("PROBLEM CONFIRMED: Django loaded with dummy backend!")
        print("!" * 80)
    elif default_db.get('ENGINE') == 'django.db.backends.sqlite3':
        print("\nDjango loaded with SQLite backend (test mode)")
    elif default_db.get('ENGINE') == 'django.db.backends.postgresql':
        print("\nSUCCESS: Django loaded with PostgreSQL backend!")

    # Additional settings checks
    print(f"\nDEBUG: {settings.DEBUG}")
    print(f"SECRET_KEY set: {bool(settings.SECRET_KEY)}")

except Exception as e:
    print(f"ERROR loading Django settings: {e}")
    import traceback
    traceback.print_exc()

print("\n8. SETTINGS FILE ANALYSIS")
print("-" * 80)

# Check which settings files exist
settings_dir = BASE_DIR / 'azure_advisor_reports' / 'settings'
if settings_dir.exists():
    print(f"Settings directory structure:")
    for file in settings_dir.glob('*.py'):
        if not file.name.startswith('__pycache__'):
            print(f"  - {file.name}")

            # Read the file and check for DATABASE configuration
            with open(file, 'r') as f:
                content = f.read()
                has_databases = 'DATABASES' in content
                has_database_url = 'DATABASE_URL' in content
                has_dj_database_url = 'dj_database_url' in content

                print(f"    * Contains DATABASES: {has_databases}")
                print(f"    * Contains DATABASE_URL: {has_database_url}")
                print(f"    * Uses dj_database_url: {has_dj_database_url}")
else:
    print("No settings directory found - checking for single settings.py")
    settings_file = BASE_DIR / 'azure_advisor_reports' / 'settings.py'
    if settings_file.exists():
        print("Found single settings.py file")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)

# Provide recommendations based on findings
print("\nRECOMMENDATIONS:")
print("-" * 80)

if not database_url:
    print("1. DATABASE_URL environment variable is NOT set")
    print("   Solution: Set DATABASE_URL in your environment")

if settings_module == 'azure_advisor_reports.settings':
    print("2. Using settings package - check __init__.py for correct routing")
    print("   The __init__.py should route to the correct environment settings")

print("\nFor Azure Container Apps:")
print("  - Ensure DATABASE_URL is set in Container App environment variables")
print("  - Set DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production")
print("  - Or ensure settings/__init__.py properly detects production environment")
