# vim: expandtab
# -*- coding: utf-8 -*-
from poleno.utils.forms import EditableSpan
from django.utils.translation import gettext_lazy as _
from chcemvediet.apps.wizards.forms import PaperCharField

from .common import AppealSectionStep, AppealLegalDateStep


class DisclosureAppeal(AppealSectionStep):
    u"""
    Appeal wizard for branches that end with a non-full disclosure action.
    """
    label = _(u'inforequests:appeal:disclosure:DisclosureAppeal:label')
    text_template = u'inforequests/appeal/texts/disclosure.html'
    section_template = u'inforequests/appeal/papers/disclosure.html'
    global_fields = [u'reason']
    post_step_class = AppealLegalDateStep

    def add_fields(self):
        super(DisclosureAppeal, self).add_fields()
        self.fields[u'reason'] = PaperCharField(widget=EditableSpan())
