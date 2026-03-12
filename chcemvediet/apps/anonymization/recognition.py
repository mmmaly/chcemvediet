import os
import shutil
import traceback

import subprocess
from django.core.files.base import ContentFile
from django.conf import settings

from poleno.cron import cron_logger

from .models import AttachmentNormalization, AttachmentRecognition
from .utils import temporary_directory
from . import content_types


OCR_TIMEOUT = 300

def recognize_using_mock(attachment_normalization):
    normalized = os.path.join(settings.PROJECT_PATH,
                              u'chcemvediet/apps/anonymization/mocks/recognized.odt')
    with open(normalized, u'rb') as file:
        AttachmentRecognition.objects.create(
            attachment=attachment_normalization.attachment,
            successful=True,
            file=ContentFile(file.read()),
            content_type=content_types.ODT_CONTENT_TYPE,
            debug=u'Created using mocked abbyyocr11.'
        )
    cron_logger.info(u'Recogized attachment_normalizon using mocked abbyyocr11: {}'.format(
        attachment_normalization))

def recognize_using_ocr(attachment_normalization):
    if settings.MOCK_OCR:
        recognize_using_mock(attachment_normalization)
        return

    try:
        p = None
        with temporary_directory() as directory:
            filename = os.path.join(directory, u'file.pdf')
            shutil.copy2(attachment_normalization.file.path, filename)
            p = subprocess.run(
                [u'abbyyocr11', u'--recognitionLanguage', u'Slovak', u'--splitDualPages', u'-if',
                 filename, u'-f', u'ODT', u'--rtfKeepLines', u'--rtfRemoveSoftHyphens',
                 u'--rtfPageSynthesisMode', u'ExactCopy', u'-of',
                 os.path.join(directory, u'file.odt')],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=OCR_TIMEOUT,
                check=True,
            )
            with open(os.path.join(directory, u'file.odt'), u'rb') as file_odt:
                AttachmentRecognition.objects.create(
                    attachment=attachment_normalization.attachment,
                    successful=True,
                    file=ContentFile(file_odt.read()),
                    content_type=content_types.ODT_CONTENT_TYPE,
                    debug=u'STDOUT:\n{}\nSTDERR:\n{}'.format(p.stdout.decode(u'utf-8'),
                                                             p.stderr.decode(u'utf-8'),
                                                             )
                )
            cron_logger.info(u'Recognized attachment_normalization using OCR: {}'.format(
                attachment_normalization))
    except Exception as e:
        trace = traceback.format_exc()
        stdout = (p.stdout if p else getattr(e, u'stdout', b'')).decode(u'utf-8')
        stderr = (p.stderr if p else getattr(e, u'stderr', b'')).decode(u'utf-8')
        AttachmentRecognition.objects.create(
            attachment=attachment_normalization.attachment,
            successful=False,
            content_type=content_types.ODT_CONTENT_TYPE,
            debug=u'STDOUT:\n{}\nSTDERR:\n{}\n{}'.format(stdout, stderr, trace)
        )
        cron_logger.error(u'Recognizing attachment_normalization using OCR has failed: {}\n An '
                          u'unexpected error occured: {}\n{}'.format(
                          attachment_normalization, e.__class__.__name__, trace))

def recognize_attachment():
    attachment_normalization = (AttachmentNormalization.objects
            .successful()
            .normalized_to_pdf()
            .not_recognized()
            .first())
    if attachment_normalization is None:
        return
    else:
        recognize_using_ocr(attachment_normalization)
