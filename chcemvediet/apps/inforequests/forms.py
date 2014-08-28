# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.db import IntegrityError
from django.utils.translation import ugettext_lazy as _
from django.contrib.webdesign.lorem_ipsum import paragraphs as lorem

from chcemvediet.apps.obligees.models import Obligee, validate_obligee_name_exists

from models import History, Action

class InforequestForm(forms.Form):
    obligee = forms.CharField(
            label=_(u'Obligee'),
            max_length=255,
            validators=[validate_obligee_name_exists],
            widget=forms.TextInput(attrs={
                u'placeholder': _(u'Obligee'),
                }),
            )
    subject = forms.CharField(
            label=_(u'Subject'),
            initial=_(u'Information request'),
            max_length=255,
            widget=forms.TextInput(attrs={
                u'placeholder': _(u'Subject'),
                }),
            )
    content = forms.CharField(
            label=_(u'Request'),
            initial=lorem(1)[0],
            widget=forms.Textarea(attrs={
                u'placeholder': _(u'Request'),
                u'class': u'input-block-level',
                }),
            )

    def save(self, inforequest):
        if not self.is_valid():
            raise ValueError(u"The %s could not be saved because the data didn't validate." % type(self).__name__)

        obligee_name = self.cleaned_data[u'obligee']
        obligee = Obligee.objects.filter(name=obligee_name).first()

        history = History(obligee=obligee)
        history.save() # FIXME: treba? nesavne sa samo, ked sa savne inforequest?
        inforequest.history = history

class InforequestDraftForm(InforequestForm):

    def __init__(self, *args, **kwargs):
        super(InforequestDraftForm, self).__init__(*args, **kwargs)
        self.fields[u'obligee'].required = False
        self.fields[u'subject'].required = False
        self.fields[u'content'].required = False

    def save(self, draft):
        if not self.is_valid():
            raise ValueError(u"The %s could not be saved because the data didn't validate." % type(self).__name__)

        obligee_name = self.cleaned_data[u'obligee']
        draft.obligee = Obligee.objects.filter(name=obligee_name).first() if obligee_name else None
        draft.subject = self.cleaned_data[u'subject']
        draft.content = self.cleaned_data[u'content']

class ExtensionEmailForm(forms.Form):
    deadline = forms.IntegerField(
            label=_(u'New Deadline'),
            initial=Action.DEFAULT_DEADLINES.EXTENSION,
            min_value=2,
            max_value=100,
            widget=forms.NumberInput(attrs={
                u'placeholder': _(u'Deadline'),
                }),
            )

    def save(self, action):
        if not self.is_valid():
            raise ValueError(u"The %s could not be saved because the data didn't validate." % type(self).__name__)

        action.deadline = self.cleaned_data[u'deadline']

