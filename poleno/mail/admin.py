# vim: expandtab
# -*- coding: utf-8 -*-
from functools import partial
from email.utils import parseaddr, getaddresses

from django import forms
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.utils import formats
from django.utils.http import urlencode
from django.utils.html import escape
from django.contrib import admin
from django.contrib.sessions.models import Session

from poleno.attachments.forms import AttachmentsField
from poleno.attachments.admin import AttachmentInline
from poleno.utils.models import after_saved
from poleno.utils.forms import validate_formatted_email, validate_comma_separated_emails
from poleno.utils.misc import decorate, squeeze
from poleno.utils.admin import simple_list_filter_factory, admin_obj_format

from .models import Message, Recipient

class RecipientInlineForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(RecipientInlineForm, self).clean()

        # Validate correct status for inbound/outbound message
        message = cleaned_data.get(u'message', None)
        status = cleaned_data.get(u'status', None)
        if status and message:
            if message.type == Message.TYPES.INBOUND and status not in Recipient.INBOUND_STATUSES:
                self.add_error(u'status', u'Must be an inbound status.')
            elif message.type == Message.TYPES.OUTBOUND and status not in Recipient.OUTBOUND_STATUSES:
                self.add_error(u'status', u'Must be an outbound status.')

        return cleaned_data

class RecipientInlineFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super(RecipientInlineFormSet, self).clean()

        # Validate recipient set is not empty
        for form in self.forms:
            if not form.is_valid():
                break # Other errors exist, give up
            if form.cleaned_data and not form.cleaned_data.get(u'DELETE'):
                break # There is a valid recipint
        else:
            raise ValidationError(u'Recipients are required.')

class RecipientInline(admin.TabularInline):
    model = Recipient
    form = RecipientInlineForm
    formset = RecipientInlineFormSet
    extra = 0

    fields = [
            u'type',
            u'name',
            u'mail',
            u'status',
            u'status_details',
            u'remote_id',
            ]

class MessageAdminAddForm(forms.ModelForm):
    from_formatted = forms.CharField(
            label=u'From',
            help_text=escape(squeeze(u"""
                Sender e-mail address, e.g. "John Smith <smith@example.com>".
                """)),
            validators=[validate_formatted_email],
            widget=admin.widgets.AdminTextInputWidget(),
            )
    to_formatted = forms.CharField(
            label=u'To',
            help_text=escape(squeeze(u"""
                Comma separated list of 'To' recipients, e.g. "John Smith <smith@example.com>,
                agency@example.com".
                """)),
            required=False,
            validators=[validate_comma_separated_emails],
            widget=admin.widgets.AdminTextInputWidget(),
            )
    cc_formatted = forms.CharField(
            label=u'Cc',
            help_text=escape(squeeze(u"""
                Comma separated list of 'Cc' recipients, e.g. "John Smith <smith@example.com>,
                agency@example.com".
                """)),
            required=False,
            validators=[validate_comma_separated_emails],
            widget=admin.widgets.AdminTextInputWidget(),
            )
    bcc_formatted = forms.CharField(
            label=u'Bcc',
            help_text=escape(squeeze(u"""
                Comma separated list of 'Bcc' recipients, e.g. "John Smith <smith@example.com>,
                agency@example.com".
                """)),
            required=False,
            validators=[validate_comma_separated_emails],
            widget=admin.widgets.AdminTextInputWidget(),
            )
    attachments = AttachmentsField(
            required=False,
            upload_url_func=(lambda: reverse(u'admin:attachments_attachment_upload')),
            download_url_func=(lambda a: reverse(u'admin:attachments_attachment_download', args=(a.pk,))),
            )

    def __init__(self, *args, **kwargs):
        attached_to = kwargs.pop(u'attached_to')
        super(MessageAdminAddForm, self).__init__(*args, **kwargs)

        self.fields[u'attachments'].attached_to = attached_to

    def clean(self):
        cleaned_data = super(MessageAdminAddForm, self).clean()

        if u'to_formatted' in cleaned_data and u'cc_formatted' in cleaned_data and u'bcc_formatted' in cleaned_data:
            if not cleaned_data[u'to_formatted'] and not cleaned_data[u'cc_formatted'] and not cleaned_data[u'bcc_formatted']:
                self.add_error(u'to_formatted', u"At least one of 'To', 'Cc' or 'Bcc' is required.")

        return cleaned_data

    def save(self, commit=True):
        assert self.is_valid()

        from_name, from_mail = parseaddr(self.cleaned_data[u'from_formatted'])

        message = Message(
                type=self.cleaned_data[u'type'],
                processed=self.cleaned_data[u'processed'],
                from_name=from_name,
                from_mail=from_mail,
                received_for=self.cleaned_data[u'received_for'],
                subject=self.cleaned_data[u'subject'],
                text=self.cleaned_data[u'text'],
                html=self.cleaned_data[u'html'],
                headers=self.cleaned_data[u'headers'],
                )

        @after_saved(message)
        def deferred(message):
            message.attachment_set = self.cleaned_data[u'attachments']

            status = (Recipient.STATUSES.INBOUND if message.type == Message.TYPES.INBOUND else
                      Recipient.STATUSES.QUEUED if message.processed is None else
                      Recipient.STATUSES.SENT)

            for field, type in [
                    (u'to_formatted', Recipient.TYPES.TO),
                    (u'cc_formatted', Recipient.TYPES.CC),
                    (u'bcc_formatted', Recipient.TYPES.BCC),
                    ]:
                for name, mail in getaddresses([self.cleaned_data[field]]):
                    recipient = Recipient(
                            message=message,
                            name=name,
                            mail=mail,
                            type=type,
                            status=status,
                            )
                    recipient.save()

        if commit:
            message.save()
        return message

    def save_m2m(self):
        pass

class MessageAdmin(admin.ModelAdmin):
    list_display = [
            u'message_column',
            u'type',
            u'from_formatted_column',
            u'recipients_formatted_column',
            u'processed',
            ]
    list_filter = [
            u'type',
            simple_list_filter_factory(u'Processed', u'processed', [
                (u'1', u'Yes', lambda qs: qs.processed()),
                (u'0', u'No',  lambda qs: qs.not_processed()),
                ]),
            u'processed',
            ]
    search_fields = [
            u'=id',
            u'from_name',
            u'from_mail',
            u'recipient__name',
            u'recipient__mail',
            u'received_for',
            ]
    ordering = [u'-processed', u'-pk']

    @decorate(short_description=u'Message')
    @decorate(admin_order_field=u'pk')
    def message_column(self, message):
        return admin_obj_format(message, link=False)

    @decorate(short_description=u'From')
    @decorate(admin_order_field=u'from_mail')
    def from_formatted_column(self, message):
        return message.from_formatted

    @decorate(short_description=u'Recipients')
    def recipients_formatted_column(self, message):
        res = []
        for label, formatted in [
                (u'To', message.to_formatted),
                (u'Cc', message.cc_formatted),
                (u'Bcc', message.bcc_formatted),
                ]:
            if formatted:
                res.append(u'%s: %s' % (label, formatted))
        return u'; '.join(res)

    form_add = MessageAdminAddForm
    form_change = forms.ModelForm
    fieldsets = (
            (None, {
                u'fields': [
                    u'type',
                    u'processed',
                    u'from_name',
                    u'from_mail',
                    u'received_for',
                    u'subject',
                    (u'text', u'html'),
                    ],
                }),
            (u'Advanced', {
                u'classes': [u'collapse'],
                u'fields': [
                    u'headers',
                    ],
                }),
            )
    fieldsets_add = (
            (None, {
                u'fields': [
                    u'type',
                    u'processed',
                    u'from_formatted',
                    u'to_formatted',
                    u'cc_formatted',
                    u'bcc_formatted',
                    u'received_for',
                    u'subject',
                    (u'text', u'html'),
                    u'attachments',
                    ],
                }),
            (u'Advanced', {
                u'classes': [u'collapse'],
                u'fields': [
                    u'headers',
                    ],
                }),
            )
    inlines = [
            RecipientInline,
            AttachmentInline,
            ]

    def render_change_form(self, request, context, **kwargs):
        message = kwargs.get(u'obj', None)

        # Reply button
        if message and message.processed:
            query = {}
            query[u'type'] = Message.TYPES.INBOUND if message.type == Message.TYPES.OUTBOUND else Message.TYPES.OUTBOUND
            query[u'to_formatted'] = message.from_formatted
            query[u'subject'] = u'%s%s' % (u'' if message.subject.startswith(u'Re:') else u'Re: ', message.subject)

            if message.received_for:
                query[u'from_formatted'] = message.received_for
            else:
                sender = message.recipients_to.first() or message.recipients.first()
                if sender:
                    query[u'from_formatted'] = sender.formatted

            date = formats.date_format(message.processed, u'DATETIME_FORMAT')
            name = message.from_name or message.from_mail
            quote = u'On {date}, {name} wrote:'.format(date=date, name=name)
            query[u'text'] = u'\n\n%s\n%s\n' % (quote, u'\n'.join(u'> %s' % l for l in message.text.split(u'\n')))
            query[u'html'] = u'\n\n%s\n%s\n' % (quote, u'\n'.join(u'> %s' % l for l in message.html.split(u'\n')))

            context[u'reply_url'] = u'%s?%s' % (reverse(u'admin:mail_message_add'), urlencode(query))

        return super(MessageAdmin, self).render_change_form(request, context, **kwargs)

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(MessageAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            self.form = self.form_add
            form = super(MessageAdmin, self).get_form(request, obj, **kwargs)
            session = Session.objects.get(session_key=request.session.session_key)
            form = partial(form, attached_to=session)
        else:
            self.form = self.form_change
            form = super(MessageAdmin, self).get_form(request, obj, **kwargs)
        return form

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(MessageAdmin, self).get_formsets(request, obj)

admin.site.register(Message, MessageAdmin)
