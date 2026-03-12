# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from django.utils.datastructures import MultiValueDict

from poleno.utils.html import merge_html_attrs
from poleno.utils.template import render_to_string
from poleno.utils.misc import cached_method

from .models import Obligee


class ObligeeWidget(forms.Widget):

    def __init__(self, *args, **kwargs):
        self.input_attrs = kwargs.pop(u'input_attrs', {})
        super(ObligeeWidget, self).__init__(*args, **kwargs)

    def _widget_attrs(self, attrs=None):
        return merge_html_attrs(self.attrs, attrs, {
                u'class': u'chv-obligee-widget',
                })

    def _input_attrs(self, name, value, skel=False):
        obligee = value if isinstance(value, Obligee) else None
        value = force_text(obligee.name if obligee else u'' if value is None else value)
        return merge_html_attrs(self.input_attrs, {
                u'class': u'pln-autocomplete form-control',
                u'type': u'text',
                u'name': name if not skel else u'',
                u'value': value,
                u'data-autocomplete-url': reverse_lazy(u'obligees:autocomplete'),
                u'data-name': name,
                })

    def render(self, name, value, attrs=None):
        obligee = value if isinstance(value, Obligee) else None
        return render_to_string(u'obligees/widgets/obligee_widget.html', {
                u'widget_attrs': self._widget_attrs(attrs),
                u'input_attrs': self._input_attrs(name, value),
                u'obligee': obligee,
                })

class MultipleObligeeWidget(ObligeeWidget):

    def render(self, name, value, attrs=None):
        inputs = []
        for item in value or [None]:
            obligee = item if isinstance(item, Obligee) else None
            input_attrs = self._input_attrs(name, item)
            inputs.append((input_attrs, obligee))
        return render_to_string(u'obligees/widgets/multiple_obligee_widget.html', {
                u'widget_attrs': self._widget_attrs(attrs),
                u'skel_attrs': self._input_attrs(name, None, skel=True),
                u'inputs': inputs,
                })

    def value_from_datadict(self, data, files, name):
        if isinstance(data, MultiValueDict):
            return data.getlist(name)
        return data.get(name, None)

class ObligeeField(forms.Field):
    widget = ObligeeWidget

    def __init__(self, *args, **kwargs):
        self.email_required = kwargs.pop(u'email_required', True)
        super(ObligeeField, self).__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, Obligee):
            return value
        try:
            return self.coerce(value)
        except ValidationError:
            return value

    def to_python(self, value):
        u""" Returns an Obligee """
        return self.coerce(value)

    @cached_method(cached_exceptions=ValidationError)
    def coerce(self, value):
        u""" Returns an Obligee """
        if value in self.empty_values:
            return None
        # FIXME: Should be ``.get(name=value)``, but there are Obligees with duplicate names, yet.
        value = Obligee.objects.pending().filter(name=value).order_by_pk().first()
        if value is None:
            raise ValidationError(_(u'obligees:ObligeeField:error:invalid_obligee'))
        if self.email_required and not value.emails_parsed:
            raise ValidationError(_(u'obligees:ObligeeField:error:no_email'))
        return value

class MultipleObligeeField(ObligeeField):
    widget = MultipleObligeeWidget

    def prepare_value(self, value):
        if not isinstance(value, (list, tuple)):
            value = [value]
        return [super(MultipleObligeeField, self).prepare_value(v) for v in value]

    def to_python(self, value):
        u""" Returns a list of Obligees """
        if not value:
            return []
        if not isinstance(value, (list, tuple)):
            raise ValidationError(_(u'obligees:ObligeeField:error:invalid_list'))
        return [self.coerce(v) for v in value if self.coerce(v)]
