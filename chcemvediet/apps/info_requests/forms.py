# vim: expandtab
# -*- coding: utf-8 -*-
import random

from django import forms
from django.db import IntegrityError
from django.utils.translation import ugettext_lazy as _
from django.contrib.webdesign.lorem_ipsum import paragraphs as lorem

from chcemvediet.apps.obligees.models import Obligee, validate_obligee_name_exists

from models import History

class InfoRequestForm(forms.Form):
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

    def save(self, info_request):
        if not self.is_valid():
            raise ValueError(u"The %s could not be saved because the data didn't validate." % type(self).__name__)

        obligee_name = self.cleaned_data[u'obligee']

        history = History()
        history.obligee = Obligee.objects.filter(name=obligee_name)[0]
        history.obligee_name = history.obligee.name
        history.obligee_street = history.obligee.street
        history.obligee_city = history.obligee.city
        history.obligee_zip = history.obligee.zip
        history.save()

        info_request.history = history

        def random_email(domain, length):
            u"""
            Returns a random e-mail address with ``domain`` for its domain part. The local part of
            the generated e-mail address has form of

            [:vowel:]? ([:consonant:][:vowel:]){length} [:consonant:]?

            where `[:vowel:]` is the set of all vowels `[aeiouy]` and `['consonant']` is the set of
            consonants `[bcdfghjklmnprstvxz]`.
            """
            vowels = u'aeiouy'
            consonants = u'bcdfghjklmnprstvxz'

            res = []
            if random.random() < 0.5:
                res.append(random.choice(vowels))
            for i in range(length):
                res.append(random.choice(consonants))
                res.append(random.choice(vowels))
            if random.random() < 0.5:
                res.append(random.choice(consonants))
            res.append(u'@')
            res.append(domain)

            return u''.join(res)

        # Generate random ``info_request.unique_email``
        length = 2
        while length < 20:
            info_request.unique_email = random_email(u'mail.chcemvediet.sk', length)
            try:
                info_request.save()
            except IntegrityError:
                length += 1
                continue
            break
        else:
            raise RuntimeError(u'Failed to generate unique random e-mail address.')

class InfoRequestDraftForm(InfoRequestForm):

    def __init__(self, *args, **kwargs):
        super(InfoRequestDraftForm, self).__init__(*args, **kwargs)
        self.fields[u'obligee'].required = False
        self.fields[u'subject'].required = False
        self.fields[u'content'].required = False

    def save(self, draft):
        if not self.is_valid():
            raise ValueError(u"The %s could not be saved because the data didn't validate." % type(self).__name__)

        obligee_name = self.cleaned_data[u'obligee']
        draft.obligee = Obligee.objects.filter(name=obligee_name)[0] if obligee_name else None
        draft.subject = self.cleaned_data[u'subject']
        draft.content = self.cleaned_data[u'content']
        draft.save()

