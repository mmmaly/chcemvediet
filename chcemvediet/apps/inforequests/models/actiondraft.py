# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Prefetch
from django.utils.functional import cached_property
from django.contrib.contenttypes import generic
from multiselectfield import MultiSelectField

from poleno.attachments.models import Attachment
from poleno.utils.models import QuerySet, join_lookup

from chcemvediet.apps.obligees.models import Obligee

from .action import Action

class ActionDraftQuerySet(QuerySet):
    def order_by_pk(self):
        return self.order_by(u'pk')

class ActionDraft(models.Model):
    # May NOT be NULL
    inforequest = models.ForeignKey(u'Inforequest')

    # May be NULL; Must be owned by the inforequest if set
    branch = models.ForeignKey(u'Branch', blank=True, null=True,
            help_text=u'Must be owned by inforequest if set')

    # May NOT be NULL
    TYPES = Action.TYPES
    type = models.SmallIntegerField(choices=TYPES._choices)

    # May be empty
    subject = models.CharField(blank=True, max_length=255)
    content = models.TextField(blank=True)

    # May be empty
    attachment_set = generic.GenericRelation(u'attachments.Attachment', content_type_field=u'generic_type', object_id_field=u'generic_id')

    # May be NULL
    effective_date = models.DateField(blank=True, null=True)

    # May be NULL for EXTENSION; Must be NULL otherwise
    deadline = models.IntegerField(blank=True, null=True,
            help_text=u'Optional for extension actions. Must be NULL for all other actions.')

    # May be NULL for ADVANCEMENT, DISCLOSURE, REVERSION and REMANDMENT; Must be NULL otherwise
    DISCLOSURE_LEVELS = Action.DISCLOSURE_LEVELS
    disclosure_level = models.SmallIntegerField(choices=DISCLOSURE_LEVELS._choices, blank=True, null=True,
            help_text=u'Optional for advancement, disclosure, reversion and remandment actions. Must be NULL for all other actions.')

    # May be NULL for REFUSAL and AFFIRMATION; Must be NULL otherwise
    REFUSAL_REASONS = Action.REFUSAL_REASONS
    refusal_reason = MultiSelectField(choices=REFUSAL_REASONS._choices, blank=True,
            help_text=u'Optional for refusal and affirmation actions. Must be NULL for all other actions.')

    # May be empty for ADVANCEMENT; Must be empty otherwise
    obligee_set = models.ManyToManyField(u'obligees.Obligee', blank=True,
            help_text=u'May be empty for advancement actions. Must be empty for all other actions.')

    # Backward relations added to other models:
    #
    #  -- Inforequest.actiondraft_set
    #
    #  -- Branch.actiondraft_set
    #
    #  -- Obligee.actiondraft_set

    objects = ActionDraftQuerySet.as_manager()

    class Meta:
        index_together = [
                # [u'inforequest'] -- ForeignKey defines index by default
                # [u'branch'] -- ForeignKey defines index by default
                ]

    @staticmethod
    def prefetch_attachments(path=None, queryset=None):
        u"""
        Use to prefetch ``ActionDraft.attachments``.
        """
        if queryset is None:
            queryset = Attachment.objects.get_queryset()
        queryset = queryset.order_by_pk()
        return Prefetch(join_lookup(path, u'attachment_set'), queryset, to_attr=u'attachments')

    @cached_property
    def attachments(self):
        u"""
        Cached list of all action draft attachments ordered by ``pk``. May be prefetched with
        ``prefetch_related(ActionDraft.prefetch_attachments())`` queryset method.
        """
        return list(self.attachment_set.order_by_pk())

    @staticmethod
    def prefetch_obligees(path=None, queryset=None):
        u"""
        Use to prefetch ``ActionDraft.obligees``.
        """
        if queryset is None:
            queryset = Obligee.objects.get_queryset()
        queryset = queryset.order_by_name()
        return Prefetch(join_lookup(path, u'obligee_set'), queryset, to_attr=u'obligees')

    @cached_property
    def obligees(self):
        u"""
        Cached list of all obligees the action draft advances to ordered by ``name``. May be
        prefetched with ``prefetch_related(ActionDraft.prefetch_obligees())`` queryset method.
        """
        return list(self.obligee_set.order_by_name())

    def __unicode__(self):
        return u'%s' % self.pk
