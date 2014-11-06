# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.test import TestCase

from poleno.utils.test import ViewTestCaseMixin

from .. import InforequestsTestCaseMixin
from ...models import InforequestDraft

class DeleteDraftViewTest(InforequestsTestCaseMixin, ViewTestCaseMixin, TestCase):
    u"""
    Tests ``delete_draft()`` view registered as "inforequests:delete_draft".
    """

    def test_allowed_http_methods(self):
        draft = self._create_inforequest_draft()
        allowed = [u'POST']
        self.assert_allowed_http_methods(allowed, reverse(u'inforequests:delete_draft', args=(draft.pk,)))

    def test_post_with_anonymous_user_is_redirected(self):
        draft = self._create_inforequest_draft()
        self.assert_anonymous_user_is_redirected(reverse(u'inforequests:delete_draft', args=(draft.pk,)), method=u'POST')

    def test_post_deletes_draft(self):
        draft = self._create_inforequest_draft()
        self._login_user()
        response = self.client.post(reverse(u'inforequests:delete_draft', args=(draft.pk,)))
        self.assertFalse(InforequestDraft.objects.filter(pk=draft.pk).exists())

    def test_post_is_redirected_to_inforequests_index(self):
        draft = self._create_inforequest_draft()
        self._login_user()
        response = self.client.post(reverse(u'inforequests:delete_draft', args=(draft.pk,)), follow=True)
        self.assertRedirects(response, reverse(u'inforequests:index'))

    def test_post_with_invalid_draft_returns_404_not_found(self):
        self._login_user()
        response = self.client.post(reverse(u'inforequests:delete_draft', args=(47,)))
        self.assertEqual(response.status_code, 404)

    def test_post_with_draft_owned_by_another_user_returns_404_not_found(self):
        draft = self._create_inforequest_draft(applicant=self.user2)
        self._login_user(self.user1)
        response = self.client.post(reverse(u'inforequests:delete_draft', args=(draft.pk,)))
        self.assertEqual(response.status_code, 404)
