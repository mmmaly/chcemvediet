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
from multiselectfield import MultiSelectFormField

from poleno.attachments.forms import AttachmentsField
from poleno.utils.models import after_saved
from poleno.utils.forms import AutoSuppressedSelect
from poleno.utils.date import local_date, local_today
from chcemvediet.apps.wizards import Wizard, WizardStep
from chcemvediet.apps.obligees.forms import ObligeeWithAddressInput, ObligeeAutocompleteField
from chcemvediet.apps.inforequests.models import Branch, Action, InforequestEmail

class ObligeeActionStep(WizardStep):
    template = u'inforequests/obligee_action/wizard.html'
    form_template = u'main/snippets/form_horizontal.html'


class BasicsStep(ObligeeActionStep):
    text_template = u'inforequests/obligee_action/texts/basics.html'

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

class IsOnTopicStep(ObligeeActionStep):
    text_template = u'inforequests/obligee_action/texts/is_on_topic.html'

    is_on_topic = forms.TypedChoiceField(
            label=u' ',
            coerce=int,
            choices=(
                (1, _(u'inforequests:obligee_action:IsOnTopicStep:yes')),
                (0, _(u'inforequests:obligee_action:IsOnTopicStep:no')),
                ),
            widget=forms.RadioSelect(),
            )

    @classmethod
    def applicable(cls, wizard):
        result = wizard.values.get(u'result', None)
        branch = wizard.values.get(u'branch', None)
        return not result and branch and branch.can_add_refusal

class ContainsInfoStep(ObligeeActionStep):
    text_template = u'inforequests/obligee_action/texts/contains_info.html'

    contains_info = forms.TypedChoiceField(
            label=u' ',
            coerce=int,
            choices=(
                (Action.DISCLOSURE_LEVELS.FULL, _(u'inforequests:obligee_action:ContainsInfoStep:full')),
                (Action.DISCLOSURE_LEVELS.PARTIAL, _(u'inforequests:obligee_action:ContainsInfoStep:partial')),
                (Action.DISCLOSURE_LEVELS.NONE, _(u'inforequests:obligee_action:ContainsInfoStep:none')),
                ),
            widget=forms.RadioSelect(),
            )

    @classmethod
    def applicable(cls, wizard):
        result = wizard.values.get(u'result', None)
        branch = wizard.values.get(u'branch', None)
        is_on_topic = wizard.values.get(u'is_on_topic', True)
        return not result and branch and branch.can_add_refusal and is_on_topic

    def values(self):
        res = super(ContainsInfoStep, self).values()
        res[u'result_disclosure_level'] = self.cleaned_data[u'contains_info']
        if self.cleaned_data[u'contains_info'] == Action.DISCLOSURE_LEVELS.FULL:
            res[u'result'] = u'action'
            res[u'result_action'] = Action.TYPES.DISCLOSURE
        return res

class IsDecisionStep(ObligeeActionStep):
    text_template = u'inforequests/obligee_action/texts/is_decision.html'

    is_decision = forms.TypedChoiceField(
            label=u' ',
            coerce=int,
            choices=(
                (1, _(u'inforequests:obligee_action:IsDecisionStep:yes')),
                (0, _(u'inforequests:obligee_action:IsDecisionStep:no')),
                ),
            widget=forms.RadioSelect(),
            )

    @classmethod
    def applicable(cls, wizard):
        result = wizard.values.get(u'result', None)
        branch = wizard.values.get(u'branch', None)
        is_on_topic = wizard.values.get(u'is_on_topic', True)
        return not result and branch and branch.can_add_refusal and is_on_topic

    def values(self):
        res = super(IsDecisionStep, self).values()
        if self.cleaned_data[u'is_decision']:
            res[u'result'] = u'action'
            res[u'result_action'] = Action.TYPES.REFUSAL
        return res

class RefusalReasonsStep(ObligeeActionStep):
    text_template = u'inforequests/obligee_action/texts/refusal_reasons.html'

    no_reason = forms.BooleanField(
            label=_(u'inforequests:obligee_action:RefusalReasonsStep:none'),
            required=False,
            widget=forms.CheckboxInput(attrs={
                u'class': u'toggle-changed',
                u'data-container': u'form',
                u'data-action': u'disable',
                u'data-target-false': u'.disabled-if-no-reasons',
                })
            )
    refusal_reason = MultiSelectFormField(
            label=u' ',
            required=False,
            choices=Action.REFUSAL_REASONS._choices,
            widget=forms.CheckboxSelectMultiple(attrs={
                u'class': u'disabled-if-no-reasons',
                }),
            )

    @classmethod
    def applicable(cls, wizard):
        result = wizard.values.get(u'result', None)
        action = wizard.values.get(u'result_action', None)
        return result == u'action' and action == Action.TYPES.REFUSAL

    def clean(self):
        cleaned_data = super(RefusalReasonsStep, self).clean()

        no_reason = cleaned_data.get(u'no_reason', None)
        refusal_reason = cleaned_data.get(u'refusal_reason', None)
        if not no_reason and not refusal_reason:
            msg = self.fields[u'refusal_reason'].error_messages[u'required']
            self.add_error(u'refusal_reason', msg)

        return cleaned_data

    def values(self):
        res = super(RefusalReasonsStep, self).values()
        if self.cleaned_data[u'no_reason']:
            res[u'result_refusal_reason'] = []
        else:
            res[u'result_refusal_reason'] = self.cleaned_data[u'refusal_reason']
        return res

class IsAdvancementStep(ObligeeActionStep):
    text_template = u'inforequests/obligee_action/texts/is_advancement.html'

    is_advancement = forms.TypedChoiceField(
            label=u' ',
            coerce=int,
            choices=(
                (1, _(u'inforequests:obligee_action:IsAdvancementStep:yes')),
                (0, _(u'inforequests:obligee_action:IsAdvancementStep:no')),
                ),
            widget=forms.RadioSelect(attrs={
                u'class': u'toggle-changed',
                u'data-container': u'form',
                u'data-target-1': u'.control-group:has(.visible-if-advancement)',
                }),
            )
    advanced_to_1 = ObligeeAutocompleteField(
            label=_(u'inforequests:obligee_action:IsAdvancementStep:advanced_to_1:label'),
            required=False,
            widget=ObligeeWithAddressInput(attrs={
                u'placeholder': _(u'inforequests:obligee_action:IsAdvancementStep:advanced_to_1:placeholder'),
                u'class': u'span5 visible-if-advancement',
                }),
            )
    advanced_to_2 = ObligeeAutocompleteField(
            label=_(u'inforequests:obligee_action:IsAdvancementStep:advanced_to_2:label'),
            required=False,
            widget=ObligeeWithAddressInput(attrs={
                u'placeholder': _(u'inforequests:obligee_action:IsAdvancementStep:advanced_to_2:placeholder'),
                u'class': u'span5 visible-if-advancement',
                }),
            )
    advanced_to_3 = ObligeeAutocompleteField(
            label=_(u'inforequests:obligee_action:IsAdvancementStep:advanced_to_3:label'),
            required=False,
            widget=ObligeeWithAddressInput(attrs={
                u'placeholder': _(u'inforequests:obligee_action:IsAdvancementStep:advanced_to_3:placeholder'),
                u'class': u'span5 visible-if-advancement',
                }),
            )
    ADVANCED_TO_FIELDS = [u'advanced_to_1', u'advanced_to_2', u'advanced_to_3']

    @classmethod
    def applicable(cls, wizard):
        result = wizard.values.get(u'result', None)
        branch = wizard.values.get(u'branch', None)
        is_on_topic = wizard.values.get(u'is_on_topic', True)
        return not result and branch and branch.can_add_advancement and is_on_topic

    def clean(self):
        cleaned_data = super(IsAdvancementStep, self).clean()

        is_advancement = cleaned_data.get(u'is_advancement', None)
        if is_advancement and not any(cleaned_data.get(f) for f in self.ADVANCED_TO_FIELDS):
            msg = self.fields[u'advanced_to_1'].error_messages[u'required']
            self.add_error(u'advanced_to_1', msg)

        branch = self.wizard.values[u'branch']
        for i, field in enumerate(self.ADVANCED_TO_FIELDS):
            advanced_to = cleaned_data.get(field, None)
            try:
                if advanced_to and advanced_to == branch.obligee:
                    raise ValidationError(_(u'inforequests:obligee_action:IsAdvancementStep:same_obligee_error'))
                for field_2 in self.ADVANCED_TO_FIELDS[0:i]:
                    advanced_to_2 = cleaned_data.get(field_2, None)
                    if advanced_to_2 and advanced_to_2 == advanced_to:
                        raise ValidationError(_(u'inforequests:obligee_action:IsAdvancementStep:duplicate_obligee_error'))
            except ValidationError as e:
                self.add_error(field, e)

        return cleaned_data

    def values(self):
        res = super(IsAdvancementStep, self).values()
        if self.cleaned_data[u'is_advancement']:
            res[u'result'] = u'action'
            res[u'result_action'] = Action.TYPES.ADVANCEMENT
            res[u'result_advanced_to'] = [self.cleaned_data[f] for f in self.ADVANCED_TO_FIELDS]
        return res

class NotCategorizedStep(ObligeeActionStep):
    text_template = u'inforequests/obligee_action/texts/not_categorized.html'

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
            (u'is_on_topic', IsOnTopicStep),
            (u'contains_info', ContainsInfoStep),
            (u'is_decision', IsDecisionStep),
            (u'refusal_reasons', RefusalReasonsStep),
            (u'is_advancement', IsAdvancementStep),
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

        for obligee in self.values.get(u'result_advanced_to', []):
            if obligee:
                sub_branch = Branch(
                        obligee=obligee,
                        inforequest=action.branch.inforequest,
                        advanced_by=action,
                        )
                sub_branch.save()

                sub_action = Action(
                        branch=sub_branch,
                        effective_date=action.effective_date,
                        type=Action.TYPES.ADVANCED_REQUEST,
                        )
                sub_action.save()

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
