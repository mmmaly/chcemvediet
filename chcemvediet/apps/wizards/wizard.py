# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from django import forms
from django.template import RequestContext
from django.template.loader import render_to_string
from django.shortcuts import render

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

    def context(self, extra=None):
        return dict(self.wizard.context(extra),
                step=self,
                text_template=self.text_template,
                form_template=self.form_template,
                )

    def get_url(self, anchor=u''):
        return self.wizard.get_step_url(self, anchor)

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
        self.draft = None
        self.values = None

    def step(self, request, index=None):
        try:
            self.draft = WizardDraft.objects.get(pk=self.instance_id)
        except WizardDraft.DoesNotExist:
            self.draft = WizardDraft(id=self.instance_id, data={})

        try:
            current_index = int(index)
        except (TypeError, ValueError):
            current_index = -1

        self.steps = OrderedDict([(k, None) for k in self.step_classes])
        self.values = {}
        self.current_step = None

        prefixed_data = {self.add_prefix(f): v for f, v in self.draft.data.items()}
        for step_index, (step_key, step_class) in enumerate(self.step_classes.items()):
            if step_class.applicable(self):
                if step_index < current_index:
                    post = dict(prefixed_data)
                    step = step_class(self, step_index, step_key, data=post)
                    self.steps[step_key] = step
                    if not step.is_valid():
                        raise WizzardRollback(step)
                    for field_name in step.fields:
                        self.values[field_name] = step.cleaned_data[field_name]
                elif step_index == current_index:
                    initial = dict(self.draft.data)
                    post = request.POST if request.method == u'POST' else None
                    step = step_class(self, step_index, step_key, initial=initial, data=post)
                    self.steps[step_key] = step
                    self.current_step = step
                else:
                    initial = dict(self.draft.data)
                    step = step_class(self, step_index, step_key, initial=initial)
                    self.steps[step_key] = step

        if self.current_step is None:
            for step in self.steps.values():
                if step is not None:
                    raise WizzardRollback(step)
            raise ValueError(u'The wizard has no applicable steps')

    def commit(self):
        for field_name in self.current_step.fields:
            self.draft.data[field_name] = self.current_step._raw_value(field_name)
        self.draft.step = self.current_step.key
        self.draft.save()

    def reset(self):
        self.draft.delete()

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

    def get_step_url(self, step, anchor=u''):
        raise NotImplementedError

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
