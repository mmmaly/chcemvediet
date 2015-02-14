# vim: expandtab
# -*- coding: utf-8 -*-
import re
import json

from django.core.urlresolvers import reverse

from poleno.timewarp import timewarp
from poleno.utils.date import local_datetime_from_local, local_today, naive_date
from poleno.utils.test import created_instances

from . import AbstractTests
from ...models import Action, ActionDraft

class FieldsTests(AbstractTests):
    form_class = None

    def _tested_fields(self):
        return []

    def test_all_form_fields_are_being_tested(self):
        u"""
        Checks that all form fields are being tested. We do this to make sure we notice if there
        was a new untested field mixin added to the form.
        """
        tested_fields = self._tested_fields()
        defined_fields = self.form_class.base_fields.keys()
        self.assertItemsEqual(tested_fields, defined_fields)


class BranchFieldTests(FieldsTests):
    good_scenario = None # Some scenario the view will be successfull on
    bad_scenario = None # Some scenario to which the action may not be added

    def _create_post_data(self, **kwargs):
        kwargs.setdefault(u'branch', u'')
        return super(BranchFieldTests, self)._create_post_data(**kwargs)

    def _tested_fields(self):
        return super(BranchFieldTests, self)._tested_fields() + [u'branch']


    def test_branch_field_initial_value(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertIsNone(response.context[u'form'][u'branch'].value())

    def test_branch_field_is_saved(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        action = action_set.get()

        self.assertEqual(action.branch, scenario.branch)

    def test_branch_field_is_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(omit=[u'branch'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'branch', 'This field is required.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_branch_field_with_invalid_branch_is_invalid(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'branch', 'Select a valid choice. invalid is not one of the available choices.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_branch_field_with_branch_from_another_inforequest_is_invalid(self):
        scenario = self._create_scenario()
        inforequest2, branch2, _ = self._create_inforequest_scenario()
        data = self._create_post_data(branch=branch2)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'branch', 'Select a valid choice. %s is not one of the available choices.' % branch2.pk)

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_branch_field_is_valid_only_with_branch_to_which_the_action_may_be_added(self):
        scenario = self._create_scenario(inforequest_scenario=[
                (u'advancement', self.good_scenario, self.bad_scenario),
            ])
        _, (_, [(good_branch, _), (bad_branch, _)]) = scenario.actions
        url = self._create_url(scenario)

        self._login_user()

        data = self._create_post_data(branch=bad_branch)
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'branch', 'Select a valid choice. %s is not one of the available choices.' % bad_branch.pk)
        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

        data = self._create_post_data(branch=good_branch)
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

    def test_branch_field_shows_only_branches_to_which_the_action_may_be_added(self):
        obligee = self._create_obligee(name=u'Obligee')
        scenario = self._create_scenario(inforequest_scenario=[
                (u'advancement', [obligee] + self.good_scenario, [obligee] + self.good_scenario, self.bad_scenario),
                # Make sure nothing can be added to outer branch
                u'appeal',
                u'affirmation',
            ])
        _, (_, [(good_branch1, _), (good_branch2, _), (bad_branch, _)]), _, _ = scenario.actions
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        choices = response.context[u'form'].fields[u'branch'].choices
        self.assertItemsEqual(choices, [(u'', u''), (good_branch1, u'Obligee'), (good_branch2, u'Obligee')])

    def test_branch_field_with_multiple_choices_shows_empty_choice_as_its_first_choice(self):
        scenario = self._create_scenario(inforequest_scenario=[
                (u'advancement', self.good_scenario, self.good_scenario),
            ])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        choices = response.context[u'form'].fields[u'branch'].choices
        self.assertEqual(choices[0], (u'', u''))

    def test_branch_field_with_only_one_choice_does_not_show_empty_choice(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        choices = response.context[u'form'].fields[u'branch'].choices
        self.assertEqual(len(choices), 1)
        self.assertNotEqual(choices[0][0], u'')

class EffectiveDateFieldTests(FieldsTests):

    def _create_post_data(self, **kwargs):
        kwargs.setdefault(u'effective_date', local_today())
        return super(EffectiveDateFieldTests, self)._create_post_data(**kwargs)

    def _tested_fields(self):
        return super(EffectiveDateFieldTests, self)._tested_fields() + [u'effective_date']


    def test_effective_date_field_initial_values(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertIsNone(response.context[u'form'][u'effective_date'].value())

    def test_effective_date_field_is_saved(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        scenario = self._create_scenario()
        timewarp.jump(local_datetime_from_local(u'2010-10-17 10:33:00'))
        data = self._create_post_data(branch=scenario.branch, effective_date=naive_date(u'2010-10-13'))
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        action = action_set.get()

        self.assertEqual(action.effective_date, naive_date(u'2010-10-13'))

    def test_effective_date_field_is_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, omit=[u'effective_date'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'effective_date', 'This field is required.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_effective_date_field_with_invalid_value_is_invalid(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, effective_date=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'effective_date', 'Enter a valid date.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_effective_date_field_may_not_be_older_than_previous_action(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, effective_date=naive_date(u'2010-10-04'))
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'effective_date', 'May not be older than previous action.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_effective_date_field_may_not_be_from_future(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, effective_date=naive_date(u'2010-10-06'))
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'effective_date', 'May not be from future.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_effective_date_field_may_not_be_older_than_one_month(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        scenario = self._create_scenario()
        timewarp.jump(local_datetime_from_local(u'2010-11-17 10:33:00'))
        data = self._create_post_data(branch=scenario.branch, effective_date=naive_date(u'2010-10-16'))
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'effective_date', 'May not be older than one month.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

class SubjectContentAttachmentsFieldsTests(FieldsTests):

    def _create_post_data(self, **kwargs):
        kwargs.setdefault(u'subject', u'Default Testint Subject')
        kwargs.setdefault(u'content', u'Default Testint Content')
        kwargs.setdefault(u'attachments', [])
        return super(SubjectContentAttachmentsFieldsTests, self)._create_post_data(**kwargs)

    def _tested_fields(self):
        return super(SubjectContentAttachmentsFieldsTests, self)._tested_fields() + [u'subject', u'content', u'attachments']


    def test_subject_content_and_attachments_fields_initial_values(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertIsNone(response.context[u'form'][u'subject'].value())
        self.assertIsNone(response.context[u'form'][u'content'].value())
        self.assertIsNone(response.context[u'form'][u'attachments'].value())

    def test_subject_content_and_attachments_fields_are_saved(self):
        self._login_user()
        scenario = self._create_scenario()
        attachment1 = self._create_attachment(generic_object=self._get_session(), name=u'filename.txt', content=u'content', content_type=u'text/plain')
        attachment2 = self._create_attachment(generic_object=self._get_session(), name=u'filename.html', content=u'<p>content</p>', content_type=u'text/html')
        data = self._create_post_data(branch=scenario.branch, subject=u'Subject', content=u'Content', attachments=u'%s,%s' % (attachment1.pk, attachment2.pk))
        url = self._create_url(scenario)

        with created_instances(scenario.branch.action_set) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        action = action_set.get()

        self.assertEqual(action.subject, u'Subject')
        self.assertEqual(action.content, u'Content')

        attachments = [(a.name, a.content, a.content_type) for a in action.attachment_set.all()]
        self.assertItemsEqual(attachments, [
            (u'filename.txt', u'content', u'text/plain'),
            (u'filename.html', u'<p>content</p>', u'text/html'),
            ])

    def test_subject_field_is_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, omit=[u'subject'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'subject', 'This field is required.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_subject_field_max_length(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, subject=u'x'*256)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'subject', 'Ensure this value has at most 255 characters (it has 256).')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_content_field_is_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, omit=[u'content'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'content', 'This field is required.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_attachments_field_is_not_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, omit=[u'attachments'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

    def test_attachments_field_with_invalid_attachment_is_invalid(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, attachments=u',47,')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'attachments', 'Invalid attachments.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_attachments_field_with_attachment_owned_by_another_session_is_invalid(self):
        self._login_user(self.user1)
        scenario = self._create_scenario()
        attachment = self._create_attachment(generic_object=self._get_session())
        data = self._create_post_data(branch=scenario.branch, attachments=u',%s,' % attachment.pk)
        url = self._create_url(scenario)
        self._logout_user()

        self._login_user(self.user1)
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'attachments', 'Invalid attachments.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_attachments_field_with_attachment_owned_by_session_is_valid(self):
        self._login_user()
        scenario = self._create_scenario()
        attachment = self._create_attachment()
        data = self._create_post_data(branch=scenario.branch, attachments=u',%s,' % attachment.pk)
        url = self._create_url(scenario)

        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

    def test_attachments_field_upload_url_func(self):
        self._login_user()
        scenario = self._create_scenario()
        attachment = self._create_attachment()
        url = self._create_url(scenario)

        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # ``download_url_func`` is not used if not loading from draft. So it may not be tested
        # without using drafts.
        form = response.context[u'form']
        rendered = form[u'attachments'].as_widget()
        upload_regexp = u'<input [^>]*type="file" [^>]*data-url="%s"[^>]*>' % re.escape(reverse(u'inforequests:upload_attachment'))
        self.assertRegexpMatches(rendered, upload_regexp)

class DeadlineFieldTests(FieldsTests):

    def _create_post_data(self, **kwargs):
        kwargs.setdefault(u'deadline', 47)
        return super(DeadlineFieldTests, self)._create_post_data(**kwargs)

    def _tested_fields(self):
        return super(DeadlineFieldTests, self)._tested_fields() + [u'deadline']


    def test_deadline_field_initial_value(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.context[u'form'][u'deadline'].value(), 10)

    def test_deadline_field_is_saved(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, deadline=13)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        action = action_set.get()

        self.assertEqual(action.deadline, 13)

    def test_deadline_field_is_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, omit=[u'deadline'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'deadline', 'This field is required.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_deadline_field_min_value(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, deadline=1)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'deadline', 'Ensure this value is greater than or equal to 2.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_deadline_field_max_value(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, deadline=101)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'deadline', 'Ensure this value is less than or equal to 100.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

class AdvancedToFieldsTests(FieldsTests):

    def _create_post_data(self, **kwargs):
        kwargs.setdefault(u'advanced_to_1', u'Default Testing Name 3')
        kwargs.setdefault(u'advanced_to_2', u'')
        kwargs.setdefault(u'advanced_to_3', u'')
        return super(AdvancedToFieldsTests, self)._create_post_data(**kwargs)

    def _tested_fields(self):
        return super(AdvancedToFieldsTests, self)._tested_fields() + [u'advanced_to_1', u'advanced_to_2', u'advanced_to_3']


    def test_advanced_to_fields_initial_values(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertIsNone(response.context[u'form'][u'advanced_to_1'].value())
        self.assertIsNone(response.context[u'form'][u'advanced_to_2'].value())
        self.assertIsNone(response.context[u'form'][u'advanced_to_3'].value())

    def test_advanced_to_fields_are_saved(self):
        obligee1 = self._create_obligee(name=u'Obligee1')
        obligee2 = self._create_obligee(name=u'Obligee2')
        obligee3 = self._create_obligee(name=u'Obligee3')
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, advanced_to_1=u'Obligee1', advanced_to_2=u'Obligee2', advanced_to_3=u'Obligee3')
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        action = action_set.get()

        advanced_to = action.advanced_to_set.all()
        self.assertEqual(len(advanced_to), 3)
        self.assertItemsEqual([p.obligee for p in advanced_to], [obligee1, obligee2, obligee3])
        self.assertItemsEqual([p.inforequest for p in advanced_to], [scenario.inforequest]*3)
        self.assertItemsEqual([[a.type for a in p.action_set.all()] for p in advanced_to], [[Action.TYPES.ADVANCED_REQUEST]]*3)
        self.assertItemsEqual([[a.effective_date for a in p.action_set.all()] for p in advanced_to], [[action.effective_date]]*3)

    def test_advanced_to_1_field_is_required(self):
        obligee2 = self._create_obligee(name=u'Obligee2')
        obligee3 = self._create_obligee(name=u'Obligee3')
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, omit=[u'advanced_to_1'], advanced_to_2=u'Obligee2', advanced_to_3=u'Obligee3')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'advanced_to_1', 'This field is required.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_advanced_to_2_and_3_are_not_required(self):
        obligee = self._create_obligee(name=u'Obligee')
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, advanced_to_1=u'Obligee', omit=[u'advanced_to_2', u'advanced_to_3'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

    def test_advanced_to_fields_may_not_advance_to_same_obligee(self):
        obligee = self._create_obligee(name=u'Obligee')
        scenario = self._create_scenario(inforequest_args=[obligee])
        data = self._create_post_data(branch=scenario.branch, advanced_to_1=u'Obligee')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'advanced_to_1', 'May not advance to the same obligee.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_advanced_to_fields_may_not_advance_twice_to_same_obligee(self):
        obligee = self._create_obligee(name=u'Obligee')
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, advanced_to_1=u'Obligee', advanced_to_2=u'Obligee')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'advanced_to_2', 'May not advance twice to the same obligee.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

class DisclosureLevelFieldTests(FieldsTests):

    def _create_post_data(self, **kwargs):
        kwargs.setdefault(u'disclosure_level', Action.DISCLOSURE_LEVELS.PARTIAL)
        return super(DisclosureLevelFieldTests, self)._create_post_data(**kwargs)

    def _tested_fields(self):
        return super(DisclosureLevelFieldTests, self)._tested_fields() + [u'disclosure_level']


    def test_disclosure_level_field_initial_value(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertIsNone(response.context[u'form'][u'disclosure_level'].value())

    def test_disclosure_level_field_is_saved(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, disclosure_level=Action.DISCLOSURE_LEVELS.FULL)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        action = action_set.get()

        self.assertEqual(action.disclosure_level, Action.DISCLOSURE_LEVELS.FULL)

    def test_disclosure_level_field_is_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, omit=[u'disclosure_level'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'disclosure_level', 'This field is required.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_disclosure_level_field_with_invalid_value_is_invalid(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, disclosure_level=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'disclosure_level', 'Select a valid choice. invalid is not one of the available choices.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

class RefusalReasonFieldTests(FieldsTests):

    def _create_post_data(self, **kwargs):
        kwargs.setdefault(u'refusal_reason', Action.REFUSAL_REASONS.OTHER_REASON)
        return super(RefusalReasonFieldTests, self)._create_post_data(**kwargs)

    def _tested_fields(self):
        return super(RefusalReasonFieldTests, self)._tested_fields() + [u'refusal_reason']


    def test_refusal_reason_field_initial_value(self):
        scenario = self._create_scenario()
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertIsNone(response.context[u'form'][u'refusal_reason'].value())

    def test_refusal_reason_field_is_saved(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, refusal_reason=Action.REFUSAL_REASONS.PERSONAL)
        url = self._create_url(scenario)

        self._login_user()
        with created_instances(scenario.branch.action_set) as action_set:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        action = action_set.get()

        self.assertEqual(action.refusal_reason, Action.REFUSAL_REASONS.PERSONAL)

    def test_refusal_reason_field_is_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, omit=[u'refusal_reason'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'refusal_reason', 'This field is required.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')

    def test_refusal_reason_field_with_invalid_value_is_invalid(self):
        scenario = self._create_scenario()
        data = self._create_post_data(branch=scenario.branch, refusal_reason=u'invalid')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertFormError(response, u'form', u'refusal_reason', 'Select a valid choice. invalid is not one of the available choices.')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'invalid')


class DraftBranchFieldTests(BranchFieldTests):

    def test_draft_branch_field_is_loaded_from_draft(self):
        scenario = self._create_scenario(draft_args=dict())
        url = self._create_url(scenario)

        scenario.draft.branch = scenario.branch
        scenario.draft.save()

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.context[u'form'][u'branch'].value(), scenario.branch)

    def test_draft_branch_field_is_saved_to_draft(self):
        scenario = self._create_scenario(draft_args=dict(branch=None))
        data = self._create_post_data(button=u'draft', branch=scenario.branch)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        draft = ActionDraft.objects.get(pk=scenario.draft.pk)
        self.assertEqual(draft.branch, scenario.branch)

    def test_draft_branch_field_with_empty_value_is_saved_to_draft(self):
        scenario = self._create_scenario(draft_args=dict())
        scenario.draft.branch = scenario.branch
        scenario.draft.save()
        data = self._create_post_data(button=u'draft', branch=u'')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        draft = ActionDraft.objects.get(pk=scenario.draft.pk)
        self.assertIsNone(draft.branch)

    def test_draft_branch_field_is_not_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', omit=[u'branch'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

class DraftEffectiveDateFieldTests(EffectiveDateFieldTests):

    def test_draft_effective_date_field_is_loaded_from_draft(self):
        scenario = self._create_scenario(draft_args=dict(effective_date=naive_date(u'2010-10-13')))
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.context[u'form'][u'effective_date'].value(), naive_date(u'2010-10-13'))

    def test_draft_effective_date_field_is_saved_to_draft(self):
        scenario = self._create_scenario(draft_args=dict(effective_date=naive_date(u'2010-10-05')))
        data = self._create_post_data(button=u'draft', effective_date=naive_date(u'2010-10-13'))
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        draft = ActionDraft.objects.get(pk=scenario.draft.pk)
        self.assertEqual(draft.effective_date, naive_date(u'2010-10-13'))

    def test_draft_effective_date_field_with_empty_value_is_saved_to_draft(self):
        scenario = self._create_scenario(draft_args=dict(effective_date=naive_date(u'2010-10-05')))
        data = self._create_post_data(button=u'draft', effective_date=u'')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        draft = ActionDraft.objects.get(pk=scenario.draft.pk)
        self.assertIsNone(draft.effective_date)

    def test_draft_effective_date_field_is_not_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', omit=[u'effective_date'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

    def test_draft_effective_date_may_be_older_than_previous_action(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', effective_date=naive_date(u'2003-07-04'))
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

    def test_draft_effective_date_may_be_from_future(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', effective_date=naive_date(u'2014-11-06'))
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

    def test_draft_effective_date_may_be_older_than_one_month(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        scenario = self._create_scenario()
        timewarp.jump(local_datetime_from_local(u'2012-11-17 10:33:00'))
        data = self._create_post_data(button=u'draft', effective_date=naive_date(u'2010-10-16'))
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

class DraftSubjectContentAttachmentsFieldsTests(SubjectContentAttachmentsFieldsTests):

    def test_draft_subject_content_and_attachments_fields_are_loaded_from_draft(self):
        scenario = self._create_scenario(draft_args=dict(subject=u'Subject', content=u'Content'))
        attachment1 = self._create_attachment(generic_object=scenario.draft)
        attachment2 = self._create_attachment(generic_object=scenario.draft)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.context[u'form'][u'subject'].value(), u'Subject')
        self.assertEqual(response.context[u'form'][u'content'].value(), u'Content')
        self.assertItemsEqual(response.context[u'form'][u'attachments'].value(), [attachment1, attachment2])

    def test_draft_subject_content_and_attachments_fields_are_saved_to_draft(self):
        self._login_user()
        scenario = self._create_scenario(draft_args=dict(subject=u'Old Subject', content=u'Old Content'))
        attachment1 = self._create_attachment(generic_object=scenario.draft)
        attachment2 = self._create_attachment(generic_object=scenario.draft)
        attachment3 = self._create_attachment()
        data = self._create_post_data(button=u'draft', subject=u'New Subject', content=u'New Content',
                attachments=u'%s,%s' % (attachment2.pk, attachment3.pk))
        url = self._create_url(scenario)

        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        draft = ActionDraft.objects.get(pk=scenario.draft.pk)
        self.assertEqual(draft.subject, u'New Subject')
        self.assertEqual(draft.content, u'New Content')
        self.assertItemsEqual(draft.attachment_set.all(), [attachment2, attachment3])

    def test_draft_subject_content_and_attachments_fields_are_not_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', omit=[u'subject', u'content', u'attachments'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

class DraftDeadlineFieldTests(DeadlineFieldTests):

    def test_draft_deadline_field_is_loaded_from_draft(self):
        scenario = self._create_scenario(draft_args=dict(deadline=13))
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.context[u'form'][u'deadline'].value(), 13)

    def test_draft_deadline_field_is_saved_to_draft(self):
        scenario = self._create_scenario(draft_args=dict(deadline=13))
        data = self._create_post_data(button=u'draft', deadline=17)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        draft = ActionDraft.objects.get(pk=scenario.draft.pk)
        self.assertEqual(draft.deadline, 17)

    def test_draft_deadline_field_is_not_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', omit=[u'deadline'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

class DraftAdvancedToFieldsTests(AdvancedToFieldsTests):

    def test_draft_advanced_to_fields_are_loaded_from_draft(self):
        obligee1 = self._create_obligee(name=u'Obligee1')
        obligee2 = self._create_obligee(name=u'Obligee2')
        obligee3 = self._create_obligee(name=u'Obligee3')
        scenario = self._create_scenario(draft_args=dict())
        scenario.draft.obligee_set = [obligee1, obligee2, obligee3]
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.context[u'form'][u'advanced_to_1'].value(), obligee1)
        self.assertEqual(response.context[u'form'][u'advanced_to_2'].value(), obligee2)
        self.assertEqual(response.context[u'form'][u'advanced_to_3'].value(), obligee3)

    def test_draft_advanced_to_fields_are_loaded_from_draft_with_fewer_obligees(self):
        obligee1 = self._create_obligee(name=u'Obligee1')
        scenario = self._create_scenario(draft_args=dict())
        scenario.draft.obligee_set = [obligee1]
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.context[u'form'][u'advanced_to_1'].value(), obligee1)
        self.assertIsNone(response.context[u'form'][u'advanced_to_2'].value())
        self.assertIsNone(response.context[u'form'][u'advanced_to_3'].value())

    def test_draft_advanced_to_fields_are_loaded_from_draft_with_more_obligees(self):
        obligee1 = self._create_obligee(name=u'Obligee1')
        obligee2 = self._create_obligee(name=u'Obligee2')
        obligee3 = self._create_obligee(name=u'Obligee3')
        obligee4 = self._create_obligee(name=u'Obligee4')
        scenario = self._create_scenario(draft_args=dict())
        scenario.draft.obligee_set = [obligee1, obligee2, obligee3, obligee4]
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.context[u'form'][u'advanced_to_1'].value(), obligee1)
        self.assertEqual(response.context[u'form'][u'advanced_to_2'].value(), obligee2)
        self.assertEqual(response.context[u'form'][u'advanced_to_3'].value(), obligee3)

    def test_draft_advanced_to_fields_are_saved_to_draft(self):
        obligee1 = self._create_obligee(name=u'Obligee1')
        obligee2 = self._create_obligee(name=u'Obligee2')
        obligee3 = self._create_obligee(name=u'Obligee3')
        obligee4 = self._create_obligee(name=u'Obligee4')
        scenario = self._create_scenario(draft_args=dict())
        scenario.draft.obligee_set = [obligee1, obligee2]
        data = self._create_post_data(button=u'draft', advanced_to_1=u'Obligee2', advanced_to_2=u'Obligee3', advanced_to_3=u'Obligee4')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        draft = ActionDraft.objects.get(pk=scenario.draft.pk)
        self.assertItemsEqual(draft.obligee_set.all(), [obligee2, obligee3, obligee4])

    def test_draft_advanced_to_fields_are_not_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', omit=[u'advanced_to_1', u'advanced_to_2', u'advanced_to_3'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

    def test_draft_advanced_to_fields_may_advance_to_same_obligee(self):
        obligee = self._create_obligee(name=u'Obligee')
        scenario = self._create_scenario(inforequest_args=[obligee])
        data = self._create_post_data(button=u'draft', advanced_to_1=u'Obligee')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

    def test_draft_advanced_to_fields_may_advance_twice_to_same_obligee(self):
        obligee = self._create_obligee(name=u'Obligee')
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', advanced_to_1=u'Obligee', advanced_to_2=u'Obligee')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

class DraftDisclosureLevelFieldTests(DisclosureLevelFieldTests):

    def test_draft_disclosure_level_field_is_loaded_from_draft(self):
        scenario = self._create_scenario(draft_args=dict(disclosure_level=Action.DISCLOSURE_LEVELS.FULL))
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.context[u'form'][u'disclosure_level'].value(), Action.DISCLOSURE_LEVELS.FULL)

    def test_draft_disclosure_level_field_is_saved_to_draft(self):
        scenario = self._create_scenario(draft_args=dict(disclosure_level=Action.DISCLOSURE_LEVELS.FULL))
        data = self._create_post_data(button=u'draft', disclosure_level=Action.DISCLOSURE_LEVELS.NONE)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        draft = ActionDraft.objects.get(pk=scenario.draft.pk)
        self.assertEqual(draft.disclosure_level, Action.DISCLOSURE_LEVELS.NONE)

    def test_draft_disclosure_level_field_with_empty_value_is_saved_to_draft(self):
        scenario = self._create_scenario(draft_args=dict(disclosure_level=Action.DISCLOSURE_LEVELS.FULL))
        data = self._create_post_data(button=u'draft', disclosure_level=u'')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        draft = ActionDraft.objects.get(pk=scenario.draft.pk)
        self.assertIsNone(draft.disclosure_level)

    def test_draft_disclosure_level_field_is_not_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', omit=[u'disclosure_level'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')

class DraftRefusalReasonFieldTests(RefusalReasonFieldTests):

    def test_draft_refusal_reason_field_is_loaded_from_draft(self):
        scenario = self._create_scenario(draft_args=dict(refusal_reason=Action.REFUSAL_REASONS.CONFIDENTIAL))
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.get(url, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        self.assertEqual(response.context[u'form'][u'refusal_reason'].value(), Action.REFUSAL_REASONS.CONFIDENTIAL)

    def test_draft_refusal_reason_field_is_saved_to_draft(self):
        scenario = self._create_scenario(draft_args=dict(refusal_reason=Action.REFUSAL_REASONS.CONFIDENTIAL))
        data = self._create_post_data(button=u'draft', refusal_reason=Action.REFUSAL_REASONS.PERSONAL)
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        draft = ActionDraft.objects.get(pk=scenario.draft.pk)
        self.assertEqual(draft.refusal_reason, Action.REFUSAL_REASONS.PERSONAL)

    def test_draft_refusal_reason_field_with_empty_value_is_saved_to_draft(self):
        scenario = self._create_scenario(draft_args=dict(refusal_reason=Action.REFUSAL_REASONS.CONFIDENTIAL))
        data = self._create_post_data(button=u'draft', refusal_reason=u'')
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        draft = ActionDraft.objects.get(pk=scenario.draft.pk)
        self.assertIsNone(draft.refusal_reason)

    def test_draft_refusal_reason_field_is_not_required(self):
        scenario = self._create_scenario()
        data = self._create_post_data(button=u'draft', omit=[u'refusal_reason'])
        url = self._create_url(scenario)

        self._login_user()
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')

        data = json.loads(response.content)
        self.assertEqual(data[u'result'], u'success')
