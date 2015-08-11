# vim: expandtab
# -*- coding: utf-8 -*-
import json

from django.core.urlresolvers import reverse
from django.http import JsonResponse

from poleno.utils.date import utc_datetime_from_local, naive_date
from poleno.utils.misc import Bunch
from poleno.utils.test import created_instances, patch_with_exception

from ... import forms
from ...models import InforequestEmail, Action
from . import CustomTestCase
from .fields_tests import BranchFieldTests, DeadlineFieldTests, AdvancedToFieldsTests
from .fields_tests import DisclosureLevelFieldTests, RefusalReasonFieldTests
from .common_tests import CommonDecoratorsTests, CanAddActionTests
from .common_tests import OwnedNotClosedInforequestArgTests, OldestUndecitedEmailArgTests


class DecideEmailTests(
        CommonDecoratorsTests,
        OwnedNotClosedInforequestArgTests,
        OldestUndecitedEmailArgTests,
        CanAddActionTests,
        BranchFieldTests,
        ):
    u"""
    Absract tests for ``decide_email_*()`` views registered as "inforequests:decide_email_*".
    """
    action_type = None
    view_name = None
    form_class = None
    template = None
    good_scenario = None # Some scenario the view will be successfull on
    post_with_bad_scenario_returns_404 = True


    def _create_scenario(self, **kwargs):
        res = Bunch()

        inforequest_args = kwargs.pop(u'inforequest_args', [])
        inforequest_scenario = kwargs.pop(u'inforequest_scenario', self.good_scenario)
        inforequest_args = list(inforequest_args) + list(inforequest_scenario)
        res.inforequest, res.branch, res.actions = self._create_inforequest_scenario(*inforequest_args)

        email_args = kwargs.pop(u'email_args', {})
        email_args.setdefault(u'inforequest', res.inforequest)
        res.email, res.rel = self._create_inforequest_email(**email_args)

        self.assertEqual(kwargs, {})
        return res

    def _create_url(self, scenario, **kwargs):
        inforequest_pk = kwargs.pop(u'inforequest_pk', scenario.inforequest.pk)
        email_pk = kwargs.pop(u'email_pk', scenario.email.pk)
        url = reverse(self.view_name, args=(inforequest_pk, email_pk))

        self.assertEqual(kwargs, {})
        return url


    def test_get_renders_form(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertTemplateUsed(response, self.template)
        self.assertEqual(response.context[u'inforequest'], scenario.inforequest)
        self.assertEqual(response.context[u'email'], scenario.email)
        self.assertIsInstance(response.context[u'form'], self.form_class)

    def test_get_related_models_are_prefetched_before_render(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        with self.assertQueriesDuringRender([]):
            response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

    def test_post_with_valid_data_creates_action_instance(self):
        scenario = self._create_scenario(email_args=dict(subject=u'Subject', text=u'Content', processed=utc_datetime_from_local(u'2010-10-05 00:33:00')))
        attachment1 = self._create_attachment(generic_object=scenario.email, name=u'filename.txt', content=u'content', content_type=u'text/plain')
        attachment2 = self._create_attachment(generic_object=scenario.email, name=u'filename.html', content=u'<p>content</p>', content_type=u'text/html')
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        action = action_set.get()

        self.assertEqual(action.email, scenario.email)
        self.assertEqual(action.type, self.action_type)
        self.assertEqual(action.subject, u'Subject')
        self.assertEqual(action.content, u'Content')
        self.assertEqual(action.effective_date, naive_date(u'2010-10-05'))

        attachments = [(a.name, a.content, a.content_type) for a in action.attachment_set.all()]
        self.assertItemsEqual(attachments, [
            (u'filename.txt', u'content', u'text/plain'),
            (u'filename.html', u'<p>content</p>', u'text/html'),
            ])

        scenario.rel = InforequestEmail.objects.get(pk=scenario.rel.pk)
        self.assertEqual(scenario.rel.type, InforequestEmail.TYPES.OBLIGEE_ACTION)

    def test_post_with_valid_data_does_not_create_action_instance_if_exception_raised(self):
        scenario = self._create_scenario(email_args=dict(subject=u'Subject', text=u'Content', processed=utc_datetime_from_local(u'2010-10-05 00:33:00')))
        attachment1 = self._create_attachment(generic_object=scenario.email, name=u'filename.txt', content=u'content', content_type=u'text/plain')
        attachment2 = self._create_attachment(generic_object=scenario.email, name=u'filename.html', content=u'<p>content</p>', content_type=u'text/html')
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            with patch_with_exception(u'chcemvediet.apps.inforequests.views.JsonResponse'):
                response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFalse(action_set.exists())

        scenario.rel = InforequestEmail.objects.get(pk=scenario.rel.pk)
        self.assertEqual(scenario.rel.type, InforequestEmail.TYPES.UNDECIDED)

    def test_post_with_valid_data_returns_json_with_success_and_inforequests_detail(self):
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

    def test_post_with_valid_data_related_models_are_prefetched_before_render(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with self.assertQueriesDuringRender([]):
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

    def test_post_with_invalid_data_does_not_create_action_instance(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(Action.objects) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFalse(action_set.exists())

        scenario.rel = InforequestEmail.objects.get(pk=scenario.rel.pk)
        self.assertEqual(scenario.rel.type, InforequestEmail.TYPES.UNDECIDED)

    def test_post_with_invalid_data_returns_json_with_invalid_and_rendered_form(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        self.assertTemplateUsed(response, self.template)
        self.assertEqual(response.context[u'inforequest'], scenario.inforequest)
        self.assertEqual(response.context[u'email'], scenario.email)
        self.assertIsInstance(response.context[u'form'], self.form_class)

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_post_with_invalid_data_related_models_are_prefetched_before_render(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        with self.assertQueriesDuringRender([]):
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

class DecideEmailConfirmationViewTest(
        DecideEmailTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.CONFIRMATION
    view_name = u'inforequests:decide_email_confirmation'
    form_class = forms.ConfirmationEmailForm
    form_prefix = u'confirmationemailform'
    template = u'inforequests/modals/confirmation_email.html'
    good_scenario = []
    bad_scenario = [u'extension']
    can_add_after = {
            u'request': True,
            u'clarification_response': False,
            u'appeal': False,
            u'confirmation': False,
            u'extension': False,
            u'advancement': False,
            u'clarification_request': False,
            u'disclosure_none': False,
            u'disclosure_partial': False,
            u'disclosure_full': False,
            u'refusal': False,
            u'affirmation': False,
            u'reversion': False,
            u'remandment': False,
            u'advanced_request': True,
            u'expiration': False,
            u'appeal_expiration': False,
            }

class DecideEmailExtensionViewTest(
        DecideEmailTests,
        DeadlineFieldTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.EXTENSION
    view_name = u'inforequests:decide_email_extension'
    form_class = forms.ExtensionEmailForm
    form_prefix = u'extensionemailform'
    template = u'inforequests/modals/extension_email.html'
    good_scenario = []
    bad_scenario = [u'extension']
    can_add_after = {
            u'request': True,
            u'clarification_response': True,
            u'appeal': False,
            u'confirmation': True,
            u'extension': False,
            u'advancement': False,
            u'clarification_request': False,
            u'disclosure_none': False,
            u'disclosure_partial': False,
            u'disclosure_full': False,
            u'refusal': False,
            u'affirmation': False,
            u'reversion': False,
            u'remandment': True,
            u'advanced_request': True,
            u'expiration': False,
            u'appeal_expiration': False,
            }

class DecideEmailAdvancementViewTest(
        DecideEmailTests,
        DisclosureLevelFieldTests,
        AdvancedToFieldsTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.ADVANCEMENT
    view_name = u'inforequests:decide_email_advancement'
    form_class = forms.AdvancementEmailForm
    form_prefix = u'advancementemailform'
    template = u'inforequests/modals/advancement_email.html'
    good_scenario = []
    bad_scenario = [u'extension']
    can_add_after = {
            u'request': True,
            u'clarification_response': True,
            u'appeal': False,
            u'confirmation': True,
            u'extension': False,
            u'advancement': False,
            u'clarification_request': False,
            u'disclosure_none': False,
            u'disclosure_partial': False,
            u'disclosure_full': False,
            u'refusal': False,
            u'affirmation': False,
            u'reversion': False,
            u'remandment': False,
            u'advanced_request': True,
            u'expiration': False,
            u'appeal_expiration': False,
            }

class DecideEmailClarificationRequestViewTest(
        DecideEmailTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.CLARIFICATION_REQUEST
    view_name = u'inforequests:decide_email_clarification_request'
    form_class = forms.ClarificationRequestEmailForm
    form_prefix = u'clarificationrequestemailform'
    template = u'inforequests/modals/clarification_request_email.html'
    good_scenario = []
    bad_scenario = [u'extension']
    can_add_after = {
            u'request': True,
            u'clarification_response': True,
            u'appeal': False,
            u'confirmation': True,
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
            u'advanced_request': True,
            u'expiration': False,
            u'appeal_expiration': False,
            }

class DecideEmailDisclosureViewTest(
        DecideEmailTests,
        DisclosureLevelFieldTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.DISCLOSURE
    view_name = u'inforequests:decide_email_disclosure'
    form_class = forms.DisclosureEmailForm
    form_prefix = u'disclosureemailform'
    template = u'inforequests/modals/disclosure_email.html'
    good_scenario = []
    bad_scenario = [u'refusal']
    can_add_after = {
            u'request': True,
            u'clarification_response': True,
            u'appeal': False,
            u'confirmation': True,
            u'extension': True,
            u'advancement': False,
            u'clarification_request': False,
            u'disclosure_none': False,
            u'disclosure_partial': False,
            u'disclosure_full': False,
            u'refusal': False,
            u'affirmation': False,
            u'reversion': False,
            u'remandment': True,
            u'advanced_request': True,
            u'expiration': False,
            u'appeal_expiration': False,
            }

class DecideEmailRefusalViewTest(
        DecideEmailTests,
        RefusalReasonFieldTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.REFUSAL
    view_name = u'inforequests:decide_email_refusal'
    form_class = forms.RefusalEmailForm
    form_prefix = u'refusalemailform'
    template = u'inforequests/modals/refusal_email.html'
    good_scenario = []
    bad_scenario = [u'refusal']
    can_add_after = {
            u'request': True,
            u'clarification_response': True,
            u'appeal': False,
            u'confirmation': True,
            u'extension': True,
            u'advancement': False,
            u'clarification_request': False,
            u'disclosure_none': False,
            u'disclosure_partial': False,
            u'disclosure_full': False,
            u'refusal': False,
            u'affirmation': False,
            u'reversion': False,
            u'remandment': True,
            u'advanced_request': True,
            u'expiration': False,
            u'appeal_expiration': False,
            }
