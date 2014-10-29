# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase

from . import AccountsTestCaseMixin

class SignupFormTest(AccountsTestCaseMixin, TestCase):
    u"""
    Tests ``allauth`` ``account_signup`` view using ``SignupForm`` form. Does not check
    ``account_signup`` functionality, only checks functionality added by ``SignupForm``.
    """

    def _create_account_signup_data(self, **kwargs):
        defaults = {
                u'first_name': u'Default Testing First Name',
                u'last_name': u'Default Testing Last Name',
                u'street': u'Default Testing Street',
                u'city': u'Default Testing City',
                u'zip': u'00000',
                u'email': u'default_testing_mail@example.com',
                u'password1': u'default_testing_password',
                u'password2': u'default_testing_password',
                }
        defaults.update(kwargs)
        return defaults


    def test_get_signup_form(self):
        response = self.client.get(reverse(u'account_signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'account/signup.html')
        self.assertInHTML(u'<input id="id_first_name" maxlength="30" name="first_name" placeholder="First name" type="text">', response.content)
        self.assertInHTML(u'<input id="id_last_name" maxlength="30" name="last_name" placeholder="Last name" type="text">', response.content)
        self.assertInHTML(u'<input id="id_street" maxlength="100" name="street" placeholder="Street" type="text">', response.content)
        self.assertInHTML(u'<input id="id_city" maxlength="30" name="city" placeholder="City" type="text">', response.content)
        self.assertInHTML(u'<input id="id_zip" maxlength="5" name="zip" placeholder="Zip" type="text">', response.content)

    def test_post_signup_form_with_valid_data_creates_user_and_his_profile(self):
        data = self._create_account_signup_data(
                first_name=u'John',
                last_name=u'Smith',
                street=u'147 Lake Side',
                city=u'Winterfield',
                zip=u'12345',
                email=u'smith@example.com',
                )
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertRedirects(response, reverse(u'account_email_verification_sent'))

        created_user = User.objects.get(email=u'smith@example.com')
        self.assertEqual(created_user.first_name, u'John')
        self.assertEqual(created_user.last_name, u'Smith')
        self.assertEqual(created_user.profile.user, created_user)
        self.assertEqual(created_user.profile.street, u'147 Lake Side')
        self.assertEqual(created_user.profile.city, u'Winterfield')
        self.assertEqual(created_user.profile.zip, u'12345')

    def test_post_signup_form_with_invalid_data_does_not_create_user(self):
        data = self._create_account_signup_data(zip=u'invalid', email=u'smith@example.com')
        response = self.client.post(reverse(u'account_signup'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'account/signup.html')

        with self.assertRaisesMessage(User.DoesNotExist, u'User matching query does not exist.'):
            User.objects.get(email=u'smith@example.com')

    def test_first_name_field_is_required(self):
        data = self._create_account_signup_data(first_name=u'')
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'first_name', 'This field is required.')

    def test_first_name_field_max_length(self):
        data = self._create_account_signup_data(first_name=u'x'*31)
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'first_name', 'Ensure this value has at most 30 characters (it has 31).')

    def test_last_name_field_is_required(self):
        data = self._create_account_signup_data(last_name=u'')
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'last_name', 'This field is required.')

    def test_last_name_field_max_length(self):
        data = self._create_account_signup_data(last_name=u'x'*31)
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'last_name', 'Ensure this value has at most 30 characters (it has 31).')

    def test_street_field_is_required(self):
        data = self._create_account_signup_data(street=u'')
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'street', 'This field is required.')

    def test_street_field_max_length(self):
        data = self._create_account_signup_data(street=u'x'*101)
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'street', 'Ensure this value has at most 100 characters (it has 101).')

    def test_city_field_is_required(self):
        data = self._create_account_signup_data(city=u'')
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'city', 'This field is required.')

    def test_city_field_max_length(self):
        data = self._create_account_signup_data(city=u'x'*31)
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'city', 'Ensure this value has at most 30 characters (it has 31).')

    def test_zip_field_is_required(self):
        data = self._create_account_signup_data(zip=u'')
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'zip', 'This field is required.')

    def test_zip_field_max_length(self):
        data = self._create_account_signup_data(zip=u'1'*6)
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'zip', 'Ensure this value has at most 5 characters (it has 6).')

    def test_zip_field_regex(self):
        data = self._create_account_signup_data(zip=u'wrong')
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'zip', 'Enter a valid value.')

