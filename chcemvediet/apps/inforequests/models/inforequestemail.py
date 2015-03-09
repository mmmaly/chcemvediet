# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from aggregate_if import Count

from poleno import datacheck
from poleno.mail.models import Message
from poleno.utils.models import FieldChoices, QuerySet
from poleno.utils.misc import squeeze

class InforequestEmailQuerySet(QuerySet):
    def undecided(self):
        return self.filter(type=InforequestEmail.TYPES.UNDECIDED)
    def order_by_pk(self):
        return self.order_by(u'pk')
    def order_by_email(self):
        return self.order_by(u'email__processed', u'email__pk', u'pk')
    def oldest(self):
        return self.order_by_email()[:1]
    def newest(self):
        return self.order_by_email().reverse()[:1]

class InforequestEmail(models.Model):
    # May NOT be NULL; m2m ends; Indexes are prefixes of [inforequest, email] and
    # [email, inforequest] indexes, respectively, see index_together
    inforequest = models.ForeignKey(u'Inforequest', db_index=False)
    email = models.ForeignKey(u'mail.Message', db_index=False)

    # May NOT be NULL
    TYPES = FieldChoices(
            # For outbound messages
            (u'APPLICANT_ACTION', 1, _(u'inforequests:InforequestEmail:type:APPLICANT_ACTION')),
            # For inbound messages
            (u'OBLIGEE_ACTION',   2, _(u'inforequests:InforequestEmail:type:OBLIGEE_ACTION')),
            (u'UNDECIDED',        3, _(u'inforequests:InforequestEmail:type:UNDECIDED')),
            (u'UNRELATED',        4, _(u'inforequests:InforequestEmail:type:UNRELATED')),
            (u'UNKNOWN',          5, _(u'inforequests:InforequestEmail:type:UNKNOWN')),
            )
    type = models.SmallIntegerField(choices=TYPES._choices,
            help_text=squeeze(u"""
                "Applicant Action": the email represents an applicant action;
                "Obligee Action": the email represents an obligee action;
                "Undecided": The email is waiting for applicant decision;
                "Unrelated": Marked as an unrelated email;
                "Unknown": Marked as an email the applicant didn't know how to decide.
                It must be "Applicant Action" for outbound mesages or one of the remaining values
                for inbound messages.
                """
                ))

    # Backward relations added to other models:
    #
    #  -- Inforequest.inforequestemail_set
    #
    #  -- Message.inforequestemail_set

    objects = InforequestEmailQuerySet.as_manager()

    class Meta:
        index_together = [
                [u'email', u'inforequest'],
                [u'inforequest', u'email'],
                [u'type', u'inforequest'],
                ]

    def __unicode__(self):
        return u'%s' % self.pk

    @classmethod
    def datacheck(cls, superficial=False):
        u"""
        Checks that every ``Message`` has exactly one ``InforequestEmail`` relation to
        ``Inforequest``.
        """
        emails = (Message.objects
                .annotate(Count(u'inforequest'))
                .filter(inforequest__count__gt=1)
                )

        if superficial:
            emails = emails[:5+1]
        issues = [u'%r is assigned to %d inforequests' % (m, m.inforequest__count) for m in emails]
        if superficial and issues:
            if len(issues) > 5:
                issues[-1] = u'More messages are assigned to multiple inforequests'
            issues = [u'; '.join(issues)]
        for issue in issues:
            yield datacheck.Error(issue + u'.')
