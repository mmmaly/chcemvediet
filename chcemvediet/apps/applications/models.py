# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class Application(models.Model):
    applicant = models.ForeignKey(User, verbose_name=_('Applicant'))
    obligee = models.ForeignKey('obligees.Obligee', verbose_name=_('Obligee'))
    subject = models.CharField(max_length=255, verbose_name=_('Subject'))
    message = models.TextField(verbose_name=_('Message'))
    submission_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Submission Date'))
    sender_email = models.EmailField(max_length=255, unique=True, verbose_name=_('Sender E-mail'))
    recepient_email = models.EmailField(max_length=255, verbose_name=_('Recepient E-mail'))
    def __unicode__(self):
        return unicode(repr((self.applicant, self.obligee, str(self.submission_date))), 'utf-8')

