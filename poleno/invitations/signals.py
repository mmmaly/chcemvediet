# vim: expandtab
# -*- coding: utf-8 -*-
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from .models import InvitationSupply

@receiver(post_save, sender=User)
def create_invitationsupply_on_user_post_save(sender, **kwargs):
    user = kwargs[u'instance']
    if kwargs[u'created']:
        invitationsupply = InvitationSupply(user=user)
        invitationsupply.save()
