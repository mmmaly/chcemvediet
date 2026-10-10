import os
import shutil
import traceback

import subprocess
from django.core.files.base import ContentFile
from django.conf import settings

from poleno.cron import cron_logger
from poleno.utils.misc import guess_extension

from .utils import temporary_directory, libreoffice_convert_to_pdf, process_output
from .models import AttachmentAnonymization, AttachmentFinalization
from . import content_types


# Converting a recognized document of a few hundred pages (about 30,000 text boxes) to PDF takes
# LibreOffice 10 to 15 minutes; ordinary documents need seconds.
LIBREOFFICE_TIMEOUT = 1200

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
            p = libreoffice_convert_to_pdf(filename, directory, LIBREOFFICE_TIMEOUT)
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
        stdout, stderr = process_output(p, e)
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
