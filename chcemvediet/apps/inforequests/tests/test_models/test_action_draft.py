# vim: expandtab
# -*- coding: utf-8 -*-
import random

from django.db import IntegrityError
from django.test import TestCase

from poleno.utils.date import naive_date
from poleno.attachments.models import Attachment
from chcemvediet.apps.obligees.models import Obligee

from .. import InforequestsTestCaseMixin
from ...models import Inforequest, ActionDraft

class ActionDraftTest(InforequestsTestCaseMixin, TestCase):
    u"""
    Tests ``ActionDraft`` model.
    """

    def test_inforequest_field(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest)
        self.assertEqual(draft.inforequest, inforequest)

    def test_inforequest_field_may_not_be_null(self):
        with self.assertRaisesMessage(IntegrityError, u'inforequests_actiondraft.inforequest_id may not be NULL'):
            self._create_action_draft(omit=[u'inforequest'])

    def test_branch_field(self):
        inforequest = self._create_inforequest()
        branch = self._create_branch(inforequest=inforequest)
        draft = self._create_action_draft(inforequest=inforequest, branch=branch)
        self.assertEqual(draft.branch, branch)

    def test_branch_field_default_value_if_omitted(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest, omit=[u'branch'])
        self.assertIsNone(draft.branch)

    def test_type_field(self):
        tests = (
                (ActionDraft.TYPES.REQUEST,                u'Request'),
                (ActionDraft.TYPES.CLARIFICATION_RESPONSE, u'Clarification Response'),
                (ActionDraft.TYPES.APPEAL,                 u'Appeal'),
                (ActionDraft.TYPES.CONFIRMATION,           u'Confirmation'),
                (ActionDraft.TYPES.EXTENSION,              u'Extension'),
                (ActionDraft.TYPES.ADVANCEMENT,            u'Advancement'),
                (ActionDraft.TYPES.CLARIFICATION_REQUEST,  u'Clarification Request'),
                (ActionDraft.TYPES.DISCLOSURE,             u'Disclosure'),
                (ActionDraft.TYPES.REFUSAL,                u'Refusal'),
                (ActionDraft.TYPES.AFFIRMATION,            u'Affirmation'),
                (ActionDraft.TYPES.REVERSION,              u'Reversion'),
                (ActionDraft.TYPES.REMANDMENT,             u'Remandment'),
                (ActionDraft.TYPES.ADVANCED_REQUEST,       u'Advanced Request'),
                (ActionDraft.TYPES.EXPIRATION,             u'Expiration'),
                (ActionDraft.TYPES.APPEAL_EXPIRATION,      u'Appeal Expiration'),
                )
        # Make sure we are testing all defined action types
        tested_action_types = [a for a, _ in tests]
        defined_action_types = ActionDraft.TYPES._inverse.keys()
        self.assertItemsEqual(tested_action_types, defined_action_types)

        inforequest = self._create_inforequest()
        for action_type, expected_display in tests:
            draft = self._create_action_draft(inforequest=inforequest, type=action_type)
            self.assertEqual(draft.type, action_type)
            self.assertEqual(draft.get_type_display(), expected_display)

    def test_type_field_may_not_be_null(self):
        inforequest = self._create_inforequest()
        with self.assertRaisesMessage(IntegrityError, u'inforequests_actiondraft.type may not be NULL'):
            self._create_action_draft(inforequest=inforequest, omit=[u'type'])

    def test_subject_and_content_fields(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest, subject=u'Subject', content=u'Content')
        self.assertEqual(draft.subject, u'Subject')
        self.assertEqual(draft.content, u'Content')

    def test_subject_and_content_fields_adefault_values_if_omitted(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest, omit=[u'subject', u'content'])
        self.assertEqual(draft.subject, u'')
        self.assertEqual(draft.content, u'')

    def test_attachment_set_relation(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest)
        attachment1 = self._create_attachment(generic_object=draft)
        attachment2 = self._create_attachment(generic_object=draft)
        self.assertItemsEqual(draft.attachment_set.all(), [attachment1, attachment2])

    def test_attachment_set_relation_empty_by_default(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest)
        self.assertItemsEqual(draft.attachment_set.all(), [])

    def test_effective_date_field(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest, effective_date=naive_date(u'2010-10-05'))
        self.assertEqual(draft.effective_date, naive_date(u'2010-10-05'))

    def test_effective_date_field_default_value_if_omitted(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest, omit=[u'effective_date'])
        self.assertIsNone(draft.effective_date)

    def test_deadline_field(self):
        tests = (
                ActionDraft.TYPES.REQUEST,
                ActionDraft.TYPES.CLARIFICATION_RESPONSE,
                ActionDraft.TYPES.APPEAL,
                ActionDraft.TYPES.CONFIRMATION,
                ActionDraft.TYPES.EXTENSION,
                ActionDraft.TYPES.ADVANCEMENT,
                ActionDraft.TYPES.CLARIFICATION_REQUEST,
                ActionDraft.TYPES.DISCLOSURE,
                ActionDraft.TYPES.REFUSAL,
                ActionDraft.TYPES.AFFIRMATION,
                ActionDraft.TYPES.REVERSION,
                ActionDraft.TYPES.REMANDMENT,
                ActionDraft.TYPES.ADVANCED_REQUEST,
                ActionDraft.TYPES.EXPIRATION,
                ActionDraft.TYPES.APPEAL_EXPIRATION,
                )
        # Make sure we are testing all action types
        defined_action_types = ActionDraft.TYPES._inverse.keys()
        self.assertItemsEqual(tests, defined_action_types)

        inforequest = self._create_inforequest()
        for action_type in tests:
            draft = self._create_action_draft(inforequest=inforequest, type=action_type, deadline=3)
            self.assertEqual(draft.deadline, 3)

    def test_deadline_field_default_value_if_omitted(self):
        tests = (
                ActionDraft.TYPES.REQUEST,
                ActionDraft.TYPES.CLARIFICATION_RESPONSE,
                ActionDraft.TYPES.APPEAL,
                ActionDraft.TYPES.CONFIRMATION,
                ActionDraft.TYPES.EXTENSION,
                ActionDraft.TYPES.ADVANCEMENT,
                ActionDraft.TYPES.CLARIFICATION_REQUEST,
                ActionDraft.TYPES.DISCLOSURE,
                ActionDraft.TYPES.REFUSAL,
                ActionDraft.TYPES.AFFIRMATION,
                ActionDraft.TYPES.REVERSION,
                ActionDraft.TYPES.REMANDMENT,
                ActionDraft.TYPES.ADVANCED_REQUEST,
                ActionDraft.TYPES.EXPIRATION,
                ActionDraft.TYPES.APPEAL_EXPIRATION,
                )
        # Make sure we are testing all action types
        defined_action_types = ActionDraft.TYPES._inverse.keys()
        self.assertItemsEqual(tests, defined_action_types)

        inforequest = self._create_inforequest()
        for action_type in tests:
            draft = self._create_action_draft(inforequest=inforequest, type=action_type, omit=[u'deadline'])
            self.assertIsNone(draft.deadline)

    def test_disclosure_level_field(self):
        tests = (
                (ActionDraft.DISCLOSURE_LEVELS.NONE,    u'No Disclosure at All'),
                (ActionDraft.DISCLOSURE_LEVELS.PARTIAL, u'Partial Disclosure'),
                (ActionDraft.DISCLOSURE_LEVELS.FULL,    u'Full Disclosure'),
                )
        # Make sure we are testing all defined disclosure levels
        tested_disclosure_levels = [a for a, _ in tests]
        defined_disclosure_levels = ActionDraft.DISCLOSURE_LEVELS._inverse.keys()
        self.assertItemsEqual(tested_disclosure_levels, defined_disclosure_levels)

        inforequest = self._create_inforequest()
        for disclosure_level, expected_display in tests:
            draft = self._create_action_draft(inforequest=inforequest, disclosure_level=disclosure_level)
            self.assertEqual(draft.disclosure_level, disclosure_level)
            self.assertEqual(draft.get_disclosure_level_display(), expected_display)

    def test_disclosure_level_field_default_value_if_omitted(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest, omit=[u'disclosure_level'])
        self.assertIsNone(draft.disclosure_level)

    def test_refusal_reason_field(self):
        tests = (
                (ActionDraft.REFUSAL_REASONS.DOES_NOT_HAVE,    u'Does not Have Information'),
                (ActionDraft.REFUSAL_REASONS.DOES_NOT_PROVIDE, u'Does not Provide Information'),
                (ActionDraft.REFUSAL_REASONS.DOES_NOT_CREATE,  u'Does not Create Information'),
                (ActionDraft.REFUSAL_REASONS.COPYRIGHT,        u'Copyright Restriction'),
                (ActionDraft.REFUSAL_REASONS.BUSINESS_SECRET,  u'Business Secret'),
                (ActionDraft.REFUSAL_REASONS.PERSONAL,         u'Personal Information'),
                (ActionDraft.REFUSAL_REASONS.CONFIDENTIAL,     u'Confidential Information'),
                (ActionDraft.REFUSAL_REASONS.NO_REASON,        u'No Reason Specified'),
                (ActionDraft.REFUSAL_REASONS.OTHER_REASON,     u'Other Reason'),
                )
        # Make sure we are testing all defined refusal reasons
        tested_refusal_reasons = [a for a, _ in tests]
        defined_refusal_reasons = ActionDraft.REFUSAL_REASONS._inverse.keys()
        self.assertItemsEqual(tested_refusal_reasons, defined_refusal_reasons)

        inforequest = self._create_inforequest()
        for refusal_reason, expected_display in tests:
            draft = self._create_action_draft(inforequest=inforequest, refusal_reason=refusal_reason)
            self.assertEqual(draft.refusal_reason, refusal_reason)
            self.assertEqual(draft.get_refusal_reason_display(), expected_display)

    def test_refusal_reason_field_default_value_if_omitted(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest, omit=[u'refusal_reason'])
        self.assertIsNone(draft.refusal_reason)

    def test_obligee_set_relation(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest)
        draft.obligee_set.add(self.obligee1)
        draft.obligee_set.add(self.obligee2)
        result = draft.obligee_set.all()
        self.assertItemsEqual(result, [self.obligee1, self.obligee2])

    def test_obligee_set_relation_empty_by_default(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest)
        result = draft.obligee_set.all()
        self.assertItemsEqual(result, [])

    def test_inforequest_actiondraft_set_backward_relation(self):
        inforequest = self._create_inforequest()
        draft1 = self._create_action_draft(inforequest=inforequest)
        draft2 = self._create_action_draft(inforequest=inforequest)
        result = inforequest.actiondraft_set.all()
        self.assertItemsEqual(result, [draft1, draft2])

    def test_inforequest_actiondraft_set_backward_relation_empty_by_default(self):
        inforequest = self._create_inforequest()
        result = inforequest.actiondraft_set.all()
        self.assertItemsEqual(result, [])

    def test_branch_actiondraft_set_backward_relation(self):
        inforequest = self._create_inforequest()
        branch = self._create_branch(inforequest=inforequest)
        draft1 = self._create_action_draft(inforequest=inforequest, branch=branch)
        draft2 = self._create_action_draft(inforequest=inforequest, branch=branch)
        result = branch.actiondraft_set.all()
        self.assertItemsEqual(result, [draft1, draft2])

    def test_branch_actiondraft_set_backward_relation_empty_by_default(self):
        inforequest = self._create_inforequest()
        branch = self._create_branch(inforequest=inforequest)
        result = branch.actiondraft_set.all()
        self.assertItemsEqual(result, [])

    def test_obligee_actiondraft_set_backward_relation(self):
        inforequest = self._create_inforequest()
        draft1 = self._create_action_draft(inforequest=inforequest)
        draft2 = self._create_action_draft(inforequest=inforequest)
        draft1.obligee_set.add(self.obligee1)
        draft2.obligee_set.add(self.obligee1)
        result = self.obligee1.actiondraft_set.all()
        self.assertItemsEqual(result, [draft1, draft2])

    def test_obligee_actiondraft_set_backward_relation_empty_by_default(self):
        result = self.obligee1.actiondraft_set.all()
        self.assertItemsEqual(result, [])

    def test_no_default_ordering(self):
        self.assertFalse(ActionDraft.objects.all().ordered)

    def test_prefetch_attachments_staticmethod(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest)
        attachment1 = self._create_attachment(generic_object=draft)
        attachment2 = self._create_attachment(generic_object=draft)

        # Without arguments
        with self.assertNumQueries(2):
            draft = ActionDraft.objects.prefetch_related(ActionDraft.prefetch_attachments()).get(pk=draft.pk)
        with self.assertNumQueries(0):
            self.assertEqual(draft.attachments, [attachment1, attachment2])

        # With custom path and queryset
        with self.assertNumQueries(3):
            inforequest = (Inforequest.objects
                    .prefetch_related(u'actiondraft_set')
                    .prefetch_related(ActionDraft.prefetch_attachments(u'actiondraft_set', Attachment.objects.extra(select=dict(moo=47))))
                    .get(pk=inforequest.pk))
        with self.assertNumQueries(0):
            self.assertEqual(inforequest.actiondraft_set.all()[0].attachments, [attachment1, attachment2])
            self.assertEqual(inforequest.actiondraft_set.all()[0].attachments[0].moo, 47)

    def test_attachments_property(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest)
        attachment1 = self._create_attachment(generic_object=draft)
        attachment2 = self._create_attachment(generic_object=draft)

        # Property is cached
        with self.assertNumQueries(1):
            draft = ActionDraft.objects.get(pk=draft.pk)
        with self.assertNumQueries(1):
            self.assertEqual(draft.attachments, [attachment1, attachment2])
        with self.assertNumQueries(0):
            self.assertEqual(draft.attachments, [attachment1, attachment2])

        # Property is prefetched with prefetch_attachments()
        with self.assertNumQueries(2):
            draft = ActionDraft.objects.prefetch_related(ActionDraft.prefetch_attachments()).get(pk=draft.pk)
        with self.assertNumQueries(0):
            self.assertEqual(draft.attachments, [attachment1, attachment2])

    def test_prefetch_obligees_staticmethod(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest)
        draft.obligee_set.add(self.obligee1)
        draft.obligee_set.add(self.obligee2)

        # Without arguments
        with self.assertNumQueries(2):
            draft = ActionDraft.objects.prefetch_related(ActionDraft.prefetch_obligees()).get(pk=draft.pk)
        with self.assertNumQueries(0):
            self.assertEqual(draft.obligees, [self.obligee1, self.obligee2])

        # With custom path and queryset
        with self.assertNumQueries(3):
            inforequest = (Inforequest.objects
                    .prefetch_related(u'actiondraft_set')
                    .prefetch_related(ActionDraft.prefetch_obligees(u'actiondraft_set', Obligee.objects.extra(select=dict(moo=47))))
                    .get(pk=inforequest.pk))
        with self.assertNumQueries(0):
            self.assertEqual(inforequest.actiondraft_set.all()[0].obligees, [self.obligee1, self.obligee2])
            self.assertEqual(inforequest.actiondraft_set.all()[0].obligees[0].moo, 47)

    def test_obligees_property(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest)
        draft.obligee_set.add(self.obligee1)
        draft.obligee_set.add(self.obligee2)

        # Property is cached
        with self.assertNumQueries(1):
            draft = ActionDraft.objects.get(pk=draft.pk)
        with self.assertNumQueries(1):
            self.assertEqual(draft.obligees, [self.obligee1, self.obligee2])
        with self.assertNumQueries(0):
            self.assertEqual(draft.obligees, [self.obligee1, self.obligee2])

        # Property is prefetched with prefetch_obligees()
        with self.assertNumQueries(2):
            draft = ActionDraft.objects.prefetch_related(ActionDraft.prefetch_obligees()).get(pk=draft.pk)
        with self.assertNumQueries(0):
            self.assertEqual(draft.obligees, [self.obligee1, self.obligee2])

    def test_repr(self):
        inforequest = self._create_inforequest()
        draft = self._create_action_draft(inforequest=inforequest)
        self.assertEqual(repr(draft), u'<ActionDraft: %s>' % draft.pk)

    def test_order_by_pk_query_method(self):
        inforequest = self._create_inforequest()
        drafts = [self._create_action_draft(inforequest=inforequest) for i in range(20)]
        sample = random.sample(drafts, 10)
        result = ActionDraft.objects.filter(pk__in=(d.pk for d in sample)).order_by_pk().reverse()
        self.assertEqual(list(result), sorted(sample, key=lambda d: -d.pk))
