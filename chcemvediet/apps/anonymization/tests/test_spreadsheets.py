import re
import zipfile
from io import BytesIO
from unittest import mock

from lxml import etree
from django.test import TestCase

from chcemvediet.apps.anonymization import spreadsheets


CONTENT = u'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
    xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    xmlns:calcext="urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0"
    xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
    xmlns:xlink="http://www.w3.org/1999/xlink">
<office:body><office:spreadsheet>
<table:table table:name="Novák 2020">
 <table:table-row>
  <table:table-cell office:value-type="string"><text:p>Ján <text:span>Nov</text:span>ák, Bratislava</text:p></table:table-cell>
  <table:table-cell office:value-type="float" office:value="81101" calcext:value-type="float"><text:p>81101</text:p></table:table-cell>
  <table:table-cell office:value-type="float" office:value="12.5"><text:p>12,5</text:p></table:table-cell>
  <table:table-cell table:formula="of:=CONCATENATE(&quot;pan Novák&quot;;A1)" office:value-type="string" office:string-value="pan Novák"><text:p>pan Novák</text:p></table:table-cell>
  <table:table-cell office:value-type="string"><text:p>Novakova ulica</text:p></table:table-cell>
 </table:table-row>
</table:table>
<table:table table:name="Skrytý" table:display="false">
 <table:table-row><table:table-cell office:value-type="string"><text:p>tajný NOVÁK</text:p></table:table-cell></table:table-row>
</table:table>
</office:spreadsheet></office:body></office:document-content>'''

MANIFEST = u'''<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">
 <manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.spreadsheet"/>
 <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="Thumbnails/thumbnail.png" manifest:media-type="image/png"/>
</manifest:manifest>'''

META = u'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    xmlns:dc="http://purl.org/dc/elements/1.1/"><office:meta><dc:creator>Peter Úradník</dc:creator>
</office:meta></office:document-meta>'''

NS = {u'table': spreadsheets.NS_TABLE, u'office': spreadsheets.NS_OFFICE, u'text': spreadsheets.NS_TEXT}


def make_ods(extra=()):
    output = BytesIO()
    with zipfile.ZipFile(output, u'w') as z:
        z.writestr(u'mimetype', u'application/vnd.oasis.opendocument.spreadsheet')
        z.writestr(u'content.xml', CONTENT)
        z.writestr(u'meta.xml', META)
        z.writestr(u'META-INF/manifest.xml', MANIFEST)
        z.writestr(u'Thumbnails/thumbnail.png', b'PNG')
        for name in extra:
            z.writestr(name, b'x')
    return output.getvalue()

def pattern(*words):
    return re.compile(u'|'.join(u'(\\b{}\\b)'.format(w) for w in words), re.IGNORECASE | re.UNICODE)


class SpreadsheetsTest(TestCase):
    u"""
    Tests ``spreadsheets``: inspection, text extraction and anonymization of ODS files.
    """

    def test_inspect_ods(self):
        self.assertEqual(spreadsheets.inspect_ods(make_ods()), set())
        self.assertEqual(spreadsheets.inspect_ods(make_ods([u'Pictures/1.png'])), {u'images'})
        self.assertEqual(spreadsheets.inspect_ods(make_ods([u'Basic/Standard/Module1.xml'])), {u'macros'})
        self.assertEqual(spreadsheets.inspect_ods(make_ods([u'Basic/Standard/script-lb.xml'])), set())
        self.assertEqual(spreadsheets.inspect_ods(make_ods([u'Object 1/content.xml'])), set())
        self.assertEqual(spreadsheets.inspect_ods(make_ods([u'Object 2'])), {u'embedded objects'})

    def test_chart_picture_is_not_an_image(self):
        chart = (b'<draw:frame><draw:object xlink:href="./Object 1"/>'
                 b'<draw:image xlink:href="./ObjectReplacements/Object 1"/></draw:frame>')
        picture = b'<draw:frame><draw:image xlink:href="Pictures/1.png"/></draw:frame>'
        for extra, expected in [(chart, set()), (picture, {u'images'})]:
            output = BytesIO()
            with zipfile.ZipFile(output, u'w') as z:
                z.writestr(u'content.xml', CONTENT.encode(u'utf-8').replace(b'</office:spreadsheet>', extra + b'</office:spreadsheet>'))
            self.assertEqual(spreadsheets.inspect_ods(output.getvalue()), expected)

    def test_extracted_text_joins_spans_and_includes_hidden_sheets_names_and_metadata(self):
        text = spreadsheets.extract_ods_text(make_ods())
        self.assertIn(u'Ján Novák, Bratislava', text)
        self.assertIn(u'Novák 2020', text)
        self.assertIn(u'tajný NOVÁK', text)
        self.assertIn(u'Peter Úradník', text)
        self.assertIn(u'of:=CONCATENATE("pan Novák";A1)', text)

    def test_anonymize_ods(self):
        ods = spreadsheets.anonymize_ods(pattern(u'Novák', u'81101'), make_ods())
        with zipfile.ZipFile(BytesIO(ods)) as z:
            self.assertEqual(z.namelist()[0], u'mimetype')
            self.assertNotIn(u'Thumbnails/thumbnail.png', z.namelist())
            self.assertNotIn(b'Thumbnails', z.read(u'META-INF/manifest.xml'))
            root = etree.fromstring(z.read(u'content.xml'))
        text = spreadsheets.extract_ods_text(ods)
        self.assertNotIn(u'81101', text)
        self.assertEqual(re.findall(u'novák', text, re.IGNORECASE), [])
        cells = root.findall(u'.//table:table-cell', NS)
        value_type = u'{%s}value-type' % spreadsheets.NS_OFFICE
        value = u'{%s}value' % spreadsheets.NS_OFFICE
        # the postcode stops being a number
        self.assertEqual(cells[1].get(value_type), u'string')
        self.assertIsNone(cells[1].get(value))
        self.assertEqual(u''.join(cells[1].itertext()), u'xxxxx')
        # other numbers are kept
        self.assertEqual((cells[2].get(value_type), cells[2].get(value)), (u'float', u'12.5'))
        # the formula and its cached value are gone
        self.assertIsNone(cells[3].get(u'{%s}formula' % spreadsheets.NS_TABLE))
        self.assertEqual(u''.join(cells[3].itertext()), u'pan xxxxx')
        # sheet name, hidden sheet, other words
        self.assertEqual(root.find(u'.//table:table', NS).get(u'{%s}name' % spreadsheets.NS_TABLE), u'xxxxx 2020')
        self.assertEqual(u''.join(cells[5].itertext()), u'tajný xxxxx')
        self.assertEqual(u''.join(cells[4].itertext()), u'Novakova ulica')

    def test_word_split_into_spans_is_replaced(self):
        ods = spreadsheets.anonymize_ods(pattern(u'Novák'), make_ods())
        with zipfile.ZipFile(BytesIO(ods)) as z:
            root = etree.fromstring(z.read(u'content.xml'))
        self.assertEqual(u''.join(root.find(u'.//table:table-cell', NS).itertext()), u'Ján xxxxx, Bratislava')
        spreadsheets.assert_not_identifiable(pattern(u'Novák'), spreadsheets.extract_ods_text(ods))

    def test_final_check_refuses_identifying_data(self):
        with self.assertRaises(spreadsheets.StillIdentifiable):
            spreadsheets.assert_not_identifiable(pattern(u'Novák'), spreadsheets.extract_ods_text(make_ods()))

    def test_identifying_strings(self):
        profile = mock.Mock(custom_anonymized_strings=None, street=u'Hlavná 5', city=u'Bratislava', zip=u'81101')
        user = mock.Mock(first_name=u'Ján', last_name=u'Novák', profile=profile)
        inforequest = mock.Mock(applicant=user, applicant_name=u'Ján Novák', applicant_street=u'Hlavná 5',
                applicant_city=u'Bratislava', applicant_zip=u'81101', unique_email=u'abcd@mail.example.com')
        prog = spreadsheets.generate_identifying_pattern(inforequest)
        for text in [u'pan NOVAK', u'Hlavna 5', u'na abcd@mail.example.com']:
            self.assertTrue(spreadsheets.found(prog, text), text)
        for text in [u'Ján z Bratislavy', u'Bratislava 81101', u'Hlavná stanica']:
            self.assertFalse(spreadsheets.found(prog, text), text)
        profile.custom_anonymized_strings = [u'Kocian', u'0905 123 456']
        prog = spreadsheets.generate_identifying_pattern(inforequest)
        self.assertTrue(spreadsheets.found(prog, u'tel. 0905123456'))
        self.assertFalse(spreadsheets.found(prog, u'pan Novák'))

    def test_is_spreadsheet(self):
        for name, content_type, expected in [
                (u'a.xlsx', u'application/octet-stream', True),
                (u'a.XLS', u'application/CDFV2', True),
                (u'a.bin', u'application/vnd.ms-excel', True),
                (u'a.doc', u'application/CDFV2', False),
                (u'a.pdf', u'application/pdf', False),
                ]:
            attachment = mock.Mock(content_type=content_type)
            attachment.name = name
            self.assertEqual(spreadsheets.is_spreadsheet(attachment), expected)
