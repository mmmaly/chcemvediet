# vim: expandtab
# -*- coding: utf-8 -*-
from testfixtures import TempDirectory

from django import forms
from django.core.exceptions import ValidationError
from django.template import Context, Template
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.test.utils import override_settings

from poleno.utils.forms import (clean_button, AutoSuppressedSelect, CompositeTextField,
        PrefixedForm, validate_formatted_email, validate_comma_separated_emails)

class CleanButtonTest(TestCase):
    u"""
    Tests ``clean_button()`` functions. Checks that valid button values are accepted and invalid or
    missing button values blocked. Also checks if optinal arguments ``default_value`` and ``key``
    work.
    """

    def test_valid_button(self):
        post = {u'button': u'valid'}
        clean = clean_button(post, [u'valid', u'another'])
        self.assertEqual(clean, u'valid')

    def test_invalid_button(self):
        post = {u'button': u'invalid'}
        clean = clean_button(post, [u'valid', u'another'])
        self.assertIsNone(clean)

    def test_missing_button(self):
        post = {u'other': u'valid'}
        clean = clean_button(post, [u'valid', u'another'])
        self.assertIsNone(clean)

    def test_default_value(self):
        post = {u'button': u'invalid'}
        clean = clean_button(post, [u'valid', u'another'], u'default')
        self.assertEqual(clean, u'default')

    def test_custom_button_name(self):
        post = {u'other': u'valid'}
        clean = clean_button(post, [u'valid', u'another'], key=u'other')
        self.assertEqual(clean, u'valid')

class AutoSuppressedSelectTest(TestCase):
    u"""
    Tests ``AutoSuppressedSelect`` form widget with ``ChoiceField`` and ``ModelChoiceField`` form
    fields. Checks that selectboxes with exactly one choice (including any empty choices) are
    suppressed and replaced with a static text and selectboxes with zore or more than one choices
    are left unchanged. Checks that if the only selectbox choice is a group, the selectbox is not
    suppressed. Also checks that rendered selectboxex (or the static replacements for them)
    contains custom HTML attributes passed to widget constructor.
    """

    class ChoiceFieldForm(forms.Form):
        name = forms.ChoiceField(
                widget=AutoSuppressedSelect,
                )

        def __init__(self, *args, **kwargs):
            choices = kwargs.pop(u'choices')
            super(AutoSuppressedSelectTest.ChoiceFieldForm, self).__init__(*args, **kwargs)
            self.fields[u'name'].choices = choices

    class ChoiceFieldWithAttributesForm(forms.Form):
        name = forms.ChoiceField(
                widget=AutoSuppressedSelect(attrs={
                        u'class': u'class-for-selectbox',
                    }, suppressed_attrs={
                        u'class': u'class-for-plain-text',
                    }),
                )

        def __init__(self, *args, **kwargs):
            choices = kwargs.pop(u'choices')
            super(AutoSuppressedSelectTest.ChoiceFieldWithAttributesForm, self).__init__(*args, **kwargs)
            self.fields[u'name'].choices = choices

    class ModelChoiceFieldForm(forms.Form):
        obj = forms.ModelChoiceField(
                queryset=ContentType.objects.none(),
                empty_label=None,
                widget=AutoSuppressedSelect,
                )

        def __init__(self, *args, **kwargs):
            queryset = kwargs.pop(u'queryset')
            empty_label = kwargs.pop(u'empty_label', None)
            super(AutoSuppressedSelectTest.ModelChoiceFieldForm, self).__init__(*args, **kwargs)
            self.fields[u'obj'].queryset = queryset
            self.fields[u'obj'].empty_label = empty_label


    def _render(self, template, **context):
        return Template(template).render(Context(context))


    def test_choice_field_with_two_choices_has_selectbox(self):
        form = self.ChoiceFieldForm(choices=[(1, 'first'), (2, 'second')])
        rendered = self._render(u'{{ form }}', form=form)
        self.assertHTMLEqual(rendered, u"""
                <tr><th>
                  <label for="id_name">Name:</label>
                </th><td>
                  <select id="id_name" name="name">
                    <option value="1">first</option>
                    <option value="2">second</option>
                  </select>
                </td></tr>
                """)

    def test_choice_field_with_one_choice_has_suppressed_selectbox(self):
        form = self.ChoiceFieldForm(choices=[(1, 'first')])
        rendered = self._render(u'{{ form }}', form=form)
        self.assertHTMLEqual(rendered, u"""
                <tr><th>
                  <label for="id_name">Name:</label>
                </th><td>
                  <span><input name="name" type="hidden" value="1" />first</span>
                </td></tr>
                """)

    def test_choice_field_with_no_choices_has_empty_selectbox(self):
        form = self.ChoiceFieldForm(choices=[])
        rendered = self._render(u'{{ form }}', form=form)
        self.assertHTMLEqual(rendered, u"""
                <tr><th>
                  <label for="id_name">Name:</label>
                </th><td>
                  <select id="id_name" name="name">
                  </select>
                </td></tr>
                """)

    def test_choice_field_with_one_group_has_selectbox(self):
        form = self.ChoiceFieldForm(choices=[(None, [(1, 'groupped')])])
        rendered = self._render(u'{{ form }}', form=form)
        self.assertHTMLEqual(rendered, u"""
                <tr><th>
                  <label for="id_name">Name:</label>
                </th><td>
                  <select id="id_name" name="name">
                    <optgroup label="None">
                      <option value="1">groupped</option>
                    </optgroup>
                  </select>
                </td></tr>
                """)

    def test_model_choice_field_with_two_choices_has_selectbox(self):
        queryset = ContentType.objects.all()[:2]
        form = self.ModelChoiceFieldForm(queryset=queryset)
        rendered = self._render(u'{{ form }}', form=form)
        self.assertHTMLEqual(rendered, u"""
                <tr><th>
                  <label for="id_obj">Obj:</label>
                </th><td>
                  <select id="id_obj" name="obj">
                    <option value="{queryset[0].pk}">{queryset[0].name}</option>
                    <option value="{queryset[1].pk}">{queryset[1].name}</option>
                  </select>
                </td></tr>
                """.format(queryset=queryset))

    def test_model_choice_field_with_one_choice_has_suppressed_selectbox(self):
        queryset = ContentType.objects.all()[:1]
        form = self.ModelChoiceFieldForm(queryset=queryset)
        rendered = self._render(u'{{ form }}', form=form)
        self.assertHTMLEqual(rendered, u"""
                <tr><th>
                  <label for="id_obj">Obj:</label>
                </th><td>
                  <span><input name="obj" type="hidden" value="{queryset[0].pk}" />{queryset[0].name}</span>
                </td></tr>
                """.format(queryset=queryset))

    def test_model_choice_field_with_no_choices_has_selectbox(self):
        queryset = ContentType.objects.none()
        form = self.ModelChoiceFieldForm(queryset=queryset)
        rendered = self._render(u'{{ form }}', form=form)
        self.assertHTMLEqual(rendered, u"""
                <tr><th>
                  <label for="id_obj">Obj:</label>
                </th><td>
                  <select id="id_obj" name="obj">
                  </select>
                </td></tr>
                """)

    def test_model_choice_field_with_one_choice_and_empty_label_has_selectbox(self):
        queryset = ContentType.objects.all()[:1]
        form = self.ModelChoiceFieldForm(queryset=queryset, empty_label=u'(empty)')
        rendered = self._render(u'{{ form }}', form=form)
        self.assertHTMLEqual(rendered, u"""
                <tr><th>
                  <label for="id_obj">Obj:</label>
                </th><td>
                  <select id="id_obj" name="obj">
                    <option selected="selected" value="">(empty)</option>
                    <option value="{queryset[0].pk}">{queryset[0].name}</option>
                  </select>
                </td></tr>
                """.format(queryset=queryset))

    def test_model_choice_field_with_no_choices_and_empty_label_has_suppressed_selectbox(self):
        queryset = ContentType.objects.none()
        form = self.ModelChoiceFieldForm(queryset=queryset, empty_label=u'(empty)')
        rendered = self._render(u'{{ form }}', form=form)
        self.assertHTMLEqual(rendered, u"""
                <tr><th>
                  <label for="id_obj">Obj:</label>
                </th><td>
                  <span><input name="obj" type="hidden" value="" />(empty)</span>
                </td></tr>
                """)

    def test_selectbox_with_attributes(self):
        form = self.ChoiceFieldWithAttributesForm(choices=[(1, 'first'), (2, 'second')])
        rendered = self._render(u'{{ form }}', form=form)
        self.assertHTMLEqual(rendered, u"""
                <tr><th>
                  <label for="id_name">Name:</label>
                </th><td>
                  <select id="id_name" name="name" class="class-for-selectbox">
                    <option value="1">first</option>
                    <option value="2">second</option>
                  </select>
                </td></tr>
                """)

    def test_suppressed_selectbox_with_attributes(self):
        form = self.ChoiceFieldWithAttributesForm(choices=[(1, 'first')])
        rendered = self._render(u'{{ form }}', form=form)
        self.assertHTMLEqual(rendered, u"""
                <tr><th>
                  <label for="id_name">Name:</label>
                </th><td>
                  <span class="class-for-plain-text"><input name="name" type="hidden" value="1" />first</span>
                </td></tr>
                """)

class CompositeTextFieldTest(TestCase):
    u"""
    Tests ``CompositeTextField`` with ``CompositeTextWidget``.
    """

    class Form(forms.Form):
        composite = CompositeTextField(
                template=u'composite.txt',
                fields=[
                    forms.EmailField(),
                    forms.IntegerField(),
                    ],
                composite_attrs={
                    u'class': u'custom-class',
                    u'custom-attribute': u'value',
                    },
                context={
                    u'aaa': u'(aaa)',
                    u'bbb': u'(bbb)',
                    },
                )


    def _render(self, template, **context):
        return Template(template).render(Context(context))


    def setUp(self):
        self.tempdir = TempDirectory()
        self.settings_override = override_settings(
            TEMPLATE_LOADERS=(u'django.template.loaders.filesystem.Loader',),
            TEMPLATE_DIRS=(self.tempdir.path,),
            )
        self.settings_override.enable()
        self.tempdir.write(u'composite.txt', u'(composite.txt)\n{{ aaa }}{{ bbb }}\n{{ inputs.0 }}\n{{ inputs.1 }}\n')

    def tearDown(self):
        self.settings_override.disable()
        self.tempdir.cleanup()


    def test_new_form(self):
        form = self.Form()
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<label for="id_composite_0">Composite:</label>', rendered)
        self.assertInHTML(u"""
                <div class="custom-class composite-text" custom-attribute="value">
                  (composite.txt)
                  (aaa)(bbb)
                  <input id="id_composite_0" name="composite_0" type="email">
                  <input id="id_composite_1" name="composite_1" type="number">
                </div>
                """, rendered)

    def test_new_form_with_initial_value(self):
        form = self.Form(initial={u'composite': [u'aaa', u'bbb']})
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<input id="id_composite_0" name="composite_0" type="email" value="aaa">', rendered)
        self.assertInHTML(u'<input id="id_composite_1" name="composite_1" type="number" value="bbb">', rendered)

    def test_submitted_with_both_empty_values_but_required(self):
        form = self.Form({u'composite_0': u'', u'composite_1': u''})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors[u'composite'], [u'This field is required.'])

        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<ul class="errorlist"><li>This field is required.</li></ul>', rendered)
        self.assertInHTML(u'<input id="id_composite_0" name="composite_0" type="email">', rendered)
        self.assertInHTML(u'<input id="id_composite_1" name="composite_1" type="number">', rendered)

    def test_submitted_with_both_empty_values_but_not_required(self):
        form = self.Form({u'composite_0': u'', u'composite_1': u''})
        form.fields[u'composite'].required = False
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data[u'composite'], [])

        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<ul class="errorlist"><li>This field is required.</li></ul>', rendered, count=0)
        self.assertInHTML(u'<input id="id_composite_0" name="composite_0" type="email">', rendered)
        self.assertInHTML(u'<input id="id_composite_1" name="composite_1" type="number">', rendered)

    def test_submitted_with_one_invalid_and_one_empty_value(self):
        form = self.Form({u'composite_0': u'invalid', u'composite_1': u''})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors[u'composite'], [u'This field is required.'])

        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<ul class="errorlist"><li>This field is required.</li></ul>', rendered)
        self.assertInHTML(u'<input id="id_composite_0" name="composite_0" type="email" value="invalid">', rendered)
        self.assertInHTML(u'<input id="id_composite_1" name="composite_1" type="number">', rendered)

    def test_submitted_with_both_invalid_values(self):
        form = self.Form({u'composite_0': u'invalid', u'composite_1': u'invalid'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors[u'composite'], [u'Enter a valid email address.', u'Enter a whole number.'])

        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<ul class="errorlist"><li>Enter a valid email address.</li><li>Enter a whole number.</li></ul>', rendered)
        self.assertInHTML(u'<input id="id_composite_0" name="composite_0" type="email" value="invalid">', rendered)
        self.assertInHTML(u'<input id="id_composite_1" name="composite_1" type="number" value="invalid">', rendered)

    def test_submitted_with_one_valid_and_one_invalid_value(self):
        form = self.Form({u'composite_0': u'invalid', u'composite_1': u'47'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors[u'composite'], [u'Enter a valid email address.'])

        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<ul class="errorlist"><li>Enter a valid email address.</li></ul>', rendered)
        self.assertInHTML(u'<input id="id_composite_0" name="composite_0" type="email" value="invalid">', rendered)
        self.assertInHTML(u'<input id="id_composite_1" name="composite_1" type="number" value="47">', rendered)

    def test_submitted_with_both_valid_values(self):
        form = self.Form({u'composite_0': u'valid@example.com', u'composite_1': u'47'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data[u'composite'], [u'valid@example.com', 47])

        rendered = self._render(u'{{ form }}', form=form)
        self.assertNotIn(u'errorlist', rendered)
        self.assertInHTML(u'<input id="id_composite_0" name="composite_0" type="email" value="valid@example.com">', rendered)
        self.assertInHTML(u'<input id="id_composite_1" name="composite_1" type="number" value="47">', rendered)

    def test_finalize(self):
        form = self.Form({u'composite_0': u'valid@example.com', u'composite_1': u'47'})
        self.assertTrue(form.is_valid())

        finalized = form.fields[u'composite'].finalize(form.cleaned_data[u'composite'], context={u'bbb': u'(new_bbb)'})
        self.assertEqual(finalized, u'(composite.txt)\n(aaa)(new_bbb)\nvalid@example.com\n47')

class PrefixedFormTest(TestCase):
    u"""
    Tests ``PrefixedForm`` form class. Checks that automatic form prefixes are generated correctly
    and that any additional prefixes passed to the form constructor are used as well.
    """

    class PrefixedForm(PrefixedForm):
        name = forms.CharField()


    def _render(self, template, **context):
        return Template(template).render(Context(context))


    def test_with_additional_prefix(self):
        form = self.PrefixedForm(prefix=u'additionalprefix')
        rendered = self._render(u'{{ form }}', form=form)
        self.assertHTMLEqual(rendered, u"""
                <tr><th>
                  <label for="id_additionalprefix-prefixedform-name">Name:</label>
                </th><td>
                  <input id="id_additionalprefix-prefixedform-name" name="additionalprefix-prefixedform-name" type="text" />
                </td></tr>
                """)

    def test_without_additional_prefix(self):
        form = self.PrefixedForm()
        rendered = self._render(u'{{ form }}', form=form)
        self.assertHTMLEqual(rendered, u"""
                <tr><th>
                  <label for="id_prefixedform-name">Name:</label>
                </th><td>
                  <input id="id_prefixedform-name" name="prefixedform-name" type="text" />
                </td></tr>
                """)

class ValidateFormattedEmail(TestCase):
    u"""
    Tests ``validate_formatted_email()`` validator.
    """

    def test_empty_string_is_invalid(self):
        with self.assertRaisesMessage(ValidationError, u'"" is not a valid email address'):
            validate_formatted_email(u'')

    def test_valid_values(self):
        validate_formatted_email(u'smith@example.com')
        validate_formatted_email(u'John Smith <smith@example.com>')
        validate_formatted_email(u'"John \\"Agent\\" Smith" <smith@example.com>')
        validate_formatted_email(u'"Smith, John" <smith@example.com>')
        validate_formatted_email(u'"smith@example.com" <smith@example.com>')

    def test_invalid_values(self):
        with self.assertRaisesMessage(ValidationError, u'"invalid" is not a valid email address'):
            validate_formatted_email(u'invalid')
        with self.assertRaisesMessage(ValidationError, u'"invalid@example" is not a valid email address'):
            validate_formatted_email(u'invalid@example')
        with self.assertRaisesMessage(ValidationError, u'"John" is not a valid email address'):
            validate_formatted_email(u'John "Smith <smith@example.com>')
        with self.assertRaisesMessage(ValidationError, u'"Smith" is not a valid email address'):
            validate_formatted_email(u'Smith, John <smith@example.com>')
        with self.assertRaisesMessage(ValidationError, u'"" is not a valid email address'):
            validate_formatted_email(u',smith@example.com')

    def test_normalized_values(self):
        with self.assertRaisesMessage(ValidationError, u'Parsed as: smith@example.com'):
            validate_formatted_email(u'<smith@example.com>')
        with self.assertRaisesMessage(ValidationError, u'Parsed as: invalidsmith@example.com'):
            validate_formatted_email(u'invalid smith@example.com')
        with self.assertRaisesMessage(ValidationError, u'Parsed as: invalid <smith@example.com>'):
            validate_formatted_email(u'"invalid" <smith@example.com>')
        with self.assertRaisesMessage(ValidationError, u'Parsed as: "aaa, bbb ccc" <smith@example.com>'):
            validate_formatted_email(u'"aaa, bbb" ccc <smith@example.com>')
        with self.assertRaisesMessage(ValidationError, u'Parsed as: smith@example.com'):
            validate_formatted_email(u'smith@example.com <smith@example.com>')
        with self.assertRaisesMessage(ValidationError, u'Parsed as: smith@example.com'):
            validate_formatted_email(u'smith@example.com,')
        with self.assertRaisesMessage(ValidationError, u'Parsed as: John Smith <smith@example.com>'):
            validate_formatted_email(u'John Smith <smith@example.com>, john@example.com')

class ValidateCommaSeparatedEmailsTest(TestCase):
    u"""
    Tests ``validate_comma_separated_emails()`` validator.
    """

    def test_empty_string_is_valid(self):
        validate_comma_separated_emails(u'')

    def test_valid_values(self):
        validate_comma_separated_emails(u'smith@example.com')
        validate_comma_separated_emails(u'John Smith <smith@example.com>, john@example.com')
        validate_comma_separated_emails(u'"John \\"Agent\\" Smith" <smith@example.com>')
        validate_comma_separated_emails(u'"Smith, John" <smith@example.com>')
        validate_comma_separated_emails(u'"smith@example.com" <smith@example.com>')

    def test_invalid_values(self):
        with self.assertRaisesMessage(ValidationError, u'"invalid" is not a valid email address'):
            validate_comma_separated_emails(u'invalid')
        with self.assertRaisesMessage(ValidationError, u'"invalid@example" is not a valid email address'):
            validate_comma_separated_emails(u'invalid@example')
        with self.assertRaisesMessage(ValidationError, u'"John" is not a valid email address'):
            validate_comma_separated_emails(u'John "Smith <smith@example.com>')
        with self.assertRaisesMessage(ValidationError, u'"Smith" is not a valid email address'):
            validate_comma_separated_emails(u'Smith, John <smith@example.com>')
        with self.assertRaisesMessage(ValidationError, u'"" is not a valid email address'):
            validate_comma_separated_emails(u',smith@example.com')

    def test_normalized_values(self):
        with self.assertRaisesMessage(ValidationError, u'Parsed as: smith@example.com'):
            validate_comma_separated_emails(u'<smith@example.com>')
        with self.assertRaisesMessage(ValidationError, u'Parsed as: invalidsmith@example.com'):
            validate_comma_separated_emails(u'invalid smith@example.com')
        with self.assertRaisesMessage(ValidationError, u'Parsed as: invalid <smith@example.com>'):
            validate_comma_separated_emails(u'"invalid" <smith@example.com>')
        with self.assertRaisesMessage(ValidationError, u'Parsed as: "aaa, bbb ccc" <smith@example.com>'):
            validate_comma_separated_emails(u'"aaa, bbb" ccc <smith@example.com>')
        with self.assertRaisesMessage(ValidationError, u'Parsed as: smith@example.com, smith@example.com'):
            validate_comma_separated_emails(u'smith@example.com <smith@example.com>')
        with self.assertRaisesMessage(ValidationError, u'Parsed as: smith@example.com'):
            validate_comma_separated_emails(u'smith@example.com,')
