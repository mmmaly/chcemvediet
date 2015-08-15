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
from chcemvediet.apps.inforequests.models import Action, InforequestEmail

class ObligeeActionStep(WizardStep):
    template = u'inforequests/obligee_action/wizard.html'


class BasicsStep(ObligeeActionStep):
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
        res[u'result_branch'] = self.cleaned_data[u'branch']
        res[u'result_effective_date'] = self.cleaned_data[u'effective_date'] if not self.wizard.email else None
        res[u'result_file_number'] = self.cleaned_data[u'file_number']
        res[u'result_attachments'] = self.cleaned_data[u'attachments'] if not self.wizard.email else None
        return res

class IsQuestionStep(ObligeeActionStep):
    text_template = u'inforequests/obligee_action/texts/is_question.html'
    form_template = u'main/snippets/form_horizontal.html'

    is_question = forms.TypedChoiceField(
            label=u' ',
            coerce=int,
            choices=(
                (1, _(u'inforequests:obligee_action:IsQuestionStep:yes')),
                (0, _(u'inforequests:obligee_action:IsQuestionStep:no')),
                ),
            widget=forms.RadioSelect(),
            )

    @classmethod
    def applicable(cls, wizard):
        result = wizard.values.get(u'result', None)
        branch = wizard.values.get(u'branch', None)
        return not result and branch and branch.can_add_clarification_request

    def values(self):
        res = super(IsQuestionStep, self).values()
        if self.cleaned_data[u'is_question']:
            res[u'result'] = u'action'
            res[u'result_action'] = Action.TYPES.CLARIFICATION_REQUEST
        return res

class IsConfirmationStep(ObligeeActionStep):
    text_template = u'inforequests/obligee_action/texts/is_confirmation.html'
    form_template = u'main/snippets/form_horizontal.html'

    is_confirmation = forms.TypedChoiceField(
            label=u' ',
            coerce=int,
            choices=(
                (1, _(u'inforequests:obligee_action:IsConfirmationStep:yes')),
                (0, _(u'inforequests:obligee_action:IsConfirmationStep:no')),
                ),
            widget=forms.RadioSelect(),
            )

    @classmethod
    def applicable(cls, wizard):
        result = wizard.values.get(u'result', None)
        branch = wizard.values.get(u'branch', None)
        return not result and branch and branch.can_add_confirmation

    def values(self):
        res = super(IsConfirmationStep, self).values()
        if self.cleaned_data[u'is_confirmation']:
            res[u'result'] = u'action'
            res[u'result_action'] = Action.TYPES.CONFIRMATION
        return res

class NotCategorizedStep(ObligeeActionStep):
    text_template = u'inforequests/obligee_action/texts/not_categorized.html'
    form_template = u'main/snippets/form_horizontal.html'

    wants_help = forms.TypedChoiceField(
            label=u' ',
            coerce=int,
            choices=(
                (1, _(u'inforequests:obligee_action:NotCategorizedStep:help')),
                (0, _(u'inforequests:obligee_action:NotCategorizedStep:unrelated')),
                ),
            widget=forms.RadioSelect(attrs={
                u'class': u'toggle-changed',
                u'data-container': u'form',
                u'data-target-1': u'.control-group:has(.visible-if-wants-help)',
                }),
            )
    help_request = forms.CharField(
            label=_(u'inforequests:obligee_action:NotCategorizedStep:help_request:label'),
            required=False,
            widget=forms.Textarea(attrs={
                u'placeholder': _(u'inforequests:obligee_action:NotCategorizedStep:help_request:placeholder'),
                u'class': u'input-block-level visible-if-wants-help',
                }),
            )

    @classmethod
    def applicable(cls, wizard):
        result = wizard.values.get(u'result', None)
        return not result

    def clean(self):
        cleaned_data = super(NotCategorizedStep, self).clean()

        wants_help = cleaned_data.get(u'wants_help', None)
        help_request = cleaned_data.get(u'help_request', None)
        if wants_help and not help_request:
            msg = self.fields[u'help_request'].error_messages[u'required']
            self.add_error(u'help_request', msg)

        return cleaned_data

    def values(self):
        res = super(NotCategorizedStep, self).values()
        if self.cleaned_data[u'wants_help']:
            res[u'result'] = u'help'
            res[u'result_help'] = self.cleaned_data[u'help_request']
        else:
            res[u'result'] = u'unrelated'
        return res

class CategorizedStep(ObligeeActionStep):
    text_template = u'inforequests/obligee_action/texts/categorized.html'

    @classmethod
    def applicable(cls, wizard):
        result = wizard.values.get(u'result', None)
        return result == u'action'


class ObligeeActionWizard(Wizard):
    step_classes = OrderedDict([
            (u'basics', BasicsStep),
            (u'is_question', IsQuestionStep),
            (u'is_confirmation', IsConfirmationStep),
            (u'not_categorized', NotCategorizedStep),
            (u'categorized', CategorizedStep),
            ])

    def __init__(self, request, inforequest, inforequestemail, email):
        super(ObligeeActionWizard, self).__init__(request)
        self.instance_id = u'%s-%s' % (self.__class__.__name__, inforequest.pk)
        self.inforequest = inforequest
        self.inforequestemail = inforequestemail
        self.email = email

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

    def save_action(self):
        assert self.values[u'result'] == u'action'
        assert self.values[u'result_action'] in Action.OBLIGEE_ACTION_TYPES
        assert not self.email or self.values[u'result_action'] in Action.OBLIGEE_EMAIL_ACTION_TYPES
        assert self.values[u'result_branch'].can_add_action(self.values[u'result_action'])

        action = Action(type=self.values[u'result_action'])
        action.branch = self.values[u'result_branch']
        action.email = self.email if self.email else None
        action.subject = self.email.subject if self.email else u''
        action.content = self.email.text if self.email else u''
        action.effective_date = (
                local_date(self.email.processed) if self.email else
                self.values[u'result_effective_date'])
        action.file_number = self.values.get(u'result_file_number', u'')
        action.deadline = self.values.get(u'result_deadline', None)
        action.disclosure_level = self.values.get(u'result_disclosure_level', None)
        action.refusal_reason = self.values.get(u'result_refusal_reason', None)
        action.save()

        if self.email:
            for attch in self.email.attachments:
                attachment = attch.clone(action)
                attachment.save()
        else:
            action.attachment_set = self.values[u'result_attachments']

        if self.email:
            self.inforequestemail.type = InforequestEmail.TYPES.OBLIGEE_ACTION
            self.inforequestemail.save(update_fields=[u'type'])

        return action

    def save_help(self):
        assert self.values[u'result'] == u'help'
        # FIXME: use wizard.values[u'result_help'] to create a ticket

        if self.email:
            self.inforequestemail.type = InforequestEmail.TYPES.UNKNOWN
            self.inforequestemail.save(update_fields=[u'type'])

    def save_unrelated(self):
        assert self.values[u'result'] == u'unrelated'

        if self.email:
            self.inforequestemail.type = InforequestEmail.TYPES.UNRELATED
            self.inforequestemail.save(update_fields=[u'type'])
