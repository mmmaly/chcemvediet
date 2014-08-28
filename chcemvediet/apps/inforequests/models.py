# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.mail import send_mail
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django_mailbox.signals import message_received

from poleno.utils.misc import Bunch, random_readable_string
from poleno.utils.model import FieldChoices, QuerySet

class InforequestDraftQuerySet(QuerySet):
    def owned_by(self, user):
        return self.filter(applicant=user)

class InforequestDraft(models.Model):
    applicant = models.ForeignKey(User, verbose_name=_(u'Applicant'))
    obligee = models.ForeignKey(u'obligees.Obligee', blank=True, null=True, verbose_name=_(u'Obligee'))
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
    applicant = models.ForeignKey(User, verbose_name=_(u'Applicant'))
    history = models.OneToOneField(u'History', verbose_name=_(u'History'))
    unique_email = models.EmailField(max_length=255, unique=True, verbose_name=_(u'Unique E-mail')) # Default value computed in save()
    submission_date = models.DateTimeField(auto_now_add=True, verbose_name=_(u'Submission Date'))

    # Frozen Applicant contact information at the time the Inforequest was submitted, in case that
    # the contact information changes in the future. The information is frozen in save() when
    # creating a new object.
    applicant_name = models.CharField(max_length=255, verbose_name=_(u'Applicant Name'))
    applicant_street = models.CharField(max_length=255, verbose_name=_(u'Applicant Street'))
    applicant_city = models.CharField(max_length=255, verbose_name=_(u'Applicant City'))
    applicant_zip = models.CharField(max_length=10, verbose_name=_(u'Applicant Zip'))

    # Backward relations:
    #  -- receivedemail_set: by ReceivedEmail.inforequest

    objects = InforequestQuerySet.as_manager()

    class Meta:
        ordering = [u'submission_date', u'pk']

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
                while length < 20:
                    self.unique_email = u'%s@mail.chcemvediet.sk' % random_readable_string(length)
                    try:
                        super(Inforequest, self).save(*args, **kwargs)
                    except IntegrityError:
                        length += 1
                        continue
                    return # object is successfully saved
                else:
                    raise RuntimeError(u'Failed to generate unique random e-mail address.')

        super(Inforequest, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % ((self.applicant, self.history.obligee, str(self.submission_date)),)

class History(models.Model):
    obligee = models.ForeignKey(u'obligees.Obligee', verbose_name=_(u'Obligee'))

    # Frozen Obligee contact information at the time the Inforequest was submitted if this is its
    # main History, or the time the Inforequest was advanced to this Obligee otherwise. The
    # information is frozen in save() when creating a new object.
    obligee_name = models.CharField(max_length=255, verbose_name=_(u'Obligee Name'))
    obligee_street = models.CharField(max_length=255, verbose_name=_(u'Obligee Street'))
    obligee_city = models.CharField(max_length=255, verbose_name=_(u'Obligee City'))
    obligee_zip = models.CharField(max_length=10, verbose_name=_(u'Obligee Zip'))

    # Backward relations:
    #  -- inforequest: by Inforequest.history; Raises DoesNotExist of it's not main history
    #  -- action_set: by Action.history

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
    TYPES = FieldChoices(
            (u'REQUEST', 1, _(u'Request')),
            (u'CONFIRMATION', 2, _(u'Confirmation')),
            (u'EXTENSION', 3, _(u'Extension')),
            (u'ADVANCEMENT', 4, _(u'Advancement')),
            (u'CLARIFICATION_REQUEST', 5, _(u'Clarification Request')),
            )
    DEFAULT_DEADLINES = Bunch(
            REQUEST=8,
            CONFIRMATION=8,
            EXTENSION=10,
            ADVANCEMENT=None,
            CLARIFICATION_REQUEST=7,
            )
    history = models.ForeignKey(u'History', verbose_name=_(u'History'))
    type = models.SmallIntegerField(choices=TYPES._choices, verbose_name=_(u'Type'))
    subject = models.CharField(max_length=255, verbose_name=_(u'Subject'))
    content = models.TextField(verbose_name=_(u'Content'))
    effective_date = models.DateTimeField(verbose_name=_(u'Effective Date'))
    deadline = models.IntegerField(blank=True, null=True, verbose_name=_(u'Deadline')) # default value computed in save()

    objects = ActionQuerySet.as_manager()

    class Meta:
        ordering = [u'effective_date', u'pk']

    def save(self, *args, **kwargs):
        if self.pk is None: # Creating a new object
            if self.deadline is None:
                type = self.TYPES._inverse[self.type]
                self.deadline = getattr(self.DEFAULT_DEADLINES, type)
        super(Action, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % ((self.history, self.get_type_display(), self.effective_date),)

class ReceivedEmailQuerySet(QuerySet):
    def undecided(self):
        return self.filter(status=ReceivedEmail.STATUSES.UNDECIDED)

class ReceivedEmail(models.Model):
    STATUSES = FieldChoices(
        (u'UNASSIGNED', 1, _(u'Unassigned')),
        (u'UNDECIDED', 2, _(u'Undecided')),
        (u'UNKNOWN', 3, _(u'Unknown')),
        (u'UNRELATED', 4, _(u'Unrelated')),
        (u'OBLIGEE_ACTION', 5, _(u'Obligee Action')),
        )
    inforequest = models.ForeignKey(u'Inforequest', blank=True, null=True, verbose_name=_(u'Inforequest'))
    raw_email = models.ForeignKey(u'django_mailbox.Message', verbose_name=_(u'Raw E-mail'))
    status = models.SmallIntegerField(choices=STATUSES._choices, verbose_name=_(u'Status'))

    objects = ReceivedEmailQuerySet.as_manager()

    class Meta:
        ordering = [u'raw_email__processed', u'pk']

    def __unicode__(self):
        return u'%s' % ((self.inforequest, self.get_status_display(), self.raw_email),)

@receiver(message_received)
def assign_email_on_message_received(sender, message, **kwargs):
    received_email = ReceivedEmail(raw_email=message)
    try:
        inforequest = Inforequest.objects.get(unique_email__in=message.to_addresses)
    except (Inforequest.DoesNotExist, Inforequest.MultipleObjectsReturned):
        received_email.status = received_email.STATUSES.UNASSIGNED
    else:
        received_email.inforequest = inforequest
        received_email.status = received_email.STATUSES.UNDECIDED
    received_email.save()

    if received_email.inforequest:
        subject = _(u'New e-mail notification');
        message = _(u'We got an e-mail from \'%s\' regarding your inforequest to \'%s\'.') % (
                message.from_header, received_email.inforequest.history.obligee_name)
        send_mail(subject, message, u'info@chcemvediet.sk', [received_email.inforequest.applicant.email])
