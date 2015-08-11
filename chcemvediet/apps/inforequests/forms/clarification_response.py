# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from django import forms
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.contrib.sessions.models import Session

from poleno.attachments.forms import AttachmentsField
from poleno.utils.models import after_saved
from poleno.utils.date import local_today
from poleno.utils.forms import CompositeTextField
from poleno.utils.misc import squeeze
from chcemvediet.apps.wizards import Wizard, WizardStep


class ClarificationResponseStep(WizardStep):
    template = u'inforequests/clarification_response/step.html'
    text_template = u'inforequests/clarification_response/texts/main.html'
    form_template = u'main/snippets/form_horizontal.html'

    content = CompositeTextField(
            label=_(u'inforequests:ClarificationResponseStep:content:label'),
            template=u'inforequests/clarification_response/forms/content.txt',
            fields=[
                forms.CharField(widget=forms.Textarea(attrs={
                    u'placeholder': _(u'inforequests:ClarificationResponseStep:content:placeholder'),
                    u'class': u'autosize',
                    u'cols': u'', u'rows': u'',
                    })),
                ],
            composite_attrs={
                u'class': u'input-block-level',
                },
            )
    attachments = AttachmentsField(
            label=_(u'inforequests:ClarificationResponseStep:attachments:label'),
            required=False,
            upload_url_func=(lambda: reverse(u'inforequests:upload_attachment')),
            download_url_func=(lambda a: reverse(u'inforequests:download_attachment', args=[a.pk])),
            )

    def __init__(self, *args, **kwargs):
        super(ClarificationResponseStep, self).__init__(*args, **kwargs)
        session = Session.objects.get(session_key=self.wizard.request.session.session_key)
        self.fields[u'content'].widget.context.update(self.context())
        self.fields[u'attachments'].attached_to = (self.wizard.draft, session)

    def commit(self):
        super(ClarificationResponseStep, self).commit()

        @after_saved(self.wizard.draft)
        def deferred(draft):
            for attachment in self.cleaned_data[u'attachments']:
                attachment.generic_object = draft
                attachment.save()

    def values(self):
        res = super(ClarificationResponseStep, self).values()
        res[u'subject'] = squeeze(render_to_string(u'inforequests/clarification_response/forms/subject.txt'))
        res[u'content'] = self.fields[u'content'].finalize(self.cleaned_data[u'content'])
        return res

class ClarificationResponseWizard(Wizard):
    step_classes = OrderedDict([
            (u'step', ClarificationResponseStep),
            ])

    def __init__(self, request, branch):
        super(ClarificationResponseWizard, self).__init__(request)
        self.instance_id = u'%s-%s' % (self.__class__.__name__, branch.last_action.pk)
        self.branch = branch

    def get_step_url(self, step, anchor=u''):
        return reverse(u'inforequests:clarification_response',
                args=[self.branch.inforequest.pk, self.branch.pk, step.index]) + anchor

    def context(self, extra=None):
        res = super(ClarificationResponseWizard, self).context(extra)
        res.update({
                u'inforequest': self.branch.inforequest,
                u'branch': self.branch,
                u'last_action': self.branch.last_action,
                })
        return res

    def save(self, action):
        action.branch = self.branch
        action.subject = self.values[u'subject']
        action.content = self.values[u'content']
        action.effective_date = local_today()

        @after_saved(action)
        def deferred(action):
            action.attachment_set = self.values[u'attachments']
