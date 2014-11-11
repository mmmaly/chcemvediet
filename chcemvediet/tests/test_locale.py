# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.test import TestCase

from poleno.utils.date import local_datetime_from_local, naive_date
from poleno.utils.translation import translation

class LocaleEnTest(TestCase):
    u"""
    Tests ``settings.DATE_INPUT_FORMATS`` and ``settings.DATETIME_INPUT_FORMATS`` for "en" locale.
    """

    def test_date_input_formats(self):
        with translation(u'en'):
            self.assertFieldOutput(forms.DateField,
                    valid={
                        u'10/25/2006': naive_date(u'2006-10-25'),
                        u'10/25/06': naive_date(u'2006-10-25'),
                        u'2006-10-25': naive_date(u'2006-10-25'),
                        },
                    invalid={
                        u'25/10/2006': [u'Enter a valid date.'],
                        u'25/10/06':   [u'Enter a valid date.'],
                        u'25.10.2006': [u'Enter a valid date.'],
                        u'25.10.06':   [u'Enter a valid date.'],
                        u'10.25.2006': [u'Enter a valid date.'],
                        u'10.25.06':   [u'Enter a valid date.'],
                        u'2006-25-10': [u'Enter a valid date.'],
                        },
                    field_kwargs=dict(localize=True),
                    empty_value=None,
                    )

    def test_datetime_input_formats(self):
        with translation(u'en'):
            self.assertFieldOutput(forms.DateTimeField,
                    valid={
                        u'10/25/2006 14:30:59':        local_datetime_from_local(u'2006-10-25 14:30:59'),
                        u'10/25/2006 14:30:59.000200': local_datetime_from_local(u'2006-10-25 14:30:59.000200'),
                        u'10/25/2006 14:30':           local_datetime_from_local(u'2006-10-25 14:30:00'),
                        u'10/25/2006':                 local_datetime_from_local(u'2006-10-25 00:00:00'),
                        u'10/25/06 14:30:59':          local_datetime_from_local(u'2006-10-25 14:30:59'),
                        u'10/25/06 14:30:59.000200':   local_datetime_from_local(u'2006-10-25 14:30:59.000200'),
                        u'10/25/06 14:30':             local_datetime_from_local(u'2006-10-25 14:30:00'),
                        u'10/25/06':                   local_datetime_from_local(u'2006-10-25 00:00:00'),
                        u'2006-10-25 14:30:59':        local_datetime_from_local(u'2006-10-25 14:30:59'),
                        u'2006-10-25 14:30:59.000200': local_datetime_from_local(u'2006-10-25 14:30:59.000200'),
                        u'2006-10-25 14:30':           local_datetime_from_local(u'2006-10-25 14:30:00'),
                        u'2006-10-25':                 local_datetime_from_local(u'2006-10-25 00:00:00'),
                        },
                    invalid={
                        u'25/10/2006 14:30': [u'Enter a valid date/time.'],
                        u'25/10/06 14:30':   [u'Enter a valid date/time.'],
                        u'25.10.2006 14:30': [u'Enter a valid date/time.'],
                        u'25.10.06 14:30':   [u'Enter a valid date/time.'],
                        u'10.25.2006 14:30': [u'Enter a valid date/time.'],
                        u'10.25.06 14:30':   [u'Enter a valid date/time.'],
                        u'2006-25-10 14:30': [u'Enter a valid date/time.'],
                        u'10/25/2006 14':    [u'Enter a valid date/time.'],
                        },
                    field_kwargs=dict(localize=True),
                    empty_value=None,
                    )

    def test_date_output_format(self):
        with translation(u'en'):
            class Form(forms.Form):
                field = forms.DateField(localize=True)

            form = Form(initial=dict(field=naive_date(u'2006-10-25')))
            self.assertHTMLEqual(str(form[u'field']), u'<input id="id_field" name="field" type="text" value="10/25/2006">')

    def test_datetime_output_format(self):
        with translation(u'en'):
            class Form(forms.Form):
                field = forms.DateTimeField(localize=True)

            form = Form(initial=dict(field=local_datetime_from_local(u'2006-10-25 14:30:59.000200')))
            self.assertHTMLEqual(str(form[u'field']), u'<input id="id_field" name="field" type="text" value="10/25/2006 14:30:59">')

            form = Form(initial=dict(field=local_datetime_from_local(u'2006-10-25')))
            self.assertHTMLEqual(str(form[u'field']), u'<input id="id_field" name="field" type="text" value="10/25/2006 00:00:00">')

class LocaleSkTest(TestCase):
    u"""
    Tests ``settings.DATE_INPUT_FORMATS`` and ``settings.DATETIME_INPUT_FORMATS`` for "sk" locale.
    """

    def test_date_input_formats(self):
        with translation(u'sk'):
            self.assertFieldOutput(forms.DateField,
                    valid={
                        u'25.10.2006': naive_date(u'2006-10-25'),
                        u'25.10.06': naive_date(u'2006-10-25'),
                        u'2006-10-25': naive_date(u'2006-10-25'),
                        },
                    invalid={
                        u'10.25.2006': [u'Zadajte platný dátum.'],
                        u'10.25.06':   [u'Zadajte platný dátum.'],
                        u'10/25/2006': [u'Zadajte platný dátum.'],
                        u'10/25/06':   [u'Zadajte platný dátum.'],
                        u'25/10/2006': [u'Zadajte platný dátum.'],
                        u'25/10/06':   [u'Zadajte platný dátum.'],
                        u'2006-25-10': [u'Zadajte platný dátum.'],
                        },
                    field_kwargs=dict(localize=True),
                    empty_value=None,
                    )

    def test_datetime_input_formats(self):
        with translation(u'sk'):
            self.assertFieldOutput(forms.DateTimeField,
                    valid={
                        u'25.10.2006 14:30:59':        local_datetime_from_local(u'2006-10-25 14:30:59'),
                        u'25.10.2006 14:30:59.000200': local_datetime_from_local(u'2006-10-25 14:30:59.000200'),
                        u'25.10.2006 14:30':           local_datetime_from_local(u'2006-10-25 14:30:00'),
                        u'25.10.2006':                 local_datetime_from_local(u'2006-10-25 00:00:00'),
                        u'25.10.06 14:30:59':          local_datetime_from_local(u'2006-10-25 14:30:59'),
                        u'25.10.06 14:30:59.000200':   local_datetime_from_local(u'2006-10-25 14:30:59.000200'),
                        u'25.10.06 14:30':             local_datetime_from_local(u'2006-10-25 14:30:00'),
                        u'25.10.06':                   local_datetime_from_local(u'2006-10-25 00:00:00'),
                        u'2006-10-25 14:30:59':        local_datetime_from_local(u'2006-10-25 14:30:59'),
                        u'2006-10-25 14:30:59.000200': local_datetime_from_local(u'2006-10-25 14:30:59.000200'),
                        u'2006-10-25 14:30':           local_datetime_from_local(u'2006-10-25 14:30:00'),
                        u'2006-10-25':                 local_datetime_from_local(u'2006-10-25 00:00:00'),
                        },
                    invalid={
                        u'10.25.2006 14:30': [u'Zadajte platný dátum a čas.'],
                        u'10.25.06 14:30':   [u'Zadajte platný dátum a čas.'],
                        u'10/25/2006 14:30': [u'Zadajte platný dátum a čas.'],
                        u'10/25/06 14:30':   [u'Zadajte platný dátum a čas.'],
                        u'25/10/2006 14:30': [u'Zadajte platný dátum a čas.'],
                        u'25/10/06 14:30':   [u'Zadajte platný dátum a čas.'],
                        u'2006-25-10 14:30': [u'Zadajte platný dátum a čas.'],
                        u'25.10.2006 14':    [u'Zadajte platný dátum a čas.'],
                        },
                    field_kwargs=dict(localize=True),
                    empty_value=None,
                    )

    def test_date_output_format(self):
        with translation(u'sk'):
            class Form(forms.Form):
                field = forms.DateField(localize=True)

            form = Form(initial=dict(field=naive_date(u'2006-10-25')))
            self.assertHTMLEqual(str(form[u'field']), u'<input id="id_field" name="field" type="text" value="25.10.2006">')

    def test_datetime_output_format(self):
        with translation(u'sk'):
            class Form(forms.Form):
                field = forms.DateTimeField(localize=True)

            form = Form(initial=dict(field=local_datetime_from_local(u'2006-10-25 14:30:59.000200')))
            self.assertHTMLEqual(str(form[u'field']), u'<input id="id_field" name="field" type="text" value="25.10.2006 14:30:59">')

            form = Form(initial=dict(field=local_datetime_from_local(u'2006-10-25')))
            self.assertHTMLEqual(str(form[u'field']), u'<input id="id_field" name="field" type="text" value="25.10.2006 00:00:00">')
