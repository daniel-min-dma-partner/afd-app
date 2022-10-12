from django.conf import settings
from django.core.management.base import BaseCommand
from main.models import SalesforceEnvironment as Env, User, Profile


class Command(BaseCommand):
    def handle(self, *args, **options):
        print('')
