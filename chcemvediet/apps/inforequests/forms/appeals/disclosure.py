# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _

from chcemvediet.apps.inforequests.models import Action
from chcemvediet.apps.inforequests.forms.wizard import WizardStep

from . import AppealFinalStep, AppealWizard


class DisclosureAppealReasonStep(WizardStep):
    template = u'inforequests/appeals/disclosure-reason.html'

    reason = forms.CharField(
            label=_(u'inforequests:DisclosureAppealReasonStep:reason:label'),
            widget=forms.Textarea(attrs={
                u'placeholder': _(u'inforequests:DisclosureAppealReasonStep:reason:placeholder'),
                u'class': u'input-block-level',
                }),
            )

class DisclosureAppealWizard(AppealWizard):
    u"""
    Appeal wizard for branches that:
     -- are not advanced;
     -- has no previous appeal action; and
     -- end with a non-full disclosure action.
    """
    appeal_subject_template = u'inforequests/appeals/content/subject.html'
    appeal_content_template = u'inforequests/appeals/content/disclosure.html'
    step_classes = [
            DisclosureAppealReasonStep,
            AppealFinalStep,
            ]

    @classmethod
    def applicable(cls, branch):
        if not branch.is_main:
            return False
        for action in branch.actions:
            if action.type == Action.TYPES.APPEAL:
                return False
        if branch.last_action.type != Action.TYPES.DISCLOSURE:
            return False
        if branch.last_action.disclosure_level == Action.DISCLOSURE_LEVELS.FULL:
            return False
        return True

    def appeal_context(self):
        res = super(DisclosureAppealWizard, self).appeal_context()
        res.update({
                u'not_at_all': self.branch.last_action.disclosure_level == Action.DISCLOSURE_LEVELS.NONE,
                u'reason': self.steps[0].cleaned_data[u'reason'],
                })
        return res
