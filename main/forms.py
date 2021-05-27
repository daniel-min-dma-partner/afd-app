from django import forms
from django.utils.safestring import mark_safe


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
                   'placeholder': 'Output dataflow name'}
        ),
        label=mark_safe("Case Contact Manager"),
        required=False
    )
