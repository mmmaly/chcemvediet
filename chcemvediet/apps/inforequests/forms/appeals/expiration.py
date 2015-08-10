# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from chcemvediet.apps.inforequests.models import Action

from . import AppealPaperStep, AppealFinalStep, AppealWizard


class ExpirationAppealPaperStep(AppealPaperStep):
    text_template = u'inforequests/appeals/texts/expiration-paper.html'
    content_template = u'inforequests/appeals/papers/expiration.html'

class ExpirationAppealWizard(AppealWizard):
    u"""
    Appeal wizard for branches that end with an action with an expired obligee deadline, or an
    expiration action.
    """

    step_classes = OrderedDict([
            (u'paper', ExpirationAppealPaperStep),
            (u'final', AppealFinalStep),
            ])

    @classmethod
    def applicable(cls, branch):
        if branch.last_action.type == Action.TYPES.EXPIRATION:
            return True
        if not branch.last_action.has_obligee_deadline:
            return False
        if not branch.last_action.deadline_missed:
            return False
        return True
