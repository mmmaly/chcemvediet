# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Prefetch
from django.utils.functional import cached_property
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from jsonfield import JSONField

from poleno.attachments.models import Attachment
from poleno.utils.models import QuerySet, join_lookup
from poleno.utils.misc import squeeze

class InforequestDraftQuerySet(QuerySet):
    def owned_by(self, user):
        return self.filter(applicant=user)
    def order_by_pk(self):
        return self.order_by(u'pk')

class InforequestDraft(models.Model):
    # May NOT be NULL
    applicant = models.ForeignKey(User,
            help_text=squeeze(u"""
                The draft owner, the future inforequest applicant.
                """))

    # May be NULL
    obligee = models.ForeignKey(u'obligees.Obligee', blank=True, null=True,
            help_text=squeeze(u"""
                The obligee the inforequest will be sent to, if the user has already set it.
                """))

    # May be empty; Django migrations for MySQL backend are broken in ``default`` is mutable.
    subject = JSONField(blank=True, default=())
    content = JSONField(blank=True, default=())

    # May be empty
    attachment_set = generic.GenericRelation(u'attachments.Attachment', content_type_field=u'generic_type', object_id_field=u'generic_id')

    # Backward relations added to other models:
    #
    #  -- User.inforequestdraft_set
    #     May be empty
    #
    #  -- Obligee.inforequestdraft_set
    #     May be empty

    objects = InforequestDraftQuerySet.as_manager()

    class Meta:
        index_together = [
                # [u'applicant'] -- ForeignKey defines index by default
                # [u'obligee'] -- ForeignKey defines index by default
                ]

    @staticmethod
    def prefetch_attachments(path=None, queryset=None):
        u"""
        Use to prefetch ``InforequestDraft.attachments``
        """
        if queryset is None:
            queryset = Attachment.objects.get_queryset()
        queryset = queryset.order_by_pk()
        return Prefetch(join_lookup(path, u'attachment_set'), queryset, to_attr=u'attachments')

    @cached_property
    def attachments(self):
        u"""
        Cached list of all inforequest draft attachments ordered by ``pk``. May be prefetched with
        ``prefetch_related(InforequestDraft.prefetch_attachments())`` queryset method.
        """
        return list(self.attachment_set.order_by_pk())

    def __unicode__(self):
        return u'%s' % self.pk
