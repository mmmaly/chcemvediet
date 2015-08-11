# vim: expandtab
# -*- coding: utf-8 -*-
from collections import defaultdict

from django.core.urlresolvers import reverse
from django.test import TestCase

from poleno.utils.test import ViewTestCaseMixin

from .. import InforequestsTestCaseMixin

class DetailViewTest(InforequestsTestCaseMixin, ViewTestCaseMixin, TestCase):
    u"""
    Tests ``detail()`` view registered as "inforequests:detail".
    """

    def assertTemplateUsedCount(self, response, template_name, count):
        used = sum(1 for t in response.templates if t.name == template_name)
        self.assertEqual(used, count)


    def test_allowed_http_methods(self):
        inforequest, _, _ = self._create_inforequest_scenario()
        allowed = [u'HEAD', u'GET']
        self.assert_allowed_http_methods(allowed, reverse(u'inforequests:detail', args=(inforequest.pk,)))

    def test_anonymous_user_is_redirected(self):
        inforequest, _, _ = self._create_inforequest_scenario()
        self.assert_anonymous_user_is_redirected(reverse(u'inforequests:detail', args=(inforequest.pk,)))

    def test_authenticated_user_gets_inforequest_detail(self):
        inforequest, _, _ = self._create_inforequest_scenario()
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'inforequests/detail.html')

    def test_invalid_inforequest_returns_404_not_found(self):
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(47,)))
        self.assertEqual(response.status_code, 404)

    def test_inforequest_owned_by_another_user_returns_404_not_found(self):
        inforequest, _, _ = self._create_inforequest_scenario(self.user2)
        self._login_user(self.user1)
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.pk,)))
        self.assertEqual(response.status_code, 404)

    def test_inforequest_with_single_branch(self):
        inforequest, _, _ = self._create_inforequest_scenario(u'confirmation', u'extension')
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.pk,)))

        # Three actions in single branch
        self.assertTemplateUsedCount(response, u'inforequests/detail_branch.html', 1)
        self.assertTemplateUsedCount(response, u'inforequests/detail_action.html', 3)

    def test_inforequest_with_single_branch_related_models_are_prefetched_before_render(self):
        inforequest, _, _ = self._create_inforequest_scenario(u'confirmation', u'extension')
        self._login_user()
        with self.assertQueriesDuringRender([]):
            response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.pk,)))

    def test_inforequest_with_multiple_branches(self):
        inforequest, _, _ = self._create_inforequest_scenario(
                u'confirmation',
                (u'advancement',
                    [u'disclosure'],
                    [u'refusal'],
                    [u'confirmation', (u'advancement', [u'refusal'])]),
                )
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.pk,)))

        # Total 12 actions in 5 branches.
        #  -- Main Branch:
        #      -- request
        #      -- confirmation
        #      -- advancement
        #          -- branch:
        #              -- advanced_request
        #              -- disclosure
        #          -- branch:
        #              -- advanced_request
        #              -- refusal
        #          -- branch:
        #              -- advanced_request
        #              -- confirmation
        #              -- advancement:
        #                  -- branch:
        #                      -- advanced_request
        #                      -- refusal
        self.assertTemplateUsedCount(response, u'inforequests/detail_branch.html', 5)
        self.assertTemplateUsedCount(response, u'inforequests/detail_action.html', 12)

    def test_inforequest_with_multiple_branches_related_models_are_prefetched_before_render(self):
        inforequest, _, _ = self._create_inforequest_scenario(
                u'confirmation',
                (u'advancement',
                    [u'disclosure'],
                    [u'refusal'],
                    [u'confirmation', (u'advancement', [u'refusal'])]),
                )
        self._login_user()
        with self.assertQueriesDuringRender([]):
            response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.pk,)))

    def test_inforequest_with_undecided_email(self):
        inforequest, _, _ = self._create_inforequest_scenario()
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)

        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.pk,)))

        # User can decide
        self.assertTemplateUsed(response, u'inforequests/detail_decide.html')
        self.assertTemplateUsed(response, u'inforequests/detail_undecided.html')
        # User may not act
        self.assertTemplateNotUsed(response, u'inforequests/detail_add_smail.html')
        self.assertTemplateNotUsed(response, u'inforequests/detail_new_action.html')

        templates = defaultdict(list)
        for template in response.templates:
            templates[template.name].append(template)

        self.assertTemplateUsedCount(response, u'inforequests/detail_email.html', 3)

    def test_inforequest_with_undecided_email_related_models_are_prefetched_before_render(self):
        inforequest, _, _ = self._create_inforequest_scenario()
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)

        self._login_user()
        with self.assertQueriesDuringRender([]):
            response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.pk,)))

    def test_inforequest_without_undecided_email(self):
        inforequest, _, _ = self._create_inforequest_scenario()
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.pk,)))

        # There is nothing to decide
        self.assertTemplateNotUsed(response, u'inforequests/detail_decide.html')
        self.assertTemplateNotUsed(response, u'inforequests/detail_undecided.html')
        # User may act
        self.assertTemplateUsed(response, u'inforequests/detail_add_smail.html')
        self.assertTemplateUsed(response, u'inforequests/detail_new_action.html')

    def test_inforequest_without_undecided_email_related_models_are_prefetched_before_render(self):
        inforequest, _, _ = self._create_inforequest_scenario()
        self._login_user()
        with self.assertQueriesDuringRender([]):
            response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.pk,)))

    def test_closed_inforequest_with_undecided_email(self):
        inforequest, _, _ = self._create_inforequest_scenario(dict(closed=True))
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)

        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.pk,)))

        # Inforequest is closed, user may do nothing
        self.assertTemplateNotUsed(response, u'inforequests/detail_decide.html')
        self.assertTemplateNotUsed(response, u'inforequests/detail_undecided.html')
        self.assertTemplateNotUsed(response, u'inforequests/detail_add_smail.html')
        self.assertTemplateNotUsed(response, u'inforequests/detail_new_action.html')

    def test_closed_inforequest_without_undecided_email(self):
        inforequest, _, _ = self._create_inforequest_scenario(dict(closed=True))
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.pk,)))

        # Inforequest is closed, user may do nothing
        self.assertTemplateNotUsed(response, u'inforequests/detail_decide.html')
        self.assertTemplateNotUsed(response, u'inforequests/detail_undecided.html')
        self.assertTemplateNotUsed(response, u'inforequests/detail_add_smail.html')
        self.assertTemplateNotUsed(response, u'inforequests/detail_new_action.html')

    def test_closed_inforequest_related_models_are_prefetched_before_render(self):
        inforequest, _, _ = self._create_inforequest_scenario(dict(closed=True))
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)

        self._login_user()
        with self.assertQueriesDuringRender([]):
            response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.pk,)))
