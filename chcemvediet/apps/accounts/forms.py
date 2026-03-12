# vim: expandtab
# -*- coding: utf-8 -*-
from allauth.account.forms import (LoginForm as AllauthLoginForm,
                                   SignupForm as AllauthSignupForm,
                                   ResetPasswordForm as AllauthResetPasswordForm)
from allauth.utils import set_form_field_order
from captcha.fields import ReCaptchaField
from django import forms
from django.utils.translation import ngettext_lazy, gettext_lazy as _

from poleno.utils.lazy import lazy_format
from poleno.utils.forms import RangeWidget
from chcemvediet.apps.anonymization.anonymization import (WORD_SIZE_MIN,
                                                          get_default_anonymized_strings_for_user)
from chcemvediet.apps.inforequests.constants import MAX_DAYS_TO_PUBLISH_INFOREQUEST


class LoginForm(AllauthLoginForm):

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields[u'recaptcha'] = ReCaptchaField(label=u'')

class SignupForm(AllauthSignupForm):
    first_name = forms.CharField(
            max_length=30,
            label=_(u'accounts:SignupForm:first_name:label'),
            widget=forms.TextInput(attrs={
                u'placeholder': _(u'accounts:SignupForm:first_name:placeholder'),
                }),
            )
    last_name = forms.CharField(
            max_length=30,
            label=_(u'accounts:SignupForm:last_name:label'),
            widget=forms.TextInput(attrs={
                u'placeholder': _(u'accounts:SignupForm:last_name:placeholder'),
                }),
            )
    street = forms.CharField(
            max_length=100,
            label=_(u'accounts:SignupForm:street:label'),
            widget=forms.TextInput(attrs={
                u'placeholder': _(u'accounts:SignupForm:street:placeholder'),
                }),
            )
    city = forms.CharField(
            max_length=30,
            label=_(u'accounts:SignupForm:city:label'),
            widget=forms.TextInput(attrs={
                u'placeholder': _(u'accounts:SignupForm:city:placeholder'),
                }),
            )
    zip = forms.RegexField(
            max_length=5,
            label=_(u'accounts:SignupForm:zip:label'),
            widget=forms.TextInput(attrs={
                u'placeholder': _(u'accounts:SignupForm:zip:placeholder'),
                }),
            regex=r'^\d{5}$',
            )
    agreement = forms.BooleanField(
            label=_(u'accounts:SignupForm:agreement:label'),
            required=True,
            )
    recaptcha = ReCaptchaField(label=u'')

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        fields_order = (u'first_name', u'last_name', u'street', u'city', u'zip', u'email',
                        u'password1', u'password2', u'agreement', u'recaptcha',)
        set_form_field_order(self, fields_order)

    def save(self, request):
        user = super(SignupForm, self).save(request)
        user.first_name = self.cleaned_data[u'first_name']
        user.last_name = self.cleaned_data[u'last_name']
        user.save()
        user.profile.street = self.cleaned_data[u'street']
        user.profile.city = self.cleaned_data[u'city']
        user.profile.zip = self.cleaned_data[u'zip']
        user.profile.save()
        return user

class ResetPasswordForm(AllauthResetPasswordForm):

    def __init__(self, *args, **kwargs):
        super(ResetPasswordForm, self).__init__(*args, **kwargs)
        self.fields[u'recaptcha'] = ReCaptchaField(label=u'')

class SettingsForm(forms.Form):

    anonymize_inforequests = forms.BooleanField(
            label=_(u'accounts:SettingsForm:anonymize_inforequests:label'),
            required=False,
            )

    custom_anonymization = forms.BooleanField(
            label=_(u'accounts:SettingsForm:custom_anonymization:label'),
            required=False,
            widget=forms.CheckboxInput(attrs={
                u'class': u'pln-toggle-changed',
                u'data-container': u'form',
                u'data-hide-target-true': u'.form-group:has(.chv-visible-if-custom-anonymization)',
                u'data-disable-target-true': u'.chv-visible-if-custom-anonymization',
            }),
            )

    custom_anonymized_strings = forms.CharField(
            label=_(u'accounts:SettingsForm:custom_anonymized_strings:label'),
            required=False,
            help_text=lazy_format(ngettext_lazy(
                u'accounts:SettingsForm:custom_anonymized_strings:help_text',
                u'accounts:SettingsForm:custom_anonymized_strings:help_text {count}',
                WORD_SIZE_MIN), count=WORD_SIZE_MIN),
            widget=forms.Textarea(attrs={
                u'class': u'pln-autosize chv-visible-if-custom-anonymization',
                u'cols': u'', u'rows': u'',
                }),
            )

    days_to_publish_inforequest = forms.IntegerField(
            min_value=0,
            max_value=MAX_DAYS_TO_PUBLISH_INFOREQUEST,
            label=_(u'accounts:SettingsForm:days_to_publish_inforequest:label'),
            help_text=_(u'accounts:SettingsForm:days_to_publish_inforequest:help_text'),
            widget=RangeWidget(attrs={
                u'min': 0,
                u'step': 1,
                u'max': MAX_DAYS_TO_PUBLISH_INFOREQUEST,
                }),
            )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        kwargs[u'initial'] = {
                u'anonymize_inforequests': self.user.profile.anonymize_inforequests,
                u'custom_anonymization': self.user.profile.custom_anonymized_strings is not None,
                u'custom_anonymized_strings': self._initial_custom_anonymized_strings(),
                u'days_to_publish_inforequest': self.user.profile.days_to_publish_inforequest
                }
        super(SettingsForm, self).__init__(*args, **kwargs)

    def save(self):
        profile = self.user.profile
        profile.anonymize_inforequests = self.cleaned_data[u'anonymize_inforequests']
        profile.custom_anonymized_strings = self.cleaned_data[u'custom_anonymized_strings']
        profile.days_to_publish_inforequest = self.cleaned_data[u'days_to_publish_inforequest']
        profile.save(update_fields=[u'anonymize_inforequests',
                                    u'custom_anonymized_strings',
                                    u'days_to_publish_inforequest',
                                    ]
                     )

    def clean_custom_anonymized_strings(self):
        if self.cleaned_data[u'custom_anonymization'] is False:
            return None
        custom_anonymized_strings = self.cleaned_data[u'custom_anonymized_strings']
        lines = []
        if not custom_anonymized_strings:
            msg = _(u'accounts:SettingsForm:custom_anonymized_strings:error:empty')
            raise forms.ValidationError(msg)
        for line in custom_anonymized_strings.split(u'\n'):
            line = line.strip()
            if len(line) >= WORD_SIZE_MIN:
                lines.append(line)
            else:
                error_message = lazy_format(ngettext_lazy(
                        u'accounts:SettingsForm:custom_anonymized_strings:error:line_too_short',
                        u'accounts:SettingsForm:custom_anonymized_strings:error:line_too_short {count}',
                        WORD_SIZE_MIN), count=WORD_SIZE_MIN)
                raise forms.ValidationError(error_message)
        return lines

    def _initial_custom_anonymized_strings(self):
        ret = self.user.profile.custom_anonymized_strings
        if ret is None:
            words, numbers = get_default_anonymized_strings_for_user(self.user)
            ret = words + numbers
        return u'\n'.join(ret)
