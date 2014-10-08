# vim: expandtab
# -*- coding: utf-8 -*-
from email.utils import formataddr

from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage
from django.db import models, IntegrityError
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic

from poleno.workdays import workdays
from poleno.utils.misc import Bunch, random_readable_string, squeeze
from poleno.utils.models import FieldChoices, QuerySet
from poleno.utils.mail import render_mail
from poleno.utils.date import utc_now, local_today

class InforequestDraftQuerySet(QuerySet):
    def owned_by(self, user):
        return self.filter(applicant=user)

class InforequestDraft(models.Model):
    # May NOT be NULL
    applicant = models.ForeignKey(User, verbose_name=_(u'Applicant'))

    # May be NULL
    obligee = models.ForeignKey(u'obligees.Obligee', blank=True, null=True, verbose_name=_(u'Obligee'))

    # May be empty
    subject = models.CharField(blank=True, max_length=255, verbose_name=_(u'Subject'))
    content = models.TextField(blank=True, verbose_name=_(u'Content'))

    # May be empty
    attachment_set = generic.GenericRelation(u'attachments.Attachment', content_type_field=u'generic_type', object_id_field=u'generic_id', verbose_name=_(u'Attachment Set'))

    objects = InforequestDraftQuerySet.as_manager()

    class Meta:
        ordering = [u'pk']

    def __unicode__(self):
        return u'%s' % self.pk

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

class Inforequest(models.Model):
    # May NOT be NULL
    applicant = models.ForeignKey(User, verbose_name=_(u'Applicant'))

    # May be empty; m2m through InforequestEmail
    email_set = models.ManyToManyField(u'mail.Message', through=u'InforequestEmail', verbose_name=_(u'E-mail Set'))

    # Frozen Applicant contact information at the time the Inforequest was submitted, in case that
    # the contact information changes in the future. The information is mandatory and automaticly
    # frozen in save() when creating a new object.
    applicant_name = models.CharField(max_length=255, verbose_name=_(u'Applicant Name'))
    applicant_street = models.CharField(max_length=255, verbose_name=_(u'Applicant Street'))
    applicant_city = models.CharField(max_length=255, verbose_name=_(u'Applicant City'))
    applicant_zip = models.CharField(max_length=10, verbose_name=_(u'Applicant Zip'))

    # May NOT be empty; Unique; Automaticly computed in save() when creating a new object.
    unique_email = models.EmailField(max_length=255, unique=True, verbose_name=_(u'Unique E-mail'))

    # May NOT be NULL; Automaticly computed by Django when creating a new object.
    submission_date = models.DateField(auto_now_add=True, verbose_name=_(u'Submission Date'))

    # May NOT be NULL
    closed = models.BooleanField(default=False, verbose_name=_(u'Closed'))

    # May be NULL; Used by ``cron.undecided_email_reminder``
    last_undecided_email_reminder = models.DateTimeField(blank=True, null=True, verbose_name=_(u'Last Undecided Email Reminder'))

    # Backward relation:
    #
    #  -- history_set: by History.inforequest
    #     May NOT be empty
    #
    #  -- actiondraft_set: by ActionDraft.inforequest
    #     May be empty; May contain at most one instance for every ActionDraft.TYPES
    #
    #  -- inforequestemail_set: by InforequestEmail.inforequest
    #     May be empty

    objects = InforequestQuerySet.as_manager()

    class Meta:
        ordering = [u'submission_date', u'pk']

    # May NOT be NULL; Read-only
    @property
    def history(self):
        return self.history_set.get(advanced_by=None)

    # May be empty; Read-only
    @property
    def undecided_set(self):
        return self.email_set.filter(inforequestemail__type=InforequestEmail.TYPES.UNDECIDED)

    # May NOT be NULL; Read-only
    @property
    def has_undecided_email(self):
        return self.undecided_set.exists()

    # May be NULL; Read-only
    @property
    def oldest_undecided_email(self):
        return self.undecided_set.first()

    # May be NULL; Read-only
    @property
    def newest_undecided_email(self):
        return self.undecided_set.last()

    # May NOT be NULL; Read-only
    @property
    def can_add_clarification_response(self):
        return self.can_add_action(Action.TYPES.CLARIFICATION_RESPONSE)

    # May NOT be NULL; Read-only
    @property
    def can_add_appeal(self):
        return self.can_add_action(Action.TYPES.APPEAL)

    # May NOT be NULL; Read-only
    @property
    def can_add_confirmation(self):
        return self.can_add_action(Action.TYPES.CONFIRMATION)

    # May NOT be NULL; Read-only
    @property
    def can_add_extension(self):
        return self.can_add_action(Action.TYPES.EXTENSION)

    # May NOT be NULL; Read-only
    @property
    def can_add_advancement(self):
        return self.can_add_action(Action.TYPES.ADVANCEMENT)

    # May NOT be NULL; Read-only
    @property
    def can_add_clarification_request(self):
        return self.can_add_action(Action.TYPES.CLARIFICATION_REQUEST)

    # May NOT be NULL; Read-only
    @property
    def can_add_disclosure(self):
        return self.can_add_action(Action.TYPES.DISCLOSURE)

    # May NOT be NULL; Read-only
    @property
    def can_add_refusal(self):
        return self.can_add_action(Action.TYPES.REFUSAL)

    # May NOT be NULL; Read-only
    @property
    def can_add_affirmation(self):
        return self.can_add_action(Action.TYPES.AFFIRMATION)

    # May NOT be NULL; Read-only
    @property
    def can_add_reversion(self):
        return self.can_add_action(Action.TYPES.REVERSION)

    # May NOT be NULL; Read-only
    @property
    def can_add_remandment(self):
        return self.can_add_action(Action.TYPES.REMANDMENT)

    def can_add_action(self, action_type):
        for history in self.history_set.all():
            if history.can_add_action(action_type):
                return True
        return False

    def save(self, *args, **kwargs):
        if self.pk is None: # Creating a new object

            # Freeze applicant contact information
            if self.applicant:
                self.applicant_name = self.applicant.get_full_name()
                self.applicant_street = self.applicant.profile.street
                self.applicant_city = self.applicant.profile.city
                self.applicant_zip = self.applicant.profile.zip

            # Generate unique random email
            if not self.unique_email:
                length = 4
                while True:
                    token = random_readable_string(length)
                    self.unique_email = settings.INFOREQUEST_UNIQUE_EMAIL.format(token=token)
                    try:
                        super(Inforequest, self).save(*args, **kwargs)
                    except IntegrityError:
                        if length > 10:
                            self.unique_email = None
                            raise # Give up
                        length += 1
                        continue
                    return # object is already saved

        super(Inforequest, self).save(*args, **kwargs)

    def _send_notification(self, template, anchor, dictionary):
        url = u'http://127.0.0.1:8000%s#%s' % (reverse(u'inforequests:detail', args=(self.id,)), anchor)
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
        self.save()

    def send_obligee_deadline_reminder(self, action):
        self._send_notification(u'inforequests/mails/obligee_deadline_reminder', u'action-%s' % action.pk, {
                u'action': action,
                })

        action.last_deadline_reminder = utc_now()
        action.save()

    def send_applicant_deadline_reminder(self, action):
        self._send_notification(u'inforequests/mails/applicant_deadline_reminder', u'action-%s' % action.pk, {
                u'action': action,
                })

        action.last_deadline_reminder = utc_now()
        action.save()

    def __unicode__(self):
        return u'%s' % self.pk

class InforequestEmail(models.Model):
    # May NOT be NULL; m2m ends
    inforequest = models.ForeignKey(u'Inforequest', verbose_name=_(u'Inforequest'))
    email = models.ForeignKey(u'mail.Message', verbose_name=_(u'E-mail'))

    # May NOT be NULL
    TYPES = FieldChoices(
            # For outbound messages
            (u'APPLICANT_ACTION', 1, _(u'Applicant Action')),
            # For inbound messages
            (u'OBLIGEE_ACTION', 2, _(u'Obligee Action')),
            (u'UNDECIDED', 3, _(u'Undecided')),
            (u'UNRELATED', 4, _(u'Unrelated')),
            (u'UNKNOWN', 5, _(u'Unknown')),
            )
    type = models.SmallIntegerField(choices=TYPES._choices, verbose_name=_(u'Type'))

class History(models.Model):
    # May NOT be NULL
    inforequest = models.ForeignKey(u'Inforequest', verbose_name=_(u'Inforequest'))

    # May NOT be NULL
    obligee = models.ForeignKey(u'obligees.Obligee', verbose_name=_(u'Obligee'))

    # Advancement action that advanced the inforequest to this obligee; None if it's inforequest
    # main history. Inforequest must contain exactly one history with ``advanced_by`` set to None.
    advanced_by = models.ForeignKey(u'Action', related_name=u'advanced_to_set', blank=True, null=True, verbose_name=_(u'Advanced By'))

    # Frozen Obligee contact information at the time the Inforequest was submitted if this is its
    # main History, or the time the Inforequest was advanced to this Obligee otherwise. The
    # information is mandatory and automaticly frozen in save() when creating a new object.
    obligee_name = models.CharField(max_length=255, verbose_name=_(u'Obligee Name'))
    obligee_street = models.CharField(max_length=255, verbose_name=_(u'Obligee Street'))
    obligee_city = models.CharField(max_length=255, verbose_name=_(u'Obligee City'))
    obligee_zip = models.CharField(max_length=10, verbose_name=_(u'Obligee Zip'))

    # Backward relations:
    #
    #  -- action_set: by Action.history
    #     May NOT be empty; The first action of every main history must be REQUEST and the first
    #     action of every advanced history ADVANCED_REQUEST.

    objects = QuerySet.as_manager()

    class Meta:
        ordering = [u'obligee_name', u'pk']

    # May NOT be NULL; Read-only
    @property
    def last_action(self):
        return self.action_set.last()

    # May NOT be NULL; Read-only
    @property
    def can_add_clarification_response(self):
        return self.last_action.type == Action.TYPES.CLARIFICATION_REQUEST

    # May NOT be NULL; Read-only
    @property
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

    # May NOT be NULL; Read-only
    @property
    def can_add_confirmation(self):
        return self.last_action.type in [
                Action.TYPES.REQUEST,
                Action.TYPES.ADVANCED_REQUEST,
                ]

    # May NOT be NULL; Read-only
    @property
    def can_add_extension(self):
        return self.last_action.type in [
                Action.TYPES.REQUEST,
                Action.TYPES.CONFIRMATION,
                Action.TYPES.CLARIFICATION_RESPONSE,
                Action.TYPES.REMANDMENT,
                Action.TYPES.ADVANCED_REQUEST,
                ]

    # May NOT be NULL; Read-only
    @property
    def can_add_advancement(self):
        return self.last_action.type in [
                Action.TYPES.REQUEST,
                Action.TYPES.CLARIFICATION_RESPONSE,
                Action.TYPES.CONFIRMATION,
                Action.TYPES.ADVANCED_REQUEST,
                ]

    # May NOT be NULL; Read-only
    @property
    def can_add_clarification_request(self):
        return self.last_action.type in [
                Action.TYPES.REQUEST,
                Action.TYPES.CLARIFICATION_RESPONSE,
                Action.TYPES.CONFIRMATION,
                Action.TYPES.CLARIFICATION_REQUEST,
                Action.TYPES.ADVANCED_REQUEST,
                ]

    # May NOT be NULL; Read-only
    @property
    def can_add_disclosure(self):
        return self.last_action.type in [
                Action.TYPES.REQUEST,
                Action.TYPES.CLARIFICATION_RESPONSE,
                Action.TYPES.CONFIRMATION,
                Action.TYPES.EXTENSION,
                Action.TYPES.REMANDMENT,
                Action.TYPES.ADVANCED_REQUEST,
                ]

    # May NOT be NULL; Read-only
    @property
    def can_add_refusal(self):
        return self.last_action.type in [
                Action.TYPES.REQUEST,
                Action.TYPES.CLARIFICATION_RESPONSE,
                Action.TYPES.CONFIRMATION,
                Action.TYPES.EXTENSION,
                Action.TYPES.REMANDMENT,
                Action.TYPES.ADVANCED_REQUEST,
                ]

    # May NOT be NULL; Read-only
    @property
    def can_add_affirmation(self):
        return self.last_action.type == Action.TYPES.APPEAL

    # May NOT be NULL; Read-only
    @property
    def can_add_reversion(self):
        return self.last_action.type == Action.TYPES.APPEAL

    # May NOT be NULL; Read-only
    @property
    def can_add_remandment(self):
        return self.last_action.type == Action.TYPES.APPEAL

    def can_add_action(self, action_type):
        type_name = Action.TYPES._inverse[action_type]
        return getattr(self, u'can_add_%s' % type_name.lower())

    def save(self, *args, **kwargs):
        if self.pk is None: # Creating a new object

            # Freeze obligee contact information
            if self.obligee:
                self.obligee_name = self.obligee.name
                self.obligee_street = self.obligee.street
                self.obligee_city = self.obligee.city
                self.obligee_zip = self.obligee.zip

        super(History, self).save(*args, **kwargs)

    def add_expiration_if_expired(self):
        if self.last_action.has_obligee_deadline and self.last_action.deadline_missed:
            expiration = Action(
                    history=self,
                    type=(Action.TYPES.APPEAL_EXPIRATION if self.last_action.type == Action.TYPES.APPEAL else Action.TYPES.EXPIRATION),
                    effective_date=local_today(),
                    )
            expiration.save()

    def __unicode__(self):
        return u'%s' % self.pk

class ActionQuerySet(QuerySet):
    def requests(self):
        return self.filter(type=Action.TYPES.REQUEST)
    def confirmations(self):
        return self.filter(type=Action.TYPES.CONFIRMATION)
    def extensions(self):
        return self.filter(type=Action.TYPES.EXTENSION)
    def advancements(self):
        return self.filter(type=Action.TYPES.ADVANCEMENT)
    def clarification_requests(self):
        return self.filter(type=Action.TYPES.CLARIFICATION_REQUEST)

class Action(models.Model):
    # May NOT be NULL
    history = models.ForeignKey(u'History', verbose_name=_(u'History'))

    # May NOT be NULL for actions sent or received by email; NULL otherwise
    email = models.OneToOneField(u'mail.Message', blank=True, null=True, verbose_name=_(u'E-mail'))

    # May NOT be NULL
    TYPES = FieldChoices(
            # Applicant actions
            (u'REQUEST', 1, _(u'Request')),
            (u'CLARIFICATION_RESPONSE', 12, _(u'Clarification Response')),
            (u'APPEAL', 13, _(u'Appeal')),
            # Obligee actions
            (u'CONFIRMATION', 2, _(u'Confirmation')),
            (u'EXTENSION', 3, _(u'Extension')),
            (u'ADVANCEMENT', 4, _(u'Advancement')),
            (u'CLARIFICATION_REQUEST', 5, _(u'Clarification Request')),
            (u'DISCLOSURE', 6, _(u'Disclosure')),
            (u'REFUSAL', 7, _(u'Refusal')),
            (u'AFFIRMATION', 8, _(u'Affirmation')),
            (u'REVERSION', 9, _(u'Reversion')),
            (u'REMANDMENT', 10, _(u'Remandment')),
            # Implicit actions
            (u'ADVANCED_REQUEST', 11, _(u'Advanced Request')),
            (u'EXPIRATION', 14, _(u'Expiration')),
            (u'APPEAL_EXPIRATION', 15, _(u'Appeal Expiration')),
            )
    type = models.SmallIntegerField(choices=TYPES._choices, verbose_name=_(u'Type'))

    # May be empty for implicit actions; Should NOT be empty for other actions
    subject = models.CharField(blank=True, max_length=255, verbose_name=_(u'Subject'))
    content = models.TextField(blank=True, verbose_name=_(u'Content'))

    # May be empty
    attachment_set = generic.GenericRelation(u'attachments.Attachment', content_type_field=u'generic_type', object_id_field=u'generic_id', verbose_name=_(u'Attachment Set'))

    # May NOT be NULL
    effective_date = models.DateField(verbose_name=_(u'Effective Date'))

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
            ADVANCEMENT=None,
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
            EXPIRATION=None,
            APPEAL_EXPIRATION=None,
            )
    deadline = models.IntegerField(blank=True, null=True, verbose_name=_(u'Deadline'))

    # May be NULL
    extension = models.IntegerField(blank=True, null=True, verbose_name=_(u'Deadline Extension'))

    # May NOT be NULL for ADVANCEMENT, DISCLOSURE, REVERSION and REMANDMENT; Must be NULL otherwise
    DISCLOSURE_LEVELS = FieldChoices(
            (u'NONE', 1, _(u'No Disclosure at All')),
            (u'PARTIAL', 2, _(u'Partial Disclosure')),
            (u'FULL', 3, _(u'Full Disclosure')),
            )
    disclosure_level = models.SmallIntegerField(choices=DISCLOSURE_LEVELS._choices, blank=True, null=True, verbose_name=_(u'Disclosure Level'))

    # May NOT be NULL for REFUSAL, AFFIRMATION; Must be None otherwise
    REFUSAL_REASONS = FieldChoices(
            (u'DOES_NOT_HAVE', 3, _(u'Does not Have Information')),
            (u'DOES_NOT_PROVIDE', 4, _(u'Does not Provide Information')),
            (u'DOES_NOT_CREATE', 5, _(u'Does not Create Information')),
            (u'COPYRIGHT', 6, _(u'Copyright Restriction')),
            (u'BUSINESS_SECRET', 7, _(u'Business Secret')),
            (u'PERSONAL', 8, _(u'Personal Information')),
            (u'CONFIDENTIAL', 9, _(u'Confidential Information')),
            (u'NO_REASON', -1, _(u'No Reason Specified')),
            (u'OTHER_REASON', -2, _(u'Other Reason')),
            )
    refusal_reason = models.SmallIntegerField(choices=REFUSAL_REASONS._choices, blank=True, null=True, verbose_name=_(u'Refusal Reason'))

    # May be NULL; Used by ``cron.obligee_deadline_reminder`` and ``cron.applicant_deadline_reminder``
    last_deadline_reminder = models.DateTimeField(blank=True, null=True, verbose_name=_(u'Last Deadline Reminder'))

    # Backward relations:
    #
    #  -- advanced_to_set: by History.advanced_by
    #     May NOT be empty for ADVANCEMENT; Must be empty otherwise

    objects = ActionQuerySet.as_manager()

    class Meta:
        ordering = [u'effective_date', u'pk']

    # May NOT be NULL; Read-only
    @property
    def is_applicant_action(self):
        return self.type in [
                self.TYPES.REQUEST,
                self.TYPES.CLARIFICATION_RESPONSE,
                self.TYPES.APPEAL,
                ]

    # May NOT be NULL; Read-only
    @property
    def is_obligee_action(self):
        return self.type in [
                self.TYPES.CONFIRMATION,
                self.TYPES.EXTENSION,
                self.TYPES.ADVANCEMENT,
                self.TYPES.CLARIFICATION_REQUEST,
                self.TYPES.DISCLOSURE,
                self.TYPES.REFUSAL,
                self.TYPES.AFFIRMATION,
                self.TYPES.REVERSION,
                self.TYPES.REMANDMENT,
                ]

    # May NOT be NULL; Read-only
    @property
    def is_implicit_action(self):
        return self.type in [
                self.TYPES.ADVANCED_REQUEST,
                self.TYPES.EXPIRATION,
                self.TYPES.APPEAL_EXPIRATION,
                ]

    # May NOT be NULL; Read-only
    @property
    def days_passed(self):
        return self.days_passed_at(local_today())

    # May be NULL; Read-only
    @property
    def deadline_remaining(self):
        return self.deadline_remaining_at(local_today())

    # May NOT be NULL; Read-only
    @property
    def deadline_missed(self):
        return self.deadline_missed_at(local_today())

    # May NOT be NULL; Read-only
    @property
    def has_deadline(self):
        return self.deadline is not None

    # May NOT be NULL; Read-only
    @property
    def has_applicant_deadline(self):
        return self.deadline is not None and self.type in [
                # Applicant actions
                # Obligee actions
                self.TYPES.CLARIFICATION_REQUEST,
                self.TYPES.DISCLOSURE,
                self.TYPES.REFUSAL,
                # Implicit actions
                ]

    # May NOT be NULL; Read-only
    @property
    def has_obligee_deadline(self):
        return self.deadline is not None and self.type in [
                # Applicant actions
                self.TYPES.REQUEST,
                self.TYPES.CLARIFICATION_RESPONSE,
                self.TYPES.APPEAL,
                # Obligee actions
                self.TYPES.CONFIRMATION,
                self.TYPES.EXTENSION,
                self.TYPES.REMANDMENT,
                # Implicit actions
                self.TYPES.ADVANCED_REQUEST,
                ]

    def save(self, *args, **kwargs):
        if self.pk is None: # Creating a new object
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
            raise TypeError

        sender_name = self.history.inforequest.applicant_name
        sender_address = self.history.inforequest.unique_email
        sender_full = formataddr((squeeze(sender_name), sender_address))
        recipient_address = self.history.obligee.email

        # FIXME: Attachment name and content type are set by client and not to be trusted. The name
        # must be sanitized and the content type white listed for known content types. Any unknown
        # content type should be replaced with 'application/octet-stream'.

        msg = EmailMessage(self.subject, self.content, sender_full, [recipient_address])
        for attachment in self.attachment_set.all():
            msg.attach(attachment.name, attachment.content, attachment.content_type)
        msg.send()

        inforequestemail = InforequestEmail(
                inforequest=self.history.inforequest,
                email=msg.instance,
                type=InforequestEmail.TYPES.APPLICANT_ACTION,
                )
        inforequestemail.save()

        self.email = msg.instance
        self.save()

    def __unicode__(self):
        return u'%s' % self.pk

class ActionDraft(models.Model):
    # May NOT be NULL
    inforequest = models.ForeignKey(u'Inforequest', verbose_name=_(u'Inforequest'))

    # May be NULL; Must be owned by the inforequest if set.
    history = models.ForeignKey(u'History', blank=True, null=True, verbose_name=_(u'History'))

    # May NOT be NULL
    TYPES = Action.TYPES
    type = models.SmallIntegerField(choices=TYPES._choices, verbose_name=_(u'Type'))

    # May be empty
    subject = models.CharField(blank=True, max_length=255, verbose_name=_(u'Subject'))
    content = models.TextField(blank=True, verbose_name=_(u'Content'))

    # May be empty
    attachment_set = generic.GenericRelation(u'attachments.Attachment', content_type_field=u'generic_type', object_id_field=u'generic_id', verbose_name=_(u'Attachment Set'))

    # May NOT be NULL
    effective_date = models.DateField(blank=True, null=True, verbose_name=_(u'Effective Date'))

    # May be NULL for EXTENSION; Must be NULL otherwise
    deadline = models.IntegerField(blank=True, null=True, verbose_name=_(u'Deadline'))

    # May be NULL for ADVANCEMENT, DISCLOSURE, REVERSION and REMANDMENT; Must be NULL otherwise
    DISCLOSURE_LEVELS = Action.DISCLOSURE_LEVELS
    disclosure_level = models.SmallIntegerField(choices=DISCLOSURE_LEVELS._choices, blank=True, null=True, verbose_name=_(u'Disclosure Level'))

    # May be NULL for REFUSAL and AFFIRMATION; Must be NULL otherwise
    REFUSAL_REASONS = Action.REFUSAL_REASONS
    refusal_reason = models.SmallIntegerField(choices=REFUSAL_REASONS._choices, blank=True, null=True, verbose_name=_(u'Refusal Reason'))

    # May be empty for ADVANCEMENT; Must be empty otherwise
    obligee_set = models.ManyToManyField(u'obligees.Obligee', verbose_name=_(u'Obligee Set'))

    objects = QuerySet.as_manager()

    class Meta:
        ordering = [u'pk']

    def __unicode__(self):
        return u'%s' % self.pk

import signals
