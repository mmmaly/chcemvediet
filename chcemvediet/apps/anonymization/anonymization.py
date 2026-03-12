# -*- coding: utf-8 -*-
import re
import zipfile
import io
import traceback
from contextlib import closing

import magic
from lxml import etree
from django.core.files.base import ContentFile

from poleno.cron import cron_logger

from .models import AttachmentRecognition, AttachmentAnonymization
from . import content_types


ANONYMIZATION_STRING = u'xxxxx'
WORD_SIZE_MIN = 3

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
    return etree.tostring(root)

def anonymize_odt(attachment_recognition):
    try:
        inforequest = attachment_recognition.attachment.generic_object.branch.inforequest
        parser = etree.XMLParser()
        pattern = generate_user_pattern(inforequest)
        namespace = {u'text': u'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}
        with closing(io.BytesIO(attachment_recognition.content)) as buffer_in:
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
                AttachmentAnonymization.objects.create(
                    attachment=attachment_recognition.attachment,
                    successful=True,
                    file=ContentFile(buffer_out.getvalue()),
                    content_type=content_types.ODT_CONTENT_TYPE,
                )
                cron_logger.info(u'Anonymized attachment_recognition: {}'.format(
                        attachment_recognition))
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
