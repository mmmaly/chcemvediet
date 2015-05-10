# vim: expandtab
# -*- coding: utf-8 -*-
from itertools import chain
from email.utils import formataddr, parseaddr, getaddresses

from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.forms.util import flatatt
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.html import format_html

from poleno.utils.html import merge_html_attrs

def clean_button(post, clean_values, default_value=None, key=u'button'):
    u"""
    Djago forms do not care about buttons. To distinguish which submit button was pressed, we need
    to give them names and values. This function filters ``request.POST`` values set by submit
    buttons for allowed values. Default button name is "button".

    Example:
        <button type="submit" name="button" value="email">...</button>
        <button type="submit" name="button" value="print">...</button>

        button = clean_button(request.POST, ['email', 'print'], default_value='email')
    """
    if key not in post:
        return default_value
    if post[key] not in clean_values:
        return default_value
    return post[key]

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

class CompositeTextWidget(forms.MultiWidget):
    u"""
    See ``CompositeTextField``.
    """
    def __init__(self, *args, **kwargs):
        self.template = kwargs.pop(u'template')
        self.composite_attrs = kwargs.pop(u'composite_attrs', {})
        self.context = kwargs.pop(u'context', {})
        super(CompositeTextWidget, self).__init__(*args, **kwargs)

    def format_output(self, rendered_widgets):
        context = dict(self.context, inputs=rendered_widgets, finalize=False)
        content = mark_safe(render_to_string(self.template, context).strip())
        attrs = merge_html_attrs(self.composite_attrs, class_=u'composite-text')
        return format_html(u'<div{0}>{1}</div>', flatatt(attrs), content)

    def decompress(self, value):
        assert value is None
        return [None for w in self.widgets]

class CompositeTextField(forms.MultiValueField):
    u"""
    Form field for structured fields with multiple inputs/textareas and static text. Field
    structure is defined with a template. Uses ``CompositeTextWidget``.

    Example:
        class InforequestForm(PrefixedForm):
            address = CompositeTextField(
                    label='Address',
                    template='address.txt',
                    fields=[
                        forms.CharField(widget=forms.TextInput(attrs={
                            'placeholder': 'Street',
                            })),
                        forms.CharField(widget=forms.TextInput(attrs={
                            'placeholder': 'City',
                            })),
                        forms.CharField(widget=forms.Textarea(attrs={
                            'placeholder': 'Description how to get there',
                            'class': u'autosize',
                            })),
                        ],
                    composite_attrs={
                        'class': u'input-block-level',
                        },
                    )
    """

    def __init__(self, *args, **kwargs):
        kwargs[u'widget'] = CompositeTextWidget(
                template=kwargs.pop(u'template'),
                composite_attrs=kwargs.pop(u'composite_attrs', {}),
                context=kwargs.pop(u'context', {}),
                widgets=[f.widget for f in kwargs.get(u'fields')],
                )
        super(CompositeTextField, self).__init__(*args, **kwargs)

    def compress(self, data_list):
        return data_list

    def finalize(self, cleaned_data, context={}):
        context = dict(self.widget.context, inputs=cleaned_data, finalize=True, **context)
        return render_to_string(self.widget.template, context).strip()

class PrefixedForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(PrefixedForm, self).__init__(*args, **kwargs)
        self.prefix = u'%s%s%s' % (self.prefix or u'', u'-' if self.prefix else u'', self.__class__.__name__.lower())

class ValidatorChain(object):
    u"""
    By default every form field runs all its validators, even if some of them fail. Therefore it is
    not possible to chain the validators and assume the value already passed any previous
    validation.

    ``ValidatorChain`` runs given validators in a sequencial order and stops validating after the
    first validator raises an exception. Any further validators are run only if all previous
    validators were successfull.
    """

    def __init__(self, *args):
        self.validators = args

    def __call__(self, value):
        for validator in self.validators:
            validator(value)

def validate_formatted_email(value):
    name, address = parseaddr(value)
    try:
        validate_email(address)
    except ValidationError:
        raise ValidationError(_(u'utils:validate_formatted_email:invalid_error {0}').format(address))

    #formatted = formataddr((name, address))
    #if formatted != value:
    #    raise ValidationError(_(u'utils:validate_formatted_email:parse_error {0}').format(formatted))

def validate_comma_separated_emails(value):
    parsed = getaddresses([value])
    for name, address in parsed:
        try:
            validate_email(address)
        except ValidationError:
            raise ValidationError(_(u'utils:validate_comma_separated_emails:invalid_error {0}').format(address))

    #formatted = u', '.join(formataddr((n, a)) for n, a in parsed)
    #if formatted != value:
    #    raise ValidationError(_(u'utils:validate_comma_separated_emails:parse_error {0}').format(formatted))
