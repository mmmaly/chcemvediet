# vim: expandtab
# -*- coding: utf-8 -*-

from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from models import Obligee


class ObligeeWithAddressInput(forms.TextInput):
    u"""
    TextInput with extra information about the selected Obligee rendered below the inputbox.
    """
    def render(self, name, value, attrs=None):
        obligee = value if isinstance(value, Obligee) else None

        textinput_value = obligee.name if obligee else value
        textinput = super(ObligeeWithAddressInput, self).render(name, textinput_value, attrs)

        return render_to_string(u'inforequests/widgets/obligee_with_address_input.html', {
                u'textinput': textinput,
                u'obligee': obligee,
                })

class ObligeeAutocompleteField(forms.Field):
    u"""
    Form field for Obligee selection with autocomplete functionality. Works with classic
    ``TextInput`` widget and with ``ObligeeWithAddressInput`` widget as well.
    ``ObligeeWithAddressInput`` shows additional information about selected Obligee below the
    inputbox.

    Example;
        class MyForm(forms.Form):
            obligee = ObligeeAutocompleteField(
                    label=_(u'Obligee'),
                    )

        class AnotherForm(forms.Form):
            obligee = ObligeeAutocompleteField(
                    label=_(u'Obligee'),
                    widget=ObligeeWithAddressInput(),
                    )
    """
    def prepare_value(self, value):
        if isinstance(self.widget, ObligeeWithAddressInput):
            # ``ObligeeWithAddressInput`` needs ``Obligee`` as its value, but somehow sometimes the
            # given value is just a string containing an obligee name, not the Obligee itself. It's
            # probably taken directly from POST request and not converted by ``to_python`` method.
            if not isinstance(value, Obligee):
                try:
                    value = self.to_python(value)
                except ValidationError:
                    pass
        else:
            if isinstance(value, Obligee):
                value = value.name
        return value

    def to_python(self, value):
        u""" Returns an Obligee """
        if value in self.empty_values:
            return None
        # FIXME: Should be ``.get(name=value)``, but there are Obligees with duplicate names, yet.
        value = Obligee.objects.pending().filter(name=value).first()
        if value is None:
            raise ValidationError(_(u'Invalid obligee name. Select one form the menu.'))
        return value

    def widget_attrs(self, widget):
        attrs = super(ObligeeAutocompleteField, self).widget_attrs(widget)
        attrs[u'data-autocomplete-url'] = reverse_lazy(u'obligees:autocomplete')
        attrs[u'class'] = u'autocomplete %s' % attrs[u'class'] if u'class' in attrs else u'autocomplete'
        return attrs

