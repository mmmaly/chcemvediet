# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from chcemvediet.apps.inforequests.models import Action

from . import ClarificationResponseWizard, ClarificationResponseStep

class SmailClarificationResponseContentStep(ClarificationResponseStep):
    pass

class SmailClarificationResponseWizard(ClarificationResponseWizard):
    u"""
    Clarification response wizard to clarification requests received by s-mail.
    """
    step_classes = OrderedDict([
            (u'content', SmailClarificationResponseContentStep),
            ])

    @classmethod
    def applicable(cls, branch):
        if branch.last_action.type != Action.TYPES.CLARIFICATION_REQUEST:
            return False
        if branch.last_action.is_by_email:
            return False
        return True
