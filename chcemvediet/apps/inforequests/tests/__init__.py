# vim: expandtab
# -*- coding: utf-8 -*-
import mock
import contextlib
from testfixtures import TempDirectory

from django.core.files.base import ContentFile
from django.db import connection
from django.template import Context, Template
from django.template.loader import render_to_string
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.test.utils import override_settings, CaptureQueriesContext

from poleno.timewarp import timewarp
from poleno.attachments.models import Attachment
from poleno.mail.models import Message, Recipient
from poleno.utils.date import utc_now, local_today
from chcemvediet.apps.obligees.models import Obligee

from ..models import InforequestDraft, Inforequest, InforequestEmail, Branch, Action, ActionDraft

class InforequestsTestCaseMixin(TestCase):

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
                self.pre_mock_render_to_string(*args, **kwargs)
            with CaptureQueriesContext(connection) as captured:
                res = render_to_string(*args, **kwargs)
            queries.append(captured)
            return res

        with mock.patch(u'chcemvediet.apps.inforequests.views.render', mock_render):
            with mock.patch(u'chcemvediet.apps.inforequests.views.render_to_string', mock_render_to_string):
                yield

        self.assertEqual(len(queries), len(patterns), u'%d renders executed, %d expected' % (len(queries), len(patterns)))
        for render_queries, render_patterns in zip(queries, patterns):
            self.assertEqual(len(render_queries), len(render_patterns), u'\n'.join([
                u'%d queries executed, %d expected' % (len(render_queries), len(render_patterns)),
                u'Captured queries were:',
                u'\n'.join(q[u'sql'] for q in render_queries),
                u'Expected patterns were:',
                u'\n'.join(render_patterns),
                ]))
            for query, pattern in zip(render_queries, render_patterns):
                self.assertRegexpMatches(query[u'sql'], pattern)


    def _pre_setup(self):
        super(InforequestsTestCaseMixin, self)._pre_setup()
        timewarp.enable()
        timewarp.reset()
        self.tempdir = TempDirectory()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.tempdir.path,
            EMAIL_BACKEND=u'poleno.mail.backend.EmailBackend',
            PASSWORD_HASHERS=(u'django.contrib.auth.hashers.MD5PasswordHasher',),
            )
        self.settings_override.enable()

        self.user1 = self._create_user()
        self.user2 = self._create_user()
        self.obligee1 = self._create_obligee(name=u'Default Testing Name 1')
        self.obligee2 = self._create_obligee(name=u'Default Testing Name 2')
        self.obligee3 = self._create_obligee(name=u'Default Testing Name 3')

    def _post_teardown(self):
        self.settings_override.disable()
        self.tempdir.cleanup()
        timewarp.reset()
        super(InforequestsTestCaseMixin, self)._post_teardown()


    def _call_with_defaults(self, func, kwargs, defaults):
        omit = kwargs.pop(u'omit', [])
        defaults.update(kwargs)
        for key in omit:
            defaults.pop(key, None)
        return func(**defaults)

    def _create_user(self, **kwargs):
        try:
            tag = u'%s' % (User.objects.latest('pk').pk + 1)
        except User.DoesNotExist:
            tag = u'1'
        street = kwargs.pop(u'street', u'Default User Street')
        city = kwargs.pop(u'city', u'Default User City')
        zip = kwargs.pop(u'zip', u'00000')
        email_verified = kwargs.pop(u'email_verified', True)
        user = self._call_with_defaults(User.objects.create_user, kwargs, {
                u'username': 'default_testing_username_%s' % tag,
                u'first_name': 'Default Testing First Name',
                u'last_name': 'Default Testing Last Name',
                u'email': 'default_testing_mail_%s@a.com' % tag,
                u'password': 'default_testing_secret',
                })
        user.profile.street = street
        user.profile.city = city
        user.profile.zip = zip
        user.profile.save()
        if email_verified:
            user.emailaddress_set.create(email=user.email, verified=True)
        return user

    def _login_user(self, user=None, password=u'default_testing_secret'):
        if user is None:
            user = self.user1
        self.client.login(username=user.username, password=password)

    def _logout_user(self):
        self.client.logout()

    def _get_session(self):
        if hasattr(self.client.session, u'session_key'):
            return Session.objects.get(session_key=self.client.session.session_key)
        return None

    def _create_obligee(self, **kwargs):
        return self._call_with_defaults(Obligee.objects.create, kwargs, {
                u'name': u'Default Testing Name',
                u'street': u'Default Testing Street',
                u'city': u'Default Testing City',
                u'zip': u'00000',
                u'emails': u'default_testing_mail@example.com',
                u'status': Obligee.STATUSES.PENDING,
                })

    def _create_attachment(self, **kwargs):
        content = kwargs.pop(u'content', u'Default Testing Content')
        return self._call_with_defaults(Attachment.objects.create, kwargs, {
                u'generic_object': self._get_session(),
                u'file': ContentFile(content, name=u'filename.txt'),
                u'name': u'filename.txt',
                u'content_type': u'text/plain',
                })

    def _create_recipient(self, **kwargs):
        return self._call_with_defaults(Recipient.objects.create, kwargs, {
            u'name': u'Default Testing Name',
            u'mail': u'default_testing_mail@example.com',
            u'type': Recipient.TYPES.TO,
            u'status': Recipient.STATUSES.INBOUND,
            u'status_details': u'',
            u'remote_id': u'',
            })

    def _create_message(self, **kwargs):
        return self._call_with_defaults(Message.objects.create, kwargs, {
            u'type': Message.TYPES.OUTBOUND,
            u'processed': utc_now(),
            u'from_name': u'Default Testing From Name',
            u'from_mail': u'default_testing_from_mail@example.com',
            u'received_for': u'default_testing_for_mail@example.com',
            u'subject': u'Default Testing Subject',
            u'text': u'Default Testing Text Content',
            u'html': u'<p>Default Testing HTML Content</p>',
            })

    def _create_inforequest_draft(self, **kwargs):
        return self._call_with_defaults(InforequestDraft.objects.create, kwargs, {
                u'applicant': self.user1,
                u'obligee': self.obligee1,
                u'subject': [u'Default Testing Subject'],
                u'content': [u'Default Testing Content'],
                })

    def _create_inforequest(self, **kwargs):
        return self._call_with_defaults(Inforequest.objects.create, kwargs, {
                u'applicant': self.user1,
                })

    def _create_inforequest_scenario__action(self, inforequest, branch, args):
        action_name = args.pop(0)
        action_type = getattr(Action.TYPES, action_name.upper())
        action_extra = args.pop() if args and isinstance(args[0], dict) else {}
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
                    default_from_name, default_from_mail = next(branch.obligee.emails_parsed)
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
        args = [[a] if isinstance(a, basestring) else list(a) for a in args]
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
        applicant = args.pop(0) if args and isinstance(args[0], User) else self.user1
        obligee = args.pop(0) if args and isinstance(args[0], Obligee) else self.obligee1
        extra = args.pop(0) if args and isinstance(args[0], dict) else {}
        inforequest = Inforequest.objects.create(applicant=applicant, **extra)
        branch, actions = self._create_inforequest_scenario__branch(inforequest, obligee, None, u'request', args)
        return inforequest, branch, actions

    def _create_inforequest_email(self, **kwargs):
        create = object()

        relargs = {
                u'inforequest': kwargs.pop(u'inforequest', None),
                u'type': kwargs.pop(u'reltype', InforequestEmail.TYPES.UNDECIDED),
                u'email': kwargs.pop(u'email', create),
                }

        omit = kwargs.get(u'omit', [])
        for kwarg, relarg in ((u'inforequest', u'inforequest'), (u'reltype', u'type'), (u'email', u'email')):
            if kwarg in omit:
                relargs.pop(relarg)
                omit.remove(kwarg)

        if relargs.get(u'email') is create:
            relargs[u'email'] = self._create_message(**kwargs)

        rel = InforequestEmail.objects.create(**relargs)
        email = relargs.get(u'email')
        return email, rel

    def _create_branch(self, **kwargs):
        return self._call_with_defaults(Branch.objects.create, kwargs, {
                u'obligee': self.obligee1,
                })

    def _create_action(self, **kwargs):
        return self._call_with_defaults(Action.objects.create, kwargs, {
                u'type': Action.TYPES.REQUEST,
                u'subject': u'Default Testing Subject',
                u'content': u'Default Testing Content',
                u'effective_date': local_today(),
                })

    def _create_action_draft(self, **kwargs):
        return self._call_with_defaults(ActionDraft.objects.create, kwargs, {
                u'type': ActionDraft.TYPES.REQUEST,
                u'subject': u'Default Testing Subject',
                u'content': u'Default Testing Content',
                })
