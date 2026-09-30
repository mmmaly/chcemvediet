import re

from lxml import etree
from django.test import TestCase

from chcemvediet.apps.anonymization.anonymization import anonymize_markup


class AnonymizeMarkupTest(TestCase):
    u"""
    Tests ``anonymize_markup()`` function.
    """

    def test_html_str_is_anonymized_to_str(self):
        prog = re.compile(u'(\\bNovák\\b)', re.IGNORECASE | re.UNICODE)
        res = anonymize_markup(prog, u'<p>Ján <b>Novák</b>, Novák</p>', etree.HTMLParser())
        self.assertIsInstance(res, str)
        self.assertIn(u'<p>Ján <b>xxxxx</b>, xxxxx</p>', res)

    def test_xml_bytes_are_anonymized_to_bytes(self):
        prog = re.compile(u'(\\bNovák\\b)', re.IGNORECASE | re.UNICODE)
        content = u'<?xml version="1.0" encoding="UTF-8"?><a><b>Ján Novák</b></a>'.encode(u'utf-8')
        res = anonymize_markup(prog, content, etree.XMLParser())
        self.assertIsInstance(res, bytes)
        self.assertEqual(etree.fromstring(res).findtext(u'b'), u'Ján xxxxx')

    def test_empty_pattern_returns_content_unchanged(self):
        prog = re.compile(u'')
        self.assertEqual(anonymize_markup(prog, u'<p>x</p>', etree.HTMLParser()), u'<p>x</p>')


class HideUniqueEmailTest(TestCase):
    u"""
    Tests ``hide_unique_email()`` template helper.
    """

    class Inforequest(object):
        applicant = u'applicant'
        unique_email = u'abcd@mail.example.com'

    def _hide(self, user, content):
        from chcemvediet.apps.anonymization.templatetags.chcemvediet.anonymization import (
                hide_unique_email)
        return hide_unique_email(self.Inforequest(), user, content)

    def test_address_is_hidden_from_others(self):
        res = self._hide(u'other', u'Reply to ABCD@mail.example.com <mailto:abcd@mail.example.com>.')
        self.assertEqual(res, u'Reply to xxxxx <mailto:xxxxx>.')

    def test_address_is_hidden_in_attachment_name(self):
        res = self._hide(u'other', u'list_Abcd@mail.example.com.pdf')
        self.assertEqual(res, u'list_xxxxx.pdf')

    def test_address_is_shown_to_applicant(self):
        res = self._hide(u'applicant', u'Reply to abcd@mail.example.com.')
        self.assertEqual(res, u'Reply to abcd@mail.example.com.')

    def test_other_addresses_are_kept(self):
        content = u'xabcd@mail.example.com, abcd@mail.example.community, abcdx@mail.example.com'
        self.assertEqual(self._hide(u'other', content), content)
