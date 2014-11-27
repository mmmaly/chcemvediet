# vim: expandtab
# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.contrib.contenttypes import generic

from poleno.utils.misc import filesize, decorate
from poleno.utils.admin import admin_obj_link

from .models import Attachment

class AttachmentInline(generic.GenericTabularInline):
    model = Attachment
    ct_field = u'generic_type'
    ct_fk_field = u'generic_id'
    extra = 0

    fields = [
            u'attachment_field',
            u'file',
            u'name',
            u'content_type',
            u'created',
            u'size_field',
            ]
    readonly_fields = fields

    @decorate(short_description=_(u'Attachment'))
    @decorate(allow_tags=True)
    def attachment_field(self, attachment):
        return admin_obj_link(attachment)

    @decorate(short_description=_(u'Size'))
    def size_field(self, attachment):
        return filesize(attachment.size)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class AttachmentAdmin(admin.ModelAdmin):
    list_display = [
            u'attachment_column',
            u'generic_object_column',
            u'file',
            u'name',
            u'content_type',
            u'created',
            u'size_column',
            ]
    list_filter = [
            u'created',
            u'content_type',
            u'generic_type',
            ]
    search_fields = [
            u'=id',
            u'=generic_id',
            u'generic_type__name',
            u'file',
            u'name',
            u'content_type',
            ]

    @decorate(short_description=_(u'Attachment'))
    @decorate(admin_order_field=u'pk')
    def attachment_column(self, attachment):
        return u'<%s: %s>' % (attachment.__class__.__name__, attachment.pk)

    @decorate(short_description=_(u'Generic Object'))
    @decorate(admin_order_field=u'generic_type__name')
    @decorate(allow_tags=True)
    def generic_object_column(self, attachment):
        generic = attachment.generic_object
        return admin_obj_link(generic)

    @decorate(short_description=_(u'Size'))
    @decorate(admin_order_field=u'size')
    def size_column(self, attachment):
        return filesize(attachment.size)

    fields = [
            u'generic_type',
            u'generic_id',
            u'generic_object_column',
            u'file',
            u'name',
            u'content_type',
            u'created',
            u'size',
            ]
    readonly_fields = [
            u'generic_object_column',
            u'file',
            u'size',
            ]
    raw_id_fields = [
            ]

admin.site.register(Attachment, AttachmentAdmin)
