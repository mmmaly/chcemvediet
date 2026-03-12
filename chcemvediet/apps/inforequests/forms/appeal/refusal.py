# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property

from poleno.utils.forms import EditableSpan
from chcemvediet.apps.wizards.forms import PaperCharField, OptionalSectionCheckboxField
from chcemvediet.apps.inforequests.models import Action

from .common import AppealStep, AppealSectionStep, AppealDeadendStep, AppealLegalDateStep


class RefusalStep(AppealStep):

    @cached_property
    def number_of_reasons(self):
        return len(self.wizard.last_action.refusal_reason)

class ReasonStep(RefusalStep):
    covered_reason = None

    @cached_property
    def reason_number_in_wizard(self):
        return len(set(step.covered_reason
                for step in self.wizard.steps[:self.index+1]
                if isinstance(step, ReasonStep)
                ))

    @cached_property
    def reason_number_on_paper(self):
        return len(set(step.covered_reason
                for step in self.wizard.steps[:self.index+1]
                if isinstance(step, ReasonStep) and isinstance(step, AppealSectionStep)
                    and not step.section_is_empty()
                ))

class ReasonDispatcher(ReasonStep):
    with_reason_step_class = None
    without_reason_step_class = None

    def pre_transition(self):
        res = super(ReasonDispatcher, self).pre_transition()

        if self.covered_reason in self.wizard.last_action.refusal_reason:
            res.next = self.with_reason_step_class
        else:
            res.next = self.without_reason_step_class

        return res


class SanitizationStep(RefusalStep):
    all_sanitizable_reasons = set([
            Action.REFUSAL_REASONS.BUSINESS_SECRET,
            Action.REFUSAL_REASONS.PERSONAL,
            Action.REFUSAL_REASONS.CONFIDENTIAL,
            ])

    @cached_property
    def actual_sanitizable_reasons(self):
        return self.all_sanitizable_reasons & set(self.wizard.last_action.refusal_reason)

    def reasons_with_empty_sections(self):
        res = []
        for reason in self.actual_sanitizable_reasons:
            for step in self.wizard.steps:
                if isinstance(step, ReasonStep) and step.covered_reason == reason:
                    if isinstance(step, AppealSectionStep) and not step.section_is_empty():
                        break
            else:
                res.append(reason)
        return res

class SanitizationEnd(SanitizationStep):
    pre_step_class = AppealLegalDateStep

class SanitizationProperlySanitized(AppealDeadendStep, SanitizationStep):
    label = _(u'inforequests:appeal:refusal:SanitizationProperlySanitized:label')
    text_template = u'inforequests/appeal/texts/refusal/sanitization_properly_sanitized.html'

class SanitizationMissingDocument(AppealSectionStep, SanitizationStep):
    label = _(u'inforequests:appeal:refusal:SanitizationMissingDocument:label')
    text_template = u'inforequests/appeal/texts/refusal/sanitization_missing_document.html'
    section_template = u'inforequests/appeal/papers/refusal/sanitization_missing_document.html'
    global_fields = [u'sanitization_missing_document']
    post_step_class = SanitizationEnd

    def add_fields(self):
        super(SanitizationMissingDocument, self).add_fields()
        self.fields[u'sanitization_missing_document'] = PaperCharField(widget=EditableSpan())

class SanitizationOverlySanitized(AppealSectionStep, SanitizationStep):
    label = _(u'inforequests:appeal:refusal:SanitizationOverlySanitized:label')
    text_template = u'inforequests/appeal/texts/refusal/sanitization_overly_sanitized.html'
    section_template = u'inforequests/appeal/papers/refusal/sanitization_overly_sanitized.html'
    global_fields = [u'sanitization_overly_sanitized']
    post_step_class = SanitizationEnd

    def add_fields(self):
        super(SanitizationOverlySanitized, self).add_fields()
        self.fields[u'sanitization_overly_sanitized'] = PaperCharField(widget=EditableSpan())

class SanitizationLevel(SanitizationStep):
    label = _(u'inforequests:appeal:refusal:SanitizationLevel:label')
    text_template = u'inforequests/appeal/texts/refusal/sanitization_level.html'
    form_template = u'main/forms/form_horizontal.html'

    def add_fields(self):
        super(SanitizationLevel, self).add_fields()
        self.fields[u'sanitization_level'] = forms.ChoiceField(
                label=u' ',
                choices=(
                    (u'overly-sanitized',
                        _(u'inforequests:appeal:refusal:SanitizationLevel:OverlySanitized')),
                    (u'missing-document',
                        _(u'inforequests:appeal:refusal:SanitizationLevel:MissingDocument')),
                    (u'properly-sanitized',
                        _(u'inforequests:appeal:refusal:SanitizationLevel:ProperlySanitized')),
                    ),
                widget=forms.RadioSelect(),
                )

    def post_transition(self):
        res = super(SanitizationLevel, self).post_transition()

        if not self.is_valid():
            res.next = SanitizationEnd
        elif self.cleaned_data[u'sanitization_level'] == u'overly-sanitized':
            res.next = SanitizationOverlySanitized
        elif self.cleaned_data[u'sanitization_level'] == u'missing-document':
            res.next = SanitizationMissingDocument
        elif self.reasons_with_empty_sections():
            res.next = SanitizationProperlySanitized
        else:
            res.next = SanitizationEnd

        return res

class Sanitization(SanitizationStep):

    def pre_transition(self):
        res = super(Sanitization, self).pre_transition()

        if self.actual_sanitizable_reasons:
            res.next = SanitizationLevel
        else:
            res.next = SanitizationEnd

        return res


class OtherReasonEnd(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.OTHER_REASON
    pre_step_class = Sanitization

class OtherReasonInvalidReason(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.OTHER_REASON
    label = _(u'inforequests:appeal:refusal:OtherReasonInvalidReason:label')
    text_template = u'inforequests/appeal/texts/refusal/other_reason_invalid_reason.html'
    section_template = u'inforequests/appeal/papers/refusal/other_reason_invalid_reason.html'
    global_fields = [u'other_reason_invalid_reason']
    post_step_class = OtherReasonEnd

    def add_fields(self):
        super(OtherReasonInvalidReason, self).add_fields()
        self.fields[u'other_reason_invalid_reason'] = PaperCharField(widget=EditableSpan())

class OtherReasonValidReason(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.OTHER_REASON
    label = _(u'inforequests:appeal:refusal:OtherReasonValidReason:label')
    text_template = u'inforequests/appeal/texts/refusal/other_reason_valid_reason.html'
    section_template = u'inforequests/appeal/papers/refusal/other_reason_valid_reason.html'
    global_fields = [u'other_reason_valid_reason']
    post_step_class = OtherReasonEnd

    def add_fields(self):
        super(OtherReasonValidReason, self).add_fields()
        self.fields[u'other_reason_valid_reason'] = PaperCharField(widget=EditableSpan())

class OtherReasonValid(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.OTHER_REASON
    label = _(u'inforequests:appeal:refusal:OtherReasonValid:label')
    text_template = u'inforequests/appeal/texts/refusal/other_reason_valid.html'
    form_template = u'main/forms/form_horizontal.html'

    def add_fields(self):
        super(OtherReasonValid, self).add_fields()
        self.fields[u'other_reason_valid'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (1, _(u'inforequests:appeal:refusal:OtherReasonValid:yes')),
                    (0, _(u'inforequests:appeal:refusal:OtherReasonValid:no')),
                    ),
                widget=forms.RadioSelect(),
                )

    def post_transition(self):
        res = super(OtherReasonValid, self).post_transition()

        if not self.is_valid():
            res.next = OtherReasonValidReason
        elif self.cleaned_data[u'other_reason_valid']:
            res.next = OtherReasonValidReason
        else:
            res.next = OtherReasonInvalidReason

        return res

class OtherReason(ReasonDispatcher):
    covered_reason = Action.REFUSAL_REASONS.OTHER_REASON
    with_reason_step_class = OtherReasonValid
    without_reason_step_class = OtherReasonEnd


class ConfidentialEnd(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.CONFIDENTIAL
    pre_step_class = OtherReason

class ConfidentialFallbackReason(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.CONFIDENTIAL
    label = _(u'inforequests:appeal:refusal:ConfidentialFallbackReason:label')
    text_template = u'inforequests/appeal/texts/refusal/confidential_fallback_reason.html'
    section_template = u'inforequests/appeal/papers/refusal/confidential_fallback_reason.html'
    global_fields = [u'confidential_fallback', u'confidential_fallback_reason']
    post_step_class = ConfidentialEnd

    def add_fields(self):
        super(ConfidentialFallbackReason, self).add_fields()
        self.fields[u'confidential_fallback'] = OptionalSectionCheckboxField(
                label=_(u'inforequests:appeal:refusal:ConfidentialFallbackReason:confidential_fallback:label'),
                required=False,
                )
        self.fields[u'confidential_fallback_reason'] = PaperCharField(
                required=False,
                widget=EditableSpan(),
                )

    def section_is_empty(self):
        return not self.wizard.values.get(u'confidential_fallback', True)

    def clean(self):
        cleaned_data = super(ConfidentialFallbackReason, self).clean()

        fallback = cleaned_data.get(u'confidential_fallback', None)
        fallback_reason = cleaned_data.get(u'confidential_fallback_reason', None)
        if fallback and not fallback_reason:
            msg = self.fields[u'confidential_fallback_reason'].error_messages[u'required']
            if u'confidential_fallback_reason' in cleaned_data:
                self.add_error(u'confidential_fallback_reason', msg)

        return cleaned_data

class ConfidentialNotConfidentialReason(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.CONFIDENTIAL
    label = _(u'inforequests:appeal:refusal:ConfidentialNotConfidentialReason:label')
    text_template = u'inforequests/appeal/texts/refusal/confidential_not_confidential_reason.html'
    section_template = u'inforequests/appeal/papers/refusal/confidential_not_confidential_reason.html'
    global_fields = [u'confidential_not_confidential_reason']
    post_step_class = ConfidentialEnd

    def add_fields(self):
        super(ConfidentialNotConfidentialReason, self).add_fields()
        self.fields[u'confidential_not_confidential_reason'] = PaperCharField(
                required=False, widget=EditableSpan())

class ConfidentialNotConfidential(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.CONFIDENTIAL
    label = _(u'inforequests:appeal:refusal:ConfidentialNotConfidential:label')
    text_template = u'inforequests/appeal/texts/refusal/confidential_not_confidential.html'
    form_template = u'main/forms/form_horizontal.html'

    def add_fields(self):
        super(ConfidentialNotConfidential, self).add_fields()
        self.fields[u'confidential_not_confidential'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (1, _(u'inforequests:appeal:refusal:ConfidentialNotConfidential:yes')),
                    (0, _(u'inforequests:appeal:refusal:ConfidentialNotConfidential:no')),
                    ),
                widget=forms.RadioSelect(),
                )

    def post_transition(self):
        res = super(ConfidentialNotConfidential, self).post_transition()

        if not self.is_valid():
            res.next = ConfidentialNotConfidentialReason
        elif self.cleaned_data[u'confidential_not_confidential']:
            res.next = ConfidentialNotConfidentialReason
        else:
            res.next = ConfidentialFallbackReason

        return res

class Confidential(ReasonDispatcher):
    covered_reason = Action.REFUSAL_REASONS.CONFIDENTIAL
    with_reason_step_class = ConfidentialNotConfidential
    without_reason_step_class = ConfidentialEnd


class PersonalEnd(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.PERSONAL
    pre_step_class = Confidential

class PersonalFallbackReason(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.PERSONAL
    label = _(u'inforequests:appeal:refusal:PersonalFallbackReason:label')
    text_template = u'inforequests/appeal/texts/refusal/personal_fallback_reason.html'
    section_template = u'inforequests/appeal/papers/refusal/personal_fallback_reason.html'
    global_fields = [u'personal_fallback', u'personal_fallback_reason']
    post_step_class = PersonalEnd

    def add_fields(self):
        super(PersonalFallbackReason, self).add_fields()
        self.fields[u'personal_fallback'] = OptionalSectionCheckboxField(
                label=_(u'inforequests:appeal:refusal:PersonalFallbackReason:personal_fallback:label'),
                required=False,
                )
        self.fields[u'personal_fallback_reason'] = PaperCharField(
                required=False,
                widget=EditableSpan(),
                )

    def section_is_empty(self):
        return not self.wizard.values.get(u'personal_fallback', True)

    def clean(self):
        cleaned_data = super(PersonalFallbackReason, self).clean()

        fallback = cleaned_data.get(u'personal_fallback', None)
        fallback_reason = cleaned_data.get(u'personal_fallback_reason', None)
        if fallback and not fallback_reason:
            msg = self.fields[u'personal_fallback_reason'].error_messages[u'required']
            if u'personal_fallback_reason' in cleaned_data:
                self.add_error(u'personal_fallback_reason', msg)

        return cleaned_data

class PersonalOfficerReason(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.PERSONAL
    label = _(u'inforequests:appeal:refusal:PersonalOfficerReason:label')
    text_template = u'inforequests/appeal/texts/refusal/personal_officer_reason.html'
    section_template = u'inforequests/appeal/papers/refusal/personal_officer_reason.html'
    global_fields = [u'personal_officer_reason']
    post_step_class = PersonalEnd

    def add_fields(self):
        super(PersonalOfficerReason, self).add_fields()
        self.fields[u'personal_officer_reason'] = PaperCharField(
                required=False, widget=EditableSpan())

class PersonalOfficer(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.PERSONAL
    label = _(u'inforequests:appeal:refusal:PersonalOfficer:label')
    text_template = u'inforequests/appeal/texts/refusal/personal_officer.html'
    form_template = u'main/forms/form_horizontal.html'

    def add_fields(self):
        super(PersonalOfficer, self).add_fields()
        self.fields[u'personal_officer'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (1, _(u'inforequests:appeal:refusal:PersonalOfficer:yes')),
                    (0, _(u'inforequests:appeal:refusal:PersonalOfficer:no')),
                    ),
                widget=forms.RadioSelect(),
                )

    def post_transition(self):
        res = super(PersonalOfficer, self).post_transition()

        if not self.is_valid():
            res.next = PersonalOfficerReason
        elif self.cleaned_data[u'personal_officer']:
            res.next = PersonalOfficerReason
        else:
            res.next = PersonalFallbackReason

        return res

class Personal(ReasonDispatcher):
    covered_reason = Action.REFUSAL_REASONS.PERSONAL
    with_reason_step_class = PersonalOfficer
    without_reason_step_class = PersonalEnd


class BusinessSecretEnd(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    pre_step_class = Personal

class BusinessSecretFallbackReason(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    label = _(u'inforequests:appeal:refusal:BusinessSecretFallbackReason:label')
    text_template = u'inforequests/appeal/texts/refusal/business_secret_fallback_reason.html'
    section_template = u'inforequests/appeal/papers/refusal/business_secret_fallback_reason.html'
    global_fields = [u'business_secret_fallback', u'business_secret_fallback_reason']
    post_step_class = BusinessSecretEnd

    def add_fields(self):
        super(BusinessSecretFallbackReason, self).add_fields()
        self.fields[u'business_secret_fallback'] = OptionalSectionCheckboxField(
                label=_(u'inforequests:appeal:refusal:BusinessSecretFallbackReason:business_secret_fallback:label'),
                required=False,
                )
        self.fields[u'business_secret_fallback_reason'] = PaperCharField(
                required=False,
                widget=EditableSpan(),
                )

    def section_is_empty(self):
        return not self.wizard.values.get(u'business_secret_fallback', False)

    def clean(self):
        cleaned_data = super(BusinessSecretFallbackReason, self).clean()

        fallback = cleaned_data.get(u'business_secret_fallback', None)
        fallback_reason = cleaned_data.get(u'business_secret_fallback_reason', None)
        if fallback and not fallback_reason:
            msg = self.fields[u'business_secret_fallback_reason'].error_messages[u'required']
            if u'business_secret_fallback_reason' in cleaned_data:
                self.add_error(u'business_secret_fallback_reason', msg)

        return cleaned_data

class BusinessSecretDefinitionReason(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    label = _(u'inforequests:appeal:refusal:BusinessSecretDefinitionReason:label')
    text_template = u'inforequests/appeal/texts/refusal/business_secret_definition_reason.html'
    section_template = u'inforequests/appeal/papers/refusal/business_secret_definition_reason.html'
    # For ``global_fields`` see ``get_global_fields()``
    post_step_class = BusinessSecretEnd

    def add_fields(self):
        super(BusinessSecretDefinitionReason, self).add_fields()
        for choice in self.wizard.values[u'business_secret_definition']:
            self.fields[u'business_secret_definition_reason_' + choice] = PaperCharField(
                    widget=EditableSpan())

    def get_global_fields(self):
        res = super(BusinessSecretDefinitionReason, self).get_global_fields()
        for choice in self.wizard.values[u'business_secret_definition']:
            res.append(u'business_secret_definition_reason_' + choice)
        return res

class BusinessSecretDefinition(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    label = _(u'inforequests:appeal:refusal:BusinessSecretDefinition:label')
    text_template = u'inforequests/appeal/texts/refusal/business_secret_definition.html'
    form_template = u'main/forms/form_horizontal.html'
    global_fields = [u'business_secret_definition']

    def add_fields(self):
        super(BusinessSecretDefinition, self).add_fields()
        self.fields[u'business_secret_definition'] = forms.MultipleChoiceField(
                label=u' ',
                required=False,
                choices=(
                    (u'comercial',
                        _(u'inforequests:appeal:refusal:BusinessSecretDefinition:comercial')),
                    (u'value',
                        _(u'inforequests:appeal:refusal:BusinessSecretDefinition:value')),
                    (u'common',
                        _(u'inforequests:appeal:refusal:BusinessSecretDefinition:common')),
                    (u'will',
                        _(u'inforequests:appeal:refusal:BusinessSecretDefinition:will')),
                    (u'ensured',
                        _(u'inforequests:appeal:refusal:BusinessSecretDefinition:ensured')),
                    ),
                widget=forms.CheckboxSelectMultiple(),
                )

    def post_transition(self):
        res = super(BusinessSecretDefinition, self).post_transition()

        if not self.is_valid():
            res.next = BusinessSecretDefinitionReason
        elif self.cleaned_data[u'business_secret_definition']:
            res.next = BusinessSecretDefinitionReason
        elif self.wizard.values[u'business_secret_public_funds']:
            res.next = BusinessSecretDefinitionReason
        else:
            res.next = BusinessSecretFallbackReason

        return res

class BusinessSecretPublicFunds(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    label = _(u'inforequests:appeal:refusal:BusinessSecretPublicFunds:label')
    text_template = u'inforequests/appeal/texts/refusal/business_secret_public_funds.html'
    form_template = u'main/forms/form_horizontal.html'
    global_fields = [u'business_secret_public_funds']
    post_step_class = BusinessSecretDefinition

    def add_fields(self):
        super(BusinessSecretPublicFunds, self).add_fields()
        self.fields[u'business_secret_public_funds'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (1, _(u'inforequests:appeal:refusal:BusinessSecretPublicFunds:yes')),
                    (0, _(u'inforequests:appeal:refusal:BusinessSecretPublicFunds:no')),
                    ),
                widget=forms.RadioSelect(),
                )

class BusinessSecret(ReasonDispatcher):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    with_reason_step_class = BusinessSecretPublicFunds
    without_reason_step_class = BusinessSecretEnd


class CopyrightEnd(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.COPYRIGHT
    pre_step_class = BusinessSecret

class CopyrightReason(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.COPYRIGHT
    label = _(u'inforequests:appeal:refusal:CopyrightReason:label')
    text_template = u'inforequests/appeal/texts/refusal/copyright_reason.html'
    section_template = u'inforequests/appeal/papers/refusal/copyright_reason.html'
    global_fields = [u'copyright_reason']
    post_step_class = CopyrightEnd

    def add_fields(self):
        super(CopyrightReason, self).add_fields()
        self.fields[u'copyright_reason'] = PaperCharField(widget=EditableSpan())

class Copyright(ReasonDispatcher):
    covered_reason = Action.REFUSAL_REASONS.COPYRIGHT
    with_reason_step_class = CopyrightReason
    without_reason_step_class = CopyrightEnd


class DoesNotCreateEnd(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_CREATE
    pre_step_class = Copyright

class DoesNotCreateReason(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_CREATE
    label = _(u'inforequests:appeal:refusal:DoesNotCreateReason:label')
    text_template = u'inforequests/appeal/texts/refusal/does_not_create_reason.html'
    section_template = u'inforequests/appeal/papers/refusal/does_not_create_reason.html'
    global_fields = [u'does_not_create_reason']
    post_step_class = DoesNotCreateEnd

    def add_fields(self):
        super(DoesNotCreateReason, self).add_fields()
        self.fields[u'does_not_create_reason'] = PaperCharField(widget=EditableSpan())

class DoesNotCreate(ReasonDispatcher):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_CREATE
    with_reason_step_class = DoesNotCreateReason
    without_reason_step_class = DoesNotCreateEnd


class DoesNotProvideEnd(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_PROVIDE
    pre_step_class = DoesNotCreate

class DoesNotProvideFallbackReason(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_PROVIDE
    label = _(u'inforequests:appeal:refusal:DoesNotProvideFallbackReason:label')
    text_template = u'inforequests/appeal/texts/refusal/does_not_provide_fallback_reason.html'
    section_template = u'inforequests/appeal/papers/refusal/does_not_provide_fallback_reason.html'
    global_fields = [u'does_not_provide_fallback_reason']
    post_step_class = DoesNotProvideEnd

    def add_fields(self):
        super(DoesNotProvideFallbackReason, self).add_fields()
        self.fields[u'does_not_provide_fallback'] = OptionalSectionCheckboxField(
                label=_(u'inforequests:appeal:refusal:DoesNotProvideFallbackReason:does_not_provide_fallback:label'),
                )
        self.fields[u'does_not_provide_fallback_reason'] = PaperCharField(
                widget=EditableSpan(),
                )

class DoesNotProvidePublicFundsReason(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_PROVIDE
    label = _(u'inforequests:appeal:refusal:DoesNotProvidePublicFundsReason:label')
    text_template = u'inforequests/appeal/texts/refusal/does_not_provide_public_funds_reason.html'
    section_template = u'inforequests/appeal/papers/refusal/does_not_provide_public_funds_reason.html'
    global_fields = [u'does_not_provide_public_funds_reason']
    post_step_class = DoesNotProvideEnd

    def add_fields(self):
        super(DoesNotProvidePublicFundsReason, self).add_fields()
        self.fields[u'does_not_provide_public_funds_reason'] = PaperCharField(widget=EditableSpan())

class DoesNotProvidePublicFunds(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_PROVIDE
    label = _(u'inforequests:appeal:refusal:DoesNotProvidePublicFunds:label')
    text_template = u'inforequests/appeal/texts/refusal/does_not_provide_public_funds.html'
    form_template = u'main/forms/form_horizontal.html'

    def add_fields(self):
        super(DoesNotProvidePublicFunds, self).add_fields()
        self.fields[u'does_not_provide_public_funds'] = forms.TypedChoiceField(
                label=u' ',
                coerce=int,
                choices=(
                    (1, _(u'inforequests:appeal:refusal:DoesNotProvidePublicFunds:yes')),
                    (0, _(u'inforequests:appeal:refusal:DoesNotProvidePublicFunds:no')),
                    ),
                widget=forms.RadioSelect(),
                )

    def post_transition(self):
        res = super(DoesNotProvidePublicFunds, self).post_transition()

        if not self.is_valid():
            res.next = DoesNotProvidePublicFundsReason
        elif self.cleaned_data[u'does_not_provide_public_funds']:
            res.next = DoesNotProvidePublicFundsReason
        else:
            res.next = DoesNotProvideFallbackReason

        return res

class DoesNotProvide(ReasonDispatcher):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_PROVIDE
    with_reason_step_class = DoesNotProvidePublicFunds
    without_reason_step_class = DoesNotProvideEnd


class DoesNotHaveEnd(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_HAVE
    pre_step_class = DoesNotProvide

class DoesNotHaveReason(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_HAVE
    label = _(u'inforequests:appeal:refusal:DoesNotHaveReason:label')
    text_template = u'inforequests/appeal/texts/refusal/does_not_have_reason.html'
    section_template = u'inforequests/appeal/papers/refusal/does_not_have_reason.html'
    global_fields = [u'does_not_have_reason']
    post_step_class = DoesNotHaveEnd

    def add_fields(self):
        super(DoesNotHaveReason, self).add_fields()
        self.fields[u'does_not_have_reason'] = PaperCharField(widget=EditableSpan())

class DoesNotHave(ReasonDispatcher):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_HAVE
    with_reason_step_class = DoesNotHaveReason
    without_reason_step_class = DoesNotHaveEnd


class RefusalAppeal(AppealSectionStep, RefusalStep):
    u"""
    Appeal wizard for branches that end with a refusal action with a reason. The wizard supports
    only reasons covered by its reason steps. If the last action contains any other reason, the
    wizard does not apply.
    """
    label = _(u'inforequests:appeal:refusal:RefusalAppeal:label')
    text_template = u'inforequests/appeal/texts/refusal.html'
    section_template = u'inforequests/appeal/papers/refusal.html'
    post_step_class = DoesNotHave

    @classmethod
    def covered_reasons(cls):
        res = set()
        step_class = cls.post_step_class
        while issubclass(step_class, ReasonDispatcher):
            res.add(step_class.covered_reason)
            step_class = step_class.without_reason_step_class.pre_step_class
        return res
