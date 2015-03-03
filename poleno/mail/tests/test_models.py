# vim: expandtab
# -*- coding: utf-8 -*-
import random

from django.db import IntegrityError
from django.test import TestCase

from poleno.attachments.models import Attachment
from poleno.utils.date import utc_now, utc_datetime_from_local

from . import MailTestCaseMixin
from ..models import Message, Recipient

class MessageModelTest(MailTestCaseMixin, TestCase):
    u"""
    Tests ``Message`` model.
    """

    def test_create_instance(self):
        msg = self._create_message()
        self.assertIsNotNone(msg.pk)

    def test_type_field(self):
        tests = (
                (Message.TYPES.INBOUND, u'Inbound'),
                (Message.TYPES.OUTBOUND, u'Outbound'),
                )
        # Make sure we are testing all defined message types
        tested_types = [a for a, _ in tests]
        defined_types = Message.TYPES._inverse.keys()
        self.assertItemsEqual(tested_types, defined_types)

        for message_type, expected_display in tests:
            msg = self._create_message(type=message_type)
            self.assertEqual(msg.type, message_type)
            self.assertEqual(msg.get_type_display(), expected_display)

    def test_type_field_may_not_be_ommited(self):
        with self.assertRaisesMessage(IntegrityError, u'mail_message.type may not be NULL'):
            msg = self._create_message(omit=[u'type'])

    def test_processed_field_with_explicit_value(self):
        msg = self._create_message(processed=utc_datetime_from_local(u'2014-10-04 13:22:12'))
        self.assertEqual(msg.processed, utc_datetime_from_local(u'2014-10-04 13:22:12'))

    def test_processed_field_with_default_value_if_ommited(self):
        msg = self._create_message(omit=[u'processed'])
        self.assertIsNone(msg.processed)

    def test_from_name_and_from_mail_fields_with_explicit_values(self):
        msg = self._create_message(from_name=u'From Name', from_mail=u'from@example.com')
        self.assertEqual(msg.from_name, u'From Name')
        self.assertEqual(msg.from_mail, u'from@example.com')

    def test_from_name_and_from_mail_fields_with_default_values_if_ommited(self):
        msg = self._create_message(omit=[u'from_name', u'from_mail'])
        self.assertEqual(msg.from_name, u'')
        self.assertEqual(msg.from_mail, u'')

    def test_received_for_field_with_explicit_value(self):
        msg = self._create_message(received_for=u'received_for@example.com')
        self.assertEqual(msg.received_for, u'received_for@example.com')

    def test_received_for_field_with_default_value_if_ommited(self):
        msg = self._create_message(omit=[u'received_for'])
        self.assertEqual(msg.received_for, u'')

    def test_subject_text_and_html_fields_with_explicit_values(self):
        msg = self._create_message(subject=u'Subject', text=u'Text', html=u'<b>HTML</b>')
        self.assertEqual(msg.subject, u'Subject')
        self.assertEqual(msg.text, u'Text')
        self.assertEqual(msg.html, u'<b>HTML</b>')

    def test_subject_text_and_html_fields_with_default_values_if_ommited(self):
        msg = self._create_message(omit=[u'subject', u'text', u'html'])
        self.assertEqual(msg.subject, u'')
        self.assertEqual(msg.text, u'')
        self.assertEqual(msg.html, u'')

    def test_headers_field_with_explicit_value(self):
        msg = self._create_message(headers={u'X-Some-Header': u'Some Value'})
        self.assertEqual(msg.headers, {u'X-Some-Header': u'Some Value'})

    def test_headers_field_with_default_value_if_ommited(self):
        msg = self._create_message(omit=[u'headers'])
        self.assertEqual(msg.headers, {})

    def test_attachment_set_empty_by_default(self):
        msg = self._create_message()
        self.assertItemsEqual(msg.attachment_set.all(), [])

    def test_attachment_set_with_added_items(self):
        msg = self._create_message()
        attch1 = self._create_attachment(generic_object=msg)
        attch2 = self._create_attachment(generic_object=msg)
        self.assertItemsEqual(msg.attachment_set.all(), [attch1, attch2])

    def test_recipient_set_empty_by_default(self):
        msg = self._create_message()
        self.assertItemsEqual(msg.recipient_set.all(), [])

    def test_recipient_set_with_added_items(self):
        msg = self._create_message()
        rcpt1 = self._create_recipient(message=msg)
        rcpt2 = self._create_recipient(message=msg)
        self.assertItemsEqual(msg.recipient_set.all(), [rcpt1, rcpt2])

    def test_default_ordering_by_processed_then_pk(self):
        dates = [
                u'2010-11-06 10:19:11',
                u'2014-10-06 10:19:11',
                u'2014-10-05 10:20:11',
                u'2014-10-05 11:20:11',
                u'2014-10-05 13:20:11',
                u'2014-10-06 13:20:11',
                u'2014-10-06 13:20:12.000000', # Many same dates to ckeck secondary sorting by pk
                u'2014-10-06 13:20:12.000000',
                u'2014-10-06 13:20:12.000000',
                u'2014-10-06 13:20:12.000000',
                u'2014-10-06 13:20:12.000000',
                u'2014-10-06 13:20:12.000000',
                u'2014-10-06 13:20:12.000000',
                u'2014-10-06 13:20:12.000001',
                u'2014-10-06 13:20:12.000001',
                u'2014-10-06 13:20:12.000001',
                u'2014-10-06 13:20:12.000001',
                u'2014-10-06 13:20:12.000001',
                u'2014-10-06 13:20:12.000001',
                u'2014-11-06 10:19:11',
                ]
        random.shuffle(dates)
        msgs = [self._create_message(processed=utc_datetime_from_local(d)) for d in dates]
        result = Message.objects.all()
        self.assertEqual(list(result), sorted(msgs, key=lambda o: (o.processed, o.pk)))

    def test_from_formatted_property(self):
        msg = self._create_message(from_name=u'From Name', from_mail=u'mail@example.com')
        self.assertEqual(msg.from_formatted, u'From Name <mail@example.com>')

    def test_from_formatted_property_with_ommited_name(self):
        msg = self._create_message(from_mail=u'mail@example.com', omit=[u'from_name'])
        self.assertEqual(msg.from_formatted, u'mail@example.com')

    def test_from_formatted_property_with_ommited_mail(self):
        msg = self._create_message(from_name=u'From Name', omit=[u'from_mail'])
        self.assertEqual(msg.from_formatted, u'From Name <>')

    def test_from_formatted_property_with_ommited_both_name_and_mail(self):
        msg = self._create_message(omit=[u'from_name', u'from_mail'])
        self.assertEqual(msg.from_formatted, u'')

    def test_from_formatted_property_with_at_symbol_in_name(self):
        msg = self._create_message(from_name=u'bad@name.com', from_mail=u'mail@example.com')
        self.assertEqual(msg.from_formatted, u'"bad@name.com" <mail@example.com>')

    def test_from_formatted_property_with_quote_symbol_in_name(self):
        msg = self._create_message(from_name=u'bad "name"', from_mail=u'mail@example.com')
        self.assertEqual(msg.from_formatted, u'"bad \\"name\\"" <mail@example.com>')

    def test_from_formatted_property_with_comma_in_name(self):
        msg = self._create_message(from_name=u'Smith, John', from_mail=u'mail@example.com')
        self.assertEqual(msg.from_formatted, u'"Smith, John" <mail@example.com>')

    def test_from_formatted_property_setter(self):
        msg = self._create_message(from_name=u'From Name', from_mail=u'mail@example.com')
        msg.from_formatted = u'Another Name <another@example.com>'
        self.assertEqual(msg.from_name, u'Another Name')
        self.assertEqual(msg.from_mail, u'another@example.com')

    def test_from_formatted_property_setter_without_name(self):
        msg = self._create_message(from_name=u'From Name', from_mail=u'mail@example.com')
        msg.from_formatted = u'another@example.com'
        self.assertEqual(msg.from_name, u'')
        self.assertEqual(msg.from_mail, u'another@example.com')

    def test_prefetch_attachments_staticmethod(self):
        msg = self._create_message()
        attch1 = self._create_attachment(generic_object=msg)
        attch2 = self._create_attachment(generic_object=msg)
        rcpt1 = self._create_recipient(message=msg)
        rcpt2 = self._create_recipient(message=msg)

        # Without arguments
        with self.assertNumQueries(2):
            msg = Message.objects.prefetch_related(Message.prefetch_attachments()).get(pk=msg.pk)
        with self.assertNumQueries(0):
            self.assertItemsEqual(msg.attachments, [attch1, attch2])

        # With custom path and queryset
        with self.assertNumQueries(2):
            rcpt = (Recipient.objects
                    .select_related(u'message')
                    .prefetch_related(Message.prefetch_attachments(u'message', Attachment.objects.extra(select=dict(moo=47))))
                    .get(pk=rcpt1.pk))
        with self.assertNumQueries(0):
            self.assertItemsEqual(rcpt.message.attachments, [attch1, attch2])
            self.assertEqual(rcpt.message.attachments[0].moo, 47)

    def test_attachments_property(self):
        msg = self._create_message()
        attch1 = self._create_attachment(generic_object=msg)
        attch2 = self._create_attachment(generic_object=msg)

        # Property is cached
        with self.assertNumQueries(1):
            msg = Message.objects.get(pk=msg.pk)
        with self.assertNumQueries(1):
            self.assertItemsEqual(msg.attachments, [attch1, attch2])
        with self.assertNumQueries(0):
            self.assertItemsEqual(msg.attachments, [attch1, attch2])

        # Property is prefetched with prefetch_attachments()
        with self.assertNumQueries(2):
            msg = Message.objects.prefetch_related(Message.prefetch_attachments()).get(pk=msg.pk)
        with self.assertNumQueries(0):
            self.assertItemsEqual(msg.attachments, [attch1, attch2])

    def test_prefetch_recipients_staticmethod(self):
        msg = self._create_message()
        attch1 = self._create_attachment(generic_object=msg)
        attch2 = self._create_attachment(generic_object=msg)
        rcpt1 = self._create_recipient(message=msg)
        rcpt2 = self._create_recipient(message=msg)

        # Without arguments
        with self.assertNumQueries(2):
            msg = Message.objects.prefetch_related(Message.prefetch_recipients()).get(pk=msg.pk)
        with self.assertNumQueries(0):
            self.assertItemsEqual(msg.recipients, [rcpt1, rcpt2])

        # With custom path and queryset
        with self.assertNumQueries(2):
            rcpt = (Recipient.objects
                    .select_related(u'message')
                    .prefetch_related(Message.prefetch_recipients(u'message', Recipient.objects.extra(select=dict(moo=47))))
                    .get(pk=rcpt1.pk))
        with self.assertNumQueries(0):
            self.assertItemsEqual(rcpt.message.recipients, [rcpt1, rcpt2])
            self.assertEqual(rcpt.message.recipients[0].moo, 47)

    def test_recipients_property(self):
        msg = self._create_message()
        rcpt1 = self._create_recipient(message=msg)
        rcpt2 = self._create_recipient(message=msg)

        # Property is cached
        with self.assertNumQueries(1):
            msg = Message.objects.get(pk=msg.pk)
        with self.assertNumQueries(1):
            self.assertItemsEqual(msg.recipients, [rcpt1, rcpt2])
        with self.assertNumQueries(0):
            self.assertItemsEqual(msg.recipients, [rcpt1, rcpt2])

        # Property is prefetched with prefetch_recipients()
        with self.assertNumQueries(2):
            msg = Message.objects.prefetch_related(Message.prefetch_recipients()).get(pk=msg.pk)
        with self.assertNumQueries(0):
            self.assertItemsEqual(msg.recipients, [rcpt1, rcpt2])

    def test_recipients_to_cc_and_bcc_properties(self):
        msg = self._create_message()
        to1 = self._create_recipient(message=msg, type=Recipient.TYPES.TO)
        to2 = self._create_recipient(message=msg, type=Recipient.TYPES.TO)
        to3 = self._create_recipient(message=msg, type=Recipient.TYPES.TO)
        cc1 = self._create_recipient(message=msg, type=Recipient.TYPES.CC)
        cc2 = self._create_recipient(message=msg, type=Recipient.TYPES.CC)
        bcc = self._create_recipient(message=msg, type=Recipient.TYPES.BCC)

        # Properies are cached
        with self.assertNumQueries(1):
            msg = Message.objects.get(pk=msg.pk)
        with self.assertNumQueries(3):
            self.assertItemsEqual(msg.recipients_to, [to1, to2, to3])
            self.assertItemsEqual(msg.recipients_cc, [cc1, cc2])
            self.assertItemsEqual(msg.recipients_bcc, [bcc])
        with self.assertNumQueries(0):
            self.assertItemsEqual(msg.recipients_to, [to1, to2, to3])
            self.assertItemsEqual(msg.recipients_cc, [cc1, cc2])
            self.assertItemsEqual(msg.recipients_bcc, [bcc])

        # Properies use cached recipients property
        with self.assertNumQueries(1):
            msg = Message.objects.get(pk=msg.pk)
        with self.assertNumQueries(1):
            msg.recipients
        with self.assertNumQueries(0):
            self.assertItemsEqual(msg.recipients_to, [to1, to2, to3])
            self.assertItemsEqual(msg.recipients_cc, [cc1, cc2])
            self.assertItemsEqual(msg.recipients_bcc, [bcc])

        # Properties are prefetched with prefetch_recipients()
        with self.assertNumQueries(2):
            msg = Message.objects.prefetch_related(Message.prefetch_recipients()).get(pk=msg.pk)
        with self.assertNumQueries(0):
            self.assertItemsEqual(msg.recipients_to, [to1, to2, to3])
            self.assertItemsEqual(msg.recipients_cc, [cc1, cc2])
            self.assertItemsEqual(msg.recipients_bcc, [bcc])

    def test_to_cc_and_bcc_formatted_properties(self):
        msg = self._create_message()
        to1 = self._create_recipient(message=msg, name=u'First', mail=u'first@a.com', type=Recipient.TYPES.TO)
        to2 = self._create_recipient(message=msg, name=u'Second', mail=u'second@a.com', type=Recipient.TYPES.TO)
        to3 = self._create_recipient(message=msg, name=u'Third', mail=u'third@a.com', type=Recipient.TYPES.TO)
        cc1 = self._create_recipient(message=msg, name=u'CC First', mail=u'ccfirst@a.com', type=Recipient.TYPES.CC)
        cc2 = self._create_recipient(message=msg, name=u'CC Second', mail=u'ccsecond@a.com', type=Recipient.TYPES.CC)
        bcc = self._create_recipient(message=msg, name=u'BCC First', mail=u'bccfirst@a.com', type=Recipient.TYPES.BCC)
        self.assertEqual(msg.to_formatted, u'First <first@a.com>, Second <second@a.com>, Third <third@a.com>')
        self.assertEqual(msg.cc_formatted, u'CC First <ccfirst@a.com>, CC Second <ccsecond@a.com>')
        self.assertEqual(msg.bcc_formatted, u'BCC First <bccfirst@a.com>')

    def test_repr(self):
        msg = self._create_message()
        self.assertEqual(repr(msg), u'<Message: %s>' % msg.pk)

    def test_inbound_and_outbound_query_methods(self):
        obj1 = self._create_message(type=Message.TYPES.INBOUND)
        obj2 = self._create_message(type=Message.TYPES.INBOUND)
        obj3 = self._create_message(type=Message.TYPES.OUTBOUND)
        result = Message.objects.inbound()
        self.assertItemsEqual(result, [obj1, obj2])
        result = Message.objects.outbound()
        self.assertItemsEqual(result, [obj3])

    def test_processed_and_not_processed_query_methods(self):
        obj1 = self._create_message(omit=[u'processed'])
        obj2 = self._create_message(omit=[u'processed'])
        obj3 = self._create_message(processed=utc_now())
        result = Message.objects.processed()
        self.assertItemsEqual(result, [obj3])
        result = Message.objects.not_processed()
        self.assertItemsEqual(result, [obj1, obj2])

class RecipientModelTest(MailTestCaseMixin, TestCase):
    u"""
    Tests ``Recipient`` model.
    """

    def test_create_instance(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg)
        self.assertIsNotNone(rcpt.pk)

    def test_message_field_with_explicit_value(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg)
        self.assertEqual(rcpt.message, msg)

    def test_message_field_may_not_be_ommited(self):
        msg = self._create_message()
        with self.assertRaisesMessage(IntegrityError, u'mail_recipient.message_id may not be NULL'):
            rcpt = self._create_recipient(omit=[u'message'])

    def test_name_and_mail_fields_with_explicit_values(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, name=u'Rcpt Name', mail=u'mail@example.com')
        self.assertEqual(rcpt.name, u'Rcpt Name')
        self.assertEqual(rcpt.mail, u'mail@example.com')

    def test_name_and_mail_fields_with_default_values_if_ommited(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, omit=[u'name', u'mail'])
        self.assertEqual(rcpt.name, u'')
        self.assertEqual(rcpt.mail, u'')

    def test_type_field(self):
        tests = (
                (Recipient.TYPES.TO,  u'To'),
                (Recipient.TYPES.CC,  u'Cc'),
                (Recipient.TYPES.BCC, u'Bcc'),
                )
        # Make sure we are testing all defined recipient types
        tested_types = [a for a, _ in tests]
        defined_types = Recipient.TYPES._inverse.keys()
        self.assertItemsEqual(tested_types, defined_types)

        msg = self._create_message()
        for recipient_type, expected_display in tests:
            rcpt = self._create_recipient(message=msg, type=recipient_type)
            self.assertEqual(rcpt.type, recipient_type)
            self.assertEqual(rcpt.get_type_display(), expected_display)

    def test_type_field_may_not_be_ommited(self):
        msg = self._create_message()
        with self.assertRaisesMessage(IntegrityError, u'mail_recipient.type may not be NULL'):
            rcpt = self._create_recipient(message=msg, omit=['type'])

    def test_status_field_with_explicit_value(self):
        tests = (
                (Recipient.STATUSES.INBOUND,   u'Inbound'),
                (Recipient.STATUSES.UNDEFINED, u'Undefined'),
                (Recipient.STATUSES.QUEUED,    u'Queued'),
                (Recipient.STATUSES.REJECTED,  u'Rejected'),
                (Recipient.STATUSES.INVALID,   u'Invalid'),
                (Recipient.STATUSES.SENT,      u'Sent'),
                (Recipient.STATUSES.DELIVERED, u'Delivered'),
                (Recipient.STATUSES.OPENED,    u'Opened'),
                )
        # Make sure we are testing all defined recipient statuses
        tested_statuses = [a for a, _ in tests]
        defined_statuses = Recipient.STATUSES._inverse.keys()
        self.assertItemsEqual(tested_statuses, defined_statuses)

        msg = self._create_message()
        for recipient_status, expected_display in tests:
            rcpt = self._create_recipient(message=msg, status=recipient_status)
            self.assertEqual(rcpt.status, recipient_status)
            self.assertEqual(rcpt.get_status_display(), expected_display)

    def test_status_field_may_not_be_ommited(self):
        msg = self._create_message()
        with self.assertRaisesMessage(IntegrityError, u'mail_recipient.status may not be NULL'):
            rcpt = self._create_recipient(message=msg, omit=['status'])

    def test_status_details_and_remote_id_with_explicit_values(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, status_details=u'status_details', remote_id=u'remote_id')
        self.assertEqual(rcpt.status_details, u'status_details')
        self.assertEqual(rcpt.remote_id, u'remote_id')

    def test_status_details_and_remote_id_with_default_values_if_ommited(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, omit=[u'status_details', u'remote_id'])
        self.assertEqual(rcpt.status_details, u'')
        self.assertEqual(rcpt.remote_id, u'')

    def test_message_recipient_set_backward_relation(self):
        msg = self._create_message()
        rcpt1 = self._create_recipient(message=msg)
        rcpt2 = self._create_recipient(message=msg)
        result = msg.recipient_set.all()
        self.assertItemsEqual(result, [rcpt1, rcpt2])

    def test_message_recipient_set_backward_relation_empty_by_default(self):
        msg = self._create_message()
        result = msg.recipient_set.all()
        self.assertItemsEqual(result, [])

    def test_default_ordering_by_pk(self):
        msg = self._create_message()
        rcpts = [self._create_recipient(message=msg) for i in range(10)]
        rcpts = random.sample(rcpts, 5)
        result = msg.recipient_set.filter(pk__in=[r.pk for r in rcpts])
        self.assertEqual(list(result), sorted(rcpts, key=lambda r: r.pk))

    def test_formatted_property(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, name=u'Rcpt Name', mail=u'mail@example.com')
        self.assertEqual(rcpt.formatted, u'Rcpt Name <mail@example.com>')

    def test_formatted_property_with_ommited_name(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, mail=u'mail@example.com', omit=[u'name'])
        self.assertEqual(rcpt.formatted, u'mail@example.com')

    def test_formatted_property_with_at_comma_and_quote_symbols_in_name(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, name=u'Smith, John "@goo"', mail=u'mail@example.com')
        self.assertEqual(rcpt.formatted, u'"Smith, John \\"@goo\\"" <mail@example.com>')

    def test_formatted_property_setter(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, name=u'Rcpt Name', mail=u'mail@example.com')
        rcpt.formatted = u'Another Name <another@example.com>'
        self.assertEqual(rcpt.name, u'Another Name')
        self.assertEqual(rcpt.mail, u'another@example.com')

    def test_formatted_property_setter_without_name(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, name=u'Rcpt Name', mail=u'mail@example.com')
        rcpt.formatted = u'another@example.com'
        self.assertEqual(rcpt.name, u'')
        self.assertEqual(rcpt.mail, u'another@example.com')

    def test_repr(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg)
        self.assertEqual(repr(rcpt), u'<Recipient: %s>' % rcpt.pk)

    def test_to_cc_and_bcc_query_methods(self):
        msg = self._create_message()
        to1 = self._create_recipient(message=msg, type=Recipient.TYPES.TO)
        to2 = self._create_recipient(message=msg, type=Recipient.TYPES.TO)
        to3 = self._create_recipient(message=msg, type=Recipient.TYPES.TO)
        cc1 = self._create_recipient(message=msg, type=Recipient.TYPES.CC)
        cc2 = self._create_recipient(message=msg, type=Recipient.TYPES.CC)
        bcc = self._create_recipient(message=msg, type=Recipient.TYPES.BCC)
        result = msg.recipient_set.to()
        self.assertItemsEqual(result, [to1, to2, to3])
        result = msg.recipient_set.cc()
        self.assertItemsEqual(result, [cc1, cc2])
        result = msg.recipient_set.bcc()
        self.assertItemsEqual(result, [bcc])
