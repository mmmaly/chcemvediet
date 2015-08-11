# vim: expandtab
# -*- coding: utf-8 -*-
import json

from django.http import JsonResponse

from poleno.utils.test import created_instances, patch_with_exception

from ...models import InforequestEmail, Action, ActionDraft
from . import AbstractTests

class CommonDecoratorsTests(AbstractTests):
    u"""
    Tests for views implementing HEAD, GET and POST methods expecting ajax requests from
    authentificated users.
    """

    def test_allowed_http_methods(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        allowed = [u'HEAD', u'GET', u'POST']
        self.assert_allowed_http_methods(allowed, url)

    def test_non_ajax_request_returns_400_bad_request(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_anonymous_user_gets_403_firbidden(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_gets_200_ok(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

class OwnedNotClosedInforequestArgTests(AbstractTests):
    u"""
    Tests for views expecting owned not closed ``Inforequest`` argument.
    """

    def test_invalid_inforequest_returns_404_not_found(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario, inforequest_pk=47)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_inforequest_owned_by_another_user_returns_404_not_found(self):
        scenario = self._create_scenario(inforequest_args=[self.user2])
        url = self._create_url(scenario)

        self._login_user(self.user1)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_closed_inforequest_returns_404_not_found(self):
        scenario = self._create_scenario(inforequest_args=[dict(closed=True)])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_not_closed_inforequest_owned_by_user_return_200_ok(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

class OldestUndecitedEmailArgTests(AbstractTests):
    u"""
    Tests for views expecting undecided ``Message`` argument.
    """

    def test_invalid_email_returns_404_not_found(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario, email_pk=47)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_email_assigned_to_another_inforequest_returns_404_not_found(self):
        scenario = self._create_scenario()
        inforequest2, _, _ = self._create_inforequest_scenario()
        email2, _ = self._create_inforequest_email(inforequest=inforequest2)
        url = self._create_url(scenario, email_pk=email2.pk)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_email_unassigned_to_any_inforequest_returns_404_not_found(self):
        scenario = self._create_scenario()
        email2 = self._create_message()
        url = self._create_url(scenario, email_pk=email2.pk)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_email_that_is_not_undecided_returns_404_not_found(self):
        scenario = self._create_scenario(email_args=dict(reltype=InforequestEmail.TYPES.UNKNOWN))
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_email_that_is_not_oldest_undecided_email_returns_404_not_found(self):
        scenario = self._create_scenario()
        email2, _ = self._create_inforequest_email(inforequest=scenario.inforequest)
        url = self._create_url(scenario, email_pk=email2.pk)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_oldest_undecided_email_assigned_to_inforequest_returns_200_ok(self):
        scenario = self._create_scenario()
        email2, _ = self._create_inforequest_email(inforequest=scenario.inforequest)
        url = self._create_url(scenario, email_pk=scenario.email.pk)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

class CanAddActionTests(AbstractTests):
    u"""
    Tests for views using ``Inforequest.can_add_action()`` method.
    """
    action_type = None
    good_scenario = None # Some scenario the view will be successfull on
    bad_scenario = None # Some scenario to which the action may not be added
    can_add_after = None
    post_with_bad_scenario_returns_404 = None

    def test_get_with_good_scenario_returns_200_ok(self):
        scenario = self._create_scenario(inforequest_scenario=self.good_scenario)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_get_with_bad_scenario_returns_404_not_found(self):
        scenario = self._create_scenario(inforequest_scenario=self.bad_scenario)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_post_with_bad_scenario_returns_200_ok_or_404_not_found(self):
        scenario = self._create_scenario(inforequest_scenario=self.bad_scenario)
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertIsNotNone(self.post_with_bad_scenario_returns_404)
        if self.post_with_bad_scenario_returns_404:
            self.assertEqual(response.status_code, 404)
        else:
            self.assertEqual(response.status_code, 200)

    def test_get_with_can_add_action_returns_200_ok_or_404_not_found(self):
        tests = ( # test name,              scenario
                (u'request',                [u'request']),
                (u'clarification_response', [u'clarification_request', u'clarification_response']),
                (u'appeal',                 [u'refusal', u'appeal']),
                (u'confirmation',           [u'confirmation']),
                (u'extension',              [u'extension']),
                (u'advancement',            [(u'advancement', [u'refusal', u'appeal', u'affirmation'])]),
                (u'clarification_request',  [u'clarification_request']),
                (u'disclosure_none',        [(u'disclosure', dict(disclosure_level=Action.DISCLOSURE_LEVELS.NONE))]),
                (u'disclosure_partial',     [(u'disclosure', dict(disclosure_level=Action.DISCLOSURE_LEVELS.PARTIAL))]),
                (u'disclosure_full',        [(u'disclosure', dict(disclosure_level=Action.DISCLOSURE_LEVELS.FULL))]),
                (u'refusal',                [u'refusal']),
                (u'affirmation',            [u'refusal', u'appeal', u'affirmation']),
                (u'reversion',              [u'refusal', u'appeal', u'reversion']),
                (u'remandment',             [u'refusal', u'appeal', u'remandment']),
                (u'advanced_request',       [u'advancement', u'appeal', u'affirmation']),
                (u'expiration',             [u'expiration']),
                (u'appeal_expiration',      [u'refusal', u'appeal', u'appeal_expiration']),
                )

        self._login_user()
        tested_action_types = set()
        for test_name, scenario in tests:
            scenario = self._create_scenario(inforequest_scenario=scenario)
            url = self._create_url(scenario)

            response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
            action_name = Action.TYPES._inverse[self.action_type].lower()
            if self.can_add_after[test_name]:
                self.assertEqual(response.status_code, 200, u'Cannot add "%s" after "%s"' % (action_name, test_name))
            else:
                self.assertEqual(response.status_code, 404, u'Can add "%s" after "%s"' % (action_name, test_name))

            for branch in scenario.inforequest.branches:
                tested_action_types.add(branch.last_action.type)

        # Make sure we tested all defined action types
        defined_action_types = Action.TYPES._inverse.keys()
        self.assertItemsEqual(tested_action_types, defined_action_types)

class AddSmailAndNewActionCommonTests(AbstractTests):
    u"""
    Common tests for ``add_smail_*()`` and ``new_action_*()`` views, so we don't need to write them
    twice.
    """
    action_type = None
    form_class = None
    template = None
    undecided_email_message_template = None

    def test_get_with_undecided_email_returns_404_not_found(self):
        scenario = self._create_scenario()
        email = self._create_inforequest_email(inforequest=scenario.inforequest)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)

    def test_post_with_undecided_email_returns_200_ok(self):
        scenario = self._create_scenario()
        email = self._create_inforequest_email(inforequest=scenario.inforequest)
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_get_renders_form(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertTemplateUsed(response, self.template)
        self.assertEqual(response.context[u'inforequest'], scenario.inforequest)
        self.assertIsInstance(response.context[u'form'], self.form_class)

    def test_get_related_models_are_prefetched_before_render(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        with self.assertQueriesDuringRender([]):
            response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

    def test_post_with_draft_button_and_valid_data_creates_new_draft_instance(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(ActionDraft.objects) as actiondraft_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        draft = actiondraft_set.get()

        self.assertEqual(draft.inforequest, scenario.inforequest)
        self.assertEqual(draft.branch, scenario.branch)

    def test_post_with_draft_button_and_valid_data_does_not_create_new_draft_instance_if_exception_raised(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(ActionDraft.objects) as actiondraft_set:
            with patch_with_exception(u'chcemvediet.apps.inforequests.views.JsonResponse'):
                response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFalse(actiondraft_set.exists())

    def test_post_with_draft_button_and_valid_data_updates_existing_draft_instance(self):
        scenario = self._create_scenario(draft_args=dict(branch=None))
        data = self._create_post_data(button=u'draft', branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(ActionDraft.objects) as actiondraft_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFalse(actiondraft_set.exists())

        draft = ActionDraft.objects.get(pk=scenario.draft.pk)
        self.assertEqual(draft.inforequest, scenario.inforequest)
        self.assertEqual(draft.branch, scenario.branch)

    def test_post_with_draft_button_and_valid_data_does_not_update_existing_draft_instance_if_exception_raised(self):
        scenario = self._create_scenario(draft_args=dict(branch=None))
        data = self._create_post_data(button=u'draft', branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(ActionDraft.objects) as actiondraft_set:
            with patch_with_exception(u'chcemvediet.apps.inforequests.views.JsonResponse'):
                response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFalse(actiondraft_set.exists())

        draft = ActionDraft.objects.get(pk=scenario.draft.pk)
        self.assertEqual(draft.inforequest, scenario.inforequest)
        self.assertIsNone(draft.branch)

    def test_post_with_draft_button_and_valid_data_returns_json_with_success(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

    def test_post_with_draft_button_and_valid_data_related_models_are_prefetched_before_render(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with self.assertQueriesDuringRender():
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

    def test_post_with_draft_button_and_invalid_data_does_not_create_new_draft_instance(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', branch=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(ActionDraft.objects) as actiondraft_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFalse(actiondraft_set.exists())

    def test_post_with_draft_button_and_invalid_data_does_not_update_existing_draft_instance(self):
        scenario = self._create_scenario(draft_args=dict())
        data = self._create_post_data(button=u'draft', branch=u'invalid')
        url = self._create_url(scenario)

        self.assertIsNone(scenario.draft.branch)

        self._login_user()
        with created_instances(ActionDraft.objects) as actiondraft_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFalse(actiondraft_set.exists())

        draft = ActionDraft.objects.get(pk=scenario.draft.pk)
        self.assertEqual(draft.inforequest, scenario.inforequest)
        self.assertIsNone(draft.branch)

    def test_post_with_draft_button_and_invalid_data_returns_json_with_invalid_and_rendered_form(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', branch=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        self.assertTemplateUsed(response, self.template)
        self.assertEqual(response.context[u'inforequest'], scenario.inforequest)
        self.assertIsInstance(response.context[u'form'], self.form_class)

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_post_with_draft_button_and_invalid_data_related_models_are_prefetched_before_render(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', branch=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        with self.assertQueriesDuringRender([]):
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

    def test_post_with_default_button_and_valid_data_creates_action(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        action = action_set.get()

        self.assertIsNone(action.email)
        self.assertEqual(action.type, self.action_type)
        self.assertEqual(action.branch, scenario.branch)

    def test_post_with_default_button_and_valid_data_does_not_create_action_if_exception_raised(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            with patch_with_exception(u'chcemvediet.apps.inforequests.views.JsonResponse'):
                response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFalse(action_set.exists())

    def test_post_with_default_button_and_valid_data_deletes_draft(self):
        scenario = self._create_scenario(draft_args=dict())
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertFalse(ActionDraft.objects.filter(pk=scenario.draft.pk).exists())

    def test_post_with_default_button_and_valid_data_does_not_delete_draft_if_exception_raised(self):
        scenario = self._create_scenario(draft_args=dict())
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with patch_with_exception(u'chcemvediet.apps.inforequests.views.JsonResponse'):
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertTrue(ActionDraft.objects.filter(pk=scenario.draft.pk).exists())

    def test_post_with_default_button_and_valid_data_returns_json_with_success_and_inforequests_detail(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        action = action_set.get()

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        self.assertTemplateUsed(response, u'inforequests/detail_main.html')
        self.assertEqual(response.context[u'inforequest'], scenario.inforequest)

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')
        self.assertEqual(data[u'scroll_to'], u'#action-%s' % action.pk)

    def test_post_with_default_button_and_valid_data_related_models_are_prefetched_before_render(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        patterns = ([], [u'FROM "obligees_obligee"']) if data[u'button'] == u'print' else ([],)
        with self.assertQueriesDuringRender(*patterns):
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

    def test_post_with_default_button_and_invalid_data_does_not_create_action(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFalse(action_set.exists())

    def test_post_with_default_button_and_invalid_data_does_not_delete_draft(self):
        scenario = self._create_scenario(draft_args=dict())
        data = self._create_post_data(branch=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertTrue(ActionDraft.objects.filter(pk=scenario.draft.pk).exists())

    def test_post_with_default_button_and_invalid_data_returns_json_with_invalid_and_rendered_form(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        self.assertTemplateUsed(response, self.template)
        self.assertEqual(response.context[u'inforequest'], scenario.inforequest)
        self.assertIsInstance(response.context[u'form'], self.form_class)

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_post_with_default_button_and_invalid_data_related_models_are_prefetched_before_render(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        with self.assertQueriesDuringRender([]):
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

    def test_post_with_invalid_button_returns_400_bad_request(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 400)

    def test_form_with_undecided_emails_is_invalid(self):
        scenario = self._create_scenario()
        email, _ = self._create_inforequest_email(inforequest=scenario.inforequest)
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertTemplateUsed(response, self.undecided_email_message_template)
        self.assertEqual(len(response.context[u'form'].errors[u'__all__']), 1)

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_form_with_no_undecided_emails_is_valid(self):
        scenario = self._create_scenario()
        email, _ = self._create_inforequest_email(inforequest=scenario.inforequest, reltype=InforequestEmail.TYPES.UNRELATED)
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        json_data = json.loads(response.content)
        self.assertEqual(json_data[u'result'], u'success')

    def test_draft_form_with_undecided_emails_is_valid(self):
        scenario = self._create_scenario()
        email, _ = self._create_inforequest_email(inforequest=scenario.inforequest)
        data = self._create_post_data(button=u'draft', branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        json_data = json.loads(response.content)
        self.assertEqual(json_data[u'result'], u'success')
