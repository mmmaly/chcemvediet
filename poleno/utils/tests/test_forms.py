# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError
from django.template import Context, Template
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from poleno.utils.forms import clean_button, AutoSuppressedSelect, PrefixedForm, validate_comma_separated_emails

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
