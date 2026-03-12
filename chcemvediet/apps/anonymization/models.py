import logging
import itertools

from django.db import models
from django.utils.functional import cached_property

from poleno import datacheck
from poleno.attachments.models import Attachment
from poleno.attachments.utils import attachment_file_check, attachment_orphaned_file_check
from poleno.utils.models import QuerySet
from poleno.utils.date import utc_now
from poleno.utils.misc import FormatMixin, random_string, squeeze, decorate, adjust_extension

from . import content_types


class AttachmentNormalizationQuerySet(QuerySet):
    def successful(self):
        return self.filter(successful=True)

    def normalized_to_pdf(self):
        return self.filter(content_type=content_types.PDF_CONTENT_TYPE)

    def not_recognized(self):
        return self.filter(attachment__attachmentrecognition__isnull=True)

    def order_by_pk(self):
        return self.order_by(u'pk')

class AttachmentNormalization(FormatMixin, models.Model):

    # May NOT be NULL
    attachment = models.ForeignKey(Attachment, on_delete=models.CASCADE)

    # May NOT be NULL
    successful = models.BooleanField(default=False,
            help_text=squeeze(u"""
                True if normalization has succeeded, False otherwise.
                """))

    # Filename may be empty; Random local filename is generated in save() when creating a new object
    file = models.FileField(upload_to=u'attachment_normalizations', max_length=255, blank=True,
            help_text=squeeze(u"""
                Empty filename if normalization failed or normalization didn't create any file.
                """))

    # May be empty: Extension automatically adjusted in save() when creating new object.
    name = models.CharField(max_length=255, blank=True,
            help_text=squeeze(u"""
                Attachment normalization file name, e.g. "document.pdf". Extension automatically 
                adjusted when creating a new object. Empty, if file.name is empty.
                """))

    # May be NULL
    content_type = models.CharField(max_length=255, null=True,
            help_text=squeeze(u"""
                Attachment normalization content type, e.g. "application/pdf". The value may be 
                specified even if normalization failed.
                """))

    # May NOT be NULL; Automatically computed in save() when creating a new object if undefined.
    created = models.DateTimeField(blank=True,
            help_text=squeeze(u"""
                Date and time the attachment was normalized. Leave blank for current time.
                """))

    # May be NULL; Automatically computed in save() when creating a new object.
    size = models.IntegerField(null=True, blank=True,
            help_text=squeeze(u"""
                Attachment normalization file size in bytes. NULL if file is NULL. Automatically 
                computed when creating a new object.
                """))

    # May NOT be NULL
    debug = models.TextField(blank=True,
            help_text=squeeze(u"""
                Debug message from normalization.
                """))

    # Backward relations added to other models:
    #
    #  -- Attachment.attachment_normalization_set
    #     May be empty

    # Indexes:
    #  -- attachment: ForeignKey

    objects = AttachmentNormalizationQuerySet.as_manager()

    @cached_property
    def content(self):
        if not self.file:
            return None
        try:
            self.file.open(u'rb')
            return self.file.read()
        except IOError:
            logger = logging.getLogger(u'chcemvediet.apps.anonymization')
            logger.error(u'{} is missing its file: "{}".'.format(self, self.file.name))
            raise
        finally:
            self.file.close()

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        if self.pk is None:  # Creating a new object
            if self.created is None:
                self.created = utc_now()
            if self.file._file:
                self.file.name = random_string(10)
                self.size = self.file.size
                self.name = adjust_extension(self.attachment.name, self.content_type)
        super(AttachmentNormalization, self).save(*args, **kwargs)

    def __str__(self):
        return format(self.pk)

class AttachmentRecognitionQuerySet(QuerySet):
    def successful(self):
        return self.filter(successful=True)

    def recognized_to_odt(self):
        return self.filter(content_type=content_types.ODT_CONTENT_TYPE)

    def not_anonymized(self):
        return self.filter(attachment__attachmentanonymization__isnull=True)

    def order_by_pk(self):
        return self.order_by(u'pk')

class AttachmentRecognition(FormatMixin, models.Model):

    # May NOT be NULL
    attachment = models.ForeignKey(Attachment, on_delete=models.CASCADE)

    # May NOT be NULL
    successful = models.BooleanField(default=False,
            help_text=squeeze(u"""
                True if recognition has succeeded, False otherwise.
                """))

    # Filename may be empty; Random local filename is generated in save() when creating a new object
    file = models.FileField(upload_to=u'attachment_recognitions', max_length=255, blank=True,
            help_text=squeeze(u"""
                Empty filename if recognition failed.
                """))

    # May be empty: Extension automatically adjusted in save() when creating new object.
    name = models.CharField(max_length=255, blank=True,
            help_text=squeeze(u"""
                Attachment recognition file name, e.g. "document.odt". Extension automatically
                adjusted when creating a new object. Empty, if file.name is empty.
                """))

    # May be NULL
    content_type = models.CharField(max_length=255, null=True,
            help_text=squeeze(u"""
                Attachment recognition content type, e.g. "application/vnd.oasis.opendocument.text".
                The value may be specified even if recognition failed.
                """))

    # May NOT be NULL; Automatically computed in save() when creating a new object if undefined.
    created = models.DateTimeField(blank=True,
            help_text=squeeze(u"""
                Date and time the attachment was recognized. Leave blank for current time.
                """))

    # May be NULL; Automatically computed in save() when creating a new object.
    size = models.IntegerField(null=True, blank=True,
            help_text=squeeze(u"""
                Attachment recognition file size in bytes. NULL if file is NULL. Automatically
                computed when creating a new object.
                """))

    # May NOT be NULL
    debug = models.TextField(blank=True,
            help_text=squeeze(u"""
                Debug message from recognition.
                """))

    # Backward relations added to other models:
    #
    #  -- Attachment.attachment_recognition_set
    #     May be empty

    # Indexes:
    #  -- attachment: ForeignKey

    objects = AttachmentRecognitionQuerySet.as_manager()

    @cached_property
    def content(self):
        if not self.file:
            return None
        try:
            self.file.open(u'rb')
            return self.file.read()
        except IOError:
            logger = logging.getLogger(u'chcemvediet.apps.anonymization')
            logger.error(u'{} is missing its file: "{}".'.format(self, self.file.name))
            raise
        finally:
            self.file.close()

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        if self.pk is None:  # Creating a new object
            if self.created is None:
                self.created = utc_now()
            if self.file._file:
                self.file.name = random_string(10)
                self.size = self.file.size
                self.name = adjust_extension(self.attachment.name, self.content_type)
        super(AttachmentRecognition, self).save(*args, **kwargs)

    def __str__(self):
        return format(self.pk)

class AttachmentAnonymizationQuerySet(QuerySet):
    def successful(self):
        return self.filter(successful=True)

    def anonymized_to_odt(self):
        return self.filter(content_type=content_types.ODT_CONTENT_TYPE)

    def not_finalized(self):
        return self.filter(attachment__attachmentfinalization__isnull=True)

    def order_by_pk(self):
        return self.order_by(u'pk')

    def owned_by(self, user):
        return self.filter(attachment__action__branch__inforequest__applicant=user)

class AttachmentAnonymization(FormatMixin, models.Model):

    # May NOT be NULL
    attachment = models.ForeignKey(Attachment, on_delete=models.CASCADE)

    # May NOT be NULL
    successful = models.BooleanField(default=False,
            help_text=squeeze(u"""
                True if anonymization has succeeded, False otherwise.
                """))

    # Filename may be empty; Random local filename is generated in save() when creating a new object
    file = models.FileField(upload_to=u'attachment_anonymizations', max_length=255, blank=True,
            help_text=squeeze(u"""
                Empty filename if anonymization failed.
                """))

    # May be empty: Extension automatically adjusted in save() when creating new object.
    name = models.CharField(max_length=255, blank=True,
            help_text=squeeze(u"""
                Attachment anonymization file name, e.g. "document.odt". Extension automatically
                adjusted when creating a new object. Empty, if file.name is empty.
                """))

    # May be NULL
    content_type = models.CharField(max_length=255, null=True,
            help_text=squeeze(u"""
                Attachment anonymization content type, e.g.
                "application/vnd.oasis.opendocument.text". The value may be specified even if
                anonymization failed.
                """))

    # May NOT be NULL; Automatically computed in save() when creating a new object if undefined.
    created = models.DateTimeField(blank=True,
            help_text=squeeze(u"""
                Date and time the attachment was anonymized. Leave blank for current time.
                """))

    # May be NULL; Automatically computed in save() when creating a new object.
    size = models.IntegerField(null=True, blank=True,
            help_text=squeeze(u"""
                Attachment anonymization file size in bytes. NULL if file is NULL. Automatically
                computed when creating a new object.
                """))

    # May NOT be NULL
    debug = models.TextField(blank=True,
            help_text=squeeze(u"""
                Debug message from anonymization.
                """))

    # Backward relations added to other models:
    #
    #  -- Attachment.attachment_anonymization_set
    #     May be empty

    # Indexes:
    #  -- attachment: ForeignKey

    objects = AttachmentAnonymizationQuerySet.as_manager()

    @cached_property
    def content(self):
        if not self.file:
            return None
        try:
            self.file.open(u'rb')
            return self.file.read()
        except IOError:
            logger = logging.getLogger(u'chcemvediet.apps.anonymization')
            logger.error(u'{} is missing its file: "{}".'.format(self, self.file.name))
            raise
        finally:
            self.file.close()

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        if self.pk is None:  # Creating a new object
            if self.created is None:
                self.created = utc_now()
            if self.file._file:
                self.file.name = random_string(10)
                self.size = self.file.size
                self.name = adjust_extension(self.attachment.name, self.content_type)
        super(AttachmentAnonymization, self).save(*args, **kwargs)

    def __str__(self):
        return format(self.pk)

class AttachmentFinalizationQuerySet(QuerySet):
    def successful(self):
        return self.filter(successful=True)

    def order_by_pk(self):
        return self.order_by(u'pk')

    def owned_by(self, user):
        return self.filter(attachment__action__branch__inforequest__applicant=user)

class AttachmentFinalization(FormatMixin, models.Model):

    # May NOT be NULL
    attachment = models.ForeignKey(Attachment, on_delete=models.CASCADE)

    # May NOT be NULL
    successful = models.BooleanField(default=False,
            help_text=squeeze(u"""
                True if finalization has succeeded, False otherwise.
                """))

    # Filename may be empty; Random local filename is generated in save() when creating a new object
    file = models.FileField(upload_to=u'attachment_finalizations', max_length=255, blank=True,
            help_text=squeeze(u"""
                Empty filename if finalization failed.
                """))

    # May be empty: Extension automatically adjusted in save() when creating new object.
    name = models.CharField(max_length=255, blank=True,
            help_text=squeeze(u"""
                Attachment finalization file name, e.g. "document.pdf". Extension automatically
                adjusted when creating a new object. Empty, if file.name is empty.
                """))

    # May be NULL
    content_type = models.CharField(max_length=255, null=True,
            help_text=squeeze(u"""
                Attachment finalization content type, e.g. "application/pdf". The value may be
                specified even if finalization failed.
                """))

    # May NOT be NULL; Automatically computed in save() when creating a new object if undefined.
    created = models.DateTimeField(blank=True,
            help_text=squeeze(u"""
                Date and time the attachment was finalized. Leave blank for current time.
                """))

    # May be NULL; Automatically computed in save() when creating a new object.
    size = models.IntegerField(null=True, blank=True,
            help_text=squeeze(u"""
                Attachment finalization file size in bytes. NULL if file is NULL. Automatically
                computed when creating a new object.
                """))

    # May NOT be NULL
    debug = models.TextField(blank=True,
            help_text=squeeze(u"""
                Debug message from finalization.
                """))

    # Backward relations added to other models:
    #
    #  -- Attachment.attachment_finalization_set
    #     May be empty

    # Indexes:
    #  -- attachment: ForeignKey

    objects = AttachmentFinalizationQuerySet.as_manager()

    @cached_property
    def content(self):
        if not self.file:
            return None
        try:
            self.file.open(u'rb')
            return self.file.read()
        except IOError:
            logger = logging.getLogger(u'chcemvediet.apps.anonymization')
            logger.error(u'{} is missing its file: "{}".'.format(self, self.file.name))
            raise
        finally:
            self.file.close()

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        if self.pk is None:  # Creating a new object
            if self.created is None:
                self.created = utc_now()
            if self.file._file:
                self.file.name = random_string(10)
                self.size = self.file.size
                self.name = adjust_extension(self.attachment.name, self.content_type)
        super(AttachmentFinalization, self).save(*args, **kwargs)

    def __str__(self):
        return format(self.pk)


@datacheck.register
def datachecks_AttachmentNormalization(superficial, autofix):
    u"""
    Checks that every ``AttachmentNormalization`` instance, which file is not NULL, has its file
    working, and there are not any orphaned attachment_normalization files.
    """
    # This check is a bit slow. We skip it if running from cron or the user asked for superficial
    # tests only.
    if superficial:
        return []
    attachment_normalizations = AttachmentNormalization.objects.all()
    field = AttachmentNormalization._meta.get_field(u'file')
    return itertools.chain(
        attachment_file_check(attachment_normalizations),
        attachment_orphaned_file_check(attachment_normalizations, field, AttachmentNormalization),
    )

@datacheck.register
def datachecks_AttachmentRecognition(superficial, autofix):
    u"""
    Checks that every ``AttachmentRecognition`` instance, which file is not NULL, has its file
    working, and there are not any orphaned attachment_recognition files.
    """
    # This check is a bit slow. We skip it if running from cron or the user asked for superficial
    # tests only.
    if superficial:
        return []
    attachment_recognitions = AttachmentRecognition.objects.all()
    field = AttachmentRecognition._meta.get_field(u'file')
    return itertools.chain(
        attachment_file_check(attachment_recognitions),
        attachment_orphaned_file_check(attachment_recognitions, field, AttachmentRecognition),
    )

@datacheck.register
def datachecks_AttachmentAnonymization(superficial, autofix):
    u"""
    Checks that every ``AttachmentAnonymization`` instance, which file is not NULL, has its file
    working, and there are not any orphaned attachment_anonymization files.
    """
    # This check is a bit slow. We skip it if running from cron or the user asked for superficial
    # tests only.
    if superficial:
        return []
    attachment_anonymization = AttachmentAnonymization.objects.all()
    field = AttachmentAnonymization._meta.get_field(u'file')
    return itertools.chain(
        attachment_file_check(attachment_anonymization),
        attachment_orphaned_file_check(attachment_anonymization, field, AttachmentAnonymization),
    )

@datacheck.register
def datachecks_AttachmentFinalization(superficial, autofix):
    u"""
    Checks that every ``AttachmentFinalization`` instance, which file is not NULL, has its file
    working, and there are not any orphaned attachment_finalization files.
    """
    # This check is a bit slow. We skip it if running from cron or the user asked for superficial
    # tests only.
    if superficial:
        return []
    attachment_finalization = AttachmentFinalization.objects.all()
    field = AttachmentFinalization._meta.get_field(u'file')
    return itertools.chain(
        attachment_file_check(attachment_finalization),
        attachment_orphaned_file_check(attachment_finalization, field, AttachmentFinalization),
    )
