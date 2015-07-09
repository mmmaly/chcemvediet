# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.core.validators import validate_email
from django.utils.translation import ugettext_lazy as _

from poleno.utils.forms import ValidatorChain

from .validators import validate_unused_emails

class InviteForm(forms.Form):
    email = forms.CharField(
            label=_(u'invitations:InviteForm:email:label'),
            validators=[ValidatorChain(
                validate_email,
                validate_unused_emails,
                )],
            widget=forms.EmailInput(attrs={
                u'placeholder': _(u'invitations:InviteForm:email:placeholder'),
                }),
            )
