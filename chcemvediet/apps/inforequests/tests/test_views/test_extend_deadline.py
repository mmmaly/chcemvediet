# vim: expandtab
# -*- coding: utf-8 -*-
import json
import mock

from django.core.urlresolvers import reverse
from django.http import JsonResponse

from poleno.timewarp import timewarp
from poleno.utils.date import local_datetime_from_local
from poleno.utils.misc import Bunch
from poleno.utils.test import patch_with_exception

from ...forms import ExtendDeadlineForm
from ...models import Action
from . import CustomTestCase
from .common_tests import CommonDecoratorsTests, OwnedNotClosedInforequestArgTests


class ExtendDeadlineViewTest(
        CommonDecoratorsTests,
        OwnedNotClosedInforequestArgTests,
        CustomTestCase,
        ):
    u"""
    Tests ``extend_deadline()`` view registered as "inforequests:extend_deadline".
    """

    def _create_scenario(self, **kwargs):
        res = Bunch()

        created = kwargs.pop(u'created', u'2010-03-07 10:33:00')
        timewarp.jump(local_datetime_from_local(created))

        inforequest_args = kwargs.pop(u'inforequest_args', [])
        inforequest_scenario = kwargs.pop(u'inforequest_scenario', [u'request'])
        inforequest_args = list(inforequest_args) + list(inforequest_scenario)
        res.inforequest, res.branch, res.actions = self._create_inforequest_scenario(*inforequest_args)
        res.action = res.branch.last_action

        now = kwargs.pop(u'now', u'2010-07-08 10:33:00')
        timewarp.jump(local_datetime_from_local(now))

        self.assertEqual(kwargs, {})
        self._scenario = res
        return res

    def _create_url(self, scenario, **kwargs):
        inforequest_pk = kwargs.pop(u'inforequest_pk', scenario.inforequest.pk)
        branch_pk = kwargs.pop(u'branch_pk', scenario.branch.pk)
        action_pk = kwargs.pop(u'action_pk', scenario.action.pk)
        url = reverse(u'inforequests:extend_deadline', args=(inforequest_pk, branch_pk, action_pk))

        self.assertEqual(kwargs, {})
        return url

    def _create_post_data(self, **kwargs):
        action_pk = kwargs.pop(u'action_pk', self._scenario.action.pk)
        kwargs.setdefault(u'extension', 47)
        kwargs.setdefault(u'prefix', u'%s-extenddeadlineform' % action_pk)
        return super(ExtendDeadlineViewTest, self)._create_post_data(**kwargs)


    def test_invalid_branch_returns_404_not_found(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario, branch_pk=47)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_branch_assigned_to_another_inforequest_returns_404_not_found(self):
        _, branch, _ = self._create_inforequest_scenario()
        scenario = self._create_scenario()
        url = self._create_url(scenario, branch_pk=branch.pk)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_branch_assigned_to_inforequest_returns_200_ok(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario, branch_pk=scenario.branch.pk)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_invalid_action_returns_404_not_found(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario, action_pk=47)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_action_assigned_to_another_branch_return_404_not_found(self):
        scenario = self._create_scenario(inforequest_scenario=[u'advancement'])
        _, (_, [(_, [advanced_request])]) = scenario.actions
        url = self._create_url(scenario, action_pk=advanced_request.pk)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_action_that_is_not_last_branch_action_returns_404_not_found(self):
        scenario = self._create_scenario(inforequest_scenario=[u'request', u'confirmation'])
        request, _ = scenario.actions
        url = self._create_url(scenario, action_pk=request.pk)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_action_without_obligee_deadline_returns_404_not_found(self):
        scenario = self._create_scenario(inforequest_scenario=[u'refusal'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_action_with_obligee_deadline_that_is_not_missed_returns_404_not_found(self):
        scenario = self._create_scenario(created=u'2010-05-10', now=u'2010-05-11')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_last_branch_action_with_missed_obligee_deadline_returns_200_ok(self):
        scenario = self._create_scenario(inforequest_scenario=[u'request', u'confirmation'], created=u'2010-05-10', now=u'2010-09-11')
        _, confirmation = scenario.actions
        url = self._create_url(scenario, action_pk=confirmation.pk)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_inforequest_with_undecided_email_returns_404_not_found(self):
        scenario = self._create_scenario()
        email = self._create_inforequest_email(inforequest=scenario.inforequest)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_get_renders_form_with_initial_value(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertTemplateUsed(response, u'inforequests/modals/extend_deadline.html')
        self.assertEqual(response.context[u'inforequest'], scenario.inforequest)
        self.assertEqual(response.context[u'branch'], scenario.branch)
        self.assertEqual(response.context[u'action'], scenario.action)
        self.assertIsInstance(response.context[u'form'], ExtendDeadlineForm)
        self.assertEqual(response.context[u'form'][u'extension'].value(), 5)

    def test_get_related_models_are_prefetched_before_render(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        with self.assertQueriesDuringRender([
                u'FROM "inforequests_branch" WHERE .* "inforequests_branch"."advanced_by_id" IS NULL',
                u'FROM "obligees_historicalobligee"',
                ]):
            response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

    def test_post_with_valid_data_saves_deadline_extension(self):
        scenario = self._create_scenario(created=u'2014-10-01', now=u'2014-10-16',
                inforequest_scenario=[(u'request', dict(deadline=10))])
        data = self._create_post_data(extension=7)
        url = self._create_url(scenario)

        self._login_user()
        with mock.patch(u'chcemvediet.apps.inforequests.models.action.workdays.between', side_effect=lambda a,b: (b-a).days):
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        # The action was created at 2014-10-01 and has 10 days deadline that ends at 2014-10-11.
        # Now is 2014-10-16 and already 5 days passed since the deadline was missed. If the user
        # wants to extend the deadline by 7 days relative to today, it must be extended by
        # 5 + 7 = 12 days. Note that for sake of simplicity we ignore weekends and holidays in this
        # test.
        action = Action.objects.get(pk=scenario.action.pk)
        self.assertEqual(action.extension, 12)

    def test_post_with_valid_data_does_not_save_deadline_extension_if_exception_raised(self):
        scenario = self._create_scenario(created=u'2014-10-01', now=u'2014-10-16',
                inforequest_scenario=[(u'request', dict(deadline=10))])
        data = self._create_post_data(extension=7)
        url = self._create_url(scenario)

        self._login_user()
        with mock.patch(u'chcemvediet.apps.inforequests.models.action.workdays.between', side_effect=lambda a,b: (b-a).days):
            with patch_with_exception(u'chcemvediet.apps.inforequests.views.JsonResponse'):
                response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        action = Action.objects.get(pk=scenario.action.pk)
        self.assertIsNone(action.extension)

    def test_post_with_valid_data_returns_json_with_success_and_inforequests_detail(self):
        scenario = self._create_scenario()
        data = self._create_post_data(extension=7)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        self.assertTemplateUsed(response, u'inforequests/detail_main.html')
        self.assertEqual(response.context[u'inforequest'], scenario.inforequest)

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

    def test_post_with_valid_data_related_models_are_prefetched_before_render(self):
        scenario = self._create_scenario()
        data = self._create_post_data(extension=7)
        url = self._create_url(scenario)

        self._login_user()
        with self.assertQueriesDuringRender([]):
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

    def test_post_with_invalid_data_does_not_save_deadline_extension(self):
        scenario = self._create_scenario()
        data = self._create_post_data(extension=10000)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        action = Action.objects.get(pk=scenario.action.pk)
        self.assertIsNone(action.extension)

    def test_post_with_invalid_data_returns_json_with_invalid_and_rendered_form(self):
        scenario = self._create_scenario()
        data = self._create_post_data(extension=10000)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        self.assertTemplateUsed(response, u'inforequests/modals/extend_deadline.html')
        self.assertEqual(response.context[u'inforequest'], scenario.inforequest)
        self.assertEqual(response.context[u'branch'], scenario.branch)
        self.assertEqual(response.context[u'action'], scenario.action)
        self.assertIsInstance(response.context[u'form'], ExtendDeadlineForm)

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_post_with_invalid_data_related_models_are_prefetched_before_render(self):
        scenario = self._create_scenario()
        data = self._create_post_data(extension=10000)
        url = self._create_url(scenario)

        self._login_user()
        with self.assertQueriesDuringRender([
                u'FROM "inforequests_branch" WHERE .* "inforequests_branch"."advanced_by_id" IS NULL',
                u'FROM "obligees_historicalobligee"',
                ]):
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

    def test_extension_field_min_value(self):
        scenario = self._create_scenario()
        data = self._create_post_data(extension=1)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'extension', 'Ensure this value is greater than or equal to 2.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_extension_field_max_value(self):
        scenario = self._create_scenario()
        data = self._create_post_data(extension=101)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'extension', 'Ensure this value is less than or equal to 100.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')
