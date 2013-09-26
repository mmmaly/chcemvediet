# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User

class Application(models.Model):
    applicant = models.ForeignKey(User)
    obligee = models.ForeignKey('obligees.Obligee')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    submission_date = models.DateTimeField(auto_now_add=True)
    sender_email = models.EmailField(max_length=255)
    recepient_email = models.EmailField(max_length=255)
    def __unicode__(self):
        return unicode(repr((self.applicant, self.obligee, str(self.submission_date))), "utf-8")

