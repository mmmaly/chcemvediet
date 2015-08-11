# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from poleno.utils.forms import EditableSpan
from chcemvediet.apps.wizards.forms import PaperCharField
from chcemvediet.apps.inforequests.models import Action

from . import AppealSectionStep, AppealPaperStep, AppealFinalStep, AppealWizard


class AdvancementAppealReasonStep(AppealSectionStep):
    text_template = u'inforequests/appeals/texts/advancement.html'
    section_template = u'inforequests/appeals/papers/advancement.html'

    reason = PaperCharField(widget=EditableSpan())

    def paper_fields(self, step):
        step.fields[u'reason'] = PaperCharField(widget=EditableSpan())

class AdvancementAppealWizard(AppealWizard):
    u"""
    Appeal wizard for branches that end with an advancement action.
    """
    step_classes = OrderedDict([
            (u'reason', AdvancementAppealReasonStep),
            (u'paper', AppealPaperStep),
            (u'final', AppealFinalStep),
            ])

    @classmethod
    def applicable(cls, branch):
        if branch.last_action.type != Action.TYPES.ADVANCEMENT:
            return False
        return True
