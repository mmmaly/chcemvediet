# vim: expandtab
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

# Creates default InvitationSupply objects for all registered users.

def forward(apps, schema_editor):
    InvitationSupply = apps.get_model(u'invitations', u'InvitationSupply')
    User = apps.get_model(u'auth', u'User')
    for user in User.objects.all():
        invitationsupply = InvitationSupply(user=user)
        invitationsupply.save()

def backward(apps, schema_editor):
    InvitationSupply = apps.get_model(u'invitations', u'InvitationSupply')
    InvitationSupply.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('invitations', '0003_invitationsupply'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
