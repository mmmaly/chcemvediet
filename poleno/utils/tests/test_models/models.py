# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models

from poleno.utils.models import FieldChoices, QuerySet

class MockModelQuerySet(QuerySet):
    def black(self):
        return self.filter(type=MockModel.TYPES.BLACK)
    def red(self):
        return self.filter(type=MockModel.TYPES.RGB.RED)
    def rgb(self):
        return self.filter(type__in=[MockModel.TYPES.RGB.RED, MockModel.TYPES.RGB.GREEN, MockModel.TYPES.RGB.BLUE])
    def _private(self):
        pass

class MockModel(models.Model):
    name = models.CharField(blank=True, max_length=255)

    TYPES = FieldChoices(
            (u'BLACK', 1, u'Black'),
            (u'WHITE', 2, u'White'),
            (u'RGB', 3, (
                (u'RED', 4, u'Red'),
                (u'GREEN', 5, u'Green'),
                (u'BLUE', 6, u'Blue'),
                )),
            )
    type = models.SmallIntegerField(choices=TYPES._choices, default=TYPES.BLACK)

    objects = MockModelQuerySet.as_manager()

    class Meta:
        app_label = u'utils'
