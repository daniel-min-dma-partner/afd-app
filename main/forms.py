from django import forms
from django.utils.safestring import mark_safe


class TreeRemoverForm(forms.Form):
    dataflow = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': False}), required=False,
                               label='Dataflows', help_text='Select a dataflow')
    replacers = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                label='Replacer Dataflow', help_text='Select one or more replacers')
    registers = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 1,
                                                             'placeholder': "List Register Nodes"}),
                                required=True,
                                label=mark_safe(
                                    "List of <strong>sfdcRegisters, registers, edgeMart</strong> nodes"), )
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Output dataflow name'}))
    result = forms.JSONField(required=False, label='Result', initial=False)
