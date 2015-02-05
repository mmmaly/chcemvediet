# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    zip = models.CharField(max_length=10)

    def __unicode__(self):
        return u'%s' % self.pk

@receiver(post_save, sender=User)
def create_profile_on_user_post_save(sender, **kwargs):
    user = kwargs[u'instance']
    if kwargs[u'created']:
        profile = Profile(user=user)
        profile.save()

