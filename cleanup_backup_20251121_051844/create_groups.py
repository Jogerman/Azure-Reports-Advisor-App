#!/usr/bin/env python
"""Script to manually create permission groups."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.authentication.models import User
from apps.clients.models import Client, ClientContact, ClientNote
from apps.reports.models import Report, Recommendation, ReportTemplate, ReportShare
from apps.analytics.models import DashboardMetrics, UserActivity, ReportUsageStats, SystemHealthMetrics

# Define models per app
app_models = {
    'authentication': [User],
    'clients': [Client, ClientContact, ClientNote],
    'reports': [Report, Recommendation, ReportTemplate, ReportShare],
    'analytics': [DashboardMetrics, UserActivity, ReportUsageStats, SystemHealthMetrics],
}

# Manager group - can manage most things but not delete users
print("Creating Manager group...")
group, created = Group.objects.get_or_create(name='Manager')
group.permissions.clear()
count = 0
for app_name in ['authentication', 'clients', 'reports', 'analytics']:
    if app_name == 'authentication':
        perms = ['view', 'add', 'change']  # No delete for users
    elif app_name == 'analytics':
        perms = ['view', 'add', 'change']
    else:
        perms = ['view', 'add', 'change', 'delete']

    for model in app_models[app_name]:
        ct = ContentType.objects.get_for_model(model)
        for pt in perms:
            try:
                p = Permission.objects.get(content_type=ct, codename=f'{pt}_{model._meta.model_name}')
                group.permissions.add(p)
                count += 1
            except Permission.DoesNotExist:
                pass
print(f"Manager group: {count} permissions")

# Analyst group - can create reports and manage clients
print("Creating Analyst group...")
group, created = Group.objects.get_or_create(name='Analyst')
group.permissions.clear()
count = 0
for app_name in ['authentication', 'clients', 'reports', 'analytics']:
    if app_name in ['authentication', 'analytics']:
        perms = ['view']  # Read-only for users and analytics
    else:
        perms = ['view', 'add', 'change']  # Can create/edit clients and reports

    for model in app_models[app_name]:
        ct = ContentType.objects.get_for_model(model)
        for pt in perms:
            try:
                p = Permission.objects.get(content_type=ct, codename=f'{pt}_{model._meta.model_name}')
                group.permissions.add(p)
                count += 1
            except Permission.DoesNotExist:
                pass
print(f"Analyst group: {count} permissions")

# Viewer group - read-only access
print("Creating Viewer group...")
group, created = Group.objects.get_or_create(name='Viewer')
group.permissions.clear()
count = 0
for app_name in ['clients', 'reports', 'analytics']:  # No user access for viewers
    for model in app_models[app_name]:
        ct = ContentType.objects.get_for_model(model)
        try:
            p = Permission.objects.get(content_type=ct, codename=f'view_{model._meta.model_name}')
            group.permissions.add(p)
            count += 1
        except Permission.DoesNotExist:
            pass
print(f"Viewer group: {count} permissions")

print("\nAll groups created successfully!")
print("Total groups:", Group.objects.count())
for g in Group.objects.all().order_by('name'):
    print(f"  - {g.name}: {g.permissions.count()} permissions")
