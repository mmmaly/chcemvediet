# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin
from django.http import Http404

from poleno.attachments.views import download
from poleno.utils.misc import decorate, filesize
from poleno.utils.admin import admin_obj_format

from .models import Attachment


class DownloadAdminMixin(admin.ModelAdmin):

    def download_view(self, request, obj_pk):
        obj = self.model.objects.get_or_404(pk=obj_pk)
        if not obj.file.name:
            raise Http404
        return download(request, obj)

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        download_view = self.admin_site.admin_view(self.download_view)
        urls = [
                url(r'^(.+)/download/$', download_view, name=u'{}_{}_download'.format(*info)),
                ]
        return urls + super(DownloadAdminMixin, self).get_urls()

@admin.register(Attachment, site=admin.site)
class AttachmentAdmin(DownloadAdminMixin, admin.ModelAdmin):
    date_hierarchy = u'created'
    list_display = [
            u'id',
            decorate(
                lambda o: admin_obj_format(o.generic_object),
                short_description=u'Generic Object',
                admin_order_field=u'generic_type__name',
                ),
            decorate(
                lambda o: admin_obj_format(o, u'{obj.file.name}', link=u'download'),
                short_description=u'File',
                admin_order_field=u'file',
                ),
            u'name',
            u'content_type',
            u'created',
            decorate(
                lambda o: filesize(o.size),
                short_description=u'Size',
                admin_order_field=u'size',
                ),
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
    ordering = [
            u'-id',
            ]
    exclude = [
            u'file',
            ]
    readonly_fields = [
            ]
    raw_id_fields = [
            ]
    inlines = [
            ]

    def get_queryset(self, request):
        queryset = super(AttachmentAdmin, self).get_queryset(request)
        queryset = queryset.prefetch_related(u'generic_object')
        return queryset
