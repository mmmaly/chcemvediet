# -*- coding: utf-8 -*-
import re
import zipfile
import io
import traceback
from contextlib import closing

import magic
from lxml import etree
from django.core.files.base import ContentFile
from django.db import transaction

from poleno.cron import cron_logger

from .models import AttachmentRecognition, AttachmentAnonymization, AttachmentFinalization
from .utils import run_command
from . import content_types


ANONYMIZATION_STRING = u'xxxxx'
WORD_SIZE_MIN = 3
# pdftotext and pdfinfo need seconds even for documents of hundreds of pages.
POPPLER_TIMEOUT = 300

TRANSLATE_TABLE = {
    u'a': u'(?:a|á|ä)',
    u'á': u'(?:a|á|ä)',
    u'ä': u'(?:a|á|ä)',
    u'e': u'(?:e|é)',
    u'é': u'(?:e|é)',
    u'i': u'(?:i|í)',
    u'í': u'(?:i|í)',
    u'o': u'(?:o|ó|ô)',
    u'ó': u'(?:o|ó|ô)',
    u'ô': u'(?:o|ó|ô)',
    u'u': u'(?:u|ú)',
    u'ú': u'(?:u|ú)',
    u'y': u'(?:y|ý)',
    u'ý': u'(?:y|ý)',
    u'c': u'(?:c|č)',
    u'č': u'(?:c|č)',
    u'd': u'(?:d|ď)',
    u'ď': u'(?:d|ď)',
    u'l': u'(?:l|ĺ|ľ)',
    u'ĺ': u'(?:l|ĺ|ľ)',
    u'ľ': u'(?:l|ĺ|ľ)',
    u'n': u'(?:n|ň)',
    u'ň': u'(?:n|ň)',
    u'r': u'(?:r|ŕ)',
    u'ŕ': u'(?:r|ŕ)',
    u's': u'(?:s|š)',
    u'š': u'(?:s|š)',
    u't': u'(?:t|ť)',
    u'ť': u'(?:t|ť)',
    u'z': u'(?:z|ž)',
    u'ž': u'(?:z|ž)',
}

def generate_word_pattern(words, match_subwords):
    u"""
    Generates list of patterns, that matches slovak accent insensitive lowercase word. Each word is
    captured in group. If ``match_subwords`` is True, pattern will also match subwords.
    """
    patterns = []
    template = u'({})' if match_subwords else u'(\\b{}\\b)'
    for word in words:
        if len(word) < WORD_SIZE_MIN:
            continue
        p = u''
        for c in word.lower():
            if c in TRANSLATE_TABLE:
                p += TRANSLATE_TABLE[c]
            else:
                p += re.escape(c)
                if not c.isalnum() and match_subwords:
                    p += u'?'
        patterns.append(template.format(p))
    return patterns

def generate_numeric_pattern(numbers, match_subwords):
    u"""
    Generates list of patterns, that matches number, where digits can be separated with ' ' or '-'.
    Each number is captured in group. If ``match_subwords`` is True, pattern will also match
    subwords.
    """
    patterns = []
    template = u'({})' if match_subwords else u'(\\b{}\\b)'
    for number in numbers:
        number = re.sub(u'[ -]', u'', number)
        if len(number) < WORD_SIZE_MIN:
            continue
        p = u'[ -]?'.join([re.escape(c) for c in number])
        patterns.append(template.format(p))
    return patterns

def get_default_anonymized_strings_for_user(user, inforequest=None):
    u"""
    Return `user` default anonymized strings in two lists. First list for words, second for numbers.
    """
    words = user.first_name.split() + user.last_name.split()
    words.append(user.profile.street)
    words.append(user.profile.city)
    numbers = [user.profile.zip]
    if inforequest:
        words += inforequest.applicant_name.split()
        words.append(inforequest.applicant_street)
        words.append(inforequest.applicant_city)
        numbers.append(inforequest.applicant_zip)
    return words, numbers

def get_custom_anonymized_strings_for_user(user):
    words = []
    numbers = []
    for line in user.profile.custom_anonymized_strings:
        if re.sub(u'[ -]', u'', line).isdigit():
            numbers.append(line)
        else:
            words.append(line)
    return words, numbers

def get_anonymized_strings_for_user(inforequest):
    if inforequest.applicant.profile.custom_anonymized_strings is None:
        return get_default_anonymized_strings_for_user(inforequest.applicant, inforequest)
    else:
        return get_custom_anonymized_strings_for_user(inforequest.applicant)

def generate_user_pattern(inforequest, match_subwords=False):
    u"""
    Generates pattern object, that matches user anonymization strings. If ``match_subwords`` is
    True, pattern will also match subwords.
    """
    words, numbers = get_anonymized_strings_for_user(inforequest)
    patterns = (
            generate_word_pattern(set(words), match_subwords) +
            generate_numeric_pattern(set(numbers), match_subwords)
    )
    return re.compile(u'|'.join(patterns), re.IGNORECASE | re.UNICODE)

def generate_attachment_pattern(inforequest):
    u"""
    Pattern for anonymized copies of attachments: the user strings and the inforequest unique
    e-mail address. The address is printed in most replies and published addresses attract spam.
    """
    patterns = [generate_user_pattern(inforequest).pattern]
    if inforequest.unique_email:
        patterns.append(u'({})'.format(re.escape(inforequest.unique_email)))
    return re.compile(u'|'.join(p for p in patterns if p), re.IGNORECASE | re.UNICODE)

def anonymize_filename(inforequest, filename):
    u"""
    File name of a public copy of an attachment: the user strings (also inside longer words, file
    names are often written without spaces) and the inforequest unique e-mail address are replaced.
    """
    if inforequest.unique_email:
        filename = re.sub(re.escape(inforequest.unique_email), ANONYMIZATION_STRING, filename,
                flags=re.IGNORECASE)
    return anonymize_string(generate_user_pattern(inforequest, match_subwords=True), filename)

def anonymize_string(prog, content):
    if not prog.pattern:
        return content
    return prog.sub(ANONYMIZATION_STRING, content)

def anonymize_markup(prog, content, parser, xpath=u'.//', namespace=None):
    u"""
    Anonymize user in each xpath of markup (xml or html) content, using defined namespace.
    """
    if not prog.pattern:
        return content
    root = etree.fromstring(content, parser)
    for t in root.findall(xpath, namespace):
        for tt in list(t):
            if tt.tail is None:
                continue
            tt.tail = prog.sub(ANONYMIZATION_STRING, tt.tail)
        if t.text is None:
            continue
        t.text = prog.sub(ANONYMIZATION_STRING, t.text)
    # Return the same type we got: ``str`` for HTML rendered into templates, ``bytes`` for ODT
    # files. ``etree.tostring()`` returns bytes by default on Python 3.
    if isinstance(content, str):
        return etree.tostring(root, encoding=u'unicode')
    return etree.tostring(root)

def odt_text(odt):
    u"""
    Text of all XML members of ``odt`` (bytes): every paragraph and heading on its own line, with
    its spans joined, so a word split into several spans is found too; then any other text.
    """
    paragraphs = (u'{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p',
                  u'{urn:oasis:names:tc:opendocument:xmlns:text:1.0}h')
    texts = []
    with zipfile.ZipFile(io.BytesIO(odt)) as z:
        for name in z.namelist():
            if name.endswith(u'.xml'):
                root = etree.fromstring(z.read(name), etree.XMLParser(huge_tree=True))
                texts.extend(u''.join(e.itertext()) for e in root.iter(*paragraphs))
                texts.extend(root.itertext())
    return u'\n'.join(texts)

def pdf_text(path):
    u"""
    Text layer and metadata (document info and XMP) of the PDF file ``path``.
    """
    texts = []
    for args in ([u'pdftotext', u'-q', path, u'-'], [u'pdfinfo', path], [u'pdfinfo', u'-meta', path]):
        texts.append(run_command(args, POPPLER_TIMEOUT).stdout.decode(u'utf-8', u'replace'))
    return u'\n'.join(texts)

def original_pdf_is_publishable(attachment, recognized_odt):
    u"""
    Whether the original PDF ``attachment`` can be published untouched. The copy rebuilt from the
    recognized text loses every picture, drawing and stamp, so a PDF in which there is nothing to
    hide is published as it is, like spreadsheets: no identifying data of the requester (see
    ``spreadsheets.get_identifying_strings``) may be found in its recognized text, in its own text
    layer, or in its metadata. If anything can not be checked, the PDF is not publishable.
    """
    from .spreadsheets import generate_identifying_pattern, found
    if attachment.content_type != content_types.PDF_CONTENT_TYPE:
        return False
    inforequest = attachment.generic_object.branch.inforequest
    pattern = generate_identifying_pattern(inforequest)
    try:
        text = odt_text(recognized_odt) + u'\n' + pdf_text(attachment.file.path)
    except Exception:
        cron_logger.warning(u'Checking original PDF has failed, it will not be published: {}\n{}'
                .format(attachment, traceback.format_exc()))
        return False
    return not found(pattern, text)

def anonymize_odt(attachment_recognition):
    try:
        attachment = attachment_recognition.attachment
        inforequest = attachment.generic_object.branch.inforequest
        parser = etree.XMLParser()
        pattern = generate_attachment_pattern(inforequest)
        namespace = {u'text': u'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}
        recognized_odt = attachment_recognition.content
        publish_original = original_pdf_is_publishable(attachment, recognized_odt)
        with closing(io.BytesIO(recognized_odt)) as buffer_in:
            with closing(io.BytesIO()) as buffer_out:
                with zipfile.ZipFile(buffer_in) as zipfile_in:
                    with zipfile.ZipFile(buffer_out, u'w') as zipfile_out:
                        for f in zipfile_in.filelist:
                            content = zipfile_in.read(f)
                            if magic.from_buffer(content, mime=True) in content_types.XML_CONTENT_TYPES:
                                zipfile_out.writestr(f, anonymize_markup(
                                        pattern, content, parser, u'.//text:span', namespace))
                            else:
                                zipfile_out.writestr(f, content)
                with transaction.atomic():
                    AttachmentAnonymization.objects.create(
                        attachment=attachment,
                        successful=True,
                        file=ContentFile(buffer_out.getvalue()),
                        content_type=content_types.ODT_CONTENT_TYPE,
                    )
                    if publish_original:
                        # The finalization step skips attachments that are already finalized.
                        with open(attachment.file.path, u'rb') as original:
                            AttachmentFinalization.objects.create(
                                attachment=attachment,
                                successful=True,
                                file=ContentFile(original.read()),
                                content_type=content_types.PDF_CONTENT_TYPE,
                                debug=u'Original PDF published untouched: no identifying data '
                                      u'of the requester found in it.',
                            )
                cron_logger.info(u'Anonymized attachment_recognition: {}{}'.format(
                        attachment_recognition,
                        u' (original PDF published)' if publish_original else u''))
    except Exception as e:
        trace = traceback.format_exc()
        AttachmentAnonymization.objects.create(
            attachment=attachment_recognition.attachment,
            successful=False,
            content_type=content_types.ODT_CONTENT_TYPE,
            debug=trace
        )
        cron_logger.error(u'Anonymizing attachment_recognition has failed: {}\n An '
                          u'unexpected error occured: {}\n{}'.format(
                                  attachment_recognition, e.__class__.__name__, trace))

def anonymize_attachment():
    attachment_recognition = (AttachmentRecognition.objects
            .successful()
            .recognized_to_odt()
            .not_anonymized()
            .first())
    if attachment_recognition is None:
        return
    else:
        anonymize_odt(attachment_recognition)
