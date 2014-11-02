# vim: expandtab
# -*- coding: utf-8 -*-
from testfixtures import TempDirectory

from django.core.files.base import ContentFile
from django.template import Context, Template
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from poleno.timewarp import timewarp
from poleno.attachments.models import Attachment
from poleno.mail.models import Message
from poleno.utils.date import utc_now, local_today
from chcemvediet.apps.obligees.models import Obligee

from ..models import InforequestDraft, Inforequest, InforequestEmail, Paperwork, Action, ActionDraft

class InforequestsTestCaseMixin(TestCase):

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
        self.obligee1 = self._create_obligee()
        self.obligee2 = self._create_obligee()
        self.obligee3 = self._create_obligee()

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
        return user

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
                u'file': ContentFile(content, name=u'filename.txt'),
                u'name': u'filename.txt',
                u'content_type': u'text/plain',
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
                u'subject': u'Default Testing Subject',
                u'content': u'Default Testing Content',
                })

    def _create_inforequest(self, **kwargs):
        return self._call_with_defaults(Inforequest.objects.create, kwargs, {
                u'applicant': self.user1,
                })

    def _create_inforequest_scenario__action(self, inforequest, paperwork, args):
        if isinstance(args, basestring):
            args = [args]

        action_name = args.pop(0)
        if action_name == u'request':
            action_type = Action.TYPES.REQUEST
            mail_type = Message.TYPES.OUTBOUND
        elif action_name == u'clarification_response':
            action_type = Action.TYPES.CLARIFICATION_RESPONSE
            mail_type = Message.TYPES.OUTBOUND
        elif action_name == u'appeal':
            action_type = Action.TYPES.APPEAL
            mail_type = None
        elif action_name == u'confirmation':
            action_type = Action.TYPES.CONFIRMATION
            mail_type = Message.TYPES.INBOUND
        elif action_name == u'extension':
            action_type = Action.TYPES.EXTENSION
            mail_type = Message.TYPES.INBOUND
        elif action_name == u'advancement':
            action_type = Action.TYPES.ADVANCEMENT
            mail_type = Message.TYPES.INBOUND
        elif action_name == u'clarification_request':
            action_type = Action.TYPES.CLARIFICATION_REQUEST
            mail_type = Message.TYPES.INBOUND
        elif action_name == u'disclosure':
            action_type = Action.TYPES.DISCLOSURE
            mail_type = Message.TYPES.INBOUND
        elif action_name == u'refusal':
            action_type = Action.TYPES.REFUSAL
            mail_type = Message.TYPES.INBOUND
        elif action_name == u'affirmation':
            action_type = Action.TYPES.AFFIRMATION
            mail_type = None
        elif action_name == u'reversion':
            action_type = Action.TYPES.REVERSION
            mail_type = None
        elif action_name == u'remandment':
            action_type = Action.TYPES.REMANDMENT
            mail_type = None
        elif action_name == u'advanced_request':
            action_type = Action.TYPES.ADVANCED_REQUEST
            mail_type = None
        elif action_name == u'expiration':
            action_type = Action.TYPES.EXPIRATION
            mail_type = None
        else:
            assert action_name == u'appeal_expiration'
            action_type = Action.TYPES.APPEAL_EXPIRATION
            mail_type = None

        email = None
        action_means = args.pop(0) if args and args[0] in [u'email', u'smail', u'default'] else u'default'
        if action_means == u'email' or (action_means == u'default' and mail_type is not None):
            assert mail_type is not None
            email = self._create_message(type=mail_type)
            rel_type = InforequestEmail.TYPES.OBLIGEE_ACTION if mail_type == Message.TYPES.INBOUND else InforequestEmail.TYPES.APPLICANT_ACTION
            rel = InforequestEmail.objects.create(inforequest=inforequest, email=email, type=rel_type)
        action = self._create_action(paperwork=paperwork, email=email, type=action_type)

        if action_type == Action.TYPES.ADVANCEMENT:
            paperworks = []
            for arg in args or [[]]:
                obligee = arg.pop(0) if arg and isinstance(arg[0], Obligee) else self.obligee1
                paperworks.append(self._create_inforequest_scenario__paperwork(inforequest, obligee, action, [u'advanced_request'] + arg))
            return action, paperworks

        assert len(args) == 0
        return action

    def _create_inforequest_scenario__paperwork(self, inforequest, obligee, advanced_by, args):
        paperwork = Paperwork.objects.create(inforequest=inforequest, obligee=obligee, advanced_by=advanced_by)
        actions = []
        for arg in args:
            actions.append(self._create_inforequest_scenario__action(inforequest, paperwork, arg))
        return paperwork, actions

    def _create_inforequest_scenario(self, *args):
        args = list(args)
        applicant = args.pop(0) if args and isinstance(args[0], User) else self.user1
        obligee = args.pop(0) if args and isinstance(args[0], Obligee) else self.obligee1
        inforequest = Inforequest.objects.create(applicant=applicant)
        paperwork, actions = self._create_inforequest_scenario__paperwork(inforequest, obligee, None, [u'request'] + args)
        return inforequest, paperwork, actions

    def _create_inforequest_email(self, **kwargs):
        inforequest = kwargs.pop(u'inforequest')
        reltype = kwargs.pop(u'reltype', InforequestEmail.TYPES.UNDECIDED)
        email = self._create_message(**kwargs)
        rel = InforequestEmail.objects.create(inforequest=inforequest, email=email, type=reltype)
        return email, rel

    def _create_paperwork(self, **kwargs):
        return self._call_with_defaults(Paperwork.objects.create, kwargs, {
                u'obligee': self.obligee1,
                })

    def _create_action(self, **kwargs):
        return self._call_with_defaults(Action.objects.create, kwargs, {
                u'subject': u'Default Testing Subject',
                u'content': u'Default Testing Content',
                u'effective_date': local_today(),
                })

    def _create_action_draft(self, **kwargs):
        return self._call_with_defaults(ActionDraft.objects.create, kwargs, {
                u'subject': u'Default Testing Subject',
                u'content': u'Default Testing Content',
                })

    def _render(self, template, **context):
        return Template(template).render(Context(context))
