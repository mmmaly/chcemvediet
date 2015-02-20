# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.test import TestCase

from poleno.utils.test import ViewTestCaseMixin

from .. import InforequestsTestCaseMixin

class IndexViewTest(InforequestsTestCaseMixin, ViewTestCaseMixin, TestCase):
    u"""
    Tests ``index()`` view registered as "inforequests:index".
    """

    def test_allowed_http_methods(self):
        allowed = [u'HEAD', u'GET']
        self.assert_allowed_http_methods(allowed, reverse(u'inforequests:index'))

    def test_anonymous_user_is_redirected(self):
        self.assert_anonymous_user_is_redirected(reverse(u'inforequests:index'))

    def test_authenticated_user_gets_inforequest_index(self):
        self._login_user()
        response = self.client.get(reverse(u'inforequests:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'inforequests/index.html')

    def test_user_gets_only_his_inforequests_and_drafts(self):
        drafts1 = [self._create_inforequest_draft(applicant=self.user1) for i in range(5)]
        drafts2 = [self._create_inforequest_draft(applicant=self.user2) for i in range(3)]
        inforequests1 = [self._create_inforequest(applicant=self.user1) for i in range(4)]
        inforequests2 = [self._create_inforequest(applicant=self.user2) for i in range(5)]
        closed1 = [self._create_inforequest(applicant=self.user1, closed=True) for i in range(3)]
        closed2 = [self._create_inforequest(applicant=self.user2, closed=True) for i in range(3)]

        self._login_user(self.user1)
        response = self.client.get(reverse(u'inforequests:index'))
        self.assertEqual(response.status_code, 200)
        self.assertItemsEqual(response.context[u'inforequests'], inforequests1)
        self.assertItemsEqual(response.context[u'drafts'], drafts1)
        self.assertItemsEqual(response.context[u'closed_inforequests'], closed1)

    def test_with_user_with_no_his_inforequests_nor_drafts(self):
        drafts2 = [self._create_inforequest_draft(applicant=self.user2) for i in range(3)]
        inforequests2 = [self._create_inforequest(applicant=self.user2) for i in range(5)]
        closed2 = [self._create_inforequest(applicant=self.user2, closed=True) for i in range(3)]

        self._login_user(self.user1)
        response = self.client.get(reverse(u'inforequests:index'))
        self.assertEqual(response.status_code, 200)
        self.assertItemsEqual(response.context[u'inforequests'], [])
        self.assertItemsEqual(response.context[u'drafts'], [])
        self.assertItemsEqual(response.context[u'closed_inforequests'], [])
