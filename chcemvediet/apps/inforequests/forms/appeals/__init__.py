# vim: expandtab
# -*- coding: utf-8 -*-
from django.template.loader import render_to_string

from poleno.utils.date import local_today
from poleno.utils.misc import squeeze
from chcemvediet.apps.inforequests.models import Action
from chcemvediet.apps.inforequests.forms.wizard import WizardStep, Wizard, WizardGroup

class AppealFinalStep(WizardStep):
    template = u'inforequests/appeals/final.html'

    def context(self, extra=None):
        res = super(AppealFinalStep, self).context(extra)
        res.update({
                u'appeal_subject': self.wizard.appeal_subject(),
                u'appeal_content': self.wizard.appeal_content(),
                })
        return res

class AppealWizard(Wizard):
    appeal_subject_template = None
    appeal_content_template = None

    def __init__(self, branch):
        super(AppealWizard, self).__init__()
        self.branch = branch
        self.effective_date = local_today()

    def context(self, extra=None):
        res = super(AppealWizard, self).context(extra)
        res.update({
                u'inforequest': self.branch.inforequest,
                u'branch': self.branch,
                })
        return res

    def extra_state(self):
        return self.branch.pk

    def appeal_context(self):
        res = {}
        res.update({
                u'inforequest': self.branch.inforequest,
                u'branch': self.branch,
                u'last_action': self.branch.last_action,
                u'effective_date': self.effective_date,
                u'rozklad': u'ministerstvo' in self.branch.obligee.name.lower(),
                u'fiktivne': self.branch.last_action.type != Action.TYPES.REFUSAL,
                u'not_at_all': True,
                })
        return res

    def appeal_subject(self):
        return squeeze(render_to_string(self.appeal_subject_template, self.appeal_context()))

    def appeal_content(self):
        return render_to_string(self.appeal_content_template, self.appeal_context())

    def save(self, appeal):
        appeal.branch = self.branch
        appeal.subject = self.appeal_subject()
        appeal.content = self.appeal_content()
        appeal.content_type = Action.CONTENT_TYPES.HTML
        appeal.effective_date = self.effective_date


# Must be after ``AppealWizard`` to break cyclic dependency
from .fallback import FallbackAppealWizard
from .disclosure import DisclosureAppealWizard

class AppealWizards(WizardGroup):
    wizard_classes = [
            DisclosureAppealWizard,
            FallbackAppealWizard
            ]
