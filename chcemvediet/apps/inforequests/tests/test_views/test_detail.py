# vim: expandtab
# -*- coding: utf-8 -*-
from django.test import TestCase

from poleno.timewarp import timewarp
from poleno.utils.date import local_datetime_from_local, naive_date
from poleno.utils.templatetags.poleno.utils import url
from poleno.utils.test import ViewTestCaseMixin
from poleno.utils.urls import reverse

from .. import InforequestsTestCaseMixin
from .. import render_query_patterns


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
        self.assert_allowed_http_methods(allowed, reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))

    def test_owner_gets_inforequest_detail(self):
        inforequest, _, _ = self._create_inforequest_scenario({u'published': False})
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'inforequests/detail/detail.html')

    def test_invalid_inforequest_returns_404_not_found(self):
        response = self.client.get(reverse(u'inforequests:detail', args=(47,)))
        self.assertEqual(response.status_code, 404)

    def test_published_inforequest_owned_by_another_user_returns_inforequest_detail(self):
        inforequest, _, _ = self._create_inforequest_scenario(self.user, {u'published': True})
        self._login_user(self.user1)
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'inforequests/detail/detail.html')

    def test_published_inforequest_returns_inforequest_detail_to_anonymous_user(self):
        inforequest, _, _ = self._create_inforequest_scenario({u'published': True})
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'inforequests/detail/detail.html')

    def test_non_published_inforequest_owned_by_another_user_returns_404_not_found(self):
        inforequest, _, _ = self._create_inforequest_scenario(self.user, {u'published': False})
        self._login_user(self.user1)
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        self.assertEqual(response.status_code, 404)

    def test_non_published_inforequest_returns_404_not_found_to_anonymous_user(self):
        inforequest, _, _ = self._create_inforequest_scenario({u'published': False})
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        self.assertEqual(response.status_code, 404)

    def test_invalid_inforequest_slug_is_redirected_to_inforequest_detail(self):
        inforequest, _, _ = self._create_inforequest_scenario({u'published': True})
        response1 = self.client.get(reverse(u'inforequests:detail', args=(u'invalid', inforequest.pk)))
        response2 = self.client.get(reverse(u'inforequests:detail', args=(inforequest.pk,)))
        self.assertRedirects(response1, reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        self.assertRedirects(response2, reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))

    def test_inforequest_with_single_branch(self):
        inforequest, _, _ = self._create_inforequest_scenario(u'confirmation', u'reversion')
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))

        # Three actions in single branch
        self.assertTemplateUsedCount(response, u'inforequests/detail/branch/main.html', 1)
        self.assertTemplateUsedCount(response, u'inforequests/detail/action/main.html', 3)

    def test_inforequest_with_single_branch_related_models_are_prefetched_before_render(self):
        inforequest, _, _ = self._create_inforequest_scenario(u'confirmation', u'reversion')
        self._login_user()
        with self.assertQueriesDuringRender(render_query_patterns.base):
            response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))

    def test_inforequest_with_multiple_branches(self):
        inforequest, _, _ = self._create_inforequest_scenario(
                u'confirmation',
                (u'advancement',
                    [u'disclosure'],
                    [u'refusal'],
                    [u'confirmation', (u'advancement', [u'refusal'])]),
                )
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))

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
        self.assertTemplateUsedCount(response, u'inforequests/detail/branch/main.html', 1)
        self.assertTemplateUsedCount(response, u'inforequests/detail/branch/sub.html', 4)
        self.assertTemplateUsedCount(response, u'inforequests/detail/action/main.html', 12)

    def test_inforequest_with_multiple_branches_related_models_are_prefetched_before_render(self):
        inforequest, _, _ = self._create_inforequest_scenario(
                u'confirmation',
                (u'advancement',
                    [u'disclosure'],
                    [u'refusal'],
                    [u'confirmation', (u'advancement', [u'refusal'])]),
                )
        self._login_user()
        with self.assertQueriesDuringRender(render_query_patterns.base):
            response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))

    def test_inforequest_with_undecided_email(self):
        inforequest, _, _ = self._create_inforequest_scenario()
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)

        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))

        # User can decide
        self.assertTemplateUsed(response, u'inforequests/detail/texts/add_email.html')
        # User may not act
        self.assertTemplateNotUsed(response, u'inforequests/detail/texts/add_smail.html')

    def test_inforequest_with_undecided_email_related_models_are_prefetched_before_render(self):
        inforequest, _, _ = self._create_inforequest_scenario()
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)

        self._login_user()
        with self.assertQueriesDuringRender(render_query_patterns.base):
            response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))

    def test_inforequest_without_undecided_email(self):
        inforequest, _, _ = self._create_inforequest_scenario()
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))

        # There is nothing to decide
        self.assertTemplateNotUsed(response, u'inforequests/detail/texts/add_email.html')
        # User may act
        self.assertTemplateUsed(response, u'inforequests/detail/texts/add_smail.html')

    def test_inforequest_without_undecided_email_related_models_are_prefetched_before_render(self):
        inforequest, _, _ = self._create_inforequest_scenario()
        self._login_user()
        with self.assertQueriesDuringRender(render_query_patterns.base):
            response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))

    def test_closed_inforequest_with_undecided_email(self):
        inforequest, _, _ = self._create_inforequest_scenario(dict(closed=True))
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)

        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))

        # Inforequest is closed, user may do nothing
        self.assertTemplateNotUsed(response, u'inforequests/detail/texts/add_email.html')
        self.assertTemplateNotUsed(response, u'inforequests/detail/texts/add_smail.html')

    def test_closed_inforequest_without_undecided_email(self):
        inforequest, _, _ = self._create_inforequest_scenario(dict(closed=True))
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))

        # Inforequest is closed, user may do nothing
        self.assertTemplateNotUsed(response, u'inforequests/detail/texts/add_email.html')
        self.assertTemplateNotUsed(response, u'inforequests/detail/texts/add_smail.html')

    def test_closed_inforequest_related_models_are_prefetched_before_render(self):
        inforequest, _, _ = self._create_inforequest_scenario(dict(closed=True))
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)
        self._create_inforequest_email(inforequest=inforequest)

        self._login_user()
        with self.assertQueriesDuringRender(render_query_patterns.base):
            response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))

    def test_inforequest_with_undecided_email_cannot_applicant_snooze(self):
        inforequest, _, _ = self._create_inforequest_scenario(
                (u'request', dict(legal_date=naive_date(u'2010-10-05'), delivered_date=naive_date(u'2010-10-05')))
        )
        self._create_inforequest_email(inforequest=inforequest)
        timewarp.jump(local_datetime_from_local(u'2010-10-22 10:33:00'))
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        snooze_url = url(u'inforequests:snooze', action=inforequest.last_action)
        self.assertTrue(inforequest.last_action.can_applicant_snooze)
        self.assertNotContains(response, u'type="button" action="{}"'.format(snooze_url))

    def test_inforequest_without_undecided_email_can_applicant_snooze(self):
        inforequest, _, _ = self._create_inforequest_scenario(
                (u'request', dict(legal_date=naive_date(u'2010-10-05'), delivered_date=naive_date(u'2010-10-05')))
        )
        timewarp.jump(local_datetime_from_local(u'2010-10-22 10:33:00'))
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        snooze_url = url(u'inforequests:snooze', action=inforequest.last_action)
        self.assertTrue(inforequest.last_action.can_applicant_snooze)
        self.assertContains(response, u'type="button" action="{}"'.format(snooze_url))

    def test_closed_inforequest_without_undecided_email_cannot_applicant_snooze(self):
        inforequest, _, _ = self._create_inforequest_scenario(dict(closed=True),
                (u'request', dict(legal_date=naive_date(u'2010-10-05'), delivered_date=naive_date(u'2010-10-05')))
        )
        timewarp.jump(local_datetime_from_local(u'2010-10-22 10:33:00'))
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        snooze_url = url(u'inforequests:snooze', action=inforequest.last_action)
        self.assertTrue(inforequest.last_action.can_applicant_snooze)
        self.assertNotContains(response, u'type="button" action="{}"'.format(snooze_url))

    def test_inforequest_with_undecided_email_applicant_cannot_add_clarification_response(self):
        inforequest, _, _ = self._create_inforequest_scenario(u'clarification_request')
        self._create_inforequest_email(inforequest=inforequest)
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        clarification_response_url = url(u'inforequests:clarification_response', branch=inforequest.main_branch)
        self.assertTrue(inforequest.can_add_clarification_response)
        self.assertNotContains(response, u'href="{}"'.format(clarification_response_url))

    def test_inforequest_without_undecided_email_applicant_can_add_clarification_response(self):
        inforequest, _, _ = self._create_inforequest_scenario(u'clarification_request')
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        clarification_response_url = url(u'inforequests:clarification_response', branch=inforequest.main_branch)
        self.assertTrue(inforequest.can_add_clarification_response)
        self.assertContains(response, u'href="{}"'.format(clarification_response_url))

    def test_closed_inforequest_without_undecided_email_applicant_cannot_add_clarification_response(self):
        inforequest, _, _ = self._create_inforequest_scenario(dict(closed=True), u'clarification_request')
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        clarification_response_url = url(u'inforequests:clarification_response', branch=inforequest.main_branch)
        self.assertTrue(inforequest.can_add_clarification_response)
        self.assertNotContains(response, u'href="{}"'.format(clarification_response_url))

    def test_inforequest_with_undecided_email_applicant_cannot_add_appeal(self):
        inforequest, _, _ = self._create_inforequest_scenario(u'advancement')
        self._create_inforequest_email(inforequest=inforequest)
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        appeal_url = url(u'inforequests:appeal', branch=inforequest.main_branch)
        self.assertTrue(inforequest.can_add_appeal)
        self.assertNotContains(response, u'href="{}"'.format(appeal_url))

    def test_inforequest_without_undecided_email_applicant_can_add_appeal(self):
        inforequest, _, _ = self._create_inforequest_scenario(u'advancement')
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        appeal_url = url(u'inforequests:appeal', branch=inforequest.main_branch)
        self.assertTrue(inforequest.can_add_appeal)
        self.assertContains(response, u'href="{}"'.format(appeal_url))

    def test_closed_inforequest_without_undecided_email_applicant_cannot_add_appeal(self):
        inforequest, _, _ = self._create_inforequest_scenario(dict(closed=True), u'advancement')
        self._login_user()
        response = self.client.get(reverse(u'inforequests:detail', args=(inforequest.slug, inforequest.pk)))
        appeal_url = url(u'inforequests:appeal', branch=inforequest.main_branch)
        self.assertTrue(inforequest.can_add_appeal)
        self.assertNotContains(response, u'href="{}"'.format(appeal_url))
