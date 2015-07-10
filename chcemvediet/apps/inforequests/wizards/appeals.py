# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _

from chcemvediet.apps.inforequests.models import Action
from chcemvediet.apps.inforequests.wizards import WizardStep, Wizard, WizardGroup

appeals = WizardGroup()


def NonFullDisclosureAppealReason(WizardStep):
    reason = forms.CharField(
            label=_(u'inforequests:NonFullDisclosureAppealReason:reason:label'),
            widget=forms.Textarea(attrs={
                u'placeholder': _(u'inforequests:NonFullDisclosureAppealReason:reason:placeholder'),
                u'class': u'input-block-level',
                }),
            )

@appeals.register
def NonFullDisclosureAppealWizard(Wizard):
    u"""
    Appeal wizard for branches that:
     -- are not advanced;
     -- has no previous appeal action; and
     -- end with a non-full disclosure action.
    """

    @classmethod
    def condition(cls, branch):
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


@appeals.register
def RefusalAppealWizard(Wizard):
    u"""
    Trivial appeal wizard for all cases not covered with a more specific wizard.
    """

    @classmethod
    def condition(cls, branch):
        return True
