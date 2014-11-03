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

    def test_type_field_with_applicant_action(self):
        inforequest = self._create_inforequest()
        email, rel = self._create_inforequest_email(inforequest=inforequest, reltype=InforequestEmail.TYPES.APPLICANT_ACTION)
        self.assertEqual(rel.type, InforequestEmail.TYPES.APPLICANT_ACTION)
        self.assertEqual(rel.get_type_display(), u'Applicant Action')

    def test_type_field_with_obligee_action(self):
        inforequest = self._create_inforequest()
        email, rel = self._create_inforequest_email(inforequest=inforequest, reltype=InforequestEmail.TYPES.OBLIGEE_ACTION)
        self.assertEqual(rel.type, InforequestEmail.TYPES.OBLIGEE_ACTION)
        self.assertEqual(rel.get_type_display(), u'Obligee Action')

    def test_type_field_with_undecided(self):
        inforequest = self._create_inforequest()
        email, rel = self._create_inforequest_email(inforequest=inforequest, reltype=InforequestEmail.TYPES.UNDECIDED)
        self.assertEqual(rel.type, InforequestEmail.TYPES.UNDECIDED)
        self.assertEqual(rel.get_type_display(), u'Undecided')

    def test_type_field_with_unrelated(self):
        inforequest = self._create_inforequest()
        email, rel = self._create_inforequest_email(inforequest=inforequest, reltype=InforequestEmail.TYPES.UNRELATED)
        self.assertEqual(rel.type, InforequestEmail.TYPES.UNRELATED)
        self.assertEqual(rel.get_type_display(), u'Unrelated')

    def test_type_field_with_unknown(self):
        inforequest = self._create_inforequest()
        email, rel = self._create_inforequest_email(inforequest=inforequest, reltype=InforequestEmail.TYPES.UNKNOWN)
        self.assertEqual(rel.type, InforequestEmail.TYPES.UNKNOWN)
        self.assertEqual(rel.get_type_display(), u'Unknown')

    def test_type_field_may_not_be_null(self):
        inforequest = self._create_inforequest()
        with self.assertRaisesMessage(IntegrityError, u'inforequests_inforequestemail.type may not be NULL'):
            self._create_inforequest_email(inforequest=inforequest, omit=[u'reltype'])
