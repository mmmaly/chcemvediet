# vim: expandtab
# -*- coding: utf-8 -*-
from functools import partial

from django import forms
from django.core.urlresolvers import reverse
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

from poleno.attachments.forms import AttachmentsField
from poleno.attachments.admin import AttachmentInline
from poleno.utils.models import after_saved
from poleno.utils.misc import decorate
from poleno.utils.admin import (admin_obj_format, live_field, AdminLiveFieldsMixin,
        ADMIN_FIELD_INDENT)

from chcemvediet.apps.inforequests.models import InforequestDraft


class InforequestDraftAdminAddForm(forms.ModelForm):
    attachments = AttachmentsField(
            required=False,
            upload_url_func=(lambda: reverse(u'admin:attachments_attachment_upload')),
            download_url_func=(lambda a: reverse(u'admin:attachments_attachment_download', args=(a.pk,))),
            )

    def __init__(self, *args, **kwargs):
        attached_to = kwargs.pop(u'attached_to')
        super(InforequestDraftAdminAddForm, self).__init__(*args, **kwargs)

        self.fields[u'attachments'].attached_to = attached_to

    def save(self, commit=True):
        assert self.is_valid()

        draft = InforequestDraft(
                applicant=self.cleaned_data[u'applicant'],
                obligee=self.cleaned_data[u'obligee'],
                subject=self.cleaned_data[u'subject'],
                content=self.cleaned_data[u'content'],
                )

        @after_saved(draft)
        def deferred(draft):
            draft.attachment_set = self.cleaned_data[u'attachments']

        if commit:
            draft.save()
        return draft

    def save_m2m(self):
        pass

class InforequestDraftAdmin(AdminLiveFieldsMixin, admin.ModelAdmin):
    list_display = [
            u'inforequestdraft_column',
            u'applicant_column',
            u'obligee_column',
            ]
    list_filter = [
            ]
    search_fields = [
            u'=id',
            u'applicant__first_name',
            u'applicant__last_name',
            u'applicant__email',
            u'obligee__name',
            ]
    ordering = [u'-pk']

    @decorate(short_description=u'Inforequest Draft')
    @decorate(admin_order_field=u'pk')
    def inforequestdraft_column(self, draft):
        return admin_obj_format(draft, link=False)

    @decorate(short_description=u'Applicant')
    @decorate(admin_order_field=u'applicant__email')
    def applicant_column(self, draft):
        user = draft.applicant
        return admin_obj_format(user, u'{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'Obligee')
    @decorate(admin_order_field=u'obligee')
    def obligee_column(self, draft):
        obligee = draft.obligee
        return admin_obj_format(obligee, u'{obj.name}')

    form_add = InforequestDraftAdminAddForm
    form_change = forms.ModelForm
    fieldsets = [
            (None, {
                u'fields': [
                    u'applicant',
                    u'applicant_details_live',
                    u'obligee',
                    u'obligee_details_live',
                    u'subject',
                    u'content',
                    ],
                }),
            ]
    fieldsets_add = [
            (None, {
                u'fields': [
                    u'applicant',
                    u'applicant_details_live',
                    u'obligee',
                    u'obligee_details_live',
                    u'subject',
                    u'content',
                    u'attachments',
                    ],
                }),
            ]
    live_fields = [
            u'applicant_details_live',
            u'obligee_details_live',
            ]
    readonly_fields = live_fields
    raw_id_fields = [
            u'applicant',
            u'obligee',
            ]
    inlines = [
            AttachmentInline,
            ]

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'applicant')
    def applicant_details_live(self, applicant):
        user = applicant
        return admin_obj_format(user, u'{tag}\n{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'obligee')
    def obligee_details_live(self, obligee):
        return admin_obj_format(obligee, u'{tag}\n{obj.name}')

    def get_queryset(self, request):
        queryset = super(InforequestDraftAdmin, self).get_queryset(request)
        queryset = queryset.select_related(u'applicant')
        queryset = queryset.select_related(u'obligee')
        return queryset

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(InforequestDraftAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            self.form = self.form_add
            form = super(InforequestDraftAdmin, self).get_form(request, obj, **kwargs)
            session = Session.objects.get(session_key=request.session.session_key)
            form = partial(form, attached_to=session)
        else:
            self.form = self.form_change
            form = super(InforequestDraftAdmin, self).get_form(request, obj, **kwargs)
        return form

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(InforequestDraftAdmin, self).get_formsets(request, obj)

admin.site.register(InforequestDraft, InforequestDraftAdmin)
