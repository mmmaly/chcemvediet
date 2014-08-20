# vim: expandtab
# -*- coding: utf-8 -*-
import random

from django import forms
from django.db import IntegrityError
from django.utils.translation import ugettext_lazy as _
from django.contrib.webdesign.lorem_ipsum import paragraphs as lorem

from chcemvediet.apps.obligees.models import Obligee, validate_obligee_name_exists

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

    def save(self, application):
        if not self.is_valid():
            raise ValueError("The %s could not be saved because the data didn't validate." % type(self).__name__)

        obligee_name = self.cleaned_data['obligee']
        application.obligee = Obligee.objects.filter(name=obligee_name)[0]

        application.applicant_name = application.applicant.get_full_name()
        application.applicant_street = application.applicant.profile.street
        application.applicant_city = application.applicant.profile.city
        application.applicant_zip = application.applicant.profile.zip
        application.obligee_name = application.obligee.name
        application.obligee_street = application.obligee.street
        application.obligee_city = application.obligee.city
        application.obligee_zip = application.obligee.zip

        def random_email(domain, length):
            """
            Returns a random e-mail address with ``domain`` for its domain part. The local part of
            the generated e-mail address has form of

            [:vowel:]? ([:consonant:][:vowel:]){length} [:consonant:]?

            where `[:vowel:]` is the set of all vowels `[aeiouy]` and `['consonant']` is the set of
            consonants `[bcdfghjklmnprstvxz]`.
            """
            vowels = 'aeiouy'
            consonants = 'bcdfghjklmnprstvxz'

            res = []
            if random.random() < 0.5:
                res.append(random.choice(vowels))
            for i in range(length):
                res.append(random.choice(consonants))
                res.append(random.choice(vowels))
            if random.random() < 0.5:
                res.append(random.choice(consonants))
            res.append('@')
            res.append(domain)

            return ''.join(res)

        # Use unique random sender email address
        length = 2
        while True:
            application.unique_email = random_email('mail.chcemvediet.sk', length)
            try:
                application.save()
            except IntegrityError:
                length += 1
                continue
            break

class ApplicationFormDraft(ApplicationForm):

    def __init__(self, *args, **kwargs):
        super(ApplicationFormDraft, self).__init__(*args, **kwargs)
        self.fields['obligee'].required = False
        self.fields['subject'].required = False
        self.fields['content'].required = False

    def save(self, draft):
        if not self.is_valid():
            raise ValueError("The %s could not be saved because the data didn't validate." % type(self).__name__)

        obligee_name = self.cleaned_data['obligee']
        draft.obligee = Obligee.objects.filter(name=obligee_name)[0] if obligee_name else None
        draft.subject = self.cleaned_data['subject']
        draft.content = self.cleaned_data['content']
        draft.save()

