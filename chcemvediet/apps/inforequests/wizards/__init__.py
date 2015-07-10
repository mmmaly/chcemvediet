# vim: expandtab
# -*- coding: utf-8 -*-
from poleno.utils.forms import PrefixedForm


class WizardStep(PrefixedForm):

    def __init__(self, *args, **kwargs):
        self.draft = kwargs.pop(u'draft', False)
        super(WizardStep, self).__init__(*args, **kwargs)

        if self.draft:
            for field in self.fields:
                field.required = False


class Wizard(object):

    @classmethod
    def condition(cls):
        raise NotImplementedError


class WizardGroup(object):

    def __init__(self):
        self._wizards = []

    def register(self, wizard):
        self._wizards.append(wizard)

    def find(self, **kwargs):
        for wizard in self._wizards:
            if wizard.condition(**kwargs):
                return wizard
        raise ValueError
