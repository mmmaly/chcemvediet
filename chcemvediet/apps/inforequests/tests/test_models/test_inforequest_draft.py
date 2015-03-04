# vim: expandtab
# -*- coding: utf-8 -*-
import random

from django.db import IntegrityError
from django.contrib.auth.models import User
from django.test import TestCase

from poleno.attachments.models import Attachment

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
        self.assertEqual(draft.subject, ())

    def test_content_field(self):
        draft = self._create_inforequest_draft(content=[u'Content'])
        self.assertEqual(draft.content, [u'Content'])

    def test_content_field_default_value_if_omitted(self):
        draft = self._create_inforequest_draft(omit=[u'content'])
        self.assertEqual(draft.content, ())

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

    def test_no_default_ordering(self):
        self.assertFalse(InforequestDraft.objects.all().ordered)

    def test_prefetch_attachments_staticmethod(self):
        draft = self._create_inforequest_draft()
        attch1 = self._create_attachment(generic_object=draft)
        attch2 = self._create_attachment(generic_object=draft)

        # Without arguments
        with self.assertNumQueries(2):
            draft = InforequestDraft.objects.prefetch_related(InforequestDraft.prefetch_attachments()).get(pk=draft.pk)
        with self.assertNumQueries(0):
            self.assertEqual(draft.attachments, [attch1, attch2])

        # With custom path and queryset
        with self.assertNumQueries(3):
            user = (User.objects
                    .prefetch_related(u'inforequestdraft_set')
                    .prefetch_related(InforequestDraft.prefetch_attachments(u'inforequestdraft_set', Attachment.objects.extra(select=dict(moo=47))))
                    .get(pk=self.user1.pk))
        with self.assertNumQueries(0):
            self.assertEqual(user.inforequestdraft_set.all()[0].attachments, [attch1, attch2])
            self.assertEqual(user.inforequestdraft_set.all()[0].attachments[0].moo, 47)

    def test_attachments_property(self):
        draft = self._create_inforequest_draft()
        attch1 = self._create_attachment(generic_object=draft)
        attch2 = self._create_attachment(generic_object=draft)

        # Property is cached
        with self.assertNumQueries(1):
            draft = InforequestDraft.objects.get(pk=draft.pk)
        with self.assertNumQueries(1):
            self.assertEqual(draft.attachments, [attch1, attch2])
        with self.assertNumQueries(0):
            self.assertEqual(draft.attachments, [attch1, attch2])

        # Property is prefetched with prefetch_attachments()
        with self.assertNumQueries(2):
            draft = InforequestDraft.objects.prefetch_related(InforequestDraft.prefetch_attachments()).get(pk=draft.pk)
        with self.assertNumQueries(0):
            self.assertEqual(draft.attachments, [attch1, attch2])

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

    def test_order_by_pk_query_method(self):
        drafts = [self._create_inforequest_draft() for i in range(20)]
        sample = random.sample(drafts, 10)
        result = InforequestDraft.objects.filter(pk__in=(d.pk for d in sample)).order_by_pk().reverse()
        self.assertEqual(list(result), sorted(sample, key=lambda d: -d.pk))
