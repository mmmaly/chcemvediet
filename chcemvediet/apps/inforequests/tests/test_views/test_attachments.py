# vim: expandtab
# -*- coding: utf-8 -*-
import json
import datetime

from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.http import JsonResponse

from poleno.attachments.models import Attachment
from poleno.utils.date import utc_now
from poleno.utils.test import created_instances

from . import CustomTestCase

class UploadAttachmentViewTest(CustomTestCase):
    u"""
    Tests ``upload_attachment()`` view registered as "inforequests:upload_attachment".
    """

    def test_allowed_http_methods(self):
        url = reverse(u'inforequests:upload_attachment')

        allowed = [u'POST']
        self.assert_allowed_http_methods(allowed, url)

    def test_non_ajax_request_returns_400_bad_request(self):
        url = reverse(u'inforequests:upload_attachment')

        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_anonymous_user_gets_403_firbidden(self):
        url = reverse(u'inforequests:upload_attachment')

        response = self.client.post(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_gets_200_ok(self):
        self._login_user()
        url = reverse(u'inforequests:upload_attachment')

        response = self.client.post(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_upload_file_uploads_file_and_attaches_it_to_session(self):
        self._login_user(self.user1)
        data = {u'files': ContentFile(u'Content', name=u'filename.txt')}
        url = reverse(u'inforequests:upload_attachment')

        with created_instances(Attachment.objects) as attachment_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        attachment = attachment_set.get()

        self.assertEqual(attachment.generic_object, self._get_session())
        self.assertEqual(attachment.name, u'filename.txt')
        self.assertEqual(attachment.content_type, u'text/plain')
        self.assertAlmostEqual(attachment.created, utc_now(), delta=datetime.timedelta(seconds=10))
        self.assertEqual(attachment.size, 7)
        self.assertEqual(attachment.content, u'Content')

    def test_upload_file_returns_json_with_uploaded_file(self):
        self._login_user()
        data = {u'files': ContentFile(u'Content', name=u'filename.txt')}
        url = reverse(u'inforequests:upload_attachment')

        with created_instances(Attachment.objects) as attachment_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        attachment = attachment_set.get()

        self.assertIs(type(response), JsonResponse)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {u'files': [{
                u'url': reverse(u'inforequests:download_attachment', args=(attachment.pk,)),
                u'pk': attachment.pk,
                u'name': u'filename.txt', u'size': 7,
            }]})

class DownloadAttachmentViewTest(CustomTestCase):
    u"""
    Tests ``download_attachment()`` view registered as "inforequests:download_attachment".
    """

    def test_allowed_http_methods(self):
        self._login_user()
        attachment = self._create_attachment()
        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))

        allowed = [u'HEAD', u'GET']
        self.assert_allowed_http_methods(allowed, url)

    def test_anonymous_user_gets_403_firbidden(self):
        self._login_user()
        attachment = self._create_attachment()
        self._logout_user()

        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_gets_200_ok(self):
        self._login_user()
        attachment = self._create_attachment()
        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_invalid_attachment_returns_404_not_found(self):
        self._login_user()
        url = reverse(u'inforequests:download_attachment', args=(47,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_attachment_owned_by_user_returns_404_not_found(self):
        self._login_user(self.user1)
        attachment = self._create_attachment(generic_object=self.user1)
        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_attachment_owned_by_another_session_returns_404_not_found(self):
        self._login_user()
        attachment = self._create_attachment()
        self._logout_user()

        self._login_user()
        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_attachment_owned_by_session_returns_200_ok(self):
        self._login_user(self.user1)
        attachment = self._create_attachment(generic_object=self._get_session())
        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_attachment_assigned_to_email_assigned_to_inforequest_owned_by_another_user_returns_404_not_found(self):
        self._login_user(self.user1)
        inforequest, _, _ = self._create_inforequest_scenario(self.user2)
        email, _ = self._create_inforequest_email(inforequest=inforequest)
        attachment = self._create_attachment(generic_object=email)
        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_attachment_assigned_to_email_assigned_to_inforequest_owned_by_user_returns_200_ok(self):
        self._login_user(self.user1)
        inforequest, _, _ = self._create_inforequest_scenario(self.user1)
        email, _ = self._create_inforequest_email(inforequest=inforequest)
        attachment = self._create_attachment(generic_object=email)
        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_attachment_assigned_to_inforequest_draft_owned_by_another_user_returns_404_not_found(self):
        self._login_user(self.user1)
        draft = self._create_inforequest_draft(applicant=self.user2)
        attachment = self._create_attachment(generic_object=draft)
        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_attachment_assigned_to_inforequest_draft_owned_by_user_returns_200_ok(self):
        self._login_user(self.user1)
        draft = self._create_inforequest_draft(applicant=self.user1)
        attachment = self._create_attachment(generic_object=draft)
        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_attachment_assigned_to_action_of_inforequest_owned_by_another_user_returns_404_not_found(self):
        self._login_user(self.user1)
        _, _, (request,) = self._create_inforequest_scenario(self.user2)
        attachment = self._create_attachment(generic_object=request)
        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_attachment_assigned_to_action_of_inforequest_owned_by_user_returns_200_ok(self):
        self._login_user(self.user1)
        _, _, (request,) = self._create_inforequest_scenario(self.user1)
        attachment = self._create_attachment(generic_object=request)
        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_attachment_assigned_to_action_draft_of_inforequest_owned_by_another_user_returns_404_not_found(self):
        self._login_user(self.user1)
        inforequest, _, _ = self._create_inforequest_scenario(self.user2)
        draft = self._create_action_draft(inforequest=inforequest)
        attachment = self._create_attachment(generic_object=draft)
        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_attachment_assigned_to_action_draft_of_inforequest_owned_by_user_returns_200_ok(self):
        self._login_user(self.user1)
        inforequest, _, _ = self._create_inforequest_scenario(self.user1)
        draft = self._create_action_draft(inforequest=inforequest)
        attachment = self._create_attachment(generic_object=draft)
        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_download_returns_file_content(self):
        self._login_user()
        attachment = self._create_attachment(content=u'Content')
        url = reverse(u'inforequests:download_attachment', args=(attachment.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(u''.join(response.streaming_content), u'Content')
