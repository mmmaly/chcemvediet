# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from django import forms
from django.utils.translation import ugettext_lazy as _

from chcemvediet.apps.wizards import WizardStep

from . import AppealPaperStep, AppealFinalStep, AppealWizard


class FallbackAppealReasonStep(WizardStep):
    template = u'inforequests/appeals/fallback-reason.html'

    reason = forms.CharField(
            label=_(u'inforequests:FallbackAppealReasonStep:reason:label'),
            widget=forms.Textarea(attrs={
                u'placeholder': _(u'inforequests:FallbackAppealReasonStep:reason:placeholder'),
                u'class': u'input-block-level',
                }),
            )

class FallbackAppealPaperStep(AppealPaperStep):
    subject_template = u'inforequests/appeals/papers/subject.txt'
    content_template = u'inforequests/appeals/papers/fallback.html'

    reason = forms.CharField(
            widget=forms.Textarea(attrs={
                u'placeholder': _(u'inforequests:FallbackAppealPaperStep:reason:placeholder'),
                u'class': u'input-block-level autosize',
                u'cols': u'', u'rows': u'',
                }),
            )

    def __init__(self, *args, **kwargs):
        super(FallbackAppealPaperStep, self).__init__(*args, **kwargs)
        self.initial[u'reason'] = self.wizard.steps[u'reason'].get_cleaned_data(u'reason')


class FallbackAppealWizard(AppealWizard):
    u"""
    Fallback appeal wizard for all cases not covered with a more specific wizard.
    """
    step_classes = OrderedDict([
            (u'reason', FallbackAppealReasonStep),
            (u'paper', FallbackAppealPaperStep),
            (u'final', AppealFinalStep),
            ])

    @classmethod
    def applicable(cls, branch):
        return True
