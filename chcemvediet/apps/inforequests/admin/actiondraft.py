# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.contrib import admin

from poleno.attachments.admin import AttachmentInline
from poleno.utils.misc import decorate
from poleno.utils.admin import (admin_obj_format, admin_obj_format_join, live_field,
        AdminLiveFieldsMixin, ADMIN_FIELD_INDENT)

from chcemvediet.apps.inforequests.models import Branch, Action, ActionDraft

from .action import ActionAdmin
from .misc import ForeignKeyRawIdWidgetWithUrlParams


class ActionDraftAdminChangeForm(forms.ModelForm):
    branch = ActionDraft._meta.get_field(u'branch').formfield(
            widget=ForeignKeyRawIdWidgetWithUrlParams(
                Action._meta.get_field(u'branch').rel, admin.site),
            )

    def __init__(self, *args, **kwargs):
        super(ActionDraftAdminChangeForm, self).__init__(*args, **kwargs)
        self.fields[u'branch'].queryset = Branch.objects.filter(inforequest=self.instance.branch.inforequest).order_by_pk()
        self.fields[u'branch'].widget.url_params = dict(inforequest=self.instance.branch.inforequest)

class ActionDraftAdmin(AdminLiveFieldsMixin, admin.ModelAdmin):
    list_display = [
            u'actiondraft_column',
            u'inforequest_column',
            u'inforequest_closed_column',
            u'inforequest_applicant_column',
            u'branch_column',
            u'branch_obligee_column',
            u'type',
            ]
    list_filter = [
            u'type',
            u'inforequest__closed',
            ]
    search_fields = [
            u'=id',
            u'=inforequest__pk',
            u'inforequest__applicant__first_name',
            u'inforequest__applicant__last_name',
            u'inforequest__applicant__email',
            u'=branch__pk',
            u'branch__obligee__name',
            ]
    ordering = [u'-pk']

    @decorate(short_description=u'Action Draft')
    @decorate(admin_order_field=u'pk')
    def actiondraft_column(self, draft):
        return admin_obj_format(draft, link=False)

    @decorate(short_description=u'Inforequest')
    @decorate(admin_order_field=u'inforequest__pk')
    def inforequest_column(self, draft):
        inforequest = draft.inforequest
        return admin_obj_format(inforequest)

    @decorate(short_description=u'Closed')
    @decorate(admin_order_field=u'inforequest__closed')
    @decorate(boolean=True)
    def inforequest_closed_column(self, draft):
        return draft.inforequest.closed

    @decorate(short_description=u'Applicant')
    @decorate(admin_order_field=u'inforequest__applicant__email')
    def inforequest_applicant_column(self, draft):
        user = draft.inforequest.applicant
        return admin_obj_format(user, u'{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'Branch')
    @decorate(admin_order_field=u'branch__pk')
    def branch_column(self, draft):
        branch = draft.branch
        return admin_obj_format(branch)

    @decorate(short_description=u'Obligee')
    @decorate(admin_order_field=u'branch__obligee__name')
    def branch_obligee_column(self, draft):
        obligee = draft.branch.obligee if draft.branch else None
        return admin_obj_format(obligee, u'{obj.name}')

    form = ActionDraftAdminChangeForm
    fieldsets = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'inforequest_field',
                    u'inforequest_applicant_field',
                    u'inforequest_closed_field',
                    u'branch',
                    u'branch_details_live',
                    u'branch_inforequest_live',
                    u'branch_obligee_live',
                    u'type',
                    u'type_details_live',
                    u'subject',
                    u'content',
                    u'effective_date',
                    u'deadline',
                    u'deadline_details_live',
                    u'disclosure_level',
                    u'refusal_reason',
                    u'obligee_set',
                    u'obligee_set_details_live',
                    ],
                }),
            ]
    raw_id_fields = [
            u'branch',
            u'obligee_set',
            ]
    live_fields = [
            u'type_details_live',
            u'branch_details_live',
            u'branch_inforequest_live',
            u'branch_obligee_live',
            u'deadline_details_live',
            u'obligee_set_details_live',
            ]
    readonly_fields = live_fields + [
            u'inforequest_field',
            u'inforequest_applicant_field',
            u'inforequest_closed_field',
            ]
    inlines = [
            AttachmentInline,
            ]

    @decorate(short_description=u'Inforequest')
    def inforequest_field(self, draft):
        inforequest = draft.inforequest if draft else None
        return admin_obj_format(inforequest)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Applicant'))
    def inforequest_applicant_field(self, draft):
        inforequest = draft.inforequest if draft else None
        user = inforequest.applicant if inforequest else None
        return admin_obj_format(user, u'{tag}\n{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Closed'))
    @decorate(boolean=True)
    def inforequest_closed_field(self, draft):
        inforequest = draft.inforequest if draft else None
        return inforequest.closed if inforequest else u'--'

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'branch')
    def branch_details_live(self, branch):
        return admin_obj_format(branch)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Inforequest'))
    @live_field(u'branch')
    def branch_inforequest_live(self, branch):
        inforequest = branch.inforequest if branch else None
        return admin_obj_format(inforequest)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Obligee'))
    @live_field(u'branch')
    def branch_obligee_live(self, branch):
        obligee = branch.obligee if branch else None
        return admin_obj_format(obligee, u'{tag}\n{obj.name}')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'type')
    def type_details_live(self, type):
        return ActionAdmin.type_details_live_aux(type)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'effective_date', u'deadline')
    def deadline_details_live(self, effective_date, deadline):
        return ActionAdmin.deadline_details_live_aux(effective_date, deadline, None)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'obligee_set')
    def obligee_set_details_live(self, obligees):
        return admin_obj_format_join(u'\n', obligees, u'{tag} {obj.name}')

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        queryset = super(ActionDraftAdmin, self).get_queryset(request)
        queryset = queryset.select_related(u'inforequest__applicant')
        queryset = queryset.select_related(u'branch__obligee')
        return queryset

admin.site.register(ActionDraft, ActionDraftAdmin)
