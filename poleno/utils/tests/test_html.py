# vim: expandtab
# -*- coding: utf-8 -*-
from django.test import TestCase

from poleno.utils.html import merge_html_attrs

class MergeHtmlAttrsTest(TestCase):
    u"""
    Tests ``merge_html_attrs()`` functions.
    """

    def test_with_no_args(self):
        res = merge_html_attrs()
        self.assertEqual(res, {})

    def test_with_multiple_args(self):
        res = merge_html_attrs({u'title': u'Title', u'alt': u'Alt'}, dict(name=u'Name', id=u'id47'), href=u'#')
        self.assertEqual(res, {u'title': u'Title', u'alt': u'Alt', u'name': u'Name', u'id': u'id47', u'href': u'#'})

    def test_with_empty_args(self):
        res = merge_html_attrs({}, None, title=u'Some Title')
        self.assertEqual(res, {u'title': u'Some Title'})

    def test_duplicate_attrs_raises_error(self):
        with self.assertRaisesMessage(ValueError, u'Duplicate attribute "alt".'):
            merge_html_attrs(dict(alt=u'first'), alt=u'duplicate')

    def test_duplicate_class_attrs_are_merged(self):
        res = merge_html_attrs({u'class': u'first second'}, class_=u'second third')
        self.assertItemsEqual(res[u'class'].split(), u'first second third'.split())

    def test_duplicate_style_attrs_are_concatenated(self):
        res = merge_html_attrs({u'style': u'color: red;'}, style=u'border: 1px;')
        self.assertEqual(res[u'style'], u'color: red; border: 1px;')
