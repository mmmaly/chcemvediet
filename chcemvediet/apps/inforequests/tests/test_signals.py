# vim: expandtab
# -*- coding: utf-8 -*-
import mock

from django.test import TestCase

from poleno.mail.models import Message, Recipient
from poleno.mail.signals import message_received
from poleno.utils.test import created_instances

from . import InforequestsTestCaseMixin
from ..signals import assign_email_on_message_received
from ..models import InforequestEmail

class AssignEmailOnMessageReceivedTest(InforequestsTestCaseMixin, TestCase):
    u"""
    Tests ``assign_email_on_message_received()`` event receiver.
    """

    def test_event_receiver_is_registered(self):
        self.assertIn(assign_email_on_message_received, message_received._live_receivers(sender=None))

    def test_received_message_is_assigned_and_marked_undecided(self):
        inforequest = self._create_inforequest()
        msg = self._create_message(omit=[u'received_for'])
        self._create_recipient(message=msg, mail=inforequest.unique_email)

        with created_instances(InforequestEmail.objects) as rel_set:
            assign_email_on_message_received(sender=None, message=msg)
        rel = rel_set.get()

        self.assertEqual(rel.inforequest, inforequest)
        self.assertEqual(rel.email, msg)
        self.assertEqual(rel.type, InforequestEmail.TYPES.UNDECIDED)
        self.assertItemsEqual(msg.inforequest_set.all(), [inforequest])

    def test_received_message_with_no_match_is_not_assigned(self):
        inforequest = self._create_inforequest()
        msg = self._create_message(omit=[u'received_for'])
        self._create_recipient(message=msg, mail=u'invalid@mail.com')

        with created_instances(InforequestEmail.objects) as rel_set:
            assign_email_on_message_received(sender=None, message=msg)
        self.assertFalse(rel_set.exists())

        self.assertItemsEqual(msg.inforequest_set.all(), [])

    def test_received_message_with_multiple_matches_is_not_assigned(self):
        inforequest1 = self._create_inforequest()
        inforequest2 = self._create_inforequest()
        msg = self._create_message(omit=[u'received_for'])
        self._create_recipient(message=msg, mail=inforequest1.unique_email)
        self._create_recipient(message=msg, mail=inforequest2.unique_email)

        with created_instances(InforequestEmail.objects) as rel_set:
            assign_email_on_message_received(sender=None, message=msg)
        self.assertFalse(rel_set.exists())

        self.assertItemsEqual(msg.inforequest_set.all(), [])

    def test_received_message_with_no_recipients_is_not_assigned(self):
        inforequest = self._create_inforequest()
        msg = self._create_message(omit=[u'received_for'])

        with created_instances(InforequestEmail.objects) as rel_set:
            assign_email_on_message_received(sender=None, message=msg)
        self.assertFalse(rel_set.exists())

        self.assertItemsEqual(msg.inforequest_set.all(), [])

    def test_address_is_matched_against_to_recipient(self):
        inforequest = self._create_inforequest()
        msg = self._create_message(omit=[u'received_for'])
        self._create_recipient(message=msg, mail=inforequest.unique_email, type=Recipient.TYPES.TO)

        assign_email_on_message_received(sender=None, message=msg)

        self.assertItemsEqual(msg.inforequest_set.all(), [inforequest])

    def test_address_is_matched_against_cc_recipient(self):
        inforequest = self._create_inforequest()
        msg = self._create_message(omit=[u'received_for'])
        self._create_recipient(message=msg, mail=inforequest.unique_email, type=Recipient.TYPES.CC)

        assign_email_on_message_received(sender=None, message=msg)

        self.assertItemsEqual(msg.inforequest_set.all(), [inforequest])

    def test_address_is_matched_against_bcc_recipient(self):
        inforequest = self._create_inforequest()
        msg = self._create_message(omit=[u'received_for'])
        self._create_recipient(message=msg, mail=inforequest.unique_email, type=Recipient.TYPES.BCC)

        assign_email_on_message_received(sender=None, message=msg)

        self.assertItemsEqual(msg.inforequest_set.all(), [inforequest])

    def test_address_is_matched_against_received_for(self):
        inforequest = self._create_inforequest()
        msg = self._create_message(received_for=inforequest.unique_email)

        assign_email_on_message_received(sender=None, message=msg)

        self.assertItemsEqual(msg.inforequest_set.all(), [inforequest])

    def test_address_is_matched_against_received_for_only_if_there_are_other_recipients(self):
        inforequest1 = self._create_inforequest()
        inforequest2 = self._create_inforequest()
        msg = self._create_message(received_for=inforequest1.unique_email)
        self._create_recipient(message=msg, mail=inforequest2.unique_email)

        assign_email_on_message_received(sender=None, message=msg)

        self.assertItemsEqual(msg.inforequest_set.all(), [inforequest1])

    def test_address_is_matched_against_multiple_recipients(self):
        inforequest = self._create_inforequest()
        msg = self._create_message(omit=[u'received_for'])
        self._create_recipient(message=msg, mail=inforequest.unique_email)
        self._create_recipient(message=msg, mail=u'other@example.com')

        assign_email_on_message_received(sender=None, message=msg)

        self.assertItemsEqual(msg.inforequest_set.all(), [inforequest])

    def test_recipient_address_is_matched_case_insensitive(self):
        with self.settings(INFOREQUEST_UNIQUE_EMAIL=u'{token}@eXAMplE.coM'):
            with mock.patch(u'chcemvediet.apps.inforequests.models.inforequest.random_readable_string', return_value=u'aAAa'):
                inforequest = self._create_inforequest()
        msg = self._create_message(omit=[u'received_for'])
        self._create_recipient(message=msg, mail=u'AaAA@ExampLE.com')

        assign_email_on_message_received(sender=None, message=msg)

        self.assertItemsEqual(msg.inforequest_set.all(), [inforequest])

    def test_received_for_is_matched_case_insensitive(self):
        with self.settings(INFOREQUEST_UNIQUE_EMAIL=u'{token}@eXAMplE.coM'):
            with mock.patch(u'chcemvediet.apps.inforequests.models.inforequest.random_readable_string', return_value=u'aAAa'):
                inforequest = self._create_inforequest()
        msg = self._create_message(received_for=u'AaAA@ExampLE.com')

        assign_email_on_message_received(sender=None, message=msg)

        self.assertItemsEqual(msg.inforequest_set.all(), [inforequest])

    def test_notification_email_is_sent(self):
        user = self._create_user(email=u'smith@example.com')
        inforequest = self._create_inforequest(applicant=user)
        msg = self._create_message(received_for=inforequest.unique_email)

        with self.settings(DEFAULT_FROM_EMAIL=u'info@example.com'):
            with created_instances(Message.objects) as message_set:
                assign_email_on_message_received(sender=None, message=msg)
        notification = message_set.get()

        self.assertEqual(notification.type, Message.TYPES.OUTBOUND)
        self.assertEqual(notification.from_formatted, u'info@example.com')
        self.assertEqual(notification.to_formatted, u'smith@example.com')
        self.assertEqual(notification.cc_formatted, u'')
        self.assertEqual(notification.bcc_formatted, u'')

    def test_notification_email_is_not_sent_if_inforequest_is_closed(self):
        inforequest = self._create_inforequest(closed=True)
        msg = self._create_message(received_for=inforequest.unique_email)

        with created_instances(Message.objects) as message_set:
            assign_email_on_message_received(sender=None, message=msg)
        self.assertFalse(message_set.exists())
