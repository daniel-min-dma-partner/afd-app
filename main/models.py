import copy

from django.contrib.auth.models import User
from django.db import models


# Create your models here.


class SalesforceEnvironment(models.Model):
    _ENVIRONMENT_CHOICE = (
        ('https://test.salesforce.com', 'Sandbox'),
        ('https://login.salesforce.com', 'Production'),
    )

    _OAUTH_FLOW_STAGES = {
        "LOGOUT": 0,
        "AUTHORIZATION_CODE_REQUEST": 1,
        "AUTHORIZATION_CODE_RECEIVE": 2,
        "ACCESS_TOKEN_REQUEST": 3,
        "ACCESS_TOKEN_RECEIVE": 4,
    }

    _HEADER = {'Authorization': "Bearer {{access_token}}", 'Content-Type': "application/json"}

    client_key = models.CharField(max_length=128, help_text='', null=False, blank=False, default='')
    client_secret = models.CharField(max_length=128, help_text='', null=False, blank=False, default='')
    client_username = models.CharField(max_length=128, help_text='', null=False, blank=True, default='')
    client_password = models.CharField(max_length=128, help_text='', null=False, blank=False, default='')
    environment = models.CharField(max_length=28, help_text='', null=False, blank=False, choices=_ENVIRONMENT_CHOICE,
                                   default='https://test.salesforce.com')
    name = models.CharField(max_length=128, help_text='', null=False, blank=False, default='')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    oauth_flow_stage = models.IntegerField(default=0, blank=True, null=True)
    oauth_authorization_code = models.CharField(max_length=256, help_text='', default='', null=True, blank=True)
    oauth_access_token = models.CharField(max_length=256, help_text='', default='', null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'environment', 'name'], name='unique_user_env_name')
        ]

    @classmethod
    def environment_choice(cls):
        return copy.deepcopy(cls._ENVIRONMENT_CHOICE)

    @classmethod
    def oauth_flow_stages(cls):
        return copy.deepcopy(cls._OAUTH_FLOW_STAGES)

    @classmethod
    def get_header_template(cls):
        return copy.deepcopy(cls._HEADER)

    def get_header(self):
        _header_copy = copy.deepcopy(self._HEADER)
        _header_copy = {
            key: value.replace('{{access_token}}', self.oauth_access_token) if key == 'Authorization' else value
            for key, value in self._HEADER.items()
        }

        return _header_copy

    def set_oauth_authorization_code(self, code: str):
        self.oauth_authorization_code = code.rstrip()

    def set_oauth_flow_stage(self, stage):
        self.oauth_flow_stage = self._OAUTH_FLOW_STAGES[stage]

    def set_oauth_access_token(self, token):
        self.oauth_access_token = token.rstrip()

    def flush_oauth_data(self):
        self.oauth_access_token = ""
        self.oauth_authorization_code = ""
        self.oauth_flow_stage = 0

    def get_oauth_flow_stage_string(self):
        inv_map = {v: k for k, v in self._OAUTH_FLOW_STAGES.items()}
        return inv_map[self.oauth_flow_stage].rstrip()

