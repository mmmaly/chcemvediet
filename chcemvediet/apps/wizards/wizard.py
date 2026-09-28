# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.template import RequestContext
from django.shortcuts import render

from poleno.utils.template import render_to_string
from poleno.utils.misc import squeeze

from .models import WizardDraft


class WizzardRollback(Exception):
    def __init__(self, step):
        self.step = step

class Bottom(object):
    pass

class Transition(object):
    def __init__(self):
        self.values = {}
        self.globals = {}
        self.next = None

class Step(forms.Form):
    label = u''
    base_template = u'wizards/wizard.html'
    template = None
    text_template = None
    form_template = None
    global_fields = []
    pre_step_class = None
    post_step_class = Bottom

    def __init__(self, wizard, index, accessible, *args, **kwargs):
        super(Step, self).__init__(*args, **kwargs)
        self.wizard = wizard
        self.index = index
        self.key = self.__class__.__name__
        self.accessible = accessible
        self.values = None

        # Make sure there are no step name conflicts
        assert self.key != u'global'
        assert self.key not in [s.key for s in wizard.steps]

    def commit(self):
        global_fields = self.get_global_fields()
        step_values = self.wizard.draft.data.setdefault(self.key, {})
        global_values = self.wizard.draft.data.setdefault(u'global', {})
        for field_name in self.fields:
            # ``Form._raw_value()`` was removed in Django 1.9; ``BoundField.data`` returns the same
            # raw widget value.
            if field_name in global_fields:
                global_values[field_name] = self[field_name].data
            else:
                step_values[field_name] = self[field_name].data

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

    def add_fields(self):
        pass

    def get_global_fields(self):
        return self.global_fields

    def context(self, extra=None):
        return dict(self.wizard.context(extra), step=self)

    def get_url(self, anchor=u''):
        return self.wizard.get_step_url(self, anchor)

    def render(self):
        return render(self.wizard.request, self.template or self.base_template, self.context())

    def render_to_string(self):
        return render_to_string(self.template or self.base_template, self.context())

    def pre_transition(self):
        res = Transition()
        res.next = self.pre_step_class
        return res

    def post_transition(self):
        res = Transition()
        if self.is_valid():
            global_fields = self.get_global_fields()
            for field_name in self.fields:
                if field_name in global_fields:
                    res.globals[field_name] = self.cleaned_data[field_name]
                else:
                    res.values[field_name] = self.cleaned_data[field_name]
        res.next = self.post_step_class
        return res

class SectionStep(Step):
    base_template = u'wizards/section.html'
    section_template = None

    def section_is_empty(self):
        return False

class DeadendStep(Step):
    base_template = u'wizards/deadend.html'

    def clean(self):
        cleaned_data = super(DeadendStep, self).clean()
        self.add_error(None, u'deadend')
        return cleaned_data

class PaperStep(Step):
    subject_template = None
    content_template = None
    subject_value_name = u'subject'
    content_value_name = u'content'

    def pre_transition(self):
        res = super(PaperStep, self).pre_transition()

        if self.accessible:
            context = self.context(dict(finalize=True))
            subject = squeeze(render_to_string(self.subject_template, context))
            content = render_to_string(self.content_template, context)
            res.globals[self.subject_value_name] = subject
            res.globals[self.content_value_name] = content

        return res

class PrintStep(Step):
    base_template = u'wizards/print.html'
    print_value_name = u'content'

    def print_content(self):
        return self.wizard.values[self.print_value_name]

class Wizard(object):
    first_step_class = None

    def _step_data(self, step, prefixed=False):
        res = {}
        step_values = self.draft.data.get(step.key, {})
        global_values = self.draft.data.get(u'global', {})
        for field, value in step_values.items():
            res[field] = value
        for field in step.get_global_fields():
            if field in global_values:
                res[field] = global_values[field]
        if prefixed:
            res = {self.add_prefix(f): v for f, v in res.items()}
        return res

    def __init__(self, request, index=None):
        self.request = request
        self.steps = []
        self.values = {}
        self.instance_id = self.get_instance_id()

        try:
            self.draft = WizardDraft.objects.owned_by(request.user).get(pk=self.instance_id)
        except WizardDraft.DoesNotExist:
            self.draft = WizardDraft(id=self.instance_id, owner=request.user, data={})

        try:
            current_index = int(index)
        except (TypeError, ValueError):
            current_index = -1

        accessible = True
        step_class = self.first_step_class
        while step_class and step_class is not Bottom:
            step = step_class(self, len(self.steps), accessible)

            transition = step.pre_transition()
            step.values = dict(transition.values if accessible else {})
            self.values.update(transition.globals if accessible else {})
            step_class = transition.next
            if step_class:
                continue

            if accessible:
                step.add_fields()
                step.initial = self._step_data(step)
                if len(self.steps) == current_index and request.method == u'POST':
                    step.data = request.POST
                    step.is_bound = True
                else:
                    step.data = self._step_data(step, prefixed=True)
                    step.is_bound = step.key in self.draft.data
                if not step.is_valid():
                    accessible = False
            self.steps.append(step)

            transition = step.post_transition()
            step.values.update(transition.values if accessible else {})
            self.values.update(transition.globals if accessible else {})
            step_class = transition.next

        assert len(self.steps) > 0
        current_index = max(0, min(current_index, len(self.steps)-1))
        while current_index > 0 and not self.steps[current_index].accessible:
            current_index -= 1
        if format(current_index) != index:
            raise WizzardRollback(self.steps[current_index])
        self.current_step = self.steps[current_index]

    def add_prefix(self, field_name):
        return u'{}-{}'.format(self.instance_id, field_name)

    def commit(self):
        self.current_step.commit()
        self.draft.step = self.current_step.key
        self.draft.save()

    def reset(self):
        self.draft.delete()

    def next_step(self, step=None):
        if step is None:
            step = self.current_step
        if step.index+1 < len(self.steps):
            return self.steps[step.index+1]
        else:
            return None

    def prev_step(self, step=None):
        if step is None:
            step = self.current_step
        if step.index > 0:
            return self.steps[step.index-1]
        else:
            return None

    def is_last_step(self, step=None):
        return self.next_step(step) is None

    def is_first_step(self, step=None):
        return self.prev_step(step) is None

    def get_instance_id(self):
        raise NotImplementedError

    def get_step_url(self, step, anchor=u''):
        raise NotImplementedError

    def context(self, extra=None):
        return dict(extra or {}, wizard=self)

    def finish(self):
        raise NotImplementedError
