# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion
import poleno.utils.forms


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalObligee',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('name', models.CharField(max_length=255)),
                ('street', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=255)),
                ('zip', models.CharField(max_length=10)),
                ('emails', models.CharField(help_text='Comma separated list of e-mails. E.g. &#39;John &lt;john@example.com&gt;, another@example.com, &quot;Smith, Jane&quot; &lt;jane.smith@example.com&gt;&#39;', max_length=1024, validators=[poleno.utils.forms.validate_comma_separated_emails])),
                ('slug', models.SlugField(help_text='Slug for full-text search. Automaticly computed whenever creating a new object or changing its name. Any user defined value is replaced.', max_length=255, db_index=False)),
                ('status', models.SmallIntegerField(help_text='"Pending" for obligees that exist and accept inforequests; "Dissolved" for obligees that do not exist any more and no further inforequests may be submitted to them.', choices=[(1, 'Pending'), (2, 'Dissolved')])),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('history_user', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical obligee',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Obligee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('street', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=255)),
                ('zip', models.CharField(max_length=10)),
                ('emails', models.CharField(help_text='Comma separated list of e-mails. E.g. &#39;John &lt;john@example.com&gt;, another@example.com, &quot;Smith, Jane&quot; &lt;jane.smith@example.com&gt;&#39;', max_length=1024, validators=[poleno.utils.forms.validate_comma_separated_emails])),
                ('slug', models.SlugField(help_text='Slug for full-text search. Automaticly computed whenever creating a new object or changing its name. Any user defined value is replaced.', max_length=255, db_index=False)),
                ('status', models.SmallIntegerField(help_text='"Pending" for obligees that exist and accept inforequests; "Dissolved" for obligees that do not exist any more and no further inforequests may be submitted to them.', choices=[(1, 'Pending'), (2, 'Dissolved')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='obligee',
            index_together=set([('name', 'id')]),
        ),
    ]
