# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.utils.html import format_html
from django.utils.dateformat import format

class PaperField(forms.Field):

    def __init__(self, *args, **kwargs):
        super(PaperField, self).__init__(*args, **kwargs)

    def render_finalized(self, value):
        return format_html(u'{0}', value)

class PaperDateField(PaperField, forms.DateField):

    def __init__(self, *args, **kwargs):
        self.final_format = kwargs.pop(u'final_format', settings.DATE_FORMAT)
        super(PaperDateField, self).__init__(*args, **kwargs)

    def render_finalized(self, value):
        if value in [None, u'']:
            return u''
        return format_html(u'{0}', format(value, self.final_format))

class PaperCharField(PaperField, forms.CharField):

    def render_finalized(self, value):
        if value is None:
            value = u''
        return format_html(u'<span style="white-space: pre-wrap;">{0}</span>', value)

class OptionalSectionCheckboxField(forms.BooleanField):

    def __init__(self, *args, **kwargs):
        kwargs[u'widget'] = forms.CheckboxInput(attrs={
                u'class': u'toggle-changed',
                u'data-container': u'form',
                u'data-target-true': u'button[value="next"], .paper-section'
                    if kwargs.get(u'required', True) else u'.paper-section',
                })
        super(OptionalSectionCheckboxField, self).__init__(*args, **kwargs)
