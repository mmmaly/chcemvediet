# vim: expandtab
# -*- coding: utf-8 -*-
import lxml.html
from django.contrib.auth.models import User
from django.test import TestCase

from poleno.utils.urls import reverse


class LoginFormTest(TestCase):
    u"""
    Tests ``allauth`` ``account_login`` view using ``LoginForm`` form registered as
    "account_login". Does not check ``account_login`` functionality, only checks functionality
    added by ``LoginForm``.
    """

    def setUp(self):
        user = User.objects.create(username=u'john', email=u'john@doe.org')
        user.set_password(u'doe')
        user.save()

    def _create_account_login_data(self, **kwargs):
        defaults = {
                u'login': u'john@doe.org',
                u'password': u'doe',
                u'g-recaptcha-response': u'PASSED',
                }
        defaults.update(kwargs)
        return defaults


    def test_get_login_form(self):
        response = self.client.get(reverse(u'account_login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'account/login.html')
        html = lxml.html.fromstring(response.content.decode(u'utf-8'))
        element = html.get_element_by_id(u'g-recaptcha-response')

    def test_post_login_form_with_valid_data(self):
        data = self._create_account_login_data(login=u'john@doe.org', password=u'doe')
        response = self.client.post(reverse(u'account_login'), data, follow=True)
        self.assertTrue(response.context[u'user'].is_active)
        self.assertRedirects(response, reverse(u'inforequests:mine'))

    def test_recaptcha_field_is_required(self):
        data = self._create_account_login_data(**{u'g-recaptcha-response': u''})
        response = self.client.post(reverse(u'account_login'), data, follow=True)
        self.assertFormError(response, u'form', u'recaptcha', u'This field is required.')

class SignupFormTest(TestCase):
    u"""
    Tests ``allauth`` ``account_signup`` view using ``SignupForm`` form registered as
    "account_signup". Does not check ``account_signup`` functionality, only checks functionality
    added by ``SignupForm``.
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
                u'agreement': True,
                u'g-recaptcha-response': u'PASSED',
                }
        defaults.update(kwargs)
        return defaults


    def test_get_signup_form(self):
        response = self.client.get(reverse(u'account_signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'account/signup.html')
        html = lxml.html.fromstring(response.content.decode(u'utf-8'))

        element = html.get_element_by_id(u'id_first_name')
        self.assertEqual(element.tag, u'input')
        self.assertEqual(element.attrib[u'class'], u'form-control')
        self.assertEqual(element.attrib[u'name'], u'first_name')
        self.assertEqual(element.attrib[u'type'], u'text')

        element = html.get_element_by_id(u'id_last_name')
        self.assertEqual(element.tag, u'input')
        self.assertEqual(element.attrib[u'class'], u'form-control')
        self.assertEqual(element.attrib[u'name'], u'last_name')
        self.assertEqual(element.attrib[u'type'], u'text')

        element = html.get_element_by_id(u'id_street')
        self.assertEqual(element.tag, u'input')
        self.assertEqual(element.attrib[u'class'], u'form-control')
        self.assertEqual(element.attrib[u'name'], u'street')
        self.assertEqual(element.attrib[u'type'], u'text')

        element = html.get_element_by_id(u'id_city')
        self.assertEqual(element.tag, u'input')
        self.assertEqual(element.attrib[u'class'], u'form-control')
        self.assertEqual(element.attrib[u'name'], u'city')
        self.assertEqual(element.attrib[u'type'], u'text')

        element = html.get_element_by_id(u'id_zip')
        self.assertEqual(element.tag, u'input')
        self.assertEqual(element.attrib[u'class'], u'form-control')
        self.assertEqual(element.attrib[u'name'], u'zip')
        self.assertEqual(element.attrib[u'type'], u'text')

        element = html.get_element_by_id(u'g-recaptcha-response')

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
        self.assertRedirects(response, reverse(u'inforequests:mine'))

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
        self.assertFormError(response, u'form', u'first_name', u'This field is required.')

    def test_first_name_field_max_length(self):
        data = self._create_account_signup_data(first_name=u'x'*31)
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'first_name', u'Ensure this value has at most 30 characters (it has 31).')

    def test_last_name_field_is_required(self):
        data = self._create_account_signup_data(last_name=u'')
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'last_name', u'This field is required.')

    def test_last_name_field_max_length(self):
        data = self._create_account_signup_data(last_name=u'x'*31)
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'last_name', u'Ensure this value has at most 30 characters (it has 31).')

    def test_street_field_is_required(self):
        data = self._create_account_signup_data(street=u'')
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'street', u'This field is required.')

    def test_street_field_max_length(self):
        data = self._create_account_signup_data(street=u'x'*101)
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'street', u'Ensure this value has at most 100 characters (it has 101).')

    def test_city_field_is_required(self):
        data = self._create_account_signup_data(city=u'')
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'city', u'This field is required.')

    def test_city_field_max_length(self):
        data = self._create_account_signup_data(city=u'x'*31)
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'city', u'Ensure this value has at most 30 characters (it has 31).')

    def test_zip_field_is_required(self):
        data = self._create_account_signup_data(zip=u'')
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'zip', u'This field is required.')

    def test_zip_field_max_length(self):
        data = self._create_account_signup_data(zip=u'1'*6)
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'zip', u'Ensure this value has at most 5 characters (it has 6).')

    def test_zip_field_regex(self):
        data = self._create_account_signup_data(zip=u'wrong')
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'zip', u'Enter a valid value.')

    def test_agreement_field_is_required(self):
        data = self._create_account_signup_data(agreement=False)
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'agreement', u'This field is required.')

    def test_recaptcha_field_is_required(self):
        data = self._create_account_signup_data(**{u'g-recaptcha-response': u''})
        response = self.client.post(reverse(u'account_signup'), data, follow=True)
        self.assertFormError(response, u'form', u'recaptcha', u'This field is required.')

class ResetPasswordFormTest(TestCase):
    u"""
    Tests ``allauth`` ``password_reset`` view using ``ResetPasswordForm`` form registered as
    "password_reset". Does not check ``password_reset`` functionality, only checks functionality
    added by ``ResetPasswordForm``.
    """

    def setUp(self):
        user = User.objects.create(username=u'john', email=u'john@doe.org')
        user.set_password(u'doe')
        user.save()

    def _create_account_password_reset_data(self, **kwargs):
        defaults = {
                u'email': u'john@doe.org',
                u'g-recaptcha-response': u'PASSED',
                }
        defaults.update(kwargs)
        return defaults


    def test_get_login_form(self):
        response = self.client.get(reverse(u'account_reset_password'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'account/password_reset.html')
        html = lxml.html.fromstring(response.content.decode(u'utf-8'))
        element = html.get_element_by_id(u'g-recaptcha-response')

    def test_post_reset_password_form_with_valid_data(self):
        data = self._create_account_password_reset_data(email=u'john@doe.org')
        response = self.client.post(reverse(u'account_reset_password'), data, follow=True)
        self.assertRedirects(response, reverse(u'account_reset_password_done'))

    def test_recaptcha_field_is_required(self):
        data = self._create_account_password_reset_data(**{u'g-recaptcha-response': u''})
        response = self.client.post(reverse(u'account_reset_password'), data, follow=True)
        self.assertFormError(response, u'form', u'recaptcha', u'This field is required.')
