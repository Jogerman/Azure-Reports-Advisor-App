"""
Management command to create a superuser with environment variables
"""
import os
from django.core.management.base import BaseCommand
from authentication.models import User


class Command(BaseCommand):
    help = 'Create a superuser using environment variables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Admin email address',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Admin password',
        )
        parser.add_argument(
            '--first-name',
            type=str,
            help='Admin first name',
        )
        parser.add_argument(
            '--last-name',
            type=str,
            help='Admin last name',
        )

    def handle(self, *args, **options):
        # Get values from arguments or environment variables
        email = options.get('email') or os.getenv('ADMIN_EMAIL', 'admin@solvex.com.do')
        password = options.get('password') or os.getenv('ADMIN_PASSWORD', 'Admin123!@#')
        first_name = options.get('first_name') or os.getenv('ADMIN_FIRST_NAME', 'Admin')
        last_name = options.get('last_name') or os.getenv('ADMIN_LAST_NAME', 'User')

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'User with email "{email}" already exists.')
            )
            user = User.objects.get(email=email)
            if not user.is_superuser:
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Granted superuser privileges to "{email}"')
                )
        else:
            User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{email}" created successfully!')
            )

        self.stdout.write(
            self.style.SUCCESS('\nYou can now login with:')
        )
        self.stdout.write(f'  Email: {email}')
        self.stdout.write(f'  Password: {password}')
