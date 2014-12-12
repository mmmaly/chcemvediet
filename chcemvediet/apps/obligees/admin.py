# vim: expandtab
# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from aggregate_if import Count

from poleno.utils.misc import decorate
from poleno.utils.admin import simple_list_filter_factory, admin_obj_format
from chcemvediet.apps.inforequests.models import Branch

from .models import Obligee, HistoricalObligee

class ObligeeAdminBranchInline(admin.TabularInline):
    model = Branch
    extra = 0

    fields = [
            u'branch_field',
            u'inforequest_field',
            u'inforequest_closed_field',
            u'inforequest_applicant_field',
            u'main_branch_field',
            ]
    readonly_fields = fields

    @decorate(short_description=_(u'Branch'))
    def branch_field(self, branch):
        return admin_obj_format(branch)

    @decorate(short_description=_(u'Inforequest'))
    def inforequest_field(self, branch):
        inforequest = branch.inforequest
        return admin_obj_format(inforequest)

    @decorate(short_description=_(u'Closed'))
    @decorate(boolean=True)
    def inforequest_closed_field(self, branch):
        return branch.inforequest.closed

    @decorate(short_description=_(u'Applicant'))
    def inforequest_applicant_field(self, branch):
        user = branch.inforequest.applicant
        return admin_obj_format(user, u'{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=_(u'Main Branch'))
    @decorate(boolean=True)
    def main_branch_field(self, branch):
        return branch.is_main

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class ObligeeAdmin(SimpleHistoryAdmin):
    list_display = [
            u'obligee_column',
            u'name',
            u'emails',
            u'status',
            u'branch_count_column',
            ]
    list_filter = [
            simple_list_filter_factory(_(u'Branches'), u'branches', [
                (u'1', _(u'With'), lambda qs: qs.filter(branch__count__gt=0)),
                (u'0', _(u'Without'), lambda qs: qs.filter(branch__count=0)),
                ]),
            u'status',
            ]
    search_fields = [
            u'=id',
            u'name',
            u'emails',
            ]

    @decorate(short_description=_(u'Obligee'))
    @decorate(admin_order_field=u'pk')
    def obligee_column(self, obligee):
        return admin_obj_format(obligee, link=False)

    @decorate(short_description=_(u'Branches'))
    @decorate(admin_order_field=u'branch__count')
    def branch_count_column(self, obligee):
        return obligee.branch__count

    fields = [
            u'name',
            u'street',
            u'city',
            u'zip',
            u'emails',
            u'status',
            ]
    inlines = [
            ObligeeAdminBranchInline,
            ]

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(ObligeeAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        # Use textarea for emails
        if db_field.name == u'emails':
            field.widget = admin.widgets.AdminTextareaWidget()
        return field

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        return not obj.branch_set.exists()

    def get_queryset(self, request):
        queryset = super(ObligeeAdmin, self).get_queryset(request)
        queryset = queryset.annotate(Count(u'branch'))
        return queryset

class HistoricalObligeeAdmin(admin.ModelAdmin):
    list_display = [
            u'historicalobligee_column',
            u'obligee_column',
            u'name',
            u'history_date',
            u'history_type',
            ]
    list_filter = [
            u'history_date',
            u'history_type',
            ]
    search_fields = [
            u'=history_id',
            u'=id',
            u'name',
            ]

    @decorate(short_description=_(u'Historical Obligee'))
    @decorate(admin_order_field=u'pk')
    def historicalobligee_column(self, historical):
        return admin_obj_format(historical, link=False)

    @decorate(short_description=_(u'Obligee'))
    @decorate(admin_order_field=u'id')
    def obligee_column(self, historical):
        obligee = historical.history_object
        return admin_obj_format(obligee)

    fields = [
            u'obligee_field',
            u'name',
            u'street',
            u'city',
            u'zip',
            u'emails',
            u'status',
            u'history_date',
            u'history_user_field',
            u'history_type',
            ]
    readonly_fields = fields

    @decorate(short_description=_(u'Obligee'))
    def obligee_field(self, historical):
        obligee = historical.history_object
        return admin_obj_format(obligee)

    @decorate(short_description=_(u'History user'))
    def history_user_field(self, historical):
        user = historical.history_user
        return admin_obj_format(user, u'{tag}\n{obj.first_name} {obj.last_name} <{obj.email}>')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Obligee, ObligeeAdmin)
admin.site.register(HistoricalObligee, HistoricalObligeeAdmin)
