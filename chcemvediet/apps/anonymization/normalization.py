import os
import shutil
import traceback

import subprocess
from django.core.files.base import ContentFile
from django.conf import settings

from poleno.cron import cron_logger
from poleno.attachments.models import Attachment
from poleno.utils.misc import guess_extension
from chcemvediet.apps.inforequests.models import Action

from .models import AttachmentNormalization
from .utils import temporary_directory
from . import content_types


LIBREOFFICE_TIMEOUT = 300
IMAGEMAGIC_TIMEOUT = 300

def normalize_pdf(attachment):
    AttachmentNormalization.objects.create(
        attachment=attachment,
        successful=True,
        file=ContentFile(attachment.content),
        content_type=content_types.PDF_CONTENT_TYPE
    )
    cron_logger.info(u'Normalized attachment: {}'.format(attachment))

def normalize_using_mock(attachment, package):
    normalized = os.path.join(settings.PROJECT_PATH,
                              u'chcemvediet/apps/anonymization/mocks/normalized.pdf')
    with open(normalized, u'rb') as file:
        AttachmentNormalization.objects.create(
            attachment=attachment,
            successful=True,
            file=ContentFile(file.read()),
            content_type=content_types.PDF_CONTENT_TYPE,
            debug=u'Created using mocked {}.'.format(package)
        )
    cron_logger.info(u'Normalized attachment using mocked {}: {}'.format(package, attachment))

def normalize_using_libreoffice(attachment):
    if settings.MOCK_LIBREOFFICE:
        normalize_using_mock(attachment, u'libreoffice')
        return

    try:
        p = None
        with temporary_directory() as directory:
            filename = os.path.join(directory, u'file' + guess_extension(attachment.content_type))
            shutil.copy2(attachment.file.path, filename)
            p = subprocess.run(
                [u'libreoffice', u'--headless', u'--convert-to', u'pdf', u'--outdir', directory,
                 filename],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=LIBREOFFICE_TIMEOUT,
                check=True,
            )
            with open(os.path.join(directory, u'file.pdf'), u'rb') as file_pdf:
                AttachmentNormalization.objects.create(
                    attachment=attachment,
                    successful=True,
                    file=ContentFile(file_pdf.read()),
                    content_type=content_types.PDF_CONTENT_TYPE,
                    debug=u'STDOUT:\n{}\nSTDERR:\n{}'.format(p.stdout.decode(u'utf-8'),
                                                             p.stderr.decode(u'utf-8'),
                                                             )
                )
            cron_logger.info(u'Normalized attachment using libreoffice: {}'.format(attachment))
    except Exception as e:
        trace = traceback.format_exc()
        stdout = (p.stdout if p else getattr(e, u'stdout', b'')).decode(u'utf-8')
        stderr = (p.stderr if p else getattr(e, u'stderr', b'')).decode(u'utf-8')
        AttachmentNormalization.objects.create(
            attachment=attachment,
            successful=False,
            content_type=content_types.PDF_CONTENT_TYPE,
            debug=u'STDOUT:\n{}\nSTDERR:\n{}\n{}'.format(stdout, stderr, trace)
        )
        cron_logger.error(u'Normalizing attachment using libreoffice has failed: {}\n An '
                          u'unexpected error occured: {}\n{}'.format(
                                  attachment, e.__class__.__name__, trace))

def normalize_using_imagemagic(attachment):
    if settings.MOCK_IMAGEMAGIC:
        normalize_using_mock(attachment, u'imagemagic')
        return

    try:
        p = None
        with temporary_directory() as directory:
            filename = os.path.join(directory, u'file' + guess_extension(attachment.content_type))
            shutil.copy2(attachment.file.path, filename)
            p = subprocess.run(
                [u'convert', filename, os.path.join(directory, u'file.pdf')],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=IMAGEMAGIC_TIMEOUT,
                check=True,
            )
            with open(os.path.join(directory, u'file.pdf'), u'rb') as file_pdf:
                AttachmentNormalization.objects.create(
                    attachment=attachment,
                    successful=True,
                    file=ContentFile(file_pdf.read()),
                    content_type=content_types.PDF_CONTENT_TYPE,
                    debug=u'STDOUT:\n{}\nSTDERR:\n{}'.format(p.stdout.decode(u'utf-8'),
                                                             p.stderr.decode(u'utf-8'),
                                                             )
                )
            cron_logger.info(u'Normalized attachment using imagemagic: {}'.format(attachment))
    except Exception as e:
        trace = traceback.format_exc()
        stdout = (p.stdout if p else getattr(e, u'stdout', b'')).decode(u'utf-8')
        stderr = (p.stderr if p else getattr(e, u'stderr', b'')).decode(u'utf-8')
        AttachmentNormalization.objects.create(
            attachment=attachment,
            successful=False,
            content_type=content_types.PDF_CONTENT_TYPE,
            debug=u'STDOUT:\n{}\nSTDERR:\n{}\n{}'.format(stdout, stderr, trace)
        )
        cron_logger.error(u'Normalizing attachment using imagemagic has failed: {}\n An '
                          u'unexpected error occured: {}\n{}'.format(
                                  attachment, e.__class__.__name__, trace))

def skip_normalization(attachment):
    AttachmentNormalization.objects.create(
        attachment=attachment,
        successful=False,
        content_type=None,
        debug=u'Not supported content type'
    )
    cron_logger.info(u'Skipping normalization of attachment with not supported content '
                     u'type: {}'.format(attachment))

def normalize_attachment():
    attachment = (Attachment.objects
                  .attached_to(Action)
                  .not_normalized()
                  .first()
                  )
    if attachment is None:
        return
    elif attachment.content_type == content_types.PDF_CONTENT_TYPE:
        normalize_pdf(attachment)
    elif attachment.content_type in content_types.LIBREOFFICE_CONTENT_TYPES:
        normalize_using_libreoffice(attachment)
    elif attachment.content_type in content_types.IMAGEMAGICK_CONTENT_TYPES:
        normalize_using_imagemagic(attachment)
    else:
        skip_normalization(attachment)
