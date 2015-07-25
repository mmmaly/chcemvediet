# vim: expandtab
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forward(apps, schema_editor):
    Action = apps.get_model(u'inforequests', u'Action')
    Action.objects.filter(refusal_reason__regex=r'(^|,)-1(,|$)').update(refusal_reason=[])

    ActionDraft = apps.get_model(u'inforequests', u'ActionDraft')
    ActionDraft.objects.filter(refusal_reason__regex=r'(^|,)-1(,|$)').update(refusal_reason=[])

def backward(apps, schema_editor):
    Action = apps.get_model(u'inforequests', u'Action')
    Action.objects.filter(refusal_reason=u'', type__in=[7, 8]).update(refusal_reason=[u'-1'])

    ActionDraft = apps.get_model(u'inforequests', u'ActionDraft')
    ActionDraft.objects.filter(refusal_reason=u'', type__in=[7, 8]).update(refusal_reason=[u'-1'])

class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0006_action_no_reason'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
