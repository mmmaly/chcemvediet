# vim: expandtab
# -*- coding: utf-8 -*-
from poleno.utils.forms import EditableSpan
from django.utils.translation import gettext_lazy as _
from chcemvediet.apps.wizards.forms import PaperCharField

from .common import AppealSectionStep, AppealLegalDateStep


class FallbackAppeal(AppealSectionStep):
    u"""
    Fallback appeal wizard for all cases not covered with a more specific wizard.
    """
    label = _(u'inforequests:appeal:fallback:FallbackAppeal:label')
    text_template = u'inforequests/appeal/texts/fallback.html'
    section_template = u'inforequests/appeal/papers/fallback.html'
    global_fields = [u'reason']
    post_step_class = AppealLegalDateStep

    def add_fields(self):
        super(FallbackAppeal, self).add_fields()
        self.fields[u'reason'] = PaperCharField(widget=EditableSpan())
