from django.conf import settings
from django.core.management.base import BaseCommand
from main.models import SalesforceEnvironment as Env, User, Profile


class Command(BaseCommand):
    def handle(self, *args, **options):
        env = Env.objects
        if not env.exists():
            env = Env(client_username='dpark8752+field-deprecation@gmail.com',
                      client_password='Oktana.secure1',
                      client_key='3MVG9FMtW0XJDLd3c3RjH4jXOyHmZ9mapXe5CJwB.aNdZgPnnApUeW3Yrj1PpNOA2eEVszkpDl.7kYBpkRba0',
                      client_secret='41CAE4ECBA7336C7DEA04218C8096AAB4C2B9E4B2133174884663422A5CBACFF',
                      environment='https://oktana-2be-dev-ed.my.salesforce.com',
                      user_id=1,
                      name='TCRM Dev',
                      oauth_flow_stage=0)
            env.save()
            if env.pk:
                print(f"Environment {env.name} created. PK {env.pk}")
        else:
            print('Default Environment already exists')
