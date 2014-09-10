# vim: expandtab
# -*- coding: utf-8 -*-
import datetime
from email.utils import formataddr

from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.db import models, IntegrityError
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _, activate
from django.contrib.auth.models import User

from django_mailbox.signals import message_received

from poleno.utils.misc import Bunch, random_readable_string, squeeze
from poleno.utils.model import FieldChoices, QuerySet
from poleno.utils.mail import render_mail
from poleno.workdays import workdays

class InforequestDraftQuerySet(QuerySet):
    def owned_by(self, user):
        return self.filter(applicant=user)

class InforequestDraft(models.Model):
    # Mandatory
    applicant = models.ForeignKey(User, verbose_name=_(u'Applicant'))

    # Optional
    obligee = models.ForeignKey(u'obligees.Obligee', blank=True, null=True, verbose_name=_(u'Obligee'))

    # May be empty
    subject = models.CharField(blank=True, max_length=255, verbose_name=_(u'Subject'))
    content = models.TextField(blank=True, verbose_name=_(u'Content'))

    objects = InforequestDraftQuerySet.as_manager()

    class Meta:
        ordering = [u'pk']

    def __unicode__(self):
        return u'%s' % ((self.applicant, self.obligee),)

class InforequestQuerySet(QuerySet):
    def owned_by(self, user):
        return self.filter(applicant=user)

class Inforequest(models.Model):
    # Mandatory
    applicant = models.ForeignKey(User, verbose_name=_(u'Applicant'))

    # Frozen Applicant contact information at the time the Inforequest was submitted, in case that
    # the contact information changes in the future. The information is mandatory and automaticly
    # frozen in save() when creating a new object.
    applicant_name = models.CharField(max_length=255, verbose_name=_(u'Applicant Name'))
    applicant_street = models.CharField(max_length=255, verbose_name=_(u'Applicant Street'))
    applicant_city = models.CharField(max_length=255, verbose_name=_(u'Applicant City'))
    applicant_zip = models.CharField(max_length=10, verbose_name=_(u'Applicant Zip'))

    # Mandatory and unique; Automaticly computed in save() when creating a new object.
    unique_email = models.EmailField(max_length=255, unique=True, verbose_name=_(u'Unique E-mail'))

    # Mandatory; Automaticly computed by Django when creating a new object.
    submission_date = models.DateField(auto_now_add=True, verbose_name=_(u'Submission Date'))

    # Backward relation:
    #
    #  -- history_set: by History.inforequest
    #     May NOT be empty
    #
    #  -- actiondraft_set: by ActionDraft.inforequest
    #     May be empty; May contain at most one instance for every ActionDraft.TYPES
    #
    #  -- receivedemail_set: by ReceivedEmail.inforequest
    #     May be empty

    objects = InforequestQuerySet.as_manager()

    class Meta:
        ordering = [u'submission_date', u'pk']

    @property
    def history(self):
        return self.history_set.get(advanced_by=None)

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
                    self.unique_email = u'%s@mail.chcemvediet.sk' % random_readable_string(length)
                    try:
                        super(Inforequest, self).save(*args, **kwargs)
                    except IntegrityError:
                        if length > 10:
                            raise # Give up
                        length += 1
                        continue
                    return # object is already saved

        super(Inforequest, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % ((self.applicant, self.history.obligee, str(self.submission_date)),)

class History(models.Model):
    # Mandatory
    inforequest = models.ForeignKey(u'Inforequest', verbose_name=_(u'Inforequest'))

    # Mandatory
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

    def save(self, *args, **kwargs):
        if self.pk is None: # Creating a new object

            # Freeze obligee contact information
            if self.obligee:
                self.obligee_name = self.obligee.name
                self.obligee_street = self.obligee.street
                self.obligee_city = self.obligee.city
                self.obligee_zip = self.obligee.zip

        super(History, self).save(*args, **kwargs)

    def __unicode__(self):
        try:
            return u'%s' % ((self.inforequest, self.obligee),)
        except Inforequest.DoesNotExist:
            return u'%s' % ((self.obligee,),)

class ReceivedEmailQuerySet(QuerySet):
    def undecided(self):
        return self.filter(status=ReceivedEmail.STATUSES.UNDECIDED)

class ReceivedEmail(models.Model):
    # None for UNASSIGNED emails; Mandatory otherwise
    inforequest = models.ForeignKey(u'Inforequest', blank=True, null=True, verbose_name=_(u'Inforequest'))

    # Mandatory
    raw_email = models.ForeignKey(u'django_mailbox.Message', verbose_name=_(u'Raw E-mail'))

    # Mandatory choice
    STATUSES = FieldChoices(
        (u'UNASSIGNED', 1, _(u'Unassigned')),
        (u'UNDECIDED', 2, _(u'Undecided')),
        (u'UNKNOWN', 3, _(u'Unknown')),
        (u'UNRELATED', 4, _(u'Unrelated')),
        (u'OBLIGEE_ACTION', 5, _(u'Obligee Action')),
        )
    status = models.SmallIntegerField(choices=STATUSES._choices, verbose_name=_(u'Status'))

    # Backward relations:
    #
    #  -- action: by Action.receivedemail
    #     Mandatory for OBLIGEE_ACTION; Raises DoesNotExist otherwise

    objects = ReceivedEmailQuerySet.as_manager()

    class Meta:
        ordering = [u'raw_email__processed', u'pk']

    def __unicode__(self):
        return u'%s' % ((self.inforequest, self.get_status_display(), self.raw_email),)

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
    # Mandatory
    history = models.ForeignKey(u'History', verbose_name=_(u'History'))

    # Mandatory for actions received by email; None otherwise
    receivedemail = models.OneToOneField(u'ReceivedEmail', blank=True, null=True, verbose_name=_(u'Received E-mail'))

    # Mandatory choice
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
            )
    type = models.SmallIntegerField(choices=TYPES._choices, verbose_name=_(u'Type'))

    # May be empty for implicit actions; Should NOT be empty for other actions
    subject = models.CharField(blank=True, max_length=255, verbose_name=_(u'Subject'))
    content = models.TextField(blank=True, verbose_name=_(u'Content'))

    # Mandatory
    effective_date = models.DateField(verbose_name=_(u'Effective Date'))

    # Mandatory for actions that set deadline; Must be NULL otherwise. Default value is determined
    # and automaticly set in save() when creating a new object. All actions that set deadlines
    # except CLARIFICATION_REQUEST, DISCLOSURE and REFUSAL set the deadline for the obligee.
    # CLARIFICATION_REQUEST, DISCLOSURE and REFUSAL set the deadline for the applicant.
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
            DISCLOSURE=15,           # Deadline for the applicant
            REFUSAL=15,              # Deadline for the applicant
            AFFIRMATION=None,
            REVERSION=None,
            REMANDMENT=13,
            # Implicit actions
            ADVANCED_REQUEST=13,
            )
    deadline = models.IntegerField(blank=True, null=True, verbose_name=_(u'Deadline'))

    # Optional
    extension = models.IntegerField(blank=True, null=True, verbose_name=_(u'Deadline Extension'))

    # Mandatory for ADVANCEMENT, DISCLOSURE, REVERSION and REMANDMENT; Must be NULL otherwise
    DISCLOSURE_LEVELS = FieldChoices(
            (u'NONE', 1, _(u'No Disclosure at All')),
            (u'PARTIAL', 2, _(u'Partial Disclosure')),
            (u'FULL', 3, _(u'Full Disclosure')),
            )
    disclosure_level = models.SmallIntegerField(choices=DISCLOSURE_LEVELS._choices, blank=True, null=True, verbose_name=_(u'Disclosure Level'))

    # Mandatory for REFUSAL, AFFIRMATION; Must be None otherwise
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

    # Backward relations:
    #
    #  -- advanced_to_set: by History.advanced_by
    #     Mandatory for ADVANCEMENT; Must be empty otherwise

    objects = ActionQuerySet.as_manager()

    class Meta:
        ordering = [u'effective_date', u'pk']

    @property
    def days_passed(self):
        return workdays.between(self.effective_date, datetime.date.today())

    @property
    def deadline_remaining(self):
        if self.deadline is None:
            return None
        deadline = self.deadline + (self.extension or 0)
        return deadline - self.days_passed

    @property
    def deadline_missed(self):
        # self.deadline_remaining is 0 on the last day of deadline
        remaining = self.deadline_remaining
        return remaining is not None and remaining < 0

    def save(self, *args, **kwargs):
        if self.pk is None: # Creating a new object
            if self.deadline is None:
                type = self.TYPES._inverse[self.type]
                self.deadline = getattr(self.DEFAULT_DEADLINES, type)
        super(Action, self).save(*args, **kwargs)

    def send_by_email(self):
        # FIXME: We should assert, this is an Applicant Action!
        sender_name = self.history.inforequest.applicant_name
        sender_address = self.history.inforequest.unique_email
        sender_full = formataddr((squeeze(sender_name), sender_address))
        recipient_address = self.history.obligee.email
        send_mail(self.subject, self.content, sender_full, [recipient_address])

    def __unicode__(self):
        return u'%s' % ((self.history, self.get_type_display(), self.effective_date),)

class ActionDraft(models.Model):
    # Mandatory
    inforequest = models.ForeignKey(u'Inforequest', verbose_name=_(u'Inforequest'))

    # Optional; Must be owned by the inforequest if set.
    history = models.ForeignKey(u'History', blank=True, null=True, verbose_name=_(u'History'))

    # Mandatory choice
    TYPES = Action.TYPES
    type = models.SmallIntegerField(choices=TYPES._choices, verbose_name=_(u'Type'))

    # May be empty
    subject = models.CharField(blank=True, max_length=255, verbose_name=_(u'Subject'))
    content = models.TextField(blank=True, verbose_name=_(u'Content'))

    # Optional
    effective_date = models.DateField(blank=True, null=True, verbose_name=_(u'Effective Date'))

    # Optional for EXTENSION; Must be None otherwise
    deadline = models.IntegerField(blank=True, null=True, verbose_name=_(u'Deadline'))

    # Optional for ADVANCEMENT, DISCLOSURE, REVERSION and REMANDMENT; Must be None otherwise
    DISCLOSURE_LEVELS = Action.DISCLOSURE_LEVELS
    disclosure_level = models.SmallIntegerField(choices=DISCLOSURE_LEVELS._choices, blank=True, null=True, verbose_name=_(u'Disclosure Level'))

    # Optional for REFUSAL and AFFIRMATION; Must be None otherwise
    REFUSAL_REASONS = Action.REFUSAL_REASONS
    refusal_reason = models.SmallIntegerField(choices=REFUSAL_REASONS._choices, blank=True, null=True, verbose_name=_(u'Refusal Reason'))

    # May be empty for ADVANCEMENT; Must be empty otherwise
    obligee_set = models.ManyToManyField(u'obligees.Obligee', verbose_name=_(u'Obligee Set'))

    objects = QuerySet.as_manager()

    class Meta:
        ordering = [u'pk']

    def __unicode__(self):
        return u'%s' % ((self.inforequest, self.get_type_display()),)

@receiver(message_received)
def assign_email_on_message_received(sender, message, **kwargs):
    try:
        receivedemail = ReceivedEmail(raw_email=message)
        try:
            inforequest = Inforequest.objects.get(unique_email__in=message.to_addresses)
        except (Inforequest.DoesNotExist, Inforequest.MultipleObjectsReturned):
            receivedemail.status = receivedemail.STATUSES.UNASSIGNED
        else:
            receivedemail.inforequest = inforequest
            receivedemail.status = receivedemail.STATUSES.UNDECIDED
        receivedemail.save()

        if receivedemail.inforequest:
            activate(u'en') # We need to select active locale ('en-us' is selected by default)
            decide_url = u'http://127.0.0.1:8000%s#decide' % reverse(u'inforequests:detail', args=(receivedemail.inforequest.id,))
            msg = render_mail(u'inforequests/mails/new_mail_notification',
                    from_email=u'info@chcemvediet.sk',
                    to=[receivedemail.inforequest.applicant.email],
                    dictionary={
                        u'receivedemail': receivedemail,
                        u'inforequest': receivedemail.inforequest,
                        u'decide_url': decide_url,
                        })
            msg.send()
    except Exception as e:
        print(e)
        raise
