# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from poleno.utils.migrations import AlterIndexTogetherStateOnly
import poleno.utils.forms


class Migration(migrations.Migration):

    dependencies = [
        ('obligees', '0003_obligeegroup'),
        ('obligees', '0003_obligee_name_force_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalobligee',
            name='gender',
            field=models.SmallIntegerField(default=1, help_text='Obligee name grammar gender.', choices=[(1, 'obligees:Obligee:gender:MASCULINE'), (2, 'obligees:Obligee:gender:FEMININE'), (3, 'obligees:Obligee:gender:NEUTER'), (4, 'obligees:Obligee:gender:PLURALE')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalobligee',
            name='ico',
            field=models.CharField(help_text='Legal identification number if known.', max_length=32, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalobligee',
            name='name_accusative',
            field=models.CharField(default='', help_text='Accusative of obligee name.', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalobligee',
            name='name_dative',
            field=models.CharField(default='', help_text='Dative of obligee name.', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalobligee',
            name='name_genitive',
            field=models.CharField(default='', help_text='Genitive of obligee name.', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalobligee',
            name='name_instrumental',
            field=models.CharField(default='', help_text='Instrumental of obligee name.', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalobligee',
            name='name_locative',
            field=models.CharField(default='', help_text='Locative of obligee name.', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalobligee',
            name='notes',
            field=models.TextField(help_text='Internal freetext notes. Not shown to the user.', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalobligee',
            name='official_description',
            field=models.TextField(help_text='Official obligee description.', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalobligee',
            name='official_name',
            field=models.CharField(default='', help_text='Official obligee name.', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalobligee',
            name='simple_description',
            field=models.TextField(help_text='Human readable obligee description.', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='obligee',
            name='gender',
            field=models.SmallIntegerField(default=1, help_text='Obligee name grammar gender.', choices=[(1, 'obligees:Obligee:gender:MASCULINE'), (2, 'obligees:Obligee:gender:FEMININE'), (3, 'obligees:Obligee:gender:NEUTER'), (4, 'obligees:Obligee:gender:PLURALE')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='obligee',
            name='ico',
            field=models.CharField(help_text='Legal identification number if known.', max_length=32, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='obligee',
            name='name_accusative',
            field=models.CharField(default='', help_text='Accusative of obligee name.', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='obligee',
            name='name_dative',
            field=models.CharField(default='', help_text='Dative of obligee name.', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='obligee',
            name='name_genitive',
            field=models.CharField(default='', help_text='Genitive of obligee name.', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='obligee',
            name='name_instrumental',
            field=models.CharField(default='', help_text='Instrumental of obligee name.', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='obligee',
            name='name_locative',
            field=models.CharField(default='', help_text='Locative of obligee name.', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='obligee',
            name='notes',
            field=models.TextField(help_text='Internal freetext notes. Not shown to the user.', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='obligee',
            name='official_description',
            field=models.TextField(help_text='Official obligee description.', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='obligee',
            name='official_name',
            field=models.CharField(default='', help_text='Official obligee name.', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='obligee',
            name='simple_description',
            field=models.TextField(help_text='Human readable obligee description.', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='historicalobligee',
            name='city',
            field=models.CharField(help_text='City part of postal address.', max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='historicalobligee',
            name='emails',
            field=models.CharField(blank=True, help_text='Comma separated list of e-mails. E.g. &#39;John &lt;john@example.com&gt;, another@example.com, &quot;Smith, Jane&quot; &lt;jane.smith@example.com&gt;&#39;. Empty the email address is unknown.', max_length=1024, validators=[poleno.utils.forms.validate_comma_separated_emails]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='historicalobligee',
            name='name',
            field=models.CharField(help_text='Human readable obligee name. If official obligee name is ambiguous, it should be made more specific. There is no unique constrain on this field, because there is one on the slug.', max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='historicalobligee',
            name='slug',
            field=models.SlugField(help_text='Unique slug to identify the obligee used in urls. Automaticly computed from the obligee name. May not be changed manually.', max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='historicalobligee',
            name='street',
            field=models.CharField(help_text='Street and number part of postal address.', max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='historicalobligee',
            name='zip',
            field=models.CharField(help_text='Zip part of postal address.', max_length=10),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='obligee',
            name='city',
            field=models.CharField(help_text='City part of postal address.', max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='obligee',
            name='emails',
            field=models.CharField(blank=True, help_text='Comma separated list of e-mails. E.g. &#39;John &lt;john@example.com&gt;, another@example.com, &quot;Smith, Jane&quot; &lt;jane.smith@example.com&gt;&#39;. Empty the email address is unknown.', max_length=1024, validators=[poleno.utils.forms.validate_comma_separated_emails]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='obligee',
            name='name',
            field=models.CharField(help_text='Human readable obligee name. If official obligee name is ambiguous, it should be made more specific. There is no unique constrain on this field, because there is one on the slug.', max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='obligee',
            name='slug',
            field=models.SlugField(help_text='Unique slug to identify the obligee used in urls. Automaticly computed from the obligee name. May not be changed manually.', unique=True, max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='obligee',
            name='street',
            field=models.CharField(help_text='Street and number part of postal address.', max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='obligee',
            name='zip',
            field=models.CharField(help_text='Zip part of postal address.', max_length=10),
            preserve_default=True,
        ),
        AlterIndexTogetherStateOnly(
            name='obligeegroup',
            index_together=set([('name', 'id')]),
        ),
        AlterIndexTogetherStateOnly(
            name='obligeetag',
            index_together=set([('name', 'id')]),
        ),
    ]
