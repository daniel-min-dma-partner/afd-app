import copy

import pytz
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

from .models import SalesforceEnvironment, FileModel, DataflowCompareFilesModel as DFCompModel, Profile
from django.core.exceptions import ValidationError


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control',
                   'placeholder': ''}
        ),
        label=mark_safe("Username"))

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'class': 'form-control form-control-use',
        }))


class RegisterUserForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, initial='password', required=True)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput, initial='password',
                                required=True)

    class Meta:
        model = User
        help_texts = {'username': ''}
        exclude = {'id', 'password', 'is_superuser', 'is_staff', 'last_login', 'date_joined',
                   'user_permissions', 'is_active', 'groups'}
        REQUIRED_FIELDS = [
            'email', 'username', 'password1', 'password2', 'first_name', 'last_name'
        ]

    def clean_email(self):
        _email = self.cleaned_data['email'].strip()
        if User.objects.filter(email=_email).exists():
            raise forms.ValidationError("The email has been already taken.")
        return _email

    def clean_password2(self):
        p1 = self.cleaned_data['password1'].strip()
        p2 = self.cleaned_data['password2'].strip()
        if p1 == p2:
            return p2
        raise forms.ValidationError("Password mismatch")

    def clean_username(self):
        return self.cleaned_data['username'].strip()

    def save(self, commit=True):
        user = super(RegisterUserForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class SfdcEnvEditForm(forms.ModelForm):
    _FORBIDDEN_SYMBOLS = ['-', '+', '*', '$', '&']

    class Meta:
        model = SalesforceEnvironment
        exclude = {'user'}
        REQUIRED_FIELDS = [
            'client_key', 'client_secret', 'client_username', 'client_password', 'environment', 'name'
        ]

    def clean_name(self):
        return ''.join(e for e in self.cleaned_data['name'].strip() if e not in self._FORBIDDEN_SYMBOLS) \
            .replace(' ', "_")

    def save(self, commit=True):
        sfdc_env = super(SfdcEnvEditForm, self).save(commit=False)
        if commit:
            sfdc_env.save()
        return sfdc_env


# SfdcEnvEditFormset = modelformset_factory(SalesforceEnvironment,
#                                           fields=('client_key', 'client_secret', 'client_username',
#                                                   'client_password', 'environment', 'name'), exclude=('user',))


class TreeRemoverForm(forms.Form):
    # Common fields
    dataflow = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': False}), required=False,
                               label='Dataflows', help_text='Select the main dataflow')
    registers = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 1,
                                                             'placeholder': "\"Register\" nodes"}),
                                required=False,
                                label=mark_safe(
                                    "List of <strong>sfdcRegisters, registers, edgeMart</strong> nodes"), )
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Output dataflow name',
                                      'value': 'UpdatedDataflow.json'}), required=False)

    # For tree removers
    replacers = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                label='Replacer Dataflow', help_text='Select new dataflows')

    # For tree extractor
    extract = forms.BooleanField(required=False)

    def clean_extract(self):
        _extract = self.cleaned_data['extract']
        _registers = self.cleaned_data['registers']

        if _extract and not _registers:
            _msg = "When <strong>Extract?</strong> is checked, <strong>sfdcRegister nodes</strong> field can't be empty."
            raise forms.ValidationError(mark_safe(_msg))

        return _extract


class SlackMsgPusherForm(forms.Form):
    case_contact = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control',
                   'placeholder': ''}
        ),
        label=mark_safe("Case Contact Name"),
        required=False
    )
    case_number = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control',
                   'placeholder': 'Output dataflow name'}
        ),
        label=mark_safe("Case Number"),
        required=False
    )
    case_url = forms.URLField(label='SupportForce Case URL')
    case_description = forms.CharField(
        widget=forms.Textarea(
            attrs={'class': 'form-control', 'rows': 1, 'placeholder': 'Brief descriptiion of the customer request.'}
        ),
        label=mark_safe("Case Description")
    )
    case_business_justification = forms.BooleanField(required=False, label=mark_safe("Has Business Justification?"))
    case_manager_approval = forms.BooleanField(required=False, label=mark_safe("Has Manager's Approval?"))
    case_manager_name = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control',
                   'placeholder': ''}
        ),
        label=mark_safe("Case Contact Manager"),
        required=False
    )

    SLACK_WEBHOOK_LINKS = {
        "SFDC_INTERNAL_SUBBARAO": {
            "url": "https://hooks.slack.com/services/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",
            "name": "Subbarao Talachiru"
        },
        "SFDF_I_bt-eops-dna-all": {
            "url": "https://hooks.slack.com/services/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",
            "name": "bt-eops-dna-all"
        },
        "DPARK": {
            "url": "https://hooks.slack.com/services/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",
            "name": "Daniel"
        },
        "SFDC_INTERNAL_TCRM": {
            "url": "https://hooks.slack.com/services/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",
            "name": "bt-eops-tableau-crm"
        },
        "SFDC_SAI_SURESH": {
            "url": "https://hooks.slack.com/services/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",
            "name": "Sai Suresh"
        }
    }

    _SLACK_TARGET_CHOICES = [
        ('SFDC_INTERNAL_SUBBARAO', 'Subbarao Talachiru'),
        ('SFDC_INTERNAL_SAI', 'bt-eops-tableau-crm'),
        ('SFDF_I_bt-eops-dna-all', 'bt-eops-dna-all'),
        ('DPARK', '민 현 기'),
        ('SFDC_SAI_SURESH', 'Sai Suresh'),
    ]

    slack_target = forms.ChoiceField(choices=_SLACK_TARGET_CHOICES, widget=forms.RadioSelect(), required=True)

    @classmethod
    def slack_target_choices(cls):
        return copy.deepcopy(cls._SLACK_TARGET_CHOICES)

    @classmethod
    def get_slack_webhook(cls, key):
        if key not in cls.SLACK_WEBHOOK_LINKS.keys():
            raise KeyError(f"'{key}' is not a valid Slack target.")

        return cls.SLACK_WEBHOOK_LINKS[key]['url']


class SlackCustomerConversationForm(forms.Form):
    channel_id = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control',
                   'placeholder': ''}
        ),
        label=mark_safe("Channel ID")
    )
    case_number_slack_customer = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control',
                   'placeholder': ''}
        ),
        label=mark_safe("Case Number"),
        required=False
    )
    case_url_slack_customer = forms.URLField(label='SupportForce Case URL', required=False)
    _MSG_TPLT_SECTIONS = {
        "salutation": "Hi {{target}}, Nice to meet you! :wave:",
        "whoami": "I'm from Salesforce BT Tableau CRM - Enterprise & Operations Support Team.",
        "reason": "I'm reaching you for your <{{case_url}}|case #{{case_number}}>.",
        "request": "I've left a replay to your case in concierge. Could you review it and provide me the indicated "
                   "additional information?"
    }
    _MESSAGE_TEMPLATE = "\n".join([
        _MSG_TPLT_SECTIONS['salutation'],
        _MSG_TPLT_SECTIONS['whoami'],
        _MSG_TPLT_SECTIONS['reason'],
        _MSG_TPLT_SECTIONS['request'],
    ])

    @classmethod
    def get_msg_template(cls):
        return copy.deepcopy(cls._MESSAGE_TEMPLATE)


class DataflowDownloadForm(forms.Form):
    env_selector = forms.IntegerField()


class DataflowUploadForm(forms.ModelForm):
    dataflow_selector = forms.CharField(required=False)
    env_selector = forms.IntegerField(required=False)

    class Meta:
        model = FileModel
        exclude = {}
        fields = {'file'}
        REQUIRED_FIELDS = [
            'file'
        ]

    def save(self, commit=True):
        model = super(self.__class__, self).save(commit=False)
        if commit:
            model.save()
        return model


class CompareDataflowForm(forms.ModelForm):
    _METHOD_CHOICE = (
        ('jdd', "JDD"),
        ('d2h', "Diff to HTML"),
    )
    field1 = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': False}), required=False)
    field2 = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': False}), required=False)
    method = forms.ChoiceField(choices=_METHOD_CHOICE, widget=forms.RadioSelect(), required=True)

    class Meta:
        model = DFCompModel
        exclude = {}
        fields = {'file1', 'file2'}

    def save(self, commit=True):
        model = super(self.__class__, self).save(commit=False)
        if commit:
            model.save()
        return model


class DeprecateFieldsForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    org = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)
    case_url = forms.URLField(label='SupportForce Case URL')
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': False}), required=False)
    from_file = forms.BooleanField(required=False)
    save_metadata = forms.BooleanField(required=False)
    sobjects = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    fields = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)

    def clean_sobjects(self):
        from_file = self.cleaned_data.get('from_file')
        sobjects = self.cleaned_data.get('sobjects')

        if not from_file and not sobjects:
            raise ValidationError("<code><strong>Objects</strong></code> field can not be empty if <code>From File?</code> is un-checked.")

    def clean_fields(self):
        from_file = self.cleaned_data.get('from_file')
        fields = self.cleaned_data.get('fields')

        if not from_file and not fields:
            raise ValidationError("<code><strong>Fields</strong></code> field can not be empty if <code>From File?</code> is un-checked.")


class SecpredToSaqlForm(forms.Form):
    dataset = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True,
                              label="Dataflow API Name")
    secpred = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': ""}),
                              required=False, label="Security Predicate")
    saql = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': "", "readonly": True}),
        required=False, label="Generated SAQL")


class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ['key', 'value', 'type']

    def clean_key(self):
        key = self.cleaned_data.get('key').strip().lower()

        return key

    def clean_value(self):
        value = self.cleaned_data.get('value').strip()

        if self.clean_key() == 'timezone':
            if value not in pytz.all_timezones:
                link = '<a href="https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568#file-pytz-time-zones-py" target="_blank">here</a>'
                raise ValidationError(f"The timezone <code>{value}</code> is not a valid timezone specification. Check valid timezones string {link}.")

        return value

    def save(self, commit=True):
        model = super(ProfileForm, self).save(commit=False)
        if commit:
            model.save()
        return model
