# vim: expandtab
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def string_to_json(apps, schema_editor):
    InforequestDraft = apps.get_model(u'inforequests', u'InforequestDraft')
    for draft in InforequestDraft.objects.all():
        draft.content_tmp = [draft.content]
        draft.save()

def json_to_string(apps, schema_editor):
    InforequestDraft = apps.get_model(u'inforequests', u'InforequestDraft')
    for draft in InforequestDraft.objects.all():
        try:
            draft.content = draft.content_tmp[0]
        except (KeyError, TypeError, IndexError):
            draft.content = u''
        draft.save()

class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0004_inforequestdraft_content_tmp'),
    ]

    operations = [
        migrations.RunPython(string_to_json, json_to_string),
    ]
