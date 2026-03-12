# vim: expandtab
# -*- coding: utf-8 -*-
from email.utils import formataddr

from django.core.mail import EmailMessage
from django.db import models
from django.db.models import Prefetch, Q, F, Count, Case, When, IntegerField
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property
from django.contrib.contenttypes import generic
from multiselectfield import MultiSelectField

from poleno import datacheck
from poleno.attachments.models import Attachment
from poleno.workdays import workdays
from poleno.utils.models import FieldChoices, QuerySet, join_lookup, after_saved
from poleno.utils.date import utc_now, local_today
from poleno.utils.misc import Bunch, squeeze, decorate, FormatMixin


class ActionQuerySet(QuerySet):
    def owned_by(self, user):
        return self.filter(branch__inforequest__applicant=user)

    # Applicant actions
    def applicant_actions(self):
        return self.filter(type__in=Action.APPLICANT_ACTION_TYPES)
    def requests(self):
        return self.filter(type=Action.TYPES.REQUEST)
    def clarification_responses(self):
        return self.filter(type=Action.TYPES.CLARIFICATION_RESPONSE)
    def appeals(self):
        return self.filter(type=Action.TYPES.APPEAL)

    # Obligee actions
    def obligee_actions(self):
        return self.filter(type__in=Action.OBLIGEE_ACTION_TYPES)
    def confirmations(self):
        return self.filter(type=Action.TYPES.CONFIRMATION)
    def extensions(self):
        return self.filter(type=Action.TYPES.EXTENSION)
    def advancements(self):
        return self.filter(type=Action.TYPES.ADVANCEMENT)
    def clarification_requests(self):
        return self.filter(type=Action.TYPES.CLARIFICATION_REQUEST)
    def disclosures(self):
        return self.filter(type=Action.TYPES.DISCLOSURE)
    def refusals(self):
        return self.filter(type=Action.TYPES.REFUSAL)
    def affirmations(self):
        return self.filter(type=Action.TYPES.AFFIRMATION)
    def reversions(self):
        return self.filter(type=Action.TYPES.REVERSION)
    def remandments(self):
        return self.filter(type=Action.TYPES.REMANDMENT)

    # Implicit actions
    def implicit_actions(self):
        return self.filter(type__in=Action.IMPLICIT_ACTION_TYPES)
    def advanced_requests(self):
        return self.filter(type=Action.TYPES.ADVANCED_REQUEST)
    def expirations(self):
        return self.filter(type=Action.TYPES.EXPIRATION)
    def appeal_expirations(self):
        return self.filter(type=Action.TYPES.APPEAL_EXPIRATION)

    # Other methods
    def by_email(self):
        return self.filter(email__isnull=False)
    def by_smail(self):
        return self.filter(email__isnull=True)
    def of_inforequest(self, inforequest):
        return self.filter(branch__inforequest=inforequest)
    def order_by_pk(self):
        return self.order_by(u'pk')
    def order_by_created(self):
        return self.order_by(u'created', u'pk')
    def before(self, other):
        return self.filter(Q(created__lt=other.created) | Q(created=other.created, pk__lt=other.pk))
    def after(self, other):
        return self.filter(Q(created__gt=other.created) | Q(created=other.created, pk__gt=other.pk))

class Action(FormatMixin, models.Model):
    # NOT NULL
    branch = models.ForeignKey(u'Branch')

    # NOT NULL for actions sent or received by email; NULL otherwise
    email = models.OneToOneField(u'mail.Message', blank=True, null=True, on_delete=models.SET_NULL)

    # NOT NULL
    TYPES = FieldChoices(
            # Applicant actions
            (u'REQUEST',                 1, _(u'inforequests:Action:type:REQUEST')),
            (u'CLARIFICATION_RESPONSE', 12, _(u'inforequests:Action:type:CLARIFICATION_RESPONSE')),
            (u'APPEAL',                 13, _(u'inforequests:Action:type:APPEAL')),
            # Obligee actions
            (u'CONFIRMATION',            2, _(u'inforequests:Action:type:CONFIRMATION')),
            (u'EXTENSION',               3, _(u'inforequests:Action:type:EXTENSION')),
            (u'ADVANCEMENT',             4, _(u'inforequests:Action:type:ADVANCEMENT')),
            (u'CLARIFICATION_REQUEST',   5, _(u'inforequests:Action:type:CLARIFICATION_REQUEST')),
            (u'DISCLOSURE',              6, _(u'inforequests:Action:type:DISCLOSURE')),
            (u'REFUSAL',                 7, _(u'inforequests:Action:type:REFUSAL')),
            (u'AFFIRMATION',             8, _(u'inforequests:Action:type:AFFIRMATION')),
            (u'REVERSION',               9, _(u'inforequests:Action:type:REVERSION')),
            (u'REMANDMENT',             10, _(u'inforequests:Action:type:REMANDMENT')),
            # Implicit actions
            (u'ADVANCED_REQUEST',       11, _(u'inforequests:Action:type:ADVANCED_REQUEST')),
            (u'EXPIRATION',             14, _(u'inforequests:Action:type:EXPIRATION')),
            (u'APPEAL_EXPIRATION',      15, _(u'inforequests:Action:type:APPEAL_EXPIRATION')),
            )
    APPLICANT_ACTION_TYPES = (
            TYPES.REQUEST,
            TYPES.CLARIFICATION_RESPONSE,
            TYPES.APPEAL,
            )
    APPLICANT_EMAIL_ACTION_TYPES = (
            TYPES.REQUEST,
            TYPES.CLARIFICATION_RESPONSE,
            )
    OBLIGEE_ACTION_TYPES = (
            TYPES.CONFIRMATION,
            TYPES.EXTENSION,
            TYPES.ADVANCEMENT,
            TYPES.CLARIFICATION_REQUEST,
            TYPES.DISCLOSURE,
            TYPES.REFUSAL,
            TYPES.AFFIRMATION,
            TYPES.REVERSION,
            TYPES.REMANDMENT,
            )
    OBLIGEE_EMAIL_ACTION_TYPES = (
            TYPES.CONFIRMATION,
            TYPES.EXTENSION,
            TYPES.ADVANCEMENT,
            TYPES.CLARIFICATION_REQUEST,
            TYPES.DISCLOSURE,
            TYPES.REFUSAL,
            )
    IMPLICIT_ACTION_TYPES = (
            TYPES.ADVANCED_REQUEST,
            TYPES.EXPIRATION,
            TYPES.APPEAL_EXPIRATION,
            )
    type = models.SmallIntegerField(choices=TYPES._choices)

    # May be empty for implicit actions; Should NOT be empty for other actions
    subject = models.CharField(blank=True, max_length=255)
    content = models.TextField(blank=True)

    # NOT NULL
    CONTENT_TYPES = FieldChoices(
            (u'PLAIN_TEXT', 1, u'Plain Text'),
            (u'HTML',       2, u'HTML'),
            )
    content_type = models.SmallIntegerField(choices=CONTENT_TYPES._choices,
            default=CONTENT_TYPES.PLAIN_TEXT,
            help_text=squeeze(u"""
                Mandatory choice for action content type. Supported formats are plain text and html
                code. The html code is assumed to be safe. It is passed to the client without
                sanitizing. It must be sanitized before saving it here.
                """))

    # May be empty
    attachment_set = generic.GenericRelation(u'attachments.Attachment',
            content_type_field=u'generic_type', object_id_field=u'generic_id',
            related_query_name=u'action')

    # May be empty
    file_number = models.CharField(blank=True, max_length=255,
            help_text=squeeze(u"""
                A file number assigned to the action by the obligee. Usually only obligee actions
                have it. However, if we know tha obligee assigned a file number to an applicant
                action, we should keep it here as well. The file number is optional.
                """))

    # NOT NULL
    created = models.DateTimeField(default=utc_now,
            help_text=squeeze(u"""
                Point in time used to order branch actions chronologically. By default it's the
                datetime the action was created. The admin may set the value manually to change
                actions order in the branch.
                """))

    # NOT NULL for applicant actions; May be NULL for obligee actions; NULL otherwise
    sent_date = models.DateField(blank=True, null=True,
            help_text=squeeze(u"""
                The date the action was sent by the applicant or the obligee. It is mandatory for
                applicant actions, optional for obligee actions and should be NULL for implicit
                actions.
                """))

    # May be NULL for applicant actions; NOT NULL for obligee actions; NULL otherwise
    delivered_date = models.DateField(blank=True, null=True,
            help_text=squeeze(u"""
                The date the action was delivered to the applicant or the obligee. It is optional
                for applicant actions, mandatory for obligee actions and should be NULL for
                implicit actions.
                """))

    # NOT NULL
    legal_date = models.DateField(
            help_text=squeeze(u"""
                The date the action legally occured. Mandatory for every action.
                """))

    # NOT NULL for EXTENSION; NULL otherwise
    extension = models.IntegerField(blank=True, null=True,
            help_text=squeeze(u"""
                Obligee extension to the original deadline. Applicable only to extension actions.
                Ignored for all other actions.
                """))

    # May be NULL for actions with obligee deadline; NULL otherwise
    snooze = models.DateField(blank=True, null=True,
            help_text=squeeze(u"""
                The applicant may snooze for few days after the obligee misses its deadline and
                wait a little longer. He may snooze multiple times. Ignored for applicant
                deadlines.
                """))

    # NOT NULL for obligee actions that may disclose the information; NULL otherwise
    DISCLOSURE_LEVELS = FieldChoices(
            (u'NONE',    1, _(u'inforequests:Action:disclosure_level:NONE')),
            (u'PARTIAL', 2, _(u'inforequests:Action:disclosure_level:PARTIAL')),
            (u'FULL',    3, _(u'inforequests:Action:disclosure_level:FULL')),
            )
    disclosure_level = models.SmallIntegerField(choices=DISCLOSURE_LEVELS._choices,
            blank=True, null=True,
            help_text=squeeze(u"""
                Mandatory choice for obligee actions that may disclose the information, NULL
                otherwise. Specifies if the obligee disclosed any requested information by this
                action.
                """))

    # May be empty for obligee actions that may provide a reason; Empty otherwise
    REFUSAL_REASONS = FieldChoices(
            (u'DOES_NOT_HAVE',    u'3', _(u'inforequests:Action:refusal_reason:DOES_NOT_HAVE')),
            (u'DOES_NOT_PROVIDE', u'4', _(u'inforequests:Action:refusal_reason:DOES_NOT_PROVIDE')),
            (u'DOES_NOT_CREATE',  u'5', _(u'inforequests:Action:refusal_reason:DOES_NOT_CREATE')),
            (u'COPYRIGHT',        u'6', _(u'inforequests:Action:refusal_reason:COPYRIGHT')),
            (u'BUSINESS_SECRET',  u'7', _(u'inforequests:Action:refusal_reason:BUSINESS_SECRET')),
            (u'PERSONAL',         u'8', _(u'inforequests:Action:refusal_reason:PERSONAL')),
            (u'CONFIDENTIAL',     u'9', _(u'inforequests:Action:refusal_reason:CONFIDENTIAL')),
            (u'OTHER_REASON',    u'-2', _(u'inforequests:Action:refusal_reason:OTHER_REASON')),
            )
    APPEAL_REFUSAL_REASONS = FieldChoices(
            (u'DOES_NOT_HAVE',    u'3', _(u'inforequests:Action:appeal_refusal_reason:DOES_NOT_HAVE')),
            (u'DOES_NOT_PROVIDE', u'4', _(u'inforequests:Action:appeal_refusal_reason:DOES_NOT_PROVIDE')),
            (u'DOES_NOT_CREATE',  u'5', _(u'inforequests:Action:appeal_refusal_reason:DOES_NOT_CREATE')),
            (u'COPYRIGHT',        u'6', _(u'inforequests:Action:appeal_refusal_reason:COPYRIGHT')),
            (u'BUSINESS_SECRET',  u'7', _(u'inforequests:Action:appeal_refusal_reason:BUSINESS_SECRET')),
            (u'PERSONAL',         u'8', _(u'inforequests:Action:appeal_refusal_reason:PERSONAL')),
            (u'CONFIDENTIAL',     u'9', _(u'inforequests:Action:appeal_refusal_reason:CONFIDENTIAL')),
            (u'OTHER_REASON',    u'-2', _(u'inforequests:Action:appeal_refusal_reason:OTHER_REASON')),
            )
    refusal_reason = MultiSelectField(choices=REFUSAL_REASONS._choices, blank=True,
            help_text=squeeze(u"""
                Optional multichoice for obligee actions that may provide a reason for not
                disclosing the information, Should be empty for all other actions. Specifies the
                reason why the obligee refused to disclose the information. An empty value means
                that the obligee did not provide any reason.
                """))

    # May be NULL; Used by ``cron.obligee_deadline_reminder`` and ``cron.applicant_deadline_reminder``
    last_deadline_reminder = models.DateTimeField(blank=True, null=True)

    # Backward relations:
    #
    #  -- advanced_to_set: by Branch.advanced_by
    #     May NOT be empty for ADVANCEMENT; Must be empty otherwise

    # Backward relations added to other models:
    #
    #  -- Branch.action_set
    #     May NOT be empty; The first action of every main branch must be REQUEST and the first
    #     action of every advanced branch ADVANCED_REQUEST.
    #
    #  -- Message.action
    #     May raise DoesNotExist

    # Indexes:
    #  -- branch:      ForeignKey
    #  -- email:       OneToOneField
    #  -- created, id: index_together

    objects = ActionQuerySet.as_manager()

    class Meta:
        index_together = [
                [u'created', u'id'],
                ]

    @staticmethod
    def prefetch_attachments(path=None, queryset=None):
        u"""
        Use to prefetch ``Action.attachments``.
        """
        if queryset is None:
            queryset = Attachment.objects.get_queryset()
        queryset = queryset.order_by_pk()
        return Prefetch(join_lookup(path, u'attachment_set'), queryset, to_attr=u'attachments')

    @cached_property
    def attachments(self):
        u"""
        Cached list of all action attachments ordered by ``pk``. May be prefetched with
        ``prefetch_related(Action.prefetch_attachments())`` queryset method.
        """
        return list(self.attachment_set.order_by_pk())

    @cached_property
    def previous_action(self):
        return self.branch.action_set.order_by_created().before(self).last()

    @cached_property
    def next_action(self):
        return self.branch.action_set.order_by_created().after(self).first()

    @cached_property
    def is_last_action(self):
        return self.next_action is None

    @cached_property
    def action_path(self):
        res = [] if self.branch.is_main else self.branch.advanced_by.action_path
        res += self.branch.actions[:self.branch.actions.index(self)+1]
        return res

    @cached_property
    def is_applicant_action(self):
        return self.type in self.APPLICANT_ACTION_TYPES

    @cached_property
    def is_obligee_action(self):
        return self.type in self.OBLIGEE_ACTION_TYPES

    @cached_property
    def is_implicit_action(self):
        return self.type in self.IMPLICIT_ACTION_TYPES

    @cached_property
    def is_by_email(self):
        return self.email_id is not None

    @cached_property
    def has_obligee_deadline(self):
        return self.deadline is not None and self.deadline.is_obligee_deadline

    @cached_property
    def has_obligee_deadline_missed(self):
        return self.has_obligee_deadline and self.deadline.is_deadline_missed

    @cached_property
    def has_obligee_deadline_snooze_missed(self):
        return self.has_obligee_deadline and self.deadline.is_snooze_missed

    @cached_property
    def has_applicant_deadline(self):
        return self.deadline is not None and self.deadline.is_applicant_deadline

    @cached_property
    def has_applicant_deadline_missed(self):
        return self.has_applicant_deadline and self.deadline.is_deadline_missed

    @cached_property
    def can_applicant_snooze(self):
        u"""
        Whether the applicant may snooze for 3 calendar days since today such that the total snooze
        since the deadline date will not be more than 8 calendar days.
        """
        return (self.has_obligee_deadline_snooze_missed
                and 8 - self.deadline.calendar_days_behind >= 3)

    @cached_property
    def deadline(self):

        # Applicant actions
        if self.type == self.TYPES.REQUEST:
            return Deadline(Deadline.TYPES.OBLIGEE_DEADLINE,
                    self.delivered_date or workdays.advance(self.sent_date, 1),
                    12, Deadline.UNITS.WORKDAYS, self.snooze)

        elif self.type == self.TYPES.CLARIFICATION_RESPONSE:
            return Deadline(Deadline.TYPES.OBLIGEE_DEADLINE,
                    self.delivered_date or workdays.advance(self.sent_date, 1),
                    12, Deadline.UNITS.WORKDAYS, self.snooze)

        elif self.type == self.TYPES.APPEAL:
            return Deadline(Deadline.TYPES.OBLIGEE_DEADLINE,
                    self.delivered_date or workdays.advance(self.sent_date, 6),
                    15, Deadline.UNITS.CALENDAR_DAYS, self.snooze)

        # Obligee actions
        elif self.type == self.TYPES.CONFIRMATION:
            previous = self.previous_action.deadline
            return Deadline(Deadline.TYPES.OBLIGEE_DEADLINE,
                    previous.base_date, previous.value, previous.unit,
                    self.snooze or previous.snooze_date)

        elif self.type == self.TYPES.EXTENSION:
            previous = self.previous_action.deadline
            extension = self.extension or 0
            return Deadline(Deadline.TYPES.OBLIGEE_DEADLINE,
                    previous.base_date, previous.value + extension, previous.unit,
                    self.snooze or previous.snooze_date)

        elif self.type == self.TYPES.ADVANCEMENT:
            # The user may send an appeal after advancement. But it is not very common, so we don't
            # show any deadline nor send deadline reminder.
            return None

        elif self.type == self.TYPES.CLARIFICATION_REQUEST:
            return Deadline(Deadline.TYPES.APPLICANT_DEADLINE,
                    self.delivered_date, 7, Deadline.UNITS.CALENDAR_DAYS, 0)

        elif self.type == self.TYPES.DISCLOSURE:
            if self.disclosure_level == self.DISCLOSURE_LEVELS.FULL:
                return None
            return Deadline(Deadline.TYPES.APPLICANT_DEADLINE,
                    self.delivered_date, 15, Deadline.UNITS.CALENDAR_DAYS, 0)

        elif self.type == self.TYPES.REFUSAL:
            return Deadline(Deadline.TYPES.APPLICANT_DEADLINE,
                    self.delivered_date, 15, Deadline.UNITS.CALENDAR_DAYS, 0)

        elif self.type == self.TYPES.AFFIRMATION:
            return None

        elif self.type == self.TYPES.REVERSION:
            return None

        elif self.type == self.TYPES.REMANDMENT:
            return Deadline(Deadline.TYPES.OBLIGEE_DEADLINE,
                    workdays.advance(self.legal_date, 4),
                    8, Deadline.UNITS.WORKDAYS, self.snooze)

        # Implicit actions
        elif self.type == self.TYPES.ADVANCED_REQUEST:
            return Deadline(Deadline.TYPES.OBLIGEE_DEADLINE,
                    workdays.advance(self.legal_date, 4),
                    8, Deadline.UNITS.WORKDAYS, self.snooze)

        elif self.type == self.TYPES.EXPIRATION:
            return Deadline(Deadline.TYPES.APPLICANT_DEADLINE,
                    self.legal_date, 15, Deadline.UNITS.CALENDAR_DAYS, 0)

        elif self.type == self.TYPES.APPEAL_EXPIRATION:
            return None

        raise ValueError(u'Invalid action type: {}'.format(self.type))

    @classmethod
    def create(cls, *args, **kwargs):
        advanced_to = kwargs.pop(u'advanced_to', None) or []
        attachments = kwargs.pop(u'attachments', None) or []
        action = Action(*args, **kwargs)

        @after_saved(action)
        def deferred(action):
            for obligee in advanced_to:
                if not obligee:
                    continue
                sub_branch = Branch.create(
                        obligee=obligee,
                        inforequest=action.branch.inforequest,
                        advanced_by=action,
                        action_kwargs=dict(
                            type=Action.TYPES.ADVANCED_REQUEST,
                            legal_date=action.legal_date,
                            ),
                        )
                sub_branch.save()

            for attch in attachments:
                attachment = attch.clone(action)
                attachment.save()

        return action

    def get_extended_type_display(self):
        u"""
        Return a bit more verbose action type description. It is not based only on the action type.
        For instance ``DISCLOSURE`` actions have different descriptions based on their disclosure
        levels.
        """
        if self.type == self.TYPES.DISCLOSURE:
            if self.disclosure_level == self.DISCLOSURE_LEVELS.NONE:
                return _(u'inforequests:Action:type:DISCLOSURE:NONE')
            if self.disclosure_level == self.DISCLOSURE_LEVELS.PARTIAL:
                return _(u'inforequests:Action:type:DISCLOSURE:PARTIAL')
            if self.disclosure_level == self.DISCLOSURE_LEVELS.FULL:
                return _(u'inforequests:Action:type:DISCLOSURE:FULL')
        return self.get_type_display()

    def get_absolute_url(self):
        return self.branch.inforequest.get_absolute_url(u'#a{}'.format(self.pk))

    def send_by_email(self):
        if not self.is_applicant_action:
            raise TypeError(u'{} is not applicant action'.format(self.get_type_display()).encode(u'utf-8'))
        if not self.branch.collect_obligee_emails:
            # Django silently ignores messages with no recipients
            raise ValueError(u'Action has no recipients')

        sender_name = self.branch.inforequest.applicant_name
        sender_address = self.branch.inforequest.unique_email
        sender_formatted = formataddr((squeeze(sender_name), sender_address))
        recipients = [formataddr(r) for r in self.branch.collect_obligee_emails]

        msg = EmailMessage(self.subject, self.content, sender_formatted, recipients)
        for attachment in self.attachments:
            msg.attach(attachment.name, attachment.content, attachment.content_type)
        msg.send()

        inforequestemail = InforequestEmail(
                inforequest=self.branch.inforequest,
                email=msg.instance,
                type=InforequestEmail.TYPES.APPLICANT_ACTION,
                )
        inforequestemail.save()

        self.email = msg.instance
        self.save(update_fields=[u'email'])

    def __unicode__(self):
        return u'[{}] {}'.format(self.pk, self.get_type_display())

@datacheck.register
def datachecks(superficial, autofix):
    u"""
    Checks that every ``Action.email`` is assigned to ``Action.branch.inforequest``.
    """
    actions = (Action.objects
            .filter(email__isnull=False)
            .annotate(email_match_count=Count(Case(
                When(branch__inforequest__email_set=F(u'email'), then=1),
                output_field=IntegerField())))
            .filter(email_match_count=0)
            )

    if superficial:
        actions = actions[:5+1]
    issues = [u'{} email is assigned to another inforequest'.format(a) for a in actions]
    if superficial and issues:
        if len(issues) > 5:
            issues[-1] = u'More action emails are assigned to other inforequests'
        issues = [u'; '.join(issues)]
    for issue in issues:
        yield datacheck.Error(issue + u'.')

# Must be after ``Action`` to break cyclic dependency
from .deadline import Deadline
from .branch import Branch
from .inforequestemail import InforequestEmail
