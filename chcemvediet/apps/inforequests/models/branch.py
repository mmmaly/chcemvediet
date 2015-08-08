# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models, connection
from django.db.models import Q, F, Prefetch
from django.utils.functional import cached_property

from poleno import datacheck
from poleno.utils.models import QuerySet, join_lookup
from poleno.utils.date import local_today
from poleno.utils.misc import squeeze, decorate

from .action import Action

class BranchQuerySet(QuerySet):
    def main(self):
        return self.filter(advanced_by__isnull=True)
    def advanced(self):
        return self.filter(advanced_by__isnull=False)
    def order_by_pk(self):
        return self.order_by(u'pk')

class Branch(models.Model):
    # May NOT be NULL; Index is prefix of [inforequest, advanced_by] index, see index_together
    inforequest = models.ForeignKey(u'Inforequest', db_index=False)

    # May NOT be NULL
    obligee = models.ForeignKey(u'obligees.Obligee',
            help_text=u'The obligee the inforequest was sent or advanced to.')

    # May NOT be NULL; Automaticly frozen in save() when creating a new object
    historicalobligee = models.ForeignKey(u'obligees.HistoricalObligee',
            help_text=u'Frozen Obligee at the time the Inforequest was submitted or advanced to it.')

    # Advancement action that advanced the inforequest to this obligee; None if it's inforequest
    # main branch. Inforequest must contain exactly one branch with ``advanced_by`` set to None;
    # Index is prefix of [advanced_by, inforequest] index, see index_together
    advanced_by = models.ForeignKey(u'Action', related_name=u'advanced_to_set', blank=True, null=True, db_index=False,
            help_text=squeeze(u"""
                NULL for main branches. The advancement action the inforequest was advanced by for
                advanced branches. Every Inforequest must contain exactly one main branch.
                """))

    # Backward relations:
    #
    #  -- action_set: by Action.branch
    #     May NOT be empty; The first action of every main branch must be REQUEST and the first
    #     action of every advanced branch ADVANCED_REQUEST.
    #
    #  -- actiondraft_set: by ActionDraft.branch
    #     May be empty

    # Backward relations added to other models:
    #
    #  -- Inforequest.branch_set
    #     Should NOT be empty
    #
    #  -- Obligee.branch_set
    #     May be empty
    #
    #  -- HistoricalObligee.branch_set
    #     May be empty
    #
    #  -- Action.advanced_to_set
    #     May be empty

    objects = BranchQuerySet.as_manager()

    class Meta:
        verbose_name_plural = u'Branches'
        index_together = [
                [u'inforequest', u'advanced_by'],
                [u'advanced_by', u'inforequest'],
                # [u'obligee'] -- ForeignKey defines index by default
                # [u'historicalobligee'] -- ForeignKey defines index by default
                ]

    @cached_property
    def is_main(self):
        return self.advanced_by_id is None

    @staticmethod
    def prefetch_actions(path=None, queryset=None):
        u"""
        Use to prefetch ``Branch.actions``.
        """
        if queryset is None:
            queryset = Action.objects.get_queryset()
        queryset = queryset.order_by_effective_date()
        return Prefetch(join_lookup(path, u'action_set'), queryset, to_attr=u'actions')

    @cached_property
    def actions(self):
        u"""
        Cached list of all branch actions ordered by ``effective_date``. The list should not be
        empty. May be prefetched with ``prefetch_related(Branch.prefetch_actions())`` queryset
        method.
        """
        return list(self.action_set.order_by_effective_date())

    @staticmethod
    def prefetch_actions_by_email(path=None, queryset=None):
        u"""
        Use to prefetch ``Branch.actions_by_email``.
        """
        if queryset is None:
            queryset = Action.objects.get_queryset()
        queryset = queryset.by_email()
        queryset = queryset.order_by_effective_date()
        return Prefetch(join_lookup(path, u'action_set'), queryset, to_attr=u'actions_by_email')

    @cached_property
    def actions_by_email(self):
        u"""
        Cached list of all branch actions sent by email ordered by ``effective_date``. May be
        prefetched with ``prefetch_related(Branch.prefetch_actions_by_email())`` queryset method.
        Takes advantage of ``Branch.actions`` if it is fetched already.
        """
        if u'actions' in self.__dict__:
            return list(a for a in self.actions if a.is_by_email)
        else:
            return list(self.action_set.by_email().order_by_effective_date())

    @staticmethod
    def prefetch_last_action(path=None, queryset=None):
        u"""
        Use to prefetch ``Branch.last_action``. Redundant if ``prefetch_actions()`` is already
        used.
        """
        if queryset is None:
            queryset = Action.objects.get_queryset()
        quote_name = connection.ops.quote_name
        queryset = queryset.extra(where=[
            u'{action}.{pk} = ('
                u'SELECT p.{pk} '
                u'FROM {action} p '
                u'WHERE p.{branch} = {action}.{branch} '
                u'ORDER BY p.{effective_date} DESC, p.{pk} DESC '
                u'LIMIT 1'
            u')'.format(
                action = quote_name(Action._meta.db_table),
                pk = quote_name(Action._meta.pk.column),
                branch = quote_name(Action._meta.get_field(u'branch').column),
                effective_date = quote_name(Action._meta.get_field(u'effective_date').column),
                )
            ])
        return Prefetch(join_lookup(path, u'action_set'), queryset, to_attr=u'_last_action')

    @cached_property
    def last_action(self):
        u"""
        Cached last branch action. Returns None if the branch has no actions. May be prefetched
        with ``prefetch_related(Branch.prefetch_last_action())`` queryset method. Takes advantage
        of ``Branch.actions`` if it is fetched already.
        """
        if u'_last_action' in self.__dict__:
            try:
                return self._last_action[0]
            except IndexError:
                return None
        elif u'actions' in self.__dict__:
            try:
                return self.actions[-1]
            except IndexError:
                return None
        else:
            return self.action_set.order_by_effective_date().last()

    @cached_property
    def can_add_request(self):
        return False

    @cached_property
    def can_add_clarification_response(self):
        return self.last_action.type == Action.TYPES.CLARIFICATION_REQUEST

    @cached_property
    def can_add_appeal(self):
        if self.last_action.type == Action.TYPES.DISCLOSURE:
            return self.last_action.disclosure_level != Action.DISCLOSURE_LEVELS.FULL
        if self.last_action.type in [
                Action.TYPES.REQUEST,
                Action.TYPES.CLARIFICATION_RESPONSE,
                Action.TYPES.CONFIRMATION,
                Action.TYPES.EXTENSION,
                Action.TYPES.REMANDMENT,
                Action.TYPES.ADVANCED_REQUEST,
                ]:
            return self.last_action.deadline_missed
        return self.last_action.type in [
                Action.TYPES.REFUSAL,
                Action.TYPES.ADVANCEMENT,
                Action.TYPES.EXPIRATION,
                ]

    @cached_property
    def can_add_confirmation(self):
        return self.last_action.type in [
                Action.TYPES.REQUEST,
                Action.TYPES.ADVANCED_REQUEST,
                ]

    @cached_property
    def can_add_extension(self):
        return self.last_action.type in [
                Action.TYPES.REQUEST,
                Action.TYPES.CONFIRMATION,
                Action.TYPES.CLARIFICATION_RESPONSE,
                Action.TYPES.REMANDMENT,
                Action.TYPES.ADVANCED_REQUEST,
                ]

    @cached_property
    def can_add_advancement(self):
        return self.last_action.type in [
                Action.TYPES.REQUEST,
                Action.TYPES.CLARIFICATION_RESPONSE,
                Action.TYPES.CONFIRMATION,
                Action.TYPES.ADVANCED_REQUEST,
                ]

    @cached_property
    def can_add_clarification_request(self):
        return self.last_action.type in [
                Action.TYPES.REQUEST,
                Action.TYPES.CLARIFICATION_RESPONSE,
                Action.TYPES.CONFIRMATION,
                Action.TYPES.CLARIFICATION_REQUEST,
                Action.TYPES.ADVANCED_REQUEST,
                ]

    @cached_property
    def can_add_disclosure(self):
        return self.last_action.type in [
                Action.TYPES.REQUEST,
                Action.TYPES.CLARIFICATION_RESPONSE,
                Action.TYPES.CONFIRMATION,
                Action.TYPES.EXTENSION,
                Action.TYPES.REMANDMENT,
                Action.TYPES.ADVANCED_REQUEST,
                ]

    @cached_property
    def can_add_refusal(self):
        return self.last_action.type in [
                Action.TYPES.REQUEST,
                Action.TYPES.CLARIFICATION_RESPONSE,
                Action.TYPES.CONFIRMATION,
                Action.TYPES.EXTENSION,
                Action.TYPES.REMANDMENT,
                Action.TYPES.ADVANCED_REQUEST,
                ]

    @cached_property
    def can_add_affirmation(self):
        return self.last_action.type == Action.TYPES.APPEAL

    @cached_property
    def can_add_reversion(self):
        return self.last_action.type == Action.TYPES.APPEAL

    @cached_property
    def can_add_remandment(self):
        return self.last_action.type == Action.TYPES.APPEAL

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
        for action_type in action_types:
            type_name = Action.TYPES._inverse[action_type]
            if getattr(self, u'can_add_%s' % type_name.lower()):
                return True
        return False

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        if self.pk is None: # Creating a new object
            assert self.obligee_id is not None, u'%s.obligee is mandatory' % self.__class__.__name__
            assert self.historicalobligee_id is None, u'%s.historicalobligee is read-only' % self.__class__.__name__
            self.historicalobligee = self.obligee.history.first()

        super(Branch, self).save(*args, **kwargs)

    def add_expiration_if_expired(self):
        if self.last_action.has_obligee_deadline and self.last_action.deadline_missed:
            expiration = Action(
                    branch=self,
                    type=(Action.TYPES.APPEAL_EXPIRATION if self.last_action.type == Action.TYPES.APPEAL else Action.TYPES.EXPIRATION),
                    effective_date=self.last_action.deadline_date,
                    )
            expiration.save()

    def collect_obligee_emails(self):
        res = {}
        for action in self.actions_by_email:
            if action.email.type == action.email.TYPES.INBOUND:
                res.update({action.email.from_mail: action.email.from_name})
            else: # OUTBOUND
                res.update({r.mail: r.name for r in action.email.recipients})
        # Current obligee emails
        res.update({mail: name for name, mail in self.obligee.emails_parsed})

        return ((name, mail) for mail, name in res.items())

    def __unicode__(self):
        return u'%s' % self.pk

@datacheck.register
def datachecks(superficial, autofix):
    u"""
    Checks that every advanced ``Branch`` instance is advanced by an action from the same
    inforequest.
    """
    branches = (Branch.objects
            .filter(advanced_by__isnull=False)
            .filter(~Q(advanced_by__branch__inforequest=F(u'inforequest')))
            .select_related('advanced_by__branch')
            )

    if superficial:
        branches = branches[:5+1]
    issues = [u'%r has inforequest_id = %s but advanced_by.branch.inforequest_id = %s' %
                (b, b.inforequest_id, b.advanced_by.branch.inforequest_id) for b in branches]
    if superficial and issues:
        if len(issues) > 5:
            issues[-1] = u'More branches have invalid advanced by references'
        issues = [u'; '.join(issues)]
    for issue in issues:
        yield datacheck.Error(issue + u'.')
