# vim: expandtab
# -*- coding: utf-8 -*-
from django.utils.html import format_html, format_html_join

def format_tag(tag, attrs={}, content=u''):
    u"""
    Helper to render html tag with proper escaping.

    Examples:
        format_tag('a', dict(href='mailto:smith@example.com'), 'John Smith <smith@example.com>')
         -> '<a href="mailto:smith@example.com">John Smith &lt;smith@example.com&gt;</a>'

        format_tag('span', dict(title='John Smith <smith@example.com>'), 'John Smith')
         -> '<span title="John Smith &lt;smith@example.com&gt;">John Smith</span>'

        format_tag('p', {'class': 'moo'}, format_tag('span', {'class': 'foo'}, '"goo"'))
         -> '<p class="moo"><span class="foo">&quot;goo&quot;</span></p>'
    """
    return format_html(u'<{0} {1}>{2}</{0}>', tag, format_html_join(u' ', u'{0}="{1}"', attrs.iteritems()), content)
