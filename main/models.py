import copy
import datetime as dt
import os

import tzlocal
from django.contrib.auth.models import User
from django.db import models

from core.settings import MEDIA_ROOT


# Create your models here.

class FileModel(models.Model):
    UPLOAD_TO = 'documents/%Y/%m/%d'

    file: models.FileField = models.FileField(upload_to=UPLOAD_TO)
    parent_file = models.ForeignKey("FileModel", blank=True, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def delete(self, using=None, keep_parents=False):
        _filepath = os.path.join(MEDIA_ROOT, self.file.name)
        print(f'Trying to delete {_filepath}')
        if os.path.isfile(_filepath) and not os.path.isdir(_filepath):
            os.remove(_filepath)
            print(f"File {_filepath} deleted")

        _filepath = os.path.join(MEDIA_ROOT, self.file.name.replace('ORIGINAL__', '') + '.log')
        print(f'Trying to delete {_filepath}')
        if os.path.isfile(_filepath) and not os.path.isdir(_filepath):
            os.remove(_filepath)
            print(f"File {_filepath} deleted")

        _filepath = os.path.join(MEDIA_ROOT, self.file.name.replace('ORIGINAL__', 'DEPRECATED__'))
        print(f'Trying to delete {_filepath}')
        if os.path.isfile(_filepath) and not os.path.isdir(_filepath):
            os.remove(_filepath)
            print(f"File {_filepath} deleted")

        super(self.__class__, self).delete(using=using, keep_parents=keep_parents)


class DataflowCompareFilesModel(models.Model):
    file1: models.FileField = models.FileField(upload_to='documents/%Y/%m/%d')
    file2: models.FileField = models.FileField(upload_to='documents/%Y/%m/%d')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def delete(self, using=None, keep_parents=False):
        os.remove(os.path.join(MEDIA_ROOT, self.file1.name))
        os.remove(os.path.join(MEDIA_ROOT, self.file2.name))
        super(self.__class__, self).delete(using=using, keep_parents=keep_parents)


class Profile(models.Model):
    _TYPE_CHOICE = (
        ('int', "Integer"),
        ('str', "String")
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    key = models.CharField(max_length=128, help_text='', null=False, blank=False)
    value = models.CharField(max_length=128, help_text='', null=False, blank=False)
    type = models.CharField(max_length=4, help_text='', null=False, blank=False, choices=_TYPE_CHOICE)

    def clean_key(self):
        self.key = self.key.strip()

        return self.key

    def clean_value(self):
        self.value = self.value.strip()

        return self.value


class SalesforceEnvironment(models.Model):
    _ENVIRONMENT_CHOICE = (
        ('https://test.salesforce.com', 'Sandbox'),
        ('https://login.salesforce.com', 'Production'),
    )

    STATUS_LOGOUT = "LOGOUT"
    STATUS_AUTHORIZATION_CODE_REQUEST = "AUTHORIZATION_CODE_REQUEST"
    STATUS_AUTHORIZATION_CODE_RECEIVE = "AUTHORIZATION_CODE_RECEIVE"
    STATUS_ACCESS_TOKEN_REQUEST = "ACCESS_TOKEN_REQUEST"
    STATUS_ACCESS_TOKEN_RECEIVE = "ACCESS_TOKEN_RECEIVE"

    _OAUTH_FLOW_STAGES = {
        STATUS_LOGOUT: 0,
        STATUS_AUTHORIZATION_CODE_REQUEST: 1,
        STATUS_AUTHORIZATION_CODE_RECEIVE: 2,
        STATUS_ACCESS_TOKEN_REQUEST: 3,
        STATUS_ACCESS_TOKEN_RECEIVE: 4,
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

    instance_url = models.CharField(max_length=256, help_text='', default='', null=True, blank=True)
    oauth_flow_stage = models.IntegerField(default=0, blank=True, null=True)
    oauth_authorization_code = models.CharField(max_length=256, help_text='', default='', null=True, blank=True)
    oauth_access_token = models.CharField(max_length=256, help_text='', default='', null=True, blank=True)
    oauth_access_token_created_date = models.DateTimeField(blank=True, null=True)

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
        self.oauth_access_token_created_date = dt.datetime.now(tz=tzlocal.get_localzone())

    def flush_oauth_data(self):
        self.instance_url = ""
        self.oauth_access_token = ""
        self.oauth_access_token_created_date = None
        self.oauth_authorization_code = ""
        self.oauth_flow_stage = 0

    def get_oauth_flow_stage_string(self):
        inv_map = {v: k for k, v in self._OAUTH_FLOW_STAGES.items()}
        return inv_map[self.oauth_flow_stage].rstrip()

    def get_environment_name(self):
        inv_map = {key: value for (key, value) in self._ENVIRONMENT_CHOICE}
        return inv_map[self.environment]
