# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from chcemvediet.apps.obligees.models import validate_obligee_name_exists

class ApplicationForm(forms.Form):
    obligee = forms.CharField(
            label=u'Povinná osoba',
            help_text=u'<span id="id_obligee_details">(Vyber povinnú osobu)</span>',
            validators=[validate_obligee_name_exists],
            max_length=255,
            )
    subject = forms.CharField(
            label=u'Vec (subject)',
            initial=u'Žiadosť o informáciu',
            max_length=255,
            )
    message = forms.CharField(
            label=u'Znenie žiadosti',
            widget=forms.Textarea,
            )

