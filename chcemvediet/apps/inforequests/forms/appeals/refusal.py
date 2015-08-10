# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from django import forms
from django.utils.translation import ugettext_lazy as _

from poleno.utils.forms import EditableSpan
from chcemvediet.apps.inforequests.models import Action

from . import PaperCharField, OptionalReasonCheckboxField
from . import AppealStep, AppealSectionStep, AppealPaperStep, AppealFinalStep, AppealWizard

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


class RefusalAppealDoesNotHaveReasonStep(ReasonStep, AppealSectionStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_HAVE
    text_template = u'inforequests/appeals/texts/refusal-does-not-have-reason-text.html'
    section_template = u'inforequests/appeals/papers/refusal-does-not-have-reason.html'

    does_not_have_reason = PaperCharField(widget=EditableSpan())

    def paper_fields(self, step):
        step.fields[u'does_not_have_reason'] = PaperCharField(widget=EditableSpan())


class RefusalAppealDoesNotProvidePublicFundsStep(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_PROVIDE
    text_template = u'inforequests/appeals/texts/refusal-does-not-provide-public-funds-text.html'

    does_not_provide_public_funds = forms.TypedChoiceField(
            coerce=int,
            choices=(
                (None, u''),
                (1, _(u'inforequests:RefusalAppealDoesNotProvidePublicFundsStep:yes')),
                (0, _(u'inforequests:RefusalAppealDoesNotProvidePublicFundsStep:no')),
                ),
            )

class RefusalAppealDoesNotProvidePublicFundsReasonStep(ReasonStep, AppealSectionStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_PROVIDE
    text_template = u'inforequests/appeals/texts/refusal-does-not-provide-public-funds-reason-text.html'
    section_template = u'inforequests/appeals/papers/refusal-does-not-provide-public-funds-reason.html'

    does_not_provide_public_funds_reason = PaperCharField(widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealDoesNotProvidePublicFundsReasonStep, cls).applicable(wizard):
            return False
        return wizard.values.get(u'does_not_provide_public_funds', True)

    def paper_fields(self, step):
        step.fields[u'does_not_provide_public_funds_reason'] = PaperCharField(widget=EditableSpan())

class RefusalAppealDoesNotProvideFallbackReasonStep(ReasonStep, AppealSectionStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_PROVIDE
    text_template = u'inforequests/appeals/texts/refusal-does-not-provide-fallback-reason-text.html'
    section_template = u'inforequests/appeals/papers/refusal-does-not-provide-fallback-reason.html'

    does_not_provide_fallback = OptionalReasonCheckboxField()
    does_not_provide_fallback_reason = PaperCharField(widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealDoesNotProvideFallbackReasonStep, cls).applicable(wizard):
            return False
        return not wizard.values.get(u'does_not_provide_public_funds', True)

    def paper_fields(self, step):
        step.fields[u'does_not_provide_fallback_reason'] = PaperCharField(widget=EditableSpan())


class RefusalAppealDoesNotCreateReasonStep(ReasonStep, AppealSectionStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_CREATE
    text_template = u'inforequests/appeals/texts/refusal-does-not-create-reason-text.html'
    section_template = u'inforequests/appeals/papers/refusal-does-not-create-reason.html'

    does_not_create_reason = PaperCharField(widget=EditableSpan())

    def paper_fields(self, step):
        step.fields[u'does_not_create_reason'] = PaperCharField(widget=EditableSpan())


class RefusalAppealCopyrightReasonStep(ReasonStep, AppealSectionStep):
    covered_reason = Action.REFUSAL_REASONS.COPYRIGHT
    text_template = u'inforequests/appeals/texts/refusal-copyright-reason-text.html'
    section_template = u'inforequests/appeals/papers/refusal-copyright-reason.html'

    copyright_reason = PaperCharField(widget=EditableSpan())

    def paper_fields(self, step):
        step.fields[u'copyright_reason'] = PaperCharField(widget=EditableSpan())


class RefusalAppealBusinessSecretPublicFundsStep(ReasonStep):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    text_template = u'inforequests/appeals/texts/refusal-business-secret-public-funds-text.html'

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
    text_template = u'inforequests/appeals/texts/refusal-business-secret-definition-text.html'
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

class RefusalAppealBusinessSecretDefinitionReasonStep(ReasonStep, AppealSectionStep):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    text_template = u'inforequests/appeals/texts/refusal-business-secret-definition-reason-text.html'
    section_template = u'inforequests/appeals/papers/refusal-business-secret-definition-reason.html'

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

class RefusalAppealBusinessSecretFallbackReasonStep(ReasonStep, AppealSectionStep):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    text_template = u'inforequests/appeals/texts/refusal-business-secret-fallback-reason-text.html'
    section_template = u'inforequests/appeals/papers/refusal-business-secret-fallback-reason.html'

    business_secret_fallback = OptionalReasonCheckboxField(required=False)
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
    text_template = u'inforequests/appeals/texts/refusal-personal-officer-text.html'

    personal_officer = forms.TypedChoiceField(
            coerce=int,
            choices=(
                (None, u''),
                (1, _(u'inforequests:RefusalAppealPersonalOfficerStep:yes')),
                (0, _(u'inforequests:RefusalAppealPersonalOfficerStep:no')),
                ),
            )

class RefusalAppealPersonalOfficerReasonStep(ReasonStep, AppealSectionStep):
    covered_reason = Action.REFUSAL_REASONS.PERSONAL
    text_template = u'inforequests/appeals/texts/refusal-personal-officer-reason-text.html'
    section_template = u'inforequests/appeals/papers/refusal-personal-officer-reason.html'

    personal_officer_reason = PaperCharField(required=False, widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealPersonalOfficerReasonStep, cls).applicable(wizard):
            return False
        return wizard.values.get(u'personal_officer', True)

    def paper_fields(self, step):
        step.fields[u'personal_officer_reason'] = PaperCharField(required=False, widget=EditableSpan())

class RefusalAppealPersonalFallbackReasonStep(ReasonStep, AppealSectionStep):
    covered_reason = Action.REFUSAL_REASONS.PERSONAL
    text_template = u'inforequests/appeals/texts/refusal-personal-fallback-reason-text.html'
    section_template = u'inforequests/appeals/papers/refusal-personal-fallback-reason.html'

    personal_fallback = OptionalReasonCheckboxField(required=False)
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
    text_template = u'inforequests/appeals/texts/refusal-confidential-not-confidential-text.html'

    confidential_not_confidential = forms.TypedChoiceField(
            coerce=int,
            choices=(
                (None, u''),
                (1, _(u'inforequests:RefusalAppealConfidentialNotConfidentialStep:yes')),
                (0, _(u'inforequests:RefusalAppealConfidentialNotConfidentialStep:no')),
                ),
            )

class RefusalAppealConfidentialNotConfidentialReasonStep(ReasonStep, AppealSectionStep):
    covered_reason = Action.REFUSAL_REASONS.CONFIDENTIAL
    text_template = u'inforequests/appeals/texts/refusal-confidential-not-confidential-reason-text.html'
    section_template = u'inforequests/appeals/papers/refusal-confidential-not-confidential-reason.html'

    confidential_not_confidential_reason = PaperCharField(required=False, widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealConfidentialNotConfidentialReasonStep, cls).applicable(wizard):
            return False
        return wizard.values.get(u'confidential_not_confidential', True)

    def paper_fields(self, step):
        step.fields[u'confidential_not_confidential_reason'] = PaperCharField(required=False, widget=EditableSpan())

class RefusalAppealConfidentialFallbackReasonStep(ReasonStep, AppealSectionStep):
    covered_reason = Action.REFUSAL_REASONS.CONFIDENTIAL
    text_template = u'inforequests/appeals/texts/refusal-confidential-fallback-reason-text.html'
    section_template = u'inforequests/appeals/papers/refusal-confidential-fallback-reason.html'

    confidential_fallback = OptionalReasonCheckboxField(required=False)
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
    text_template = u'inforequests/appeals/texts/refusal-other-reason-valid-text.html'

    other_reason_valid = forms.TypedChoiceField(
            coerce=int,
            choices=(
                (None, u''),
                (1, _(u'inforequests:RefusalAppealOtherReasonValidStep:yes')),
                (0, _(u'inforequests:RefusalAppealOtherReasonValidStep:no')),
                ),
            )

class RefusalAppealOtherReasonValidReasonStep(ReasonStep, AppealSectionStep):
    covered_reason = Action.REFUSAL_REASONS.OTHER_REASON
    text_template = u'inforequests/appeals/texts/refusal-other-reason-valid-reason-text.html'
    section_template = u'inforequests/appeals/papers/refusal-other-reason-valid-reason.html'

    other_reason_valid_reason = PaperCharField(widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealOtherReasonValidReasonStep, cls).applicable(wizard):
            return False
        return wizard.values.get(u'other_reason_valid', True)

    def paper_fields(self, step):
        step.fields[u'other_reason_valid_reason'] = PaperCharField(widget=EditableSpan())

class RefusalAppealOtherReasonInvalidReasonStep(ReasonStep, AppealSectionStep):
    covered_reason = Action.REFUSAL_REASONS.OTHER_REASON
    text_template = u'inforequests/appeals/texts/refusal-other-reason-invalid-reason-text.html'
    section_template = u'inforequests/appeals/papers/refusal-other-reason-invalid-reason.html'

    other_reason_invalid_reason = PaperCharField(widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealOtherReasonInvalidReasonStep, cls).applicable(wizard):
            return False
        return not wizard.values.get(u'other_reason_valid', True)

    def paper_fields(self, step):
        step.fields[u'other_reason_invalid_reason'] = PaperCharField(widget=EditableSpan())


class SanitizationStep(AppealStep):
    sanitizable_reasons = set([
            Action.REFUSAL_REASONS.BUSINESS_SECRET,
            Action.REFUSAL_REASONS.PERSONAL,
            Action.REFUSAL_REASONS.CONFIDENTIAL,
            ])

    @classmethod
    def applicable(cls, wizard):
        return bool(cls.sanitizable_reasons & set(wizard.branch.last_action.refusal_reason))

    def context(self, extra=None):
        res = super(SanitizationStep, self).context(extra)
        res.update({
                u'sanitizable': self.sanitizable(),
                })
        return res

    def paper_context(self, extra=None):
        res = super(SanitizationStep, self).paper_context(extra)
        res.update({
                u'sanitizable': self.sanitizable(),
                })
        return res

    def sanitizable(self):
        covered = set(step.covered_reason
                for step in self.wizard.steps.values()
                if step and isinstance(step, ReasonStep) and isinstance(step, AppealSectionStep)
                    and not step.section_is_empty()
                )
        sanitizable = self.sanitizable_reasons & set(self.wizard.branch.last_action.refusal_reason)
        return {
                u'all': sanitizable,
                u'covered': sanitizable & covered,
                u'not_covered': sanitizable - covered,
                }

class RefusalAppealSanitizationLevelStep(SanitizationStep):
    text_template = u'inforequests/appeals/texts/refusal-sanitization-level-text.html'

    sanitization_level = forms.ChoiceField(
            choices=(
                (None, u''),
                (u'overly-sanitized',   _(u'inforequests:RefusalAppealSanitizationLevelStep:OverlySanitized')),
                (u'missing-document',   _(u'inforequests:RefusalAppealSanitizationLevelStep:MissingDocument')),
                (u'properly-sanitized', _(u'inforequests:RefusalAppealSanitizationLevelStep:ProperlySanitized')),
                (u'not-sanitized',      _(u'inforequests:RefusalAppealSanitizationLevelStep:NotSanitized')),
                ),
            )

class RefusalAppealSanitizationOverlySanitizedStep(SanitizationStep, AppealSectionStep):
    text_template = u'inforequests/appeals/texts/refusal-sanitization-overly-sanitized-text.html'
    section_template = u'inforequests/appeals/papers/refusal-sanitization-overly-sanitized.html'

    sanitization_overly_sanitized = PaperCharField(widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealSanitizationOverlySanitizedStep, cls).applicable(wizard):
            return False
        return wizard.values.get(u'sanitization_level', None) == u'overly-sanitized'

    def paper_fields(self, step):
        step.fields[u'sanitization_overly_sanitized'] = PaperCharField(widget=EditableSpan())

class RefusalAppealSanitizationMissingDocumentStep(SanitizationStep, AppealSectionStep):
    text_template = u'inforequests/appeals/texts/refusal-sanitization-missing-document-text.html'
    section_template = u'inforequests/appeals/papers/refusal-sanitization-missing-document.html'

    sanitization_missing_document = PaperCharField(widget=EditableSpan())

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealSanitizationMissingDocumentStep, cls).applicable(wizard):
            return False
        return wizard.values.get(u'sanitization_level', None) == u'missing-document'

    def paper_fields(self, step):
        step.fields[u'sanitization_missing_document'] = PaperCharField(widget=EditableSpan())


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
