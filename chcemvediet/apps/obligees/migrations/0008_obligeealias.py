# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('obligees', '0007_obligee_tags_groups'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObligeeAlias',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Unique human readable obligee alias if the obligee has multiple common names.', unique=True, max_length=255, db_index=True)),
                ('slug', models.SlugField(help_text='Unique slug to identify the obligee alias used in urls. Automaticly computed from the obligee name. May not be changed manually.', unique=True, max_length=255)),
                ('description', models.TextField(help_text='Obligee alias description.', blank=True)),
                ('notes', models.TextField(help_text='Internal freetext notes. Not shown to the user.', blank=True)),
                ('obligee', models.ForeignKey(help_text='Obligee of which this is alias.', to='obligees.Obligee', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='historicalobligee',
            name='name',
            field=models.CharField(help_text='Unique human readable obligee name. If official obligee name is ambiguous, it should be made more specific.', max_length=255, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='obligee',
            name='name',
            field=models.CharField(help_text='Unique human readable obligee name. If official obligee name is ambiguous, it should be made more specific.', unique=True, max_length=255, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='obligeegroup',
            name='key',
            field=models.CharField(help_text='Unique key to identify the group. The key is a path of slash separated words each of which represents a parent group. Every word in the path should be a nonempty string and should only contain alphanumeric characters, underscores and hyphens.', unique=True, max_length=255, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='obligeegroup',
            name='name',
            field=models.CharField(help_text='Unique human readable group name.', unique=True, max_length=255, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='obligeetag',
            name='name',
            field=models.CharField(help_text='Unique human readable tag name.', unique=True, max_length=255, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='obligee',
            index_together=set([]),
        ),
        migrations.AlterIndexTogether(
            name='obligeegroup',
            index_together=set([]),
        ),
        migrations.AlterIndexTogether(
            name='obligeetag',
            index_together=set([]),
        ),
    ]
