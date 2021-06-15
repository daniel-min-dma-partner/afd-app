import copy

from django.contrib.auth.models import User
from django.db import models


# Create your models here.


class SalesforceEnvironment(models.Model):
    _ENVIRONMENT_CHOICE = (
        ('https://test.salesforce.com', 'Sandbox'),
        ('https://login.salesforce.com', 'Production'),
    )

    client_key = models.CharField(max_length=128, help_text='', null=False, blank=False, default='')
    client_secret = models.CharField(max_length=128, help_text='', null=False, blank=False, default='')
    client_username = models.CharField(max_length=128, help_text='', null=False, blank=True, default='')
    client_password = models.CharField(max_length=128, help_text='', null=False, blank=False, default='')
    environment = models.CharField(max_length=28, help_text='', null=False, blank=False, choices=_ENVIRONMENT_CHOICE,
                                   default='https://test.salesforce.com')
    name = models.CharField(max_length=128, help_text='', null=False, blank=False, default='')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'environment', 'name'], name='unique_user_env_name')
        ]

    @classmethod
    def environment_choice(cls):
        return copy.deepcopy(cls._ENVIRONMENT_CHOICE)
