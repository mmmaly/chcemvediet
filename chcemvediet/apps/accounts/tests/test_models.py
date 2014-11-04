# vim: expandtab
# -*- coding: utf-8 -*-
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from . import AccountsTestCaseMixin
from ..models import Profile, create_profile_on_user_post_save

class ProfileModelTest(AccountsTestCaseMixin, TestCase):
    u"""
    Tests ``Profile`` model.
    """

    def test_create_profile_on_user_post_save_signal_receiver_registered(self):
        self.assertIn(create_profile_on_user_post_save, post_save._live_receivers(sender=User))

    def test_creating_new_user_automatically_creates_user_profile(self):
        user = User.objects.create_user(u'john', u'lennon@thebeatles.com', u'johnpassword')
        self.assertEqual(type(user.profile), Profile)
        self.assertIsNotNone(user.profile.pk)

    def test_saving_existing_user_does_not_recreate_user_profile(self):
        user = User.objects.create_user(u'john', u'lennon@thebeatles.com', u'johnpassword')
        old_profile = Profile.objects.get(user=user)

        user.name = u'johny'
        user.save()
        new_profile = Profile.objects.get(user=user)
        self.assertEqual(old_profile, new_profile)

    def test_user_field(self):
        user = User.objects.create_user(u'john', u'lennon@thebeatles.com', u'johnpassword')
        self.assertEqual(user.profile.user, user)

    def test_street_field(self):
        user = User.objects.create_user(u'john', u'lennon@thebeatles.com', u'johnpassword')
        self.assertEqual(user.profile.street, u'')

    def test_city_field(self):
        user = User.objects.create_user(u'john', u'lennon@thebeatles.com', u'johnpassword')
        self.assertEqual(user.profile.city, u'')

    def test_zip_field(self):
        user = User.objects.create_user(u'john', u'lennon@thebeatles.com', u'johnpassword')
        self.assertEqual(user.profile.zip, u'')

    def test_repr(self):
        user = User.objects.create_user(u'john', u'lennon@thebeatles.com', u'johnpassword')
        self.assertEqual(repr(user.profile), u'<Profile: %s>' % user.profile.pk)
