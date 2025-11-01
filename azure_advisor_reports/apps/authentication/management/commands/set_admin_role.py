"""
Django management command to set a user as admin.
"""
from django.core.management.base import BaseCommand, CommandError
from apps.authentication.models import User


class Command(BaseCommand):
    help = 'Set a user as admin by email address'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address of the user to set as admin'
        )

    def handle(self, *args, **options):
        email = options['email']

        try:
            user = User.objects.get(email=email)
            user.role = 'admin'
            user.is_staff = True
            user.is_superuser = True
            user.save()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated user {email}')
            )
            self.stdout.write(f'  Role: {user.role}')
            self.stdout.write(f'  Is Staff: {user.is_staff}')
            self.stdout.write(f'  Is Superuser: {user.is_superuser}')

        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {email} not found!')
            )
            self.stdout.write('\nAvailable users:')
            for u in User.objects.all():
                self.stdout.write(f'  - {u.email} (role: {u.role})')
            raise CommandError(f'User {email} does not exist')
