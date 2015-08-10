# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse

from chcemvediet.apps.wizards import WizardGroup, Wizard, WizardStep


class ClarificationResponseStep(WizardStep):
    template = u'inforequests/clarification_responses/base.html'

class ClarificationResponseWizard(Wizard):

    def __init__(self, branch):
        super(ClarificationResponseWizard, self).__init__()
        self.instance_id = u'%s-%s' % (self.__class__.__name__, branch.last_action.pk)
        self.branch = branch

    def get_step_url(self, step, anchor=u''):
        return reverse(u'inforequests:clarification_response_step', args=[self.branch.inforequest.pk, self.branch.pk, step.index]) + anchor

    def context(self, extra=None):
        res = super(ClarificationResponseWizard, self).context(extra)
        res.update({
                u'inforequest': self.branch.inforequest,
                u'branch': self.branch,
                u'last_action': self.branch.last_action,
                })
        return res


# Must be after ``ClarificationResponseWizard`` to break cyclic dependency
from .smail import SmailClarificationResponseWizard

class ClarificationResponseWizards(WizardGroup):
    wizard_classes = [
            SmailClarificationResponseWizard,
            ]
