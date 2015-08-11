# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from django import forms
from django.utils.translation import ugettext_lazy as _

from poleno.utils.forms import EditableSpan
from chcemvediet.apps.wizards.forms import PaperCharField, OptionalSectionCheckboxField
from chcemvediet.apps.inforequests.models import Action

from . import AppealStep, AppealSectionStep, AppealDeadendStep, AppealPaperStep, AppealFinalStep
from . import AppealWizard

class ReasonStep(AppealStep):
    covered_reason = None

    @classmethod
    def applicable(cls, wizard):
        return cls.covered_reason in wizard.branch.last_action.refusal_reason

    def context(self, extra=None):
        res = super(ReasonStep, self).context(extra)
        res.update({
                u'reason_number_in_wizard': self.reason_number_in_wizard(),
                u'reason_number_on_paper': self.reason_number_on_paper(),
                })
        return res

    def reason_number_in_wizard(self):
        return len(set(step.covered_reason
                for step in self.wizard.steps.values()[:self.index+1]
                if step and isinstance(step, ReasonStep)
                ))

    def reason_number_on_paper(self):
        return len(set(step.covered_reason
                for step in self.wizard.steps.values()[:self.index+1]
                if step and isinstance(step, ReasonStep) and isinstance(step, AppealSectionStep)
                    and not step.section_is_empty()
                ))


class RefusalAppealDoesNotHaveReasonStep(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_HAVE
    text_template = u'inforequests/appeals/texts/refusal/does_not_have_reason.html'
    section_template = u'inforequests/appeals/papers/refusal/does_not_have_reason.html'

    does_not_have_reason = PaperCharField(widget=EditableSpan())

    def paper_fields(self, step):
        step.fields[u'does_not_have_reason'] = PaperCharField(widget=EditableSpan())


class RefusalAppealDoesNotProvidePublicFundsStep(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_PROVIDE
    text_template = u'inforequests/appeals/texts/refusal/does_not_provide_public_funds.html'

    does_not_provide_public_funds = forms.TypedChoiceField(
            coerce=int,
            choices=(
                (None, u''),
                (1, _(u'inforequests:RefusalAppealDoesNotProvidePublicFundsStep:yes')),
                (0, _(u'inforequests:RefusalAppealDoesNotProvidePublicFundsStep:no')),
                ),
            )

class RefusalAppealDoesNotProvidePublicFundsReasonStep(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_PROVIDE
    text_template = u'inforequests/appeals/texts/refusal/does_not_provide_public_funds_reason.html'
    section_template = u'inforequests/appeals/papers/refusal/does_not_provide_public_funds_reason.html'

    does_not_provide_public_funds_reason = PaperCharField(widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealDoesNotProvidePublicFundsReasonStep, cls).applicable(wizard):
            return False
        return wizard.values.get(u'does_not_provide_public_funds', True)

    def paper_fields(self, step):
        step.fields[u'does_not_provide_public_funds_reason'] = PaperCharField(widget=EditableSpan())

class RefusalAppealDoesNotProvideFallbackReasonStep(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_PROVIDE
    text_template = u'inforequests/appeals/texts/refusal/does_not_provide_fallback_reason.html'
    section_template = u'inforequests/appeals/papers/refusal/does_not_provide_fallback_reason.html'

    does_not_provide_fallback = OptionalSectionCheckboxField()
    does_not_provide_fallback_reason = PaperCharField(widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealDoesNotProvideFallbackReasonStep, cls).applicable(wizard):
            return False
        return not wizard.values.get(u'does_not_provide_public_funds', True)

    def paper_fields(self, step):
        step.fields[u'does_not_provide_fallback_reason'] = PaperCharField(widget=EditableSpan())


class RefusalAppealDoesNotCreateReasonStep(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_CREATE
    text_template = u'inforequests/appeals/texts/refusal/does_not_create_reason.html'
    section_template = u'inforequests/appeals/papers/refusal/does_not_create_reason.html'

    does_not_create_reason = PaperCharField(widget=EditableSpan())

    def paper_fields(self, step):
        step.fields[u'does_not_create_reason'] = PaperCharField(widget=EditableSpan())


class RefusalAppealCopyrightReasonStep(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.COPYRIGHT
    text_template = u'inforequests/appeals/texts/refusal/copyright_reason.html'
    section_template = u'inforequests/appeals/papers/refusal/copyright_reason.html'

    copyright_reason = PaperCharField(widget=EditableSpan())

    def paper_fields(self, step):
        step.fields[u'copyright_reason'] = PaperCharField(widget=EditableSpan())


class RefusalAppealBusinessSecretPublicFundsStep(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    text_template = u'inforequests/appeals/texts/refusal/business_secret_public_funds.html'

    business_secret_public_funds = forms.TypedChoiceField(
            coerce=int,
            choices=(
                (None, u''),
                (1, _(u'inforequests:RefusalAppealBusinessSecretPublicFundsStep:yes')),
                (0, _(u'inforequests:RefusalAppealBusinessSecretPublicFundsStep:no')),
                ),
            )

class RefusalAppealBusinessSecretDefinitionStep(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    text_template = u'inforequests/appeals/texts/refusal/business_secret_definition.html'
    form_template = u'main/snippets/form_horizontal.html'

    business_secret_definition = forms.MultipleChoiceField(
            label=u' ',
            required=False,
            choices=(
                (u'comercial', _(u'inforequests:RefusalAppealBusinessSecretDefinitionStep:comercial')),
                (u'value',     _(u'inforequests:RefusalAppealBusinessSecretDefinitionStep:value')),
                (u'common',    _(u'inforequests:RefusalAppealBusinessSecretDefinitionStep:common')),
                (u'will',      _(u'inforequests:RefusalAppealBusinessSecretDefinitionStep:will')),
                (u'ensured',   _(u'inforequests:RefusalAppealBusinessSecretDefinitionStep:ensured')),
                ),
            widget=forms.CheckboxSelectMultiple(),
            )

class RefusalAppealBusinessSecretDefinitionReasonStep(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    text_template = u'inforequests/appeals/texts/refusal/business_secret_definition_reason.html'
    section_template = u'inforequests/appeals/papers/refusal/business_secret_definition_reason.html'

    def __init__(self, *args, **kwargs):
        super(RefusalAppealBusinessSecretDefinitionReasonStep, self).__init__(*args, **kwargs)
        choices = self.wizard.values.get(u'business_secret_definition', [])
        for choice in choices:
            self.fields[u'business_secret_definition_reason_' + choice] = PaperCharField(widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealBusinessSecretDefinitionReasonStep, cls).applicable(wizard):
            return False
        return wizard.values.get(u'business_secret_public_funds', True) or wizard.values.get(u'business_secret_definition', True)

    def paper_fields(self, step):
        choices = self.wizard.values.get(u'business_secret_definition', [])
        for choice in choices:
            step.fields[u'business_secret_definition_reason_' + choice] = PaperCharField(widget=EditableSpan())

class RefusalAppealBusinessSecretFallbackReasonStep(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    text_template = u'inforequests/appeals/texts/refusal/business_secret_fallback_reason.html'
    section_template = u'inforequests/appeals/papers/refusal/business_secret_fallback_reason.html'

    business_secret_fallback = OptionalSectionCheckboxField(required=False)
    business_secret_fallback_reason = PaperCharField(required=False, widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealBusinessSecretFallbackReasonStep, cls).applicable(wizard):
            return False
        return not wizard.values.get(u'business_secret_public_funds', True) and not wizard.values.get(u'business_secret_definition', True)

    def paper_fields(self, step):
        if self.wizard.values.get(u'business_secret_fallback', True):
            step.fields[u'business_secret_fallback_reason'] = PaperCharField(widget=EditableSpan())

    def section_is_empty(self):
        return not self.wizard.values.get(u'business_secret_fallback', True)

    def clean(self):
        cleaned_data = super(RefusalAppealBusinessSecretFallbackReasonStep, self).clean()
        fallback = cleaned_data.get(u'business_secret_fallback', None)
        fallback_reason = cleaned_data.get(u'business_secret_fallback_reason', None)
        if fallback and not fallback_reason:
            msg = self.fields[u'business_secret_fallback_reason'].error_messages[u'required']
            self.add_error(u'business_secret_fallback_reason', msg)
        return cleaned_data


class RefusalAppealPersonalOfficerStep(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.PERSONAL
    text_template = u'inforequests/appeals/texts/refusal/personal_officer.html'

    personal_officer = forms.TypedChoiceField(
            coerce=int,
            choices=(
                (None, u''),
                (1, _(u'inforequests:RefusalAppealPersonalOfficerStep:yes')),
                (0, _(u'inforequests:RefusalAppealPersonalOfficerStep:no')),
                ),
            )

class RefusalAppealPersonalOfficerReasonStep(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.PERSONAL
    text_template = u'inforequests/appeals/texts/refusal/personal_officer_reason.html'
    section_template = u'inforequests/appeals/papers/refusal/personal_officer_reason.html'

    personal_officer_reason = PaperCharField(required=False, widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealPersonalOfficerReasonStep, cls).applicable(wizard):
            return False
        return wizard.values.get(u'personal_officer', True)

    def paper_fields(self, step):
        step.fields[u'personal_officer_reason'] = PaperCharField(required=False, widget=EditableSpan())

class RefusalAppealPersonalFallbackReasonStep(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.PERSONAL
    text_template = u'inforequests/appeals/texts/refusal/personal_fallback_reason.html'
    section_template = u'inforequests/appeals/papers/refusal/personal_fallback_reason.html'

    personal_fallback = OptionalSectionCheckboxField(required=False)
    personal_fallback_reason = PaperCharField(required=False, widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealPersonalFallbackReasonStep, cls).applicable(wizard):
            return False
        return not wizard.values.get(u'personal_officer', True)

    def paper_fields(self, step):
        if self.wizard.values.get(u'personal_fallback', True):
            step.fields[u'personal_fallback_reason'] = PaperCharField(widget=EditableSpan())

    def section_is_empty(self):
        return not self.wizard.values.get(u'personal_fallback', True)

    def clean(self):
        cleaned_data = super(RefusalAppealPersonalFallbackReasonStep, self).clean()
        fallback = cleaned_data.get(u'personal_fallback', None)
        fallback_reason = cleaned_data.get(u'personal_fallback_reason', None)
        if fallback and not fallback_reason:
            msg = self.fields[u'personal_fallback_reason'].error_messages[u'required']
            self.add_error(u'personal_fallback_reason', msg)
        return cleaned_data


class RefusalAppealConfidentialNotConfidentialStep(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.CONFIDENTIAL
    text_template = u'inforequests/appeals/texts/refusal/confidential_not_confidential.html'

    confidential_not_confidential = forms.TypedChoiceField(
            coerce=int,
            choices=(
                (None, u''),
                (1, _(u'inforequests:RefusalAppealConfidentialNotConfidentialStep:yes')),
                (0, _(u'inforequests:RefusalAppealConfidentialNotConfidentialStep:no')),
                ),
            )

class RefusalAppealConfidentialNotConfidentialReasonStep(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.CONFIDENTIAL
    text_template = u'inforequests/appeals/texts/refusal/confidential_not_confidential_reason.html'
    section_template = u'inforequests/appeals/papers/refusal/confidential_not_confidential_reason.html'

    confidential_not_confidential_reason = PaperCharField(required=False, widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealConfidentialNotConfidentialReasonStep, cls).applicable(wizard):
            return False
        return wizard.values.get(u'confidential_not_confidential', True)

    def paper_fields(self, step):
        step.fields[u'confidential_not_confidential_reason'] = PaperCharField(required=False, widget=EditableSpan())

class RefusalAppealConfidentialFallbackReasonStep(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.CONFIDENTIAL
    text_template = u'inforequests/appeals/texts/refusal/confidential_fallback_reason.html'
    section_template = u'inforequests/appeals/papers/refusal/confidential_fallback_reason.html'

    confidential_fallback = OptionalSectionCheckboxField(required=False)
    confidential_fallback_reason = PaperCharField(required=False, widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealConfidentialFallbackReasonStep, cls).applicable(wizard):
            return False
        return not wizard.values.get(u'confidential_not_confidential', True)

    def paper_fields(self, step):
        if self.wizard.values.get(u'confidential_fallback', True):
            step.fields[u'confidential_fallback_reason'] = PaperCharField(widget=EditableSpan())

    def section_is_empty(self):
        return not self.wizard.values.get(u'confidential_fallback', True)

    def clean(self):
        cleaned_data = super(RefusalAppealConfidentialFallbackReasonStep, self).clean()
        fallback = cleaned_data.get(u'confidential_fallback', None)
        fallback_reason = cleaned_data.get(u'confidential_fallback_reason', None)
        if fallback and not fallback_reason:
            msg = self.fields[u'confidential_fallback_reason'].error_messages[u'required']
            self.add_error(u'confidential_fallback_reason', msg)
        return cleaned_data


class RefusalAppealOtherReasonValidStep(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.OTHER_REASON
    text_template = u'inforequests/appeals/texts/refusal/other_reason_valid.html'

    other_reason_valid = forms.TypedChoiceField(
            coerce=int,
            choices=(
                (None, u''),
                (1, _(u'inforequests:RefusalAppealOtherReasonValidStep:yes')),
                (0, _(u'inforequests:RefusalAppealOtherReasonValidStep:no')),
                ),
            )

class RefusalAppealOtherReasonValidReasonStep(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.OTHER_REASON
    text_template = u'inforequests/appeals/texts/refusal/other_reason_valid_reason.html'
    section_template = u'inforequests/appeals/papers/refusal/other_reason_valid_reason.html'

    other_reason_valid_reason = PaperCharField(widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealOtherReasonValidReasonStep, cls).applicable(wizard):
            return False
        return wizard.values.get(u'other_reason_valid', True)

    def paper_fields(self, step):
        step.fields[u'other_reason_valid_reason'] = PaperCharField(widget=EditableSpan())

class RefusalAppealOtherReasonInvalidReasonStep(AppealSectionStep, ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.OTHER_REASON
    text_template = u'inforequests/appeals/texts/refusal/other_reason_invalid_reason.html'
    section_template = u'inforequests/appeals/papers/refusal/other_reason_invalid_reason.html'

    other_reason_invalid_reason = PaperCharField(widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealOtherReasonInvalidReasonStep, cls).applicable(wizard):
            return False
        return not wizard.values.get(u'other_reason_valid', True)

    def paper_fields(self, step):
        step.fields[u'other_reason_invalid_reason'] = PaperCharField(widget=EditableSpan())


class SanitizationStep(AppealStep):
    all_sanitizable_reasons = set([
            Action.REFUSAL_REASONS.BUSINESS_SECRET,
            Action.REFUSAL_REASONS.PERSONAL,
            Action.REFUSAL_REASONS.CONFIDENTIAL,
            ])

    @classmethod
    def applicable(cls, wizard):
        return bool(cls.actual_sanitizable_reasons(wizard))

    @classmethod
    def actual_sanitizable_reasons(cls, wizard):
        return cls.all_sanitizable_reasons & set(wizard.branch.last_action.refusal_reason)

    def context(self, extra=None):
        res = super(SanitizationStep, self).context(extra)
        res.update({
                u'sanitizable': self.actual_sanitizable_reasons(self.wizard),
                })
        return res

    def paper_context(self, extra=None):
        res = super(SanitizationStep, self).paper_context(extra)
        res.update({
                u'sanitizable': self.actual_sanitizable_reasons(self.wizard),
                })
        return res

class RefusalAppealSanitizationLevelStep(SanitizationStep):
    text_template = u'inforequests/appeals/texts/refusal/sanitization_level.html'

    sanitization_level = forms.ChoiceField(
            choices=(
                (None, u''),
                (u'overly-sanitized',   _(u'inforequests:RefusalAppealSanitizationLevelStep:OverlySanitized')),
                (u'missing-document',   _(u'inforequests:RefusalAppealSanitizationLevelStep:MissingDocument')),
                (u'properly-sanitized', _(u'inforequests:RefusalAppealSanitizationLevelStep:ProperlySanitized')),
                ),
            )

class RefusalAppealSanitizationOverlySanitizedStep(AppealSectionStep, SanitizationStep):
    text_template = u'inforequests/appeals/texts/refusal/sanitization_overly_sanitized.html'
    section_template = u'inforequests/appeals/papers/refusal/sanitization_overly_sanitized.html'

    sanitization_overly_sanitized = PaperCharField(widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealSanitizationOverlySanitizedStep, cls).applicable(wizard):
            return False
        return wizard.values.get(u'sanitization_level', None) == u'overly-sanitized'

    def paper_fields(self, step):
        step.fields[u'sanitization_overly_sanitized'] = PaperCharField(widget=EditableSpan())

class RefusalAppealSanitizationMissingDocumentStep(AppealSectionStep, SanitizationStep):
    text_template = u'inforequests/appeals/texts/refusal/sanitization_missing_document.html'
    section_template = u'inforequests/appeals/papers/refusal/sanitization_missing_document.html'

    sanitization_missing_document = PaperCharField(widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealSanitizationMissingDocumentStep, cls).applicable(wizard):
            return False
        return wizard.values.get(u'sanitization_level', None) == u'missing-document'

    def paper_fields(self, step):
        step.fields[u'sanitization_missing_document'] = PaperCharField(widget=EditableSpan())

class RefusalAppealSanitizationProperlySanitizedStep(AppealDeadendStep, SanitizationStep):
    text_template = u'inforequests/appeals/texts/refusal/sanitization_properly_sanitized.html'

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealSanitizationProperlySanitizedStep, cls).applicable(wizard):
            return False
        if wizard.values.get(u'sanitization_level', None) != u'properly-sanitized':
            return False
        for reason in cls.actual_sanitizable_reasons(wizard):
            if wizard.reason_sections_are_empty(reason):
                return True
        return False

    def reasons_with_empty_sections(self):
        return [r for r in self.actual_sanitizable_reasons(self.wizard)
                  if self.wizard.reason_sections_are_empty(r)]


class RefusalAppealPaperStep(AppealPaperStep):
    content_template = u'inforequests/appeals/papers/refusal.html'

class RefusalAppealWizard(AppealWizard):
    u"""
    Appeal wizard for branches that end with a refusal action with a reason. The wizard supports
    only reasons covered by its reason steps. If the last action contains any other reason, the
    wizard does not apply.
    """
    step_classes = OrderedDict([
            (u'does_not_have_reason', RefusalAppealDoesNotHaveReasonStep),
            (u'does_not_provide_public_funds', RefusalAppealDoesNotProvidePublicFundsStep),
            (u'does_not_provide_public_funds_reason', RefusalAppealDoesNotProvidePublicFundsReasonStep),
            (u'does_not_provide_fallback_reason', RefusalAppealDoesNotProvideFallbackReasonStep),
            (u'does_not_create_reason', RefusalAppealDoesNotCreateReasonStep),
            (u'copyright_reason', RefusalAppealCopyrightReasonStep),
            (u'business_secret_public_funds', RefusalAppealBusinessSecretPublicFundsStep),
            (u'business_secret_definition', RefusalAppealBusinessSecretDefinitionStep),
            (u'business_secret_definition_reason', RefusalAppealBusinessSecretDefinitionReasonStep),
            (u'business_secret_fallback_reason', RefusalAppealBusinessSecretFallbackReasonStep),
            (u'personal_officer', RefusalAppealPersonalOfficerStep),
            (u'personal_officer_reason', RefusalAppealPersonalOfficerReasonStep),
            (u'personal_fallback_reason', RefusalAppealPersonalFallbackReasonStep),
            (u'confidential_not_confidential', RefusalAppealConfidentialNotConfidentialStep),
            (u'confidential_not_confidential_reason', RefusalAppealConfidentialNotConfidentialReasonStep),
            (u'confidential_fallback_reason', RefusalAppealConfidentialFallbackReasonStep),
            (u'other_reason_valid', RefusalAppealOtherReasonValidStep),
            (u'other_reason_valid_reason', RefusalAppealOtherReasonValidReasonStep),
            (u'other_reason_invalid_reason', RefusalAppealOtherReasonInvalidReasonStep),
            (u'sanitization_level', RefusalAppealSanitizationLevelStep),
            (u'sanitization_overly_sanitized', RefusalAppealSanitizationOverlySanitizedStep),
            (u'sanitization_missing_document', RefusalAppealSanitizationMissingDocumentStep),
            (u'sanitization_properly_sanitized', RefusalAppealSanitizationProperlySanitizedStep),
            (u'paper', RefusalAppealPaperStep),
            (u'final', AppealFinalStep),
            ])

    @classmethod
    def applicable(cls, branch):
        if branch.last_action.type != Action.TYPES.REFUSAL:
            return False
        if not branch.last_action.refusal_reason: # Without reason
            return False
        supported_reasons = set(s.covered_reason
                for s in cls.step_classes.values() if issubclass(s, ReasonStep))
        if set(branch.last_action.refusal_reason) - supported_reasons: # Unsupported reason
            return False
        return True

    def context(self, extra=None):
        res = super(RefusalAppealWizard, self).context(extra)
        res.update({
                u'number_of_reasons': len(self.branch.last_action.refusal_reason),
                })
        return res

    def reason_sections_are_empty(self, reason):
        for step in self.steps.values():
            if step and isinstance(step, ReasonStep) and step.covered_reason == reason:
                if isinstance(step, AppealSectionStep) and not step.section_is_empty():
                    return False
        return True
