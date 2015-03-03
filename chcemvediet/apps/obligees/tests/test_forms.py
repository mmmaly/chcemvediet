# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.test import TestCase

from . import ObligeesTestCaseMixin
from ..forms import ObligeeWithAddressInput, ObligeeAutocompleteField

class ObligeeAutocompleteFieldWithTextInputWidgetTest(ObligeesTestCaseMixin, TestCase):
    u"""
    Tests ``ObligeeAutocompleteField`` with ``TextInput`` widget.
    """

    class Form(forms.Form):
        obligee = ObligeeAutocompleteField()

    class FormWithWidgetAttrs(forms.Form):
        obligee = ObligeeAutocompleteField(
                widget=forms.TextInput(attrs={
                    u'class': u'custom-class',
                    u'custom-attribute': u'value',
                    }),
                )


    def test_new_form(self):
        form = self.Form()
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<label for="id_obligee">Obligee:</label>', rendered)
        self.assertInHTML(u"""
                <input class="autocomplete" data-autocomplete-url="{url}" id="id_obligee" name="obligee" type="text">
                """.format(url=reverse(u'obligees:autocomplete')), rendered)

    def test_new_form_with_custom_widget_class_attributes(self):
        form = self.FormWithWidgetAttrs()
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u"""
                <input class="custom-class autocomplete" data-autocomplete-url="{url}" id="id_obligee" name="obligee" type="text" custom-attribute="value">
                """.format(url=reverse(u'obligees:autocomplete')), rendered)

    def test_new_form_with_initial_value_as_obligee_instance(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n) for n in names]
        form = self.Form(initial={u'obligee': oblgs[2]})
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u"""
                <input class="autocomplete" data-autocomplete-url="{url}" id="id_obligee" name="obligee" type="text" value="ccc">
                """.format(url=reverse(u'obligees:autocomplete')), rendered)

    def test_new_form_with_initial_value_as_obligee_name(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n) for n in names]
        form = self.Form(initial={u'obligee': u'ccc'})
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u"""
                <input class="autocomplete" data-autocomplete-url="{url}" id="id_obligee" name="obligee" type="text" value="ccc">
                """.format(url=reverse(u'obligees:autocomplete')), rendered)

    def test_submitted_with_empty_value_but_required(self):
        form = self.Form({u'obligee': u''})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors[u'obligee'], [u'This field is required.'])

        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<ul class="errorlist"><li>This field is required.</li></ul>', rendered)
        self.assertInHTML(u"""
                <input class="autocomplete" data-autocomplete-url="{url}" id="id_obligee" name="obligee" type="text">
                """.format(url=reverse(u'obligees:autocomplete')), rendered)

    def test_submitted_with_empty_value_but_not_required(self):
        form = self.Form({u'obligee': u''})
        form.fields[u'obligee'].required = False
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data[u'obligee'])

        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u"""
                <input class="autocomplete" data-autocomplete-url="{url}" id="id_obligee" name="obligee" type="text">
                """.format(url=reverse(u'obligees:autocomplete')), rendered)

    def test_submitted_with_valid_obligee_name(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n) for n in names]
        form = self.Form({u'obligee': u'bbb'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data[u'obligee'], oblgs[1])

        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u"""
                <input class="autocomplete" data-autocomplete-url="{url}" id="id_obligee" name="obligee" type="text" value="bbb">
                """.format(url=reverse(u'obligees:autocomplete')), rendered)

    def test_submitted_with_nonexisting_obligee_name(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n) for n in names]
        form = self.Form({u'obligee': u'invalid'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors[u'obligee'], [u'Invalid obligee name. Select one form the menu.'])

        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<ul class="errorlist"><li>Invalid obligee name. Select one form the menu.</li></ul>', rendered)
        self.assertInHTML(u"""
                <input class="autocomplete" data-autocomplete-url="{url}" id="id_obligee" name="obligee" type="text" value="invalid">
                """.format(url=reverse(u'obligees:autocomplete')), rendered)

    def test_to_python_is_cached(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n) for n in names]
        field = ObligeeAutocompleteField()

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

class ObligeeAutocompleteFieldWithObligeeWithAddressInputWidget(ObligeesTestCaseMixin, TestCase):
    u"""
    Tests ``ObligeeAutocompleteField`` with ``ObligeeWithAddressInput`` widget.
    """

    class Form(forms.Form):
        obligee = ObligeeAutocompleteField(
                widget=ObligeeWithAddressInput(),
                )

    class FormWithWidgetAttrs(forms.Form):
        obligee = ObligeeAutocompleteField(
                widget=ObligeeWithAddressInput(attrs={
                    u'class': u'custom-class',
                    u'custom-attribute': u'value',
                    }),
                )


    def test_new_form(self):
        form = self.Form()
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<label for="id_obligee">Obligee:</label>', rendered)
        self.assertInHTML(u"""
                <input class="autocomplete" data-autocomplete-url="{url}" id="id_obligee" name="obligee" type="text">
                """.format(url=reverse(u'obligees:autocomplete')), rendered)
        self.assertInHTML(u"""
                <div class="obligee_with_address_input_details obligee_with_address_input_hide">
                  <span class="obligee_with_address_input_street"></span><br>
                  <span class="obligee_with_address_input_zip"></span> <span class="obligee_with_address_input_city"></span><br>
                  E-mail: <span class="obligee_with_address_input_email"></span>
                </div>
                """, rendered)

    def test_new_form_with_custom_widget_class_and_attributes(self):
        form = self.FormWithWidgetAttrs()
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u"""
                <input class="autocomplete custom-class" data-autocomplete-url="{url}" id="id_obligee" name="obligee" type="text" custom-attribute="value">
                """.format(url=reverse(u'obligees:autocomplete')), rendered)

    def test_new_form_with_initial_value_as_obligee_instance(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n, street=u'%s street' % n, city=u'%s city' % n, zip=u'12345', emails=u'%s@a.com' % n) for n in names]
        form = self.Form(initial={u'obligee': oblgs[2]})
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u"""
                <input class="autocomplete" data-autocomplete-url="{url}" id="id_obligee" name="obligee" type="text" value="ccc">
                """.format(url=reverse(u'obligees:autocomplete')), rendered)
        self.assertInHTML(u"""
                <div class="obligee_with_address_input_details ">
                  <span class="obligee_with_address_input_street">ccc street</span><br>
                  <span class="obligee_with_address_input_zip">12345</span> <span class="obligee_with_address_input_city">ccc city</span><br>
                  E-mail: <span class="obligee_with_address_input_email">ccc@a.com</span>
                </div>
                """, rendered)

    def test_new_form_with_initial_value_as_obligee_name(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n, street=u'%s street' % n, city=u'%s city' % n, zip=u'12345', emails=u'%s@a.com' % n) for n in names]
        form = self.Form(initial={u'obligee': u'ccc'})
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u"""
                <input class="autocomplete" data-autocomplete-url="{url}" id="id_obligee" name="obligee" type="text" value="ccc">
                """.format(url=reverse(u'obligees:autocomplete')), rendered)
        self.assertInHTML(u"""
                <div class="obligee_with_address_input_details ">
                  <span class="obligee_with_address_input_street">ccc street</span><br>
                  <span class="obligee_with_address_input_zip">12345</span> <span class="obligee_with_address_input_city">ccc city</span><br>
                  E-mail: <span class="obligee_with_address_input_email">ccc@a.com</span>
                </div>
                """, rendered)

    def test_submitted_with_empty_value_but_required(self):
        form = self.Form({u'obligee': u''})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors[u'obligee'], [u'This field is required.'])

        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<ul class="errorlist"><li>This field is required.</li></ul>', rendered)

    def test_submitted_with_empty_value_but_not_required(self):
        form = self.Form({u'obligee': u''})
        form.fields[u'obligee'].required = False
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data[u'obligee'])

        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<ul class="errorlist"><li>This field is required.</li></ul>', rendered, count=0)

    def test_submitted_with_valid_obligee_name(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n, street=u'%s street' % n, city=u'%s city' % n, zip=u'12345', emails=u'%s@a.com' % n) for n in names]
        form = self.Form({u'obligee': u'bbb'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data[u'obligee'], oblgs[1])

        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u"""
                <input class="autocomplete" data-autocomplete-url="{url}" id="id_obligee" name="obligee" type="text" value="bbb">
                """.format(url=reverse(u'obligees:autocomplete')), rendered)
        self.assertInHTML(u"""
                <div class="obligee_with_address_input_details ">
                  <span class="obligee_with_address_input_street">bbb street</span><br>
                  <span class="obligee_with_address_input_zip">12345</span> <span class="obligee_with_address_input_city">bbb city</span><br>
                  E-mail: <span class="obligee_with_address_input_email">bbb@a.com</span>
                </div>
                """, rendered)

    def test_submitted_with_nonexisting_obligee_name(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n) for n in names]
        form = self.Form({u'obligee': u'invalid'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors[u'obligee'], [u'Invalid obligee name. Select one form the menu.'])

        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<ul class="errorlist"><li>Invalid obligee name. Select one form the menu.</li></ul>', rendered)
        self.assertInHTML(u"""
                <input class="autocomplete" data-autocomplete-url="{url}" id="id_obligee" name="obligee" type="text" value="invalid">
                """.format(url=reverse(u'obligees:autocomplete')), rendered)
        self.assertInHTML(u"""
                <div class="obligee_with_address_input_details obligee_with_address_input_hide">
                  <span class="obligee_with_address_input_street"></span><br>
                  <span class="obligee_with_address_input_zip"></span> <span class="obligee_with_address_input_city"></span><br>
                  E-mail: <span class="obligee_with_address_input_email"></span>
                </div>
                """, rendered)
