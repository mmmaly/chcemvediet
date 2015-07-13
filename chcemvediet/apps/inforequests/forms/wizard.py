# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.core import signing
from django.core.exceptions import SuspiciousOperation
from django.utils.html import format_html
from django.utils.functional import cached_property

from poleno.utils.forms import PrefixedForm


class WizzardRollback(Exception):
    def __init__(self, step):
        self.step = step


class WizardStep(PrefixedForm):
    template = None

    @classmethod
    def applicable(cls, wizard):
        return True

    def __init__(self, wizard, index, *args, **kwargs):
        self.wizard = wizard
        self.index = index
        super(WizardStep, self).__init__(*args, **kwargs)

    def next(self):
        return self.wizard.next_step(self)

    def prev(self):
        return self.wizard.prev_step(self)

    def is_last(self):
        return self.wizard.is_last_step(self)

    def is_first(self):
        return self.wizard.is_first_step(self)

    def state_field(self):
        return self.wizard.state_field(self)

    def context(self, extra=None):
        return dict(self.wizard.context(extra), step=self)


class Wizard(object):
    step_classes = None

    @classmethod
    def applicable(cls):
        raise NotImplementedError

    def __init__(self):
        self.current_step = None
        self.steps = [None for s in self.step_classes]
        self.data = [None for s in self.step_classes]

    def start(self):
        for step_index, step_class in enumerate(self.step_classes):
            if step_class.applicable(self):
                self.steps[step_index] = step_class(self, step_index)
                if self.current_step is None:
                    self.current_step = self.steps[step_index]
        assert self.current_step is not None

    def step(self, post):
        try:
            state = signing.loads(post[u'state'])
            assert state[u'wizard'] == self.__class__.__name__
            current_index = state[u'step_index']
            assert state[u'step_class'] == self.step_classes[current_index].__name__
            assert state[u'extra_state'] == self.extra_state()
            self.data = state[u'data']
            assert type(self.data) is list
            assert len(self.data) == len(self.step_classes)
        except (KeyError, IndexError, AssertionError, signing.BadSignature):
            raise SuspiciousOperation

        for step_index, step_class in enumerate(self.step_classes):
            if step_index < current_index:
                if not step_class.applicable(self):
                    continue
                step = step_class(self, step_index, self.data[step_index])
                self.steps[step_index] = step
                if not step.is_valid():
                    raise WizzardRollback(step)
            elif step_index == current_index:
                if not step_class.applicable(self):
                    raise SuspiciousOperation
                step = step_class(self, step_index, post)
                self.steps[step_index] = step
                self.current_step = step
            else:
                if not step_class.applicable(self):
                    continue
                step = step_class(self, step_index, self.data[step_index])
                self.steps[step_index] = step

    def commit(self):
        assert self.current_step.is_valid()
        step_data = {}
        for field_name in self.current_step.fields:
            step_data[self.current_step.add_prefix(field_name)] = self.current_step._raw_value(field_name)
        self.data[self.current_step.index] = step_data

    def next_step(self, step=None):
        if step is None:
            step = self.current_step
        for next_step in self.steps[step.index+1:]:
            if next_step is not None:
                return next_step
        return None

    def prev_step(self, step=None):
        if step is None:
            step = self.current_step
        for prev_step in reversed(self.steps[:step.index]):
            if prev_step is not None:
                return prev_step
        return None

    def is_last_step(self, step=None):
        return self.next_step(step) is None

    def is_first_step(self, step=None):
        return self.prev_step(step) is None

    def state_field(self, step):
        state = {}
        state[u'wizard'] = self.__class__.__name__
        state[u'step_index'] = step.index
        state[u'step_class'] = step.__class__.__name__
        state[u'extra_state'] = self.extra_state()
        state[u'data'] = self.data
        return format_html(u'<input type="hidden" name="state" value="{0}" />', signing.dumps(state))

    def context(self, extra=None):
        return dict(extra or {}, wizard=self)

    def extra_state(self):
        return None


class WizardGroup(object):
    wizard_classes = []

    @classmethod
    def find_applicable(cls, *args, **kwargs):
        for wizard_class in cls.wizard_classes:
            if wizard_class.applicable(*args, **kwargs):
                return wizard_class(*args, **kwargs)
        raise ValueError
