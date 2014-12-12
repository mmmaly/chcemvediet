# vim: expandtab
# -*- coding: utf-8 -*-
from django.utils.html import format_html, format_html_join

# FIXME: doc + tests
def format_tag(tag, attrs={}, content=u''):
    return format_html(u'<{0} {1}>{2}</{0}>', tag, format_html_join(u' ', u'{0}="{1}"', attrs.iteritems()), content)
