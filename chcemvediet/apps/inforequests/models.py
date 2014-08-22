# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from poleno.utils.model import FieldChoices

class InforequestDraft(models.Model):
    applicant = models.ForeignKey(User, verbose_name=_(u'Applicant'))
    obligee = models.ForeignKey(u'obligees.Obligee', blank=True, null=True, verbose_name=_(u'Obligee'))
    subject = models.CharField(blank=True, max_length=255, verbose_name=_(u'Subject'))
    content = models.TextField(blank=True, verbose_name=_(u'Content'))

    def __unicode__(self):
        return u'<%s: %s>' % (self.__class__.__name__, (self.applicant, self.obligee))

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

    def __unicode__(self):
        return u'<%s: %s>' % (self.__class__.__name__, (self.applicant, self.history.obligee, self.submission_date))

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
            return u'<%s: %s>' % (self.__class__.__name__, (self.inforequest, self.obligee))
        except Inforequest.DoesNotExist:
            return u'<%s: %s>' % (self.__class__.__name__, (self.obligee))

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
        return u'<%s: %s>' % (self.__class__.__name__, (self.history, self.get_type_display(), self.effective_date))

