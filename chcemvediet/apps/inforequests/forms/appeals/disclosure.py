# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from poleno.utils.forms import EditableSpan
from chcemvediet.apps.wizards.forms import PaperCharField
from chcemvediet.apps.inforequests.models import Action

from . import AppealSectionStep, AppealPaperStep, AppealFinalStep, AppealWizard


class DisclosureAppealReasonStep(AppealSectionStep):
    text_template = u'inforequests/appeals/texts/disclosure-reason.html'
    section_template = u'inforequests/appeals/papers/disclosure-reason.html'

    reason = PaperCharField(widget=EditableSpan())

    def paper_fields(self, step):
        step.fields[u'reason'] = PaperCharField(widget=EditableSpan())

class DisclosureAppealWizard(AppealWizard):
    u"""
    Appeal wizard for branches that end with a non-full disclosure action.
    """
    step_classes = OrderedDict([
            (u'reason', DisclosureAppealReasonStep),
            (u'paper', AppealPaperStep),
            (u'final', AppealFinalStep),
            ])

    @classmethod
    def applicable(cls, branch):
        if branch.last_action.type != Action.TYPES.DISCLOSURE:
            return False
        if branch.last_action.disclosure_level == Action.DISCLOSURE_LEVELS.FULL:
            return False
        return True
