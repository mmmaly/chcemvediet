# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mail', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(help_text='Invited email address. The address does not have to be unique as one person may be invited by multiple users. However, only people that are not registered yet should be invited.', max_length=255)),
                ('key', models.CharField(help_text="Unique key to identify the invitation. It's used in the invitation URL.", unique=True, max_length=255, db_index=True)),
                ('created', models.DateTimeField(help_text='Date and time the invitation was created and sent.')),
                ('valid_to', models.DateTimeField(help_text='Date and time the invitation is valid to.')),
                ('accepted', models.DateTimeField(help_text='Date and time the invitation was accepted and the invitee registered himself.', null=True, blank=True)),
                ('invitee', models.OneToOneField(related_name='invited_with', null=True, blank=True, to=settings.AUTH_USER_MODEL, help_text='NULL for pending and expired invitations and the user who was invited after he accepts the invitation and registers himself.')),
                ('invitor', models.ForeignKey(help_text='The user who sent the invitation.', to=settings.AUTH_USER_MODEL)),
                ('message', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='mail.Message', help_text='The e-mail message the invitation was sent by. NULL if the invitation was sent manually by the admin without sending any e-mail.')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
