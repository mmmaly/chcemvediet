# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import gettext_lazy as _

from poleno.utils.date import utc_now
from poleno.utils.misc import FormatMixin
from poleno.utils.models import FieldChoices, QuerySet


class FeedbackQuerySet(QuerySet):
    def order_by_pk(self):
        return self.order_by(u'pk')


class Feedback(FormatMixin, models.Model):
    # NOT NULL
    inforequest = models.ForeignKey(u'Inforequest', on_delete=models.CASCADE, db_index=False)

    # May be empty
    content = models.TextField(blank=True)

    # NOT NULL
    created = models.DateTimeField(default=utc_now)

    RATING_LEVELS = FieldChoices(
        (u'ATROCIOUS',   0, _(u'inforequests:Feedback:rating:ATROCIOUS')),
        (u'VERY POOR',   1, _(u'inforequests:Feedback:rating:VERY_POOR')),
        (u'POOR',        2, _(u'inforequests:Feedback:rating:POOR')),
        (u'MEDIOCRE',    3, _(u'inforequests:Feedback:rating:MEDIOCRE')),
        (u'GOOD',        4, _(u'inforequests:Feedback:rating:GOOD')),
        (u'VERY GOOD',   5, _(u'inforequests:Feedback:rating:VERY_GOOD')),
        (u'EXCELLENT',   6, _(u'inforequests:Feedback:rating:EXCELLENT')),
    )

    rating = models.SmallIntegerField(choices=RATING_LEVELS._choices, blank=True, null=True, default=None)

    # Indexes:
    #  -- inforequest: ForeignKey
    #  -- created, id: index_together

    objects = FeedbackQuerySet.as_manager()

    class Meta:
        verbose_name_plural = u'Feedback'
        index_together = [
            [u'created', u'id'],
        ]
