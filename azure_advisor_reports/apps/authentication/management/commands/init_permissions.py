"""
Management command to initialize role-based permission groups.

This creates Django permission groups that correspond to the User roles:
- Administrator: Full access to everything
- Manager: Can manage clients, reports, and users
- Analyst: Can create and view reports, manage clients
- Viewer: Read-only access to reports and clients
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.authentication.models import User
from apps.clients.models import Client, ClientContact, ClientNote
from apps.reports.models import Report, Recommendation, ReportTemplate, ReportShare
from apps.analytics.models import (
    DashboardMetrics,
    UserActivity,
    ReportUsageStats,
    SystemHealthMetrics
)


class Command(BaseCommand):
    help = 'Initialize permission groups based on user roles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Initializing permission groups...'))

        # Define role permissions
        permissions_config = {
            'Administrator': {
                'description': 'Full system access - all permissions',
                'permissions': 'all',
            },
            'Manager': {
                'description': 'Manage clients, reports, users, and analytics',
                'permissions': {
                    'authentication': ['view', 'add', 'change'],  # Can't delete users
                    'clients': ['view', 'add', 'change', 'delete'],
                    'reports': ['view', 'add', 'change', 'delete'],
                    'analytics': ['view', 'add', 'change'],
                },
            },
            'Analyst': {
                'description': 'Create reports and manage clients',
                'permissions': {
                    'authentication': ['view'],  # View users only
                    'clients': ['view', 'add', 'change'],
                    'reports': ['view', 'add', 'change'],  # Can create and edit reports
                    'analytics': ['view'],
                },
            },
            'Viewer': {
                'description': 'Read-only access to reports and clients',
                'permissions': {
                    'authentication': [],  # No user access
                    'clients': ['view'],
                    'reports': ['view'],
                    'analytics': ['view'],
                },
            },
        }

        # Get all content types for our apps
        app_models = {
            'authentication': [User],
            'clients': [Client, ClientContact, ClientNote],
            'reports': [Report, Recommendation, ReportTemplate, ReportShare],
            'analytics': [DashboardMetrics, UserActivity, ReportUsageStats, SystemHealthMetrics],
        }

        # Create or update groups
        for role_name, config in permissions_config.items():
            group, created = Group.objects.get_or_create(name=role_name)

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created group: {role_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⟳ Updating group: {role_name}')
                )
                group.permissions.clear()

            # Add permissions
            if config['permissions'] == 'all':
                # Administrator gets all permissions
                all_permissions = Permission.objects.all()
                group.permissions.set(all_permissions)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  → Granted all {all_permissions.count()} permissions'
                    )
                )
            else:
                # Add specific permissions for each app
                permissions_added = 0

                for app_name, permission_types in config['permissions'].items():
                    if app_name not in app_models:
                        continue

                    for model in app_models[app_name]:
                        content_type = ContentType.objects.get_for_model(model)

                        for perm_type in permission_types:
                            # Map our permission types to Django's naming convention
                            perm_codename = f'{perm_type}_{model._meta.model_name}'

                            try:
                                permission = Permission.objects.get(
                                    content_type=content_type,
                                    codename=perm_codename
                                )
                                group.permissions.add(permission)
                                permissions_added += 1
                            except Permission.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'  ! Permission not found: {perm_codename}'
                                    )
                                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'  → Granted {permissions_added} permissions'
                    )
                )

            self.stdout.write(
                self.style.SUCCESS(f'  → {config["description"]}')
            )

        # Display summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 60))
        self.stdout.write(self.style.SUCCESS('Permission groups initialized successfully!'))
        self.stdout.write(self.style.SUCCESS('═' * 60))
        self.stdout.write('')
        self.stdout.write('Role Hierarchy:')
        self.stdout.write('  1. Administrator - Full access (superuser privileges)')
        self.stdout.write('  2. Manager - Manage clients, reports, and users')
        self.stdout.write('  3. Analyst - Create reports and manage clients')
        self.stdout.write('  4. Viewer - Read-only access')
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('  • Use "python manage.py create_user" to create users with roles')
        self.stdout.write('  • Existing users can be assigned to groups via Django Admin')
        self.stdout.write('  • Groups will automatically grant permissions based on role')
