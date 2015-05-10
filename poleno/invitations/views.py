# vim: expandtab
# -*- coding: utf-8 -*-
from django.views.decorators.http import require_http_methods
from django.shortcuts import redirect

from allauth.account.adapter import get_adapter

from .models import Invitation

@require_http_methods([u'HEAD', u'GET'])
def accept(request, key):
    invitation = Invitation.objects.pending().get_or_404(key=key.lower())
    request.session[u'invitations_invitation_key'] = invitation.key
    get_adapter().stash_verified_email(request, invitation.email)
    return redirect(u'account_signup')
