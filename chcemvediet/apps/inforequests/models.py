# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.mail import send_mail
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django_mailbox.signals import message_received

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

    def __unicode__(self):
        return u'%s' % ((self.applicant, self.obligee),)

class InforequestQuerySet(QuerySet):
    def owned_by(self, user):
        return self.filter(applicant=user)

class Inforequest(models.Model):
    applicant = models.ForeignKey(User, verbose_name=_(u'Applicant'))
    history = models.OneToOneField(u'History', verbose_name=_(u'History'))
    unique_email = models.EmailField(max_length=255, unique=True, verbose_name=_(u'Unique E-mail'))
    submission_date = models.DateTimeField(auto_now_add=True, verbose_name=_(u'Submission Date'))

    # Frozen Applicant contact information at the time the Inforequest was submitted,
    # in case that the contact information changes in the future.
    applicant_name = models.CharField(max_length=255, verbose_name=_(u'Applicant Name'))
    applicant_street = models.CharField(max_length=255, verbose_name=_(u'Applicant Street'))
    applicant_city = models.CharField(max_length=255, verbose_name=_(u'Applicant City'))
    applicant_zip = models.CharField(max_length=10, verbose_name=_(u'Applicant Zip'))

    # Backward relations:
    #  -- receivedemail_set: by ReceivedEmail.inforequest

    objects = InforequestQuerySet.as_manager()

    def __unicode__(self):
        return u'%s' % ((self.applicant, self.history.obligee, str(self.submission_date)),)

class History(models.Model):
    obligee = models.ForeignKey(u'obligees.Obligee', verbose_name=_(u'Obligee'))

    # Frozen Obligee contact information at the time the Inforequest was submitted if this is its
    # main History, or the time the Inforequest was advanced to this Obligee otherwise.
    obligee_name = models.CharField(max_length=255, verbose_name=_(u'Obligee Name'))
    obligee_street = models.CharField(max_length=255, verbose_name=_(u'Obligee Street'))
    obligee_city = models.CharField(max_length=255, verbose_name=_(u'Obligee City'))
    obligee_zip = models.CharField(max_length=10, verbose_name=_(u'Obligee Zip'))

    # Backward relations:
    #  -- inforequest: by Inforequest.history; Raises DoesNotExist of it's not main history
    #  -- action_set: by Action.history

    def __unicode__(self):
        try:
            return u'%s' % ((self.inforequest, self.obligee),)
        except Inforequest.DoesNotExist:
            return u'%s' % ((self.obligee,),)

class Action(models.Model):
    TYPES = FieldChoices(
        (u'REQUEST', 1, _(u'Request')),
        )
    history = models.ForeignKey(u'History', verbose_name=_(u'History'))
    type = models.SmallIntegerField(choices=TYPES._choices, verbose_name=_(u'Type'))
    subject = models.CharField(max_length=255, verbose_name=_(u'Subject'))
    content = models.TextField(verbose_name=_(u'Content'))
    effective_date = models.DateTimeField(auto_now_add=True, verbose_name=_(u'Effective Date'))

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
