# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models.fields import PlaceholderField
from hvad.models import TranslatableModel, TranslatedFields

class Chunk(TranslatableModel):
    reverse_id = models.CharField(max_length=255, unique=True, verbose_name=_('Id'))
    content = PlaceholderField('chunk', verbose_name=_('Content'))
    translations = TranslatedFields(
        description = models.CharField(max_length=255, verbose_name=_('Description'))
        )

    class Meta:
        verbose_name = _('Chunk')
        verbose_name_plural = _('Chunks')

    def __unicode__(self):
        return self.reverse_id

