# vim: expandtab
# -*- coding: utf-8 -*-
from email.utils import formataddr, getaddresses

from django.db import models
from django.utils.translation import ugettext_lazy as _

from poleno.utils.models import FieldChoices, QuerySet
from poleno.utils.history import register_history

class ObligeeQuerySet(QuerySet):
    def pending(self):
        return self.filter(status=Obligee.STATUSES.PENDING)

@register_history
class Obligee(models.Model):
    # May NOT be empty
    name = models.CharField(max_length=255, verbose_name=_(u'Name'))
    street = models.CharField(max_length=255, verbose_name=_(u'Street'))
    city = models.CharField(max_length=255, verbose_name=_(u'City'))
    zip = models.CharField(max_length=10, verbose_name=_(u'Zip'))

    # May NOT be empty
    emails = models.CharField(max_length=1024, verbose_name=_(u'E-mail'),
            help_text=_(u"""Comma separated list of e-mails. E.g. 'John <john@example.com>, another@example.com, "Smith, Jane" <jane.smith@example.com>'"""))

    # May NOT be empty
    slug = models.SlugField(max_length=255, verbose_name=_(u'Slug'))

    # May NOT be NULL
    STATUSES = FieldChoices(
            (u'PENDING', 1, _(u'Pending')),
            (u'DISSOLVED', 2, _(u'Dissolved')),
            )
    status = models.SmallIntegerField(choices=STATUSES._choices, verbose_name=_(u'Status'))

    # Added by ``@register_history``:
    #  -- history: simple_history.manager.HistoryManager
    #     Returns instance historical snapshots as HistoricalObligee model.

    objects = ObligeeQuerySet.as_manager()

    class Meta:
        ordering = [u'name']

    # May NOT be empty; Read-only
    @property
    def emails_parsed(self):
        return getaddresses([self.emails])

    # May NOT be empty; Read-only
    @property
    def emails_formatted(self):
        return (formataddr(a) for a in getaddresses([self.emails]))

    def __unicode__(self):
        return u'%s' % self.pk
