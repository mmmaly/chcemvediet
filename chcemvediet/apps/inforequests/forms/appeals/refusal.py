# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from django import forms
from django.utils.translation import ugettext_lazy as _

from poleno.utils.forms import EditableSpan
from chcemvediet.apps.wizards import WizardStep
from chcemvediet.apps.inforequests.models import Action

from . import PaperCharField
from . import AppealSectionStep, AppealDeadEndStep, AppealPaperStep, AppealFinalStep, AppealWizard

class ReasonStep(WizardStep):
    covered_reason = None

    @classmethod
    def applicable(cls, wizard):
        return cls.covered_reason in wizard.branch.last_action.refusal_reason

    def context(self, extra=None):
        res = super(ReasonStep, self).context(extra)
        res.update({
                u'first_reason': self.is_first_reason(),
                })
        return res

    def is_first_reason(self):
        for step in self.wizard.steps.values()[:self.index]:
            if isinstance(step, ReasonSectionStep):
                return False
        return True

class ReasonSectionStep(AppealSectionStep, ReasonStep):
    pass

class ReasonDeadEndStep(AppealDeadEndStep, ReasonStep):
    pass


class RefusalAppealDoesNotHaveStep(ReasonSectionStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_HAVE
    text_template = u'inforequests/appeals/texts/refusal-does-not-have-text.html'
    section_template = u'inforequests/appeals/papers/refusal-does-not-have.html'

    does_not_have_reason = PaperCharField(widget=EditableSpan())

class RefusalAppealDoesNotProvideStep(ReasonSectionStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_PROVIDE
    text_template = u'inforequests/appeals/texts/refusal-does-not-provide-text.html'
    section_template = u'inforequests/appeals/papers/refusal-does-not-provide.html'

class RefusalAppealDoesNotCreateStep(ReasonSectionStep):
    covered_reason = Action.REFUSAL_REASONS.DOES_NOT_CREATE
    text_template = u'inforequests/appeals/texts/refusal-does-not-create-text.html'
    section_template = u'inforequests/appeals/papers/refusal-does-not-create.html'

class RefusalAppealCopyrightStep(ReasonSectionStep):
    covered_reason = Action.REFUSAL_REASONS.COPYRIGHT
    text_template = u'inforequests/appeals/texts/refusal-copyright-text.html'
    section_template = u'inforequests/appeals/papers/refusal-copyright.html'

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

class RefusalAppealBusinessSecretDeadEndStep(ReasonDeadEndStep):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    text_template = u'inforequests/appeals/texts/refusal-business-secret-dead-end-text.html'

    @classmethod
    def applicable(cls, wizard):
        if not super(RefusalAppealBusinessSecretDeadEndStep, cls).applicable(wizard):
            return False
        if wizard.values.get(u'business_secret_public_funds', True):
            return False
        if wizard.values.get(u'business_secret_definition', True):
            return False
        return True

class RefusalAppealBusinessSecretStep(ReasonSectionStep):
    covered_reason = Action.REFUSAL_REASONS.BUSINESS_SECRET
    text_template = u'inforequests/appeals/texts/refusal-business-secret-text.html'
    section_template = u'inforequests/appeals/papers/refusal-business-secret.html'

    def __init__(self, *args, **kwargs):
        super(RefusalAppealBusinessSecretStep, self).__init__(*args, **kwargs)
        choices = self.wizard.values.get(u'business_secret_definition', [])
        for choice in choices:
            self.fields[u'business_secret_definition_' + choice] = PaperCharField(widget=EditableSpan())

class RefusalAppealPersonalStep(ReasonSectionStep):
    covered_reason = Action.REFUSAL_REASONS.PERSONAL
    text_template = u'inforequests/appeals/texts/refusal-personal-text.html'
    section_template = u'inforequests/appeals/papers/refusal-personal.html'

class RefusalAppealConfidentialStep(ReasonSectionStep):
    covered_reason = Action.REFUSAL_REASONS.CONFIDENTIAL
    text_template = u'inforequests/appeals/texts/refusal-confidential-text.html'
    section_template = u'inforequests/appeals/papers/refusal-confidential.html'

class RefusalAppealOtherReasonStep(ReasonSectionStep):
    covered_reason = Action.REFUSAL_REASONS.OTHER_REASON
    text_template = u'inforequests/appeals/texts/refusal-other-reason-text.html'
    section_template = u'inforequests/appeals/papers/refusal-other-reason.html'

    other_reason_reason = PaperCharField(widget=EditableSpan())

class RefusalAppealPaperStep(AppealPaperStep):
    subject_template = u'inforequests/appeals/papers/subject.txt'
    content_template = u'inforequests/appeals/papers/refusal.html'

    def __init__(self, *args, **kwargs):
        super(RefusalAppealPaperStep, self).__init__(*args, **kwargs)
        if self.wizard.steps[u'does_not_have']:
            self.fields[u'does_not_have_reason'] = PaperCharField(widget=EditableSpan())
        if self.wizard.steps[u'business_secret']:
            choices = self.wizard.values.get(u'business_secret_definition', [])
            for choice in choices:
                self.fields[u'business_secret_definition_' + choice] = PaperCharField(widget=EditableSpan())
        if self.wizard.steps[u'other_reason']:
            self.fields[u'other_reason_reason'] = PaperCharField(widget=EditableSpan())

class RefusalAppealWizard(AppealWizard):
    u"""
    Appeal wizard for branches that end with a refusal action with a reason. The wizard supports
    only the reasons listed in ``supported_reasons``. If the last action contains any other reason,
    the wizard does not apply.
    """
    step_classes = OrderedDict([
            (u'does_not_have', RefusalAppealDoesNotHaveStep),
            (u'does_not_provide', RefusalAppealDoesNotProvideStep),
            (u'does_not_create', RefusalAppealDoesNotCreateStep),
            (u'copyright', RefusalAppealCopyrightStep),
            (u'business_secret_public_funds', RefusalAppealBusinessSecretPublicFundsStep),
            (u'business_secret_definition', RefusalAppealBusinessSecretDefinitionStep),
            (u'business_secret_dead_end', RefusalAppealBusinessSecretDeadEndStep),
            (u'business_secret', RefusalAppealBusinessSecretStep),
            (u'personal', RefusalAppealPersonalStep),
            (u'confidential', RefusalAppealConfidentialStep),
            (u'other_reason', RefusalAppealOtherReasonStep),
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
                for s in cls.step_classes.values() if issubclass(s, ReasonSectionStep))
        if set(branch.last_action.refusal_reason) - supported_reasons: # Unsupported reason
            return False
        return True

    def applicable_reason_steps(self):
        res = []
        for step in self.steps.values():
            if isinstance(step, ReasonSectionStep):
                res.append(step)
        return res
