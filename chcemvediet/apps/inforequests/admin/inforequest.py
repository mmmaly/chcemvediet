# vim: expandtab
# -*- coding: utf-8 -*-
from functools import partial

from django import forms
from django.core.urlresolvers import reverse
from django.contrib import admin
from django.contrib.sessions.models import Session

from poleno.attachments.forms import AttachmentsField
from poleno.utils.models import after_saved
from poleno.utils.misc import try_except, decorate, squeeze
from poleno.utils.admin import (simple_list_filter_factory, admin_obj_format, live_field,
        AdminLiveFieldsMixin, ADMIN_FIELD_INDENT)

from chcemvediet.apps.inforequests.models import (Inforequest, InforequestEmail, Branch, Action,
        ActionDraft)
from chcemvediet.apps.obligees.models import Obligee


class InforequestAdminBranchInline(admin.TabularInline):
    model = Branch
    extra = 0

    fields = [
            u'branch_field',
            u'obligee_field',
            u'main_branch_field',
            ]
    readonly_fields = fields
    ordering = [u'pk']

    @decorate(short_description=u'Branch')
    def branch_field(self, branch):
        return admin_obj_format(branch)

    @decorate(short_description=u'Obligee')
    def obligee_field(self, branch):
        obligee = branch.obligee
        return admin_obj_format(obligee, u'{obj.name}')

    @decorate(short_description=u'Main Branch')
    @decorate(boolean=True)
    def main_branch_field(self, branch):
        return branch.is_main

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super(InforequestAdminBranchInline, self).get_queryset(request)
        queryset = queryset.select_related(u'obligee')
        return queryset

class InforequestAdminInforequestEmailInline(admin.TabularInline):
    model = InforequestEmail
    extra = 0

    fields = [
            u'inforequestemail_field',
            u'email_field',
            u'email_type_field',
            u'email_from_field',
            u'type',
            ]
    readonly_fields = fields
    ordering = [u'email__processed', u'email__pk', u'pk']

    @decorate(short_description=u'Inforequest E-mail')
    def inforequestemail_field(self, inforequestemail):
        return admin_obj_format(inforequestemail)

    @decorate(short_description=u'E-mail')
    def email_field(self, inforequestemail):
        email = inforequestemail.email
        return admin_obj_format(email)

    @decorate(short_description=u'E-mail Type')
    def email_type_field(self, inforequestemail):
        return inforequestemail.email.get_type_display()

    @decorate(short_description=u'From')
    def email_from_field(self, inforequestemail):
        return inforequestemail.email.from_formatted

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super(InforequestAdminInforequestEmailInline, self).get_queryset(request)
        queryset = queryset.select_related(u'email')
        return queryset

class InforequestAdminActionDraftInline(admin.TabularInline):
    model = ActionDraft
    extra = 0

    fields = [
            u'actiondraft_field',
            u'branch_field',
            u'branch_obligee_field',
            u'type',
            ]
    readonly_fields = fields
    ordering = [u'pk']

    @decorate(short_description=u'Action Draft')
    def actiondraft_field(self, draft):
        return admin_obj_format(draft)

    @decorate(short_description=u'Branch')
    def branch_field(self, draft):
        branch = draft.branch
        return admin_obj_format(branch)

    @decorate(short_description=u'Obligee')
    def branch_obligee_field(self, draft):
        obligee = draft.branch.obligee if draft.branch else None
        return admin_obj_format(obligee, u'{obj.name}')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super(InforequestAdminActionDraftInline, self).get_queryset(request)
        queryset = queryset.select_related(u'branch__obligee')
        return queryset

class InforequestAdminAddForm(forms.ModelForm):
    obligee = Branch._meta.get_field(u'obligee').formfield(
            widget=admin.widgets.ForeignKeyRawIdWidget(
                Branch._meta.get_field(u'obligee').rel, admin.site),
            )
    subject = Action._meta.get_field(u'subject').formfield(
            widget=admin.widgets.AdminTextInputWidget(),
            )
    content = Action._meta.get_field(u'content').formfield(
            widget=admin.widgets.AdminTextareaWidget(),
            )
    attachments = AttachmentsField(
            required=False,
            upload_url_func=(lambda: reverse(u'admin:attachments_attachment_upload')),
            download_url_func=(lambda a: reverse(u'admin:attachments_attachment_download', args=(a.pk,))),
            )
    send_email = forms.BooleanField(
            required=False,
            help_text=squeeze(u"""
                Check to send the inforequest to the obligee by e-mail. Leave the checkbox empty if
                you just want to create a fake inforequest without sending any real e-mail to the
                obligee.
                """),
            )

    def __init__(self, *args, **kwargs):
        attached_to = kwargs.pop(u'attached_to')
        super(InforequestAdminAddForm, self).__init__(*args, **kwargs)

        self.fields[u'attachments'].attached_to = attached_to

    def save(self, commit=True):
        assert self.is_valid()

        inforequest = Inforequest(
                applicant=self.cleaned_data[u'applicant'],
                )

        @after_saved(inforequest)
        def deferred(inforequest):
            branch = Branch(
                    inforequest=inforequest,
                    obligee=self.cleaned_data[u'obligee'],
                    )
            branch.save()

            action = Action(
                    branch=branch,
                    type=Action.TYPES.REQUEST,
                    subject=self.cleaned_data[u'subject'],
                    content=self.cleaned_data[u'content'],
                    effective_date=inforequest.submission_date,
                    )
            action.save()
            action.attachment_set = self.cleaned_data[u'attachments']

            if self.cleaned_data[u'send_email']:
                action.send_by_email()

        if commit:
            inforequest.save()
        return inforequest

    def save_m2m(self):
        pass

class InforequestAdmin(AdminLiveFieldsMixin, admin.ModelAdmin):
    list_display = [
            u'inforequest_column',
            u'applicant_column',
            u'obligee_column',
            u'unique_email',
            u'submission_date',
            u'closed',
            u'undecided_emails_column',
            ]
    list_filter = [
            u'submission_date',
            simple_list_filter_factory(u'Undecided E-mail', u'undecided', [
                (u'1', u'With', lambda qs: qs.filter(undecided_emails_count__gt=0)),
                (u'0', u'Without', lambda qs: qs.filter(undecided_emails_count=0)),
                ]),
            u'closed',
            ]
    search_fields = [
            u'=id',
            u'applicant__first_name',
            u'applicant__last_name',
            u'applicant__email',
            u'branch__obligee__name',
            u'unique_email',
            ]
    ordering = [u'-submission_date', u'-pk']

    @decorate(short_description=u'Inforequest')
    @decorate(admin_order_field=u'pk')
    def inforequest_column(self, inforequest):
        return admin_obj_format(inforequest, link=False)

    @decorate(short_description=u'Applicant')
    @decorate(admin_order_field=u'applicant__email')
    def applicant_column(self, inforequest):
        user = inforequest.applicant
        return admin_obj_format(user, u'{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'Obligee')
    @decorate(admin_order_field=u'branch__obligee__name')
    def obligee_column(self, inforequest):
        obligee = inforequest.main_branch.obligee
        return admin_obj_format(obligee, u'{obj.name}')

    @decorate(short_description=u'Undecided E-mails')
    @decorate(admin_order_field=u'undecided_emails_count')
    def undecided_emails_column(self, inforequest):
        return inforequest.undecided_emails_count

    form_add = InforequestAdminAddForm
    form_change = forms.ModelForm
    fieldsets = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'applicant',
                    u'applicant_details_live',
                    u'obligee_details_field',
                    u'applicant_name',
                    (u'applicant_street', u'applicant_city', u'applicant_zip'),
                    u'unique_email',
                    u'submission_date',
                    u'closed',
                    u'undecided_emails_field',
                    ],
                }),
            (u'Advanced', {
                u'classes': [u'wide', u'collapse'],
                u'fields': [
                    u'last_undecided_email_reminder',
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
                    u'send_email',
                    ],
                }),
            ]
    live_fields = [
            u'applicant_details_live',
            u'obligee_details_live',
            ]
    readonly_fields = live_fields + [
            u'obligee_details_field',
            u'submission_date',
            u'undecided_emails_field',
            ]
    raw_id_fields = [
            u'applicant',
            ]
    inlines = [
            InforequestAdminBranchInline,
            InforequestAdminInforequestEmailInline,
            InforequestAdminActionDraftInline,
            ]

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'applicant')
    def applicant_details_live(self, applicant):
        user = applicant
        return admin_obj_format(user, u'{tag}\n{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'obligee')
    def obligee_details_live(self, obligee_pk):
        obligee = try_except(lambda: Obligee.objects.get(pk=obligee_pk), None)
        return admin_obj_format(obligee, u'{tag}\n{obj.name}')

    @decorate(short_description=u'Obligee')
    def obligee_details_field(self, inforequest):
        obligee = inforequest.main_branch.obligee
        return admin_obj_format(obligee, u'{tag}\n{obj.name}')

    @decorate(short_description=u'Undecided E-mails')
    def undecided_emails_field(self, inforequest):
        return inforequest.undecided_emails_count

    def get_queryset(self, request):
        queryset = super(InforequestAdmin, self).get_queryset(request)
        queryset = queryset.select_related(u'applicant')
        queryset = queryset.select_undecided_emails_count()
        queryset = queryset.prefetch_related(Inforequest.prefetch_main_branch(None, Branch.objects.select_related(u'obligee')))
        return queryset

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(InforequestAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            self.form = self.form_add
            form = super(InforequestAdmin, self).get_form(request, obj, **kwargs)
            session = Session.objects.get(session_key=request.session.session_key)
            form = partial(form, attached_to=session)
        else:
            self.form = self.form_change
            form = super(InforequestAdmin, self).get_form(request, obj, **kwargs)
        return form

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(InforequestAdmin, self).get_formsets(request, obj)

admin.site.register(Inforequest, InforequestAdmin)
