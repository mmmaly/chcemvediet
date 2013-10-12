# vim: expandtab
# -*- coding: utf-8 -*-
from functools import partial

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from cms.admin.placeholderadmin import PlaceholderAdmin
from hvad.admin import TranslatableAdmin

from models import Chunk

def translation_getter_for_field(field, short_description):
    def func(obj):
        return obj.lazy_translation_getter(field)
    func.short_description = short_description
    return func

@partial(admin.site.register, Chunk)
class ChunkAdmin(TranslatableAdmin, PlaceholderAdmin):
    list_display = (
        'reverse_id',
        translation_getter_for_field('description', _('Description')),
        'all_translations',
        )
    search_fields = (
        'reverse_id',
        )
    ordering = (
        'reverse_id',
        )

