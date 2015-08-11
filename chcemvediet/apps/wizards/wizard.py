# vim: expandtab
# -*- coding: utf-8 -*-
from collections import OrderedDict

from django import forms
from django.template import RequestContext
from django.template.loader import render_to_string
from django.shortcuts import render

from poleno.utils.misc import squeeze

from .models import WizardDraft


class WizzardRollback(Exception):
    def __init__(self, step):
        self.step = step


class WizardStep(forms.Form):
    base_template = u'wizards/wizard.html'
    template = None
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

    def commit(self):
        for field_name in self.fields:
            self.wizard.draft.data[field_name] = self._raw_value(field_name)

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
        return dict(self.wizard.context(extra), step=self)

    def values(self):
        return {f: self.cleaned_data[f] for f in self.fields}

    def get_url(self, anchor=u''):
        return self.wizard.get_step_url(self, anchor)

    def render(self):
        return render(self.wizard.request, self.template or self.base_template, self.context())

    def render_to_string(self):
        return render_to_string(self.template or self.base_template,
                context_instance=RequestContext(self.wizard.request), dictionary=self.context())

class WizardDeadendStep(WizardStep):
    base_template = u'wizards/deadend.html'
    counted_step = False

    def clean(self):
        cleaned_data = super(WizardDeadendStep, self).clean()
        self.add_error(None, u'deadend')
        return cleaned_data

class WizardSectionStep(WizardStep):
    base_template = u'wizards/section.html'
    section_template = None

    def paper_fields(self, step):
        pass

    def paper_context(self, extra=None):
        return dict(extra or {})

    def section_is_empty(self):
        return False

class WizardPaperStep(WizardStep):
    base_template = u'wizards/paper.html'
    subject_template = None
    content_template = None
    subject_value_name = u'subject'
    content_value_name = u'content'

    def __init__(self, *args, **kwargs):
        super(WizardPaperStep, self).__init__(*args, **kwargs)
        for step in self.wizard.steps.values():
            if isinstance(step, WizardSectionStep):
                step.paper_fields(self)

    def context(self, extra=None):
        res = super(WizardPaperStep, self).context(extra)
        for step in self.wizard.steps.values():
            if isinstance(step, WizardSectionStep):
                res.update(step.paper_context())
        return res

    def values(self):
        res = super(WizardPaperStep, self).values()

        subject = squeeze(render_to_string(self.subject_template, self.context(dict(finalize=True))))
        content = render_to_string(self.content_template, self.context(dict(finalize=True)))
        res.update({
                self.subject_value_name: subject,
                self.content_value_name: content,
                })

        return res

class WizardPrintStep(WizardStep):
    base_template = u'wizards/print.html'
    print_value_name = u'content'

    def print_content(self):
        return self.wizard.values[self.print_value_name]


class Wizard(object):
    step_classes = None

    @classmethod
    def applicable(cls):
        raise NotImplementedError

    def __init__(self, request):
        self.request = request
        self.instance_id = None
        self.current_step = None
        self.steps = None
        self.draft = None
        self.values = None

    def step(self, index=None):
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
                    self.values.update(step.values())
                elif step_index == current_index:
                    initial = dict(self.draft.data)
                    post = self.request.POST if self.request.method == u'POST' else None
                    step = step_class(self, step_index, step_key, initial=initial, data=post)
                    self.steps[step_key] = step
                    self.current_step = step
                    if not step.is_valid():
                        continue
                    self.values.update(step.values())
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
        self.current_step.commit()
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
    def find_applicable(cls, request, *args, **kwargs):
        for wizard_class in cls.wizard_classes:
            if wizard_class.applicable(*args, **kwargs):
                return wizard_class(request, *args, **kwargs)
        raise ValueError
