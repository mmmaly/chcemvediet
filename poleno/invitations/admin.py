# vim: expandtab
# -*- coding: utf-8 -*-
from functools import partial
from email.utils import getaddresses

from django import forms
from django.core.validators import validate_email
from django.db import transaction
from django.conf.urls import patterns, url
from django.shortcuts import render
from django.utils.encoding import force_text
from django.contrib import admin

from poleno.utils.forms import ValidatorChain, validate_comma_separated_emails
from poleno.utils.misc import decorate, squeeze
from poleno.utils.admin import (simple_list_filter_factory, admin_obj_format, live_field,
        AdminLiveFieldsMixin, ADMIN_FIELD_INDENT)

from . import app_settings
from .models import Invitation
from .validators import validate_unused_emails

class InvitationAdminAddForm(forms.ModelForm):
    email = forms.CharField(
            validators=[ValidatorChain(
                validate_email,
                validate_unused_emails,
                )],
            widget=admin.widgets.AdminEmailInputWidget(),
            help_text=Invitation._meta.get_field(u'email').help_text,
            )
    validity = forms.IntegerField(
            min_value=0,
            initial=app_settings.DEFAULT_VALIDITY,
            help_text=squeeze(u"""
                Number of days the invitation will be valid.
                """),
            )
    invitor = Invitation._meta.get_field(u'invitor').formfield(
            widget=admin.widgets.ForeignKeyRawIdWidget(
                Invitation._meta.get_field(u'invitor').rel, admin.site),
            )
    send_email = forms.BooleanField(
            initial=True,
            required=False,
            help_text=squeeze(u"""
                Check to send the invitation e-mail to the given address. Leave the checkbox empty
                if you just want to create a fake invitation without sending any real e-mail. For
                instance, if you want to send the invitation e-mail manually.
                """),
            )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop(u'user')
        super(InvitationAdminAddForm, self).__init__(*args, **kwargs)

        self.initial[u'invitor'] = user

    def save(self, commit=True):
        assert self.is_valid()

        invitation = Invitation.create(
                email=self.cleaned_data[u'email'],
                invitor=self.cleaned_data[u'invitor'],
                validity=self.cleaned_data[u'validity'],
                send_email=self.cleaned_data[u'send_email'],
                )

        if commit:
            invitation.save()
        return invitation

    def save_m2m(self):
        pass

class InvitationAdminBulkAddForm(forms.Form):
    emails = forms.CharField(
            validators=[ValidatorChain(
                validate_comma_separated_emails,
                validate_unused_emails,
                )],
            widget=admin.widgets.AdminTextareaWidget(),
            help_text=squeeze(u"""
                Comma separated list of email address to invite.
                """),
            )
    validity = forms.IntegerField(
            min_value=0,
            initial=app_settings.DEFAULT_VALIDITY,
            help_text=squeeze(u"""
                Number of days the invitation will be valid.
                """),
            )
    invitor = Invitation._meta.get_field(u'invitor').formfield(
            widget=admin.widgets.ForeignKeyRawIdWidget(
                Invitation._meta.get_field(u'invitor').rel, admin.site),
            )
    send_email = forms.BooleanField(
            initial=True,
            required=False,
            help_text=squeeze(u"""
                Check to send the invitation e-mail to the given address. Leave the checkbox empty
                if you just want to create a fake invitation without sending any real e-mail. For
                instance, if you want to send the invitation e-mail manually.
                """),
            )

    class _meta:
        model = Invitation
        labels = None
        help_texts = None

    def __init__(self, *args, **kwargs):
        self.instance = Invitation()
        user = kwargs.pop(u'user')
        super(InvitationAdminBulkAddForm, self).__init__(*args, **kwargs)

        self.initial[u'invitor'] = user

    def save(self):
        assert self.is_valid()

        invitations = []
        for name, email in getaddresses([self.cleaned_data[u'emails']]):
            invitation = Invitation.create(
                    email=email,
                    invitor=self.cleaned_data[u'invitor'],
                    validity=self.cleaned_data[u'validity'],
                    send_email=self.cleaned_data[u'send_email'],
                    )
            invitation.save()
            invitations.append(invitation)

        return invitations

class InvitationAdmin(AdminLiveFieldsMixin, admin.ModelAdmin):
    list_display = [
            u'invitation_column',
            u'email',
            u'accepted_column',
            u'created',
            u'invitor_column',
            u'invitee_column',
            ]
    list_filter = [
            u'created',
            simple_list_filter_factory(u'Status', u'status', [
                (u'2', u'Expired', lambda qs: qs.expired()),
                (u'1', u'Accepted',  lambda qs: qs.accepted()),
                (u'0', u'Pending',  lambda qs: qs.pending()),
                ]),
            ]
    search_fields = [
            u'=id',
            u'email',
            u'invitor__first_name',
            u'invitor__last_name',
            u'invitor__email',
            u'invitee__first_name',
            u'invitee__last_name',
            u'invitee__email',
            ]
    ordering = [u'-created', u'-pk']

    @decorate(short_description=u'Invitation')
    @decorate(admin_order_field=u'pk')
    def invitation_column(self, invitation):
        return admin_obj_format(invitation, link=False)

    @decorate(short_description=u'Accepted')
    @decorate(boolean=True)
    def accepted_column(self, invitation):
        if invitation.is_accepted:
            return True
        elif invitation.is_expired:
            return False
        else:
            return None

    @decorate(short_description=u'Invitor')
    @decorate(admin_order_field=u'invitor__email')
    def invitor_column(self, invitation):
        user = invitation.invitor
        return admin_obj_format(user, u'{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'Invitee')
    @decorate(admin_order_field=u'invitee__email')
    def invitee_column(self, invitation):
        user = invitation.invitee
        return admin_obj_format(user, u'{obj.first_name} {obj.last_name} <{obj.email}>')

    form_add = InvitationAdminAddForm
    form_change = forms.ModelForm
    fieldsets = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'email',
                    u'accepted_column',
                    u'accept_url',
                    u'invitor',
                    u'invitor_details_live',
                    u'invitee',
                    u'invitee_details_live',
                    ],
                }),
            (u'Advanced', {
                u'classes': [u'wide', u'collapse'],
                u'fields': [
                    u'created',
                    u'valid_to',
                    u'accepted',
                    u'message',
                    u'message_details_live',
                    ],
                }),
            ]
    fieldsets_add = [
            (None, {
                u'fields': [
                    u'email',
                    u'validity',
                    u'invitor',
                    u'invitor_details_live',
                    u'send_email',
                    ],
                }),
            ]
    fieldsets_bulk_add = [
            (None, {
                u'fields': [
                    u'emails',
                    u'validity',
                    u'invitor',
                    u'invitor_details_live',
                    u'send_email',
                    ],
                }),
            ]
    live_fields = [
            u'invitor_details_live',
            u'invitee_details_live',
            u'message_details_live',
            ]
    readonly_fields = live_fields + [
            u'accepted_column',
            u'accept_url',
            ]
    raw_id_fields = [
            u'invitor',
            u'invitee',
            u'message',
            ]

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'invitor')
    def invitor_details_live(self, invitor):
        user = invitor
        return admin_obj_format(user, u'{tag}\n{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'invitee')
    def invitee_details_live(self, invitee):
        user = invitee
        return admin_obj_format(user, u'{tag}\n{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'message')
    def message_details_live(self, message):
        return admin_obj_format(message)

    def get_queryset(self, request):
        queryset = super(InvitationAdmin, self).get_queryset(request)
        queryset = queryset.select_related(u'invitor', u'invitee')
        return queryset

    @transaction.atomic
    def bulk_add_view(self, request):
        invitations = None
        if request.method == u'POST':
            form = InvitationAdminBulkAddForm(request.POST, user=request.user)
            if form.is_valid():
                invitations = form.save()
        else:
            form = InvitationAdminBulkAddForm(user=request.user)

        opts = self.model._meta
        template = u'admin/%s/%s/bulk_add_form.html' % (opts.app_label, opts.model_name)
        adminForm = admin.helpers.AdminForm(form,
                fieldsets=self.fieldsets_bulk_add,
                prepopulated_fields={},
                readonly_fields=self.readonly_fields,
                model_admin=self,
                )

        return render(request, template, {
            u'invitations': invitations,
            u'object': None,
            u'title': 'Bulk add %s' % force_text(opts.verbose_name),
            u'opts': opts,
            u'adminform': adminForm,
            u'media': self.media + adminForm.media,
            })

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = patterns('',
                url(r'^bulk-add/$', self.admin_site.admin_view(self.bulk_add_view), name=u'%s_%s_bulk_add' % info),
                )
        return urls + super(InvitationAdmin, self).get_urls()

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(InvitationAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            self.form = self.form_add
            form = super(InvitationAdmin, self).get_form(request, obj, **kwargs)
            form = partial(form, user=request.user)
        else:
            self.form = self.form_change
            form = super(InvitationAdmin, self).get_form(request, obj, **kwargs)
        return form

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(InvitationAdmin, self).get_formsets(request, obj)

admin.site.register(Invitation, InvitationAdmin)
