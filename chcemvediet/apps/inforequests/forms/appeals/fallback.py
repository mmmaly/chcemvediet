# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from poleno.utils.forms import EditableSpan
from chcemvediet.apps.wizards.forms import PaperCharField

from . import AppealPaperStep, AppealFinalStep, AppealWizard


class FallbackAppealPaperStep(AppealPaperStep):
    text_template = u'inforequests/appeals/texts/fallback.html'
    content_template = u'inforequests/appeals/papers/fallback.html'

    reason = PaperCharField(widget=EditableSpan())

class FallbackAppealWizard(AppealWizard):
    u"""
    Fallback appeal wizard for all cases not covered with a more specific wizard.
    """
    step_classes = OrderedDict([
            (u'paper', FallbackAppealPaperStep),
            (u'final', AppealFinalStep),
            ])

    @classmethod
    def applicable(cls, branch):
        return True
