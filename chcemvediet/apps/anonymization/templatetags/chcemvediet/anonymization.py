# -*- coding: utf-8 -*-
import re
import traceback

from lxml import etree
from django.utils.translation import gettext_lazy as _

from poleno.utils.template import Library
from poleno.utils.http import get_request
from poleno.cron import cron_logger
from chcemvediet.apps.anonymization.anonymization import (generate_user_pattern, anonymize_string,
                                                          anonymize_markup, ANONYMIZATION_STRING)


register = Library()

def hide_unique_email(inforequest, user, content):
    u"""
    Hides the inforequest unique e-mail address from everybody but the applicant, whether the
    applicant wants the inforequest anonymized or not. Published addresses attract spam.
    """
    if user == inforequest.applicant or not inforequest.unique_email or not content:
        return content
    # Do not touch longer addresses that only contain this one. An underscore may precede the
    # address, e.g. in attachment names like "list_abcd@mail.chcemvediet.sk.pdf".
    pattern = u'(?<![A-Za-z0-9.+-])' + re.escape(inforequest.unique_email) + u'(?![\\w-])'
    return re.sub(pattern, ANONYMIZATION_STRING, content, flags=re.IGNORECASE)

@register.simple_tag(takes_context=True)
def anonymize(context, inforequest, content, match_subwords=False):
    request = context[u'request']
    content = hide_unique_email(inforequest, request.user, content)
    if not inforequest.anonymized_for(request.user):
        return content
    prog = generate_user_pattern(inforequest, match_subwords)
    return anonymize_string(prog, content)

@register.simple_tag(takes_context=True)
def anonymize_html(context, inforequest, html_content):
    request = context[u'request']
    # Replaced in the raw markup to cover attributes (``mailto:`` links) as well.
    html_content = hide_unique_email(inforequest, request.user, html_content)
    if not inforequest.anonymized_for(request.user):
        return html_content
    prog = generate_user_pattern(inforequest)
    try:
        return anonymize_markup(prog, html_content, etree.HTMLParser())
    except Exception as e:
        trace = traceback.format_exc()
        cron_logger.error(u'anonymize_html has failed.\n An '
                          u'unexpected error occured: {}\n{}'.format(e.__class__.__name__, trace))
        error = _(u'annonymization:anonymization:anonymize_html:error')
        return error

@register.filter
def anonymized(inforequest):
    return inforequest.anonymized_for(get_request().user)
