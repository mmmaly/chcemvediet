# vim: expandtab
# -*- coding: utf-8 -*-
from django.utils.html import format_html

from poleno.utils.template import Library

register = Library()

@register.simple_tag
def obligee_declension(obligee, declension, default=u''):
    if not obligee:
        return default
    if declension == u'nominative':
        return obligee.name
    return format_html(u'{0}<span style="color: red;">({1})</span>', obligee.name, declension)

@register.simple_tag
def obligee_gender(obligee, masculine, feminine, neuter, plural):
    if not obligee:
        return feminine
    return format_html(u'{0}<span style="color: red;">/{1}/{2}/{3}</span>', masculine, feminine, neuter, plural)
