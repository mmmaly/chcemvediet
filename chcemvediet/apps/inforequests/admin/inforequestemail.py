# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.core.urlresolvers import reverse
from django.db import transaction
from django.conf.urls import patterns, url
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.utils.encoding import force_text
from django.shortcuts import render
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.contrib.sessions.models import Session

from poleno.attachments.forms import AttachmentsField
from poleno.mail.models import Message
from poleno.utils.models import after_saved
from poleno.utils.date import local_date
from poleno.utils.misc import try_except, decorate
from poleno.utils.admin import (admin_obj_format, admin_obj_format_join, live_field,
        AdminLiveFieldsMixin)

from chcemvediet.apps.inforequests.models import InforequestEmail, Branch, Action, ActionDraft
from chcemvediet.apps.obligees.models import Obligee

from .action import ActionAdmin
from .misc import ADMIN_FIELD_INDENT, ForeignKeyRawIdWidgetWithUrlParams


class InforequestEmailAdminAddForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(InforequestEmailAdminAddForm, self).clean()

        if u'email' in cleaned_data:
            if cleaned_data[u'email'].inforequestemail_set.exists():
                self.add_error(u'email', u'This e-mail is already assigned to an inforequest.')

        if u'email' in cleaned_data and u'type' in cleaned_data:
            if cleaned_data[u'email'].type == Message.TYPES.INBOUND:
                if cleaned_data[u'type'] == InforequestEmail.TYPES.APPLICANT_ACTION:
                    self.add_error(u'type', u"Inbound message type may not be 'Applicant Action'.")
            else: # Message.TYPES.OUTBOUND
                if cleaned_data[u'type'] != InforequestEmail.TYPES.APPLICANT_ACTION:
                    self.add_error(u'type', u"Outbound message type must be 'Applicant Action'.")

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
                    self.add_error(u'type', u"Inbound message type may not be 'Applicant Action'.")
            else: # Message.TYPES.OUTBOUND
                if cleaned_data[u'type'] != InforequestEmail.TYPES.APPLICANT_ACTION:
                    self.add_error(u'type', u"Outbound message type must be 'Applicant Action'.")

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
        labels = None
        help_texts = None

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop(u'instance')
        attached_to = kwargs.pop(u'attached_to')
        super(InforequestEmailAdminDecideForm, self).__init__(*args, **kwargs)
        self.fields[u'branch'].queryset = Branch.objects.filter(inforequest=self.instance.inforequest).order_by_pk()
        self.fields[u'branch'].widget.url_params = dict(inforequest=self.instance.inforequest)
        self.fields[u'subject'].initial = self.instance.email.subject
        self.fields[u'content'].initial = self.instance.email.text
        self.fields[u'attachments'].initial = self.instance.email.attachment_set.order_by_pk()
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
            session_type = ContentType.objects.get_for_model(Session)
            for attachment in self.cleaned_data[u'attachments']:
                # We don't want to steal attachments owned by the email, so we clone them.
                if attachment.generic_type_id != session_type.pk:
                    attachment = attachment.clone(action)
                else:
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
    ordering = [u'-pk']

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

    @transaction.atomic
    def decide_view(self, request, inforequestemail_pk):
        inforequestemail = self.get_object(request, inforequestemail_pk)
        message = inforequestemail.email if inforequestemail else None
        action = try_except(lambda: message.action, None)

        if (inforequestemail is None or inforequestemail.type != InforequestEmail.TYPES.UNDECIDED or
                message.type != Message.TYPES.INBOUND or not message.processed or action is not None):
            return HttpResponseNotFound()

        session = Session.objects.get(session_key=request.session.session_key)
        if request.method == u'POST':
            form = InforequestEmailAdminDecideForm(request.POST, instance=inforequestemail, attached_to=session)
            if form.is_valid():
                new_action = form.save(commit=False)
                new_action.save()
                inforequestemail.type = InforequestEmail.TYPES.OBLIGEE_ACTION
                inforequestemail.save(update_fields=[u'type'])
                info = new_action._meta.app_label, new_action._meta.model_name
                return HttpResponseRedirect(reverse(u'admin:%s_%s_change' % info, args=[new_action.pk]))
        else:
            form = InforequestEmailAdminDecideForm(instance=inforequestemail, attached_to=session)

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
        queryset = queryset.select_related(u'inforequest__applicant')
        queryset = queryset.select_related(u'email__action')
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

admin.site.register(InforequestEmail, InforequestEmailAdmin)
