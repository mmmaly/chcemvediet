# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from django import forms
from django.utils.translation import ugettext_lazy as _

from chcemvediet.apps.wizards import WizardStep
from chcemvediet.apps.inforequests.models import Action

from . import AppealPaperStep, AppealFinalStep, AppealWizard


class DisclosureAppealReasonStep(WizardStep):
    template = u'inforequests/appeals/disclosure-reason.html'

    reason = forms.CharField(
            label=_(u'inforequests:DisclosureAppealReasonStep:reason:label'),
            widget=forms.Textarea(attrs={
                u'placeholder': _(u'inforequests:DisclosureAppealReasonStep:reason:placeholder'),
                u'class': u'input-block-level',
                }),
            )

class DisclosureAppealPaperStep(AppealPaperStep):
    subject_template = u'inforequests/appeals/papers/subject.txt'
    content_template = u'inforequests/appeals/papers/disclosure.html'

    reason = forms.CharField(
            widget=forms.Textarea(attrs={
                u'placeholder': _(u'inforequests:DisclosureAppealPaperStep:reason:placeholder'),
                u'class': u'input-block-level autosize',
                u'cols': u'', u'rows': u'',
                }),
            )

class DisclosureAppealWizard(AppealWizard):
    u"""
    Appeal wizard for branches that end with a non-full disclosure action.
    """
    step_classes = OrderedDict([
            (u'reason', DisclosureAppealReasonStep),
            (u'paper', DisclosureAppealPaperStep),
            (u'final', AppealFinalStep),
            ])

    @classmethod
    def applicable(cls, branch):
        if branch.last_action.type != Action.TYPES.DISCLOSURE:
            return False
        if branch.last_action.disclosure_level == Action.DISCLOSURE_LEVELS.FULL:
            return False
        return True
