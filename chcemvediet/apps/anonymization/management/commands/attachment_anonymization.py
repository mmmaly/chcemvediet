import sys

import magic
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from poleno.attachments.models import Attachment
from poleno.utils.misc import squeeze
from chcemvediet.apps.anonymization.models import AttachmentFinalization
from chcemvediet.apps.inforequests.models import Action


class Command(BaseCommand):
    help = squeeze(u"""
            Creates anonymization for the specified Attachment. The anonymized content is read from
            the given file or from stdin if no file is specified. If no file is specified and stdin
            is empty, the command will fail.
            """)

    def add_arguments(self, parser):
        parser.add_argument(u'args', nargs=u'*', metavar=u'attachment_id [file]')
        parser.add_argument(u'--content_type', default=None,
                    help=squeeze(u"""
                            Content type of file, e.g. "application/pdf". Automatically guessed from
                            the file content if not specified.
                            """)
                    )
        parser.add_argument(u'--debug',
                    default=u'',
                    help=u'Debug message to the newly created anonymization. Empty by default.'
                    )
        parser.add_argument(u'--force',
                    action=u'store_true', default=False,
                    help=u'Overwrite any existing anonymization for the attachment.'
                    )

    @transaction.atomic
    def handle(self, *args, **options):
        if not args:
            raise CommandError(u'attachment_anonymization takes at least 1 argument (0 given).')
        elif len(args) > 2:
            raise CommandError(
                u'attachment_anonymization takes at most 2 arguments ({} given).'.format(len(args))
            )

        attachment_pk = args[0]
        try:
            attachment = Attachment.objects.attached_to(Action).get(pk=attachment_pk)
        except (Attachment.DoesNotExist, ValueError):
            raise CommandError(
                u'Attachment instance with pk "{}" does not exist.'.format(attachment_pk)
            )
        attachments_finalization = (AttachmentFinalization.objects
                                    .filter(attachment=attachment)
                                    .successful())
        if not options[u'force'] and attachments_finalization:
            raise CommandError(u'Anonymization already exists. Use the --force to overwrite it.')

        if len(args) == 2:
            filename = args[1]
            try:
                with open(filename, u'rb') as file:
                    content = file.read()
            except IOError as e:
                raise CommandError(u'Could not open file: {}.'.format(e))
        else:
            content = sys.stdin.buffer.read()
            if not content:
                raise CommandError(u'No content given.')

        attachments_finalization.delete()
        AttachmentFinalization.objects.create(
            attachment=attachment,
            successful=True,
            file=ContentFile(content),
            content_type=options[u'content_type'] or magic.from_buffer(content, mime=True),
            debug=options[u'debug'],
        )
