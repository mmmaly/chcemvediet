# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.sessions.models import Session

from poleno.attachments.forms import AttachmentsField
from poleno.utils.models import after_saved
from poleno.utils.urls import reverse
from poleno.utils.date import local_today
from poleno.utils.forms import CompositeTextField
from poleno.utils.template import render_to_string
from poleno.utils.misc import squeeze, parsefilesize
from chcemvediet.apps.wizards.wizard import Step, Wizard
from chcemvediet.apps.inforequests.models import Action


class Main(Step):
    template = u'inforequests/clarification_response/main.html'
    text_template = u'inforequests/clarification_response/texts/main.html'
    form_template = u'main/forms/form_horizontal.html'
    global_fields = [u'attachments']

    def add_fields(self):
        super(Main, self).add_fields()

        self.fields[u'content'] = CompositeTextField(
                label=_(u'inforequests:clarification_response:Main:content:label'),
                template=u'inforequests/clarification_response/forms/content.txt',
                context=self.context(),
                fields=[
                    forms.CharField(widget=forms.Textarea(attrs={
                        u'placeholder':
                            _(u'inforequests:clarification_response:Main:content:placeholder'),
                        u'class': u'pln-autosize',
                        u'cols': u'', u'rows': u'',
                        })),
                    ],
                composite_attrs={
                    },
                )

        self.fields[u'attachments'] = AttachmentsField(
                label=_(u'inforequests:clarification_response:Main:attachments:label'),
                help_text=_(u'inforequests:clarification_response:Main:attachments:help_text'),
                required=False,
                max_count=20,
                max_size=parsefilesize(u'15 MB'),
                max_total_size=parsefilesize(u'15 MB'),
                attached_to=(
                    self.wizard.draft,
                    Session.objects.get(session_key=self.wizard.request.session.session_key),
                    ),
                upload_url_func=(
                    lambda: reverse(u'inforequests:upload_attachment')),
                download_url_func=(
                    lambda a: reverse(u'inforequests:download_attachment', args=[a.pk])),
                )

    def clean(self):
        cleaned_data = super(Main, self).clean()

        if self.wizard.branch.inforequest.has_undecided_emails:
            msg = _(u'inforequests:clarification_response:Main:error:undecided_emails')
            self.add_error(None, msg)
        if not self.wizard.branch.collect_obligee_emails:
            msg = _(u'inforequests:clarification_response:Main:error:no_email')
            self.add_error(None, msg)

        return cleaned_data

    def commit(self):
        super(Main, self).commit()

        @after_saved(self.wizard.draft)
        def deferred(draft):
            for attachment in self.cleaned_data.get(u'attachments', []):
                attachment.generic_object = draft
                attachment.save()

    def post_transition(self):
        res = super(Main, self).post_transition()

        if self.is_valid():
            res.globals.update({
                u'subject': squeeze(render_to_string(
                    u'inforequests/clarification_response/forms/subject.txt')),
                u'content': self.fields[u'content'].finalize(self.cleaned_data[u'content']),
                })

        return res

class ClarificationResponseWizard(Wizard):
    first_step_class = Main

    def __init__(self, request, index, branch):
        self.inforequest = branch.inforequest
        self.branch = branch
        self.last_action = branch.last_action
        super(ClarificationResponseWizard, self).__init__(request, index)

    def get_instance_id(self):
        return u'{}-{}'.format(self.__class__.__name__, self.last_action.pk)

    def get_step_url(self, step, anchor=u''):
        return reverse(u'inforequests:clarification_response',
                kwargs=dict(branch=self.branch, step=step)) + anchor

    def context(self, extra=None):
        res = super(ClarificationResponseWizard, self).context(extra)
        res.update({
                u'inforequest': self.inforequest,
                u'branch': self.branch,
                u'last_action': self.last_action,
                })
        return res

    def finish(self):
        today = local_today()
        action = Action.create(
                branch=self.branch,
                type=Action.TYPES.CLARIFICATION_RESPONSE,
                subject=self.values[u'subject'],
                content=self.values[u'content'],
                sent_date=today,
                legal_date=today,
                attachments=self.values[u'attachments'],
                )
        action.save()
        action.send_by_email()

        return action.get_absolute_url()
