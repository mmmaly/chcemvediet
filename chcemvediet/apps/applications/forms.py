# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from chcemvediet.apps.obligees.models import validate_obligee_name_exists
from django.contrib.webdesign.lorem_ipsum import paragraphs as lorem
from django.utils.translation import ugettext_lazy as _

class ApplicationForm(forms.Form):
    obligee = forms.CharField(
            label=_(u'Obligee'),
            max_length=255,
            validators=[validate_obligee_name_exists],
            widget=forms.TextInput(attrs={
                'placeholder': _(u'Obligee'),
                }),
            )
    subject = forms.CharField(
            label=_(u'Subject'),
            initial=_(u'Information request'),
            max_length=255,
            widget=forms.TextInput(attrs={
                'placeholder': _(u'Subject'),
                }),
            )
    content = forms.CharField(
            label=_(u'Request'),
            initial=lorem(1)[0],
            widget=forms.Textarea(attrs={
                'placeholder': _(u'Request'),
                'class': 'input-block-level',
                }),
            )

class ApplicationFormDraft(ApplicationForm):
    def __init__(self, *args, **kwargs):
        super(ApplicationFormDraft, self).__init__(*args, **kwargs)
        self.fields['obligee'].required = False
        self.fields['subject'].required = False
        self.fields['content'].required = False

