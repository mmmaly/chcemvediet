# vim: expandtab
# -*- coding: utf-8 -*-
from email.utils import formataddr, parseaddr

from django.db import models
from django.utils.translation import ugettext_lazy as _

from jsonfield import JSONField

from poleno.utils.models import FieldChoices, QuerySet
from poleno.utils.misc import random_string

class MessageQuerySet(QuerySet):
    def inbound(self):
        return self.filter(type=Message.TYPES.INBOUND)
    def outbound(self):
        return self.filter(type=Message.TYPES.OUTBOUND)
    def processed(self):
        return self.filter(processed__isnull=False)
    def not_processed(self):
        return self.filter(processed__isnull=True)

class Message(models.Model):
    # Mandatory choice
    TYPES = FieldChoices(
            (u'INBOUND', 1, _(u'Inbound')),
            (u'OUTBOUND', 2, _(u'Outbound')),
            )
    type = models.SmallIntegerField(choices=TYPES._choices, verbose_name=_(u'Type'))

    # Mandatory for processed messages; NULL for queued messages
    processed = models.DateTimeField(blank=True, null=True, verbose_name=_(u'Processed'))

    # May be empty
    from_name = models.CharField(blank=True, max_length=255, verbose_name=_(u'From Name'))

    # Mandatory
    from_mail = models.CharField(max_length=255, verbose_name=_(u'From E-mail'))

    # Should NOT be empty
    subject = models.CharField(blank=True, max_length=255, verbose_name=_(u'Subject'))

    # At least one should NOT be empty
    text = models.TextField(blank=True, verbose_name=_(u'Text Content'))
    html = models.TextField(blank=True, verbose_name=_(u'HTML Content'))

    # Dict: String->String; May be empty
    headers = JSONField(default={}, verbose_name=_(u'Headers'))

    # Backward relations:
    #
    #  -- recipient_set: by Recipient.message
    #     Should NOT be empty
    #
    #  -- attachment_set: by Attachment.message
    #     May be empty

    objects = MessageQuerySet.as_manager()

    class Meta:
        ordering = [u'processed', u'pk']

    def __unicode__(self):
        return u'%s' % self.pk

    @property
    def from_full(self):
        return formataddr((self.from_name, self.from_mail))

    @from_full.setter
    def from_full(self, value):
        self.from_name, self.from_mail = parseaddr(value)

    @property
    def to_full(self):
        return u', '.join(r.full for r in self.recipient_set.to())

    @property
    def cc_full(self):
        return u', '.join(r.full for r in self.recipient_set.cc())

    @property
    def bcc_full(self):
        return u', '.join(r.full for r in self.recipient_set.bcc())

class RecipientQuerySet(QuerySet):
    def to(self):
        return self.filter(type=Recipient.TYPES.TO)
    def cc(self):
        return self.filter(type=Recipient.TYPES.CC)
    def bcc(self):
        return self.filter(type=Recipient.TYPES.BCC)

class Recipient(models.Model):
    # Mandatory
    message = models.ForeignKey(u'Message', verbose_name=_(u'Message'))

    # May be empty
    name = models.CharField(blank=True, max_length=255, verbose_name=_(u'Name'))

    # Mandatory
    mail = models.CharField(max_length=255, verbose_name=_(u'E-mail'))

    # Mandatory choice
    TYPES = FieldChoices(
            (u'TO', 1, _(u'To')),
            (u'CC', 2, _(u'Cc')),
            (u'BCC', 3, _(u'Bcc')),
            )
    type = models.SmallIntegerField(choices=TYPES._choices, verbose_name=_(u'Type'))

    # Mandatory choice
    STATUSES = FieldChoices(
            (u'INBOUND', 8, _(u'Inbound')),
            (u'UNDEFINED', 1, _(u'Undefined')),
            (u'QUEUED', 2, _(u'Queued')),
            (u'REJECTED', 3, _(u'Rejected')),
            (u'INVALID', 4, _(u'Invalid')),
            (u'SENT', 5, _(u'Sent')),
            (u'DELIVERED', 6, _(u'Delivered')),
            (u'OPENED', 7, _(u'Opened')),
            )
    status = models.SmallIntegerField(choices=STATUSES._choices, verbose_name=_(u'Status'))

    # May be empty
    status_details = models.CharField(blank=True, max_length=255, verbose_name=_(u'Status Details'))

    # May be empty
    remote_id = models.CharField(blank=True, max_length=255, verbose_name=_(u'Remote ID'))

    objects = RecipientQuerySet.as_manager()

    class Meta:
        ordering = [u'pk']

    def __unicode__(self):
        return u'%s' % self.pk

    @property
    def full(self):
        return formataddr((self.name, self.mail))

    @full.setter
    def full(self, value):
        self.name, self.mail = parseaddr(value)

class Attachment(models.Model):
    # Mandatory
    message = models.ForeignKey(u'Message', verbose_name=_(u'Message'))

    # Mandatory; Random local filename is generated in save() when creating a new object.
    file = models.FileField(upload_to=u'mail_attachments', max_length=255, verbose_name=_(u'File'))

    # May be empty; May not be trusted, set by the mail sender.
    name = models.CharField(max_length=255, verbose_name=_(u'Name'))
    content_type = models.CharField(max_length=255, verbose_name=_(u'Content Type'))

    objects = QuerySet.as_manager()

    class Meta:
        ordering = [u'pk']

    def __unicode__(self):
        return u'%s' % self.pk

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
