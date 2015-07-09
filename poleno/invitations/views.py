# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from allauth.account.adapter import get_adapter

from poleno.utils.messages import render_message

from . import forms, UserMayNotInvite
from .models import Invitation

@require_http_methods([u'HEAD', u'GET', u'POST'])
@login_required
def invite(request):
    if not request.user.invitationsupply.can_use_invitations:
        return HttpResponseNotFound()

    if request.method == u'POST':
        form = forms.InviteForm(request.POST)
        if form.is_valid():
            try:
                email = form.cleaned_data[u'email']
                request.user.invitationsupply.invite(email)
            except UserMayNotInvite:
                render_message(request, messages.ERROR, u'invitations/messages/depleted.txt')
            else:
                render_message(request, messages.SUCCESS, u'invitations/messages/invited.txt', {u'email': email})
            return HttpResponseRedirect(reverse(u'invitations:invite'))

    else:
        form = forms.InviteForm()

    return render(request, u'invitations/invite.html', {
            u'form': form,
        })

@require_http_methods([u'HEAD', u'GET'])
def accept(request, key):
    invitation = Invitation.objects.pending().get_or_404(key=key.lower())
    request.session[u'invitations_invitation_key'] = invitation.key
    get_adapter().stash_verified_email(request, invitation.email)
    return redirect(u'account_signup')
