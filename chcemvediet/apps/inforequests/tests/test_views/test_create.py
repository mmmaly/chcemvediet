# vim: expandtab
# -*- coding: utf-8 -*-
import re
import mock

from django.core.urlresolvers import reverse
from django.utils.encoding import force_text
from django.test import TestCase

from poleno.mail.models import Message
from poleno.utils.test import created_instances, ViewTestCaseMixin

from .. import InforequestsTestCaseMixin
from ... import forms
from ...models import InforequestDraft, Inforequest, Action

class CreateViewTest(InforequestsTestCaseMixin, ViewTestCaseMixin, TestCase):
    u"""
    Tests ``create()`` view registered as "inforequests:create" and
    "inforequests:create_from_draft".
    """

    def _create_post_data(self, omit=(), **kwargs):
        defaults = {
                u'obligee': u'Default Testing Name',
                u'subject': u'Default Testing Subject',
                u'content': u'Default Testing Content',
                u'attachments': u',,,',
                }
        translate = {
                u'obligee': u'inforequestform-obligee',
                u'subject': u'inforequestform-subject',
                u'content': u'inforequestform-content',
                u'attachments': u'inforequestform-attachments',
                }
        defaults.update(kwargs)
        for key in omit:
            defaults.pop(key)
        defaults = {translate.get(k, k): v for k, v in defaults.iteritems()}
        return defaults


    def test_allowed_http_methods(self):
        allowed = [u'HEAD', u'GET', u'POST']
        self.assert_allowed_http_methods(allowed, reverse(u'inforequests:create'))

    def test_anonymous_user_is_redirected(self):
        self.assert_anonymous_user_is_redirected(reverse(u'inforequests:create'))

    def test_user_without_verified_email_gets_error_page_and_has_confirmation_email_sent(self):
        user = self._create_user(email=u'smith@example.com', email_verified=False)
        self._login_user(user)
        with self.settings(DEFAULT_FROM_EMAIL=u'Something <from@example.com>'):
            with created_instances(Message.objects) as query_set:
                response = self.client.get(reverse(u'inforequests:create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'account/verified_email_required.html')

        # Check confirmation email
        msg = query_set.get()
        self.assertTemplateUsed(response, u'account/email/email_confirmation_subject.txt')
        self.assertTemplateUsed(response, u'account/email/email_confirmation_message.txt')
        self.assertEqual(msg.type, Message.TYPES.OUTBOUND)
        self.assertEqual(msg.from_formatted, u'Something <from@example.com>')
        self.assertEqual(msg.to_formatted, u'smith@example.com')
        self.assertIn(reverse(u'account_email_verification_sent'), msg.text)

    def test_user_with_verified_email_gets_inforequest_create(self):
        self._login_user()
        response = self.client.get(reverse(u'inforequests:create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'inforequests/create.html')

    def test_user_with_verified_email_gets_inforequest_create_from_draft(self):
        draft = self._create_inforequest_draft()
        self._login_user()
        response = self.client.get(reverse(u'inforequests:create_from_draft', args=(draft.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'inforequests/create.html')

    def test_get_without_draft_shows_form_with_initial_values(self):
        self._login_user()
        response = self.client.get(reverse(u'inforequests:create'))

        form = response.context[u'form']
        self.assertIsInstance(form, forms.InforequestForm)
        self.assertIsNone(form[u'obligee'].value())
        self.assertEqual(force_text(form[u'subject'].value()), u'Information request')
        self.assertRegexpMatches(force_text(form[u'content'].value()), u'^Lorem ipsum')
        self.assertIsNone(form[u'attachments'].value())

    def test_get_with_draft_shows_form_with_values_from_draft(self):
        draft = self._create_inforequest_draft(applicant=self.user1, obligee=self.obligee1, subject=u'Subject', content=u'Content')
        attachment1 = self._create_attachment(generic_object=draft)
        attachment2 = self._create_attachment(generic_object=draft)

        self._login_user(self.user1)
        response = self.client.get(reverse(u'inforequests:create_from_draft', args=(draft.pk,)))

        form = response.context[u'form']
        self.assertIsInstance(form, forms.InforequestForm)
        self.assertEqual(form[u'obligee'].value(), self.obligee1)
        self.assertEqual(form[u'subject'].value(), u'Subject')
        self.assertEqual(form[u'content'].value(), u'Content')
        self.assertItemsEqual(form[u'attachments'].value(), [attachment1, attachment2])

    def test_get_with_invalid_draft_returns_404_not_found(self):
        self._login_user()
        response = self.client.get(reverse(u'inforequests:create_from_draft', args=(47,)))
        self.assertEqual(response.status_code, 404)

    def test_get_with_draft_owned_by_another_user_returns_404_not_found(self):
        draft = self._create_inforequest_draft(applicant=self.user2)
        self._login_user(self.user1)
        response = self.client.get(reverse(u'inforequests:create_from_draft', args=(draft.pk,)))
        self.assertEqual(response.status_code, 404)

    def test_post_with_draft_button_and_valid_data_creates_new_draft_instance(self):
        obligee = self._create_obligee(name=u'Obligee')
        attachment1 = self._create_attachment(generic_object=self.user1)
        attachment2 = self._create_attachment(generic_object=self.user1)
        data = self._create_post_data(button=u'draft', obligee=u'Obligee',
                subject=u'Subject', content=u'Content',
                attachments=u'%s,%s' % (attachment1.pk, attachment2.pk))

        self._login_user(self.user1)
        with created_instances(InforequestDraft.objects) as query_set:
            response = self.client.post(reverse(u'inforequests:create'), data)

        draft = query_set.get()
        self.assertEqual(draft.applicant, self.user1)
        self.assertEqual(draft.obligee, obligee)
        self.assertEqual(draft.subject, u'Subject')
        self.assertEqual(draft.content, u'Content')
        self.assertItemsEqual(draft.attachment_set.all(), [attachment1, attachment2])

    def test_post_with_draft_button_and_valid_data_updates_existing_draft_instance(self):
        obligee = self._create_obligee(name=u'New Obligee')
        attachment1 = self._create_attachment(generic_object=self.user1)
        attachment2 = self._create_attachment(generic_object=self.user1)
        draft = self._create_inforequest_draft(applicant=self.user1, obligee=self.obligee1, subject=u'Old Subject', content=u'Old Content')
        attachment3 = self._create_attachment(generic_object=draft)
        data = self._create_post_data(button=u'draft', obligee=u'New Obligee',
                subject=u'New Subject', content=u'New Content',
                attachments=u'%s,%s' % (attachment1.pk, attachment3.pk))

        self._login_user(self.user1)
        with created_instances(InforequestDraft.objects) as query_set:
            response = self.client.post(reverse(u'inforequests:create_from_draft', args=(draft.pk,)), data)

        self.assertFalse(query_set.exists())
        draft = InforequestDraft.objects.get(pk=draft.pk)
        self.assertEqual(draft.applicant, self.user1)
        self.assertEqual(draft.obligee, obligee)
        self.assertEqual(draft.subject, u'New Subject')
        self.assertEqual(draft.content, u'New Content')
        self.assertItemsEqual(draft.attachment_set.all(), [attachment1, attachment3])

    def test_post_with_draft_button_and_valid_data_redirects_to_inforequests_index(self):
        data = self._create_post_data(button=u'draft')
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data, follow=True)
        self.assertRedirects(response, reverse(u'inforequests:index'))

    def test_post_with_draft_button_and_invalid_data_does_not_create_new_draft_instance(self):
        data = self._create_post_data(button=u'draft', obligee=u'Invalid')
        self._login_user(self.user1)
        with created_instances(InforequestDraft.objects) as query_set:
            response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertFalse(query_set.exists())

    def test_post_with_draft_button_and_invalid_data_does_not_update_existing_draft_instance(self):
        draft = self._create_inforequest_draft(applicant=self.user1, subject=u'Old Subject')
        data = self._create_post_data(button=u'draft', obligee=u'Invalid')
        self._login_user(self.user1)
        with created_instances(InforequestDraft.objects) as query_set:
            response = self.client.post(reverse(u'inforequests:create_from_draft', args=(draft.pk,)), data)
        self.assertFalse(query_set.exists())
        draft = InforequestDraft.objects.get(pk=draft.pk)
        self.assertEqual(draft.subject, u'Old Subject')

    def test_post_with_draft_button_and_invalid_data_redraws_form(self):
        data = self._create_post_data(button=u'draft', obligee=u'Invalid')
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'inforequests/create.html')

    def test_post_with_submit_button_and_valid_data_creates_inforequest(self):
        obligee = self._create_obligee(name=u'Obligee')
        attachment1 = self._create_attachment(generic_object=self.user1)
        attachment2 = self._create_attachment(generic_object=self.user1)
        data = self._create_post_data(button=u'submit', obligee=u'Obligee',
                subject=u'Subject', content=u'Content',
                attachments=u'%s,%s' % (attachment1.pk, attachment2.pk))

        self._login_user(self.user1)
        with created_instances(Inforequest.objects) as query_set:
            response = self.client.post(reverse(u'inforequests:create'), data)

        inforequest = query_set.get()
        paperwork = inforequest.paperwork
        action = paperwork.last_action
        self.assertEqual(inforequest.applicant, self.user1)
        self.assertItemsEqual(inforequest.paperwork_set.all(), [paperwork])
        self.assertEqual(paperwork.obligee, obligee)
        self.assertItemsEqual(paperwork.action_set.all(), [action])
        self.assertEqual(action.type, Action.TYPES.REQUEST)
        self.assertEqual(action.subject, u'Subject')
        self.assertEqual(action.content, u'Content')
        self.assertItemsEqual(action.attachment_set.all(), [attachment1, attachment2])

    def test_post_with_submit_button_and_valid_data_sends_inforequest_email(self):
        user = self._create_user(first_name=u'John', last_name=u'Smith')
        data = self._create_post_data(button=u'submit')

        self._login_user(user)
        with self.settings(INFOREQUEST_UNIQUE_EMAIL=u'{token}@example.com'):
            with mock.patch(u'chcemvediet.apps.inforequests.models.random_readable_string', return_value=u'aaaa'):
                with created_instances(Message.objects) as message_set:
                    with created_instances(Inforequest.objects) as inforequest_set:
                        response = self.client.post(reverse(u'inforequests:create'), data)

        email = message_set.get()
        self.assertEqual(email.type, Message.TYPES.OUTBOUND)
        self.assertEqual(email.from_formatted, u'John Smith <aaaa@example.com>')

        inforequest = inforequest_set.get()
        self.assertItemsEqual(inforequest.email_set.all(), [email])
        self.assertEqual(inforequest.paperwork.last_action.email, email)

    def test_post_with_submit_button_and_valid_data_deletes_draft(self):
        draft = self._create_inforequest_draft(applicant=self.user1)
        data = self._create_post_data(button=u'submit')
        self._login_user(self.user1)
        response = self.client.post(reverse(u'inforequests:create_from_draft', args=(draft.pk,)), data)
        self.assertFalse(InforequestDraft.objects.filter(pk=draft.pk).exists())

    def test_post_with_submit_button_and_valid_data_redirects_to_inforequests_detail(self):
        data = self._create_post_data(button=u'submit')
        self._login_user(self.user1)
        with created_instances(Inforequest.objects) as query_set:
            response = self.client.post(reverse(u'inforequests:create'), data, follow=True)
        inforequest = query_set.get()
        self.assertRedirects(response, reverse(u'inforequests:detail', args=(inforequest.pk,)))

    def test_post_with_submit_button_and_invalid_data_does_not_create_inforequest(self):
        data = self._create_post_data(button=u'submit', obligee=u'invalid')
        self._login_user()
        with created_instances(Inforequest.objects) as query_set:
            response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertFalse(query_set.exists())

    def test_post_with_submit_button_and_invalid_data_does_not_send_inforequest_email(self):
        data = self._create_post_data(button=u'submit', obligee=u'invalid')
        self._login_user()
        with created_instances(Message.objects) as message_set:
            response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertFalse(message_set.exists())

    def test_post_with_submit_button_and_invalid_data_does_not_delete_draft(self):
        draft = self._create_inforequest_draft(applicant=self.user1)
        data = self._create_post_data(button=u'submit', obligee=u'invalid')
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create_from_draft', args=(draft.pk,)), data)
        self.assertTrue(InforequestDraft.objects.filter(pk=draft.pk).exists())

    def test_post_with_submit_button_and_invalid_data_redraws_form(self):
        data = self._create_post_data(button=u'submit', obligee=u'invalid')
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'inforequests/create.html')

    def test_post_with_invalid_button_returns_400_bad_request(self):
        data = self._create_post_data(button=u'invalid')
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertEqual(response.status_code, 400)

    def test_obligee_field_is_required_for_submit_button(self):
        data = self._create_post_data(button=u'submit', omit=[u'obligee'])
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertFormError(response, u'form', u'obligee', 'This field is required.')

    def test_obligee_field_is_not_required_for_draft_button(self):
        data = self._create_post_data(button=u'draft', omit=[u'obligee'])
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertIsNone(response.context)

    def test_obligee_field_with_invalid_obligee_name_is_invalid(self):
        data = self._create_post_data(button=u'draft', obligee=u'invalid')
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertFormError(response, u'form', u'obligee', 'Invalid obligee name. Select one form the menu.')

    def test_subject_field_is_required_for_submit_button(self):
        data = self._create_post_data(button=u'submit', omit=[u'subject'])
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertFormError(response, u'form', u'subject', 'This field is required.')

    def test_subject_field_is_not_required_for_draft_button(self):
        data = self._create_post_data(button=u'draft', omit=[u'subject'])
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertIsNone(response.context)

    def test_subject_field_max_length(self):
        data = self._create_post_data(button=u'draft', subject=u'x'*256)
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertFormError(response, u'form', u'subject', 'Ensure this value has at most 255 characters (it has 256).')

    def test_content_field_is_required_for_submit_button(self):
        data = self._create_post_data(button=u'submit', omit=[u'content'])
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertFormError(response, u'form', u'content', 'This field is required.')

    def test_content_field_is_not_required_for_draft_button(self):
        data = self._create_post_data(button=u'draft', omit=[u'content'])
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertIsNone(response.context)

    def test_attachments_field_is_not_required_for_submit_button(self):
        data = self._create_post_data(button=u'submit', omit=[u'attachments'])
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertIsNone(response.context)

    def test_attachments_field_is_not_required_for_draft_button(self):
        data = self._create_post_data(button=u'draft', omit=[u'attachments'])
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertIsNone(response.context)

    def test_attachments_field_with_invalid_attachment_is_invalid(self):
        data = self._create_post_data(button=u'draft', attachments=u',47,')
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertFormError(response, u'form', u'attachments', 'Invalid attachments.')

    def test_attachments_field_with_attachment_owned_by_another_user_is_invalid(self):
        attachment = self._create_attachment(generic_object=self.user2)
        data = self._create_post_data(button=u'draft', attachments=u',%s,' % attachment.pk)
        self._login_user(self.user1)
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertFormError(response, u'form', u'attachments', 'Invalid attachments.')

    def test_attachments_field_with_attachment_assigned_to_another_draft_is_invalid(self):
        draft1 = self._create_inforequest_draft()
        draft2 = self._create_inforequest_draft()
        attachment = self._create_attachment(generic_object=draft2)
        data = self._create_post_data(button=u'draft', attachments=u',%s,' % attachment.pk)
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create_from_draft', args=(draft1.pk,)), data)
        self.assertFormError(response, u'form', u'attachments', 'Invalid attachments.')

    def test_attachments_field_with_attachment_owned_by_user_is_valid(self):
        attachment = self._create_attachment()
        data = self._create_post_data(button=u'draft', attachments=u',%s,' % attachment.pk)
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create'), data)
        self.assertIsNone(response.context)

    def test_attachments_field_with_attachment_assigned_to_used_draft_is_valid(self):
        draft = self._create_inforequest_draft()
        attachment = self._create_attachment(generic_object=draft)
        data = self._create_post_data(button=u'draft', attachments=u',%s,' % attachment.pk)
        self._login_user()
        response = self.client.post(reverse(u'inforequests:create_from_draft', args=(draft.pk,)), data)
        self.assertIsNone(response.context)

    def test_attachments_field_upload_and_download_url_funcs(self):
        draft = self._create_inforequest_draft(applicant=self.user1)
        attachment = self._create_attachment(generic_object=draft)

        self._login_user()
        response = self.client.get(reverse(u'inforequests:create_from_draft', args=(draft.pk,)))
        self.assertEqual(response.status_code, 200)

        form = response.context[u'form']
        rendered = form[u'attachments'].as_widget()
        upload_regexp = u'<input [^>]*type="file" [^>]*data-url="%s"[^>]*>' % re.escape(reverse(u'inforequests:upload_attachment'))
        download_regexp = u'<a href="%s">' % re.escape(reverse(u'inforequests:download_attachment', args=(attachment.pk,)))
        self.assertRegexpMatches(rendered, upload_regexp)
        self.assertRegexpMatches(rendered, download_regexp)
