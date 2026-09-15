import datetime

from poleno.utils.misc import squeeze
from poleno.utils.date import utc_now
from poleno import datacheck


def attachment_file_check(attachments):
    u"""
    Checks that every Attachment (or Attachment like) instance, which file is not NULL, has its file
    working.
    """
    for attachment in attachments:
        if not attachment.file:
            continue
        try:
            try:
                attachment.file.open(u'rb')
            finally:
                attachment.file.close()
        except IOError:
            yield datacheck.Error(u'{} is missing its file: "{}".',
                                  attachment, attachment.file.name)

def attachment_orphaned_file_check(attachments, field, model):
    u"""
    Checks that there are not any orphaned Attachment's (or Attachment's like) files.
    """
    attachment_names = {a.file.name for a in attachments}
    if not field.storage.exists(field.upload_to):
        return
    for file_name in field.storage.listdir(field.upload_to)[1]:
        attachment_name = u'{}/{}'.format(field.upload_to, file_name)
        # ``get_modified_time`` returns an aware datetime when USE_TZ is enabled.
        modified_time = field.storage.get_modified_time(attachment_name)
        timedelta = utc_now() - modified_time
        if timedelta > datetime.timedelta(days=5) and attachment_name not in attachment_names:
            yield datacheck.Info(squeeze(u"""
                    There is no {} instance for file: "{}". The file is {} days old, so you can
                    probably remove it.
                    """), model.__name__, attachment_name, timedelta.days)
