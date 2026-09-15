# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0024_feedback_rating'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedback',
            name='rating',
            field=models.SmallIntegerField(default=None, blank=True, choices=[(0, 'inforequests:Feedback:rating:ATROCIOUS'), (1, 'inforequests:Feedback:rating:VERY_POOR'), (2, 'inforequests:Feedback:rating:POOR'), (3, 'inforequests:Feedback:rating:MEDIOCRE'), (4, 'inforequests:Feedback:rating:GOOD'), (5, 'inforequests:Feedback:rating:VERY_GOOD'), (6, 'inforequests:Feedback:rating:EXCELLENT')]),
            preserve_default=True,
        ),
    ]
