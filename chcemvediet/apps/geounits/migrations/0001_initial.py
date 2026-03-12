# vim: expandtab
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


def dummy_iczsj_forward(apps, schema_editor):
    Region = apps.get_model(u'geounits', u'Region')
    region = Region(id=u'1', name=u'dummy', slug=u'dummy')
    region.save()

    District = apps.get_model(u'geounits', u'District')
    district = District(id=u'1', name=u'dummy', slug=u'dummy', region=region)
    district.save()

    Municipality = apps.get_model(u'geounits', u'Municipality')
    municipality = Municipality(id=u'1', name=u'dummy', slug=u'dummy',
            district=district, region=region)
    municipality.save()

    Neighbourhood = apps.get_model(u'geounits', u'Neighbourhood')
    neighbourhood = Neighbourhood(id=u'1', name=u'dummy',
            municipality=municipality, district=district, region=region)
    neighbourhood.save()

def dummy_iczsj_backward(apps, schema_editor):
    Neighbourhood = apps.get_model(u'geounits', u'Neighbourhood')
    Neighbourhood.objects.filter(name=u'dummy').delete()

    Municipality = apps.get_model(u'geounits', u'Municipality')
    Municipality.objects.filter(name=u'dummy').delete()

    District = apps.get_model(u'geounits', u'District')
    District.objects.filter(name=u'dummy').delete()

    Region = apps.get_model(u'geounits', u'Region')
    Region.objects.filter(name=u'dummy').delete()

class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='District',
            fields=[
                ('id', models.CharField(help_text='District primary key. Example: "SK031B" (REGPJ.LSUJ1)', max_length=32, serialize=False, primary_key=True)),
                ('name', models.CharField(help_text='Unique human readable district name. (REGPJ.NAZOKS, REGPJ.NAZLSUJ1)', unique=True, max_length=255)),
                ('slug', models.SlugField(help_text='Unique slug to identify the district used in urls. Automaticly computed from the district name. May not be changed manually.', unique=True, max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Municipality',
            fields=[
                ('id', models.CharField(help_text='District primary key. Example: "SK031B518042" (REGPJ.LSUJ2)', max_length=32, serialize=False, primary_key=True)),
                ('name', models.CharField(help_text='Unique human readable municipality name. If municipality name is ambiguous it should be amedned with its district name. (REGPJ.NAZZUJ, REGPJ.NAZLSUJ2)', unique=True, max_length=255)),
                ('slug', models.SlugField(help_text='Unique slug to identify the municipality used in urls. Automaticly computed from the municipality name. May not be changed manually.', unique=True, max_length=255)),
                ('district', models.ForeignKey(help_text='District the municipality belongs to.', to='geounits.District', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Neighbourhood',
            fields=[
                ('id', models.CharField(help_text='Neighbourhood primary key. Example: "26289" (REGPJ.ICZSJ)', max_length=32, serialize=False, primary_key=True)),
                ('name', models.CharField(help_text='Human readable neighbourhood name. The name is unique within its municipality. (REGPJ.NAZZSJ)', max_length=255)),
                ('slug', models.SlugField(help_text='Slug to identify the neighbourhood used in urls. The slug is unique within the municipality. Automaticly computed from the neighbourhood name. May not be changed manually.', max_length=255)),
                ('district', models.ForeignKey(help_text='District the neighbourhood belongs to.', to='geounits.District', on_delete=django.db.models.deletion.CASCADE)),
                ('municipality', models.ForeignKey(help_text='Municipality the neighbourhood belongs to.', to='geounits.Municipality', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.CharField(help_text='Region primary key. Example: "SK031" (REGPJ.RSUJ3)', max_length=32, serialize=False, primary_key=True)),
                ('name', models.CharField(help_text='Unique human readable region name. (REGPJ.NAZKRJ, REGPJ.NAZRSUJ3)', unique=True, max_length=255)),
                ('slug', models.SlugField(help_text='Unique slug to identify the region used in urls. Automaticly computed from the region name. May not be changed manually.', unique=True, max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='neighbourhood',
            name='region',
            field=models.ForeignKey(help_text='Region the neighbourhood belongs to.', to='geounits.Region', on_delete=django.db.models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='neighbourhood',
            unique_together=set([('name', 'municipality'), ('slug', 'municipality')]),
        ),
        migrations.AddField(
            model_name='municipality',
            name='region',
            field=models.ForeignKey(help_text='Region the municipality belongs to.', to='geounits.Region', on_delete=django.db.models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='district',
            name='region',
            field=models.ForeignKey(help_text='Region the district belongs to.', to='geounits.Region', on_delete=django.db.models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.RunPython(dummy_iczsj_forward, dummy_iczsj_backward),
    ]
