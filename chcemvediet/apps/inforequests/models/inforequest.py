# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.db import models, IntegrityError, transaction, connection
from django.db.models import Q, Prefetch
from django.conf import settings
from django.utils.functional import cached_property
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from aggregate_if import Count

from poleno import datacheck
from poleno.mail.models import Message
from poleno.utils.models import QuerySet, join_lookup
from poleno.utils.mail import render_mail
from poleno.utils.date import utc_now
from poleno.utils.misc import random_readable_string, squeeze, decorate

from .inforequestemail import InforequestEmail
from .branch import Branch
from .action import Action

class InforequestQuerySet(QuerySet):
    def owned_by(self, user):
        return self.filter(applicant=user)
    def closed(self):
        return self.filter(closed=True)
    def not_closed(self):
        return self.filter(closed=False)
    def with_undecided_email(self):
        return self.filter(inforequestemail__type=InforequestEmail.TYPES.UNDECIDED).distinct()
    def without_undecided_email(self):
        return self.exclude(inforequestemail__type=InforequestEmail.TYPES.UNDECIDED)
    def select_undecided_emails_count(self):
        u"""
        Use to select ``Inforequest.undecided_emails_count``. Redundant if
        ``prefetch_related(Inforequest.prefetch_undecided_emails())`` is already used.
        """
        return self.annotate(undecided_emails_count=Count(u'inforequestemail', only=Q(inforequestemail__type=InforequestEmail.TYPES.UNDECIDED)))
    def order_by_pk(self):
        return self.order_by(u'pk')
    def order_by_submission_date(self):
        return self.order_by(u'submission_date', u'pk')

class Inforequest(models.Model):
    # May NOT be NULL
    applicant = models.ForeignKey(User,
            help_text=squeeze(u"""
                The inforequest owner, the user who submitted it.
                """))

    # May be empty; m2m through InforequestEmail
    email_set = models.ManyToManyField(u'mail.Message', through=u'InforequestEmail')

    # Should NOT be empty; Read-only; Frozen Applicant contact information at the time the
    # Inforequest was submitted, in case that the contact information changes in the future. The
    # information is automaticly frozen in save() when creating a new instance.
    applicant_name = models.CharField(max_length=255,
            help_text=squeeze(u"""
                Frozen applicant contact information for the case he changes it in the future. The
                information is frozen to its state at the moment the inforequest was
                submitted.
                """))
    applicant_street = models.CharField(max_length=255)
    applicant_city = models.CharField(max_length=255)
    applicant_zip = models.CharField(max_length=10)

    # May NOT be empty; Unique; Read-only; Automaticly computed in save() when creating a new
    # instance.
    unique_email = models.EmailField(max_length=255, unique=True, db_index=True,
            help_text=squeeze(u"""
                Unique email address used to identify which obligee email belongs to which
                inforequest. If the inforequest was advanced to other obligees, the same email
                address is used for communication with all such obligees, as there is no way to
                tell them to send their response to a different email address.
                """))

    # May NOT be NULL; Automaticly computed by Django when creating a new instance.
    submission_date = models.DateField(auto_now_add=True)

    # May NOT be NULL
    closed = models.BooleanField(default=False,
            help_text=squeeze(u"""
                True if the inforequest is closed and the applicant may not act on it any more.
                """))

    # May be NULL; Used by ``cron.undecided_email_reminder``
    last_undecided_email_reminder = models.DateTimeField(blank=True, null=True)

    # Backward relations:
    #
    #  -- branch_set: by Branch.inforequest
    #     May NOT be empty
    #
    #  -- actiondraft_set: by ActionDraft.inforequest
    #     May be empty; May contain at most one instance for every ActionDraft.TYPES
    #
    #  -- inforequestemail_set: by InforequestEmail.inforequest
    #     May be empty

    # Backward relations added to other models:
    #
    #  -- User.inforequest_set
    #     May be empty
    #
    #  -- Message.inforequest_set
    #     May be empty; Should NOT have more than one item

    objects = InforequestQuerySet.as_manager()

    class Meta:
        index_together = [
                [u'submission_date', u'id'],
                # [u'applicant'] -- ForeignKey defines index by default
                # [u'unique_email'] -- defined on field
                ]

    @staticmethod
    def prefetch_branches(path=None, queryset=None):
        u"""
        Use to prefetch ``Inforequest.branches``
        """
        if queryset is None:
            queryset = Branch.objects.get_queryset()
        queryset = queryset.order_by_pk()
        return Prefetch(join_lookup(path, u'branch_set'), queryset, to_attr=u'branches')

    @cached_property
    def branches(self):
        u"""
        Cached list of all inforequest branches ordered by ``pk``. The list should not be empty.
        May be prefetched with ``prefetch_related(Inforequest.prefetch_branches())`` queryset
        method.
        """
        return list(self.branch_set.order_by_pk())

    @staticmethod
    def prefetch_main_branch(path=None, queryset=None):
        u"""
        Use to prefetch ``Inforequest.main_branch``. Redundant if ``prefetch_branches()`` is
        already used,
        """
        if queryset is None:
            queryset = Branch.objects.get_queryset()
        queryset = queryset.main()
        return Prefetch(join_lookup(path, u'branch_set'), queryset, to_attr=u'_main_branch')

    @cached_property
    def main_branch(self):
        u"""
        Cached inforequest main branch. The inforequest should have exactly one main branch. Raises
        Branch.DoesNotExist if the inforequest has no main branch and Branch.MultipleObjectsReturned
        if it has more than one main branch. May be prefetched with ``prefetch_related(Inforequest.prefetch_main_branch())``
        queryset method. Takes advantage of ``Inforequest.branches`` if it is already fetched.
        """
        if u'_main_branch' in self.__dict__:
            res = self._main_branch
        elif u'branches' in self.__dict__:
            res = list(b for b in self.branches if b.is_main)
        else:
            res = list(self.branch_set.main())

        if len(res) == 0:
            raise Branch.DoesNotExist(u'Inforequest has no main branch.')
        if len(res) > 1:
            raise Branch.MultipleObjectsReturned(u'Inforequest has more than one main branch.')
        return res[0]

    @property
    def undecided_emails_set(self):
        u"""
        Queryset of all undecided emails assigned to the inforequest.
        """
        return self.email_set.filter(inforequestemail__type=InforequestEmail.TYPES.UNDECIDED)

    @staticmethod
    def prefetch_undecided_emails(path=None, queryset=None):
        u"""
        Use to prefetch ``Inforequest.undecided_emails``.
        """
        if queryset is None:
            queryset = InforequestEmail.objects.get_queryset()
        queryset = queryset.filter(type=InforequestEmail.TYPES.UNDECIDED)
        queryset = queryset.order_by_email()
        queryset = queryset.select_related(u'email')
        return Prefetch(join_lookup(path, u'inforequestemail_set'), queryset, to_attr=u'_undecided_emails')

    @cached_property
    def undecided_emails(self):
        u"""
        Cached list of all undecided emails assigned to the inforequest ordered by ``processed``.
        May be prefetched with ``prefetch_related(Inforequest.prefetch_undecided_emails())``
        queryset method.
        """
        if u'_undecided_emails' in self.__dict__:
            return list(r.email for r in self._undecided_emails)
        else:
            return list(self.undecided_emails_set.order_by_processed())

    @cached_property
    def undecided_emails_count(self):
        u"""
        Cached number of undecided emails assigned to the inforequest. May be prefetched with
        ``select_undecided_emails_count()`` queryset method, Takes advantage of ``Inforequest.undecided_emails``
        if it is already fetched.
        """
        if u'undecided_emails' in self.__dict__:
            return len(self.undecided_emails)
        elif u'_undecided_emails' in self.__dict__:
            return len(self._undecided_emails)
        else:
            return self.undecided_emails_set.count()

    @cached_property
    def has_undecided_emails(self):
        u"""
        Cached flag if the inforequest has any undecided emails assigned. Takes advantage of
        ``Inforequest.undecided_emails_count`` or ``Inforequest.undecided_emails`` if either is
        already fetched.
        """
        if u'undecided_emails_count' in self.__dict__:
            return bool(self.undecided_emails_count)
        elif u'undecided_emails' in self.__dict__:
            return bool(self.undecided_emails)
        elif u'_undecided_emails' in self.__dict__:
            return bool(self._undecided_emails)
        else:
            return self.undecided_emails_set.exists()

    @cached_property
    def oldest_undecided_email(self):
        u"""
        Cached oldest undecided email assigned to the inforequest. Returns None if the inforequest
        has no undecided emails assigned. Takes advantage of ``Inforequest.undecided_emails`` if it
        is already fetched.
        """
        if u'undecided_emails' in self.__dict__:
            try:
                return self.undecided_emails[0]
            except IndexError:
                return None
        elif u'_undecided_emails' in self.__dict__:
            try:
                return self._undecided_emails[0].email
            except IndexError:
                return None
        else:
            return self.undecided_emails_set.order_by_processed().first()

    @staticmethod
    def prefetch_newest_undecided_email(path=None, queryset=None):
        u"""
        Use to prefetch ``Inforequest.newest_undecided_email``. Redundant if
        ``prefetch_undecided_emails()`` is already used.
        """
        if queryset is None:
            queryset = InforequestEmail.objects.get_queryset()
        quote_name = connection.ops.quote_name
        queryset = queryset.filter(type=InforequestEmail.TYPES.UNDECIDED)
        queryset = queryset.select_related(u'email')
        queryset = queryset.extra(where=[
            u'{through}.{through_pk} = ('
                u'SELECT p.{through_pk} '
                u'FROM {through} p '
                    u'INNER JOIN {message} m ON (m.{message_pk} = p.{through_email}) '
                u'WHERE p.{through_inforequest} = {through}.{through_inforequest} '
                u'ORDER BY m.{message_processed} DESC, m.{message_pk} DESC, p.{through_pk} DESC '
                u'LIMIT 1'
            u')'.format(
                through = quote_name(InforequestEmail._meta.db_table),
                through_pk = quote_name(InforequestEmail._meta.pk.column),
                through_inforequest = quote_name(InforequestEmail._meta.get_field(u'inforequest').column),
                through_email = quote_name(InforequestEmail._meta.get_field(u'email').column),
                message = quote_name(Message._meta.db_table),
                message_pk = quote_name(Message._meta.pk.column),
                message_processed = quote_name(Message._meta.get_field(u'processed').column),
                )
            ])
        return Prefetch(join_lookup(path, u'inforequestemail_set'), queryset, to_attr=u'_newest_undecided_email')

    @cached_property
    def newest_undecided_email(self):
        u"""
        Cached newest undecided email assigned to the inforequest. Returns None if the inforequest
        has no undecided emails assigned. Takes advantage of ``Inforequest.undecided_emails`` if it
        is already fetched.
        """
        if u'_newest_undecided_email' in self.__dict__:
            try:
                return self._newest_undecided_email[0].email
            except IndexError:
                return None
        elif u'undecided_emails' in self.__dict__:
            try:
                return self.undecided_emails[-1]
            except IndexError:
                return None
        elif u'_undecided_emails' in self.__dict__:
            try:
                return self._undecided_emails[-1].email
            except IndexError:
                return None
        else:
            return self.undecided_emails_set.order_by_processed().last()

    @cached_property
    def can_add_request(self):
        return self.can_add_action(Action.TYPES.REQUEST)

    @cached_property
    def can_add_clarification_response(self):
        return self.can_add_action(Action.TYPES.CLARIFICATION_RESPONSE)

    @cached_property
    def can_add_appeal(self):
        return self.can_add_action(Action.TYPES.APPEAL)

    @cached_property
    def can_add_confirmation(self):
        return self.can_add_action(Action.TYPES.CONFIRMATION)

    @cached_property
    def can_add_extension(self):
        return self.can_add_action(Action.TYPES.EXTENSION)

    @cached_property
    def can_add_advancement(self):
        return self.can_add_action(Action.TYPES.ADVANCEMENT)

    @cached_property
    def can_add_clarification_request(self):
        return self.can_add_action(Action.TYPES.CLARIFICATION_REQUEST)

    @cached_property
    def can_add_disclosure(self):
        return self.can_add_action(Action.TYPES.DISCLOSURE)

    @cached_property
    def can_add_refusal(self):
        return self.can_add_action(Action.TYPES.REFUSAL)

    @cached_property
    def can_add_affirmation(self):
        return self.can_add_action(Action.TYPES.AFFIRMATION)

    @cached_property
    def can_add_reversion(self):
        return self.can_add_action(Action.TYPES.REVERSION)

    @cached_property
    def can_add_remandment(self):
        return self.can_add_action(Action.TYPES.REMANDMENT)

    @cached_property
    def can_add_applicant_action(self):
        return self.can_add_action(*Action.APPLICANT_ACTION_TYPES)

    @cached_property
    def can_add_applicant_email_action(self):
        return self.can_add_action(*Action.APPLICANT_EMAIL_ACTION_TYPES)

    @cached_property
    def can_add_obligee_action(self):
        return self.can_add_action(*Action.OBLIGEE_ACTION_TYPES)

    @cached_property
    def can_add_obligee_email_action(self):
        return self.can_add_action(*Action.OBLIGEE_EMAIL_ACTION_TYPES)

    def can_add_action(self, *action_types):
        for branch in self.branches:
            if branch.can_add_action(*action_types):
                return True
        return False

    def branches_advanced_by(self, action):
        u"""
        Returns list of branches advanced by ``action``. Takes advantage of cached list of all
        inforequest branches stored in ``Inforequest.branches`` property.
        """
        return (b for b in self.branches if b.advanced_by_id == action.id)

    def branch_by_pk(self, pk):
        u"""
        Returns inforequest branch by its ``pk``. Takes advantage of cached list of all inforequest
        branches stored in ``Inforequest.branches`` property.
        """
        for branch in self.branches:
            if branch.pk == pk:
                return branch
        raise ValueError

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        if self.pk is None: # Creating a new object

            # Freeze applicant contact information
            assert self.applicant_id is not None, u'%s.applicant is mandatory' % self.__class__.__name__
            assert self.applicant_name == u'', u'%s.applicant_name is read-only' % self.__class__.__name__
            assert self.applicant_street == u'', u'%s.applicant_street is read-only' % self.__class__.__name__
            assert self.applicant_city == u'', u'%s.applicant_city is read-only' % self.__class__.__name__
            assert self.applicant_zip == u'', u'%s.applicant_zip is read-only' % self.__class__.__name__
            self.applicant_name = self.applicant.get_full_name()
            self.applicant_street = self.applicant.profile.street
            self.applicant_city = self.applicant.profile.city
            self.applicant_zip = self.applicant.profile.zip

            # Generate unique random email
            assert self.unique_email == u'', u'%s.unique_email is read-only' % self.__class__.__name__
            length = 4
            while True:
                token = random_readable_string(length)
                self.unique_email = settings.INFOREQUEST_UNIQUE_EMAIL.format(token=token)
                try:
                    with transaction.atomic():
                        super(Inforequest, self).save(*args, **kwargs)
                except IntegrityError:
                    length += 1
                    if length <= 10:
                        continue
                    self.unique_email = None
                    raise # Give up
                return # object is already saved

        super(Inforequest, self).save(*args, **kwargs)

    def _send_notification(self, template, anchor, dictionary):
        site = Site.objects.get_current()
        url = u'http://{0}{1}#{2}'.format(site.domain, reverse(u'inforequests:detail', args=(self.pk,)), anchor)
        dictionary.update({
                u'inforequest': self,
                u'url': url,
                })
        msg = render_mail(template,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[self.applicant.email],
                dictionary=dictionary)
        msg.send()

    def send_received_email_notification(self, email):
        self._send_notification(u'inforequests/mails/received_email_notification', u'decide', {
                u'email': email,
                })

    def send_undecided_email_reminder(self):
        self._send_notification(u'inforequests/mails/undecided_email_reminder', u'decide', {
                })

        self.last_undecided_email_reminder = utc_now()
        self.save(update_fields=[u'last_undecided_email_reminder'])

    def send_obligee_deadline_reminder(self, action):
        self._send_notification(u'inforequests/mails/obligee_deadline_reminder', u'action-%s' % action.pk, {
                u'action': action,
                })

        action.last_deadline_reminder = utc_now()
        action.save(update_fields=[u'last_deadline_reminder'])

    def send_applicant_deadline_reminder(self, action):
        self._send_notification(u'inforequests/mails/applicant_deadline_reminder', u'action-%s' % action.pk, {
                u'action': action,
                })

        action.last_deadline_reminder = utc_now()
        action.save(update_fields=[u'last_deadline_reminder'])

    def __unicode__(self):
        return u'%s' % self.pk

    @classmethod
    def datacheck(cls, superficial=False):
        u"""
        Checks that every ``Inforequest`` instance has exactly one main branch.
        """
        inforequests = (Inforequest.objects
                .annotate(Count(u'branch', only=Q(branch__advanced_by=None)))
                .filter(~Q(branch__count=1))
                )

        if superficial:
            inforequests = inforequests[:5+1]
        issues = [u'%r has %d main branches' % (r, r.branch__count) for r in inforequests]
        if superficial and issues:
            if len(issues) > 5:
                issues[-1] = u'More inforequests have invalid number of main branches'
            issues = [u'; '.join(issues)]
        for issue in issues:
            yield datacheck.Error(issue + u'.')
