# vim: expandtab
# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _

from .common import AppealSectionStep, AppealLegalDateStep


class ExpirationAppeal(AppealSectionStep):
    u"""
    Appeal wizard for branches that end with an action with an expired obligee deadline, or an
    expiration action.
    """
    label = _(u'inforequests:appeal:expiration:ExpirationAppeal:label')
    text_template = u'inforequests/appeal/texts/expiration.html'
    section_template = u'inforequests/appeal/papers/expiration.html'
    post_step_class = AppealLegalDateStep
