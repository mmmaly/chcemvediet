# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.utils import formats
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.contrib.contenttypes import generic

from poleno.attachments.models import Attachment
from poleno.utils.misc import decorate

from .models import Message, Recipient

class AttachmentInline(generic.GenericTabularInline):
    model = Attachment
    ct_field = u'generic_type'
    ct_fk_field = u'generic_id'
    extra = 0

    readonly_fields = [u'size']
    fields = [
            u'file',
            u'name',
            u'content_type',
            u'created',
            u'size',
            ]

class RecipientInlineForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(RecipientInlineForm, self).clean()

        # Validate correct status for inbound/outbound message
        message = cleaned_data.get(u'message', None)
        status = cleaned_data.get(u'status', None)
        if status and message:
            if message.type == Message.TYPES.INBOUND and status not in Recipient.INBOUND_STATUSES:
                self._errors[u'status'] = self.error_class([_(u'Must be an inbound status.')])
                del cleaned_data[u'status']
            elif message.type == Message.TYPES.OUTBOUND and status not in Recipient.OUTBOUND_STATUSES:
                self._errors[u'status'] = self.error_class([_(u'Must be an outbound status.')])
                del cleaned_data[u'status']

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

    def get_extra(self, request, obj=None, **kwargs):
        try:
            return int(request.GET[u'recipients'])
        except (ValueError, KeyError):
            return 0

    def get_formset(self, request, obj=None, **kwargs):
        formset = super(RecipientInline, self).get_formset(request, obj, **kwargs)

        # Recipients initial values passed in GET
        initial = []
        count = self.get_extra(request, obj, **kwargs)
        for i in range(count):
            prefix = u'recipients-%s-' % i
            initial.append({k[len(prefix):]: v for k, v in request.GET.items() if k.startswith(prefix)})

        class new_formset(formset):
            def __init__(self, *args, **kwargs):
                kwargs.update({u'initial': initial})
                formset.__init__(self, *args, **kwargs)

        return new_formset

class ProcessedListFilter(admin.SimpleListFilter):
    title = _(u'Processed')
    parameter_name = u'processed'

    def lookups(self, request, model_admin):
        yield (u'1', _(u'Processed'))
        yield (u'0', _(u'Not Processed'))

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.processed()
        if self.value() == '0':
            return queryset.not_processed()

class MessageAdmin(admin.ModelAdmin):
    # FIXME: Only admins with correct permissions should be able to add/edit/delete messages.
    # FIXME: Some admins should only be able to change recipient statuses.
    list_display = [
            u'message_column',
            u'type',
            u'subject',
            u'from_column',
            u'recipients_column',
            u'processed',
            ]
    list_filter = [
            u'type',
            ProcessedListFilter,
            u'processed',
            ]
    search_fields = [
            u'from_name',
            u'from_mail',
            u'received_for',
            u'subject',
            u'text',
            u'html',
            u'recipient__name',
            u'recipient__mail',
            ]

    @decorate(short_description=_(u'Message'))
    @decorate(admin_order_field=u'pk')
    def message_column(self, message):
        return repr(message)

    @decorate(short_description=_(u'From'))
    @decorate(admin_order_field=u'from_mail')
    def from_column(self, message):
        return message.from_formatted

    @decorate(short_description=_(u'Recipients'))
    def recipients_column(self, message):
        res = []
        for label, formatted in [
                (u'To', message.to_formatted),
                (u'Cc', message.cc_formatted),
                (u'Bcc', message.bcc_formatted),
                ]:
            if formatted:
                res.append(u'%s: %s' % (label, formatted))
        return u'; '.join(res)

    fieldsets = (
            (None, {
                u'fields': [
                    u'type',
                    u'processed',
                    (u'from_name', u'from_mail'),
                    u'received_for',
                    u'subject',
                    (u'text', u'html'),
                    ],
                }),
            (_(u'Advanced'), {
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
            query[u'subject'] = message.subject if message.subject.startswith(u'Re: ') else u'Re: %s' % message.subject

            date = formats.date_format(message.processed, u'DATETIME_FORMAT')
            name = message.from_name or message.from_mail
            quote = _(u'On {date}, {name} wrote:').format(date=date, name=name)
            query[u'text'] = u'\n\n%s\n%s\n' % (quote, u'\n'.join(u'> %s' % l for l in message.text.split(u'\n')))
            query[u'html'] = u'\n\n%s\n%s\n' % (quote, u'\n'.join(u'> %s' % l for l in message.html.split(u'\n')))

            if message.received_for:
                query[u'from_mail'] = message.received_for
            else:
                sender = message.recipient_set.to().first() or message.recipient_set.first()
                if sender:
                    query[u'from_name'] = sender.name
                    query[u'from_mail'] = sender.mail

            query[u'recipients'] = 1
            query[u'recipients-0-name'] = message.from_name
            query[u'recipients-0-mail'] = message.from_mail
            query[u'recipients-0-type'] = Recipient.TYPES.TO
            query[u'recipients-0-status'] = Recipient.STATUSES.INBOUND if message.type == Message.TYPES.OUTBOUND else Recipient.STATUSES.QUEUED

            context[u'reply_url'] = u'%s?%s' % (reverse(u'admin:mail_message_add'), urlencode(query))

        return super(MessageAdmin, self).render_change_form(request, context, **kwargs)

admin.site.register(Message, MessageAdmin)
