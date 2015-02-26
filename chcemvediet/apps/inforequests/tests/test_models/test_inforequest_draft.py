# vim: expandtab
# -*- coding: utf-8 -*-
import random

from django.db import IntegrityError
from django.test import TestCase

from .. import InforequestsTestCaseMixin
from ...models import InforequestDraft

class InforequestDraftTest(InforequestsTestCaseMixin, TestCase):
    u"""
    Tests ``InforequestDraft`` model.
    """

    def test_applicant_field(self):
        draft = self._create_inforequest_draft(applicant=self.user1)
        self.assertEqual(draft.applicant, self.user1)

    def test_applicant_field_may_not_be_null(self):
        with self.assertRaisesMessage(IntegrityError, u'inforequests_inforequestdraft.applicant_id may not be NULL'):
            self._create_inforequest_draft(omit=[u'applicant'])

    def test_obligee_field(self):
        draft = self._create_inforequest_draft(obligee=self.obligee1)
        self.assertEqual(draft.obligee, self.obligee1)

    def test_obligee_field_default_value_if_omitted(self):
        draft = self._create_inforequest_draft(omit=[u'obligee'])
        self.assertIsNone(draft.obligee)

    def test_subject_field(self):
        draft = self._create_inforequest_draft(subject=[u'Subject'])
        self.assertEqual(draft.subject, [u'Subject'])

    def test_subject_field_default_value_if_omitted(self):
        draft = self._create_inforequest_draft(omit=[u'subject'])
        self.assertEqual(draft.subject, [])

    def test_content_field(self):
        draft = self._create_inforequest_draft(content=[u'Content'])
        self.assertEqual(draft.content, [u'Content'])

    def test_content_field_default_value_if_omitted(self):
        draft = self._create_inforequest_draft(omit=[u'content'])
        self.assertEqual(draft.content, [])

    def test_attachment_set_relation(self):
        draft = self._create_inforequest_draft()
        attch1 = self._create_attachment(generic_object=draft)
        attch2 = self._create_attachment(generic_object=draft)
        result = draft.attachment_set.all()
        self.assertItemsEqual(result, [attch1, attch2])

    def test_attachment_set_relation_empty_by_default(self):
        draft = self._create_inforequest_draft()
        result = draft.attachment_set.all()
        self.assertItemsEqual(result, [])

    def test_user_inforequestdraft_set_backward_relation(self):
        draft1 = self._create_inforequest_draft(applicant=self.user1)
        draft2 = self._create_inforequest_draft(applicant=self.user1)
        result = self.user1.inforequestdraft_set.all()
        self.assertItemsEqual(result, [draft1, draft2])

    def test_user_inforequestdraft_set_backward_relation_empty_by_default(self):
        result = self.user1.inforequestdraft_set.all()
        self.assertItemsEqual(result, [])

    def test_obligee_inforequestdraft_set_backward_relation(self):
        draft1 = self._create_inforequest_draft(obligee=self.obligee1)
        draft2 = self._create_inforequest_draft(obligee=self.obligee1)
        result = self.obligee1.inforequestdraft_set.all()
        self.assertItemsEqual(result, [draft1, draft2])

    def test_obligee_inforequestdraft_set_backward_relation_empty_by_default(self):
        result = self.obligee1.inforequestdraft_set.all()
        self.assertItemsEqual(result, [])

    def test_default_ordering_by_pk(self):
        drafts = [self._create_inforequest_draft() for i in range(10)]
        sample = random.sample(drafts, 5)
        result = InforequestDraft.objects.filter(pk__in=[d.pk for d in sample])
        self.assertEqual(list(result), sorted(sample, key=lambda d: d.pk))

    def test_repr(self):
        draft = self._create_inforequest_draft()
        self.assertEqual(repr(draft), u'<InforequestDraft: %s>' % draft.pk)

    def test_owned_by_query_method(self):
        draft1 = self._create_inforequest_draft(applicant=self.user1)
        draft2 = self._create_inforequest_draft(applicant=self.user1)
        draft3 = self._create_inforequest_draft(applicant=self.user2)
        draft4 = self._create_inforequest_draft(applicant=self.user2)
        result = InforequestDraft.objects.owned_by(self.user2)
        self.assertItemsEqual(result, [draft3, draft4])

    def test_owned_by_query_method_with_no_matches(self):
        draft1 = self._create_inforequest_draft(applicant=self.user1)
        draft2 = self._create_inforequest_draft(applicant=self.user1)
        result = InforequestDraft.objects.owned_by(self.user2)
        self.assertItemsEqual(result, [])
