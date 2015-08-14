# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict
from dateutil.relativedelta import relativedelta

from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_text
from django.contrib.sessions.models import Session

from poleno.attachments.forms import AttachmentsField
from poleno.utils.models import after_saved
from poleno.utils.forms import AutoSuppressedSelect
from poleno.utils.date import local_date, local_today
from chcemvediet.apps.wizards import Wizard, WizardStep

class BasicsStep(WizardStep):
    template = u'inforequests/obligee_action/wizard.html'
    text_template = u'inforequests/obligee_action/texts/basics.html'
    form_template = u'main/snippets/form_horizontal.html'

    branch = forms.TypedChoiceField(
            label=_(u'inforequests:obligee_action:BasicsStep:branch:label'),
            empty_value=None,
            widget=AutoSuppressedSelect(
                attrs={
                    u'class': u'span5',
                    },
                suppressed_attrs={
                    u'class': u'suppressed-control',
                    }),
            )
    effective_date = forms.DateField(
            label=_(u'inforequests:obligee_action:BasicsStep:effective_date:label'),
            localize=True,
            widget=forms.DateInput(attrs={
                u'placeholder': _('inforequests:obligee_action:BasicsStep:effective_date:placeholder'),
                u'class': u'datepicker',
                }),
            )
    file_number = forms.CharField(
            label=_(u'inforequests:obligee_action:BasicsStep:file_number:label'),
            max_length=255,
            required=False,
            widget=forms.TextInput(attrs={
                u'placeholder': _(u'inforequests:obligee_action:BasicsStep:file_number:placeholder'),
                u'class': u'span5',
                }),
            )
    attachments = AttachmentsField(
            label=_(u'inforequests:obligee_action:BasicsStep:attachments:label'),
            upload_url_func=(lambda: reverse(u'inforequests:upload_attachment')),
            download_url_func=(lambda a: reverse(u'inforequests:download_attachment', args=[a.pk])),
            )

    def __init__(self, *args, **kwargs):
        super(BasicsStep, self).__init__(*args, **kwargs)

        # branch: we assume that converting a Branch to a string gives its ``pk``
        field = self.fields[u'branch']
        field.choices = [(branch, branch.historicalobligee.name)
                for branch in self.wizard.inforequest.branches]
        if len(field.choices) > 1:
            field.choices.insert(0, (u'', u''))

        def coerce(val):
            for o, v in self.fields[u'branch'].choices:
                if o and smart_text(o.pk) == val:
                    return o
            raise ValueError
        field.coerce = coerce

        # effective_date
        if self.wizard.email:
            del self.fields[u'effective_date']

        # attachments
        if self.wizard.email:
            del self.fields[u'attachments']
        else:
            field = self.fields[u'attachments']
            session = Session.objects.get(session_key=self.wizard.request.session.session_key)
            field.attached_to = (self.wizard.draft, session)

    def clean(self):
        cleaned_data = super(BasicsStep, self).clean()

        branch = cleaned_data.get(u'branch', None)
        effective_date = cleaned_data.get(u'effective_date', None)
        if effective_date is not None:
            try:
                if branch and effective_date < branch.last_action.effective_date:
                    raise ValidationError(_(u'inforequests:obligee_action:BasicsStep:effective_date:older_than_previous_error'))
                if effective_date > local_today():
                    raise ValidationError(_(u'inforequests:obligee_action:BasicsStep:effective_date:from_future_error'))
                if effective_date < local_today() - relativedelta(months=1):
                    raise ValidationError(_(u'inforequests:obligee_action:BasicsStep:effective_date:older_than_month_error'))
            except ValidationError as e:
                self.add_error(u'effective_date', e)

        return cleaned_data

    def commit(self):
        super(BasicsStep, self).commit()

        @after_saved(self.wizard.draft)
        def deferred(draft):
            for attachment in self.cleaned_data.get(u'attachments', []):
                attachment.generic_object = draft
                attachment.save()

    def values(self):
        res = super(BasicsStep, self).values()
        if self.wizard.email:
            res[u'effective_date'] = local_date(self.wizard.email.processed)
            res[u'attachments'] = []
        return res


class ObligeeActionWizard(Wizard):
    step_classes = OrderedDict([
            (u'basics', BasicsStep),
            ])

    def __init__(self, request, inforequest):
        super(ObligeeActionWizard, self).__init__(request)
        self.instance_id = u'%s-%s' % (self.__class__.__name__, inforequest.pk)
        self.inforequest = inforequest
        self.email = inforequest.oldest_undecided_email

    def get_step_url(self, step, anchor=u''):
        return reverse(u'inforequests:obligee_action',
                args=[self.inforequest.pk, step.index]) + anchor

    def context(self, extra=None):
        res = super(ObligeeActionWizard, self).context(extra)
        res.update({
                u'inforequest': self.inforequest,
                u'email': self.email,
                })
        return res
