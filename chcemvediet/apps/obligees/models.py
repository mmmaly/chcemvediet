# vim: expandtab
# -*- coding: utf-8 -*-
from email.utils import formataddr, getaddresses

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape
from django.utils.functional import cached_property

from poleno import datacheck
from poleno.utils.models import FieldChoices, QuerySet
from poleno.utils.forms import validate_comma_separated_emails
from poleno.utils.history import register_history
from poleno.utils.misc import FormatMixin, squeeze, decorate, slugify
from chcemvediet.apps.geounits.models import Neighbourhood


class ObligeeTagQuerySet(QuerySet):
    def order_by_pk(self):
        return self.order_by(u'pk')
    def order_by_key(self):
        return self.order_by(u'key') # no tiebreaker, key is unique
    def order_by_name(self):
        return self.order_by(u'name') # no tiebreaker, name is unique

class ObligeeTag(FormatMixin, models.Model):
    # May NOT be empty
    key = models.CharField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique key to identify the tag. Should contain only alphanumeric characters,
                underscores and hyphens.
                """))

    # Should NOT be empty
    name = models.CharField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique human readable tag name.
                """))

    # Should NOT be empty; Read-only; Automaticly computed in save()
    slug = models.SlugField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique slug to identify the tag used in urls. Automaticly computed from the tag
                name. May not be changed manually.
                """))

    # Backward relations:
    #
    #  -- obligee_set: by Obligee.tags
    #     May be empty

    # Indexes:
    #  -- key:  unique
    #  -- name: unique
    #  -- slug: unique

    objects = ObligeeTagQuerySet.as_manager()

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        update_fields = kwargs.get(u'update_fields', None)

        # Generate and save slug if saving name
        if update_fields is None or u'name' in update_fields:
            self.slug = slugify(self.name)
            if update_fields is not None:
                update_fields.append(u'slug')

        super(ObligeeTag, self).save(*args, **kwargs)

    def __str__(self):
        return u'[{}] {}'.format(self.pk, self.key)


class ObligeeGroupQuerySet(QuerySet):
    def order_by_pk(self):
        return self.order_by(u'pk')
    def order_by_key(self):
        return self.order_by(u'key') # no tiebreaker, key is unique
    def order_by_name(self):
        return self.order_by(u'name') # no tiebreaker, name is unique

class ObligeeGroup(FormatMixin, models.Model):
    # May NOT be empty
    key = models.CharField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique key to identify the group. The key is a path of slash separated words each
                of which represents a parent group. Every word in the path should be a nonempty
                string and should only contain alphanumeric characters, underscores and hyphens.
                """))

    # Should NOT be empty
    name = models.CharField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique human readable group name.
                """))

    # Should NOT be empty; Read-only; Automaticly computed in save()
    slug = models.SlugField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique slug to identify the group used in urls. Automaticly computed from the group
                name. May not be changed manually.
                """))

    # May be empty
    description = models.TextField(blank=True,
            help_text=squeeze(u"""
                Human readable group description.
                """))

    # Backward relations:
    #
    #  -- obligee_set: by Obligee.groups
    #     May be empty

    # Indexes:
    #  -- key:  unique
    #  -- name: unique
    #  -- slug: unique

    objects = ObligeeGroupQuerySet.as_manager()

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        update_fields = kwargs.get(u'update_fields', None)

        # Generate and save slug if saving name
        if update_fields is None or u'name' in update_fields:
            self.slug = slugify(self.name)
            if update_fields is not None:
                update_fields.append(u'slug')

        super(ObligeeGroup, self).save(*args, **kwargs)

    def __str__(self):
        return u'[{}] {}'.format(self.pk, self.key)


class ObligeeQuerySet(QuerySet):
    def pending(self):
        return self.filter(status=Obligee.STATUSES.PENDING)
    def order_by_pk(self):
        return self.order_by(u'pk')
    def order_by_name(self):
        return self.order_by(u'name') # no tiebreaker, name is unique

@register_history
class Obligee(FormatMixin, models.Model):
    # FIXME: Ordinary indexes do not work for LIKE '%word%'. So we can't use the slug index for
    # searching. Eventually, we need to define a fulltext index for "slug" or "name" and use
    # ``__search`` instead of ``__contains`` in autocomplete view. However, SQLite does not support
    # ``__contains`` and MySQL supports fulltext indexes for InnoDB tables only since version
    # 5.6.4, but our server has only MySQL 5.5.x so far. We need to upgrate our production MySQL
    # server and find a workaround for SQLite we use in development mode. Alternatively, we can use
    # some complex fulltext search engine like ElasticSearch.

    # Should NOT be empty
    official_name = models.CharField(max_length=255, help_text=u'Official obligee name.')

    # Should NOT be empty
    name = models.CharField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique human readable obligee name. If official obligee name is ambiguous, it
                should be made more specific.
                """))

    # Should NOT be empty; Read-only; Automaticly computed in save()
    slug = models.SlugField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique slug to identify the obligee used in urls. Automaticly computed from the
                obligee name. May not be changed manually.
                """))

    # Should NOT be empty
    name_genitive = models.CharField(max_length=255, help_text=u'Genitive of obligee name.')
    name_dative = models.CharField(max_length=255, help_text=u'Dative of obligee name.')
    name_accusative = models.CharField(max_length=255, help_text=u'Accusative of obligee name.')
    name_locative = models.CharField(max_length=255, help_text=u'Locative of obligee name.')
    name_instrumental = models.CharField(max_length=255, help_text=u'Instrumental of obligee name.')

    # May NOT be NULL
    GENDERS = FieldChoices(
            (u'MASCULINE', 1, _(u'obligees:Obligee:gender:MASCULINE')),
            (u'FEMININE',  2, _(u'obligees:Obligee:gender:FEMININE')),
            (u'NEUTER',    3, _(u'obligees:Obligee:gender:NEUTER')),
            (u'PLURALE',   4, _(u'obligees:Obligee:gender:PLURALE')), # Pomnožné
            )
    gender = models.SmallIntegerField(choices=GENDERS._choices,
            help_text=u'Obligee name grammar gender.')

    # May be empty
    ico = models.CharField(blank=True, max_length=32,
            help_text=u'Legal identification number if known.')

    # Should NOT be empty
    street = models.CharField(max_length=255,
            help_text=u'Street and number part of postal address.')
    city = models.CharField(max_length=255,
            help_text=u'City part of postal address.')
    zip = models.CharField(max_length=10,
            help_text=u'Zip part of postal address.')

    # May NOT be NULL
    iczsj = models.ForeignKey(Neighbourhood, on_delete=models.CASCADE,
            help_text=u'City neighbourhood the obligee address is in.')

    # May be empty
    emails = models.CharField(blank=True, max_length=1024,
            validators=[validate_comma_separated_emails],
            help_text=escape(squeeze(u"""
                Comma separated list of e-mails. E.g. 'John <john@example.com>,
                another@example.com, "Smith, Jane" <jane.smith@example.com>'. Empty the email
                address is unknown.
                """)))

    # May be NULL
    latitude = models.FloatField(null=True, blank=True, help_text=u'Obligee GPS latitude')
    longitude = models.FloatField(null=True, blank=True, help_text=u'Obligee GPS longitude')

    # May be empty
    tags = models.ManyToManyField(ObligeeTag, blank=True)
    groups = models.ManyToManyField(ObligeeGroup, blank=True)

    # May NOT be NULL
    TYPES = FieldChoices(
            (u'SECTION_1', 1, _(u'obligees:Obligee:type:SECTION_1')),
            (u'SECTION_2', 2, _(u'obligees:Obligee:type:SECTION_2')),
            (u'SECTION_3', 3, _(u'obligees:Obligee:type:SECTION_3')),
            (u'SECTION_4', 4, _(u'obligees:Obligee:type:SECTION_4')),
            )
    type = models.SmallIntegerField(choices=TYPES._choices,
            help_text=squeeze(u"""
                Obligee type according to §2. Obligees defined in section 3 are obliged to disclose
                some information only.
                """))

    # May be empty
    official_description = models.TextField(blank=True,
            help_text=u'Official obligee description.')
    simple_description = models.TextField(blank=True,
            help_text=u'Human readable obligee description.')

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

    # May be empty
    notes = models.TextField(blank=True,
            help_text=u'Internal freetext notes. Not shown to the user.')

    # Backward relations:
    #
    #  -- history: HistoryManager added by @register_history
    #     Returns instance historical snapshots as HistoricalObligee model.
    #
    #  -- obligeealias_set: by ObligeeAlias.obligee
    #     May be empty
    #
    #  -- branch_set: by Branch.obligee
    #     May be empty
    #
    #  -- inforequestdraft_set: by InforequestDraft.obligee
    #     May be empty

    # Backward relations added to other models:
    #
    #  -- ObligeeTag.obligee_set
    #     May be empty
    #
    #  -- ObligeeGroup.obligee_set
    #     May be empty

    # Indexes:
    #  -- name: unique
    #  -- slug: unique

    objects = ObligeeQuerySet.as_manager()

    @staticmethod
    def dummy_email(name, tpl):
        slug = slugify(name)[:30].strip(u'-')
        return tpl.format(name=slug)

    @cached_property
    def emails_parsed(self):
        return [(n, a) for n, a in getaddresses([self.emails]) if a]

    @cached_property
    def emails_formatted(self):
        return [formataddr((n, a)) for n, a in getaddresses([self.emails]) if a]

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        update_fields = kwargs.get(u'update_fields', None)

        # Generate and save slug if saving name
        if update_fields is None or u'name' in update_fields:
            self.slug = slugify(self.name)
            if update_fields is not None:
                update_fields.append(u'slug')

        super(Obligee, self).save(*args, **kwargs)

    def __str__(self):
        return u'[{}] {}'.format(self.pk, self.name)


class ObligeeAliasQuerySet(QuerySet):
    def order_by_pk(self):
        return self.order_by(u'pk')
    def order_by_alias(self):
        return self.order_by(u'name') # no tiebreaker, name is unique

class ObligeeAlias(FormatMixin, models.Model):
    # May NOT be NULL
    obligee = models.ForeignKey(Obligee, on_delete=models.CASCADE, help_text=u'Obligee of which this is alias.')

    # Should NOT be empty
    name = models.CharField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique human readable obligee alias if the obligee has multiple common names.
                """))

    # Should NOT be empty; Read-only; Automaticly computed in save()
    slug = models.SlugField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique slug to identify the obligee alias used in urls. Automaticly computed from
                the obligee name. May not be changed manually.
                """))

    # May be empty
    description = models.TextField(blank=True, help_text=u'Obligee alias description.')

    # May be empty
    notes = models.TextField(blank=True,
            help_text=u'Internal freetext notes. Not shown to the user.')

    # Backward relations added to other models:
    #
    #  -- Obligee.obligeealias_set
    #     May be empty

    # Indexes:
    #  -- obligee: ForeignKey
    #  -- name:    unique
    #  -- slug:    unique

    objects = ObligeeAliasQuerySet.as_manager()

    class Meta:
        verbose_name_plural = u'obligee aliases'

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        update_fields = kwargs.get(u'update_fields', None)

        # Generate and save slug if saving name
        if update_fields is None or u'name' in update_fields:
            self.slug = slugify(self.name)
            if update_fields is not None:
                update_fields.append(u'slug')

        super(ObligeeAlias, self).save(*args, **kwargs)

    def __str__(self):
        return u'[{}] {}'.format(self.pk, self.name)


@datacheck.register
def datachecks(superficial, autofix):
    u"""
    Checks that all obligee subgroups have their parent groups.
    """
    groups = ObligeeGroup.objects.all()
    keys = set(g.key for g in groups)
    for group in groups:
        if u'/' not in group.key:
            continue
        parent_key = group.key.rsplit(u'/', 1)[0]
        if parent_key not in keys:
            yield datacheck.Error(u'{} has key="{}" but thare is no group with key="{}"',
                    group, group.key, parent_key)
