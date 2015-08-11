# vim: expandtab
# -*- coding: utf-8 -*-
import json

from django.core.urlresolvers import reverse

from poleno.timewarp import timewarp
from poleno.mail.models import Message
from poleno.utils.date import local_datetime_from_local, naive_date
from poleno.utils.misc import Bunch
from poleno.utils.test import created_instances

from . import CustomTestCase
from ... import forms
from ...models import Action
from .common_tests import CommonDecoratorsTests, CanAddActionTests, OwnedNotClosedInforequestArgTests
from .common_tests import AddSmailAndNewActionCommonTests
from .fields_tests import DraftBranchFieldTests, DraftSubjectContentAttachmentsFieldsTests

class NewActionTests(
        CommonDecoratorsTests,
        OwnedNotClosedInforequestArgTests,
        CanAddActionTests,
        DraftBranchFieldTests,
        DraftSubjectContentAttachmentsFieldsTests,
        AddSmailAndNewActionCommonTests,
        ):
    u"""
    Absract tests for ``new_action_*()`` views registered as "inforequests:new_action_*".
    """
    view_name = None
    good_scenario = None # Some scenario the view will be successfull on
    post_with_bad_scenario_returns_404 = False
    undecided_email_message_template = u'inforequests/messages/new_action_undecided_emails.en.txt'

    def _create_scenario(self, **kwargs):
        res = Bunch()

        inforequest_args = kwargs.pop(u'inforequest_args', [])
        inforequest_scenario = kwargs.pop(u'inforequest_scenario', self.good_scenario)
        inforequest_args = list(inforequest_args) + list(inforequest_scenario)
        res.inforequest, res.branch, res.actions = self._create_inforequest_scenario(*inforequest_args)

        draft_args = kwargs.pop(u'draft_args', None)
        if draft_args is not None:
            draft_args.setdefault(u'inforequest', res.inforequest)
            draft_args.setdefault(u'type', self.action_type)
            res.draft = self._create_action_draft(**draft_args)

        self.assertEqual(kwargs, {})
        return res

    def _create_url(self, scenario, **kwargs):
        inforequest_pk = kwargs.pop(u'inforequest_pk', scenario.inforequest.pk)
        url = reverse(self.view_name, args=(inforequest_pk,))

        self.assertEqual(kwargs, {})
        return url

    def _create_post_data(self, **kwargs):
        kwargs.setdefault(u'button', u'print')
        kwargs.setdefault(u'not_prefixed', []).append(u'button')
        return super(NewActionTests, self)._create_post_data(**kwargs)


    def test_post_with_default_button_and_valid_data_creates_action_with_effective_date_today(self):
        timewarp.jump(local_datetime_from_local(u'2010-03-05 10:33:00'))
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        action = action_set.get()

        self.assertEqual(action.effective_date, naive_date(u'2010-03-05'))

    def test_post_with_print_button_and_valid_data_returns_json_with_rendered_print(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'print', branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertTemplateUsed(response, u'inforequests/modals/print.html')
        data = json.loads(response.content)
        self.assertIn(u'print', data)


class NewActionClarificationResponseViewTests(
        NewActionTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.CLARIFICATION_RESPONSE
    view_name = u'inforequests:new_action_clarification_response'
    form_class = forms.ClarificationResponseForm
    form_prefix = u'clarificationresponseform'
    template = u'inforequests/modals/clarification_response.html'
    good_scenario = [u'clarification_request']
    bad_scenario = []
    can_add_after = {
            u'request': False,
            u'clarification_response': False,
            u'appeal': False,
            u'confirmation': False,
            u'extension': False,
            u'advancement': False,
            u'clarification_request': True,
            u'disclosure_none': False,
            u'disclosure_partial': False,
            u'disclosure_full': False,
            u'refusal': False,
            u'affirmation': False,
            u'reversion': False,
            u'remandment': False,
            u'advanced_request': False,
            u'expiration': False,
            u'appeal_expiration': False,
            }

    def test_post_with_email_button_and_valid_data_sends_action_by_email(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'email', branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            with created_instances(Message.objects) as message_set:
                response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        action = action_set.get()
        email = message_set.get()

        self.assertEqual(email.type, Message.TYPES.OUTBOUND)
        self.assertEqual(action.email, email)

    def test_post_with_email_button_and_invalid_data_does_not_send_email(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'email', branch=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(Message.objects) as message_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFalse(message_set.exists())

class NewActionAppealViewTests(
        NewActionTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.APPEAL
    view_name = u'inforequests:new_action_appeal'
    form_class = forms.AppealForm
    form_prefix = u'appealform'
    template = u'inforequests/modals/appeal.html'
    good_scenario = [u'refusal']
    bad_scenario = []
    can_add_after = {
            u'request': False,
            u'clarification_response': False,
            u'appeal': False,
            u'confirmation': False,
            u'extension': False,
            u'advancement': True,
            u'clarification_request': False,
            u'disclosure_none': True,
            u'disclosure_partial': True,
            u'disclosure_full': False,
            u'refusal': True,
            u'affirmation': False,
            u'reversion': False,
            u'remandment': False,
            u'advanced_request': False,
            u'expiration': True,
            u'appeal_expiration': False,
            }

    def test_post_with_default_button_and_valid_data_adds_expiration_if_expired(self):
        timewarp.jump(local_datetime_from_local(u'2010-03-05 10:33:00'))
        scenario = self._create_scenario(inforequest_scenario=[u'request'])
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        timewarp.jump(local_datetime_from_local(u'2010-08-06 10:33:00'))
        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        action_types = [a.type for a in action_set.all()]
        self.assertEqual(action_types, [Action.TYPES.EXPIRATION, Action.TYPES.APPEAL])

    def test_post_with_default_button_and_invalid_data_does_not_add_expiration_if_expired(self):
        timewarp.jump(local_datetime_from_local(u'2010-03-05 10:33:00'))
        scenario = self._create_scenario(inforequest_scenario=[u'request'])
        data = self._create_post_data(branch=u'invalid')
        url = self._create_url(scenario)

        timewarp.jump(local_datetime_from_local(u'2010-08-06 10:33:00'))
        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFalse(action_set.exists())

    def test_post_with_email_button_returns_400_bad_request(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'email')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
