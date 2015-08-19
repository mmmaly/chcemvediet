# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import lazy

from poleno.utils.forms import PrefixedForm


class ExtendDeadlineForm(PrefixedForm):
    template = u'inforequests/modals/extend_deadline.html'

    extension = forms.IntegerField(
            label=_(u'inforequests:ExtendDeadlineForm:extension:label'),
            initial=5,
            min_value=2,
            max_value=100,
            widget=forms.NumberInput(attrs={
                u'placeholder': _(u'inforequests:ExtendDeadlineForm:extension:placeholder'),
                u'class': u'with-tooltip',
                u'data-toggle': u'tooltip',
                u'title': lazy(render_to_string, unicode)(u'inforequests/modals/tooltips/extend_deadline.txt'),
                }),
            )

    def save(self, action):
        assert self.is_valid()
        assert action.deadline is not None

        # User sets the extended deadline relative to today.
        action.extension = action.days_passed - action.deadline + self.cleaned_data[u'extension']
