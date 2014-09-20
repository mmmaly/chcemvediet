# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from poleno.utils.models import QuerySet
from poleno.utils.misc import random_string

class AttachmentQuerySet(QuerySet):
    def owned_by(self, user):
        return self.filter(owner=user)

class Attachment(models.Model):
    # FIXME: Unused uploaded files are not deleted, yet. We need cron stript to delete files
    # uploaded long ago, but never (or not any more) used.

    # Mandatory
    owner = models.ForeignKey(User, verbose_name=_(u'Owner'))

    # Mandatory; Random local filename is generated in save() when creating a new object.
    file = models.FileField(upload_to=u'attachments', max_length=255, verbose_name=_(u'File'))

    # May be empty; May not be trusted, set by client.
    name = models.CharField(max_length=255, verbose_name=_(u'Name'))
    content_type = models.CharField(max_length=255, verbose_name=_(u'Content Type'))

    # Mandatory
    size = models.IntegerField(verbose_name=_(u'Size'))

    objects = AttachmentQuerySet.as_manager()

    class Meta:
        ordering = [u'pk']

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

        super(Attachment, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % self.pk

