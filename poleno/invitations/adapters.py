# vim: expandtab
# -*- coding: utf-8 -*-
from allauth.account.adapter import DefaultAccountAdapter

from poleno.utils.date import utc_now
from poleno.utils.models import after_saved

from . import app_settings
from .models import Invitation

class InvitationsAdapter(DefaultAccountAdapter):

    def _get_invitation(self, request):
            key = request.session.get(u'invitations_invitation_key')
            if not key:
                return None
            try:
                return Invitation.objects.pending().get(key=key)
            except Invitation.DoesNotExist:
                return None

    def is_open_for_signup(self, request):
        if self._get_invitation(request):
            return True
        return not app_settings.INVITATION_ONLY

    def save_user(self, request, user, form, commit=True):

        @after_saved(user)
        def deferred(user):
            invitation = self._get_invitation(request)
            if invitation:
                invitation.accepted = utc_now()
                invitation.invitee = user
                invitation.save()
            request.session[u'invitations_invitation_key'] = None

        return super(InvitationsAdapter, self).save_user(request, user, form, commit)
