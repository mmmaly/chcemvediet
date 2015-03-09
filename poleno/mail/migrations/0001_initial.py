# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.SmallIntegerField(choices=[(1, 'Inbound'), (2, 'Outbound')])),
                ('processed', models.DateTimeField(help_text='Date and time the message was sent or received and processed. Leave blank if you want the application to process it.', null=True, blank=True)),
                ('from_name', models.CharField(help_text='Sender full name. For instance setting name to &quot;John Smith&quot; and e-mail to &quot;smith@example.com&quot; will set the sender address to &quot;John Smith &lt;smith@example.com&gt;&quot;.', max_length=255, blank=True)),
                ('from_mail', models.EmailField(help_text='Sender e-mail address, e.g. "smith@example.com".', max_length=255)),
                ('received_for', models.EmailField(help_text="The address we received the massage for. It may, but does not have to be among the message recipients, as the address may have heen bcc-ed to. The address is empty for all outbound messages. It may also be empty for inbound messages if we don't know it, or the used mail transport does not support it.", max_length=255, blank=True)),
                ('subject', models.CharField(max_length=255, blank=True)),
                ('text', models.TextField(help_text='"text/plain" message body alternative.', blank=True)),
                ('html', models.TextField(help_text='"text/html" message body alternative.', blank=True)),
                ('headers', jsonfield.fields.JSONField(default={}, help_text='Dictionary mapping header names to their values, or lists of their values. For outbound messages it contains only extra headers added by the sender. For inbound messages it contains all message headers.', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Recipient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Recipient full name. For instance setting name to &quot;John Smith&quot; and e-mail to &quot;smith@example.com&quot; will send the message to &quot;John Smith &lt;smith@example.com&gt;&quot;.', max_length=255, blank=True)),
                ('mail', models.EmailField(help_text='Recipient e-mail address, e.g. "smith@example.com".', max_length=255)),
                ('type', models.SmallIntegerField(help_text='Recipient type: To, Cc, or Bcc.', choices=[(1, 'To'), (2, 'Cc'), (3, 'Bcc')])),
                ('status', models.SmallIntegerField(help_text='Delivery status for the message recipient. It must be "Inbound" for inbound mesages or one of the remaining statuses for outbound messages.', choices=[(8, 'Inbound'), (1, 'Undefined'), (2, 'Queued'), (3, 'Rejected'), (4, 'Invalid'), (5, 'Sent'), (6, 'Delivered'), (7, 'Opened')])),
                ('status_details', models.CharField(help_text='Unspecific delivery status details set by e-mail transport. Leave blank if not sure.', max_length=255, blank=True)),
                ('remote_id', models.CharField(help_text='Recipient reference ID set by e-mail transport. Leave blank if not sure.', max_length=255, db_index=True, blank=True)),
                ('message', models.ForeignKey(to='mail.Message')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='message',
            index_together=set([('processed', 'id')]),
        ),
    ]
