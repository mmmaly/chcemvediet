# vim: expandtab
# -*- coding: utf-8 -*-

from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.sessions.models import Session

from poleno.attachments.forms import AttachmentsField
from poleno.utils.models import after_saved
from poleno.utils.urls import reverse
from poleno.utils.mail import render_mail
from poleno.utils.date import local_date, local_today
from poleno.utils.template import render_to_string
from chcemvediet.apps.wizards.wizard import Bottom, Step, Wizard
from chcemvediet.apps.obligees.models import Obligee
from chcemvediet.apps.obligees.forms import MultipleObligeeWidget, MultipleObligeeField
from chcemvediet.apps.inforequests.models import Action, InforequestEmail
from chcemvediet.apps.inforequests.forms import BranchField, RefusalReasonField


def set_clarification_request(res):
    res.globals[u'result'] = u'action'
    res.globals[u'action'] = Action.TYPES.CLARIFICATION_REQUEST
    res.next = Categorized


def set_confirmation(res):
    res.globals[u'result'] = u'action'
    res.globals[u'action'] = Action.TYPES.CONFIRMATION
    res.next = Categorized


class ObligeeActionStep(Step):
    template = u'inforequests/obligee_action/wizard.html'
    form_template = u'main/forms/form_horizontal.html'

# Epilogue


class Categorized(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:Categorized:label')
    text_template = u'inforequests/obligee_action/texts/categorized.html'
    global_fields = [u'legal_date', u'file_number', u'last_action_dd']
    post_step_class = Bottom

    def add_fields(self):
        super(Categorized, self).add_fields()

        self.fields[u'legal_date'] = forms.DateField(
                label=_(u'inforequests:obligee_action:Categorized:legal_date:label'),
                help_text=render_to_string(
                    u'inforequests/obligee_action/texts/categorized_legal_date_help.txt',
                    self.context()),
                localize=True,
                widget=forms.DateInput(attrs={
                    u'placeholder':
                        _('inforequests:obligee_action:Categorized:legal_date:placeholder'),
                    u'class': u'pln-datepicker',
                    }),
                )

        self.fields[u'file_number'] = forms.CharField(
                label=_(u'inforequests:obligee_action:Categorized:file_number:label'),
                max_length=255,
                required=False,
                widget=forms.TextInput(attrs={
                    u'placeholder':
                        _(u'inforequests:obligee_action:Categorized:file_number:placeholder'),
                    }),
                )

        branch = self.wizard.values[u'branch']
        if branch.last_action.delivered_date is None and branch.last_action.type in [
                Action.TYPES.REQUEST,
                Action.TYPES.CLARIFICATION_RESPONSE,
                Action.TYPES.APPEAL,
                Action.TYPES.ADVANCED_REQUEST,
                ]:
            self.fields[u'last_action_dd'] = forms.DateField(
                    label=render_to_string(
                        u'inforequests/obligee_action/texts/categorized_last_action_dd_label.txt',
                        self.context()),
                    help_text=render_to_string(
                        u'inforequests/obligee_action/texts/categorized_last_action_dd_help.txt',
                        self.context()),
                    localize=True,
                    required=False,
                    widget=forms.DateInput(attrs={
                        u'placeholder':
                            _('inforequests:obligee_action:Categorized:last_action_dd:placeholder'),
                        u'class': u'pln-datepicker',
                        }),
                    )

    def clean(self):
        cleaned_data = super(Categorized, self).clean()

        branch = self.wizard.values[u'branch']
        delivered_date = self.wizard.values[u'delivered_date']
        legal_date = cleaned_data.get(u'legal_date', None)
        last_action_dd = cleaned_data.get(u'last_action_dd', None)

        if legal_date is not None:
            try:
                if legal_date > delivered_date:
                    msg = _(u'inforequests:obligee_action:Categorized:legal_date:error:newer_than_delivered_date')
                    raise ValidationError(msg)
                if legal_date < branch.last_action.legal_date:
                    msg = _(u'inforequests:obligee_action:Categorized:legal_date:error:older_than_previous')
                    raise ValidationError(msg)
                if legal_date > local_today():
                    msg = _(u'inforequests:obligee_action:Categorized:legal_date:error:from_future')
                    raise ValidationError(msg)
            except ValidationError as e:
                if u'legal_date' in cleaned_data:
                    self.add_error(u'legal_date', e)

        if last_action_dd is not None:
            try:
                if legal_date and last_action_dd > legal_date:
                    msg = _(u'inforequests:obligee_action:Categorized:last_action_dd:error:newer_than_legal_date')
                    raise ValidationError(msg)
                if last_action_dd < branch.last_action.legal_date:
                    msg = _(u'inforequests:obligee_action:Categorized:last_action_dd:error:older_than_last_action_legal_date')
                    raise ValidationError(msg)
                if last_action_dd > local_today():
                    msg = _(u'inforequests:obligee_action:Categorized:last_action_dd:error:from_future')
                    raise ValidationError(msg)
                pass
            except ValidationError as e:
                if u'last_action_dd' in cleaned_data:
                    self.add_error(u'last_action_dd', e)

        return cleaned_data


class NotCategorized(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:NotCategorized:label')
    text_template = u'inforequests/obligee_action/texts/not_categorized.html'
    global_fields = [u'help_request']
    post_step_class = Bottom

    def add_fields(self):
        super(NotCategorized, self).add_fields()

        self.fields[u'wants_help'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (1, _(u'inforequests:obligee_action:NotCategorized:help')),
                    (0, _(u'inforequests:obligee_action:NotCategorized:unrelated')),
                    ),
                widget=forms.RadioSelect(attrs={
                    u'class': u'pln-toggle-changed',
                    u'data-container': u'form',
                    u'data-hide-target-1': u'.form-group:has(.chv-visible-if-wants-help)',
                    u'data-disable-target-1': u'.chv-visible-if-wants-help',
                    }),
                )

        self.fields[u'help_request'] = forms.CharField(
                label=_(u'inforequests:obligee_action:NotCategorized:help_request:label'),
                required=False,
                widget=forms.Textarea(attrs={
                    u'placeholder':
                        _(u'inforequests:obligee_action:NotCategorized:help_request:placeholder'),
                    u'class': u'pln-autosize chv-visible-if-wants-help',
                    u'cols': u'', u'rows': u'',
                    }),
                )

    def clean(self):
        cleaned_data = super(NotCategorized, self).clean()

        wants_help = cleaned_data.get(u'wants_help', None)
        help_request = cleaned_data.get(u'help_request', None)
        if wants_help and not help_request:
            msg = self.fields[u'help_request'].error_messages[u'required']
            if u'help_request' in cleaned_data:
                self.add_error(u'help_request', msg)

        return cleaned_data

    def post_transition(self):
        res = super(NotCategorized, self).post_transition()

        if self.is_valid() and self.cleaned_data[u'wants_help']:
            res.globals[u'result'] = u'help'
        else:
            res.globals[u'result'] = u'unrelated'

        return res

# Pre Appeal


class DisclosureReasons(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:DisclosureReasons:label')
    text_template = u'inforequests/obligee_action/texts/disclosure_reasons.html'
    global_fields = [u'refusal_reason']

    def add_fields(self):
        super(DisclosureReasons, self).add_fields()
        branch = self.wizard.values[u'branch']
        self.fields[u'refusal_reason'] = RefusalReasonField(
                section_3=(branch.obligee.type == Obligee.TYPES.SECTION_3),
                )

    def post_transition(self):
        res = super(DisclosureReasons, self).post_transition()

        res.globals[u'result'] = u'action'
        res.globals[u'action'] = Action.TYPES.DISCLOSURE
        res.next = Categorized

        return res


class DisclosureLevelFork(ObligeeActionStep):

    def pre_transition(self):
        res = super(DisclosureLevelFork, self).pre_transition()
        disclosure_level = self.wizard.values.get(u'disclosure_level', None)

        if disclosure_level == Action.DISCLOSURE_LEVELS.FULL:
            res.globals[u'result'] = u'action'
            res.globals[u'action'] = Action.TYPES.DISCLOSURE
            res.next = Categorized
        else:
            res.next = DisclosureReasons

        return res


class CanAddDisclosure(ObligeeActionStep):

    def pre_transition(self):
        res = super(CanAddDisclosure, self).pre_transition()
        branch = self.wizard.values.get(u'branch', None)

        if not branch:
            res.next = NotCategorized
        elif branch.can_add_disclosure:
            res.next = DisclosureLevelFork
        else:
            res.next = NotCategorized

        return res


class CanAddExtension(ObligeeActionStep):

    def pre_transition(self):
        res = super(CanAddExtension, self).pre_transition()
        branch = self.wizard.values.get(u'branch', None)

        if not branch:
            res.next = NotCategorized
        elif branch.can_add_extension:
            res.globals[u'result'] = u'action'
            res.globals[u'action'] = Action.TYPES.EXTENSION
            res.next = Categorized
        else:
            res.next = NotCategorized

        return res


class IsItExtension(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:IsItExtension:label')
    text_template = u'inforequests/obligee_action/texts/is_extension.html'
    global_fields = [u'is_extension', u'extension']

    def add_fields(self):
        super(IsItExtension, self).add_fields()

        self.fields[u'is_extension'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (1, _(u'inforequests:obligee_action:IsItExtension:yes')),
                    (0, _(u'inforequests:obligee_action:IsItExtension:no')),
                    ),
                initial=1 if self.wizard.values.get(u'is_extension') else None,
                widget=forms.RadioSelect(attrs={
                    u'class': u'pln-toggle-changed',
                    u'data-container': u'form',
                    u'data-hide-target-1': u'.form-group:has(.chv-visible-if-extension)',
                    u'data-disable-target-1': u'.chv-visible-if-extension',
                    }),
                )

        self.fields[u'extension'] = forms.IntegerField(
                label=_(u'inforequests:obligee_action:IsItExtension:extension:label'),
                help_text=_(u'inforequests:obligee_action:IsItExtension:extension:help_text'),
                initial=8,
                min_value=2,
                max_value=15,
                required=False,
                widget=forms.NumberInput(attrs={
                    u'placeholder':
                        _(u'inforequests:obligee_action:IsItExtension:extension:placeholder'),
                    u'class': u'chv-visible-if-extension',
                    }),
                )

    def clean(self):
        cleaned_data = super(IsItExtension, self).clean()

        is_extension = cleaned_data.get(u'is_extension', None)
        extension = cleaned_data.get(u'extension', None)
        if is_extension and not extension:
            msg = self.fields[u'extension'].error_messages[u'required']
            if u'extension' in cleaned_data:
                self.add_error(u'extension', msg)

        return cleaned_data

    def post_transition(self):
        res = super(IsItExtension, self).post_transition()

        if not self.is_valid():
            res.next = CanAddDisclosure
        elif self.cleaned_data[u'is_extension']:
            res.next = CanAddExtension
        else:
            res.next = CanAddDisclosure

        return res


class CanAddAdvancement(ObligeeActionStep):

    def pre_transition(self):
        res = super(CanAddAdvancement, self).pre_transition()
        branch = self.wizard.values.get(u'branch', None)

        if not branch:
            res.next = NotCategorized
        elif branch.can_add_advancement:
            res.globals[u'result'] = u'action'
            res.globals[u'action'] = Action.TYPES.ADVANCEMENT
            res.next = Categorized
        else:
            res.next = NotCategorized

        return res


class IsItAdvancement(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:IsItAdvancement:label')
    text_template = u'inforequests/obligee_action/texts/is_advancement.html'
    global_fields = [u'is_advancement', u'advanced_to']

    def add_fields(self):
        super(IsItAdvancement, self).add_fields()

        self.fields[u'is_advancement'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (1, _(u'inforequests:obligee_action:IsItAdvancement:yes')),
                    (0, _(u'inforequests:obligee_action:IsItAdvancement:no')),
                    ),
                initial=1 if self.wizard.values.get(u'is_advancement') else None,
                widget=forms.RadioSelect(attrs={
                    u'class': u'pln-toggle-changed',
                    u'data-container': u'form',
                    u'data-hide-target-1': u'.form-group:has(.chv-visible-if-advancement)',
                    u'data-disable-target-1': u'.chv-visible-if-advancement',
                    }),
                )

        self.fields[u'advanced_to'] = MultipleObligeeField(
                label=_(u'inforequests:obligee_action:IsItAdvancement:advanced_to:label'),
                help_text=_(u'inforequests:obligee_action:IsItAdvancement:advanced_to:help_text'),
                required=False,
                email_required=False,
                widget=MultipleObligeeWidget(input_attrs={
                    u'class': u'chv-visible-if-advancement',
                    u'placeholder':
                        _(u'inforequests:obligee_action:IsItAdvancement:advanced_to:placeholder'),
                    }),
                )

    def clean(self):
        cleaned_data = super(IsItAdvancement, self).clean()

        is_advancement = cleaned_data.get(u'is_advancement', None)
        advanced_to = cleaned_data.get(u'advanced_to', None)
        branch = self.wizard.values[u'branch']
        if is_advancement:
            try:
                if not advanced_to:
                    msg = self.fields[u'advanced_to'].error_messages[u'required']
                    raise ValidationError(msg)
                for obligee in advanced_to:
                    if obligee == branch.obligee:
                        msg = _(u'inforequests:obligee_action:IsItAdvancement:error:same_obligee')
                        raise ValidationError(msg)
                if len(advanced_to) != len(set(advanced_to)):
                    msg = _(u'inforequests:obligee_action:IsItAdvancement:error:duplicate_obligee')
                    raise ValidationError(msg)
            except ValidationError as e:
                if u'advanced_to' in cleaned_data:
                    self.add_error(u'advanced_to', e)

        return cleaned_data

    def post_transition(self):
        res = super(IsItAdvancement, self).post_transition()

        if not self.is_valid():
            res.next = IsItExtension
        elif self.cleaned_data[u'is_advancement']:
            res.next = CanAddAdvancement
        else:
            res.next = IsItExtension

        return res


class RefusalReasons(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:RefusalReasons:label')
    text_template = u'inforequests/obligee_action/texts/refusal_reasons.html'
    global_fields = [u'refusal_reason']

    def add_fields(self):
        super(RefusalReasons, self).add_fields()
        branch = self.wizard.values[u'branch']
        self.fields[u'refusal_reason'] = RefusalReasonField(
                section_3=(branch.obligee.type == Obligee.TYPES.SECTION_3),
                )

    def post_transition(self):
        res = super(RefusalReasons, self).post_transition()

        res.globals[u'result'] = u'action'
        res.globals[u'action'] = Action.TYPES.REFUSAL
        res.next = Categorized

        return res


class CanAddRefusal(ObligeeActionStep):

    def pre_transition(self):
        res = super(CanAddRefusal, self).pre_transition()
        branch = self.wizard.values.get(u'branch', None)

        if not branch:
            res.next = NotCategorized
        elif branch.can_add_refusal:
            res.next = RefusalReasons
        else:
            res.next = NotCategorized

        return res


class IsItDecision(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:IsItDecision:label')
    text_template = u'inforequests/obligee_action/texts/is_decision.html'

    def add_fields(self):
        super(IsItDecision, self).add_fields()

        self.fields[u'is_decision'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (1, _(u'inforequests:obligee_action:IsItDecision:yes')),
                    (0, _(u'inforequests:obligee_action:IsItDecision:no')),
                    ),
                widget=forms.RadioSelect(),
                )

    def post_transition(self):
        res = super(IsItDecision, self).post_transition()

        if not self.is_valid():
            res.next = IsItAdvancement
        elif self.cleaned_data[u'is_decision']:
            res.next = CanAddRefusal
        else:
            res.next = IsItAdvancement

        return res


class ContainsInfo(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:ContainsInfo:label')
    text_template = u'inforequests/obligee_action/texts/contains_info.html'
    global_fields = [u'disclosure_level']

    def add_fields(self):
        super(ContainsInfo, self).add_fields()

        self.fields[u'disclosure_level'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (Action.DISCLOSURE_LEVELS.FULL,
                        _(u'inforequests:obligee_action:ContainsInfo:full')),
                    (Action.DISCLOSURE_LEVELS.PARTIAL,
                        _(u'inforequests:obligee_action:ContainsInfo:partial')),
                    (Action.DISCLOSURE_LEVELS.NONE,
                        _(u'inforequests:obligee_action:ContainsInfo:none')),
                    ),
                widget=forms.RadioSelect(),
                )

    def post_transition(self):
        res = super(ContainsInfo, self).post_transition()

        if not self.is_valid():
            res.next = IsItDecision
        elif self.cleaned_data[u'disclosure_level'] == Action.DISCLOSURE_LEVELS.FULL:
            res.next = CanAddDisclosure
        else:
            res.next = IsItDecision

        return res


class IsOnTopic(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:IsOnTopic:label')
    text_template = u'inforequests/obligee_action/texts/is_on_topic.html'

    def add_fields(self):
        super(IsOnTopic, self).add_fields()

        self.fields[u'is_on_topic'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (1, _(u'inforequests:obligee_action:IsOnTopic:yes')),
                    (0, _(u'inforequests:obligee_action:IsOnTopic:no')),
                    ),
                widget=forms.RadioSelect(),
                )

    def post_transition(self):
        res = super(IsOnTopic, self).post_transition()

        if not self.is_valid():
            res.next = ContainsInfo
        elif self.cleaned_data[u'is_on_topic']:
            res.next = ContainsInfo
        else:
            res.next = NotCategorized

        return res


class CanAddDisclosureRefusalAdvancementOrExtension(ObligeeActionStep):

    def pre_transition(self):
        res = super(CanAddDisclosureRefusalAdvancementOrExtension, self).pre_transition()
        branch = self.wizard.values.get(u'branch', None)

        if not branch:
            res.next = IsOnTopic
        elif branch.can_add_disclosure_refusal_advancement_or_extension:
            res.next = IsOnTopic
        else:
            res.next = NotCategorized

        return res

# Post Appeal


class InvalidReversion(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:InvalidReversion:label')
    text_template = u'inforequests/obligee_action/texts/invalid_reversion.html'
    global_fields = [u'help_request']
    post_step_class = Bottom

    def add_fields(self):
        super(InvalidReversion, self).add_fields()

        self.fields[u'help_request'] = forms.CharField(
                label=_(u'inforequests:obligee_action:InvalidReversion:help_request:label'),
                widget=forms.Textarea(attrs={
                    u'placeholder':
                        _(u'inforequests:obligee_action:InvalidReversion:help_request:placeholder'),
                    u'class': u'pln-autosize',
                    u'cols': u'', u'rows': u'',
                    }),
                )

    def post_transition(self):
        res = super(InvalidReversion, self).post_transition()

        res.globals[u'result'] = u'help'

        return res


class ReversionReasons(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:ReversionReasons:label')
    text_template = u'inforequests/obligee_action/texts/reversion_reasons.html'
    global_fields = [u'refusal_reason']

    def add_fields(self):
        super(ReversionReasons, self).add_fields()
        branch = self.wizard.values[u'branch']
        self.fields[u'refusal_reason'] = RefusalReasonField(
                section_3=(branch.obligee.type == Obligee.TYPES.SECTION_3),
                choices=Action.APPEAL_REFUSAL_REASONS._choices,
                )

    def post_transition(self):
        res = super(ReversionReasons, self).post_transition()

        res.globals[u'result'] = u'action'
        res.globals[u'action'] = Action.TYPES.REVERSION
        res.next = Categorized

        return res


class AppealDisclosureLevelFork(ObligeeActionStep):

    def pre_transition(self):
        res = super(AppealDisclosureLevelFork, self).pre_transition()
        disclosure_level = self.wizard.values.get(u'disclosure_level', None)

        if disclosure_level == Action.DISCLOSURE_LEVELS.FULL:
            res.globals[u'result'] = u'action'
            res.globals[u'action'] = Action.TYPES.REVERSION
            res.next = Categorized
        elif disclosure_level == Action.DISCLOSURE_LEVELS.PARTIAL:
            res.next = ReversionReasons
        elif disclosure_level == Action.DISCLOSURE_LEVELS.NONE:
            res.next = InvalidReversion
        else:
            res.next = ReversionReasons

        return res


class CanAddReversion(ObligeeActionStep):

    def pre_transition(self):
        res = super(CanAddReversion, self).pre_transition()
        branch = self.wizard.values.get(u'branch', None)

        if not branch:
            res.next = NotCategorized
        elif branch.can_add_reversion:
            res.next = AppealDisclosureLevelFork
        else:
            res.next = NotCategorized

        return res


class CanAddRemandment(ObligeeActionStep):

    def pre_transition(self):
        res = super(CanAddRemandment, self).pre_transition()
        branch = self.wizard.values.get(u'branch', None)

        if not branch:
            res.next = NotCategorized
        elif branch.can_add_remandment:
            res.globals[u'result'] = u'action'
            res.globals[u'action'] = Action.TYPES.REMANDMENT
            res.next = Categorized
        else:
            res.next = NotCategorized

        return res


class WasItReturned(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:WasItReturned:label')
    text_template = u'inforequests/obligee_action/texts/was_returned.html'

    def add_fields(self):
        super(WasItReturned, self).add_fields()

        self.fields[u'was_returned'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (1, _(u'inforequests:obligee_action:WasItReturned:yes')),
                    (0, _(u'inforequests:obligee_action:WasItReturned:no')),
                    ),
                widget=forms.RadioSelect(),
            )

    def post_transition(self):
        res = super(WasItReturned, self).post_transition()

        if not self.is_valid():
            res.next = CanAddReversion
        elif self.cleaned_data[u'was_returned']:
            res.next = CanAddRemandment
        else:
            res.next = CanAddReversion

        return res


class CanAddAffirmation(ObligeeActionStep):

    def pre_transition(self):
        res = super(CanAddAffirmation, self).pre_transition()
        branch = self.wizard.values.get(u'branch', None)

        if not branch:
            res.next = NotCategorized
        elif branch.can_add_affirmation:
            res.globals[u'result'] = u'action'
            res.globals[u'action'] = Action.TYPES.AFFIRMATION
            res.next = Categorized
        else:
            res.next = NotCategorized

        return res


class WasItAccepted(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:WasItAccepted:label')
    text_template = u'inforequests/obligee_action/texts/was_accepted.html'

    def add_fields(self):
        super(WasItAccepted, self).add_fields()

        self.fields[u'was_accepted'] = forms.ChoiceField(
                label=u' ',
                choices=(
                    (u'all', _(u'inforequests:obligee_action:WasItAccepted:all')),
                    (u'some', _(u'inforequests:obligee_action:WasItAccepted:some')),
                    (u'none', _(u'inforequests:obligee_action:WasItAccepted:none')),
                    ),
                widget=forms.RadioSelect(),
                )

    def post_transition(self):
        res = super(WasItAccepted, self).post_transition()

        if not self.is_valid():
            res.next = WasItReturned
        elif self.cleaned_data[u'was_accepted'] == u'none':
            res.next = CanAddAffirmation
        else:
            res.next = WasItReturned

        return res


class ContainsAppealInfo(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:ContainsAppealInfo:label')
    text_template = u'inforequests/obligee_action/texts/contains_appeal_info.html'
    global_fields = [u'disclosure_level']
    post_step_class = WasItAccepted

    def add_fields(self):
        super(ContainsAppealInfo, self).add_fields()

        self.fields[u'disclosure_level'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (Action.DISCLOSURE_LEVELS.FULL,
                        _(u'inforequests:obligee_action:ContainsAppealInfo:full')),
                    (Action.DISCLOSURE_LEVELS.PARTIAL,
                        _(u'inforequests:obligee_action:ContainsAppealInfo:partial')),
                    (Action.DISCLOSURE_LEVELS.NONE,
                        _(u'inforequests:obligee_action:ContainsAppealInfo:none')),
                    ),
                widget=forms.RadioSelect(),
                )


class IsItAppealDecision(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:IsItAppealDecision:label')
    text_template = u'inforequests/obligee_action/texts/is_appeal_decision.html'

    def add_fields(self):
        super(IsItAppealDecision, self).add_fields()

        self.fields[u'is_decision'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (1, _(u'inforequests:obligee_action:IsItAppealDecision:yes')),
                    (0, _(u'inforequests:obligee_action:IsItAppealDecision:no')),
                    ),
                widget=forms.RadioSelect(),
                )

    def post_transition(self):
        res = super(IsItAppealDecision, self).post_transition()

        if not self.is_valid():
            res.next = ContainsAppealInfo
        elif self.cleaned_data[u'is_decision']:
            res.next = ContainsAppealInfo
        else:
            res.next = CanAddDisclosureRefusalAdvancementOrExtension

        return res


class CanAddRemandmentAffirmationOrReversion(ObligeeActionStep):

    def pre_transition(self):
        res = super(CanAddRemandmentAffirmationOrReversion, self).pre_transition()
        branch = self.wizard.values.get(u'branch', None)

        if self.wizard.email:
            res.next = CanAddDisclosureRefusalAdvancementOrExtension
        elif not branch:
            res.next = CanAddDisclosureRefusalAdvancementOrExtension
        elif branch.can_add_remandment_affirmation_or_reversion:
            res.next = IsItAppealDecision
        else:
            res.next = CanAddDisclosureRefusalAdvancementOrExtension

        return res

# Confirmation and Clarification Request


class IsItConfirmation(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:IsItConfirmation:label')
    text_template = u'inforequests/obligee_action/texts/is_confirmation.html'

    def add_fields(self):
        super(IsItConfirmation, self).add_fields()

        self.fields[u'is_confirmation'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (1, _(u'inforequests:obligee_action:IsItConfirmation:yes')),
                    (0, _(u'inforequests:obligee_action:IsItConfirmation:no')),
                    ),
                widget=forms.RadioSelect(),
                )

    def post_transition(self):
        res = super(IsItConfirmation, self).post_transition()

        if not self.is_valid():
            res.next = CanAddRemandmentAffirmationOrReversion
        elif self.cleaned_data[u'is_confirmation']:
            set_confirmation(res)
        else:
            res.next = CanAddRemandmentAffirmationOrReversion

        return res


class CanAddConfirmation(ObligeeActionStep):

    def pre_transition(self):
        res = super(CanAddConfirmation, self).pre_transition()
        branch = self.wizard.values.get(u'branch', None)

        if not branch:
            res.next = CanAddRemandmentAffirmationOrReversion
        elif branch.can_add_confirmation:
            res.next = IsItConfirmation
        else:
            res.next = CanAddRemandmentAffirmationOrReversion

        return res


class IsItQuestion(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:IsItQuestion:label')
    text_template = u'inforequests/obligee_action/texts/is_question.html'

    def add_fields(self):
        super(IsItQuestion, self).add_fields()

        self.fields[u'is_question'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (1, _(u'inforequests:obligee_action:IsItQuestion:yes')),
                    (0, _(u'inforequests:obligee_action:IsItQuestion:no')),
                    ),
                widget=forms.RadioSelect(),
                )

    def post_transition(self):
        res = super(IsItQuestion, self).post_transition()

        if not self.is_valid():
            res.next = CanAddConfirmation
        elif self.cleaned_data[u'is_question']:
            set_clarification_request(res)
        else:
            res.next = CanAddConfirmation

        return res


class CanAddClarificationRequest(ObligeeActionStep):

    def pre_transition(self):
        res = super(CanAddClarificationRequest, self).pre_transition()
        branch = self.wizard.values.get(u'branch', None)

        if not branch:
            res.next = CanAddConfirmation
        elif branch.can_add_clarification_request:
            res.next = IsItQuestion
        else:
            res.next = CanAddConfirmation

        return res

# Prologue


class DirectClassification(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:DirectClassification:label')
    text_template = u'inforequests/obligee_action/texts/direct_classification.html'

    def add_fields(self):
        super(DirectClassification, self).add_fields()
        branch = self.wizard.values.get(u'branch', None)

        choices = []

        if branch and branch.can_add_clarification_request:
            choices.append(
                (u'question', _(u'inforequests:obligee_action:DirectClassification:question'))
            )

        if branch and branch.can_add_confirmation:
            choices.append(
                (u'confirmation', _(u'inforequests:obligee_action:DirectClassification:confirmation'))
            )

        if branch.can_add_remandment_affirmation_or_reversion:
            choices.append(
                (u'appeal_decision', _(u'inforequests:obligee_action:DirectClassification:appeal_decision'))
            )

        if branch.can_add_advancement:
            choices.append(
                (u'advancement', _(u'inforequests:obligee_action:DirectClassification:advancement'))
            )

        if branch.can_add_extension:
            choices.append(
                (u'extension', _(u'inforequests:obligee_action:DirectClassification:extension'))
            )

        choices.extend([
            (u'contains_info:full', _(u'inforequests:obligee_action:DirectClassification:contains_info:full')),
            (u'contains_info:partial', _(u'inforequests:obligee_action:DirectClassification:contains_info:partial')),
            (u'contains_info:none', _(u'inforequests:obligee_action:DirectClassification:contains_info:none')),
            (u'off_topic', _(u'inforequests:obligee_action:DirectClassification:off_topic')),
        ])

        self.fields[u'type'] = forms.ChoiceField(
            label=u' ',
            choices=choices,
            widget=forms.RadioSelect(),
        )

    def post_transition(self):
        res = super(DirectClassification, self).post_transition()

        if not self.is_valid():
            res.next = CanAddClarificationRequest
        elif self.is_type(u'question'):
            set_clarification_request(res)
        elif self.is_type(u'confirmation'):
            set_confirmation(res)
        elif self.is_type(u'appeal_decision'):
            res.next = ContainsAppealInfo
        elif self.is_type(u'contains_info:full'):
            res.globals[u'disclosure_level'] = Action.DISCLOSURE_LEVELS.FULL
            res.next = CanAddDisclosure
        elif self.is_type(u'contains_info:partial'):
            res.globals[u'disclosure_level'] = Action.DISCLOSURE_LEVELS.PARTIAL
            res.next = IsItDecision
        elif self.is_type(u'contains_info:none'):
            res.globals[u'disclosure_level'] = Action.DISCLOSURE_LEVELS.NONE
            res.next = IsItDecision
        elif self.is_type(u'off_topic'):
            res.next = NotCategorized
        elif self.is_type(u'advancement'):
            res.globals[u'is_advancement'] = 1
            res.next = IsItAdvancement
        elif self.is_type(u'extension'):
            res.globals[u'is_extension'] = 1
            res.next = IsItExtension
        else:
            res.next = CanAddClarificationRequest

        return res

    def is_type(self, value):
        return self.cleaned_data[u'type'] == value


class ShouldUseWizard(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:ShouldUseWizard:label')
    text_template = u'inforequests/obligee_action/texts/wizard.html'

    def add_fields(self):
        super(ShouldUseWizard, self).add_fields()

        self.fields[u'use_wizard'] = forms.TypedChoiceField(
            label=u' ',
            coerce=int,
            choices=(
                (1, _(u'inforequests:obligee_action:ShouldUseWizard:yes')),
                (0, _(u'inforequests:obligee_action:ShouldUseWizard:no'))
            ),
            widget=forms.RadioSelect(),
        )

    def post_transition(self):
        res = super(ShouldUseWizard, self).post_transition()

        if not self.is_valid():
            res.next = CanAddClarificationRequest
        elif not self.cleaned_data[u'use_wizard']:
            res.next = DirectClassification
        else:
            res.next = CanAddClarificationRequest

        return res


class InputBasics(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:InputBasics:label')
    text_template = u'inforequests/obligee_action/texts/basics.html'
    global_fields = [u'delivered_date', u'attachments']
    post_step_class = ShouldUseWizard

    def add_fields(self):
        super(InputBasics, self).add_fields()

        self.fields[u'delivered_date'] = forms.DateField(
                label=_(u'inforequests:obligee_action:InputBasics:delivered_date:label'),
                localize=True,
                widget=forms.DateInput(attrs={
                    u'placeholder':
                        _('inforequests:obligee_action:InputBasics:delivered_date:placeholder'),
                    u'class': u'pln-datepicker',
                    }),
                )

        self.fields[u'attachments'] = AttachmentsField(
                label=_(u'inforequests:obligee_action:InputBasics:attachments:label'),
                help_text=_(u'inforequests:obligee_action:InputBasics:attachments:help_text'),
                upload_url_func=(
                    lambda: reverse(u'inforequests:upload_attachment')),
                download_url_func=(
                    lambda a: reverse(u'inforequests:download_attachment', args=[a.pk])),
                attached_to=(
                    self.wizard.draft,
                    Session.objects.get(session_key=self.wizard.request.session.session_key),
                    ),
                )

    def clean(self):
        cleaned_data = super(InputBasics, self).clean()

        branch = self.wizard.values[u'branch']
        delivered_date = cleaned_data.get(u'delivered_date', None)
        if delivered_date is not None:
            try:
                if delivered_date < branch.last_action.legal_date:
                    msg = _(u'inforequests:obligee_action:InputBasics:delivered_date:error:older_than_previous')
                    raise ValidationError(msg.format(date=branch.last_action.legal_date))
                if delivered_date > local_today():
                    msg = _(u'inforequests:obligee_action:InputBasics:delivered_date:error:from_future')
                    raise ValidationError(msg)
            except ValidationError as e:
                if u'delivered_date' in cleaned_data:
                    self.add_error(u'delivered_date', e)

        return cleaned_data

    def commit(self):
        super(InputBasics, self).commit()

        @after_saved(self.wizard.draft)
        def deferred(draft):
            for attachment in self.cleaned_data.get(u'attachments', []):
                attachment.generic_object = draft
                attachment.save()


class IsByEmail(ObligeeActionStep):

    def pre_transition(self):
        res = super(IsByEmail, self).pre_transition()

        if self.wizard.email:
            res.globals[u'delivered_date'] = local_date(self.wizard.email.processed)
            res.globals[u'attachments'] = None
            res.next = ShouldUseWizard
        else:
            res.next = InputBasics

        return res


class SelectBranch(ObligeeActionStep):
    label = _(u'inforequests:obligee_action:SelectBranch:label')
    text_template = u'inforequests/obligee_action/texts/branch.html'
    global_fields = [u'branch']
    post_step_class = IsByEmail

    def add_fields(self):
        super(SelectBranch, self).add_fields()

        self.fields[u'branch'] = BranchField(
                label=_(u'inforequests:obligee_action:SelectBranch:branch:label'),
                inforequest=self.wizard.inforequest,
                )


class HasSingeBranch(ObligeeActionStep):

    def pre_transition(self):
        res = super(HasSingeBranch, self).pre_transition()

        if len(self.wizard.inforequest.branches) == 1:
            res.globals[u'branch'] = self.wizard.inforequest.branches[0]
            res.next = IsByEmail
        else:
            res.next = SelectBranch

        return res

# Wizard


class ObligeeActionWizard(Wizard):
    first_step_class = HasSingeBranch

    def __init__(self, request, index, inforequest, inforequestemail, email):
        self.inforequest = inforequest
        self.inforequestemail = inforequestemail
        self.email = email
        super(ObligeeActionWizard, self).__init__(request, index)

    def get_instance_id(self):
        return u'{}-{}'.format(self.__class__.__name__, self.inforequest.pk)

    def get_step_url(self, step, anchor=u''):
        return reverse(u'inforequests:obligee_action',
                       kwargs=dict(inforequest=self.inforequest, step=step)) + anchor

    def context(self, extra=None):
        res = super(ObligeeActionWizard, self).context(extra)
        res.update({
                u'inforequest': self.inforequest,
                u'email': self.email,
                })
        return res

    def finish(self):
        result = self.values[u'result']
        if result == u'action':
            return self.finish_action()
        if result == u'help':
            return self.finish_help()
        if result == u'unrelated':
            return self.finish_unrelated()
        raise ValueError

    def finish_action(self):
        assert self.values[u'action'] in Action.OBLIGEE_ACTION_TYPES
        assert not self.email or self.values[u'action'] in Action.OBLIGEE_EMAIL_ACTION_TYPES
        assert self.values[u'branch'].can_add_action(self.values[u'action'])

        last_action_dd = self.values.get(u'last_action_dd', None)
        if last_action_dd and not self.values[u'branch'].last_action.delivered_date:
            self.values[u'branch'].last_action.delivered_date = last_action_dd
            self.values[u'branch'].last_action.save(update_fields=[u'delivered_date'])

        action = Action.create(
                branch=self.values[u'branch'],
                type=self.values[u'action'],
                email=self.email if self.email else None,
                subject=self.email.subject if self.email else u'',
                content=self.email.text if self.email else u'',
                file_number=self.values[u'file_number'],
                delivered_date=self.values[u'delivered_date'],
                legal_date=self.values[u'legal_date'],
                extension=self.values.get(u'extension', None),
                disclosure_level=self.values.get(u'disclosure_level', None),
                refusal_reason=self.values.get(u'refusal_reason', None),
                advanced_to=self.values.get(u'advanced_to', None),
                attachments=self.email.attachments if self.email else self.values[u'attachments'],
                )
        action.save()

        if self.email:
            self.inforequestemail.type = InforequestEmail.TYPES.OBLIGEE_ACTION
            self.inforequestemail.save(update_fields=[u'type'])

        return action.get_absolute_url()

    def finish_help(self):
        msg = render_mail(u'inforequests/mails/obligee_action_help_request',
                          from_email=settings.DEFAULT_FROM_EMAIL,
                          to=[settings.SUPPORT_EMAIL],
                          attachments=[(a.name, a.content, a.content_type)
                                       for a in self.values[u'attachments'] or []],
                          dictionary={
                              u'wizard': self,
                              u'inforequest': self.inforequest,
                              u'email': self.email,
                          },
                          )
        msg.send()

        if self.email:
            self.inforequestemail.type = InforequestEmail.TYPES.UNKNOWN
            self.inforequestemail.save(update_fields=[u'type'])

        return self.inforequest.get_absolute_url()

    def finish_unrelated(self):
        if self.email:
            self.inforequestemail.type = InforequestEmail.TYPES.UNRELATED
            self.inforequestemail.save(update_fields=[u'type'])

        return self.inforequest.get_absolute_url()
