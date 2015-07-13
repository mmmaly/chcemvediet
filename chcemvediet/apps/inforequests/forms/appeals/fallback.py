# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _

from chcemvediet.apps.inforequests.forms.wizard import WizardStep

from . import AppealFinalStep, AppealWizard


class FallbackAppealReasonStep(WizardStep):
    template = u'inforequests/appeals/fallback-reason.html'

    reason = forms.CharField(
            label=_(u'inforequests:FallbackAppealReasonStep:reason:label'),
            widget=forms.Textarea(attrs={
                u'placeholder': _(u'inforequests:FallbackAppealReasonStep:reason:placeholder'),
                u'class': u'input-block-level',
                }),
            )

class FallbackAppealWizard(AppealWizard):
    u"""
    Fallback appeal wizard for all cases not covered with a more specific wizard.
    """
    appeal_subject_template = u'inforequests/appeals/content/subject.html'
    appeal_content_template = u'inforequests/appeals/content/fallback.html'
    step_classes = [
            FallbackAppealReasonStep,
            AppealFinalStep,
            ]

    @classmethod
    def applicable(cls, branch):
        return True

    def appeal_context(self):
        res = super(FallbackAppealWizard, self).appeal_context()
        res.update({
                u'reason': self.steps[0].cleaned_data[u'reason'],
                })
        return res
