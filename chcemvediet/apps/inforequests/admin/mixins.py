# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from django.contrib import admin
from django.contrib.auth.models import User
from aggregate_if import Count

from poleno.mail.models import Message
from poleno.utils.misc import try_except, decorate
from poleno.utils.admin import (simple_list_filter_factory, admin_obj_format,
        admin_obj_format_join, extend_model_admin)

from chcemvediet.apps.inforequests.models import (InforequestDraft, Inforequest, InforequestEmail,
        Branch)


class UserAdminMixinInforequestInline(admin.TabularInline):
    model = Inforequest
    extra = 0
    template = u'admin/auth/user/inforequest_inline.html'

    fields = [
            u'inforequest_field',
            u'obligee_field',
            u'unique_email',
            u'submission_date',
            u'closed',
            u'has_undecided_field',
            ]
    readonly_fields = fields
    ordering = [u'pk']

    @decorate(short_description=u'Inforequest')
    def inforequest_field(self, inforequest):
        return admin_obj_format(inforequest)

    @decorate(short_description=u'Obligee')
    def obligee_field(self, inforequest):
        obligee = inforequest.main_branch.obligee
        return admin_obj_format(obligee, u'{obj.name}')

    @decorate(short_description=u'Undecided E-mail')
    @decorate(boolean=True)
    def has_undecided_field(self, inforequest):
        return inforequest.has_undecided_emails

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super(UserAdminMixinInforequestInline, self).get_queryset(request)
        queryset = queryset.select_undecided_emails_count()
        queryset = queryset.prefetch_related(Inforequest.prefetch_main_branch(None, Branch.objects.select_related(u'obligee')))
        return queryset

class UserAdminMixinInforequestDraftInline(admin.TabularInline):
    model = InforequestDraft
    extra = 0
    template = u'admin/auth/user/inforequestdraft_inline.html'

    fields = [
            u'inforequestdraft_field',
            u'obligee_field',
            ]
    readonly_fields = fields
    ordering = [u'pk']

    @decorate(short_description=u'Inforequest Draft')
    def inforequestdraft_field(self, draft):
        return admin_obj_format(draft)

    @decorate(short_description=u'Obligee')
    def obligee_field(self, draft):
        obligee = draft.obligee
        return admin_obj_format(obligee, u'{obj.name}')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super(UserAdminMixinInforequestDraftInline, self).get_queryset(request)
        queryset = queryset.select_related(u'obligee')
        return queryset

class UserAdminMixin(admin.ModelAdmin):
    def __init__(self, *args, **kwargs):
        self.list_display = list(self.list_display) + [
                u'inforequest_count_column',
                ]
        self.list_filter = list(self.list_filter) + [
            simple_list_filter_factory(u'Inforequests', u'inforequests', [
                (u'1', u'With', lambda qs: qs.filter(inforequest__count__gt=0)),
                (u'0', u'Without', lambda qs: qs.filter(inforequest__count=0)),
                ]),
                ]
        self.inlines = list(self.inlines) + [
                UserAdminMixinInforequestInline,
                UserAdminMixinInforequestDraftInline,
                ]
        super(UserAdminMixin, self).__init__(*args, **kwargs)

    @decorate(short_description=u'Inforequests')
    @decorate(admin_order_field=u'inforequest__count')
    def inforequest_count_column(self, user):
        return user.inforequest__count

    def has_delete_permission(self, request, obj=None):
        if obj:
            # Only users that don't own any inforequests may be deleted.
            if obj.inforequest_set.exists():
                return False
        return super(UserAdminMixin, self).has_delete_permission(request, obj)

    def get_queryset(self, request):
        queryset = super(UserAdminMixin, self).get_queryset(request)
        queryset = queryset.annotate(Count(u'inforequest'))
        return queryset

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(UserAdminMixin, self).get_formsets(request, obj)

class MessageAdminMixin(admin.ModelAdmin):
    def __init__(self, *args, **kwargs):
        self.list_display = list(self.list_display) + [
                u'assigned_to_column',
                u'action_column',
                ]
        self.list_filter = list(self.list_filter) + [
                simple_list_filter_factory(u'Assigned', u'assigned', [
                    (u'1', u'Yes', lambda qs: qs.filter(inforequest__isnull=False).distinct()),
                    (u'0', u'No',  lambda qs: qs.filter(inforequest__isnull=True)),
                    ]),
                simple_list_filter_factory(u'Action', u'action', [
                    (u'1', u'Yes', lambda qs: qs.filter(action__isnull=False).distinct()),
                    (u'0', u'No',  lambda qs: qs.filter(action__isnull=True)),
                    ]),
                ]
        self.search_fields = list(self.search_fields) + [
                u'=inforequest__pk',
                u'=action__pk',
                ]
        self.fieldsets[0][1][u'fields'] = list(self.fieldsets[0][1][u'fields']) + [
                u'assigned_to_field',
                u'action_field',
                ]
        self.readonly_fields = list(self.readonly_fields) + [
                u'assigned_to_field',
                u'action_field',
                ]
        super(MessageAdminMixin, self).__init__(*args, **kwargs)

    @decorate(short_description=u'Assigned To')
    @decorate(admin_order_field=u'inforequest__pk')
    def assigned_to_column(self, message):
        inforequests = message.inforequest_set.order_by_pk()
        return admin_obj_format_join(u', ', inforequests)

    @decorate(short_description=u'Action')
    @decorate(admin_order_field=u'action__pk')
    def action_column(self, message):
        action = try_except(lambda: message.action, None)
        return admin_obj_format(action)

    @decorate(short_description=u'Assigned To')
    def assigned_to_field(self, message):
        inforequests = message.inforequest_set.order_by_pk()
        if inforequests:
            return admin_obj_format_join(u', ', inforequests)
        elif message.type == Message.TYPES.INBOUND and message.processed:
            query = dict(email=message.pk, type=InforequestEmail.TYPES.UNDECIDED)
            url = u'%s?%s' % (reverse(u'admin:inforequests_inforequestemail_add'), urlencode(query))
            btn = format_html(u'<li><a href="{0}">{1}</a></li>', url, u'Assign to Inforequest')
            res = format_html(u'<ul class="object-tools">{0}</ul>', btn)
            return res
        else:
            return u'--'

    @decorate(short_description=u'Action')
    def action_field(self, message):
        action = try_except(lambda: message.action, None)
        return admin_obj_format(action)

    def has_delete_permission(self, request, obj=None):
        if obj:
            # Only messages that are not a part of an action may be deleted.
            action = try_except(lambda: obj.action, None)
            if action is not None:
                return False
        return super(MessageAdminMixin, self).has_delete_permission(request, obj)

    def get_queryset(self, request):
        queryset = super(MessageAdminMixin, self).get_queryset(request)
        queryset = queryset.select_related(u'action')
        queryset = queryset.prefetch_related(u'inforequest_set')
        return queryset

extend_model_admin(User, UserAdminMixin)
extend_model_admin(Message, MessageAdminMixin)
