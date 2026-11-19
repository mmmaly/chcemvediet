import io
import re
import subprocess
import zipfile

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


class GenerateAttachmentPatternTest(TestCase):
    u"""
    Tests ``generate_attachment_pattern()``: user strings plus the inforequest e-mail address.
    """

    def _pattern(self, words, unique_email):
        from unittest import mock
        from chcemvediet.apps.anonymization import anonymization
        inforequest = mock.Mock(unique_email=unique_email)
        user_pattern = re.compile(u'|'.join(u'(\\b{}\\b)'.format(w) for w in words), re.IGNORECASE)
        with mock.patch.object(anonymization, u'generate_user_pattern', return_value=user_pattern):
            return anonymization.generate_attachment_pattern(inforequest)

    def test_address_and_user_strings_are_anonymized(self):
        prog = self._pattern([u'Novák'], u'abcd@mail.example.com')
        res = prog.sub(u'xxxxx', u'Ján Novák <Abcd@mail.example.com>, other@mail.example.com')
        self.assertEqual(res, u'Ján xxxxx <xxxxx>, other@mail.example.com')

    def test_address_is_anonymized_without_user_strings(self):
        prog = self._pattern([], u'abcd@mail.example.com')
        self.assertEqual(prog.sub(u'xxxxx', u'Odpoveď na abcd@mail.example.com.'), u'Odpoveď na xxxxx.')

    def test_empty_pattern_without_address_and_strings(self):
        self.assertEqual(self._pattern([], u'').pattern, u'')


class AnonymizeFilenameTest(TestCase):
    u"""
    Tests ``anonymize_filename()``: names of public copies of attachments.
    """

    def _anonymize(self, filename, unique_email=u'abcd@mail.example.com'):
        from unittest import mock
        from chcemvediet.apps.anonymization import anonymization
        inforequest = mock.Mock(unique_email=unique_email)
        user_pattern = re.compile(u'(nov(?:a|á|ä)k)', re.IGNORECASE)
        with mock.patch.object(anonymization, u'generate_user_pattern', return_value=user_pattern) as pattern:
            res = anonymization.anonymize_filename(inforequest, filename)
        pattern.assert_called_once_with(inforequest, match_subwords=True)
        return res

    def test_surname_and_address_are_replaced(self):
        self.assertEqual(self._anonymize(u'odpoved_Novak_Abcd@mail.example.com.pdf'), u'odpoved_xxxxx_xxxxx.pdf')

    def test_other_names_are_kept(self):
        self.assertEqual(self._anonymize(u'rozhodnutie 12-2026.pdf'), u'rozhodnutie 12-2026.pdf')
        self.assertEqual(self._anonymize(u'Novák.xlsx', unique_email=u''), u'xxxxx.xlsx')


class OriginalPdfIsPublishableTest(TestCase):
    u"""
    Tests ``original_pdf_is_publishable()``: a PDF without identifying data is published untouched.
    """

    ODT_NS = u'urn:oasis:names:tc:opendocument:xmlns:text:1.0'

    def _odt(self, *spans):
        content = u'<?xml version="1.0" encoding="UTF-8"?><r xmlns:text="{}"><text:p>{}</text:p></r>'.format(
                self.ODT_NS, u''.join(u'<text:span>{}</text:span>'.format(s) for s in spans))
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, u'w') as z:
            z.writestr(u'mimetype', u'application/vnd.oasis.opendocument.text')
            z.writestr(u'content.xml', content.encode(u'utf-8'))
        return buffer.getvalue()

    def _publishable(self, odt, pdf_text=u'', content_type=u'application/pdf', pdf_error=None):
        from unittest import mock
        from chcemvediet.apps.anonymization import anonymization, spreadsheets
        attachment = mock.Mock(content_type=content_type)
        pattern = re.compile(u'(\\bNov(?:a|á|ä)k\\b)', re.IGNORECASE)
        with mock.patch.object(spreadsheets, u'generate_identifying_pattern', return_value=pattern), \
                mock.patch.object(anonymization, u'pdf_text', return_value=pdf_text,
                        side_effect=pdf_error):
            return anonymization.original_pdf_is_publishable(attachment, odt)

    def test_pdf_without_identifying_data_is_publishable(self):
        self.assertTrue(self._publishable(self._odt(u'Projekt organizácie dopravy', u'Bratislava'),
                pdf_text=u'Author: Úrad'))

    def test_identifying_data_in_recognized_text(self):
        self.assertFalse(self._publishable(self._odt(u'Vážený pán Novák')))

    def test_word_split_into_spans_is_found(self):
        self.assertFalse(self._publishable(self._odt(u'Vážený pán No', u'vák')))

    def test_identifying_data_in_text_layer_or_metadata(self):
        self.assertFalse(self._publishable(self._odt(u'Rozhodnutie'), pdf_text=u'Author: Ján Novák'))

    def test_other_content_types_are_not_publishable(self):
        self.assertFalse(self._publishable(self._odt(u'Rozhodnutie'),
                content_type=u'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))

    def test_pdf_that_can_not_be_read_is_not_publishable(self):
        self.assertFalse(self._publishable(self._odt(u'Rozhodnutie'),
                pdf_error=subprocess.CalledProcessError(1, u'pdftotext')))

    def test_pdf_text_reads_text_layer_and_metadata(self):
        import os
        from django.conf import settings
        from chcemvediet.apps.anonymization.anonymization import pdf_text
        text = pdf_text(os.path.join(settings.PROJECT_PATH,
                u'chcemvediet/apps/anonymization/mocks/normalized.pdf'))
        self.assertIn(u'Pages:', text)
