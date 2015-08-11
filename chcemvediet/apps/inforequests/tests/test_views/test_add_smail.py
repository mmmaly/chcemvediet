# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse

from poleno.utils.misc import Bunch

from . import CustomTestCase
from ... import forms
from ...models import Action
from .common_tests import CommonDecoratorsTests, CanAddActionTests, OwnedNotClosedInforequestArgTests
from .common_tests import AddSmailAndNewActionCommonTests
from .fields_tests import DraftBranchFieldTests, DraftEffectiveDateFieldTests, DraftSubjectContentAttachmentsFieldsTests
from .fields_tests import DraftDeadlineFieldTests, DraftAdvancedToFieldsTests, DraftDisclosureLevelFieldTests, DraftRefusalReasonFieldTests

class AddSmailTests(
        CommonDecoratorsTests,
        OwnedNotClosedInforequestArgTests,
        CanAddActionTests,
        DraftBranchFieldTests,
        DraftEffectiveDateFieldTests,
        DraftSubjectContentAttachmentsFieldsTests,
        AddSmailAndNewActionCommonTests,
        ):
    u"""
    Absract tests for ``add_smail_*()`` views registered as "inforequests:add_smail_*".
    """
    view_name = None
    good_scenario = None # Some scenario the view will be successfull on
    post_with_bad_scenario_returns_404 = False
    undecided_email_message_template = u'inforequests/messages/add_smail_undecided_emails.en.txt'

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
        kwargs.setdefault(u'button', u'add')
        kwargs.setdefault(u'not_prefixed', []).append(u'button')
        return super(AddSmailTests, self)._create_post_data(**kwargs)


class AddSmailConfirmationViewTest(
        AddSmailTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.CONFIRMATION
    view_name = u'inforequests:add_smail_confirmation'
    form_class = forms.ConfirmationSmailForm
    form_prefix = u'confirmationsmailform'
    template = u'inforequests/modals/confirmation_smail.html'
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

class AddSmailExtensionViewTest(
        AddSmailTests,
        DraftDeadlineFieldTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.EXTENSION
    view_name = u'inforequests:add_smail_extension'
    form_class = forms.ExtensionSmailForm
    form_prefix = u'extensionsmailform'
    template = u'inforequests/modals/extension_smail.html'
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

class AddSmailAdvancementViewTest(
        AddSmailTests,
        DraftDisclosureLevelFieldTests,
        DraftAdvancedToFieldsTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.ADVANCEMENT
    view_name = u'inforequests:add_smail_advancement'
    form_class = forms.AdvancementSmailForm
    form_prefix = u'advancementsmailform'
    template = u'inforequests/modals/advancement_smail.html'
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

class AddSmailClarificationRequestViewTest(
        AddSmailTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.CLARIFICATION_REQUEST
    view_name = u'inforequests:add_smail_clarification_request'
    form_class = forms.ClarificationRequestSmailForm
    form_prefix = u'clarificationrequestsmailform'
    template = u'inforequests/modals/clarification_request_smail.html'
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

class AddSmailDisclosureViewTest(
        AddSmailTests,
        DraftDisclosureLevelFieldTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.DISCLOSURE
    view_name = u'inforequests:add_smail_disclosure'
    form_class = forms.DisclosureSmailForm
    form_prefix = u'disclosuresmailform'
    template = u'inforequests/modals/disclosure_smail.html'
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

class AddSmailRefusalViewTest(
        AddSmailTests,
        DraftRefusalReasonFieldTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.REFUSAL
    view_name = u'inforequests:add_smail_refusal'
    form_class = forms.RefusalSmailForm
    form_prefix = u'refusalsmailform'
    template = u'inforequests/modals/refusal_smail.html'
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

class AddSmailAffirmationViewTest(
        AddSmailTests,
        DraftRefusalReasonFieldTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.AFFIRMATION
    view_name = u'inforequests:add_smail_affirmation'
    form_class = forms.AffirmationSmailForm
    form_prefix = u'affirmationsmailform'
    template = u'inforequests/modals/affirmation_smail.html'
    good_scenario = [u'refusal', u'appeal']
    bad_scenario = []
    can_add_after = {
            u'request': False,
            u'clarification_response': False,
            u'appeal': True,
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
            u'advanced_request': False,
            u'expiration': False,
            u'appeal_expiration': False,
            }

class AddSmailReversionViewTest(
        AddSmailTests,
        DraftDisclosureLevelFieldTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.REVERSION
    view_name = u'inforequests:add_smail_reversion'
    form_class = forms.ReversionSmailForm
    form_prefix = u'reversionsmailform'
    template = u'inforequests/modals/reversion_smail.html'
    good_scenario = [u'refusal', u'appeal']
    bad_scenario = []
    can_add_after = {
            u'request': False,
            u'clarification_response': False,
            u'appeal': True,
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
            u'advanced_request': False,
            u'expiration': False,
            u'appeal_expiration': False,
            }

class AddSmailRemandmentViewTest(
        AddSmailTests,
        DraftDisclosureLevelFieldTests,
        CustomTestCase,
        ):
    action_type = Action.TYPES.REMANDMENT
    view_name = u'inforequests:add_smail_remandment'
    form_class = forms.RemandmentSmailForm
    form_prefix = u'remandmentsmailform'
    template = u'inforequests/modals/remandment_smail.html'
    good_scenario = [u'refusal', u'appeal']
    bad_scenario = []
    can_add_after = {
            u'request': False,
            u'clarification_response': False,
            u'appeal': True,
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
            u'advanced_request': False,
            u'expiration': False,
            u'appeal_expiration': False,
            }
