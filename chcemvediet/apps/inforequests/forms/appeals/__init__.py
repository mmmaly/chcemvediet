# vim: expandtab
# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from django import forms
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from django.utils.dateformat import format

from poleno.utils.date import local_today
from poleno.utils.misc import squeeze
from chcemvediet.apps.wizards import WizardStep, Wizard, WizardGroup
from chcemvediet.apps.inforequests.models import Action


class PaperField(forms.Field):

    def __init__(self, *args, **kwargs):
        super(PaperField, self).__init__(*args, **kwargs)

    def render_finalized(self, value):
        return format_html(u'{0}', value)

class PaperDateField(PaperField, forms.DateField):

    def __init__(self, *args, **kwargs):
        self.final_format = kwargs.pop(u'final_format', settings.DATE_FORMAT)
        super(PaperDateField, self).__init__(*args, **kwargs)

    def render_finalized(self, value):
        if value in [None, u'']:
            return u''
        return format_html(u'{0}', format(value, self.final_format))

class PaperCharField(PaperField, forms.CharField):

    def render_finalized(self, value):
        if value is None:
            value = u''
        return format_html(u'<span style="white-space: pre-wrap;">{0}</span>', value)


class AppealSectionStep(WizardStep):
    template = u'inforequests/appeals/section.html'
    section_template = None

    def context(self, extra=None):
        res = super(AppealSectionStep, self).context(extra)
        res.update({
                u'section_template': self.section_template,
                })
        return res

class AppealDeadEndStep(WizardStep):
    template = u'inforequests/appeals/dead-end.html'
    counted_step = False

    def clean(self):
        cleaned_data = super(AppealDeadEndStep, self).clean()
        self.add_error(None, u'dead-end')
        return cleaned_data

class AppealPaperStep(WizardStep):
    template = u'inforequests/appeals/paper.html'
    subject_template = None
    content_template = None

    effective_date = PaperDateField(
            localize=True,
            initial=local_today,
            final_format=u'd.m.Y',
            widget=forms.DateInput(attrs={
                u'placeholder': _('inforequests:AppealPaperStep:effective_date:placeholder'),
                u'class': u'datepicker',
                }),
            )

    def clean(self):
        cleaned_data = super(AppealPaperStep, self).clean()

        branch = self.wizard.branch
        effective_date = cleaned_data.get(u'effective_date', None)
        if effective_date:
            try:
                if effective_date < branch.last_action.effective_date:
                    raise ValidationError(_(u'inforequests:AppealPaperStep:effective_date:older_than_last_action_error'))
                if effective_date < local_today():
                    raise ValidationError(_(u'inforequests:AppealPaperStep:effective_date:from_past_error'))
                if effective_date > local_today() + relativedelta(days=5):
                    raise ValidationError(_(u'inforequests:AppealPaperStep:effective_date:too_far_from_future_error'))
            except ValidationError as e:
                self.add_error(u'effective_date', e)

        return cleaned_data

    def context(self, extra=None):
        res = super(AppealPaperStep, self).context(extra)
        res.update({
                u'subject_template': self.subject_template,
                u'content_template': self.content_template,
                })
        return res

class AppealFinalStep(WizardStep):
    template = u'inforequests/appeals/final.html'

    def context(self, extra=None):
        res = super(AppealFinalStep, self).context(extra)
        effective_date = self.wizard.values[u'effective_date']
        deadline_missed = self.wizard.branch.last_action.deadline_missed_at(effective_date)
        deadline_remaining = self.wizard.branch.last_action.deadline_remaining_at(effective_date)
        res.update({
                u'appeal_subject': self.wizard.finalize_subject(),
                u'appeal_content': self.wizard.finalize_content(),
                u'effective_date': effective_date,
                u'deadline_missed_at_effective_date': deadline_missed,
                u'deadline_remaining_at_effective_date': deadline_remaining,
                })
        return res

class AppealWizard(Wizard):

    def __init__(self, branch):
        super(AppealWizard, self).__init__()
        self.instance_id = u'%s-%s' % (self.__class__.__name__, branch.last_action.pk)
        self.branch = branch

    def context(self, extra=None):
        res = super(AppealWizard, self).context(extra)
        res.update({
                u'inforequest': self.branch.inforequest,
                u'branch': self.branch,
                u'last_action': self.branch.last_action,
                u'rozklad': u'ministerstvo' in self.branch.obligee.name.lower(),
                u'fiktivne': self.branch.last_action.type != Action.TYPES.REFUSAL,
                u'not_at_all': self.branch.last_action.disclosure_level not in [
                    Action.DISCLOSURE_LEVELS.PARTIAL, Action.DISCLOSURE_LEVELS.FULL],
                u'retrospection': self.retrospection_data(self.branch.last_action),
                })
        return res

    def retrospection_data(self, last_action, recursive=False):
        res = []
        branch = last_action.branch
        obligee = branch.historicalobligee if recursive else None

        def clause(key, **kwargs):
            res.append(dict(key=key, obligee=obligee, **kwargs))

        if branch.is_main:
            clause(u'request', inforequest=branch.inforequest)
        else:
            res.extend(self.retrospection_data(branch.advanced_by, recursive=True))

        start_index = 0
        while True:
            actions = {t: [] for t in Action.TYPES._inverse}
            for index, action in enumerate(branch.actions[start_index:]):
                actions[action.type].append((start_index+index, action))
                if action == last_action or action.type == Action.TYPES.APPEAL:
                    break

            if actions[Action.TYPES.REMANDMENT] and start_index > 0:
                clause(u'remandment', remandment=actions[Action.TYPES.REMANDMENT][0][1])
            if actions[Action.TYPES.CONFIRMATION]:
                clause(u'confirmation', confirmation=actions[Action.TYPES.CONFIRMATION][0][1])
            if actions[Action.TYPES.CLARIFICATION_REQUEST]:
                requests = [a for i, a in actions[Action.TYPES.CLARIFICATION_REQUEST]]
                responses = [a for i, a in actions[Action.TYPES.CLARIFICATION_RESPONSE]]
                clause(u'clarification', clarification_requests=requests, clarification_responses=responses)
            if actions[Action.TYPES.EXTENSION]:
                extensions = [a for i, a in actions[Action.TYPES.EXTENSION]]
                clause(u'extension', extensions=extensions)
            if actions[Action.TYPES.APPEAL]:
                index, appeal = actions[Action.TYPES.APPEAL][0]
                previous = branch.actions[index-1] if index else None
                not_at_all = previous.disclosure_level not in [Action.DISCLOSURE_LEVELS.PARTIAL, Action.DISCLOSURE_LEVELS.FULL]
                if previous.type == Action.TYPES.ADVANCEMENT:
                    clause(u'advancement-appeal', advancement=previous, appeal=appeal, not_at_all=not_at_all)
                elif previous.type == Action.TYPES.DISCLOSURE:
                    clause(u'disclosure-appeal', disclosure=previous, appeal=appeal, not_at_all=not_at_all)
                elif previous.type == Action.TYPES.REFUSAL:
                    clause(u'refusal-appeal', refusal=previous, appeal=appeal)
                elif previous.type == Action.TYPES.EXPIRATION:
                    clause(u'expiration-appeal', expiration=previous, appeal=appeal)
                else:
                    clause(u'wild-appeal', appeal=appeal)
                start_index = index + 1
            else:
                break

        if recursive:
            clause(u'advancement', advancement=last_action)

        return res

    def finalize_subject(self):
        step = self.steps[u'paper']
        return squeeze(render_to_string(step.subject_template, step.context(dict(finalize=True))))

    def finalize_content(self):
        step = self.steps[u'paper']
        return render_to_string(step.content_template, step.context(dict(finalize=True)))

    def finalize_effective_date(self):
        step = self.steps[u'paper']
        return step.cleaned_data[u'effective_date']

    def save(self, appeal):
        appeal.branch = self.branch
        appeal.subject = self.finalize_subject()
        appeal.content = self.finalize_content()
        appeal.content_type = Action.CONTENT_TYPES.HTML
        appeal.effective_date = self.finalize_effective_date()


# Must be after ``AppealWizard`` to break cyclic dependency
from .fallback import FallbackAppealWizard
from .disclosure import DisclosureAppealWizard
from .refusal import RefusalAppealWizard

class AppealWizards(WizardGroup):
    wizard_classes = [
            DisclosureAppealWizard,
            RefusalAppealWizard,
            FallbackAppealWizard,
            ]
