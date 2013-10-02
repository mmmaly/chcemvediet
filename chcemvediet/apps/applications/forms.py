# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from chcemvediet.apps.obligees.models import validate_obligee_name_exists
from django.contrib.webdesign.lorem_ipsum import paragraphs as lorem

class ApplicationForm(forms.Form):
    obligee = forms.CharField(
            label='Obligee',
            max_length=255,
            validators=[validate_obligee_name_exists],
            widget=forms.TextInput(attrs={
                'placeholder': 'Obligee',
                'required': 'required',
                }),
            )
    subject = forms.CharField(
            label='Subject',
            initial='Information request',
            max_length=255,
            widget=forms.TextInput(attrs={
                'placeholder': 'Subject',
                'required': 'required',
                }),
            )
    message = forms.CharField(
            label='Request',
            initial=lorem(1)[0],
            widget=forms.Textarea(attrs={
                'placeholder': 'Request',
                'required': 'required',
                }),
            )

