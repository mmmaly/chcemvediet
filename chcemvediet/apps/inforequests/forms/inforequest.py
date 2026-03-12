# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe

from poleno.attachments.forms import AttachmentsField
from poleno.utils.models import after_saved
from poleno.utils.urls import reverse
from poleno.utils.forms import CompositeTextField, PrefixedForm
from poleno.utils.template import render_to_string
from poleno.utils.misc import parsefilesize
from chcemvediet.apps.obligees.forms import ObligeeWidget, ObligeeField
from chcemvediet.apps.inforequests.models import Inforequest


class InforequestForm(PrefixedForm):
    obligee = ObligeeField(
            label=_(u'inforequests:InforequestForm:obligee:label'),
            help_text=_(u'inforequests:InforequestForm:obligee:help_text'),
            widget=ObligeeWidget(input_attrs={
                u'placeholder': _(u'inforequests:InforequestForm:obligee:placeholder'),
                }),
            )
    subject = CompositeTextField(
            label=_(u'inforequests:InforequestForm:subject:label'),
            help_text=_(u'inforequests:InforequestForm:subject:help_text'),
            template=u'inforequests/create/forms/subject.txt',
            fields=[
                forms.CharField(max_length=50, widget=forms.TextInput(attrs={
                    u'placeholder': _(u'inforequests:InforequestForm:subject:placeholder'),
                    })),
                ],
            )
    content = CompositeTextField(
            label=_(u'inforequests:InforequestForm:content:label'),
            template=u'inforequests/create/forms/content.txt',
            fields=[
                forms.CharField(widget=forms.Textarea(attrs={
                    u'placeholder': _(u'inforequests:InforequestForm:content:placeholder'),
                    u'class': u'pln-autosize',
                    u'cols': u'', u'rows': u'',
                    })),
                ],
            composite_attrs={
                },
            )
    attachments = AttachmentsField(
            label=_(u'inforequests:InforequestForm:attachments:label'),
            help_text=_(u'inforequests:InforequestForm:attachments:help_text'),
            required=False,
            max_count=20,
            max_size=parsefilesize(u'15 MB'),
            max_total_size=parsefilesize(u'15 MB'),
            upload_url_func=(lambda: reverse(u'inforequests:upload_attachment')),
            download_url_func=(lambda a: reverse(u'inforequests:download_attachment', args=[a.pk])),
            )

    def __init__(self, *args, **kwargs):
        self.draft = kwargs.pop(u'draft', False)
        self.attached_to = kwargs.pop(u'attached_to')
        self.user = kwargs.pop(u'user')
        super(InforequestForm, self).__init__(*args, **kwargs)

        unique_email = settings.INFOREQUEST_UNIQUE_EMAIL.format(token=u'xxxx')
        unique_email = mark_safe(render_to_string(u'inforequests/create/snippets/content_unique_email.html',
                dict(unique_email=unique_email)).strip())
        self.fields[u'content'].widget.context[u'user'] = self.user
        self.fields[u'content'].widget.context[u'unique_email'] = unique_email
        self.fields[u'attachments'].attached_to = self.attached_to

        if self.draft:
            self.fields[u'obligee'].required = False
            self.fields[u'obligee'].email_required = False
            self.fields[u'subject'].required = False
            self.fields[u'content'].required = False
            self.fields[u'attachments'].max_count = None
            self.fields[u'attachments'].max_size = None
            self.fields[u'attachments'].max_total_size = None

    def save(self):
        assert self.is_valid()
        subject_finalize = lambda inforequest: self.fields[u'subject'].finalize(
                self.cleaned_data[u'subject'])
        content_finalize = lambda inforequest: self.fields[u'content'].finalize(
                self.cleaned_data[u'content'], dict(
                    unique_email=inforequest.unique_email,
                    obligee=self.cleaned_data[u'obligee'],
                    ))
        inforequest = Inforequest.create(
                applicant=self.user,
                subject=self.cleaned_data[u'subject'][0],
                content=self.cleaned_data[u'content'][0],
                obligee=self.cleaned_data[u'obligee'],
                subject_finalize=subject_finalize,
                content_finalize=content_finalize,
                attachments=self.cleaned_data[u'attachments'],
                )
        return inforequest

    def save_to_draft(self, draft):
        assert self.is_valid()

        draft.obligee = self.cleaned_data[u'obligee']
        draft.subject = self.cleaned_data[u'subject']
        draft.content = self.cleaned_data[u'content']

        @after_saved(draft)
        def deferred(draft):
            # The new list of attachments may not be directly assigned to ``draft.attachment_set``
            # because the assignment would clear ``draft.attachment_set`` before adding the new
            # attachments. Any attachment that is in both the old and the new list would be deleted
            # and then saved again emitting ``*_delete`` signals and deleting its cascaded
            # relations.
            old_attachments = set(draft.attachment_set.all())
            new_attachments = []
            for attachment in self.cleaned_data[u'attachments']:
                if attachment in old_attachments:
                    old_attachments.remove(attachment)
                else:
                    new_attachments.append(attachment)
            draft.attachment_set.remove(*old_attachments)
            draft.attachment_set.add(*new_attachments)

    def load_from_draft(self, draft):
        self.initial[u'obligee'] = draft.obligee
        self.initial[u'subject'] = draft.subject
        self.initial[u'content'] = draft.content
        self.initial[u'attachments'] = draft.attachments
