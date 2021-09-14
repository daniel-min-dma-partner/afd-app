import copy
import datetime
import datetime as dt
import json
import os

import tzlocal
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from tinymce.models import HTMLField

from core.settings import MEDIA_ROOT
from .modelfields import CompressedJSONField

from jsoneditor.fields.django_jsonfield import JSONField


# Create your models here.

class FileModel(models.Model):
    UPLOAD_TO = 'documents/%Y/%m/%d'

    file: models.FileField = models.FileField(upload_to=UPLOAD_TO)
    parent_file = models.ForeignKey("FileModel", blank=True, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def delete(self, using=None, keep_parents=False):
        _filepath = os.path.join(MEDIA_ROOT, self.file.name)
        # print(f'Trying to delete {_filepath}')
        if os.path.isfile(_filepath) and not os.path.isdir(_filepath):
            os.remove(_filepath)
            # print(f"File {_filepath} deleted")

        _filepath = os.path.join(MEDIA_ROOT, self.file.name.replace('ORIGINAL__', '') + '.log')
        # print(f'Trying to delete {_filepath}')
        if os.path.isfile(_filepath) and not os.path.isdir(_filepath):
            os.remove(_filepath)
            # print(f"File {_filepath} deleted")

        _filepath = os.path.join(MEDIA_ROOT, self.file.name.replace('ORIGINAL__', 'DEPRECATED__'))
        # print(f'Trying to delete {_filepath}')
        if os.path.isfile(_filepath) and not os.path.isdir(_filepath):
            os.remove(_filepath)
            # print(f"File {_filepath} deleted")

        if self.pk:
            super(self.__class__, self).delete(using=using, keep_parents=keep_parents)

    def get_filename(self):
        return os.path.basename(self.file.path)


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

    TYPE_CHOICE_SELECT2 = [
        {"id": 'int', 'text': "Integer"},
        {"id": 'str', 'text': "String"},
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    key = models.CharField(max_length=128, help_text='', null=False, blank=False)
    value = models.CharField(max_length=128, help_text='', null=False, blank=False)
    type = models.CharField(max_length=4, help_text='', null=False, blank=False, choices=_TYPE_CHOICE, default='str')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['key', 'user_id'], name='Unique Key constraint per User is enforced')
        ]

    def clean_key(self):
        self.key = self.key.strip()

        return self.key

    def clean_value(self):
        self.value = self.value.strip()

        return self.value

    def get_type_text(self):
        for item in self.TYPE_CHOICE_SELECT2:
            if item['id'] == self.type:
                return item['text']
        return None


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


class Notifications(models.Model):
    _STATUS_CHOICE = (
        (1, 'UNREAD_UNCLICKED'),
        (2, 'READ_UNCLIKED'),
        (3, 'READ_CLICKED')
    )

    _TYPE_CHOICE = (
        ('warning', 'warning'),
        ('success', 'success'),
        ('danger', 'danger'),
        ('info', 'info'),
        ('primary', 'primary'),
    )

    _STATUS_CHOICE_STR = ((_str, num) for (num, _str) in _STATUS_CHOICE)

    _STATUS_MAP = {
        1: 'UNREAD_UNCLICKED',
        2: 'READ_UNCLIKED',
        3: 'READ_CLICKED',
    }

    message = models.CharField(max_length=4096, help_text='', null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.IntegerField(default=1, blank=False, null=False, choices=_STATUS_CHOICE)
    link = models.CharField(max_length=1024, help_text='', null=False, blank=False, default="#")
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=10, help_text='', null=False, blank=False, choices=_TYPE_CHOICE,
                            default='info')

    def __init__(self, *args, **kwargs):
        super(Notifications, self).__init__(*args, **kwargs)
        self.__important_fields = ['status']
        for field in self.__important_fields:
            setattr(self, '__original_%s' % field, getattr(self, field))

    def clean_status(self):
        for field in self.__important_fields:
            orig = '__original_%s' % field
            if getattr(self, orig) is not None and getattr(self, orig) > getattr(self, field):
                msg = f"The status transition of the Notification <code>{self.pk}<code>" \
                      f" from {getattr(self, orig)} to {getattr(self, field)} is not valid."
                raise ValueError(msg)

    def get_status(self):
        return self._STATUS_MAP[self.status] if self.status is not None else None

    def set_status(self, string_code: str = "UNREAD_UNCLICKED"):
        _status_map_rev = {_str: num for num, _str in self._STATUS_MAP.items()}
        self.status = _status_map_rev[string_code.upper()]

    def set_initial_status(self):
        self.set_status()

    @classmethod
    def get_initial_status(cls):
        return 1

    def set_read_clicked(self):
        self.set_status('read_clicked')

    @classmethod
    def get_max_status_level(cls):
        return 3


class DataflowDeprecation(models.Model):
    name = models.CharField(max_length=1024, help_text='', null=False, blank=False)
    salesforce_org = models.CharField(max_length=1024, help_text='', null=False, blank=False)
    sobjects = models.TextField(default="<< sfdc objs api >>")
    fields = models.TextField(default="<< sfdc obj fields api")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    case_url = models.CharField(max_length=1024, help_text='', null=True, blank=True, default="#")
    created_at = models.DateTimeField(auto_now_add=True)

    def get_objects_fields_metadata(self):
        md = {}

        for idx, obj in enumerate(self.sobjects.split('|')):
            md[obj] = self.fields.split('|')[idx].split(',')

        return json.dumps(md)


class DeprecationDetails(models.Model):
    _STATUS_CHOICES = (
        (0, 'no-deprecation'),
        (1, "success"),
        (2, "info"),
        (3, "warning"),
        (4, "danger"),
    )

    ERROR = 4
    WARNING = 3
    INFO = 2
    SUCCESS = 1
    NO_DEPRECATION = 0

    _STATUS_MAP = {
        0: "NO DEPRECATION",
        1: "DEPRECATION SUCCEEDED",
        4: "ERROR"
    }

    _STATUS_BOOSTRAP_COLOR = {
        0: 'info',
        1: 'success',
        2: 'info',
        3: 'warning',
        4: 'danger'
    }

    file_name = models.CharField(max_length=1024, help_text='', null=False, blank=False)
    original_dataflow = CompressedJSONField()
    deprecated_dataflow = CompressedJSONField()
    meta = CompressedJSONField()
    status = models.IntegerField(default=NO_DEPRECATION, blank=False, null=False, choices=_STATUS_CHOICES)
    message = models.CharField(max_length=4096, help_text='', null=True, blank=True)
    deprecation = models.ForeignKey(DataflowDeprecation, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_status_desc(self):
        if self.status in self._STATUS_MAP.keys():
            return self._STATUS_MAP[self.status]
        return self.status

    def get_status_bg_color(self):
        return self._STATUS_BOOSTRAP_COLOR[self.status]


class UploadNotifications(Notifications):
    zipfile_path = models.CharField(max_length=2048, help_text='', null=False, blank=False)
    envname = models.CharField(max_length=128, help_text='', null=False, blank=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Job(models.Model):
    STATUS_CHOICES = (
        ('created', "Created"),
        ('started', "Started"),
        ('progress', 'In Progress'),
        ('failed', 'Failed'),
        ('success', 'Succeeded'),
        ('warning', 'Warning'),
    )

    message = models.CharField(max_length=4096, help_text='', null=False, blank=False, default="New Job Created")
    status = models.CharField(max_length=10, default='created', blank=False, null=False, choices=STATUS_CHOICES)
    progress = models.IntegerField(default=0, blank=False, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    finished_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)

    @classmethod
    def format_duration(cls, duration: datetime.timedelta = None):
        if duration:
            ts = duration.total_seconds()

            days = int(ts // 86400) if ts >= 86400 else 0
            ts -= days * 86400

            hours = int(ts // 3600) if ts >= 3600 else 0
            ts -= hours * 3600

            minutes = int(ts // 60) if ts >= 60 else 0
            ts -= minutes * 60

            seconds = round(ts)

            duration = "{} days, {}:{}:{}".format(days, hours, minutes, seconds) if days else "{}:{}:{}".format(hours,
                                                                                                                minutes,
                                                                                                                seconds)

        return duration

    def duration(self):
        duration = Job.format_duration(
            self.finished_at - self.started_at if self.started_at and self.finished_at else None
        )

        return duration

    def set(self, **descriptor):
        self.message = descriptor['message'] if 'message' in descriptor else self.message
        self.status = descriptor['status'] if 'status' in descriptor else self.status
        self.progress = descriptor['progress'] if 'progress' in descriptor else self.progress
        self.user = descriptor['user'] if 'user' in descriptor else self.user
        self.started_at = descriptor['started_at'] if 'started_at' in descriptor else self.started_at
        self.finished_at = descriptor['finished_at'] if 'finished_at' in descriptor else self.finished_at

    def generate_stages(self, stage_descriptors=None):
        _job_stages_ids = []

        if self._state.adding:
            raise SystemError("Unsaved Job can't generate and/or associate itself new stages.")

        if stage_descriptors and isinstance(stage_descriptors, list):
            for descriptor in stage_descriptors:
                job_stage = JobStage()
                job_stage.set(descriptor)
                job_stage.job = self
                job_stage.save()
                _job_stages_ids.append(job_stage.pk)

        return _job_stages_ids

    def set_started(self, save=False):
        self.status = 'started'
        self.started_at = timezone.now() if not self.started_at else self.started_at

        if save:
            self.save()

    def set_finished(self, save=False):
        self.finished_at = timezone.now() if not self.finished_at else self.finished_at

        if save:
            self.save()

    def set_progress(self, save=False):
        self.status = 'progress'

        if not self.started_at:
            self.started_at = timezone.now() if not self.started_at else self.started_at

        if save:
            self.save()

    def set_successful(self, save=False):
        self.status = 'success'
        self.finished_at = timezone.now() if not self.finished_at else self.finished_at

        if save:
            self.save()

    def set_warning(self, save=False, msg: str = None):
        self.status = 'warning'
        self.finished_at = timezone.now() if not self.finished_at else self.finished_at

        if msg:
            self.message = msg

        if save:
            self.save()

    def set_failed(self, save=False, msg: str = None):
        self.status = 'failed'
        self.finished_at = timezone.now() if not self.finished_at else self.finished_at

        if msg:
            self.message = msg

        if save:
            self.save()

    def get_progress(self):
        all_stages = self.jobstage_set.count()
        succeeded = self.jobstage_set.filter(status='success').count()
        progress = 100 * (succeeded / all_stages)

        return progress

    def add_stage(self, stage_descriptor):
        job_stage = JobStage()
        job_stage.set(stage_descriptor)
        job_stage.job = self
        job_stage.save()

        return [stage.pk for stage in self.jobstage_set.order_by('pk').all()]


class JobStage(models.Model):
    message = models.CharField(max_length=4096, help_text='', null=False, blank=False, default="New Job Created")
    status = models.CharField(max_length=10, default='created', blank=False, null=False, choices=Job.STATUS_CHOICES)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    finished_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)

    def duration(self):
        duration = Job.format_duration(
            self.finished_at - self.started_at if self.started_at and self.finished_at else None
        )

        return duration

    def set(self, descriptor):
        self.message = descriptor['message'] if 'message' in descriptor else self.message
        self.status = descriptor['status'] if 'status' in descriptor else self.status
        self.started_at = descriptor['started_at'] if 'started_at' in descriptor else self.started_at
        self.finished_at = descriptor['finished_at'] if 'finished_at' in descriptor else self.finished_at

    def set_started(self, save=False):
        self.status = 'started'
        self.started_at = timezone.now() if not self.started_at else self.started_at

        if save:
            self.save()

    def set_finished(self, save=False):
        self.finished_at = timezone.now() if not self.finished_at else self.finished_at

        if save:
            self.save()

    def set_progress(self, save=False):
        self.status = 'progress'

        if not self.started_at:
            self.started_at = timezone.now() if not self.started_at else self.started_at

        if save:
            self.save()

    def set_successful(self, save=False):
        self.status = 'success'
        self.finished_at = timezone.now() if not self.finished_at else self.finished_at

        if save:
            self.save()

    def set_warning(self, save=False, msg: str = None):
        self.status = 'warning'
        self.finished_at = timezone.now() if not self.finished_at else self.finished_at

        if msg:
            self.message = msg

        if save:
            self.save()

    def set_failed(self, save=False, msg: str = None):
        self.status = 'failed'
        self.finished_at = timezone.now() if not self.finished_at else self.finished_at

        if msg:
            self.message = msg

        if save:
            self.save()

    def __str__(self):
        return f"Job '{self.message}' at '{self.status}' status."


class Release(models.Model):
    title = models.CharField(max_length=1024, help_text='', null=False, blank=False)
    description = HTMLField(blank=False, null=False)
    publisher = models.ForeignKey(User, models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    modified_at = models.DateTimeField(auto_now_add=True, blank=False, null=False)

    def save(self, *args, **kwargs):
        if not self._state.adding:
            self.modified_at = timezone.now()

        super(Release, self).save(*args, **kwargs)


class Parameter(models.Model):
    parameter = JSONField()
    created_at = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    modified_at = models.DateTimeField(auto_now_add=True, blank=False, null=False)

    def save(self, *args, **kwargs):
        if not self._state.adding:
            self.modified_at = timezone.now()

        super(Parameter, self).save(*args, **kwargs)


class SpecialPermissions(models.Model):
    """
    Used to add custom permissions into database.
    """

    class Meta:
        managed = False  # No database table creation or deletion operations will be performed for this model.

        default_permissions = []  # disable "add", "change", "delete" and "view" default permissions

        permissions = [
            ('special_permission_upload_dataflows', 'Can upload dataflows'),
        ]
