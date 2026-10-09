# vim: expandtab
# -*- coding: utf-8 -*-
u"""
Public copies of spreadsheet attachments.

Spreadsheets are not printed to PDF and recognized like other documents; a print-out of a table
is useless as data and may have thousands of pages. Instead:

 1. The file is converted to OpenDocument (ODS) with LibreOffice, whatever its format is.
 2. If it has images, embedded objects or macros, every sheet is exported to CSV and the
    requester's data are replaced in the CSV text.
 3. Otherwise, if it does not contain any *identifying* data of the requester (surname, street,
    custom anonymization strings, the inforequest e-mail address), the original file is published
    untouched. The city, the postcode and the first name alone do not identify anybody.
 4. Otherwise the requester's data are replaced with "xxxxx" in the ODS (cells, sheet names,
    comments, hidden sheets, headers, metadata, charts), exactly as in other documents, and the
    result is published as XLSX.

Whatever is published is checked once more at the end: if any identifying string is still
found in it, nothing is published.
"""
import os
import re
import shutil
import subprocess
import zipfile
from html import unescape
from io import BytesIO

from lxml import etree

from . import content_types
from .anonymization import (ANONYMIZATION_STRING, generate_attachment_pattern,
                            generate_word_pattern, generate_numeric_pattern,
                            get_custom_anonymized_strings_for_user)
from .utils import temporary_directory, libreoffice_convert


# Large workbooks take minutes to load; there is no page limit like with PDF print-outs.
LIBREOFFICE_TIMEOUT = 900
# LibreOffice filter options for CSV: comma, double quote, UTF-8, from the first row; the last
# option (-1) exports every sheet to its own file "<name>-<sheet>.csv".
CSV_FILTER = u'csv:Text - txt - csv (StarCalc):44,34,76,1,,0,false,true,false,false,false,-1'

NS_OFFICE = u'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
NS_TABLE = u'urn:oasis:names:tc:opendocument:xmlns:table:1.0'
NS_TEXT = u'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
NS_DRAW = u'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'
NS_CALCEXT = u'urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0'
NS_MANIFEST = u'urn:oasis:names:tc:opendocument:xmlns:manifest:1.0'
CELL_TAGS = (u'{%s}table-cell' % NS_TABLE, u'{%s}covered-table-cell' % NS_TABLE)
PARAGRAPH_TAGS = (u'{%s}p' % NS_TEXT, u'{%s}h' % NS_TEXT)
# Attributes holding the typed value of a cell; they are dropped when the cell becomes a string.
VALUE_ATTRIBUTES = [u'{%s}%s' % (NS_OFFICE, n) for n in (
        u'value', u'date-value', u'time-value', u'boolean-value', u'currency', u'string-value')]
# ODS members that are neither sheet data nor safe to keep in an anonymized copy.
DROPPED_PREFIXES = (u'Thumbnails/', u'ObjectReplacements/')


class NotASpreadsheet(Exception):
    u"""LibreOffice could not open the file as a spreadsheet."""

class StillIdentifiable(Exception):
    u"""Identifying data of the requester were found in the file that was about to be published."""


def is_spreadsheet(attachment):
    u"""Whether ``attachment`` should be tried as a spreadsheet (by content type or extension)."""
    if attachment.content_type in content_types.SPREADSHEET_CONTENT_TYPES:
        return True
    extension = os.path.splitext(attachment.name or u'')[1].lower()
    return extension in content_types.SPREADSHEET_EXTENSIONS

def get_identifying_strings(inforequest):
    u"""
    Strings that identify the requester: surname, street and the names given in the inforequest
    except the first name; or all custom strings if the requester has defined them. Returns lists
    of words and numbers like ``get_anonymized_strings_for_user()``.
    """
    user = inforequest.applicant
    if user.profile.custom_anonymized_strings is not None:
        return get_custom_anonymized_strings_for_user(user)
    first_names = set(w.lower() for w in user.first_name.split())
    words = user.last_name.split()
    words += [w for w in inforequest.applicant_name.split() if w.lower() not in first_names]
    words += [user.profile.street, inforequest.applicant_street]
    return words, []

def generate_identifying_pattern(inforequest):
    words, numbers = get_identifying_strings(inforequest)
    patterns = generate_word_pattern(set(words), False) + generate_numeric_pattern(set(numbers), False)
    if inforequest.unique_email:
        patterns.append(u'({})'.format(re.escape(inforequest.unique_email)))
    return re.compile(u'|'.join(patterns), re.IGNORECASE | re.UNICODE)

def found(prog, text):
    return bool(prog.pattern) and prog.search(text) is not None

def substitute(prog, text):
    return prog.sub(ANONYMIZATION_STRING, text) if prog.pattern and text else text


def is_xml_member(name):
    return name.endswith(u'.xml') and not name.startswith((u'META-INF/', u'Configurations2/')) \
            and os.path.basename(name) not in (u'settings.xml',)

def inspect_ods(ods):
    u"""
    Returns a set of reasons why the spreadsheet must not be published as a spreadsheet:
    "images", "embedded objects", "macros". Charts are fine; they are plain XML.
    """
    reasons = set()
    with zipfile.ZipFile(BytesIO(ods)) as archive:
        for name in archive.namelist():
            if name.endswith(u'/'):
                continue
            top = name.split(u'/')[0]
            if top == u'Pictures':
                reasons.add(u'images')
            elif top in (u'Basic', u'Scripts'):
                if os.path.basename(name) not in (u'script-lb.xml', u'script-lc.xml'):
                    reasons.add(u'macros')
            elif name in (u'mimetype', u'content.xml', u'styles.xml', u'meta.xml', u'settings.xml',
                          u'manifest.rdf'):
                pass
            elif top in (u'META-INF', u'Thumbnails', u'Configurations2', u'ObjectReplacements'):
                pass
            elif top.startswith(u'Object ') and name.endswith(u'.xml'):
                pass # A chart or a formula: an XML subdocument
            else:
                reasons.add(u'embedded objects')
        content = archive.read(u'content.xml')
    # A chart is a frame with the chart object and its rendered picture; that is not an image.
    for tag in re.findall(br'<draw:image\b[^>]*>', content):
        if b'"./ObjectReplacements/' not in tag and b'"ObjectReplacements/' not in tag:
            reasons.add(u'images')
    if b'<draw:plugin' in content or b'<draw:applet' in content or b'<draw:floating-frame' in content:
        reasons.add(u'embedded objects')
    return reasons

def has_macros(path):
    u"""Whether an OOXML file carries a VBA project. LibreOffice may drop it during conversion."""
    try:
        with zipfile.ZipFile(path) as archive:
            return any(u'vbaProject' in name for name in archive.namelist())
    except zipfile.BadZipFile:
        return False

def element_texts(root):
    u"""
    All texts of an XML tree a reader may ever see: whole paragraphs (a word may be split into
    several spans), texts outside of paragraphs and all attribute values (sheet names, cached
    string values, formulas, links).
    """
    for element in root.iter():
        if not isinstance(element.tag, str):
            continue
        if element.tag in PARAGRAPH_TAGS:
            yield u''.join(element.itertext())
        if element.text:
            yield element.text
        if element.tail:
            yield element.tail
        for value in element.attrib.values():
            yield value

def extract_ods_text(ods):
    texts = []
    with zipfile.ZipFile(BytesIO(ods)) as archive:
        for name in archive.namelist():
            texts.append(name)
            if is_xml_member(name):
                texts.extend(element_texts(etree.fromstring(archive.read(name))))
    return u'\n'.join(texts)

def extract_ooxml_text(data):
    u"""
    Texts of an XLSX file a reader may see: strings, numbers, formulas, comments, sheet names,
    headers and document properties. Row numbers, cell references and indexes of shared strings
    are left out; a postcode-like number would match them by accident. For checks only.
    """
    texts = []
    with zipfile.ZipFile(BytesIO(data)) as archive:
        for name in archive.namelist():
            texts.append(name)
            if not name.endswith((u'.xml', u'.vml')):
                continue
            xml = archive.read(name).decode(u'utf-8', u'replace')
            if name.startswith(u'xl/worksheets/'):
                xml = re.sub(r'(?s)<c\b[^>]*\bt="s"[^>]*>.*?</c>', u'', xml)
            elif name == u'xl/workbook.xml' or name.startswith(u'docProps/'):
                texts.extend(unescape(v) for v in re.findall(r'\bname="([^"]*)"', xml))
            # Texts of one cell may be split into runs: check them both joined and apart.
            texts.append(unescape(re.sub(r'</?(?:r|t|rPr|rFont|sz|b|i|u|color|family|charset|scheme)\b[^>]*>', u'', xml)
                    ).replace(u'<', u'\n<').replace(u'>', u'>\n'))
            texts.append(unescape(re.sub(r'<[^>]+>', u'\n', xml)))
    return u'\n'.join(l for l in u'\n'.join(texts).split(u'\n') if not l.startswith(u'<'))

def stringify_cell(cell, text=None):
    u"""Turns a typed cell (number, date, formula) into a plain string cell."""
    for attribute in VALUE_ATTRIBUTES + [u'{%s}formula' % NS_TABLE]:
        cell.attrib.pop(attribute, None)
    cell.set(u'{%s}value-type' % NS_OFFICE, u'string')
    cell.set(u'{%s}value-type' % NS_CALCEXT, u'string')
    if text is not None:
        paragraphs = [e for e in cell if e.tag in PARAGRAPH_TAGS]
        if not paragraphs:
            paragraphs = [etree.SubElement(cell, PARAGRAPH_TAGS[0])]
        for child in list(paragraphs[0]):
            paragraphs[0].remove(child)
        paragraphs[0].text = text
        for paragraph in paragraphs[1:]:
            cell.remove(paragraph)

def anonymize_xml(prog, xml):
    u"""Replaces matches of ``prog`` in all texts and attribute values of an ODS XML member."""
    root = etree.fromstring(xml)
    # Rendered pictures of charts are removed from the file, see ``DROPPED_PREFIXES``.
    for image in list(root.iter(u'{%s}image' % NS_DRAW)):
        href = image.get(u'{http://www.w3.org/1999/xlink}href', u'')
        if href.lstrip(u'./').startswith(DROPPED_PREFIXES) and image.getparent() is not None:
            image.getparent().remove(image)
    touched = []
    for element in root.iter():
        if not isinstance(element.tag, str):
            continue
        new = substitute(prog, element.text)
        if new != element.text:
            element.text = new
            touched.append(element)
        new = substitute(prog, element.tail)
        if new != element.tail:
            element.tail = new
            if element.getparent() is not None:
                touched.append(element.getparent())
        for attribute, old in list(element.attrib.items()):
            new = substitute(prog, old)
            if new != old:
                element.set(attribute, new)
                if attribute in VALUE_ATTRIBUTES:
                    touched.append(element)
    # A word may be split into several spans ("Nov<span>ák</span>"). If a whole paragraph still
    # matches, it is replaced as plain text; the formatting inside of it is lost.
    for paragraph in root.iter(*PARAGRAPH_TAGS):
        joined = u''.join(paragraph.itertext())
        new = substitute(prog, joined)
        if new != joined:
            for child in list(paragraph):
                paragraph.remove(child)
            paragraph.text = new
            touched.append(paragraph)
    # A cell whose content was changed must stop being a number, a date or a formula; otherwise
    # the application shows its original typed value again.
    done = set()
    for element in touched:
        cell = element if element.tag in CELL_TAGS else next(
                (a for a in element.iterancestors() if a.tag in CELL_TAGS), None)
        if cell is None or id(cell) in done:
            continue
        done.add(id(cell))
        visible = u''.join(u''.join(p.itertext()) for p in cell if p.tag in PARAGRAPH_TAGS)
        stringify_cell(cell, None if ANONYMIZATION_STRING in visible else ANONYMIZATION_STRING)
    return etree.tostring(root, xml_declaration=True, encoding=u'UTF-8')

def anonymize_ods(prog, ods):
    u"""
    Returns ODS with all matches of ``prog`` replaced with "xxxxx". Thumbnails and rendered
    pictures of charts are removed, because they show the original content.
    """
    output = BytesIO()
    with zipfile.ZipFile(BytesIO(ods)) as source:
        with zipfile.ZipFile(output, u'w', zipfile.ZIP_DEFLATED) as target:
            names = [u'mimetype'] + [n for n in source.namelist() if n != u'mimetype']
            for name in names:
                if name.startswith(DROPPED_PREFIXES):
                    continue
                data = source.read(name)
                if name == u'META-INF/manifest.xml':
                    root = etree.fromstring(data)
                    for entry in root.findall(u'{%s}file-entry' % NS_MANIFEST):
                        if entry.get(u'{%s}full-path' % NS_MANIFEST, u'').startswith(DROPPED_PREFIXES):
                            root.remove(entry)
                    data = etree.tostring(root, xml_declaration=True, encoding=u'UTF-8')
                elif is_xml_member(name):
                    data = anonymize_xml(prog, data)
                if name == u'mimetype':
                    target.writestr(zipfile.ZipInfo(u'mimetype'), data, zipfile.ZIP_STORED)
                else:
                    target.writestr(name, data)
    return output.getvalue()

def assert_not_identifiable(identifying, text):
    if found(identifying, text):
        raise StillIdentifiable(u'Identifying data found in the file to be published.')

def csv_copies(source, directory, name, replaced, identifying):
    u"""One anonymized CSV per sheet. Returns list of (name, content type, content)."""
    outdir = os.path.join(directory, u'csv')
    libreoffice_convert(source, outdir, CSV_FILTER, LIBREOFFICE_TIMEOUT)
    stem = os.path.splitext(os.path.basename(source))[0]
    base = os.path.splitext(name)[0]
    copies = []
    for filename in sorted(os.listdir(outdir)):
        if not filename.endswith(u'.csv') or os.path.isdir(os.path.join(outdir, filename)):
            continue
        with open(os.path.join(outdir, filename), u'rb') as f:
            text = substitute(replaced, f.read().decode(u'utf-8', u'replace'))
        sheet = os.path.splitext(filename)[0]
        sheet = sheet[len(stem)+1:] if sheet.startswith(stem + u'-') else u''
        copy_name = substitute(replaced, u'{} - {}.csv'.format(base, sheet) if sheet else base + u'.csv')
        assert_not_identifiable(identifying, copy_name + u'\n' + text)
        if text.strip(u', \r\n'):
            copies.append((copy_name, content_types.CSV_CONTENT_TYPE, text.encode(u'utf-8')))
    if not copies:
        raise NotASpreadsheet(u'No sheet with any data.')
    return copies

def public_copies(path, name, content_type, inforequest):
    u"""
    Decides what may be published instead of the spreadsheet stored in ``path``. Returns
    ``(ods, copies, note)`` where ``ods`` is the file converted to ODS, ``copies`` is a list of
    (name, content type, content) and ``note`` describes what was done. Raises ``NotASpreadsheet``
    if LibreOffice cannot read the file as a spreadsheet and ``StillIdentifiable`` if the result
    fails the final check.
    """
    replaced = generate_attachment_pattern(inforequest)
    identifying = generate_identifying_pattern(inforequest)
    with temporary_directory() as directory:
        extension = os.path.splitext(name or u'')[1].lower()
        if extension not in content_types.SPREADSHEET_EXTENSIONS:
            extension = content_types.SPREADSHEET_EXTENSIONS_BY_TYPE.get(content_type, u'.xls')
        source = os.path.join(directory, u'source' + extension)
        shutil.copy(path, source)
        try:
            libreoffice_convert(source, os.path.join(directory, u'ods'), u'ods', LIBREOFFICE_TIMEOUT)
            with open(os.path.join(directory, u'ods', u'source.ods'), u'rb') as f:
                ods = f.read()
            reasons = inspect_ods(ods)
        except subprocess.TimeoutExpired:
            raise # Too big, not unreadable: no public copy rather than thousands of PDF pages.
        except Exception as e:
            raise NotASpreadsheet(u'{}: {}'.format(e.__class__.__name__, e))
        if has_macros(source):
            reasons.add(u'macros')

        if reasons:
            copies = csv_copies(source, directory, name, replaced, identifying)
            note = u'CSV for every sheet, because the spreadsheet contains {}.'.format(
                    u', '.join(sorted(reasons)))
            return ods, copies, note

        # The file name does not matter here: names of public copies are anonymized when they are
        # shown and downloaded.
        if not found(identifying, extract_ods_text(ods)):
            with open(path, u'rb') as f:
                return ods, [(name, content_type, f.read())], u'Original file, nothing to anonymize.'

        anonymized = anonymize_ods(replaced, ods)
        assert_not_identifiable(identifying, extract_ods_text(anonymized))
        clean = os.path.join(directory, u'anonymized.ods')
        with open(clean, u'wb') as f:
            f.write(anonymized)
        libreoffice_convert(clean, os.path.join(directory, u'xlsx'), u'xlsx', LIBREOFFICE_TIMEOUT)
        with open(os.path.join(directory, u'xlsx', u'anonymized.xlsx'), u'rb') as f:
            xlsx = f.read()
        copy_name = substitute(replaced, os.path.splitext(name)[0] + u'.xlsx')
        assert_not_identifiable(identifying, copy_name + u'\n' + extract_ooxml_text(xlsx))
        return ods, [(copy_name, content_types.XLSX_CONTENT_TYPE, xlsx)], u'Anonymized copy as XLSX.'
