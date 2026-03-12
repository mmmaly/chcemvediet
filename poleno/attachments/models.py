# vim: expandtab
# -*- coding: utf-8 -*-
import logging
import itertools

import magic
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Q
from django.utils.functional import cached_property
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from poleno import datacheck
from poleno.attachments.utils import attachment_file_check, attachment_orphaned_file_check
from poleno.utils.models import QuerySet
from poleno.utils.date import utc_now
from poleno.utils.misc import FormatMixin, random_string, squeeze, decorate, sanitize_filename


class AttachmentQuerySet(QuerySet):
    def attached_to(self, *args):
        u"""
        Filter attachments attached to any of given arguments. As an argument you may pass:
         -- model instance: filters attachments attached to the instance;
         -- model class: filters attachments attached to any instance of the model;
         -- queryset: filters attachments attached to any of the objects returned by the queryset.
        """
        q = []
        for arg in args:
            if isinstance(arg, models.query.QuerySet):
                content_type = ContentType.objects.get_for_model(arg.model)
                q.append(Q(generic_type=content_type, generic_id__in=arg.values(u'pk')))
            elif isinstance(arg, models.Model):
                content_type = ContentType.objects.get_for_model(arg.__class__)
                q.append(Q(generic_type=content_type, generic_id=arg.pk))
            elif isinstance(arg, type) and issubclass(arg, models.Model):
                content_type = ContentType.objects.get_for_model(arg)
                q.append(Q(generic_type=content_type))
            else:
                raise TypeError(u'Expecting QuerySet, Model instance, or Model class.')
        q = reduce((lambda a, b: a | b), q, Q())
        return self.filter(q)

    def not_normalized(self):
        return self.filter(attachmentnormalization__isnull=True)

    def order_by_pk(self):
        return self.order_by(u'pk')

class Attachment(FormatMixin, models.Model):
    # May NOT be NULL; Generic relation; Index is prefix of [generic_type, generic_id] index
    generic_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, db_index=False)
    generic_id = models.CharField(max_length=255)
    generic_object = GenericForeignKey(u'generic_type', u'generic_id')

    # May NOT be NULL; Random local filename is generated in save() when creating a new object.
    file = models.FileField(upload_to=u'attachments', max_length=255)

    # May NOT be empty; Automatically sanitized in save() when creating a new object.
    name = models.CharField(max_length=255,
            help_text=squeeze(u"""
                Attachment file name, e.g. "document.pdf". Automatically sanitized when creating
                a new object.
                """))

    # May NOT be empty; Automatically computed in save() when creating a new object.
    content_type = models.CharField(max_length=255,
            help_text=squeeze(u"""
                Attachment content type, e.g. "application/pdf". Automatically computed when
                creating a new object.
                """))

    # May NOT be NULL; Automatically computed in save() when creating a new object if undefined.
    created = models.DateTimeField(blank=True,
            help_text=squeeze(u"""
                Date and time the attachment was uploaded or received by an email. Leave blank for
                current time.
                """))

    # May NOT by NULL; Automatically computed in save() when creating a new object.
    size = models.IntegerField(blank=True,
            help_text=squeeze(u"""
                Attachment file size in bytes. Automatically computed when creating a new object.
                """))

    # Indexes:
    #  -- generic_type, generic_id: index_together

    objects = AttachmentQuerySet.as_manager()

    class Meta:
        index_together = [
                [u'generic_type', u'generic_id'],
                ]

    @cached_property
    def content(self):
        try:
            self.file.open(u'rb')
            return self.file.read()
        except IOError:
            logger = logging.getLogger(u'poleno.attachments')
            logger.error(u'{} is missing its file: "{}".'.format(self, self.file.name))
            raise
        finally:
            self.file.close()

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        if self.pk is None: # Creating a new object
            self.file.name = random_string(10)
            if self.created is None:
                self.created = utc_now()
            self.size = self.file.size
            self.content_type = magic.from_buffer(self.file.read(), mime=True)
            self.name = sanitize_filename(self.name, self.content_type)
        super(Attachment, self).save(*args, **kwargs)

    def clone(self, generic_object):
        u""" The returned copy is not saved. """
        return Attachment(
                generic_object=generic_object,
                file=ContentFile(self.content),
                name=self.name,
                created=self.created,
                )

    def __str__(self):
        return format(self.pk)

@datacheck.register
def datachecks(superficial, autofix):
    u"""
    Checks that every ``Attachment`` instance has its file working, and there are not any orphaned
    attachment files.
    """
    # This check is a bit slow. We skip it if running from cron or the user asked for superficial
    # tests only.
    if superficial:
        return []
    attachments = Attachment.objects.all()
    field = Attachment._meta.get_field(u'file')
    return itertools.chain(
        attachment_file_check(attachments),
        attachment_orphaned_file_check(attachments, field, Attachment),
    )
