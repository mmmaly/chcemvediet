# vim: expandtab
# -*- coding: utf-8 -*-
from itertools import chain

from django import forms
from django.forms.util import flatatt
from django.utils.html import format_html

class AutoSuppressedSelect(forms.Select):
    u"""
    Selectbox that replaces itself with a static text if there is only one choice available. Actual
    selection of this only choice is made by a hidden input box. If using with ``ChoiceField``,
    make sure its ``empty_label`` is ``None``, otherwise the empty choice counts. Besides arguments
    supported by ``forms.Select`` the constructor of ``AutoSuppressedSelect`` takes one more
    keyword argument ``suppressed_attrs`` specifying widget's attributes when the selectbox is
    suppressed.

    Example:
        class MyForm(forms.Form)
            book = forms.ModelChoiceField(
                    queryset=Books.objects.all(),
                    empty_label=None,
                    widget=AutoSuppressedSelect(attrs={
                        'class': 'class-for-selectbox',
                        }, suppressed_attrs={
                        'class': 'class-for-plain-text',
                        }),
                    )

        If there are many books, you get:
            <select class="class-for-selectbox" name="...">...</select>
        If there is ony one book, you get:
            <span class="class-for-plain-text"><input type="hidden" name="..." value="...">...</span>
    """
    def __init__(self, *args, **kwargs):
        self.suppressed_attrs = kwargs.pop(u'suppressed_attrs', {})
        super(AutoSuppressedSelect, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, choices=()):
        all_choices = list(chain(self.choices, choices))
        if len(all_choices) == 1:
            option_value, option_label = all_choices[0]
            if not isinstance(option_label, (list, tuple)): # The choice is not a group
                return format_html(u'<span{0}><input type="hidden" name="{1}" value="{2}">{3}</span>',
                        flatatt(self.suppressed_attrs), name, option_value, option_label)
        return super(AutoSuppressedSelect, self).render(name, value, attrs, choices)

