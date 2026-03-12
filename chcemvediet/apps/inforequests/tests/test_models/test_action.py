# vim: expandtab
# -*- coding: utf-8 -*-
import random
import mock
import datetime
from collections import defaultdict

from django.db import IntegrityError
from django.test import TestCase
from django.utils.translation import gettext as __

from poleno.timewarp import timewarp
from poleno.attachments.models import Attachment
from poleno.mail.models import Message, Recipient
from poleno.utils.date import local_datetime_from_local, naive_date, local_today, utc_now
from poleno.utils.test import created_instances
from poleno.utils.translation import translation

from .. import InforequestsTestCaseMixin
from ...models import InforequestEmail, Branch, Action
from ...models.deadline import Deadline


class ActionTest(InforequestsTestCaseMixin, TestCase):
    u"""
    Tests ``Action`` model.
    """

    def test_branch_field(self):
        branch = self._create_branch()
        action = self._create_action(branch=branch)
        self.assertEqual(action.branch, branch)

    def test_branch_field_may_not_be_null(self):
        with self.assertRaisesMessage(IntegrityError, u'NOT NULL constraint failed: inforequests_action.branch_id'):
            self._create_action(omit=[u'branch'])

    def test_email_field(self):
        email = self._create_message()
        action = self._create_action(email=email)
        self.assertEqual(action.email, email)

    def test_email_field_default_value_if_omitted(self):
        action = self._create_action(omit=[u'email'])
        self.assertIsNone(action.email)

    def test_type_field(self):
        tests = (
                (Action.TYPES.REQUEST,                __(u'inforequests:Action:type:REQUEST')),
                (Action.TYPES.CLARIFICATION_RESPONSE, __(u'inforequests:Action:type:CLARIFICATION_RESPONSE')),
                (Action.TYPES.APPEAL,                 __(u'inforequests:Action:type:APPEAL')),
                (Action.TYPES.CONFIRMATION,           __(u'inforequests:Action:type:CONFIRMATION')),
                (Action.TYPES.EXTENSION,              __(u'inforequests:Action:type:EXTENSION')),
                (Action.TYPES.ADVANCEMENT,            __(u'inforequests:Action:type:ADVANCEMENT')),
                (Action.TYPES.CLARIFICATION_REQUEST,  __(u'inforequests:Action:type:CLARIFICATION_REQUEST')),
                (Action.TYPES.DISCLOSURE,             __(u'inforequests:Action:type:DISCLOSURE')),
                (Action.TYPES.REFUSAL,                __(u'inforequests:Action:type:REFUSAL')),
                (Action.TYPES.AFFIRMATION,            __(u'inforequests:Action:type:AFFIRMATION')),
                (Action.TYPES.REVERSION,              __(u'inforequests:Action:type:REVERSION')),
                (Action.TYPES.REMANDMENT,             __(u'inforequests:Action:type:REMANDMENT')),
                (Action.TYPES.ADVANCED_REQUEST,       __(u'inforequests:Action:type:ADVANCED_REQUEST')),
                (Action.TYPES.EXPIRATION,             __(u'inforequests:Action:type:EXPIRATION')),
                (Action.TYPES.APPEAL_EXPIRATION,      __(u'inforequests:Action:type:APPEAL_EXPIRATION')),
                )
        # Make sure we are testing all defined action types
        tested_action_types = [a for a, _ in tests]
        defined_action_types = Action.TYPES._inverse.keys()
        self.assertItemsEqual(tested_action_types, defined_action_types)

        for action_type, expected_display in tests:
            action = self._create_action(type=action_type)
            self.assertEqual(action.type, action_type)
            self.assertEqual(action.get_type_display(), expected_display)

    def test_type_field_may_not_be_null(self):
        with self.assertRaisesMessage(IntegrityError, u'NOT NULL constraint failed: inforequests_action.type'):
            self._create_action(omit=[u'type'])

    def test_subject_and_content_fields(self):
        action = self._create_action(subject=u'Subject', content=u'Content')
        self.assertEqual(action.subject, u'Subject')
        self.assertEqual(action.content, u'Content')

    def test_subject_and_content_fields_default_values_if_omitted(self):
        action = self._create_action(omit=[u'subject', u'content'])
        self.assertEqual(action.subject, u'')
        self.assertEqual(action.content, u'')

    def test_content_type_field(self):
        tests = (
            (Action.CONTENT_TYPES.PLAIN_TEXT, u'Plain Text'),
            (Action.CONTENT_TYPES.HTML, u'HTML'),
        )
        # Make sure we are testing all defined action content_types
        tested_action_content_types = [content_type for content_type, _ in tests]
        defined_action_content_types = Action.CONTENT_TYPES._inverse.keys()
        self.assertItemsEqual(defined_action_content_types, tested_action_content_types)

        for content_type, expected_display in tests:
            action = self._create_action(content_type=content_type)
            self.assertEqual(action.content_type, content_type)
            self.assertEqual(action.get_content_type_display(), expected_display)

    def test_content_type_field_default_value_if_omitted(self):
        action = self._create_action(omit=[u'content_type'])
        self.assertEqual(action.content_type, Action.CONTENT_TYPES.PLAIN_TEXT)

    def test_attachment_set_relation(self):
        action = self._create_action()
        attachment1 = self._create_attachment(generic_object=action)
        attachment2 = self._create_attachment(generic_object=action)
        self.assertItemsEqual(action.attachment_set.all(), [attachment1, attachment2])

    def test_attachment_set_relation_empty_by_default(self):
        action = self._create_action()
        self.assertItemsEqual(action.attachment_set.all(), [])

    def test_file_number_field(self):
        action = self._create_action(file_number=u'12345')
        self.assertEqual(action.file_number, u'12345')

    def test_file_number_field_default_value_if_omitted(self):
        action = self._create_action(omit=[u'file_number'])
        self.assertEqual(action.file_number, u'')

    def test_created_field(self):
        dt = local_datetime_from_local(u'2010-10-05 10:33:00.979899')
        action = self._create_action(created=dt)
        self.assertEqual(action.created, dt)

    def test_created_field_default_value_if_omitted(self):
        action = self._create_action(omit=[u'created'])
        self.assertAlmostEqual(action.created, utc_now(), delta=datetime.timedelta(milliseconds=100))

    def test_sent_date_field(self):
        date = naive_date(u'2010-10-05')
        action = self._create_action(sent_date=date)
        self.assertEqual(action.sent_date, date)

    def test_sent_date_field_default_value_if_omitted(self):
        action = self._create_action(omit=[u'sent_date'])
        self.assertIsNone(action.sent_date)

    def test_delivered_date_field(self):
        date = naive_date(u'2010-10-05')
        action = self._create_action(delivered_date=date)
        self.assertEqual(action.delivered_date, date)

    def test_delivered_date_field_default_value_if_omitted(self):
        action = self._create_action(omit=[u'delivered_date'])
        self.assertIsNone(action.delivered_date)

    def test_legal_date_field(self):
        action = self._create_action(legal_date=naive_date(u'2010-10-05'))
        self.assertEqual(action.legal_date, naive_date(u'2010-10-05'))

    def test_legal_date_field_may_not_be_null(self):
        with self.assertRaisesMessage(IntegrityError, u'NOT NULL constraint failed: inforequests_action.legal_date'):
            self._create_action(omit=[u'legal_date'])

    def test_extension_field(self):
        action = self._create_action(extension=3)
        self.assertEqual(action.extension, 3)

    def test_extension_field_default_value_if_omitted(self):
        action = self._create_action(omit=[u'extension'])
        self.assertIsNone(action.extension)

    def test_snooze_field(self):
        date = naive_date(u'2010-10-05')
        action = self._create_action(snooze=date)
        self.assertEqual(action.snooze, date)

    def test_snooze_field_default_value_if_omitted(self):
        action = self._create_action(omit=[u'snooze'])
        self.assertIsNone(action.snooze)

    def test_disclosure_level_field(self):
        tests = (
                (Action.DISCLOSURE_LEVELS.NONE,    __(u'inforequests:Action:disclosure_level:NONE')),
                (Action.DISCLOSURE_LEVELS.PARTIAL, __(u'inforequests:Action:disclosure_level:PARTIAL')),
                (Action.DISCLOSURE_LEVELS.FULL,    __(u'inforequests:Action:disclosure_level:FULL')),
                )
        # Make sure we are testing all defined disclosure levels
        tested_disclosure_levels = [a for a, _ in tests]
        defined_disclosure_levels = Action.DISCLOSURE_LEVELS._inverse.keys()
        self.assertItemsEqual(tested_disclosure_levels, defined_disclosure_levels)

        for disclosure_level, expected_display in tests:
            action = self._create_action(disclosure_level=disclosure_level)
            self.assertEqual(action.disclosure_level, disclosure_level)
            self.assertEqual(action.get_disclosure_level_display(), expected_display)

    def test_disclosure_level_field_default_value_if_omitted(self):
        action = self._create_action(omit=[u'disclosure_level'])
        self.assertIsNone(action.disclosure_level)

    def test_refusal_reason_field(self):
        tests = (
                (Action.REFUSAL_REASONS.DOES_NOT_HAVE,    __(u'inforequests:Action:refusal_reason:DOES_NOT_HAVE')),
                (Action.REFUSAL_REASONS.DOES_NOT_PROVIDE, __(u'inforequests:Action:refusal_reason:DOES_NOT_PROVIDE')),
                (Action.REFUSAL_REASONS.DOES_NOT_CREATE,  __(u'inforequests:Action:refusal_reason:DOES_NOT_CREATE')),
                (Action.REFUSAL_REASONS.COPYRIGHT,        __(u'inforequests:Action:refusal_reason:COPYRIGHT')),
                (Action.REFUSAL_REASONS.BUSINESS_SECRET,  __(u'inforequests:Action:refusal_reason:BUSINESS_SECRET')),
                (Action.REFUSAL_REASONS.PERSONAL,         __(u'inforequests:Action:refusal_reason:PERSONAL')),
                (Action.REFUSAL_REASONS.CONFIDENTIAL,     __(u'inforequests:Action:refusal_reason:CONFIDENTIAL')),
                (Action.REFUSAL_REASONS.OTHER_REASON,     __(u'inforequests:Action:refusal_reason:OTHER_REASON')),
                )
        # Make sure we are testing all defined refusal reasons
        tested_refusal_reasons = [a for a, _ in tests]
        defined_refusal_reasons = Action.REFUSAL_REASONS._inverse.keys()
        self.assertItemsEqual(tested_refusal_reasons, defined_refusal_reasons)

        for refusal_reason, expected_display in tests:
            action = self._create_action(refusal_reason=refusal_reason)
            self.assertEqual(action.refusal_reason, [refusal_reason])
            self.assertEqual(action.get_refusal_reason_display(), expected_display)

    def test_refusal_reason_field_with_multiple_reasons(self):
        tests = (
                (Action.REFUSAL_REASONS.DOES_NOT_HAVE,    __(u'inforequests:Action:refusal_reason:DOES_NOT_HAVE')),
                (Action.REFUSAL_REASONS.DOES_NOT_PROVIDE, __(u'inforequests:Action:refusal_reason:DOES_NOT_PROVIDE')),
                (Action.REFUSAL_REASONS.DOES_NOT_CREATE,  __(u'inforequests:Action:refusal_reason:DOES_NOT_CREATE')),
                (Action.REFUSAL_REASONS.COPYRIGHT,        __(u'inforequests:Action:refusal_reason:COPYRIGHT')),
                (Action.REFUSAL_REASONS.BUSINESS_SECRET,  __(u'inforequests:Action:refusal_reason:BUSINESS_SECRET')),
                (Action.REFUSAL_REASONS.PERSONAL,         __(u'inforequests:Action:refusal_reason:PERSONAL')),
                (Action.REFUSAL_REASONS.CONFIDENTIAL,     __(u'inforequests:Action:refusal_reason:CONFIDENTIAL')),
                (Action.REFUSAL_REASONS.OTHER_REASON,     __(u'inforequests:Action:refusal_reason:OTHER_REASON')),
                )
        refusal_reason = [a for a, _ in tests]
        expected_display = u', '.join([a for _, a in tests])
        action = self._create_action(refusal_reason=refusal_reason)
        self.assertItemsEqual(action.refusal_reason, refusal_reason)
        self.assertEqual(action.get_refusal_reason_display(), expected_display)

    def test_refusal_reason_field_default_value_if_omitted(self):
        action = self._create_action(omit=[u'refusal_reason'])
        self.assertIsNone(action.refusal_reason)

    def test_last_deadline_reminder_field(self):
        dt = local_datetime_from_local(u'2014-10-05 10:33:00')
        action = self._create_action(last_deadline_reminder=dt)
        self.assertEqual(action.last_deadline_reminder, dt)

    def test_last_deadline_reminder_field_default_value_if_omitted(self):
        action = self._create_action(omit=[u'last_deadline_reminder'])
        self.assertIsNone(action.last_deadline_reminder)

    def test_advanced_to_set_relation(self):
        _, branch1, actions = self._create_inforequest_scenario(
                (u'advancement', [], [], [], []), # Advanced to 4 branches
                )
        _, (advancement, [(p1, _), (p2, _), (p3, _), (p4, _)]) = actions
        result = advancement.advanced_to_set.all()
        self.assertItemsEqual(result, [p1, p2, p3, p4])

    def test_advanced_to_set_relation_empty_by_default(self):
        action = self._create_action()
        result = action.advanced_to_set.all()
        self.assertItemsEqual(result, [])

    def test_branch_action_set_backward_relation(self):
        branch = self._create_branch()
        action1 = self._create_action(branch=branch)
        action2 = self._create_action(branch=branch)
        result = branch.action_set.all()
        self.assertItemsEqual(result, [action1, action2])

    def test_branch_action_set_backward_relation_empty_by_default(self):
        inforequest = self._create_inforequest()
        branch = self._create_branch(inforequest=inforequest)
        result = branch.action_set.all()
        self.assertItemsEqual(result, [])

    def test_message_action_backward_relation(self):
        _, branch1, (request,) = self._create_inforequest_scenario()
        self.assertEqual(request.email.action, request)

    def test_message_action_backward_relation_undefined_by_default(self):
        email = self._create_message()
        with self.assertRaisesMessage(Action.DoesNotExist, u'Message has no action.'):
            email.action

    def test_no_default_ordering(self):
        self.assertFalse(Action.objects.all().ordered)

    def test_prefetch_attachments_staticmethod(self):
        branch = self._create_branch()
        action = self._create_action(branch=branch)
        attachment1 = self._create_attachment(generic_object=action)
        attachment2 = self._create_attachment(generic_object=action)

        # Without arguments
        with self.assertNumQueries(2):
            action = Action.objects.prefetch_related(Action.prefetch_attachments()).get(pk=action.pk)
        with self.assertNumQueries(0):
            self.assertEqual(action.attachments, [attachment1, attachment2])

        # With custom path and queryset
        with self.assertNumQueries(3):
            branch = (Branch.objects
                    .prefetch_related(Branch.prefetch_actions())
                    .prefetch_related(Action.prefetch_attachments(u'actions', Attachment.objects.extra(select=dict(moo=47))))
                    .get(pk=branch.pk))
        with self.assertNumQueries(0):
            self.assertEqual(branch.actions[0].attachments, [attachment1, attachment2])
            self.assertEqual(branch.actions[0].attachments[0].moo, 47)

    def test_attachments_property(self):
        action = self._create_action()
        attachment1 = self._create_attachment(generic_object=action)
        attachment2 = self._create_attachment(generic_object=action)

        # Property is cached
        with self.assertNumQueries(1):
            action = Action.objects.get(pk=action.pk)
        with self.assertNumQueries(1):
            self.assertEqual(action.attachments, [attachment1, attachment2])
        with self.assertNumQueries(0):
            self.assertEqual(action.attachments, [attachment1, attachment2])

        # Property is prefetched with prefetch_attachments()
        with self.assertNumQueries(2):
            action = Action.objects.prefetch_related(Action.prefetch_attachments()).get(pk=action.pk)
        with self.assertNumQueries(0):
            self.assertEqual(action.attachments, [attachment1, attachment2])

    def test_previous_action_next_action_and_is_last_action_properties(self):
        branch = self._create_branch()
        first = self._create_action(branch=branch)
        second = self._create_action(branch=branch)
        self.assertIsNone(first.previous_action)
        self.assertEqual(first.next_action, second)
        self.assertFalse(first.is_last_action)
        self.assertEqual(second.previous_action, first)
        self.assertIsNone(second.next_action)
        self.assertTrue(second.is_last_action)

    def test_action_path_property(self):
        inforequest, _, _ = self._create_inforequest_scenario(u'confirmation', (u'advancement', [u'extension']), u'appeal')
        actions = Action.objects.of_inforequest(inforequest).order_by_created()
        request, confirmation, advancement, advanced_request, extension, appeal = actions
        self.assertEqual(request.action_path, [request])
        self.assertEqual(confirmation.action_path, [request, confirmation])
        self.assertEqual(advancement.action_path, [request, confirmation, advancement])
        self.assertEqual(advanced_request.action_path, [request, confirmation, advancement, advanced_request])
        self.assertEqual(extension.action_path, [request, confirmation, advancement, advanced_request, extension])
        self.assertEqual(appeal.action_path, [request, confirmation, advancement, appeal])

    def test_is_applicant_action_is_obligee_action_and_is_implicit_action_properties(self):
        tests = (                                   # Applicant, Obligee, Implicit
                (Action.TYPES.REQUEST,                True,      False,   False),
                (Action.TYPES.CLARIFICATION_RESPONSE, True,      False,   False),
                (Action.TYPES.APPEAL,                 True,      False,   False),
                (Action.TYPES.CONFIRMATION,           False,     True,    False),
                (Action.TYPES.EXTENSION,              False,     True,    False),
                (Action.TYPES.ADVANCEMENT,            False,     True,    False),
                (Action.TYPES.CLARIFICATION_REQUEST,  False,     True,    False),
                (Action.TYPES.DISCLOSURE,             False,     True,    False),
                (Action.TYPES.REFUSAL,                False,     True,    False),
                (Action.TYPES.AFFIRMATION,            False,     True,    False),
                (Action.TYPES.REVERSION,              False,     True,    False),
                (Action.TYPES.REMANDMENT,             False,     True,    False),
                (Action.TYPES.ADVANCED_REQUEST,       False,     False,   True),
                (Action.TYPES.EXPIRATION,             False,     False,   True),
                (Action.TYPES.APPEAL_EXPIRATION,      False,     False,   True),
                )
        # Make sure we are testing all defined action types
        tested_action_types = [a for a, _, _, _ in tests]
        defined_action_types = Action.TYPES._inverse.keys()
        self.assertItemsEqual(tested_action_types, defined_action_types)

        for action_type, is_applicant, is_obligee, is_implicit in tests:
            action = self._create_action(type=action_type)
            self.assertEqual(action.is_applicant_action, is_applicant)
            self.assertEqual(action.is_obligee_action, is_obligee)
            self.assertEqual(action.is_implicit_action, is_implicit)

    def test_is_by_email_property(self):
        email = self._create_message()
        action1 = self._create_action(email=email)
        action2 = self._create_action()
        self.assertTrue(action1.is_by_email)
        self.assertFalse(action2.is_by_email)

    def test_has_applicant_deadline_and_has_obligee_deadline_properties(self):
        tests = (                     # has deadline: applicant, obligee
                (Action.TYPES.REQUEST,                False,     True,  dict()),
                (Action.TYPES.CLARIFICATION_RESPONSE, False,     True,  dict()),
                (Action.TYPES.APPEAL,                 False,     True,  dict()),
                (Action.TYPES.CONFIRMATION,           False,     True,  dict()),
                (Action.TYPES.EXTENSION,              False,     True,  dict()),
                (Action.TYPES.ADVANCEMENT,            False,     False, dict()),
                (Action.TYPES.CLARIFICATION_REQUEST,  True,      False, dict()),
                (Action.TYPES.DISCLOSURE,             True,      False, dict(disclosure_level=Action.DISCLOSURE_LEVELS.NONE)),
                (Action.TYPES.DISCLOSURE,             True,      False, dict(disclosure_level=Action.DISCLOSURE_LEVELS.PARTIAL)),
                (Action.TYPES.DISCLOSURE,             False,     False, dict(disclosure_level=Action.DISCLOSURE_LEVELS.FULL)),
                (Action.TYPES.REFUSAL,                True,      False, dict()),
                (Action.TYPES.AFFIRMATION,            False,     False, dict()),
                (Action.TYPES.REVERSION,              False,     False, dict()),
                (Action.TYPES.REMANDMENT,             False,     True,  dict()),
                (Action.TYPES.ADVANCED_REQUEST,       False,     True,  dict()),
                (Action.TYPES.EXPIRATION,             True,      False, dict()),
                (Action.TYPES.APPEAL_EXPIRATION,      False,     False, dict()),
                )
        # Make sure we are testing all defined action types
        tested_action_types = set(a for a, _, _, _ in tests)
        defined_action_types = Action.TYPES._inverse.keys()
        self.assertItemsEqual(tested_action_types, defined_action_types)

        for action_type, has_applicant_deadline, has_obligee_deadline, extra_args in tests:
            action = self._create_action(type=action_type, delivered_date=naive_date(u'2010-10-05'), **extra_args)
            self.assertEqual(action.has_applicant_deadline, has_applicant_deadline)
            self.assertEqual(action.has_obligee_deadline, has_obligee_deadline)

    def test_has_obligee_deadline_missed_property(self):
        action = self._create_action(type=Action.TYPES.REQUEST, legal_date=naive_date(u'2010-10-05'), delivered_date=naive_date(u'2010-10-05'))
        timewarp.jump(local_datetime_from_local(u'2010-10-15 10:33:00'))
        self.assertFalse(action.has_obligee_deadline_missed)
        action = self._create_action(type=Action.TYPES.REQUEST, legal_date=naive_date(u'2010-10-05'), delivered_date=naive_date(u'2010-10-05'))
        timewarp.jump(local_datetime_from_local(u'2011-10-16 10:33:00'))
        self.assertTrue(action.has_obligee_deadline_missed)

    def test_has_obligee_deadline_snooze_missed_property(self):
        action = self._create_action(type=Action.TYPES.REQUEST, legal_date=naive_date(u'2010-10-05'), delivered_date=naive_date(u'2010-10-05'), snooze=naive_date(u'2010-10-22'))
        timewarp.jump(local_datetime_from_local(u'2010-10-22 10:33:00'))
        self.assertFalse(action.has_obligee_deadline_snooze_missed)
        action = self._create_action(type=Action.TYPES.REQUEST, legal_date=naive_date(u'2010-10-05'), delivered_date=naive_date(u'2010-10-05'), snooze=naive_date(u'2010-10-22'))
        timewarp.jump(local_datetime_from_local(u'2010-10-23 10:33:00'))
        self.assertTrue(action.has_obligee_deadline_snooze_missed)

    def test_has_applicant_deadline_missed_property(self):
        action = self._create_action(type=Action.TYPES.CLARIFICATION_REQUEST, legal_date=naive_date(u'2010-10-05'), delivered_date=naive_date(u'2010-10-05'))
        timewarp.jump(local_datetime_from_local(u'2010-10-12 10:33:00'))
        self.assertFalse(action.has_applicant_deadline_missed)
        action = self._create_action(type=Action.TYPES.CLARIFICATION_REQUEST, legal_date=naive_date(u'2010-10-05'),  delivered_date=naive_date(u'2010-10-05'))
        timewarp.jump(local_datetime_from_local(u'2010-10-13 10:33:00'))
        self.assertTrue(action.has_applicant_deadline_missed)

    def test_can_applicant_snooze_property(self):
        action = self._create_action(type=Action.TYPES.REQUEST, legal_date=naive_date(u'2010-10-05'), delivered_date=naive_date(u'2010-10-05'))
        timewarp.jump(local_datetime_from_local(u'2010-10-21 10:33:00'))
        self.assertFalse(action.can_applicant_snooze)
        action = self._create_action(type=Action.TYPES.REQUEST, legal_date=naive_date(u'2010-10-05'), delivered_date=naive_date(u'2010-10-05'))
        timewarp.jump(local_datetime_from_local(u'2010-10-22 10:33:00'))
        self.assertTrue(action.can_applicant_snooze)
        action = self._create_action(type=Action.TYPES.REQUEST, legal_date=naive_date(u'2010-10-05'), delivered_date=naive_date(u'2010-10-05'))
        timewarp.jump(local_datetime_from_local(u'2010-10-27 10:33:00'))
        self.assertFalse(action.can_applicant_snooze)

    def test_deadline_property(self):
        delivered_date = naive_date(u'2010-10-05')
        legal_date = naive_date(u'2010-10-04')
        tests = (
                (Action.TYPES.REQUEST,                naive_date(u'2010-10-21'), Deadline.TYPES.OBLIGEE_DEADLINE, dict()),  # 12 WD since delivered_date
                (Action.TYPES.CLARIFICATION_RESPONSE, naive_date(u'2010-10-21'), Deadline.TYPES.OBLIGEE_DEADLINE, dict()),  # 12 WD since delivered_date
                (Action.TYPES.APPEAL,                 naive_date(u'2010-10-20'), Deadline.TYPES.OBLIGEE_DEADLINE, dict()),  # 15 CD since delivered_date
                (Action.TYPES.CONFIRMATION,           naive_date(u'2010-10-21'), Deadline.TYPES.OBLIGEE_DEADLINE, dict()),  # previous action deadline
                (Action.TYPES.EXTENSION,              naive_date(u'2010-10-21'), Deadline.TYPES.OBLIGEE_DEADLINE, dict()),  # previous action deadline + extension
                (Action.TYPES.ADVANCEMENT,            None, None, dict()),
                (Action.TYPES.CLARIFICATION_REQUEST,  naive_date(u'2010-10-12'), Deadline.TYPES.APPLICANT_DEADLINE, dict()),  # 7 CD since delivered date
                (Action.TYPES.DISCLOSURE,             naive_date(u'2010-10-20'), Deadline.TYPES.APPLICANT_DEADLINE, dict(disclosure_level=Action.DISCLOSURE_LEVELS.NONE)),  # 15 CD since delivered_date
                (Action.TYPES.DISCLOSURE,             naive_date(u'2010-10-20'), Deadline.TYPES.APPLICANT_DEADLINE, dict(disclosure_level=Action.DISCLOSURE_LEVELS.PARTIAL)),  # 15 CD since delivered_date
                (Action.TYPES.DISCLOSURE,             None, None, dict(disclosure_level=Action.DISCLOSURE_LEVELS.FULL)),
                (Action.TYPES.REFUSAL,                naive_date(u'2010-10-20'), Deadline.TYPES.APPLICANT_DEADLINE, dict()),  # 15 CD since delivered_date
                (Action.TYPES.AFFIRMATION,            None, None, dict()),
                (Action.TYPES.REVERSION,              None, None, dict()),
                (Action.TYPES.REMANDMENT,             naive_date(u'2010-10-20'), Deadline.TYPES.OBLIGEE_DEADLINE, dict()),  # 8 WD since legal_date advanced by 4 WD
                (Action.TYPES.ADVANCED_REQUEST,       naive_date(u'2010-10-20'), Deadline.TYPES.OBLIGEE_DEADLINE, dict()),  # 8 WD since legal_date advanced by 4 WD
                (Action.TYPES.EXPIRATION,             naive_date(u'2010-10-19'), Deadline.TYPES.APPLICANT_DEADLINE, dict()),  # 15 CD since legal_date
                (Action.TYPES.APPEAL_EXPIRATION,      None, None, dict()),
                )
        # Make sure we are testing all defined action types
        tested_action_types = set(a for a, _, _, _ in tests)
        defined_action_types = Action.TYPES._inverse.keys()
        self.assertItemsEqual(tested_action_types, defined_action_types)

        for action_type, deadline_date, deadline_type, extra_args in tests:
            previous = self._create_action(type=Action.TYPES.REQUEST, delivered_date=delivered_date)  # Deadline for CONFIRMATION, EXTENSION
            action = self._create_action(type=action_type, delivered_date=delivered_date, legal_date=legal_date, **extra_args)
            self.assertEqual(action.deadline and action.deadline.deadline_date, deadline_date)
            self.assertEqual(action.deadline and action.deadline.type, deadline_type)

    def test_deadline_property_ignores_extension_for_non_extension_action_types(self):
        tests = (
                (Action.TYPES.REQUEST,                dict()),
                (Action.TYPES.CLARIFICATION_RESPONSE, dict()),
                (Action.TYPES.APPEAL,                 dict()),
                (Action.TYPES.CONFIRMATION,           dict()),
                (Action.TYPES.ADVANCEMENT,            dict()),
                (Action.TYPES.CLARIFICATION_REQUEST,  dict()),
                (Action.TYPES.DISCLOSURE,             dict(disclosure_level=Action.DISCLOSURE_LEVELS.NONE)),
                (Action.TYPES.DISCLOSURE,             dict(disclosure_level=Action.DISCLOSURE_LEVELS.PARTIAL)),
                (Action.TYPES.DISCLOSURE,             dict(disclosure_level=Action.DISCLOSURE_LEVELS.FULL)),
                (Action.TYPES.REFUSAL,                dict()),
                (Action.TYPES.AFFIRMATION,            dict()),
                (Action.TYPES.REVERSION,              dict()),
                (Action.TYPES.REMANDMENT,             dict()),
                (Action.TYPES.ADVANCED_REQUEST,       dict()),
                (Action.TYPES.EXPIRATION,             dict()),
                (Action.TYPES.APPEAL_EXPIRATION,      dict()),
                )
        # Make sure we are testing all defined action types (except EXTENSION)
        tested_action_types = set(a for a, _ in tests)
        defined_action_types = [a for a in Action.TYPES._inverse.keys() if a != Action.TYPES.EXTENSION]
        self.assertItemsEqual(tested_action_types, defined_action_types)

        for action_type, extra_args in tests:
            previous = self._create_action(type=Action.TYPES.REQUEST)
            action_with_extension = self._create_action(type=action_type, extension=2, **extra_args)
            action_without_extension = self._create_action(type=action_type, **extra_args)
            if action_with_extension.deadline:
                self.assertEqual(action_with_extension.deadline.deadline_date, action_without_extension.deadline.deadline_date)
            else:
                self.assertIsNone(action_with_extension.deadline)
                self.assertIsNone(action_without_extension.deadline)

    def test_deadline_property_with_extension_for_extension_action_type(self):
        self._create_action(type=Action.TYPES.REQUEST, delivered_date=naive_date(u'2010-10-05'))
        action_with_extension = self._create_action(type=Action.TYPES.EXTENSION, extension=2)
        self._create_action(type=Action.TYPES.REQUEST, delivered_date=naive_date(u'2010-10-05'))
        action_without_extension = self._create_action(type=Action.TYPES.EXTENSION)
        self.assertEqual(action_with_extension.deadline.deadline_date, naive_date(u'2010-10-25'))
        self.assertEqual(action_without_extension.deadline.deadline_date, naive_date(u'2010-10-21'))

    def test_deadline_property_none_for_action_without_deadline(self):
        action = self._create_action(type=Action.TYPES.REVERSION)
        self.assertIsNone(action.deadline)

    def test_create_classmethod(self):
        obligees = [self._create_obligee() for _ in range(3)]
        attachments = [self._create_attachment(generic_object=self.user) for _ in range(2)]
        action = Action.create(
                branch=self.branch,
                type=Action.TYPES.ADVANCEMENT,
                legal_date=local_today(),
                advanced_to=obligees,
                attachments=attachments,
                )
        self.assertEqual(action.advanced_to_set.count(), 0)
        self.assertEqual(action.attachment_set.count(), 0)
        action.save()
        self.assertEqual(action.advanced_to_set.count(), 3)
        self.assertEqual(action.attachment_set.count(), 2)

    def test_get_extended_type_display_property(self):
        tests = (
            (Action.TYPES.REQUEST,                __(u'inforequests:Action:type:REQUEST'),                dict()),
            (Action.TYPES.CLARIFICATION_RESPONSE, __(u'inforequests:Action:type:CLARIFICATION_RESPONSE'), dict()),
            (Action.TYPES.APPEAL,                 __(u'inforequests:Action:type:APPEAL'),                 dict()),
            (Action.TYPES.CONFIRMATION,           __(u'inforequests:Action:type:CONFIRMATION'),           dict()),
            (Action.TYPES.EXTENSION,              __(u'inforequests:Action:type:EXTENSION'),              dict()),
            (Action.TYPES.ADVANCEMENT,            __(u'inforequests:Action:type:ADVANCEMENT'),            dict()),
            (Action.TYPES.CLARIFICATION_REQUEST,  __(u'inforequests:Action:type:CLARIFICATION_REQUEST'),  dict()),
            (Action.TYPES.DISCLOSURE,             __(u'inforequests:Action:type:DISCLOSURE:NONE'),        dict(disclosure_level=Action.DISCLOSURE_LEVELS.NONE)),
            (Action.TYPES.DISCLOSURE,             __(u'inforequests:Action:type:DISCLOSURE:PARTIAL'),     dict(disclosure_level=Action.DISCLOSURE_LEVELS.PARTIAL)),
            (Action.TYPES.DISCLOSURE,             __(u'inforequests:Action:type:DISCLOSURE:FULL'),        dict(disclosure_level=Action.DISCLOSURE_LEVELS.FULL)),
            (Action.TYPES.REFUSAL,                __(u'inforequests:Action:type:REFUSAL'),                dict()),
            (Action.TYPES.AFFIRMATION,            __(u'inforequests:Action:type:AFFIRMATION'),            dict()),
            (Action.TYPES.REVERSION,              __(u'inforequests:Action:type:REVERSION'),              dict()),
            (Action.TYPES.REMANDMENT,             __(u'inforequests:Action:type:REMANDMENT'),             dict()),
            (Action.TYPES.ADVANCED_REQUEST,       __(u'inforequests:Action:type:ADVANCED_REQUEST'),       dict()),
            (Action.TYPES.EXPIRATION,             __(u'inforequests:Action:type:EXPIRATION'),             dict()),
            (Action.TYPES.APPEAL_EXPIRATION,      __(u'inforequests:Action:type:APPEAL_EXPIRATION'),      dict()),
        )
        # Make sure we are testing all defined action types
        tested_action_types = set(a for a, _, _ in tests)
        defined_action_types = Action.TYPES._inverse.keys()
        self.assertItemsEqual(tested_action_types, defined_action_types)
        # Make sure we are testing all defined action disclosure levels
        tested_disclosure_levels = [a.get(u'disclosure_level') for _, _, a in tests if a.get(u'disclosure_level')]
        defined_disclosure_levels = Action.DISCLOSURE_LEVELS._inverse.keys()
        self.assertItemsEqual(defined_disclosure_levels, tested_disclosure_levels)

        for action_type, expected_display, extra_args in tests:
            action = self._create_action(type=action_type, **extra_args)
            self.assertEqual(action.get_extended_type_display(), expected_display)

    def test_get_absolute_url_method(self):
        action = self._create_action()
        lang = ((u'sk', u'Slovak'), (u'en', u'English'))
        for language_code, _ in lang:
            with translation(language_code):
                self.assertEqual(action.get_absolute_url(), u'/{}/{}/{}-{}/#a{}'.format(language_code, __(u'main:urls:inforequests'), self.inforequest.slug, self.inforequest.pk, action.pk))

    def test_send_by_email_works_only_for_applicant_actions(self):
        tests = (
                (Action.TYPES.REQUEST,                True),
                (Action.TYPES.CLARIFICATION_RESPONSE, True),
                (Action.TYPES.APPEAL,                 True),
                (Action.TYPES.CONFIRMATION,           False),
                (Action.TYPES.EXTENSION,              False),
                (Action.TYPES.ADVANCEMENT,            False),
                (Action.TYPES.CLARIFICATION_REQUEST,  False),
                (Action.TYPES.DISCLOSURE,             False),
                (Action.TYPES.REFUSAL,                False),
                (Action.TYPES.AFFIRMATION,            False),
                (Action.TYPES.REVERSION,              False),
                (Action.TYPES.REMANDMENT,             False),
                (Action.TYPES.ADVANCED_REQUEST,       False),
                (Action.TYPES.EXPIRATION,             False),
                (Action.TYPES.APPEAL_EXPIRATION,      False),
                )
        # Make sure we are testing all defined action types
        tested_action_types = [a for a, _ in tests]
        defined_action_types = Action.TYPES._inverse.keys()
        self.assertItemsEqual(tested_action_types, defined_action_types)

        inforequest = self._create_inforequest()
        branch = self._create_branch(inforequest=inforequest)
        for action_type, can_send in tests:
            action = self._create_action(branch=branch, type=action_type)
            if can_send:
                with created_instances(Message.objects) as message_set:
                    action.send_by_email()
                email = message_set.get()
                self.assertEqual(email.type, Message.TYPES.OUTBOUND)
                self.assertEqual(action.email, email)
                self.assertIn(email, inforequest.email_set.all())
                rel = InforequestEmail.objects.get(email=email)
                self.assertEqual(rel.inforequest, inforequest)
                self.assertEqual(rel.type, InforequestEmail.TYPES.APPLICANT_ACTION)
            else:
                with created_instances(Message.objects) as message_set:
                    with self.assertRaisesMessage(TypeError, u'is not applicant action'):
                        action.send_by_email()
                self.assertEqual(message_set.count(), 0)

    def test_send_by_email_from_name_and_from_mail(self):
        with self.settings(INFOREQUEST_UNIQUE_EMAIL=u'{token}@example.com'):
            with mock.patch(u'chcemvediet.apps.inforequests.models.inforequest.random_readable_string', return_value=u'aaaa'):
                user = self._create_user(first_name=u'John', last_name=u'Smith')
                inforequest = self._create_inforequest(applicant=user)
                branch = self._create_branch(inforequest=inforequest)
                action = self._create_action(branch=branch)

                with created_instances(Message.objects) as message_set:
                    action.send_by_email()
                email = message_set.get()

                self.assertEqual(email.from_name, u'John Smith')
                self.assertEqual(email.from_mail, u'aaaa@example.com')

    def test_send_by_email_collected_recipients(self):
        obligee = self._create_obligee(emails=u'Obligee1 <oblige1@a.com>, oblige2@a.com')
        _, branch, _ = self._create_inforequest_scenario(obligee,
                (u'request', dict(
                    email=dict(from_name=u'Request From', from_mail=u'request-from@a.com'),
                    recipients=[
                        dict(name=u'Request To1', mail=u'request-to1@a.com', type=Recipient.TYPES.TO),
                        dict(name=u'Request To2', mail=u'request-to2@a.com', type=Recipient.TYPES.TO),
                        dict(name=u'Request Cc', mail=u'request-cc@a.com', type=Recipient.TYPES.CC),
                        dict(name=u'Request Bcc', mail=u'request-bcc@a.com', type=Recipient.TYPES.BCC),
                        ],
                    )),
                (u'refusal', dict(
                    email=dict(from_name=u'Refusal From', from_mail=u'refusal-from@a.com'),
                    recipients=[
                        dict(name=u'Refusal To', mail=u'refusal-to@a.com', type=Recipient.TYPES.TO),
                        dict(name=u'Refusal Cc', mail=u'refusal-cc@a.com', type=Recipient.TYPES.CC),
                        dict(name=u'Refusal Bcc', mail=u'refusal-bcc@a.com', type=Recipient.TYPES.BCC),
                        ],
                    )),
                )
        action = self._create_action(branch=branch)

        with created_instances(Message.objects) as message_set:
            action.send_by_email()
        email = message_set.get()

        result = [r.formatted for r in email.recipient_set.to()]
        self.assertItemsEqual(result, [
                u'Request To1 <request-to1@a.com>',
                u'Request To2 <request-to2@a.com>',
                u'Request Cc <request-cc@a.com>',
                u'Request Bcc <request-bcc@a.com>',
                # Inbound email contributes with its from address only
                u'Refusal From <refusal-from@a.com>',
                # Current obligee addresses
                u'Obligee1 <oblige1@a.com>',
                u'oblige2@a.com',
            ])

    def test_send_by_email_subject_and_content(self):
        action = self._create_action(subject=u'Subject', content=u'Content')
        with created_instances(Message.objects) as message_set:
            action.send_by_email()
        email = message_set.get()

        self.assertEqual(email.subject, u'Subject')
        self.assertEqual(email.text, u'Content')
        self.assertEqual(email.html, u'')

    def test_send_by_email_attachments(self):
        action = self._create_action()
        attachment1 = self._create_attachment(generic_object=action, name=u'filename.txt', content=u'Content')
        attachment2 = self._create_attachment(generic_object=action, name=u'filename.html', content=u'<html><body>HTML content</body></html>')

        with created_instances(Message.objects) as message_set:
            action.send_by_email()
        email = message_set.get()

        result = ((a.name, a.content, a.content_type) for a in email.attachment_set.all())
        self.assertItemsEqual(result, [
            (u'filename.txt', u'Content', u'text/plain'),
            (u'filename.html', u'<html><body>HTML content</body></html>', u'text/html'),
            ])

    def test_repr(self):
        action = self._create_action()
        self.assertEqual(repr(action), u'<Action: [{}] {}>'.format(action.pk, action.get_extended_type_display()).encode(encoding=u'utf-8'))

    def test_owned_by_query_method(self):
        user1 = self._create_user()
        user2 = self._create_user()
        inforequest1 = self._create_inforequest(applicant=user1)
        inforequest2 = self._create_inforequest(applicant=user2)
        branch1 = self._create_branch(inforequest=inforequest1)
        branch2 = self._create_branch(inforequest=inforequest2)
        actions1 = [self._create_action(branch=branch1) for _ in range(10)]
        actions2 = [self._create_action(branch=branch2) for _ in range(10)]
        self.assertItemsEqual(Action.objects.owned_by(user1), actions1)
        self.assertItemsEqual(Action.objects.owned_by(user2), actions2)

    def test_action_type_query_methods(self):
        Action.objects.all().delete()
        tests = (
                (Action.TYPES.REQUEST,                u'requests'),
                (Action.TYPES.CLARIFICATION_RESPONSE, u'clarification_responses'),
                (Action.TYPES.APPEAL,                 u'appeals'),
                (Action.TYPES.CONFIRMATION,           u'confirmations'),
                (Action.TYPES.EXTENSION,              u'extensions'),
                (Action.TYPES.ADVANCEMENT,            u'advancements'),
                (Action.TYPES.CLARIFICATION_REQUEST,  u'clarification_requests'),
                (Action.TYPES.DISCLOSURE,             u'disclosures'),
                (Action.TYPES.REFUSAL,                u'refusals'),
                (Action.TYPES.AFFIRMATION,            u'affirmations'),
                (Action.TYPES.REVERSION,              u'reversions'),
                (Action.TYPES.REMANDMENT,             u'remandments'),
                (Action.TYPES.ADVANCED_REQUEST,       u'advanced_requests'),
                (Action.TYPES.EXPIRATION,             u'expirations'),
                (Action.TYPES.APPEAL_EXPIRATION,      u'appeal_expirations'),
                )
        # Make sure we are testing all defined action types
        tested_action_types = [a for a, _ in tests]
        defined_action_types = Action.TYPES._inverse.keys()
        self.assertItemsEqual(tested_action_types, defined_action_types)

        actions = defaultdict(list)
        for i in range(3):
            for action_type, _ in tests:
                actions[action_type].append(self._create_action(type=action_type))

        for action_type, query_method in tests:
            result = getattr(Action.objects, query_method)()
            self.assertItemsEqual(result, actions[action_type])

    def test_applicant_actions_obligee_actions_and_implicit_actions_query_methods(self):
        Action.objects.all().delete()
        tests = (                                   # Applicant, Obligee, Implicit
                (Action.TYPES.REQUEST,                True,      False,   False),
                (Action.TYPES.CLARIFICATION_RESPONSE, True,      False,   False),
                (Action.TYPES.APPEAL,                 True,      False,   False),
                (Action.TYPES.CONFIRMATION,           False,     True,    False),
                (Action.TYPES.EXTENSION,              False,     True,    False),
                (Action.TYPES.ADVANCEMENT,            False,     True,    False),
                (Action.TYPES.CLARIFICATION_REQUEST,  False,     True,    False),
                (Action.TYPES.DISCLOSURE,             False,     True,    False),
                (Action.TYPES.REFUSAL,                False,     True,    False),
                (Action.TYPES.AFFIRMATION,            False,     True,    False),
                (Action.TYPES.REVERSION,              False,     True,    False),
                (Action.TYPES.REMANDMENT,             False,     True,    False),
                (Action.TYPES.ADVANCED_REQUEST,       False,     False,   True),
                (Action.TYPES.EXPIRATION,             False,     False,   True),
                (Action.TYPES.APPEAL_EXPIRATION,      False,     False,   True),
                )
        # Make sure we are testing all defined action types
        tested_action_types = [a for a, _, _, _ in tests]
        defined_action_types = Action.TYPES._inverse.keys()
        self.assertItemsEqual(tested_action_types, defined_action_types)

        applicant_actions = []
        obligee_actions = []
        implicit_actions = []
        for i in range(3):
            for action_type, is_applicant, is_obligee, is_implicit in tests:
                action = self._create_action(type=action_type)
                if is_applicant:
                    applicant_actions.append(action)
                if is_obligee:
                    obligee_actions.append(action)
                if is_implicit:
                    implicit_actions.append(action)

        applicant_result = Action.objects.applicant_actions()
        obligee_result = Action.objects.obligee_actions()
        implicit_result = Action.objects.implicit_actions()
        self.assertItemsEqual(applicant_result, applicant_actions)
        self.assertItemsEqual(obligee_result, obligee_actions)
        self.assertItemsEqual(implicit_result, implicit_actions)

    def test_by_email_and_by_smail_query_methods(self):
        Action.objects.all().delete()
        _, branch, actions = self._create_inforequest_scenario(
                u'confirmation',
                u'refusal',
                (u'appeal', dict(email=False)),
                (u'remandment', dict(email=False)),
                u'extension', # Extension is not sent
                u'expiration',
                )
        request, confirmation, refusal, appeal, remandment, extension, expiration = actions

        result_by_email = Action.objects.by_email()
        result_by_smail = Action.objects.by_smail()
        self.assertItemsEqual(result_by_email, [request, confirmation, refusal, extension])
        self.assertItemsEqual(result_by_smail, [appeal, remandment, expiration])

    def test_of_inforequest_query_method(self):
        inforequest1 = self._create_inforequest()
        inforequest2 = self._create_inforequest()
        branch1 = self._create_branch(inforequest=inforequest1)
        branch2 = self._create_branch(inforequest=inforequest2)
        actions1 = [self._create_action(branch=branch1) for _ in range(10)]
        actions2 = [self._create_action(branch=branch2) for _ in range(10)]
        self.assertItemsEqual(Action.objects.of_inforequest(inforequest1), actions1)
        self.assertItemsEqual(Action.objects.of_inforequest(inforequest2), actions2)

    def test_order_by_pk_query_method(self):
        actions = [self._create_action() for _ in range(20)]
        sample = random.sample(actions, 10)
        result = Action.objects.filter(pk__in=(d.pk for d in sample)).order_by_pk().reverse()
        self.assertEqual(list(result), sorted(sample, key=lambda d: -d.pk))

    def test_order_by_created_query_method(self):
        Action.objects.all().delete()
        dates = [
                u'2014-10-04',
                u'2014-10-05',
                u'2014-10-06', # Several with the same date, to check secondary ordering
                u'2014-10-06',
                u'2014-10-06',
                u'2014-10-06',
                u'2014-10-06',
                u'2014-11-05',
                u'2015-10-05',
                ]
        random.shuffle(dates)
        actions = []
        for date in dates:
            actions.append(self._create_action(created=naive_date(date)))
        result = Action.objects.order_by_created()
        self.assertEqual(list(result), sorted(actions, key=lambda a: (a.created, a.pk)))

    def test_before_and_after_query_methods(self):
        Action.objects.all().delete()
        datetimes = [
                u'2010-10-05 10:33:00',
                u'2010-10-06 10:33:00',
                u'2010-10-06 10:33:45',
                u'2010-10-10 10:33:00', # Several with the same date, to check secondary query
                u'2010-10-10 10:33:00',
                u'2010-10-10 10:33:00',
                u'2010-10-10 10:33:00',
                u'2010-11-10 10:33:00',
                u'2011-10-10 10:33:00',
        ]
        actions = [self._create_action(created=dt) for dt in datetimes]
        for i, a in enumerate(actions):
            self.assertItemsEqual(Action.objects.before(a), actions[:i])
            self.assertItemsEqual(Action.objects.after(a), actions[i+1:])
