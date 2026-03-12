import os
import shutil
import traceback

import subprocess
from django.core.files.base import ContentFile
from django.conf import settings

from poleno.cron import cron_logger
from poleno.utils.misc import guess_extension

from .utils import temporary_directory
from .models import AttachmentAnonymization, AttachmentFinalization
from . import content_types


LIBREOFFICE_TIMEOUT = 300

def finalize_using_mock(attachment_anonymization):
    finalized = os.path.join(settings.PROJECT_PATH,
                              u'chcemvediet/apps/anonymization/mocks/finalized.pdf')
    with open(finalized, u'rb') as file:
        AttachmentFinalization.objects.create(
            attachment=attachment_anonymization.attachment,
            successful=True,
            file=ContentFile(file.read()),
            content_type=content_types.PDF_CONTENT_TYPE,
            debug=u'Created using mocked libreoffice.'.format()
        )
    cron_logger.info(u'Finalized attachment using mocked libreoffice: {}'.format(
        attachment_anonymization))

def finalize_using_libreoffice(attachment_anonymization):
    if settings.MOCK_LIBREOFFICE:
        finalize_using_mock(attachment_anonymization)
        return

    try:
        p = None
        with temporary_directory() as directory:
            filename = os.path.join(directory,
                                    u'file' + guess_extension(attachment_anonymization.content_type)
                                    )
            shutil.copy2(attachment_anonymization.file.path, filename)
            p = subprocess.run(
                [u'libreoffice', u'--headless', u'--convert-to', u'pdf', u'--outdir', directory,
                 filename],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=LIBREOFFICE_TIMEOUT,
                check=True,
            )
            with open(os.path.join(directory, u'file.pdf'), u'rb') as file_pdf:
                AttachmentFinalization.objects.create(
                    attachment=attachment_anonymization.attachment,
                    successful=True,
                    file=ContentFile(file_pdf.read()),
                    content_type=content_types.PDF_CONTENT_TYPE,
                    debug=u'STDOUT:\n{}\nSTDERR:\n{}'.format(p.stdout.decode(u'utf-8'),
                                                             p.stderr.decode(u'utf-8'),
                                                             )
                )
            cron_logger.info(u'Finalized attachment using libreoffice: {}'.format(
                attachment_anonymization))
    except Exception as e:
        trace = traceback.format_exc()
        stdout = (p.stdout if p else getattr(e, u'stdout', b'')).decode(u'utf-8')
        stderr = (p.stderr if p else getattr(e, u'stderr', b'')).decode(u'utf-8')
        AttachmentFinalization.objects.create(
            attachment=attachment_anonymization.attachment,
            successful=False,
            content_type=content_types.PDF_CONTENT_TYPE,
            debug=u'STDOUT:\n{}\nSTDERR:\n{}\n{}'.format(stdout, stderr, trace)
        )
        cron_logger.error(u'Finalizing attachment using libreoffice has failed: {}\n An '
                          u'unexpected error occured: {}\n{}'.format(
                                  attachment_anonymization, e.__class__.__name__, trace))

def finalize_attachment():
    attachment_anonymization = (AttachmentAnonymization.objects
            .successful()
            .anonymized_to_odt()
            .not_finalized()
            .first())
    if attachment_anonymization is None:
        return
    else:
        finalize_using_libreoffice(attachment_anonymization)
