"""
Management command to easily create users with roles and permissions.

This command simplifies user creation by:
- Creating the user with specified role
- Automatically assigning to appropriate permission group
- Optionally making them staff or superuser
- Setting up profile information
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group
from django.db import transaction
from apps.authentication.models import User


class Command(BaseCommand):
    help = 'Create a new user with role and permissions'

    def add_arguments(self, parser):
        # Required arguments
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='User email address (will be used as username)',
        )
        parser.add_argument(
            '--password',
            type=str,
            required=True,
            help='User password',
        )
        parser.add_argument(
            '--first-name',
            type=str,
            required=True,
            help='User first name',
        )
        parser.add_argument(
            '--last-name',
            type=str,
            required=True,
            help='User last name',
        )

        # Optional arguments
        parser.add_argument(
            '--role',
            type=str,
            choices=['admin', 'manager', 'analyst', 'viewer'],
            default='analyst',
            help='User role (default: analyst)',
        )
        parser.add_argument(
            '--job-title',
            type=str,
            default='',
            help='Job title',
        )
        parser.add_argument(
            '--department',
            type=str,
            default='',
            help='Department',
        )
        parser.add_argument(
            '--phone',
            type=str,
            default='',
            help='Phone number',
        )
        parser.add_argument(
            '--staff',
            action='store_true',
            help='Grant staff access (Django admin)',
        )
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Make this user a superuser (full system access)',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        role = options['role']
        job_title = options.get('job_title', '')
        department = options.get('department', '')
        phone = options.get('phone', '')
        is_staff = options.get('staff', False)
        is_superuser = options.get('superuser', False)

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email "{email}" already exists.')

        # Create username from email (before @ symbol)
        username = email.split('@')[0]

        # Make username unique if needed
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        self.stdout.write(
            self.style.SUCCESS('Creating new user...')
        )

        # Create user
        if is_superuser:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            self.stdout.write(
                self.style.SUCCESS('✓ Created SUPERUSER account')
            )
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

        # Set additional fields
        user.role = role
        user.job_title = job_title
        user.department = department
        user.phone_number = phone
        user.is_staff = is_staff or is_superuser  # Superusers are always staff
        user.save()

        # Assign to permission group based on role
        role_to_group = {
            'admin': 'Administrator',
            'manager': 'Manager',
            'analyst': 'Analyst',
            'viewer': 'Viewer',
        }

        group_name = role_to_group.get(role)
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Added to "{group_name}" permission group')
                )
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'! Warning: Permission group "{group_name}" not found.'
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        '  Run "python manage.py init_permissions" to create permission groups.'
                    )
                )

        # Display summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 60))
        self.stdout.write(self.style.SUCCESS('User created successfully!'))
        self.stdout.write(self.style.SUCCESS('═' * 60))
        self.stdout.write('')
        self.stdout.write(f'Username:    {user.username}')
        self.stdout.write(f'Email:       {user.email}')
        self.stdout.write(f'Full Name:   {user.full_name}')
        self.stdout.write(f'Role:        {user.get_role_display()}')
        if job_title:
            self.stdout.write(f'Job Title:   {job_title}')
        if department:
            self.stdout.write(f'Department:  {department}')
        self.stdout.write(f'Staff:       {"Yes" if user.is_staff else "No"}')
        self.stdout.write(f'Superuser:   {"Yes" if user.is_superuser else "No"}')
        self.stdout.write(f'Active:      {"Yes" if user.is_active else "No"}')
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write(f'  Email:    {email}')
        self.stdout.write(f'  Password: {password}')
        self.stdout.write('')

        # Role-specific information
        if role == 'admin' or is_superuser:
            self.stdout.write(self.style.SUCCESS('This user has FULL SYSTEM ACCESS.'))
        elif role == 'manager':
            self.stdout.write('This user can:')
            self.stdout.write('  • Manage clients, reports, and analytics')
            self.stdout.write('  • View and modify users (but not delete)')
            self.stdout.write('  • Access Django admin (if --staff flag used)')
        elif role == 'analyst':
            self.stdout.write('This user can:')
            self.stdout.write('  • Create and edit reports')
            self.stdout.write('  • Manage clients')
            self.stdout.write('  • View analytics and other users')
        elif role == 'viewer':
            self.stdout.write('This user can:')
            self.stdout.write('  • View reports and clients (read-only)')
            self.stdout.write('  • Access analytics data')
