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
