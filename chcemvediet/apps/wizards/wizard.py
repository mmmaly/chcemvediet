# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from django import forms
from django.core import signing
from django.core.exceptions import SuspiciousOperation
from django.template import RequestContext
from django.template.loader import render_to_string
from django.shortcuts import render
from django.utils.html import format_html

from .models import WizardDraft


class WizzardRollback(Exception):
    def __init__(self, step):
        self.step = step


class WizardStep(forms.Form):
    template = u'inforequests/appeals/base.html'
    text_template = None
    form_template = None
    counted_step = True

    @classmethod
    def applicable(cls, wizard):
        return True

    def __init__(self, wizard, index, key, *args, **kwargs):
        super(WizardStep, self).__init__(*args, **kwargs)
        self.wizard = wizard
        self.index = index
        self.key = key

    def add_prefix(self, field_name):
        return self.wizard.add_prefix(field_name)

    def next(self):
        return self.wizard.next_step(self)

    def prev(self):
        return self.wizard.prev_step(self)

    def is_last(self):
        return self.wizard.is_last_step(self)

    def is_first(self):
        return self.wizard.is_first_step(self)

    def step_number(self):
        return self.wizard.step_number(self)

    def state_field(self):
        return self.wizard.state_field(self)

    def context(self, extra=None):
        return dict(self.wizard.context(extra),
                step=self,
                text_template=self.text_template,
                form_template=self.form_template,
                )

    def render(self, request):
        return render(request, self.template, self.context())

    def render_to_string(self, request):
        return render_to_string(self.template, context_instance=RequestContext(request), dictionary=self.context())


class Wizard(object):
    step_classes = None

    @classmethod
    def applicable(cls):
        raise NotImplementedError

    def __init__(self):
        self.instance_id = None
        self.current_step = None
        self.steps = None
        self.data = None
        self.values = None

    def start(self):
        try:
            draft = WizardDraft.objects.get(pk=self.instance_id)
            self.data = draft.data
        except WizardDraft.DoesNotExist:
            self.data = {}

        self.steps = OrderedDict([(k, None) for k in self.step_classes])
        self.values = {}
        self.current_step = None

        for step_index, (step_key, step_class) in enumerate(self.step_classes.items()):
            if step_class.applicable(self):
                self.steps[step_key] = step_class(self, step_index, step_key, initial=dict(self.data))
                if self.current_step is None:
                    self.current_step = self.steps[step_key]
        assert self.current_step is not None

    def step(self, post):
        try:
            state = signing.loads(post.get(u'state', u''))
            current_key = state.get(u'step_key')
            state_data = state.get(u'data')
            assert state.get(u'instance_id') == self.instance_id
            assert current_key in self.step_classes
            assert type(state_data) is dict
        except (AssertionError, signing.BadSignature):
            raise SuspiciousOperation

        self.data = state_data
        self.steps = OrderedDict([(k, None) for k in self.step_classes])
        self.values = {}
        self.current_step = None

        prefixed_data = {self.add_prefix(f): v for f, v in self.data.items()}
        current_index = self.step_classes.keys().index(current_key)
        for step_index, (step_key, step_class) in enumerate(self.step_classes.items()):
            if step_index < current_index:
                if not step_class.applicable(self):
                    continue
                step = step_class(self, step_index, step_key, data=dict(prefixed_data))
                self.steps[step_key] = step
                if not step.is_valid():
                    raise WizzardRollback(step)
                for field_name in step.fields:
                    self.values[field_name] = step.cleaned_data[field_name]
            elif step_index == current_index:
                if not step_class.applicable(self):
                    raise SuspiciousOperation
                step = step_class(self, step_index, step_key, data=post)
                self.steps[step_key] = step
                self.current_step = step
                if not step.is_valid():
                    continue
                for field_name in step.fields:
                    self.values[field_name] = step.cleaned_data[field_name]
            else:
                if not step_class.applicable(self):
                    continue
                step = step_class(self, step_index, step_key, initial=dict(self.data))
                self.steps[step_key] = step
        assert self.current_step is not None

    def commit(self):
        for field_name in self.current_step.fields:
            self.data[field_name] = self.current_step._raw_value(field_name)

        data_update = {self.add_prefix(f): self.data[f] for f in self.current_step.fields}
        initial_update = {f: self.data[f] for f in self.current_step.fields}
        for step in self.steps.values():
            if step is None or step is self.current_step:
                continue
            if step.is_bound:
                step.data.update(data_update)
            else:
                step.initial.update(initial_update)

        draft = WizardDraft(
                id=self.instance_id,
                step=self.current_step.key,
                data=self.data,
                )
        draft.save()

    def add_prefix(self, field_name):
        return u'%s-%s' % (self.instance_id, field_name)

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

    def number_of_steps(self):
        return sum(1 for x in self.steps.values() if x and x.counted_step)

    def step_number(self, step=None):
        if step is None:
            step = self.current_step
        return sum(1 for x in self.steps.values()[:step.index] if x and x.counted_step) + 1

    def state_field(self, step):
        state = {}
        state[u'instance_id'] = self.instance_id
        state[u'step_key'] = step.key
        state[u'data'] = self.data
        return format_html(u'<input type="hidden" name="state" value="{0}" />', signing.dumps(state))

    def context(self, extra=None):
        return dict(extra or {}, wizard=self)


class WizardGroup(object):
    wizard_classes = []

    @classmethod
    def find_applicable(cls, *args, **kwargs):
        for wizard_class in cls.wizard_classes:
            if wizard_class.applicable(*args, **kwargs):
                return wizard_class(*args, **kwargs)
        raise ValueError
