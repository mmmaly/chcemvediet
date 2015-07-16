# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

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

    def __init__(self, wizard, index, key, *args, **kwargs):
        self.wizard = wizard
        self.index = index
        self.key = key
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

    def get_cleaned_data(self, field):
        if self.is_valid():
            return self.cleaned_data[field]
        else:
            return None

    def context(self, extra=None):
        return dict(self.wizard.context(extra), step=self)


class Wizard(object):
    step_classes = None

    @classmethod
    def applicable(cls):
        raise NotImplementedError

    def __init__(self):
        self.current_step = None
        self.steps = None
        self.data = None

    def start(self):
        self.current_step = None
        self.steps = OrderedDict([(k, None) for k in self.step_classes])
        self.data = OrderedDict([(k, None) for k in self.step_classes])

        for step_index, (step_key, step_class) in enumerate(self.step_classes.items()):
            if step_class.applicable(self):
                self.steps[step_key] = step_class(self, step_index, step_key)
                if self.current_step is None:
                    self.current_step = self.steps[step_key]
        assert self.current_step is not None

    def step(self, post):
        try:
            state = signing.loads(post[u'state'])
            assert state[u'wizard'] == self.__class__.__name__
            assert state[u'extra_state'] == self.extra_state()

            current_key = state[u'step_key']
            assert current_key in self.step_classes

            state_data = OrderedDict([(k, v) for k, v in state[u'data']])
            assert state_data.keys() == self.step_classes.keys()

        except (TypeError, KeyError, ValueError, AssertionError, signing.BadSignature):
            raise SuspiciousOperation

        self.current_step = None
        self.steps = OrderedDict([(k, None) for k in self.step_classes])
        self.data = state_data

        current_index = self.step_classes.keys().index(current_key)
        for step_index, (step_key, step_class) in enumerate(self.step_classes.items()):
            if step_index < current_index:
                if not step_class.applicable(self):
                    continue
                step = step_class(self, step_index, step_key, self.data[step_key])
                self.steps[step_key] = step
                if not step.is_valid():
                    raise WizzardRollback(step)
            elif step_index == current_index:
                if not step_class.applicable(self):
                    raise SuspiciousOperation
                step = step_class(self, step_index, step_key, post)
                self.steps[step_key] = step
                self.current_step = step
            else:
                if not step_class.applicable(self):
                    continue
                step = step_class(self, step_index, step_key, self.data[step_key])
                self.steps[step_key] = step

    def commit(self):
        assert self.current_step.is_valid()
        step_data = {}
        for field_name in self.current_step.fields:
            step_data[self.current_step.add_prefix(field_name)] = self.current_step._raw_value(field_name)
        self.data[self.current_step.key] = step_data

    def next_step(self, step=None):
        if step is None:
            step = self.current_step
        for next_step in self.steps.values()[step.index+1:]:
            if next_step is not None:
                return next_step
        return None

    def prev_step(self, step=None):
        if step is None:
            step = self.current_step
        for prev_step in reversed(self.steps.values()[:step.index]):
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
        state[u'extra_state'] = self.extra_state()
        state[u'step_key'] = step.key
        state[u'data'] = self.data.items()
        return format_html(u'<input type="hidden" name="state" value="{0}" />', signing.dumps(state))

    def context(self, extra=None):
        return dict(extra or {}, wizard=self)

    def extra_state(self):
        return None

    def unique_name(self):
        return self.__class__.__name__


class WizardGroup(object):
    wizard_classes = []

    @classmethod
    def find_applicable(cls, *args, **kwargs):
        for wizard_class in cls.wizard_classes:
            if wizard_class.applicable(*args, **kwargs):
                return wizard_class(*args, **kwargs)
        raise ValueError
