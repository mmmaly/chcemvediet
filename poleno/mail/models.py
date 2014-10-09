# vim: expandtab
# -*- coding: utf-8 -*-
from email.utils import formataddr, parseaddr

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes import generic

from jsonfield import JSONField

from poleno.utils.models import FieldChoices, QuerySet

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
    # May NOT be NULL
    TYPES = FieldChoices(
            (u'INBOUND', 1, _(u'Inbound')),
            (u'OUTBOUND', 2, _(u'Outbound')),
            )
    type = models.SmallIntegerField(choices=TYPES._choices, verbose_name=_(u'Type'))

    # May NOT be NULL for processed messages; NULL for queued messages
    processed = models.DateTimeField(blank=True, null=True, verbose_name=_(u'Processed'))

    # May be empty
    from_name = models.CharField(blank=True, max_length=255, verbose_name=_(u'From Name'))

    # Should NOT be empty
    from_mail = models.CharField(max_length=255, verbose_name=_(u'From E-mail'))

    # May be empty for inbound messages; Empty for outbound messages
    received_for = models.CharField(blank=True, max_length=255, verbose_name=_(u'Received for'))

    # May be empty
    subject = models.CharField(blank=True, max_length=255, verbose_name=_(u'Subject'))

    # May be empty
    text = models.TextField(blank=True, verbose_name=_(u'Text Content'))
    html = models.TextField(blank=True, verbose_name=_(u'HTML Content'))

    # Dict: String->(String|[String]); May be empty
    headers = JSONField(default={}, verbose_name=_(u'Headers'))

    # May be empty; Backward generic relation
    attachment_set = generic.GenericRelation(u'attachments.Attachment', content_type_field=u'generic_type', object_id_field=u'generic_id', verbose_name=_(u'Attachment Set'))

    # Backward relations:
    #
    #  -- recipient_set: by Recipient.message
    #     Should NOT be empty

    objects = MessageQuerySet.as_manager()

    class Meta:
        ordering = [u'processed', u'pk']

    def __unicode__(self):
        return u'%s' % self.pk

    # May be empty; Read-write
    @property
    def from_formatted(self):
        return formataddr((self.from_name, self.from_mail))

    @from_formatted.setter
    def from_formatted(self, value):
        self.from_name, self.from_mail = parseaddr(value)

    @property
    def to_formatted(self):
        return u', '.join(r.formatted for r in self.recipient_set.to())

    @property
    def cc_formatted(self):
        return u', '.join(r.formatted for r in self.recipient_set.cc())

    @property
    def bcc_formatted(self):
        return u', '.join(r.formatted for r in self.recipient_set.bcc())

class RecipientQuerySet(QuerySet):
    def to(self):
        return self.filter(type=Recipient.TYPES.TO)
    def cc(self):
        return self.filter(type=Recipient.TYPES.CC)
    def bcc(self):
        return self.filter(type=Recipient.TYPES.BCC)

class Recipient(models.Model):
    # May NOT be NULL
    message = models.ForeignKey(u'Message', verbose_name=_(u'Message'))

    # May be empty
    name = models.CharField(blank=True, max_length=255, verbose_name=_(u'Name'))

    # May NOT be empty
    mail = models.CharField(max_length=255, verbose_name=_(u'E-mail'))

    # May NOT be NULL
    TYPES = FieldChoices(
            (u'TO', 1, _(u'To')),
            (u'CC', 2, _(u'Cc')),
            (u'BCC', 3, _(u'Bcc')),
            )
    type = models.SmallIntegerField(choices=TYPES._choices, verbose_name=_(u'Type'))

    # May NOT be NULL
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

    # May be empty; Read-write
    @property
    def formatted(self):
        return formataddr((self.name, self.mail))

    @formatted.setter
    def formatted(self, value):
        self.name, self.mail = parseaddr(value)
