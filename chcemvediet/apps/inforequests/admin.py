# vim: expandtab
# -*- coding: utf-8 -*-
import datetime
from functools import partial

from django import forms
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.conf.urls import patterns, url
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.utils.encoding import force_text
from django.utils.formats import get_format
from django.utils.html import format_html
from django.utils.http import urlencode
from django.shortcuts import render
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from aggregate_if import Count

from poleno.attachments.forms import AttachmentsField
from poleno.attachments.admin import AttachmentInline
from poleno.mail.models import Message
from poleno.workdays import workdays
from poleno.utils.models import after_saved
from poleno.utils.date import local_date, local_today
from poleno.utils.misc import try_except, decorate, squeeze
from poleno.utils.admin import (simple_list_filter_factory, admin_obj_format,
        admin_obj_format_join, extend_model_admin, live_field, AdminLiveFieldsMixin)

from .models import InforequestDraft, Inforequest, InforequestEmail, Branch, Action, ActionDraft
from ..obligees.models import Obligee


ADMIN_FIELD_INDENT = u'    • '


class ForeignKeyRawIdWidgetWithUrlParams(admin.widgets.ForeignKeyRawIdWidget):
    def __init__(self, *args, **kwargs):
        super(ForeignKeyRawIdWidgetWithUrlParams, self).__init__(*args, **kwargs)
        self.url_params = {}

    def base_url_parameters(self):
        params = super(ForeignKeyRawIdWidgetWithUrlParams, self).base_url_parameters()
        params.update(self.url_params)
        return params


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

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(InforequestDraftAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            self.form = self.form_add
            form = super(InforequestDraftAdmin, self).get_form(request, obj, **kwargs)
            form = partial(form, attached_to=request.user)
        else:
            self.form = self.form_change
            form = super(InforequestDraftAdmin, self).get_form(request, obj, **kwargs)
        return form

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(InforequestDraftAdmin, self).get_formsets(request, obj)


class InforequestAdminBranchInline(admin.TabularInline):
    model = Branch
    extra = 0

    fields = [
            u'branch_field',
            u'obligee_field',
            u'main_branch_field',
            ]
    readonly_fields = fields

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
                (u'1', u'With', lambda qs: qs.filter(undecided__count__gt=0)),
                (u'0', u'Without', lambda qs: qs.filter(undecided__count=0)),
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
        obligee = inforequest.branch.obligee
        return admin_obj_format(obligee, u'{obj.name}')

    @decorate(short_description=u'Undecided E-mails')
    @decorate(admin_order_field=u'undecided__count')
    def undecided_emails_column(self, inforequest):
        return inforequest.undecided__count

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
        obligee = inforequest.branch.obligee
        return admin_obj_format(obligee, u'{tag}\n{obj.name}')

    @decorate(short_description=u'Undecided E-mails')
    def undecided_emails_field(self, inforequest):
        return inforequest.undecided_set.count()

    def get_queryset(self, request):
        queryset = super(InforequestAdmin, self).get_queryset(request)
        # We are interested in main branches only
        queryset = queryset.filter(branch__advanced_by__isnull=True)
        # Count undecided emails
        queryset = queryset.annotate(undecided__count=Count(u'inforequestemail',
            only=Q(inforequestemail__type=InforequestEmail.TYPES.UNDECIDED)))
        return queryset

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(InforequestAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            self.form = self.form_add
            form = super(InforequestAdmin, self).get_form(request, obj, **kwargs)
            form = partial(form, attached_to=request.user)
        else:
            self.form = self.form_change
            form = super(InforequestAdmin, self).get_form(request, obj, **kwargs)
        return form

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(InforequestAdmin, self).get_formsets(request, obj)


class InforequestEmailAdminAddForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(InforequestEmailAdminAddForm, self).clean()

        if u'email' in cleaned_data:
            if cleaned_data[u'email'].inforequestemail_set.exists():
                self._errors[u'email'] = self.error_class([u'This e-mail is already assigned to an inforequest.'])
                del cleaned_data[u'email']

        if u'email' in cleaned_data and u'type' in cleaned_data:
            if cleaned_data[u'email'].type == Message.TYPES.INBOUND:
                if cleaned_data[u'type'] == InforequestEmail.TYPES.APPLICANT_ACTION:
                    self._errors[u'type'] = self.error_class([u"Inbound message type may not be 'Applicant Action'."])
                    del cleaned_data[u'type']
            else: # Message.TYPES.OUTBOUND
                if cleaned_data[u'type'] != InforequestEmail.TYPES.APPLICANT_ACTION:
                    self._errors[u'type'] = self.error_class([u"Outbound message type must be 'Applicant Action'."])
                    del cleaned_data[u'type']

        return cleaned_data

    def save(self, commit=True):
        assert self.is_valid()

        inforequestemail = InforequestEmail(
                inforequest=self.cleaned_data[u'inforequest'],
                email=self.cleaned_data[u'email'],
                type=self.cleaned_data[u'type'],
                )

        if commit:
            inforequestemail.save()
        return inforequestemail

    def save_m2m(self):
        pass

class InforequestEmailAdminChangeForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(InforequestEmailAdminChangeForm, self).clean()

        if u'type' in cleaned_data:
            if self.instance.email.type == Message.TYPES.INBOUND:
                if cleaned_data[u'type'] == InforequestEmail.TYPES.APPLICANT_ACTION:
                    self._errors[u'type'] = self.error_class([u"Inbound message type may not be 'Applicant Action'."])
                    del cleaned_data[u'type']
            else: # Message.TYPES.OUTBOUND
                if cleaned_data[u'type'] != InforequestEmail.TYPES.APPLICANT_ACTION:
                    self._errors[u'type'] = self.error_class([u"Outbound message type must be 'Applicant Action'."])
                    del cleaned_data[u'type']

        return cleaned_data

class InforequestEmailAdminDecideForm(forms.Form):
    branch = Action._meta.get_field(u'branch').formfield(
            widget=ForeignKeyRawIdWidgetWithUrlParams(
                Action._meta.get_field(u'branch').rel, admin.site),
            )
    type = Action._meta.get_field(u'type').formfield(
            choices=[(u'', u'')] + [(c, l) for c, l in Action.TYPES._choices if c in Action.OBLIGEE_ACTION_TYPES]
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
    effective_date = Action._meta.get_field(u'effective_date').formfield(
            widget=admin.widgets.AdminDateWidget(),
            )
    deadline = Action._meta.get_field(u'deadline').formfield(
            widget=admin.widgets.AdminIntegerFieldWidget(),
            )
    extension = Action._meta.get_field(u'extension').formfield(
            widget=admin.widgets.AdminIntegerFieldWidget(),
            )
    disclosure_level = Action._meta.get_field(u'disclosure_level').formfield(
            )
    refusal_reason = Action._meta.get_field(u'refusal_reason').formfield(
            )
    obligee_set = ActionDraft._meta.get_field(u'obligee_set').formfield(
            widget=admin.widgets.ManyToManyRawIdWidget(
                ActionDraft._meta.get_field(u'obligee_set').rel, admin.site),
            )

    class _meta:
        model = InforequestEmail

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop(u'instance')
        attached_to = kwargs.pop(u'attached_to')
        super(InforequestEmailAdminDecideForm, self).__init__(*args, **kwargs)
        self.fields[u'branch'].queryset = Branch.objects.filter(inforequest=self.instance.inforequest)
        self.fields[u'branch'].widget.url_params = dict(inforequest=self.instance.inforequest)
        self.fields[u'subject'].initial = self.instance.email.subject
        self.fields[u'content'].initial = self.instance.email.text
        self.fields[u'attachments'].initial = self.instance.email.attachment_set.all()
        self.fields[u'attachments'].attached_to = [self.instance.email, attached_to]
        self.fields[u'effective_date'].initial = local_date(self.instance.email.processed)

    def save(self, commit=True):
        assert self.is_valid()

        action = Action(
                branch=self.cleaned_data[u'branch'],
                email=self.instance.email,
                type=self.cleaned_data[u'type'],
                subject=self.cleaned_data[u'subject'],
                content=self.cleaned_data[u'content'],
                effective_date=self.cleaned_data[u'effective_date'],
                deadline=self.cleaned_data[u'deadline'],
                extension=self.cleaned_data[u'extension'],
                disclosure_level=self.cleaned_data[u'disclosure_level'],
                refusal_reason=self.cleaned_data[u'refusal_reason'],
                )

        @after_saved(action)
        def deferred(action):
            user_type = ContentType.objects.get_for_model(User)
            for attachment in self.cleaned_data[u'attachments']:
                # We don't want to steal attachments owned by the email, so we clone them.
                if attachment.generic_type != user_type:
                    attachment = attachment.clone()
                attachment.generic_object = action
                attachment.save()

            for obligee in self.cleaned_data[u'obligee_set']:
                sub_branch = Branch(
                        inforequest=action.branch.inforequest,
                        obligee=obligee,
                        advanced_by=action,
                        )
                sub_branch.save()

                sub_action = Action(
                        branch=sub_branch,
                        type=Action.TYPES.ADVANCED_REQUEST,
                        effective_date=action.effective_date,
                        )
                sub_action.save()

        if commit:
            action.save()
        return action

class InforequestEmailAdmin(AdminLiveFieldsMixin, admin.ModelAdmin):
    list_display = [
            u'inforequestemail_column',
            u'inforequest_column',
            u'inforequest_closed_column',
            u'inforequest_applicant_column',
            u'email_column',
            u'email_from_column',
            u'action_column',
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
            u'=email__pk',
            u'email__from_mail',
            ]

    @decorate(short_description=u'Inforequest E-mail')
    @decorate(admin_order_field=u'pk')
    def inforequestemail_column(self, inforequestemail):
        return admin_obj_format(inforequestemail, link=False)

    @decorate(short_description=u'Inforequest')
    @decorate(admin_order_field=u'inforequest__pk')
    def inforequest_column(self, inforequestemail):
        inforequest = inforequestemail.inforequest
        return admin_obj_format(inforequest)

    @decorate(short_description=u'Closed')
    @decorate(admin_order_field=u'inforequest__closed')
    @decorate(boolean=True)
    def inforequest_closed_column(self, inforequestemail):
        return inforequestemail.inforequest.closed

    @decorate(short_description=u'Applicant')
    @decorate(admin_order_field=u'inforequest__applicant__email')
    def inforequest_applicant_column(self, inforequestemail):
        user = inforequestemail.inforequest.applicant
        return admin_obj_format(user, u'{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'E-mail')
    @decorate(admin_order_field=u'email__pk')
    def email_column(self, inforequestemail):
        email = inforequestemail.email
        return admin_obj_format(email)

    @decorate(short_description=u'From')
    @decorate(admin_order_field=u'email__from_mail')
    def email_from_column(self, inforequestemail):
        return inforequestemail.email.from_mail

    @decorate(short_description=u'Action')
    @decorate(admin_order_field=u'email__action__pk')
    def action_column(self, inforequestemail):
        action = try_except(lambda: inforequestemail.email.action, None)
        return admin_obj_format(action)

    form_add = InforequestEmailAdminAddForm
    form_change = InforequestEmailAdminChangeForm
    fieldsets = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'inforequest_field',
                    u'inforequest_applicant_field',
                    u'inforequest_closed_field',
                    u'email_field',
                    u'email_from_field',
                    u'email_subject_field',
                    u'email_action_field',
                    u'type',
                    ],
                }),
            ]
    fieldsets_add = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'inforequest',
                    u'inforequest_details_live',
                    u'inforequest_applicant_live',
                    u'inforequest_closed_live',
                    u'email',
                    u'email_details_live',
                    u'email_from_live',
                    u'email_subject_live',
                    u'email_action_live',
                    u'type',
                    ],
                }),
            ]
    fieldsets_decide = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'inforequest_field',
                    u'inforequest_applicant_field',
                    u'inforequest_closed_field',
                    u'email_field',
                    u'email_from_field',
                    u'email_subject_field',
                    u'branch',
                    u'branch_details_live',
                    u'branch_inforequest_live',
                    u'branch_obligee_live',
                    u'type',
                    u'subject',
                    u'content',
                    u'attachments',
                    u'effective_date',
                    u'deadline',
                    u'extension',
                    u'deadline_details_live',
                    u'disclosure_level',
                    u'refusal_reason',
                    u'obligee_set',
                    u'obligee_set_details_live',
                    ],
                }),
            ]
    raw_id_fields = [
            u'inforequest',
            u'email',
            ]
    live_fields = [
            u'inforequest_details_live',
            u'inforequest_applicant_live',
            u'inforequest_closed_live',
            u'email_details_live',
            u'email_from_live',
            u'email_subject_live',
            u'email_action_live',
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
            u'email_field',
            u'email_from_field',
            u'email_subject_field',
            u'email_action_field',
            ]
    inlines = [
            ]

    @decorate(short_description=u'Inforequest')
    def inforequest_field(self, inforequestemail):
        inforequest = inforequestemail.inforequest if inforequestemail else None
        return admin_obj_format(inforequest)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'inforequest')
    def inforequest_details_live(self, inforequest):
        return admin_obj_format(inforequest)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Applicant'))
    def inforequest_applicant_field(self, inforequestemail):
        inforequest = inforequestemail.inforequest if inforequestemail else None
        user = inforequest.applicant if inforequest else None
        return admin_obj_format(user, u'{tag}\n{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Applicant'))
    @live_field(u'inforequest')
    def inforequest_applicant_live(self, inforequest):
        user = inforequest.applicant if inforequest else None
        return admin_obj_format(user, u'{tag}\n{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Closed'))
    @decorate(boolean=True)
    def inforequest_closed_field(self, inforequestemail):
        inforequest = inforequestemail.inforequest if inforequestemail else None
        return inforequest.closed if inforequest else u'--'

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Closed'))
    @live_field(u'inforequest')
    def inforequest_closed_live(self, inforequest):
        return _boolean_icon(inforequest.closed) if inforequest else u'--'

    @decorate(short_description=u'E-mail')
    def email_field(self, inforequestemail):
        email = inforequestemail.email if inforequestemail else None
        return admin_obj_format(email)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'email')
    def email_details_live(self, email):
        return admin_obj_format(email)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'From'))
    def email_from_field(self, inforequestemail):
        email = inforequestemail.email if inforequestemail else None
        return email.from_formatted if email else u'--'

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'From'))
    @live_field(u'email')
    def email_from_live(self, email):
        return email.from_formatted if email else u'--'

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Subject'))
    def email_subject_field(self, inforequestemail):
        email = inforequestemail.email if inforequestemail else None
        return email.subject if email else u'--'

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Subject'))
    @live_field(u'email')
    def email_subject_live(self, email):
        return email.subject if email else u'--'

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Action'))
    def email_action_field(self, inforequestemail):
        email = inforequestemail.email if inforequestemail else None
        action = try_except(lambda: email.action, None)
        return admin_obj_format(action)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Action'))
    @live_field(u'email')
    def email_action_live(self, email):
        action = try_except(lambda: email.action, None)
        return admin_obj_format(action)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'branch')
    def branch_details_live(self, branch_pk):
        branch = try_except(lambda: Branch.objects.get(pk=branch_pk), None)
        return admin_obj_format(branch)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Inforequest'))
    @live_field(u'branch')
    def branch_inforequest_live(self, branch_pk):
        branch = try_except(lambda: Branch.objects.get(pk=branch_pk), None)
        inforequest = branch.inforequest if branch else None
        return admin_obj_format(inforequest)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Obligee'))
    @live_field(u'branch')
    def branch_obligee_live(self, branch_pk):
        branch = try_except(lambda: Branch.objects.get(pk=branch_pk), None)
        obligee = branch.obligee if branch else None
        return admin_obj_format(obligee, u'{tag}\n{obj.name}')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'effective_date', u'deadline', u'extension')
    def deadline_details_live(self, effective_date, deadline, extension):
        return ActionAdmin.deadline_details_live_aux(effective_date, deadline, extension)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'obligee_set')
    def obligee_set_details_live(self, obligee_pks):
        obligee_pks = obligee_pks.split(u',') if obligee_pks else []
        obligees = [try_except(lambda: Obligee.objects.get(pk=pk), None) for pk in obligee_pks]
        return admin_obj_format_join(u'\n', obligees, u'{tag} {obj.name}')

    def decide_view(self, request, inforequestemail_pk):
        inforequestemail = self.get_object(request, inforequestemail_pk)
        message = inforequestemail.email if inforequestemail else None
        action = try_except(lambda: message.action, None)

        if (inforequestemail is None or inforequestemail.type != InforequestEmail.TYPES.UNDECIDED or
                message.type != Message.TYPES.INBOUND or not message.processed or action is not None):
            return HttpResponseNotFound()

        if request.method == u'POST':
            form = InforequestEmailAdminDecideForm(request.POST, instance=inforequestemail, attached_to=request.user)
            if form.is_valid():
                new_action = form.save(commit=False)
                new_action.save()
                inforequestemail.type = InforequestEmail.TYPES.OBLIGEE_ACTION
                inforequestemail.save()
                info = new_action._meta.app_label, new_action._meta.module_name
                return HttpResponseRedirect(reverse(u'admin:%s_%s_change' % info, args=[new_action.pk]))
        else:
            form = InforequestEmailAdminDecideForm(instance=inforequestemail, attached_to=request.user)

        opts = self.model._meta
        template = u'admin/%s/%s/decide_form.html' % (opts.app_label, opts.model_name)
        adminForm = admin.helpers.AdminForm(form,
                fieldsets=self.fieldsets_decide,
                prepopulated_fields={},
                readonly_fields=self.readonly_fields,
                model_admin=self,
                )

        return render(request, template, {
            u'object': inforequestemail,
            u'title': 'Decide %s' % force_text(opts.verbose_name),
            u'opts': opts,
            u'adminform': adminForm,
            u'media': self.media + adminForm.media,
            })

    def render_change_form(self, request, context, **kwargs):
        inforequestemail = kwargs.get(u'obj', None)

        # Decide button
        if inforequestemail and inforequestemail.type == InforequestEmail.TYPES.UNDECIDED:
            message = inforequestemail.email
            action = try_except(lambda: message.action, None)
            if message.type == Message.TYPES.INBOUND and message.processed and action is None:
                context[u'decide_url'] = reverse(u'admin:inforequests_inforequestemail_decide', args=[inforequestemail.pk])

        return super(InforequestEmailAdmin, self).render_change_form(request, context, **kwargs)

    def has_delete_permission(self, request, obj=None):
        if not obj:
            return True
        # Only messages that are not a part of an action may be unassigned.
        action = try_except(lambda: obj.email.action, None)
        return action is None

    def get_queryset(self, request):
        queryset = super(InforequestEmailAdmin, self).get_queryset(request)
        # We are interested in main branches only now
        queryset = queryset.filter(inforequest__branch__advanced_by__isnull=True)
        return queryset

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = patterns('',
                url(r'^(.+)/decide/$', self.admin_site.admin_view(self.decide_view), name=u'%s_%s_decide' % info),
                )
        return urls + super(InforequestEmailAdmin, self).get_urls()

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(InforequestEmailAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            self.form = self.form_add
            form = super(InforequestEmailAdmin, self).get_form(request, obj, **kwargs)
        else:
            self.form = self.form_change
            form = super(InforequestEmailAdmin, self).get_form(request, obj, **kwargs)
        return form

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(InforequestEmailAdmin, self).get_formsets(request, obj)


class BranchAdminActionInline(admin.TabularInline):
    model = Action
    extra = 0
    template = u'admin/inforequests/branch/action_inline.html'

    fields = [
            u'action_field',
            u'email_field',
            u'type',
            u'effective_date',
            u'deadline_details_field',
            ]
    readonly_fields = fields

    @decorate(short_description=u'Action')
    def action_field(self, action):
        return admin_obj_format(action)

    @decorate(short_description=u'E-mail')
    def email_field(self, action):
        email = action.email
        return admin_obj_format(email)

    @decorate(short_description=u'Deadline')
    def deadline_details_field(self, action):
        if action.has_applicant_deadline:
            if action.deadline_missed:
                return u'Applicant deadline was missed {days} working days ago.'.format(days=-action.deadline_remaining)
            else:
                return u'Applicant deadline will be missed in {days} working days.'.format(days=action.deadline_remaining)
        elif action.has_obligee_deadline:
            if action.deadline_missed:
                return u'Obligee deadline was missed {days} working days ago.'.format(days=-action.deadline_remaining)
            else:
                return u'Obligee deadline will be missed in {days} working days.'.format(days=action.deadline_remaining)
        else:
            return u'Action has no deadline.'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class BranchAdminAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BranchAdminAddForm, self).__init__(*args, **kwargs)
        self.fields[u'advanced_by'].required = True

    def save(self, commit=True):
        assert self.is_valid()

        branch = Branch(
                inforequest=self.cleaned_data[u'advanced_by'].branch.inforequest,
                obligee=self.cleaned_data[u'obligee'],
                advanced_by=self.cleaned_data[u'advanced_by'],
                )

        @after_saved(branch)
        def deferred(branch):
            action = Action(
                    branch=branch,
                    effective_date=self.cleaned_data[u'advanced_by'].effective_date,
                    type=Action.TYPES.ADVANCED_REQUEST,
                    )
            action.save()

        if commit:
            branch.save()
        return branch

    def save_m2m(self):
        pass

class BranchAdminChangeForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(BranchAdminChangeForm, self).clean()

        if u'advanced_by' in cleaned_data:
            advanced_by = cleaned_data[u'advanced_by']
            try:
                if self.instance.advanced_by is None and advanced_by is not None:
                    raise ValidationError(u'This field must be empty for main branches.')
                if self.instance.advanced_by is not None and advanced_by is None:
                    raise ValidationError(u'This field is required for advanced branches.')

                if u'inforequest' in cleaned_data:
                    inforequest = cleaned_data[u'inforequest']
                    if advanced_by is not None and inforequest != advanced_by.branch.inforequest:
                        raise ValidationError(u'Advanced branch must belong to the same inforequest as the parent branch.')

                node = advanced_by
                count = 0
                while node is not None:
                    if node.branch == self.instance:
                        raise ValidationError(u'The branch may not be a sub-branch of itself.')
                    if count > 10:
                        raise ValidationError(u'Too deep branch inheritance.')
                    node = node.branch.advanced_by
                    count += 1

            except ValidationError as e:
                self._errors[u'advanced_by'] = self.error_class(e.messages)
                del cleaned_data[u'advanced_by']

        return cleaned_data

class BranchAdmin(AdminLiveFieldsMixin, admin.ModelAdmin):
    list_display = [
            u'branch_column',
            u'inforequest_column',
            u'inforequest_closed_column',
            u'inforequest_applicant_column',
            u'obligee_column',
            u'main_branch_column',
            ]
    list_filter = [
            simple_list_filter_factory(u'Main Branch', u'mainbranch', [
                (u'1', u'Yes', lambda qs: qs.main()),
                (u'0', u'No',  lambda qs: qs.advanced()),
                ]),
            u'inforequest__closed',
            ]
    search_fields = [
            u'=id',
            u'=inforequest__pk',
            u'inforequest__applicant__first_name',
            u'inforequest__applicant__last_name',
            u'inforequest__applicant__email',
            u'obligee__name',
            ]

    @decorate(short_description=u'Branch')
    @decorate(admin_order_field=u'pk')
    def branch_column(self, branch):
        return admin_obj_format(branch, link=False)

    @decorate(short_description=u'Inforequest')
    @decorate(admin_order_field=u'inforequest__pk')
    def inforequest_column(self, branch):
        inforequest = branch.inforequest
        return admin_obj_format(inforequest)

    @decorate(short_description=u'Closed')
    @decorate(admin_order_field=u'inforequest__closed')
    @decorate(boolean=True)
    def inforequest_closed_column(self, inforequestemail):
        return inforequestemail.inforequest.closed

    @decorate(short_description=u'Applicant')
    @decorate(admin_order_field=u'inforequest__applicant__email')
    def inforequest_applicant_column(self, branch):
        user = branch.inforequest.applicant
        return admin_obj_format(user, u'{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'Obligee')
    @decorate(admin_order_field=u'obligee__name')
    def obligee_column(self, branch):
        obligee = branch.obligee
        return admin_obj_format(obligee, u'{obj.name}')

    @decorate(short_description=u'Main Branch')
    @decorate(admin_order_field=u'advanced_by')
    @decorate(boolean=True)
    def main_branch_column(self, branch):
        return branch.is_main

    form_add = BranchAdminAddForm
    form_change = BranchAdminChangeForm
    fieldsets = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'inforequest',
                    u'obligee',
                    u'obligee_details_live',
                    u'historicalobligee',
                    u'historicalobligee_details_live',
                    u'advanced_by',
                    u'advanced_by_details_live',
                    u'advanced_by_branch_live',
                    u'advanced_by_inforequest_live',
                    u'advanced_by_applicant_live',
                    u'advanced_by_closed_live',
                    ],
                }),
            ]
    fieldsets_add = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'obligee',
                    u'obligee_details_live',
                    u'advanced_by',
                    u'advanced_by_details_live',
                    u'advanced_by_branch_live',
                    u'advanced_by_inforequest_live',
                    u'advanced_by_applicant_live',
                    u'advanced_by_closed_live',
                    ],
                }),
            ]
    raw_id_fields = [
            u'inforequest',
            u'obligee',
            u'historicalobligee',
            u'advanced_by',
            ]
    live_fields = [
            u'obligee_details_live',
            u'historicalobligee_details_live',
            u'advanced_by_details_live',
            u'advanced_by_branch_live',
            u'advanced_by_inforequest_live',
            u'advanced_by_applicant_live',
            u'advanced_by_closed_live',
            ]
    readonly_fields = live_fields
    inlines = [
            BranchAdminActionInline,
            ]

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'obligee')
    def obligee_details_live(self, obligee):
        return admin_obj_format(obligee, u'{tag}\n{obj.name}')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'historicalobligee')
    def historicalobligee_details_live(self, historicalobligee):
        return admin_obj_format(historicalobligee, u'{tag}\n{obj.name}')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'advanced_by')
    def advanced_by_details_live(self, advanced_by):
        action = advanced_by
        return admin_obj_format(action, u'{tag} {0}', action.get_type_display()) if action else u'--'

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Branch'))
    @live_field(u'advanced_by')
    def advanced_by_branch_live(self, advanced_by):
        branch = advanced_by.branch if advanced_by else None
        return admin_obj_format(branch)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Inforequest'))
    @live_field(u'advanced_by')
    def advanced_by_inforequest_live(self, advanced_by):
        inforequest = advanced_by.branch.inforequest if advanced_by else None
        return admin_obj_format(inforequest)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Applicant'))
    @live_field(u'advanced_by')
    def advanced_by_applicant_live(self, advanced_by):
        user = advanced_by.branch.inforequest.applicant if advanced_by else None
        return admin_obj_format(user, u'{tag}\n{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Closed'))
    @live_field(u'advanced_by')
    def advanced_by_closed_live(self, advanced_by):
        return _boolean_icon(advanced_by.branch.inforequest.closed) if advanced_by else u'--'

    def has_delete_permission(self, request, obj=None):
        if not obj:
            return True
        # Only advanced branches may be deleted. If we want to delete a main branch, we must delete
        # its inforequest.
        return not obj.is_main

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(BranchAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            self.form = self.form_add
            form = super(BranchAdmin, self).get_form(request, obj, **kwargs)
        else:
            self.form = self.form_change
            form = super(BranchAdmin, self).get_form(request, obj, **kwargs)
        return form

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(BranchAdmin, self).get_formsets(request, obj)


class ActionAdminAdvancedToInline(admin.TabularInline):
    model = Branch
    extra = 0
    verbose_name = u'Advanced To Branch'
    verbose_name_plural = u'Advanced To Branches'
    template = u'admin/inforequests/action/branch_inline.html'

    fields = [
            u'branch_field',
            u'obligee_field',
            ]
    readonly_fields = fields

    @decorate(short_description=u'Branch')
    def branch_field(self, branch):
        return admin_obj_format(branch)

    @decorate(short_description=u'Obligee')
    def obligee_field(self, branch):
        obligee = branch.obligee
        return admin_obj_format(obligee, u'{obj.name}')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class ActionAdminAddForm(forms.ModelForm):
    attachments = AttachmentsField(
            required=False,
            upload_url_func=(lambda: reverse(u'admin:attachments_attachment_upload')),
            download_url_func=(lambda a: reverse(u'admin:attachments_attachment_download', args=(a.pk,))),
            )
    obligee_set = ActionDraft._meta.get_field(u'obligee_set').formfield(
            widget=admin.widgets.ManyToManyRawIdWidget(
                ActionDraft._meta.get_field(u'obligee_set').rel, admin.site),
            )
    send_email = forms.BooleanField(
            required=False,
            help_text=squeeze(u"""
                Check to send an e-mail with the created action to the obligee. Leave the checkbox
                empty if do not want to send any e-mail. Applicable for applicant actions only.
                """),
            )

    def __init__(self, *args, **kwargs):
        attached_to = kwargs.pop(u'attached_to')
        super(ActionAdminAddForm, self).__init__(*args, **kwargs)

        self.fields[u'attachments'].attached_to = attached_to

    def clean(self):
        cleaned_data = super(ActionAdminAddForm, self).clean()

        if u'send_email' in cleaned_data and u'type' in cleaned_data:
            if cleaned_data[u'send_email'] and cleaned_data[u'type'] not in Action.APPLICANT_ACTION_TYPES:
                self._errors[u'send_email'] = self.error_class([u'Ony applicant actions may be send by e-mail.'])
                del cleaned_data[u'send_email']

        return cleaned_data

    def save(self, commit=True):
        assert self.is_valid()

        action = Action(
                branch=self.cleaned_data[u'branch'],
                type=self.cleaned_data[u'type'],
                subject=self.cleaned_data[u'subject'],
                content=self.cleaned_data[u'content'],
                effective_date=self.cleaned_data[u'effective_date'],
                deadline=self.cleaned_data[u'deadline'],
                extension=self.cleaned_data[u'extension'],
                disclosure_level=self.cleaned_data[u'disclosure_level'],
                refusal_reason=self.cleaned_data[u'refusal_reason'],
                )

        @after_saved(action)
        def deferred(action):
            action.attachment_set = self.cleaned_data[u'attachments']

            for obligee in self.cleaned_data[u'obligee_set']:
                sub_branch = Branch(
                        inforequest=action.branch.inforequest,
                        obligee=obligee,
                        advanced_by=action,
                        )
                sub_branch.save()

                sub_action = Action(
                        branch=sub_branch,
                        type=Action.TYPES.ADVANCED_REQUEST,
                        effective_date=action.effective_date,
                        )
                sub_action.save()

            if self.cleaned_data[u'send_email']:
                action.send_by_email()

        if commit:
            action.save()
        return action

    def save_m2m(self):
        pass

class ActionAdminChangeForm(forms.ModelForm):
    branch = Action._meta.get_field(u'branch').formfield(
            widget=ForeignKeyRawIdWidgetWithUrlParams(
                Action._meta.get_field(u'branch').rel, admin.site),
            )
    email = Action._meta.get_field(u'email').formfield(
            widget=ForeignKeyRawIdWidgetWithUrlParams(
                Action._meta.get_field(u'email').rel, admin.site),
            )

    def __init__(self, *args, **kwargs):
        super(ActionAdminChangeForm, self).__init__(*args, **kwargs)
        self.fields[u'branch'].queryset = Branch.objects.filter(inforequest=self.instance.branch.inforequest)
        self.fields[u'branch'].widget.url_params = dict(inforequest=self.instance.branch.inforequest)
        self.fields[u'email'].queryset = Message.objects.filter(inforequest=self.instance.branch.inforequest)
        self.fields[u'email'].widget.url_params = dict(inforequest=self.instance.branch.inforequest)

    def clean(self):
        cleaned_data = super(ActionAdminChangeForm, self).clean()

        if u'email' in cleaned_data:
            action = try_except(lambda: cleaned_data[u'email'].action, None, Action.DoesNotExist)
            if action is not None and action != self.instance:
                self._errors[u'email'] = self.error_class([u'This e-mail is already used with another action.'])
                del cleaned_data[u'email']

        return cleaned_data

class ActionAdmin(AdminLiveFieldsMixin, admin.ModelAdmin):
    list_display = [
            u'action_column',
            u'branch_column',
            u'branch_inforequest_column',
            u'branch_closed_column',
            u'branch_applicant_column',
            u'branch_obligee_column',
            u'email_column',
            u'type',
            u'effective_date',
            ]
    list_filter = [
            u'type',
            u'effective_date',
            simple_list_filter_factory(u'E-mail', u'email', [
                (u'1', u'Yes', lambda qs: qs.by_email()),
                (u'0', u'No',  lambda qs: qs.by_smail()),
                ]),
            u'branch__inforequest__closed',
            ]
    search_fields = [
            u'=id',
            u'=branch__pk',
            u'=branch__inforequest__pk',
            u'branch__inforequest__applicant__first_name',
            u'branch__inforequest__applicant__last_name',
            u'branch__inforequest__applicant__email',
            u'branch__obligee__name',
            u'=email__pk',
            ]

    @decorate(short_description=u'Action')
    @decorate(admin_order_field=u'pk')
    def action_column(self, action):
        return admin_obj_format(action, link=False)

    @decorate(short_description=u'Branch')
    @decorate(admin_order_field=u'branch__pk')
    def branch_column(self, action):
        branch = action.branch
        return admin_obj_format(branch)

    @decorate(short_description=u'Inforequest')
    @decorate(admin_order_field=u'branch__inforequest__pk')
    def branch_inforequest_column(self, action):
        inforequest = action.branch.inforequest
        return admin_obj_format(inforequest)

    @decorate(short_description=u'Closed')
    @decorate(admin_order_field=u'branch__inforequest__closed')
    @decorate(boolean=True)
    def branch_closed_column(self, action):
        return action.branch.inforequest.closed

    @decorate(short_description=u'Applicant')
    @decorate(admin_order_field=u'branch__inforequest__applicant__email')
    def branch_applicant_column(self, action):
        user = action.branch.inforequest.applicant
        return admin_obj_format(user, u'{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'Obligee')
    @decorate(admin_order_field=u'branch__obligee__name')
    def branch_obligee_column(self, action):
        obligee = action.branch.obligee
        return admin_obj_format(obligee, u'{obj.name}')

    @decorate(short_description=u'Email')
    @decorate(admin_order_field=u'email__pk')
    def email_column(self, action):
        email = action.email
        return admin_obj_format(email)

    form_add = ActionAdminAddForm
    form_change = ActionAdminChangeForm
    fieldsets = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'inforequest_field',
                    u'branch',
                    u'branch_details_live',
                    u'branch_inforequest_live',
                    u'branch_applicant_live',
                    u'branch_obligee_live',
                    u'branch_closed_live',
                    u'email',
                    u'email_details_live',
                    u'email_assigned_to_live',
                    u'email_from_live',
                    u'email_subject_live',
                    u'type',
                    u'type_details_live',
                    u'subject',
                    u'content',
                    u'effective_date',
                    u'deadline',
                    u'extension',
                    u'deadline_details_live',
                    u'disclosure_level',
                    u'refusal_reason',
                    ],
                }),
            (u'Advanced', {
                u'classes': [u'wide', u'collapse'],
                u'fields': [
                    u'last_deadline_reminder',
                    ],
                }),
            ]
    fieldsets_add = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'branch',
                    u'branch_details_live',
                    u'branch_inforequest_live',
                    u'branch_applicant_live',
                    u'branch_obligee_live',
                    u'branch_closed_live',
                    u'type',
                    u'type_details_live',
                    u'subject',
                    u'content',
                    u'attachments',
                    u'effective_date',
                    u'deadline',
                    u'extension',
                    u'deadline_details_live',
                    u'disclosure_level',
                    u'refusal_reason',
                    u'obligee_set',
                    u'obligee_set_details_live',
                    u'send_email',
                    ],
                }),
            ]
    raw_id_fields = [
            u'branch',
            u'email',
            ]
    live_fields = [
            u'branch_details_live',
            u'branch_inforequest_live',
            u'branch_applicant_live',
            u'branch_obligee_live',
            u'branch_closed_live',
            u'email_details_live',
            u'email_assigned_to_live',
            u'email_from_live',
            u'email_subject_live',
            u'type_details_live',
            u'deadline_details_live',
            u'obligee_set_details_live',
            ]
    readonly_fields = live_fields + [
            u'inforequest_field',
            ]
    inlines = [
            AttachmentInline,
            ActionAdminAdvancedToInline,
            ]

    @decorate(short_description=u'Inforequest')
    def inforequest_field(self, action):
        inforequest = action.branch.inforequest if action else None
        return admin_obj_format(inforequest)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'branch')
    def branch_details_live(self, branch):
        return admin_obj_format(branch)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Inforequest'))
    @live_field(u'branch')
    def branch_inforequest_live(self, branch):
        inforequest = branch.inforequest if branch else None
        return admin_obj_format(inforequest)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Applicant'))
    @live_field(u'branch')
    def branch_applicant_live(self, branch):
        user = branch.inforequest.applicant if branch else None
        return admin_obj_format(user, u'{tag}\n{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Obligee'))
    @live_field(u'branch')
    def branch_obligee_live(self, branch):
        obligee = branch.obligee if branch else None
        return admin_obj_format(obligee, u'{tag}\n{obj.name}')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Closed'))
    @live_field(u'branch')
    def branch_closed_live(self, branch):
        return _boolean_icon(branch.inforequest.closed) if branch else u'--'

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'email')
    def email_details_live(self, email):
        return admin_obj_format(email)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Assigned To'))
    @live_field(u'email')
    def email_assigned_to_live(self, email):
        inforequests = email.inforequest_set.all() if email else []
        return admin_obj_format_join(u', ', inforequests)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'From'))
    @live_field(u'email')
    def email_from_live(self, email):
        return email.from_formatted if email else u'--'

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Subject'))
    @live_field(u'email')
    def email_subject_live(self, email):
        return email.subject if email else u'--'

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'type')
    def type_details_live(self, type):
        return ActionAdmin.type_details_live_aux(type)

    @classmethod
    def type_details_live_aux(cls, type):
        try:
            type = int(type)
        except (ValueError, TypeError):
            return u'--'

        if type in Action.APPLICANT_ACTION_TYPES:
            return u'Applicant Action'
        elif type in Action.OBLIGEE_ACTION_TYPES:
            return u'Obligee Action'
        elif type in Action.IMPLICIT_ACTION_TYPES:
            return u'Implicit Action'
        else:
            return u'--'

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'effective_date', u'deadline', u'extension')
    def deadline_details_live(self, effective_date, deadline, extension):
        return ActionAdmin.deadline_details_live_aux(effective_date, deadline, extension)

    @classmethod
    def deadline_details_live_aux(cls, effective_date, deadline, extension):
        try:
            deadline = int(deadline)
            extension = int(extension or '0')
        except (ValueError, TypeError):
            return u'--'

        for format in get_format(u'DATE_INPUT_FORMATS'):
            try:
                effective_date = datetime.datetime.strptime(effective_date, format).date()
                break
            except (ValueError, TypeError):
                continue
            return u'--'

        days_passed = workdays.between(effective_date, local_today())
        deadline_remaining = deadline + extension - days_passed
        deadline_missed = (deadline_remaining < 0)

        if deadline_missed:
            return u'Deadline was missed {days} working days ago.'.format(days=-deadline_remaining)
        else:
            return u'Deadline will be missed in {days} working days.'.format(days=deadline_remaining)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'obligee_set')
    def obligee_set_details_live(self, obligee_pks):
        obligee_pks = obligee_pks.split(u',') if obligee_pks else []
        obligees = [try_except(lambda: Obligee.objects.get(pk=pk), None) for pk in obligee_pks]
        return admin_obj_format_join(u'\n', obligees, u'{tag} {obj.name}')

    def has_delete_permission(self, request, obj=None):
        if not obj:
            return True
        # Branches may not be left empty.
        return obj.branch.action_set.count() > 1

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(ActionAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            self.form = self.form_add
            form = super(ActionAdmin, self).get_form(request, obj, **kwargs)
            form = partial(form, attached_to=request.user)
        else:
            self.form = self.form_change
            form = super(ActionAdmin, self).get_form(request, obj, **kwargs)
        return form

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(ActionAdmin, self).get_formsets(request, obj)


class ActionDraftAdminChangeForm(forms.ModelForm):
    branch = ActionDraft._meta.get_field(u'branch').formfield(
            widget=ForeignKeyRawIdWidgetWithUrlParams(
                Action._meta.get_field(u'branch').rel, admin.site),
            )

    def __init__(self, *args, **kwargs):
        super(ActionDraftAdminChangeForm, self).__init__(*args, **kwargs)
        self.fields[u'branch'].queryset = Branch.objects.filter(inforequest=self.instance.branch.inforequest)
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

    @decorate(short_description=u'Inforequest')
    def inforequest_field(self, inforequest):
        return admin_obj_format(inforequest)

    @decorate(short_description=u'Obligee')
    def obligee_field(self, inforequest):
        obligee = inforequest.branch.obligee
        return admin_obj_format(obligee, u'{obj.name}')

    @decorate(short_description=u'Undecided E-mail')
    @decorate(boolean=True)
    def has_undecided_field(self, inforequest):
        return inforequest.has_undecided_email

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class UserAdminMixinInforequestDraftInline(admin.TabularInline):
    model = InforequestDraft
    extra = 0
    template = u'admin/auth/user/inforequestdraft_inline.html'

    fields = [
            u'inforequestdraft_field',
            u'obligee_field',
            ]
    readonly_fields = fields

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

    def get_queryset(self, request):
        queryset = super(UserAdminMixin, self).get_queryset(request)
        queryset = queryset.annotate(Count(u'inforequest'))
        return queryset

    def has_delete_permission(self, request, obj=None):
        if obj:
            # Only users that don't own any inforequests may be deleted.
            if obj.inforequest_set.exists():
                return False
        return super(UserAdminMixin, self).has_delete_permission(request, obj)

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
        inforequests = message.inforequest_set.all()
        return admin_obj_format_join(u', ', inforequests)

    @decorate(short_description=u'Action')
    @decorate(admin_order_field=u'action__pk')
    def action_column(self, message):
        action = try_except(lambda: message.action, None)
        return admin_obj_format(action)

    @decorate(short_description=u'Assigned To')
    def assigned_to_field(self, message):
        inforequests = message.inforequest_set.all()
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


admin.site.disable_action('delete_selected')
admin.site.register(InforequestDraft, InforequestDraftAdmin)
admin.site.register(Inforequest, InforequestAdmin)
admin.site.register(InforequestEmail, InforequestEmailAdmin)
admin.site.register(Branch, BranchAdmin)
admin.site.register(Action, ActionAdmin)
admin.site.register(ActionDraft, ActionDraftAdmin)
extend_model_admin(User, UserAdminMixin)
extend_model_admin(Message, MessageAdminMixin)
