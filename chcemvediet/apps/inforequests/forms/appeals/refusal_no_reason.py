# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from chcemvediet.apps.inforequests.models import Action

from . import AppealPaperStep, AppealFinalStep, AppealWizard


class RefusalNoReasonAppealPaperStep(AppealPaperStep):
    text_template = u'inforequests/appeals/texts/refusal-no-reason-paper-text.html'
    content_template = u'inforequests/appeals/papers/refusal-no-reason.html'

class RefusalNoReasonAppealWizard(AppealWizard):
    u"""
    Appeal wizard for branches that end with a refusal action with no reason specified.
    """

    step_classes = OrderedDict([
            (u'paper', RefusalNoReasonAppealPaperStep),
            (u'final', AppealFinalStep),
            ])

    @classmethod
    def applicable(cls, branch):
        if branch.last_action.type != Action.TYPES.REFUSAL:
            return False
        if branch.last_action.refusal_reason: # With a reason
            return False
        return True
