# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forward(apps, schema_editor):
    Action = apps.get_model(u'inforequests', u'Action')
    ActionDraft = apps.get_model(u'inforequests', u'ActionDraft')
    for action in Action.objects.all():
        if action.refusal_reason is None:
            action.refusal_reason2 = None
        else:
            action.refusal_reason2 = [u'%s' % action.refusal_reason]
        action.save()
    for draft in ActionDraft.objects.all():
        if draft.refusal_reason is None:
            draft.refusal_reason2 = None
        else:
            draft.refusal_reason2 = [u'%s' % draft.refusal_reason]
        draft.save()

def backward(apps, schema_editor):
    Action = apps.get_model(u'inforequests', u'Action')
    ActionDraft = apps.get_model(u'inforequests', u'ActionDraft')
    for action in Action.objects.all():
        try:
            action.refusal_reason = int(action.refusal_reason2[0])
        except (IndexError, TypeError, ValueError):
            action.refusal_reason = None
        action.save()
    for draft in ActionDraft.objects.all():
        try:
            draft.refusal_reason = int(draft.refusal_reason2[0])
        except (IndexError, TypeError, ValueError):
            draft.refusal_reason = None
        draft.save()

class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0013_auto_20150309_1347'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
