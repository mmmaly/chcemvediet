# vim: expandtab
# -*- coding: utf-8 -*-
import string
import datetime

from django.db import models
from django.db.models import F
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.functional import cached_property

from poleno.utils.models import QuerySet, after_saved
from poleno.utils.views import absolute_reverse
from poleno.utils.date import utc_now
from poleno.utils.mail import render_mail
from poleno.utils.misc import squeeze, decorate, random_string

from . import app_settings, UserMayNotInvite

class InvitationQuerySet(QuerySet):
    def accepted(self):
        return self.filter(accepted__isnull=False)
    def expired(self):
        return self.filter(accepted__isnull=True).filter(valid_to__lt=utc_now())
    def pending(self):
        return self.filter(accepted__isnull=True).filter(valid_to__gte=utc_now())

class Invitation(models.Model):
    # May NOT be empty
    email = models.EmailField(max_length=255,
            help_text=squeeze(u"""
                Invited email address. The address does not have to be unique as one person may be
                invited by multiple users. However, only people that are not registered yet should
                be invited.
                """))

    # May NOT be empty; Unique; Automaticly generated in save() when creating a new instance.
    key = models.CharField(max_length=255, unique=True, db_index=True,
            help_text=squeeze(u"""
                Unique key to identify the invitation. It's used in the invitation URL.
                """))

    # May NOT be NULL; Automaticly computed in save() when creating a new object if undefined.
    created = models.DateTimeField(
            help_text=squeeze(u"""
                Date and time the invitation was created and sent.
                """))

    # May NOT be NULL; Automaticly computed in save() when creating a new object if undefined.
    valid_to = models.DateTimeField(
            help_text=squeeze(u"""
                Date and time the invitation is valid to.
                """))

    # May be NULL
    accepted = models.DateTimeField(blank=True, null=True,
            help_text=squeeze(u"""
                Date and time the invitation was accepted and the invitee registered himself. NULL
                if the invitation was not accepted yet.
                """))

    # May NOT be NULL
    invitor = models.ForeignKey(User,
            help_text=squeeze(u"""
                The user who sent the invitation.
                """))

    # May be NULL
    invitee = models.OneToOneField(User, blank=True, null=True, related_name=u'invited_with',
            help_text=squeeze(u"""
                The user who was invited after he accepts the invitation and registers himself.
                NULL for pending and expired invitations.
                """))

    # May be NULL
    message = models.OneToOneField(u'mail.Message', blank=True, null=True, on_delete=models.SET_NULL,
            help_text=squeeze(u"""
                The e-mail message the invitation was sent by. NULL if the invitation was sent
                manually by the admin without sending any e-mail.
                """))

    # Backward relations added to other models:
    #
    #  -- User.invitation_set
    #     May be empty
    #
    #  -- User.invited_with
    #     May raise DoesNotExist
    #
    #  -- Message.invitation
    #     May raise DoesNotExist

    objects = InvitationQuerySet.as_manager()

    class Meta:
        index_together = [
                # [u'key'] -- defined on field
                # [u'invitor'] -- ForeignKey defines index by default
                # [u'invitee'] -- ForeignKey defines index by default
                # [u'message'] -- ForeignKey defines index by default
                ]

    @cached_property
    def is_accepted(self):
        return self.accepted is not None

    @cached_property
    def is_expired(self):
        return not self.is_accepted and self.valid_to < utc_now()

    @cached_property
    def is_pending(self):
        return not self.is_accepted and not self.is_expired

    @cached_property
    def accept_url(self):
        return absolute_reverse(u'invitations:accept', args=[self.key])

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        if self.pk is None: # Creating a new object
            self.key = random_string(64, chars=(string.ascii_lowercase + string.digits))
            if self.created is None:
                self.created = utc_now()
            if self.valid_to is None:
                self.valid_to = self.created + datetime.timedelta(days=app_settings.DEFAULT_VALIDITY)

        super(Invitation, self).save(*args, **kwargs)

    @staticmethod
    def create(email, invitor, validity=None, send_email=True):
        invitation = Invitation(email=email, invitor=invitor)
        if validity is not None:
            invitation.created = utc_now()
            invitation.valid_to = invitation.created + datetime.timedelta(days=validity)

        if send_email:
            @after_saved(invitation)
            def deferred(invitation):
                invitation.send_by_email()

        return invitation

    def send_by_email(self):
        msg = render_mail(u'invitations/mails/invitation',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[self.email],
                dictionary={
                    u'invitation': self,
                    })
        msg.send()

        self.message = msg.instance
        self.save(update_fields=[u'message'])

    def __unicode__(self):
        return u'%s' % self.pk


class InvitationSupplyQuerySet(QuerySet):
    pass

class InvitationSupply(models.Model):
    # May NOT be NULL
    user = models.OneToOneField(User,
            help_text=squeeze(u"""
                The user to whom the invitation supply belongs.
                """))

    # May NOT be NULL
    enabled = models.BooleanField(default=app_settings.NEW_USERS_MAY_INVITE,
            help_text=squeeze(u"""
                Whether the user may send invitations.
                """))

    # May NOT be NULL
    unlimited = models.BooleanField(default=False,
            help_text=squeeze(u"""
                Whether the user may send an unlimited number of invitations.
                """))

    # May NOT be NULL
    supply = models.IntegerField(default=0,
            help_text=squeeze(u"""
                The number of invitations the user may send.
                """))

    # Backward relations added to other models:
    #
    #  -- User.invitationsupply
    #     May raise DoesNotExist

    objects = InvitationSupplyQuerySet.as_manager()

    class Meta:
        verbose_name_plural = u'invitation supplies'
        index_together = [
                # [u'user'] -- ForeignKey defines index by default
                ]

    @cached_property
    def can_use_invitations(self):
        u"""
        Whether the invitation system is enabled for this user.
        """
        return app_settings.USERS_MAY_INVITE and self.enabled

    @cached_property
    def can_invite(self):
        u"""
        Whether the invitation system is enabled for this user and he has at least one invitation
        token available.
        """
        return self.can_use_invitations and (self.unlimited or self.supply > 0)

    def invite(self, email):
        u"""
        Send an invitation and adjust the user token supply. Raises ``UserMayNotInvite`` if the
        user is not allowed to invite or his token supply is depleted.
        """
        if not self.can_invite:
            raise UserMayNotInvite()
        if not self.unlimited:
            self.supply = F(u'supply') - 1
            self.save()
        invitation = Invitation.create(email, self.user)
        invitation.save()

    def add(self, supply):
        u"""
        Increments the user invitation supply by the given number.
        """
        self.supply = F(u'supply') + supply
        self.save()

    def __unicode__(self):
        return u'%s' % self.pk
