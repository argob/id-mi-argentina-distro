"""Base command Setup."""

# Utils
from datetime import datetime
import re
from getpass import getpass

# Django
from django.core.management import call_command
from django.core.management.base import BaseCommand

# Models
from id.models import User

class Command(BaseCommand):
    """Base command setup."""

    help = 'Setup the project for the first time'

    def handle(self, *args, **options):
        """handle."""
        call_command('migrate')
        call_command(
            'loaddata',
            'country',
            'provinces',
            'districts',
            'locality',
            'termsandconditions'
        )
        call_command('creatersakey')

        self.stdout.write('Creá tu usuario administrador:')
        user = User()
        try:
            user.email = input('EMAIL: ').lower()
            user.username = user.email
            user.first_name = input('FIRST NAME: ').title()
            user.last_name = input('LAST NAME: ').title()
            user.gender = input('GENDER (M or F): ').upper()
            user.birthdate = datetime.strptime(input('BIRTHDATE (DD/MM/YYYY): '), '%d/%m/%Y').date()

            while True:
                user.password = (getpass(prompt='PASSWORD: '))
                password_confirm = (getpass(prompt='CONFIRMAR PASSWORD: '))
                if user.password == password_confirm:
                    user.set_password(user.password)
                    break
            user.is_active = user.is_staff = user.is_superuser = True
            user.save()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR('FALLÓ LA CREACIÓN DEL USUARIO. Error: {}'.format(e))
            )

        self.stdout.write(self.style.SUCCESS('OK'))
