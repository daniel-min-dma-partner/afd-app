from django.conf import settings
from django.core.management.base import BaseCommand
from main.models import User as Account
from main.models import Profile


class Command(BaseCommand):
    def handle(self, *args, **options):
        account = Account.objects
        if not account.exists():
            username = settings.ADMIN_USERNAME
            email = settings.ADMIN_EMAIL
            password = settings.ADMIN_INITIAL_PASSWORD
            print('Creating account for %s (%s)' % (username, email))
            account = Account.objects.create_superuser(email=email, username=username, password=password)
            account.is_active = True
            account.is_admin = True
            account.is_staff = True
            account.save()
            account.refresh_from_db()

            profile = Account.objects.get(id=account.id).profile_set
            if not profile.exists():
                print(f'Creating a default profile for {account.username}')
                profile.create(key='timezone', value='UTC', type='str')
        else:
            print('Admin accounts can only be initialized if no Accounts exist')
