# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from jsonfield import JSONField

from poleno.utils.models import QuerySet

class WizardDraftQuerySet(QuerySet):
    pass

class WizardDraft(models.Model):
    # Primary key (Wizard.instance_id)
    id = models.CharField(max_length=255, primary_key=True)

    # May be empty
    step = models.CharField(blank=True, max_length=255)

    # May NOT be empty
    data = JSONField()

    # May NOT be NULL; Automatically updated on every save
    modified = models.DateTimeField(auto_now=True)

    objects = WizardDraftQuerySet.as_manager()

    class Meta:
        index_together = [
                # [u'id'] -- Primary key defines unique index by default
                ]
