# vim: expandtab
# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _

from .common import AppealSectionStep, AppealLegalDateStep


class RefusalNoReasonAppeal(AppealSectionStep):
    u"""
    Appeal wizard for branches that end with a refusal action with no reason specified.
    """
    label = _(u'inforequests:appeal:refusal_no_reason:RefusalNoReasonAppeal:label')
    text_template = u'inforequests/appeal/texts/refusal_no_reason.html'
    section_template = u'inforequests/appeal/papers/refusal_no_reason.html'
    post_step_class = AppealLegalDateStep
