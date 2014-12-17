# vim: expandtab
# -*- coding: utf-8 -*-
from django.utils.encoding import force_text
from django.test import TestCase

from poleno.utils.html import format_tag

class FormatTagTest(TestCase):
    u"""
    Tests ``format_tag()`` function.
    """

    def test_text_content_is_escaped(self):
        res = format_tag('a', dict(href=u'mailto:smith@example.com'), u'John Smith <smith@example.com>')
        self.assertEqual(u'%s' % res, u'<a href="mailto:smith@example.com">John Smith &lt;smith@example.com&gt;</a>')

    def test_attributes_are_escaped(self):
        res = format_tag('span', dict(title=u'John Smith <smith@example.com>'), u'John Smith')
        self.assertEqual(u'%s' % res, u'<span title="John Smith &lt;smith@example.com&gt;">John Smith</span>')

    def test_html_content_is_not_escaped(self):
        res = format_tag(u'p', {u'class': u'moo'}, format_tag(u'span', {u'class': u'foo'}, u'"goo"'))
        self.assertEqual(u'%s' % res, u'<p class="moo"><span class="foo">&quot;goo&quot;</span></p>')
