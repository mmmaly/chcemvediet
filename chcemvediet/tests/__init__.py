# vim: expandtab
# -*- coding: utf-8 -*-
import itertools
import logging
import os
import unittest

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core.files.base import ContentFile
from django.template import Context, Template
from django.test import TestCase
from django.test.runner import DiscoverRunner

from poleno.attachments.models import Attachment
from poleno.mail.models import Message, Recipient
from poleno.utils.date import local_today, utc_now

from ..apps.geounits.models import Region, District, Municipality, Neighbourhood
from ..apps.inforequests.models import Branch, Feedback, Inforequest, InforequestEmail, InforequestDraft, Action
from ..apps.obligees.models import Obligee, ObligeeTag, ObligeeGroup, ObligeeAlias


class CustomTestRunner(DiscoverRunner):
    u"""
    Custom test runner with the following features:
     -- Disabled logging while testing.
        Source: http://stackoverflow.com/questions/5255657/how-can-i-disable-logging-while-running-unit-tests-in-python-django
     -- Forced language code 'en'
     -- Used MD5 password hasher, it's much faster then the production hasher.
     -- Mocked google recaptcha.
        Source: https://pypi.org/project/django-recaptcha/1.0.6/#unit-testing
    """

    def setup_test_environment(self, **kwargs):
        super(CustomTestRunner, self).setup_test_environment(**kwargs)
        # Python 2 name still used throughout the test suite.
        if not hasattr(unittest.TestCase, u'assertItemsEqual'):
            unittest.TestCase.assertItemsEqual = unittest.TestCase.assertCountEqual
        settings.LANGUAGE_CODE = u'en'
        settings.PASSWORD_HASHERS = [u'django.contrib.auth.hashers.MD5PasswordHasher']
        os.environ[u'RECAPTCHA_TESTING'] = u'True'

    def teardown_test_environment(self, **kwargs):
        del os.environ[u'RECAPTCHA_TESTING']
        super(CustomTestRunner, self).teardown_test_environment(**kwargs)

    def run_tests(self, *args, **kwargs):
        logging.disable(logging.CRITICAL)
        return super(CustomTestRunner, self).run_tests(*args, **kwargs)

class ChcemvedietTestCaseMixin(TestCase):

    def _pre_setup(self):
        super(ChcemvedietTestCaseMixin, self)._pre_setup()
        self.counter = itertools.count()
        self.user = self._create_user()
        self.user1 = self._create_user()
        self.user2 = self._create_user()
        self.message = self._create_message()
        self.recipient = self._create_recipient()
        self.region = self._create_region()
        self.district = self._create_district()
        self.municipality = self._create_municipality()
        self.neighbourhood = self._create_neighbourhood()
        self.obligee = self._create_obligee()
        self.obligee1 = self._create_obligee()
        self.obligee2 = self._create_obligee()
        self.obligee3 = self._create_obligee()
        self.tag = self._create_obligee_tag()
        self.group = self._create_obligee_group()
        self.inforequest = self._create_inforequest()
        self.branch = self._create_branch()
        self.action = self._create_action()


    def _call_with_defaults(self, func, kwargs, defaults):
        omit = kwargs.pop(u'omit', [])
        defaults.update(kwargs)
        for key in omit:
            del defaults[key]
        return func(**defaults)

    def _create_user(self, **kwargs):
        nr = u'{:03d}'.format(next(self.counter))
        street = kwargs.pop(u'street', u'Default User Street')
        city = kwargs.pop(u'city', u'Default User City')
        zip = kwargs.pop(u'zip', u'00000')
        anonymize_inforequests = kwargs.pop(u'anonymize_inforequests', True)
        custom_anonymized_strings = kwargs.pop(u'custom_anonymized_strings', None)
        days_to_publish_inforequest = kwargs.pop(u'days_to_publish_inforequest', 60)
        email_verified = kwargs.pop(u'email_verified', True)
        user = self._call_with_defaults(User.objects.create_user, kwargs, {
                u'username': u'default_testing_username_{}'.format(nr),
                u'first_name': u'Default Testing First Name',
                u'last_name': u'Default Testing Last Name',
                u'email': u'default_testing_mail_{}@a.com'.format(nr),
                u'password': u'default_testing_secret',
                })
        user.profile.street = street
        user.profile.city = city
        user.profile.zip = zip
        user.profile.anonymize_inforequests = anonymize_inforequests
        user.profile.custom_anonymized_strings = custom_anonymized_strings
        user.profile.days_to_publish_inforequest = days_to_publish_inforequest
        user.profile.save()
        if email_verified:
            user.emailaddress_set.create(email=user.email, verified=True)
        return user

    def _login_user(self, user=None, password=u'default_testing_secret'):
        if user is None:
            user = self.user
        logged_in = self.client.login(username=user.username, password=password)
        self.assertTrue(logged_in, u'The provided credentials are incorrect:\nusername: {} password: {}.'.format(
                user.username, password
                ))

    def _logout_user(self):
        self.client.logout()

    def _get_session(self):
        if hasattr(self.client.session, u'session_key'):
            return Session.objects.get(session_key=self.client.session.session_key)
        return None

    def _create_attachment(self, **kwargs):
        content = kwargs.pop(u'content', u'Default Testing Content')
        return self._call_with_defaults(Attachment.objects.create, kwargs, {
                u'generic_object': self._get_session(),
                u'file': ContentFile(content, name=u'filename.txt'),
                u'name': u'filename.txt',
                })

    def _create_message(self, **kwargs):
        return self._call_with_defaults(Message.objects.create, kwargs, {
            u'type': Message.TYPES.OUTBOUND,
            u'processed': utc_now(),
            u'from_name': u'Default Testing From Name',
            u'from_mail': u'default_testing_from_mail@example.com',
            u'received_for': u'default_testing_for_mail@example.com',
            u'subject': u'Default Testing Subject',
            u'text': u'Default Testing Text Content',
            u'html': u'<html><body>Default Testing HTML Content</body></html>',
            })

    def _create_recipient(self, **kwargs):
        return self._call_with_defaults(Recipient.objects.create, kwargs, {
            u'message': self.message,
            u'name': u'Default Testing Name',
            u'mail': u'default_testing_mail@example.com',
            u'type': Recipient.TYPES.TO,
            u'status': Recipient.STATUSES.UNDEFINED,
            u'status_details': u'',
            u'remote_id': u'',
            })

    def _create_region(self, **kwargs):
        name = u'SK{:05d}'.format(next(self.counter))
        return self._call_with_defaults(Region.objects.create, kwargs, {
                u'id': name,
                u'name': name,
                })

    def _create_district(self, **kwargs):
        name = u'SK{:05d}'.format(next(self.counter))
        return self._call_with_defaults(District.objects.create, kwargs, {
                u'id': name,
                u'name': name,
                u'region': self.region,
                })

    def _create_municipality(self, **kwargs):
        name = u'SK{:05d}'.format(next(self.counter))
        return self._call_with_defaults(Municipality.objects.create, kwargs, {
                u'id': name,
                u'name': name,
                u'region': self.region,
                u'district': self.district,
                })

    def _create_neighbourhood(self, **kwargs):
        name = u'SK{:05d}'.format(next(self.counter))
        return self._call_with_defaults(Neighbourhood.objects.create, kwargs, {
                u'id': name,
                u'name': name,
                u'region': self.region,
                u'district': self.district,
                u'municipality': self.municipality,
                })

    def _create_obligee(self, **kwargs):
        return self._call_with_defaults(Obligee.objects.create, kwargs, {
                u'official_name': u'Default Testing Official Name',
                u'name': u'Default Testing Name {:03d}'.format(next(self.counter)),
                u'name_genitive': u'Default Testing Name genitive',
                u'name_dative': u'Default Testing Name dative',
                u'name_accusative': u'Default Testing Name accusative',
                u'name_locative': u'Default Testing Name locative',
                u'name_instrumental': u'Default Testing Name instrumental',
                u'gender': Obligee.GENDERS.MASCULINE,
                u'ico': u'00000000',
                u'street': u'Default Testing Street',
                u'city': u'Default Testing City',
                u'zip': u'00000',
                u'iczsj': self.neighbourhood,
                u'emails': u'default_testing_mail@example.com',
                u'latitude': 0.0,
                u'longitude': 0.0,
                u'type': Obligee.TYPES.SECTION_1,
                u'official_description': u'Default testing official description.',
                u'simple_description': u'Default testing simple description.',
                u'status': Obligee.STATUSES.PENDING,
                u'notes': u'Default testing notes.',
                })

    def _create_obligee_tag(self, **kwargs):
        nr = u'{:03d}'.format(next(self.counter))
        return self._call_with_defaults(ObligeeTag.objects.create, kwargs, {
                u'key': u'Default Testing Key {}'.format(nr),
                u'name': u'Default Testing Name {}'.format(nr),
                })

    def _create_obligee_group(self, **kwargs):
        nr = u'{:03d}'.format(next(self.counter))
        return self._call_with_defaults(ObligeeGroup.objects.create, kwargs, {
                u'key': u'Default Testing Key {}'.format(nr),
                u'name': u'Default Testing Name {}'.format(nr),
                u'description': u'Default Testing Description',
                })

    def _create_obligee_alias(self, **kwargs):
        return self._call_with_defaults(ObligeeAlias.objects.create, kwargs, {
                u'obligee': self.obligee,
                u'name': u'Default Testing Name',
                u'description': u'Default testing description.',
                u'notes': u'Default testing notes.',
                })

    def _create_inforequest_draft(self, **kwargs):
        return self._call_with_defaults(InforequestDraft.objects.create, kwargs, {
                u'applicant': self.user,
                u'obligee': self.obligee,
                u'subject': [u'Default Testing Subject'],
                u'content': [u'Default Testing Content'],
                u'modified': None,
                })

    def _create_inforequest(self, **kwargs):
        return self._call_with_defaults(Inforequest.objects.create, kwargs, {
                u'applicant': self.user,
                u'subject': u'Default Testing Subject',
                u'content': u'Default Testing Content',
                u'closed': False,
                u'published': None,
                u'last_undecided_email_reminder': None,
                })

    def _create_inforequest_email(self, **kwargs):
        create = object()

        relargs = {
                u'inforequest': kwargs.pop(u'inforequest', self.inforequest),
                u'email': kwargs.pop(u'email', create),
                u'type': kwargs.pop(u'reltype', InforequestEmail.TYPES.UNDECIDED),
                }

        omit = kwargs.get(u'omit', [])
        for kwarg, relarg in ((u'inforequest', u'inforequest'), (u'reltype', u'type'), (u'email', u'email')):
            if kwarg in omit:
                relargs.pop(relarg)
                omit.remove(kwarg)

        if relargs.get(u'email') is create:
            relargs[u'email'] = self._create_message(**kwargs)

        rel = InforequestEmail.objects.create(**relargs)
        email = relargs.get(u'email')
        return email, rel

    def _create_branch(self, **kwargs):
        return self._call_with_defaults(Branch.objects.create, kwargs, {
            u'inforequest': self.inforequest,
            u'obligee': self.obligee,
            u'advanced_by': None,
            })

    def _create_action(self, **kwargs):
        return self._call_with_defaults(Action.objects.create, kwargs, {
                u'branch': self.branch,
                u'email': None,
                u'type': Action.TYPES.REQUEST,
                u'subject': u'Default Testing Subject',
                u'content': u'Default Testing Content',
                u'content_type': Action.CONTENT_TYPES.PLAIN_TEXT,
                u'file_number': u'',
                u'created': utc_now(),
                u'sent_date': local_today(),
                u'delivered_date': local_today(),
                u'legal_date': local_today(),
                u'extension': None,
                u'snooze': None,
                u'disclosure_level': None,
                u'refusal_reason': None,
                u'last_deadline_reminder': None,
        })

    def _create_feedback(self, **kwargs):
        return self._call_with_defaults(Feedback.objects.create, kwargs, {
            u'inforequest': self.inforequest,
            u'content': u'Default Testing Content',
            u'created': utc_now(),
        })

    def _render(self, template, **context):
        return Template(template).render(Context(context))
