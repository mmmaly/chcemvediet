import os
import tempfile
import zipfile

from lxml import etree
from django.test import TestCase

from chcemvediet.apps.anonymization import tesseract_odt


HOCR = u'''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body>
<div class='ocr_page' id='page_1' title='image "page-1.png"; bbox 0 0 2480 3508; ppageno 0'>
<div class='ocr_carea' id='block_1_1' title="bbox 100 100 2300 260">
<p class='ocr_par' id='par_1_1' lang='slk' title="bbox 100 100 2300 260">
<span class='ocr_line' id='line_1_1' title="bbox 100 100 2300 160; baseline 0 -10; x_size 50; x_descenders 12; x_ascenders 12">
<span class='ocrx_word' id='word_1_1' title='bbox 100 100 300 160; x_wconf 96'>Váš</span>
<span class='ocrx_word' id='word_1_2' title='bbox 320 100 500 160; x_wconf 96'>list</span>
<span class='ocrx_word' id='word_1_3' title='bbox 1500 100 1700 160; x_wconf 96'>Dátum</span>
</span>
<span class='ocr_line' id='line_1_2' title="bbox 100 200 2300 260; baseline 0 -10; x_size 50; x_descenders 12; x_ascenders 12">
<span class='ocrx_word' id='word_1_4' title='bbox 100 200 300 260; x_wconf 40'>.</span>
<span class='ocrx_word' id='word_1_5' title='bbox 1500 200 1900 260; x_wconf 96'>1.&amp;2.</span>
</span>
</p></div></div></body></html>'''


class TesseractOdtTest(TestCase):
    u"""
    Tests ``tesseract_odt`` hOCR parsing and ODT writing.
    """

    def _parse(self):
        with tempfile.NamedTemporaryFile(u'w', suffix=u'.hocr', delete=False, encoding=u'utf-8') as f:
            f.write(HOCR)
        try:
            return tesseract_odt.parse_hocr(f.name)
        finally:
            os.remove(f.name)

    def test_lines_are_split_into_column_segments_and_noise_dropped(self):
        size, blocks = self._parse()
        self.assertEqual(size, (2480, 3508))
        self.assertEqual([b[u'lines'] for b in blocks],
                         [[u'Váš list'], [u'Dátum'], [u'1.&2.']])
        self.assertEqual(blocks[0][u'bbox'], [100, 100, 500, 160])
        self.assertEqual(blocks[1][u'bbox'], [1500, 100, 1700, 160])
        # font size in pixels from the x-height: (50 - 12 - 12) / 0.52
        self.assertAlmostEqual(blocks[0][u'size'], 50.0, places=1)

    def test_overlaps(self):
        a = {u'bbox': [0, 0, 100, 100]}
        self.assertTrue(tesseract_odt.overlaps(a, {u'bbox': [50, 50, 150, 150]}))
        self.assertFalse(tesseract_odt.overlaps(a, {u'bbox': [95, 95, 300, 300]}))
        self.assertFalse(tesseract_odt.overlaps(a, {u'bbox': [100, 0, 200, 100]}))

    def test_odt_has_positioned_spans_for_anonymization(self):
        size, blocks = self._parse()
        with tempfile.NamedTemporaryFile(suffix=u'.odt', delete=False) as f:
            path = f.name
        try:
            tesseract_odt.write_odt(path, [(size, blocks), (size, blocks[:1])], 300)
            with zipfile.ZipFile(path) as z:
                self.assertEqual(z.namelist()[0], u'mimetype')
                self.assertEqual(z.read(u'mimetype'), b'application/vnd.oasis.opendocument.text')
                content = z.read(u'content.xml')
                styles = z.read(u'styles.xml')
        finally:
            os.remove(path)
        ns = {u'text': u'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
              u'draw': u'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
              u'svg': u'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0'}
        root = etree.fromstring(content)
        spans = root.findall(u'.//text:span', ns)
        self.assertEqual([s.text for s in spans], [u'Váš list', u'Dátum', u'1.&2.', u'Váš list'])
        frames = root.findall(u'.//draw:frame', ns)
        self.assertEqual(frames[1].get(u'{%s}x' % ns[u'svg']), u'12.700cm')  # 1500 px at 300 dpi
        self.assertEqual(len(root.findall(u'.//text:p[@text:style-name="PageNext"]', ns)), 1)
        self.assertIn(b'fo:page-width="20.997cm"', styles)
