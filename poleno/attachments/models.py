# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _

from poleno.utils.models import QuerySet
from poleno.utils.date import utc_now
from poleno.utils.misc import random_string

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

class Attachment(models.Model):
    # May NOT be NULL; Generic relation
    generic_type = models.ForeignKey(ContentType)
    generic_id = models.PositiveIntegerField()
    generic_object = generic.GenericForeignKey(u'generic_type', u'generic_id')

    # May NOT be NULL; Random local filename is generated in save() when creating a new object.
    file = models.FileField(upload_to=u'attachments', max_length=255, verbose_name=_(u'File'))

    # May be empty; May NOT be trusted, set by client.
    name = models.CharField(max_length=255, verbose_name=_(u'Name'))
    content_type = models.CharField(max_length=255, verbose_name=_(u'Content Type'))

    # May NOT be NULL; Automaticly computed in save() when creating a new object if undefined.
    created = models.DateTimeField(verbose_name=_(u'Created'))

    # May NOT by NULL; Atomatically computed in save() when creating a new object.
    size = models.IntegerField(verbose_name=_(u'Size'))

    objects = AttachmentQuerySet.as_manager()

    class Meta:
        ordering = [u'pk']

    # May be empty; Read-only
    @property
    def content(self):
        try:
            self.file.open(u'rb')
            return self.file.read()
        finally:
            self.file.close()

    def save(self, *args, **kwargs):
        if self.pk is None: # Creating a new object
            self.file.name = random_string(10)
            if self.created is None:
                self.created = utc_now()
            self.size = self.file.size

        super(Attachment, self).save(*args, **kwargs)

    def clone(self):
        u""" The returned copy is not saved. """
        return Attachment(
                generic_object=self.generic_object,
                file=ContentFile(self.content),
                name=self.name,
                content_type=self.content_type,
                created=self.created,
                )

    def __unicode__(self):
        return u'%s' % self.pk
