# vim: expandtab
# -*- coding: utf-8 -*-
u"""
OCR a PDF with Tesseract and write the result as an ODT document that mimics ABBYY FineReader's
"ExactCopy" output: every recognized paragraph becomes a text box placed at its position on a
page of the original size, so the anonymization step (which edits ``text:span`` elements) and the
finalization step (LibreOffice ODT -> PDF) keep working unchanged.

Usage as a script:  tesseract_odt.py [--lang slk] [--dpi 300] input.pdf output.odt
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from xml.etree import ElementTree
from xml.sax.saxutils import escape

try:
    from .ocr_corrections import correct_line
except ImportError: # run as a script
    from ocr_corrections import correct_line

DEFAULT_LANG = u'slk'
DEFAULT_DPI = 300
FONT = u'Liberation Sans'
# Tesseract 5 thresholding: 0 = legacy Otsu, 1 = adaptive Otsu, 2 = Sauvola. The default (0) reads
# normal text best but drops light grey text (footers); a second pass with method 1 finds it. Only
# blocks that do not overlap anything found by the first pass are taken from the second pass.
THRESHOLDING_METHODS = (u'0', u'1')
XHTML = u'{http://www.w3.org/1999/xhtml}'


def run(cmd, timeout=None):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
            timeout=timeout)

def hocr_title(element):
    u"""Parses the ``title`` attribute of an hOCR element into a dict, e.g. ``bbox`` -> [x0, y0, x1, y1]."""
    res = {}
    for part in (element.get(u'title') or u'').split(u';'):
        fields = part.split()
        if fields:
            res[fields[0]] = fields[1:]
    return res

def parse_hocr(path):
    u"""
    Returns page size in pixels and a list of text blocks. Tesseract puts side-by-side columns
    (header tables, address blocks) into one line, so every line is split into segments wherever
    the gap between two words is wider than about one character height; each segment becomes its
    own block. Every block holds a single line: LibreOffice grows single-line text boxes to fit
    their text, but wraps multi-line ones at their given width. A block is a dict with ``bbox`` in
    pixels, ``size`` (font size in pixels) and ``lines`` (list with one string).
    """
    root = ElementTree.parse(path).getroot()
    page = root.find(u'.//%sdiv[@class="ocr_page"]' % XHTML)
    bbox = [int(v) for v in hocr_title(page)[u'bbox']]
    blocks = []
    for par in page.iter(u'%sp' % XHTML):
        if par.get(u'class') != u'ocr_par':
            continue
        for line in par.iter(u'%sspan' % XHTML):
            if line.get(u'class') not in (u'ocr_line', u'ocr_header', u'ocr_textfloat', u'ocr_caption'):
                continue
            title = hocr_title(line)
            size = float(title[u'x_size'][0]) if u'x_size' in title else 40.0
            # Font size in pixels: x-height / 0.52 (typical sans-serif x-height ratio); x_size
            # alone (ascender to descender) overestimates it by 10-20 %.
            try:
                xheight = size - float(title[u'x_ascenders'][0]) - float(title[u'x_descenders'][0])
                em = xheight / 0.52 if xheight > 0 else size * 0.85
            except (KeyError, ValueError, IndexError):
                em = size * 0.85
            words = []
            for w in line.iter(u'%sspan' % XHTML):
                if w.get(u'class') != u'ocrx_word':
                    continue
                text = re.sub(r'\s+', u' ', u''.join(w.itertext())).strip()
                if text:
                    wtitle = hocr_title(w)
                    conf = float(wtitle[u'x_wconf'][0]) if u'x_wconf' in wtitle else 0.0
                    words.append(([int(v) for v in wtitle[u'bbox']], text, conf))
            if not words:
                continue
            segments = [[words[0]]]
            for word in words[1:]:
                if word[0][0] - segments[-1][-1][0][2] > 1.2 * size:
                    segments.append([word])
                else:
                    segments[-1].append(word)
            for segment in segments:
                sx0 = min(b[0] for b, _, _ in segment)
                sy0 = min(b[1] for b, _, _ in segment)
                sx1 = max(b[2] for b, _, _ in segment)
                sy1 = max(b[3] for b, _, _ in segment)
                blocks.append({u'bbox': [sx0, sy0, sx1, sy1], u'sizes': [em],
                               u'lines': [correct_line(u' '.join(t for _, t, _ in segment))],
                               u'confidence': sum(c for _, _, c in segment) / len(segment)})
    # Drop noise: blocks without a single letter or digit (specks read as punctuation).
    blocks = [b for b in blocks if re.search(r'\w', u' '.join(b[u'lines']))]
    for block in blocks:
        sizes = sorted(block.pop(u'sizes'))
        block[u'size'] = sizes[len(sizes) // 2]
    return (bbox[2], bbox[3]), blocks

def cm(pixels, dpi):
    return u'%.3fcm' % (pixels * 2.54 / dpi)

def build_content(pages, dpi):
    u"""``pages``: list of (size_px, blocks). Returns content.xml as a string."""
    styles = []
    body = []
    frame_id = 0
    for page_no, (size, blocks) in enumerate(pages):
        para_style = u'PageFirst' if page_no == 0 else u'PageNext'
        frames = []
        for par in blocks:
            frame_id += 1
            x0, y0, x1, y1 = par[u'bbox']
            font_pt = max(4.0, min(72.0, par[u'size'] * 72.0 / dpi))
            styles.append(
                u'<style:style style:name="T%d" style:family="text">'
                u'<style:text-properties style:font-name="%s" fo:font-size="%.1fpt"/>'
                u'</style:style>' % (frame_id, FONT, font_pt))
            text = u'<text:line-break/>'.join(escape(line) for line in par[u'lines'])
            frames.append(
                u'<draw:frame draw:style-name="fr" draw:name="Frame%d" text:anchor-type="paragraph" '
                u'svg:x="%s" svg:y="%s" draw:z-index="%d">'
                u'<draw:text-box fo:min-width="%s" fo:min-height="%s">'
                u'<text:p text:style-name="Standard"><text:span text:style-name="T%d">%s</text:span></text:p>'
                u'</draw:text-box></draw:frame>'
                % (frame_id, cm(x0, dpi), cm(y0, dpi), frame_id, cm(x1 - x0, dpi), cm(y1 - y0, dpi),
                   frame_id, text))
        body.append(u'<text:p text:style-name="%s">%s</text:p>' % (para_style, u''.join(frames)))
    return (
        u'<?xml version="1.0" encoding="UTF-8"?>'
        u'<office:document-content '
        u'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        u'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
        u'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
        u'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
        u'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
        u'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
        u'office:version="1.2">'
        u'<office:font-face-decls>'
        u'<style:font-face style:name="%s" svg:font-family="&apos;%s&apos;" style:font-family-generic="swiss"/>'
        u'</office:font-face-decls>'
        u'<office:automatic-styles>'
        u'<style:style style:name="PageFirst" style:family="paragraph" style:master-page-name="Standard">'
        u'<style:paragraph-properties fo:margin="0cm" fo:line-height="0.1pt"/></style:style>'
        u'<style:style style:name="PageNext" style:family="paragraph" style:master-page-name="Standard">'
        u'<style:paragraph-properties fo:margin="0cm" fo:line-height="0.1pt" fo:break-before="page"/></style:style>'
        u'<style:style style:name="fr" style:family="graphic" style:parent-style-name="Frame">'
        u'<style:graphic-properties fo:background-color="#ffffff" style:background-transparency="100%%" '
        u'fo:border="none" fo:padding="0cm" fo:margin="0cm" style:flow-with-text="false" '
        u'style:wrap="run-through" style:run-through="foreground" style:vertical-pos="from-top" '
        u'style:vertical-rel="page" style:horizontal-pos="from-left" style:horizontal-rel="page" '
        u'draw:auto-grow-width="true" draw:auto-grow-height="true"/>'
        u'</style:style>%s'
        u'</office:automatic-styles>'
        u'<office:body><office:text>%s</office:text></office:body>'
        u'</office:document-content>' % (FONT, FONT, u''.join(styles), u''.join(body)))

def build_styles(size, dpi):
    width, height = size
    return (
        u'<?xml version="1.0" encoding="UTF-8"?>'
        u'<office:document-styles '
        u'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        u'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
        u'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
        u'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
        u'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
        u'office:version="1.2">'
        u'<office:font-face-decls>'
        u'<style:font-face style:name="%s" svg:font-family="&apos;%s&apos;" style:font-family-generic="swiss"/>'
        u'</office:font-face-decls>'
        u'<office:styles>'
        u'<style:default-style style:family="paragraph">'
        u'<style:paragraph-properties fo:margin="0cm" fo:line-height="100%%"/>'
        u'<style:text-properties style:font-name="%s" fo:font-size="10pt" fo:language="sk" fo:country="SK"/>'
        u'</style:default-style>'
        u'<style:style style:name="Standard" style:family="paragraph"/>'
        u'<style:style style:name="Frame" style:family="graphic"><style:graphic-properties fo:border="none"/></style:style>'
        u'</office:styles>'
        u'<office:automatic-styles>'
        u'<style:page-layout style:name="pm1">'
        u'<style:page-layout-properties fo:page-width="%s" fo:page-height="%s" style:print-orientation="%s" '
        u'fo:margin-top="0cm" fo:margin-bottom="0cm" fo:margin-left="0cm" fo:margin-right="0cm"/>'
        u'</style:page-layout>'
        u'</office:automatic-styles>'
        u'<office:master-styles><style:master-page style:name="Standard" style:page-layout-name="pm1"/></office:master-styles>'
        u'</office:document-styles>' % (FONT, FONT, FONT, cm(width, dpi), cm(height, dpi),
                                        u'portrait' if height >= width else u'landscape'))

MANIFEST = (
    u'<?xml version="1.0" encoding="UTF-8"?>'
    u'<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">'
    u'<manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>'
    u'<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
    u'<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>'
    u'</manifest:manifest>')

def write_odt(path, pages, dpi):
    with zipfile.ZipFile(path, u'w') as z:
        z.writestr(zipfile.ZipInfo(u'mimetype'), u'application/vnd.oasis.opendocument.text',
                compress_type=zipfile.ZIP_STORED)
        z.writestr(u'META-INF/manifest.xml', MANIFEST, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr(u'styles.xml', build_styles(pages[0][0], dpi), compress_type=zipfile.ZIP_DEFLATED)
        z.writestr(u'content.xml', build_content(pages, dpi), compress_type=zipfile.ZIP_DEFLATED)

def overlaps(a, b):
    u"""True if the boxes of blocks ``a`` and ``b`` overlap by more than a fifth of the smaller one."""
    ax0, ay0, ax1, ay1 = a[u'bbox']
    bx0, by0, bx1, by1 = b[u'bbox']
    inter = max(0, min(ax1, bx1) - max(ax0, bx0)) * max(0, min(ay1, by1) - max(ay0, by0))
    smaller = min((ax1 - ax0) * (ay1 - ay0), (bx1 - bx0) * (by1 - by0)) or 1
    return inter > 0.2 * smaller

def recognize(pdf, odt, lang=DEFAULT_LANG, dpi=DEFAULT_DPI, tessdata=None, timeout=None,
              text_output=None):
    u"""
    Runs the whole PDF -> ODT recognition. Raises ``subprocess.CalledProcessError`` on failure
    and ``subprocess.TimeoutExpired`` if the whole document takes longer than ``timeout`` seconds.
    ``text_output``: optional path for a plain text dump (evaluation).
    """
    deadline = time.time() + timeout if timeout else None
    def remaining():
        return max(1, deadline - time.time()) if deadline else None
    directory = tempfile.mkdtemp(prefix=u'tessodt')
    try:
        run([u'pdftoppm', u'-r', str(dpi), u'-gray', u'-png', pdf, os.path.join(directory, u'page')],
                timeout=remaining())
        images = sorted(f for f in os.listdir(directory) if f.endswith(u'.png'))
        if not images:
            raise RuntimeError(u'pdftoppm produced no pages')
        pages = []
        for image in images:
            size, blocks = None, []
            for method in THRESHOLDING_METHODS:
                base = os.path.join(directory, image[:-4] + u'-' + method)
                cmd = [u'tesseract', os.path.join(directory, image), base, u'-l', lang, u'--psm', u'3',
                       u'-c', u'thresholding_method=' + method, u'hocr']
                if tessdata:
                    cmd[3:3] = [u'--tessdata-dir', tessdata]
                run(cmd, timeout=remaining())
                size, found = parse_hocr(base + u'.hocr')
                if not blocks:
                    blocks = found
                    continue
                # Later passes only add confident real words that the first pass did not find, in
                # reading order (a block goes before the first block that starts below it).
                for block in found:
                    if block[u'confidence'] < 70 or not re.search(r'\w\w', block[u'lines'][0]):
                        continue
                    if any(overlaps(block, o) for o in blocks):
                        continue
                    index = next((i for i, o in enumerate(blocks)
                                  if o[u'bbox'][1] > block[u'bbox'][3]), len(blocks))
                    blocks.insert(index, block)
            pages.append((size, blocks))
        write_odt(odt, pages, dpi)
        if text_output:
            with open(text_output, u'w') as f:
                for _, blocks in pages:
                    f.write(u'\n'.join(line for b in blocks for line in b[u'lines']) + u'\n\n')
        return sum(len(p) for _, p in pages)
    finally:
        shutil.rmtree(directory, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(u'--lang', default=DEFAULT_LANG)
    parser.add_argument(u'--dpi', type=int, default=DEFAULT_DPI)
    parser.add_argument(u'--tessdata', default=os.environ.get(u'TESSDATA_PREFIX') or None)
    parser.add_argument(u'--txt', help=u'also write recognized text to this file')
    parser.add_argument(u'pdf')
    parser.add_argument(u'odt')
    args = parser.parse_args()
    n = recognize(args.pdf, args.odt, args.lang, args.dpi, args.tessdata, text_output=args.txt)
    print(u'%d text blocks' % n)

if __name__ == u'__main__':
    main()
