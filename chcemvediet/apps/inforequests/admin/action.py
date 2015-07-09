# vim: expandtab
# -*- coding: utf-8 -*-
import datetime
from functools import partial

from django import forms
from django.core.urlresolvers import reverse
from django.utils.formats import get_format
from django.contrib import admin
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.contrib.sessions.models import Session

from poleno.attachments.forms import AttachmentsField
from poleno.attachments.admin import AttachmentInline
from poleno.mail.models import Message
from poleno.workdays import workdays
from poleno.utils.models import after_saved
from poleno.utils.date import local_today
from poleno.utils.misc import try_except, decorate, squeeze
from poleno.utils.admin import (simple_list_filter_factory, admin_obj_format,
        admin_obj_format_join, live_field, AdminLiveFieldsMixin, ADMIN_FIELD_INDENT)

from chcemvediet.apps.inforequests.models import Branch, Action, ActionDraft
from chcemvediet.apps.obligees.models import Obligee

from .misc import ForeignKeyRawIdWidgetWithUrlParams


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
    ordering = [u'pk']

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

    def get_queryset(self, request):
        queryset = super(ActionAdminAdvancedToInline, self).get_queryset(request)
        queryset = queryset.select_related(u'obligee')
        return queryset

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
                self.add_error(u'send_email', u'Ony applicant actions may be send by e-mail.')

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
        self.fields[u'branch'].queryset = Branch.objects.filter(inforequest=self.instance.branch.inforequest).order_by_pk()
        self.fields[u'branch'].widget.url_params = dict(inforequest=self.instance.branch.inforequest)
        self.fields[u'email'].queryset = Message.objects.filter(inforequest=self.instance.branch.inforequest).order_by_processed()
        self.fields[u'email'].widget.url_params = dict(inforequest=self.instance.branch.inforequest)

    def clean(self):
        cleaned_data = super(ActionAdminChangeForm, self).clean()

        if u'email' in cleaned_data:
            if cleaned_data[u'email']:
                action = try_except(lambda: cleaned_data[u'email'].action, None, Action.DoesNotExist)
                if action is not None and action.pk != self.instance.pk:
                    self.add_error(u'email', u'This e-mail is already used with another action.')

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
    ordering = [u'-effective_date', u'-pk']

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
        else:
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

    def get_queryset(self, request):
        queryset = super(ActionAdmin, self).get_queryset(request)
        queryset = queryset.select_related(u'branch__inforequest__applicant')
        queryset = queryset.select_related(u'branch__obligee')
        queryset = queryset.select_related(u'email')
        return queryset

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(ActionAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            self.form = self.form_add
            form = super(ActionAdmin, self).get_form(request, obj, **kwargs)
            session = Session.objects.get(session_key=request.session.session_key)
            form = partial(form, attached_to=session)
        else:
            self.form = self.form_change
            form = super(ActionAdmin, self).get_form(request, obj, **kwargs)
        return form

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(ActionAdmin, self).get_formsets(request, obj)

admin.site.register(Action, ActionAdmin)
