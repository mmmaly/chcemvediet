# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from jsonfield import JSONField

from poleno.utils.models import QuerySet
from poleno.utils.misc import FormatMixin


class WizardDraftQuerySet(QuerySet):
    def owned_by(self, user):
        return self.filter(owner=user)

class WizardDraft(FormatMixin, models.Model):
    # Primary key (Wizard.instance_id)
    id = models.CharField(max_length=255, primary_key=True)

    # May NOT be NULL
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    # May be empty
    step = models.CharField(blank=True, max_length=255)

    # May NOT be empty
    data = JSONField()

    # May NOT be NULL; Automatically updated on every save
    modified = models.DateTimeField(auto_now=True)

    # May be empty; Backward generic relation
    attachment_set = GenericRelation(u'attachments.Attachment',
            content_type_field=u'generic_type', object_id_field=u'generic_id')

    # Backward relations added to other models:
    #
    #  -- User.wizarddraft_set
    #     May be empty

    # Indexes:
    #  -- id:    primary_key
    #  -- owner: ForeignKey

    objects = WizardDraftQuerySet.as_manager()

    def __unicode__(self):
        return format(self.pk)
