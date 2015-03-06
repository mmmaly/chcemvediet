# vim: expandtab
# -*- coding: utf-8 -*-
import re
from unidecode import unidecode
from email.utils import formataddr, getaddresses

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape

from poleno.utils.models import FieldChoices, QuerySet
from poleno.utils.forms import validate_comma_separated_emails
from poleno.utils.history import register_history
from poleno.utils.misc import squeeze, decorate

class ObligeeQuerySet(QuerySet):
    def pending(self):
        return self.filter(status=Obligee.STATUSES.PENDING)
    def order_by_pk(self):
        return self.order_by(u'pk')
    def order_by_name(self):
        return self.order_by(u'name', u'pk')

@register_history
class Obligee(models.Model):
    # Should NOT be empty; For index see index_together
    name = models.CharField(max_length=255)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    zip = models.CharField(max_length=10)

    # Should NOT be empty
    emails = models.CharField(max_length=1024,
            validators=[validate_comma_separated_emails],
            help_text=escape(squeeze(u"""
                Comma separated list of e-mails. E.g. 'John <john@example.com>,
                another@example.com, "Smith, Jane" <jane.smith@example.com>'
                """)))

    # Should NOT be empty; Read-only; Automaticly computed in save() whenever creating a new object
    # or changing its name. Any user defined value is replaced.
    slug = models.SlugField(max_length=255, db_index=False,
            help_text=squeeze(u"""
                Slug for full-text search. Automaticly computed whenever creating a new object or
                changing its name. Any user defined value is replaced.
                """))

    # May NOT be NULL
    STATUSES = FieldChoices(
            (u'PENDING', 1, _(u'obligees:Obligee:status:PENDING')),
            (u'DISSOLVED', 2, _(u'obligees:Obligee:status:DISSOLVED')),
            )
    status = models.SmallIntegerField(choices=STATUSES._choices,
            help_text=squeeze(u"""
                "Pending" for obligees that exist and accept inforequests; "Dissolved" for obligees
                that do not exist any more and no further inforequests may be submitted to them.
                """))

    # Added by ``@register_history``:
    #  -- history: simple_history.manager.HistoryManager
    #     Returns instance historical snapshots as HistoricalObligee model.

    objects = ObligeeQuerySet.as_manager()

    class Meta:
        # FIXME: Ordinary indexes do not work for LIKE '%word%'. So we don't declare any indexes
        # for ``slug`` yet. Eventually, we need to define a fulltext index for "slug" or "name" and
        # use ``__search`` instead of ``__contains`` in autocomplete view. However, SQLite does not
        # support ``__contains`` and MySQL supports fulltext indexes for InnoDB tables only since
        # version 5.6.4, but our server has only MySQL 5.5.x so far. We need to upgrate our
        # production MySQL server and find a workaround for SQLite we use in development mode.
        # Alternatively, we can use some complex fulltext search engine like ElasticSearch.
        index_together = [
                [u'name', u'id'],
                ]

    @property
    def emails_parsed(self):
        return ((n, a) for n, a in getaddresses([self.emails]) if a)

    @property
    def emails_formatted(self):
        return (formataddr((n, a)) for n, a in getaddresses([self.emails]) if a)

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        update_fields = kwargs.get(u'update_fields', None)

        # Generate and save slug if saving name
        if update_fields is None or u'name' in update_fields:
            name = unidecode(self.name).lower()
            words = (w for w in re.split(r'[^a-z0-9]+', name) if w)
            self.slug = u'-%s-' % u'-'.join(words)

            if update_fields is not None:
                update_fields.append(u'slug')

        super(Obligee, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % self.pk
