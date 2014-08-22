# vim: expandtab
# -*- coding: utf-8 -*-
import re

from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from allauth.account.decorators import verified_email_required

from poleno.utils.mail import mail_address_with_name
from chcemvediet.apps.obligees.models import Obligee

from models import InfoRequest, InfoRequestDraft, Action
from forms import InfoRequestForm, InfoRequestDraftForm

@login_required
@require_http_methods([u'HEAD', u'GET'])
def index(request):
    info_request_list = InfoRequest.objects.filter(applicant=request.user)
    draft_list = InfoRequestDraft.objects.filter(applicant=request.user)
    return render(request, u'info_requests/index.html', {
        u'info_request_list': info_request_list,
        u'draft_list': draft_list,
        })

@verified_email_required
@require_http_methods([u'HEAD', u'GET', u'POST'])
def create(request, draft_id=None):
    draft = get_object_or_404(InfoRequestDraft, pk=draft_id, applicant=request.user) if draft_id else None

    if request.method == u'POST':
        if u'save' in request.POST:
            form = InfoRequestDraftForm(request.POST)
            if form.is_valid():
                if not draft:
                    draft = InfoRequestDraft(applicant=request.user)
                form.save(draft)
                return HttpResponseRedirect(reverse(u'info_requests:index'))

        elif u'submit' in request.POST:
            form = InfoRequestForm(request.POST)
            if form.is_valid():
                info_request = InfoRequest(
                        applicant=request.user,
                        applicant_name=request.user.get_full_name(),
                        applicant_street=request.user.profile.street,
                        applicant_city=request.user.profile.city,
                        applicant_zip=request.user.profile.zip,
                        )
                form.save(info_request)

                action = Action(
                        type=Action.REQUEST,
                        history=info_request.history,
                        subject=form.cleaned_data[u'subject'],
                        content=form.cleaned_data[u'content'],
                        )
                action.save()

                sender_full = mail_address_with_name(info_request.applicant_name, info_request.unique_email)
                send_mail(action.subject, action.content, sender_full, [info_request.history.obligee.email])

                if draft:
                    draft.delete()
                return HttpResponseRedirect(reverse(u'info_requests:detail', args=(info_request.id,)))

        else:
            raise PermissionDenied

    else:
        if draft:
            form = InfoRequestDraftForm(initial={
                u'obligee': draft.obligee.name if draft.obligee else u'',
                u'subject': draft.subject,
                u'content': draft.content,
                })
        else:
            form = InfoRequestDraftForm()

    if request.method == u'POST':
        try:
            obligee = Obligee.objects.filter(name=request.POST[u'obligee'])[0]
        except:
            obligee = None
    else:
        obligee = draft.obligee if draft else None

    return render(request, u'info_requests/create.html', {
        u'form': form,
        u'obligee': obligee,
        })

@login_required
@require_http_methods([u'HEAD', u'GET'])
def detail(request, info_request_id):
    info_request = get_object_or_404(InfoRequest, pk=info_request_id, applicant=request.user)
    return render(request, u'info_requests/detail.html', {
        u'info_request': info_request,
        })

@login_required
@require_http_methods([u'POST'])
def delete_draft(request, draft_id):
    draft = get_object_or_404(InfoRequestDraft, pk=draft_id, applicant=request.user)
    draft.delete()
    return HttpResponseRedirect(reverse(u'info_requests:index'))

