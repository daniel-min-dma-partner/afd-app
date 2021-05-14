from django import forms
from django.utils.safestring import mark_safe


class TreeRemoverForm(forms.Form):
    dataflows = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                label='Dataflows', help_text='Select one or more dataflows')
    replacer = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': False}), required=False,
                               label='Replacer Dataflow', help_text='Select one dataflow')
    registers = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 1,
                                                             'placeholder': "List of sfdcRegisters, registers, "
                                                                            "edgeMart nodes"}),
                                required=True,
                                label=mark_safe(
                                    "List of <strong>sfdcRegisters, registers, edgeMart</strong> nodes"), )
    result = forms.JSONField(required=False, label='Result', initial=False)
