#!/usr/bin/env python
"""Script to set a user as admin."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
django.setup()

from apps.authentication.models import User

# Update your user to have admin role
email = "jose.gomez@solvex.com.do"

try:
    user = User.objects.get(email=email)
    user.role = 'admin'
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"✅ User {email} updated successfully!")
    print(f"   Role: {user.role}")
    print(f"   Is Staff: {user.is_staff}")
    print(f"   Is Superuser: {user.is_superuser}")
except User.DoesNotExist:
    print(f"❌ User {email} not found!")
    print("\nAvailable users:")
    for u in User.objects.all():
        print(f"   - {u.email} (role: {u.role})")
