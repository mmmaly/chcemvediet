# vim: expandtab
# -*- coding: utf-8 -*-
import lxml.html
from django import forms
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from poleno.utils.urls import reverse
from chcemvediet.tests import ChcemvedietTestCaseMixin

from ..forms import ObligeeWidget, ObligeeField


class ObligeeFieldTest(ChcemvedietTestCaseMixin, TestCase):
    u"""
    Tests ``ObligeeField`` field with ``ObligeeWidget`` widget.
    """

    class Form(forms.Form):
        obligee = ObligeeField()

    class FormWithWidgetAttrs(forms.Form):
        obligee = ObligeeField(
                widget=ObligeeWidget(attrs={
                    u'class': u'custom-class',
                    u'custom-attribute': u'value',
                    }),
                )

    class FormWithInputAttrs(forms.Form):
        obligee = ObligeeField(
                widget=ObligeeWidget(input_attrs={
                    u'class': u'custom-class',
                    u'custom-attribute': u'value',
                    }),
                )


    def test_new_form(self):
        form = self.Form()
        rendered = self._render(u'{{ form }}', form=form)
        html = lxml.html.fromstring(rendered)

        label = html.find(u'.//label[@for="id_obligee"]')
        self.assertEqual(label.text, u'Obligee:')

        widget = html.find(u'.//div[@id="id_obligee"]')
        self.assertIn(u'chv-obligee-widget', widget.attrib[u'class'].split())

        input = widget.find(u'.//input')
        self.assertIn(u'form-control', input.attrib[u'class'].split())
        self.assertIn(u'pln-autocomplete', input.attrib[u'class'].split())
        self.assertEqual(input.attrib[u'type'], u'text')
        self.assertEqual(input.attrib[u'name'], u'obligee')
        self.assertEqual(input.attrib[u'value'], u'')
        self.assertEqual(input.attrib[u'data-autocomplete-url'], reverse(u'obligees:autocomplete'))
        self.assertEqual(input.attrib[u'data-name'], u'obligee')

        details = widget.find_class(u'chv-obligee-widget-details')[0]
        self.assertEqual(details.tag, u'div')
        self.assertIn(u'chv-obligee-widget-hide', details.attrib[u'class'].split())

    def test_new_form_with_custom_widget_class_and_attributes(self):
        form = self.FormWithWidgetAttrs()
        rendered = self._render(u'{{ form }}', form=form)
        html = lxml.html.fromstring(rendered)

        widget = html.find(u'.//div[@id="id_obligee"]')
        self.assertIn(u'chv-obligee-widget', widget.attrib[u'class'].split())
        self.assertIn(u'custom-class', widget.attrib[u'class'].split())
        self.assertEqual(widget.attrib[u'custom-attribute'], u'value')

    def test_new_form_with_custom_input_class_and_attributes(self):
        form = self.FormWithInputAttrs()
        rendered = self._render(u'{{ form }}', form=form)
        html = lxml.html.fromstring(rendered)

        widget = html.find(u'.//div[@id="id_obligee"]')
        input = widget.find(u'.//input')
        self.assertIn(u'custom-class', input.attrib[u'class'].split())
        self.assertEqual(input.attrib[u'custom-attribute'], u'value')

    def test_new_form_with_initial_value_as_obligee_instance(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n, street=u'{} street'.format(n), city=u'{} city'.format(n), zip=u'12345', emails=u'{}@a.com'.format(n)) for n in names]

        form = self.Form(initial={u'obligee': oblgs[2]})
        rendered = self._render(u'{{ form }}', form=form)
        html = lxml.html.fromstring(rendered)

        widget = html.find(u'.//div[@id="id_obligee"]')
        input = widget.find(u'.//input')
        self.assertEqual(input.attrib[u'value'], u'ccc')

        details = widget.find_class(u'chv-obligee-widget-details')[0]
        self.assertNotIn(u'chv-obligee-widget-hide', details.attrib[u'class'].split())

        street = details.find(u'span[@class="chv-obligee-widget-street"]')
        self.assertEqual(street.text, u'ccc street')
        zip = details.find(u'span[@class="chv-obligee-widget-zip"]')
        self.assertEqual(zip.text, u'12345')
        city = details.find(u'span[@class="chv-obligee-widget-city"]')
        self.assertEqual(city.text, u'ccc city')
        email = details.find(u'span[@class="chv-obligee-widget-email"]')
        self.assertEqual(email.text, u'ccc@a.com')

    def test_new_form_with_initial_value_as_obligee_name(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n, street=u'{} street'.format(n), city=u'{} city'.format(n), zip=u'12345', emails=u'{}@a.com'.format(n)) for n in names]

        form = self.Form(initial={u'obligee': u'ccc'})
        rendered = self._render(u'{{ form }}', form=form)
        html = lxml.html.fromstring(rendered)

        widget = html.find(u'.//div[@id="id_obligee"]')
        input = widget.find(u'.//input')
        self.assertEqual(input.attrib[u'value'], u'ccc')

        details = widget.find_class(u'chv-obligee-widget-details')[0]
        self.assertNotIn(u'chv-obligee-widget-hide', details.attrib[u'class'].split())

        street = details.find(u'span[@class="chv-obligee-widget-street"]')
        self.assertEqual(street.text, u'ccc street')
        zip = details.find(u'span[@class="chv-obligee-widget-zip"]')
        self.assertEqual(zip.text, u'12345')
        city = details.find(u'span[@class="chv-obligee-widget-city"]')
        self.assertEqual(city.text, u'ccc city')
        email = details.find(u'span[@class="chv-obligee-widget-email"]')
        self.assertEqual(email.text, u'ccc@a.com')

    def test_submitted_with_empty_value_but_required(self):
        form = self.Form({u'obligee': u''})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors[u'obligee'], [u'This field is required.'])

        rendered = self._render(u'{{ form }}', form=form)
        html = lxml.html.fromstring(rendered)

        error = html.find(u'.//ul[@class="errorlist"]/li')
        self.assertEqual(error.text, u'This field is required.')

    def test_submitted_with_empty_value_but_not_required(self):
        form = self.Form({u'obligee': u''})
        form.fields[u'obligee'].required = False
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data[u'obligee'])

        rendered = self._render(u'{{ form }}', form=form)
        html = lxml.html.fromstring(rendered)

        errorlist = html.find(u'.//ul[@class="errorlist"]')
        self.assertIsNone(errorlist)

    def test_submitted_with_valid_obligee_name(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n, street=u'{} street'.format(n), city=u'{} city'.format(n), zip=u'12345', emails=u'{}@a.com'.format(n)) for n in names]

        form = self.Form({u'obligee': u'bbb'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data[u'obligee'], oblgs[1])

        rendered = self._render(u'{{ form }}', form=form)
        html = lxml.html.fromstring(rendered)

        widget = html.find(u'.//div[@id="id_obligee"]')
        input = widget.find(u'.//input')
        self.assertEqual(input.attrib[u'value'], u'bbb')

        details = widget.find_class(u'chv-obligee-widget-details')[0]
        self.assertNotIn(u'chv-obligee-widget-hide', details.attrib[u'class'].split())

        street = details.find(u'span[@class="chv-obligee-widget-street"]')
        self.assertEqual(street.text, u'bbb street')
        zip = details.find(u'span[@class="chv-obligee-widget-zip"]')
        self.assertEqual(zip.text, u'12345')
        city = details.find(u'span[@class="chv-obligee-widget-city"]')
        self.assertEqual(city.text, u'bbb city')
        email = details.find(u'span[@class="chv-obligee-widget-email"]')
        self.assertEqual(email.text, u'bbb@a.com')

    def test_submitted_with_nonexisting_obligee_name(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n) for n in names]

        form = self.Form({u'obligee': u'invalid'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors[u'obligee'], [_(u'obligees:ObligeeField:error:invalid_obligee')])

        rendered = self._render(u'{{ form }}', form=form)
        html = lxml.html.fromstring(rendered)

        error = html.find(u'.//ul[@class="errorlist"]/li')
        self.assertEqual(error.text, _(u'obligees:ObligeeField:error:invalid_obligee'))

        widget = html.find(u'.//div[@id="id_obligee"]')
        input = widget.find(u'.//input')
        self.assertEqual(input.attrib[u'value'], u'invalid')

        details = widget.find_class(u'chv-obligee-widget-details')[0]
        self.assertIn(u'chv-obligee-widget-hide', details.attrib[u'class'].split())

    def test_to_python_is_cached(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n) for n in names]
        field = ObligeeField()

        # Valid value
        with self.assertNumQueries(1):
            self.assertEqual(field.clean(u'bbb'), oblgs[1])
        with self.assertNumQueries(0):
            self.assertEqual(field.clean(u'bbb'), oblgs[1])

        # Invalid value
        with self.assertNumQueries(1):
            with self.assertRaises(ValidationError):
                field.clean(u'invalid')
        with self.assertNumQueries(0):
            with self.assertRaises(ValidationError):
                field.clean(u'invalid')
