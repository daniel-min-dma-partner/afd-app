import copy

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

from .models import SalesforceEnvironment


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
                   'user_permissions', 'is_active', 'groups', 'first_name', 'last_name', }
        REQUIRED_FIELDS = [
            'email', 'username', 'password1', 'password2'
        ]

    def clean_email(self):
        _email = self.cleaned_data['email'].rstrip()
        if User.objects.filter(email=_email).exists():
            raise forms.ValidationError("The email has been already taken.")
        return _email

    def clean_password2(self):
        p1 = self.cleaned_data['password1'].rstrip()
        p2 = self.cleaned_data['password2'].rstrip()
        if p1 == p2:
            return p2
        raise forms.ValidationError("Password mismatch")

    def clean_username(self):
        return self.cleaned_data['username'].rstrip()

    def save(self, commit=True):
        user = super(RegisterUserForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# class SfdcEnvEditForm(forms.ModelForm):
#     class Meta:
#         model = SalesforceEnvironment
#         exclude = {'user'}
#         REQUIRED_FIELDS = [
#             'client_key', 'client_secret', 'client_username', 'client_password', 'environment'
#         ]


SfdcEnvEditFormset = forms.modelform_factory(SalesforceEnvironment,
                                             fields=('client_key', 'client_secret', 'client_username',
                                                     'client_password', 'environment'))


class TreeRemoverForm(forms.Form):
    # Common fields
    dataflow = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': False}), required=False,
                               label='Dataflows', help_text='Select a dataflow')
    registers = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 1,
                                                             'placeholder': "List Register Nodes"}),
                                required=True,
                                label=mark_safe(
                                    "List of <strong>sfdcRegisters, registers, edgeMart</strong> nodes"), )
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Output dataflow name',
                                      'value': 'UpdatedDataflow.json'}), required=False)

    # For tree removers
    replacers = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                label='Replacer Dataflow', help_text='Select one or more replacers')

    # For tree extractor
    extract = forms.BooleanField(required=False)


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

    _SLACK_WEBHOOK_LINKS = {
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
        }
    }

    _SLACK_TARGET_CHOICES = [('SFDC_INTERNAL_SUBBARAO', 'Subbarao Talachiru'),
                             ('SFDF_I_bt-eops-dna-all', 'bt-eops-dna-all')]

    slack_target = forms.ChoiceField(choices=_SLACK_TARGET_CHOICES, widget=forms.RadioSelect(), required=True)

    @classmethod
    def slack_target_choices(cls):
        return copy.deepcopy(cls._SLACK_TARGET_CHOICES)

    @classmethod
    def get_slack_webhook(cls, key):
        if key not in cls._SLACK_WEBHOOK_LINKS.keys():
            raise KeyError(f"'{key}' is not a valid Slack target.")

        return cls._SLACK_WEBHOOK_LINKS[key]['url']
