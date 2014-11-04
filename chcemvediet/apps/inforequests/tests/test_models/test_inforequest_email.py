# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import IntegrityError
from django.test import TestCase

from .. import InforequestsTestCaseMixin
from ...models import InforequestEmail

class InforequestEmailTest(InforequestsTestCaseMixin, TestCase):
    u"""
    Tests ``InforequestEmail`` model.
    """

    def test_inforequest_field(self):
        inforequest = self._create_inforequest()
        email, rel = self._create_inforequest_email(inforequest=inforequest)
        self.assertEqual(rel.inforequest, inforequest)

    def test_inforequest_field_may_not_be_null(self):
        with self.assertRaisesMessage(IntegrityError, u'inforequests_inforequestemail.inforequest_id may not be NULL'):
            self._create_inforequest_email(omit=[u'inforequest'])

    def test_email_field(self):
        inforequest = self._create_inforequest()
        email, rel = self._create_inforequest_email(inforequest=inforequest)
        self.assertEqual(rel.email, email)

    def test_email_field_may_not_be_null(self):
        inforequest = self._create_inforequest()
        with self.assertRaisesMessage(IntegrityError, u'inforequests_inforequestemail.email_id may not be NULL'):
            self._create_inforequest_email(inforequest=inforequest, omit=[u'email'])

    def test_type_field(self):
        tests = (
                (InforequestEmail.TYPES.APPLICANT_ACTION, u'Applicant Action'),
                (InforequestEmail.TYPES.OBLIGEE_ACTION,   u'Obligee Action'),
                (InforequestEmail.TYPES.UNDECIDED,        u'Undecided'),
                (InforequestEmail.TYPES.UNRELATED,        u'Unrelated'),
                (InforequestEmail.TYPES.UNKNOWN,          u'Unknown'),
                )
        # Make sure we are testing all defined inforequest email types
        tested_types = [a for a, _ in tests]
        defined_types = InforequestEmail.TYPES._inverse.keys()
        self.assertItemsEqual(tested_types, defined_types)

        inforequest = self._create_inforequest()
        for rel_type, expected_display in tests:
            email, rel = self._create_inforequest_email(inforequest=inforequest, reltype=rel_type)
            self.assertEqual(rel.type, rel_type)
            self.assertEqual(rel.get_type_display(), expected_display)

    def test_type_field_may_not_be_null(self):
        inforequest = self._create_inforequest()
        with self.assertRaisesMessage(IntegrityError, u'inforequests_inforequestemail.type may not be NULL'):
            self._create_inforequest_email(inforequest=inforequest, omit=[u'reltype'])

    def test_inforequest_inforequestemail_set_backward_relation(self):
        inforequest = self._create_inforequest()
        email, rel = self._create_inforequest_email(inforequest=inforequest)
        result = inforequest.inforequestemail_set.all()
        self.assertItemsEqual(result, [rel])

    def test_inforequest_inforequestemail_set_backward_relation_empty_by_default(self):
        inforequest = self._create_inforequest()
        result = inforequest.inforequestemail_set.all()
        self.assertItemsEqual(result, [])

    def test_message_inforequestemail_set_backward_relation(self):
        inforequest = self._create_inforequest()
        email, rel = self._create_inforequest_email(inforequest=inforequest)
        result = email.inforequestemail_set.all()
        self.assertItemsEqual(result, [rel])

    def test_message_inforequestemail_set_backward_relation_empty_by_default(self):
        email = self._create_message()
        result = email.inforequestemail_set.all()
        self.assertItemsEqual(result, [])
