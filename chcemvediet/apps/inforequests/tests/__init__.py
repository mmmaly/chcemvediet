# vim: expandtab
# -*- coding: utf-8 -*-
import re
import mock
import contextlib
from testfixtures import TempDirectory

from django.db import connection
from django.template.loader import render_to_string
from django.shortcuts import render
from django.contrib.auth.models import User
from django.test.utils import override_settings, CaptureQueriesContext

from poleno.timewarp import timewarp
from poleno.mail.models import Message, Recipient
from chcemvediet.apps.obligees.models import Obligee
from chcemvediet.tests import ChcemvedietTestCaseMixin

from ..models import Inforequest, InforequestEmail, Branch, Action


class InforequestsTestCaseMixin(ChcemvedietTestCaseMixin):

    @staticmethod
    def _extract_query_sql(sql):
        u"""Extract bare SQL from query format. Handles both Django 1.8 format
        (QUERY = u'...' - PARAMS = (...)) and Django 1.9+ format (raw SQL)."""
        match = re.match(r"^QUERY = u'(.*)'( - PARAMS = .*)$", sql, re.DOTALL)
        if match:
            return match.group(1)
        return sql

    @staticmethod
    def _normalize_pattern(pattern):
        u"""Replace %s placeholders in query patterns with regex matching actual values,
        for compatibility with Django 1.9+ which inlines parameter values in logged SQL."""
        return pattern.replace(u'%s', u'\\S+')

    @contextlib.contextmanager
    def assertQueriesDuringRender(self, *patterns, **kwargs):
        u"""
        Use to assert that views prefetch all related models before rendering their templates.
        Views should prefetch their related models to prevent templates from making database
        queries in a loop.
        """
        pre_mock_render = kwargs.pop(u'pre_mock_render', None)
        pre_mock_render_to_string = kwargs.pop(u'pre_mock_render_to_string', None)
        queries = []
        def mock_render(*args, **kwargs):
            if pre_mock_render:
                pre_mock_render(*args, **kwargs)
            with CaptureQueriesContext(connection) as captured:
                res = render(*args, **kwargs)
            queries.append(captured)
            return res
        def mock_render_to_string(*args, **kwargs):
            if pre_mock_render_to_string: # pragma: no cover
                pre_mock_render_to_string(*args, **kwargs)
            with CaptureQueriesContext(connection) as captured:
                res = render_to_string(*args, **kwargs)
            queries.append(captured)
            return res

        with mock.patch(u'chcemvediet.apps.inforequests.views.inforequest.render', mock_render):
            with mock.patch(u'chcemvediet.apps.inforequests.views.shortcuts.render', mock_render):
                with mock.patch(u'chcemvediet.apps.inforequests.views.shortcuts.render_to_string', mock_render_to_string):
                    yield

        self.assertEqual(len(queries), len(patterns), u'%d renders executed, %d expected' % (len(queries), len(patterns)))
        for render_queries, render_patterns in zip(queries, patterns):
            self.assertEqual(len(render_queries), len(render_patterns), u'\n'.join([
                u'%d queries executed, %d expected' % (len(render_queries), len(render_patterns)),
                u'Captured queries were:',
                u'\n'.join(self._extract_query_sql(q[u'sql']) for q in render_queries),
                u'Expected patterns were:',
                u'\n'.join(render_patterns),
                ]))
            for query, pattern in zip(render_queries, render_patterns):
                self.assertRegexpMatches(self._extract_query_sql(query[u'sql']), self._normalize_pattern(pattern))


    def _pre_setup(self):
        super(InforequestsTestCaseMixin, self)._pre_setup()
        timewarp.enable()
        timewarp.reset()
        self.tempdir = TempDirectory()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.tempdir.path,
            EMAIL_BACKEND=u'poleno.mail.backend.EmailBackend',
            )
        self.settings_override.enable()

    def _post_teardown(self):
        self.settings_override.disable()
        self.tempdir.cleanup()
        timewarp.reset()
        super(InforequestsTestCaseMixin, self)._post_teardown()


    def _create_inforequest_scenario__action(self, inforequest, branch, args):
        action_name = args.pop(0)
        action_type = getattr(Action.TYPES, action_name.upper())
        action_extra = args.pop(0) if args and isinstance(args[0], dict) else {}
        action_args = {u'branch': branch, u'type': action_type}

        if action_type in Action.APPLICANT_ACTION_TYPES or action_type in Action.OBLIGEE_ACTION_TYPES:
            email_extra = action_extra.pop(u'email', {})
            if email_extra is not False:
                if action_type in Action.APPLICANT_ACTION_TYPES:
                    default_mail_type = Message.TYPES.OUTBOUND
                    default_rel_type = InforequestEmail.TYPES.APPLICANT_ACTION
                    default_from_name, default_from_mail = u'', inforequest.applicant.email
                    default_recipients = [{u'name': n, u'mail': a} for n, a in branch.obligee.emails_parsed]
                    default_recipient_status = Recipient.STATUSES.SENT
                else:
                    default_mail_type = Message.TYPES.INBOUND
                    default_rel_type = InforequestEmail.TYPES.OBLIGEE_ACTION
                    default_from_name, default_from_mail = branch.obligee.emails_parsed[0]
                    default_recipients = [{u'mail': inforequest.applicant.email}]
                    default_recipient_status = Recipient.STATUSES.INBOUND

                email_args = {
                        u'inforequest': inforequest,
                        u'reltype': default_rel_type,
                        u'type': default_mail_type,
                        u'from_name': default_from_name,
                        u'from_mail': default_from_mail,
                        }
                email_args.update(email_extra)
                email, _ = self._create_inforequest_email(**email_args)
                action_args[u'email'] = email

                for recipient_extra in action_extra.pop(u'recipients', default_recipients):
                    recipient_args = {
                            u'message': email,
                            u'type': Recipient.TYPES.TO,
                            u'status': default_recipient_status,
                            }
                    recipient_args.update(recipient_extra)
                    self._create_recipient(**recipient_args)

        action_args.update(action_extra)
        action = self._create_action(**action_args)

        if action_type == Action.TYPES.ADVANCEMENT:
            branches = []
            for arg in args or [[]]:
                obligee = arg.pop(0) if arg and isinstance(arg[0], Obligee) else self.obligee1
                branches.append(self._create_inforequest_scenario__branch(inforequest, obligee, action, u'advanced_request', arg))
            return action, branches

        assert len(args) == 0
        return action

    def _create_inforequest_scenario__branch(self, inforequest, obligee, advanced_by, base_action, args):
        branch = Branch.objects.create(inforequest=inforequest, obligee=obligee, advanced_by=advanced_by)
        args = [[a] if isinstance(a, str) else list(a) for a in args]
        if not args or args[0][0] != base_action:
            args[0:0] = [[base_action]]
        actions = []
        for arg in args:
            actions.append(self._create_inforequest_scenario__action(inforequest, branch, arg))
        return branch, actions

    def _create_inforequest_scenario(self, *args):
        u"""
        Synopsis:
            _create_inforequest_scenario([User], [Obligee], [<action>], ...)

        Where:
            <action> ::= <action_name> | tuple(<action_name>, [<action_extra>], [<advancement>], ...)

            <action_name>  ::= "request", "confirmation", ...
            <action_extra> ::= dict([email=<email>], [recipients=<recipients>], <action_args>)
            <email>        ::= dict(<email_args>)
            <recipients>   ::= list(<recipient>, ...)
            <recipient>    ::= dict(<recipient_args>)

            <advancement>  ::= list([Obligee], [<action>], ...)

        Where <action_args> are arguments for ``_create_action()``, <email_args> arguments for
        ``_create_message()`` and <recipient_args> arguments for ``_create_recipient()``.
        """
        args = list(args)
        applicant = args.pop(0) if args and isinstance(args[0], User) else self.user
        obligee = args.pop(0) if args and isinstance(args[0], Obligee) else self.obligee
        extra = args.pop(0) if args and isinstance(args[0], dict) else {}
        inforequest = Inforequest.objects.create(applicant=applicant, **extra)
        branch, actions = self._create_inforequest_scenario__branch(inforequest, obligee, None, u'request', args)
        return inforequest, branch, actions
