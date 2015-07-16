# vim: expandtab
# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from django import forms
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from poleno.utils.date import local_today
from poleno.utils.misc import squeeze
from chcemvediet.apps.inforequests.models import Action
from chcemvediet.apps.inforequests.forms.wizard import WizardStep, Wizard, WizardGroup


class AppealPaperStep(WizardStep):
    template = u'inforequests/appeals/paper.html'
    subject_template = None
    content_template = None

    effective_date = forms.DateField(
            localize=True,
            widget=forms.DateInput(attrs={
                u'placeholder': _('inforequests:AppealPaperStep:effective_date:placeholder'),
                u'class': u'datepicker',
                }),
            )

    def __init__(self, *args, **kwargs):
        super(AppealPaperStep, self).__init__(*args, **kwargs)
        self.initial[u'effective_date'] = local_today()

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
        res.update({
                u'appeal_subject': self.wizard.finalize_subject(),
                u'appeal_content': self.wizard.finalize_content(),
                })
        return res

class AppealWizard(Wizard):

    def __init__(self, branch):
        super(AppealWizard, self).__init__()
        self.branch = branch

    def context(self, extra=None):
        res = super(AppealWizard, self).context(extra)
        res.update({
                u'inforequest': self.branch.inforequest,
                u'branch': self.branch,
                u'last_action': self.branch.last_action,
                u'rozklad': u'ministerstvo' in self.branch.obligee.name.lower(),
                u'fiktivne': self.branch.last_action.type != Action.TYPES.REFUSAL,
                u'not_at_all': True,
                })
        return res

    def extra_state(self):
        return self.branch.pk

    def unique_name(self):
        return u'{0}-{1}'.format(self.__class__.__name__, self.branch.pk)

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

class AppealWizards(WizardGroup):
    wizard_classes = [
            DisclosureAppealWizard,
            FallbackAppealWizard
            ]
