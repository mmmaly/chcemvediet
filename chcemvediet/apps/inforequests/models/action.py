# vim: expandtab
# -*- coding: utf-8 -*-
from email.utils import formataddr

from django.core.mail import EmailMessage
from django.db import models
from django.db.models import Prefetch, Q, F
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property
from django.contrib.contenttypes import generic
from aggregate_if import Count
from multiselectfield import MultiSelectField

from poleno import datacheck
from poleno.attachments.models import Attachment
from poleno.workdays import workdays
from poleno.utils.models import FieldChoices, QuerySet, join_lookup
from poleno.utils.date import local_today
from poleno.utils.misc import Bunch, squeeze, decorate

from .inforequestemail import InforequestEmail

class ActionQuerySet(QuerySet):
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
    def order_by_pk(self):
        return self.order_by(u'pk')
    def order_by_effective_date(self):
        return self.order_by(u'effective_date', u'pk')

class Action(models.Model):
    # May NOT be NULL
    branch = models.ForeignKey(u'Branch')

    # NOT NULL for actions sent or received by email; NULL otherwise
    email = models.OneToOneField(u'mail.Message', blank=True, null=True, on_delete=models.SET_NULL)

    # May NOT be NULL
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
    content_type = models.SmallIntegerField(choices=CONTENT_TYPES._choices, default=CONTENT_TYPES.PLAIN_TEXT,
            help_text=squeeze(u"""
                Mandatory choice action content type. Supported formats are plain text and html
                code. The html code is assumed to be safe. It is passed to the client without
                sanitizing. It must be sanitized before saving it here.
                """))

    # May be empty
    attachment_set = generic.GenericRelation(u'attachments.Attachment', content_type_field=u'generic_type', object_id_field=u'generic_id')

    # May NOT be NULL
    effective_date = models.DateField(
            help_text=squeeze(u"""
                The date at which the action was sent or received. If the action was sent/received
                by e‑mail it's set automatically. If it was sent/received by s‑mail it's filled by
                the applicant.
                """))

    # May be empty for obligee actions; Should be empty for other actions
    file_number = models.CharField(blank=True, max_length=255,
            help_text=squeeze(u"""
                A file number assigned to the action by the obligee. Usually only obligee actions
                have it. However, if we know tha obligee assigned a file number to an applicant
                action, we should keep it here as well. The file number is not mandatory.
                """))

    # May NOT be NULL for actions that set deadline; Must be NULL otherwise. Default value is
    # determined and automaticly set in save() when creating a new object. All actions that set
    # deadlines except CLARIFICATION_REQUEST, DISCLOSURE and REFUSAL set the deadline for the
    # obligee. CLARIFICATION_REQUEST, DISCLOSURE and REFUSAL set the deadline for the applicant.
    # DISCLOSURE sets the deadline only if not FULL.
    DEFAULT_DEADLINES = Bunch(
            # Applicant actions
            REQUEST=8,
            CLARIFICATION_RESPONSE=8,
            APPEAL=30,
            # Obligee actions
            CONFIRMATION=8,
            EXTENSION=10,
            ADVANCEMENT=60,
            CLARIFICATION_REQUEST=7, # Deadline for the applicant
            DISCLOSURE=(lambda a: 15 # Deadline for the applicant if not full disclosure
                    if a.disclosure_level != a.DISCLOSURE_LEVELS.FULL
                    else None),
            REFUSAL=15,              # Deadline for the applicant
            AFFIRMATION=None,
            REVERSION=None,
            REMANDMENT=13,
            # Implicit actions
            ADVANCED_REQUEST=13,
            EXPIRATION=60,
            APPEAL_EXPIRATION=None,
            )
    SETTING_APPLICANT_DEADLINE_TYPES = (
            # Applicant actions
            # Obligee actions
            TYPES.ADVANCEMENT,
            TYPES.CLARIFICATION_REQUEST,
            TYPES.DISCLOSURE,
            TYPES.REFUSAL,
            # Implicit actions
            TYPES.EXPIRATION,
            )
    SETTING_OBLIGEE_DEADLINE_TYPES = (
            # Applicant actions
            TYPES.REQUEST,
            TYPES.CLARIFICATION_RESPONSE,
            TYPES.APPEAL,
            # Obligee actions
            TYPES.CONFIRMATION,
            TYPES.EXTENSION,
            TYPES.REMANDMENT,
            # Implicit actions
            TYPES.ADVANCED_REQUEST,
            )
    deadline = models.IntegerField(blank=True, null=True,
            help_text=squeeze(u"""
                The deadline that apply after the action, if the action sets a deadline, NULL
                otherwise. The deadline is expressed in a number of working days (WD) counting
                since the effective date. It may apply to the applicant or to the obligee,
                depending on the action type.
                """))

    # May be NULL
    extension = models.IntegerField(blank=True, null=True,
            help_text=squeeze(u"""
                Applicant extension to the deadline, if the action sets an obligee deadline. The
                applicant may extend the deadline after it is missed in order to be patient and
                wait a little longer. He may extend it multiple times. Applicant deadlines may not
                be extended.
                """))

    # NOT NULL for ADVANCEMENT, DISCLOSURE, REVERSION and REMANDMENT; NULL otherwise
    DISCLOSURE_LEVELS = FieldChoices(
            (u'NONE',    1, _(u'inforequests:Action:disclosure_level:NONE')),
            (u'PARTIAL', 2, _(u'inforequests:Action:disclosure_level:PARTIAL')),
            (u'FULL',    3, _(u'inforequests:Action:disclosure_level:FULL')),
            )
    disclosure_level = models.SmallIntegerField(choices=DISCLOSURE_LEVELS._choices, blank=True, null=True,
            help_text=squeeze(u"""
                Mandatory choice for advancement, disclosure, reversion and remandment actions,
                NULL otherwise. Specifies if the obligee disclosed any requested information by
                this action.
                """))

    # NOT NULL for REFUSAL and AFFIRMATION; NULL otherwise
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
    refusal_reason = MultiSelectField(choices=REFUSAL_REASONS._choices, blank=True,
            help_text=squeeze(u"""
                Optional multichoice for refusal and affirmation actions, NULL otherwise. Specifies
                the reason why the obligee refused to disclose the information. Empty value
                means that the obligee refused to disclose it with no reason.
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
    #     Should NOT be empty
    #
    #  -- Message.action
    #     May be undefined

    objects = ActionQuerySet.as_manager()

    class Meta:
        index_together = [
                [u'effective_date', u'id'],
                # [u'branch'] -- ForeignKey defines index by default
                # [u'email'] -- OneToOneField defines index by default
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
    def days_passed(self):
        return self.days_passed_at(local_today())

    @cached_property
    def deadline_remaining(self):
        return self.deadline_remaining_at(local_today())

    @cached_property
    def deadline_missed(self):
        return self.deadline_missed_at(local_today())

    @cached_property
    def deadline_date(self):
        if self.deadline is None:
            return None
        return workdays.advance(self.effective_date, self.deadline)

    @cached_property
    def has_deadline(self):
        return self.deadline is not None

    @cached_property
    def has_applicant_deadline(self):
        return self.deadline is not None and self.type in self.SETTING_APPLICANT_DEADLINE_TYPES

    @cached_property
    def has_obligee_deadline(self):
        return self.deadline is not None and self.type in self.SETTING_OBLIGEE_DEADLINE_TYPES

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        if self.pk is None: # Creating a new object

            assert self.type is not None, u'%s.type is mandatory' % self.__class__.__name__
            if self.deadline is None:
                type_name = self.TYPES._inverse[self.type]
                deadline = getattr(self.DEFAULT_DEADLINES, type_name)
                self.deadline = deadline(self) if callable(deadline) else deadline

        super(Action, self).save(*args, **kwargs)

    def days_passed_at(self, at):
        return workdays.between(self.effective_date, at)

    def deadline_remaining_at(self, at):
        if self.deadline is None:
            return None
        deadline = self.deadline + (self.extension or 0)
        return deadline - self.days_passed_at(at)

    def deadline_missed_at(self, at):
        # self.deadline_remaining is 0 on the last day of deadline
        remaining = self.deadline_remaining_at(at)
        return remaining is not None and remaining < 0

    def send_by_email(self):
        if not self.is_applicant_action:
            raise TypeError(u'%s is not applicant action' % self.get_type_display())

        sender_name = self.branch.inforequest.applicant_name
        sender_address = self.branch.inforequest.unique_email
        sender_formatted = formataddr((squeeze(sender_name), sender_address))
        recipients = (formataddr(r) for r in self.branch.collect_obligee_emails())

        # FIXME: Attachment name and content type are set by client and not to be trusted. The name
        # must be sanitized and the content type white listed for known content types. Any unknown
        # content type should be replaced with 'application/octet-stream'.

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
        return u'%s' % self.pk

@datacheck.register
def datachecks(superficial, autofix):
    u"""
    Checks that every ``Action.email`` is assigned to ``Action.branch.inforequest``.
    """
    actions = (Action.objects
            .filter(email__isnull=False)
            .annotate(Count(u'branch__inforequest__email_set', only=Q(branch__inforequest__email_set=F(u'email'))))
            .filter(branch__inforequest__email_set__count=0)
            )

    if superficial:
        actions = actions[:5+1]
    issues = [u'%r email is assigned to another inforequest' % a for a in actions]
    if superficial and issues:
        if len(issues) > 5:
            issues[-1] = u'More action emails are assigned to other inforequests'
        issues = [u'; '.join(issues)]
    for issue in issues:
        yield datacheck.Error(issue + u'.')
