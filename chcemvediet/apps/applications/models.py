# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class Application(models.Model):
    applicant = models.ForeignKey(User, verbose_name=_('Applicant'))
    obligee = models.ForeignKey('obligees.Obligee', verbose_name=_('Obligee'))
    unique_email = models.EmailField(max_length=255, unique=True, verbose_name=_('Unique E-mail'))
    submission_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Submission Date'))

    # Frozen Applicant and Obligee contact information at the time the Application was submitted,
    # in case that the contact information changes in the future.
    applicant_name = models.CharField(max_length=255, verbose_name=_('Applicant Name'))
    applicant_street = models.CharField(max_length=255, verbose_name=_('Applicant Street'))
    applicant_city = models.CharField(max_length=255, verbose_name=_('Applicant City'))
    applicant_zip = models.CharField(max_length=10, verbose_name=_('Applicant Zip'))
    obligee_name = models.CharField(max_length=255, verbose_name=_('Obligee Name'))
    obligee_street = models.CharField(max_length=255, verbose_name=_('Obligee Street'))
    obligee_city = models.CharField(max_length=255, verbose_name=_('Obligee City'))
    obligee_zip = models.CharField(max_length=10, verbose_name=_('Obligee Zip'))

    # Backward relations:
    #  -- act_set: Act

    def __unicode__(self):
        return unicode(repr((self.applicant, self.obligee, str(self.submission_date))), 'utf-8')

class ApplicationDraft(models.Model):
    applicant = models.ForeignKey(User, verbose_name=_('Applicant'))
    obligee = models.ForeignKey('obligees.Obligee', blank=True, null=True, verbose_name=_('Obligee'))
    subject = models.CharField(blank=True, max_length=255, verbose_name=_('Subject'))
    content = models.TextField(blank=True, verbose_name=_('Content'))

    def __unicode__(self):
        return unicode(repr((self.applicant, self.obligee)), 'utf-8')

class Act(models.Model):
    REQUEST = 1
    TYPES = (
        (REQUEST, _('Request Act')),
        )
    type = models.SmallIntegerField(choices=TYPES, verbose_name=_('Type'))
    application = models.ForeignKey('Application', verbose_name=_('Application'))
    subject = models.CharField(max_length=255, verbose_name=_('Subject'))
    content = models.TextField(verbose_name=_('Content'))
    effective_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Effective Date'))

    def __unicode__(self):
        return unicode(repr((self.get_type_display(), self.application, str(self.effective_date))), 'utf-8')

