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

from models import Inforequest, InforequestDraft, Action, ReceivedEmail
from forms import InforequestForm, InforequestDraftForm

@login_required
@require_http_methods([u'HEAD', u'GET'])
def index(request):
    inforequest_list = Inforequest.objects.all().owned_by(request.user)
    draft_list = InforequestDraft.objects.owned_by(request.user)
    return render(request, u'inforequests/index.html', {
        u'inforequest_list': inforequest_list,
        u'draft_list': draft_list,
        })

@verified_email_required
@require_http_methods([u'HEAD', u'GET', u'POST'])
def create(request, draft_id=None):
    draft = InforequestDraft.objects.owned_by(request.user).get_or_404(pk=draft_id) if draft_id else None

    if request.method == u'POST':
        if u'save' in request.POST:
            form = InforequestDraftForm(request.POST)
            if form.is_valid():
                if not draft:
                    draft = InforequestDraft(applicant=request.user)
                form.save(draft)
                return HttpResponseRedirect(reverse(u'inforequests:index'))

        elif u'submit' in request.POST:
            form = InforequestForm(request.POST)
            if form.is_valid():
                inforequest = Inforequest(
                        applicant=request.user,
                        applicant_name=request.user.get_full_name(),
                        applicant_street=request.user.profile.street,
                        applicant_city=request.user.profile.city,
                        applicant_zip=request.user.profile.zip,
                        )
                form.save(inforequest)

                action = Action(
                        history=inforequest.history,
                        type=Action.TYPES.REQUEST,
                        subject=form.cleaned_data[u'subject'],
                        content=form.cleaned_data[u'content'],
                        effective_date=inforequest.submission_date,
                        )
                action.save()

                sender_full = mail_address_with_name(inforequest.applicant_name, inforequest.unique_email)
                send_mail(action.subject, action.content, sender_full, [inforequest.history.obligee.email])

                if draft:
                    draft.delete()
                return HttpResponseRedirect(reverse(u'inforequests:detail', args=(inforequest.id,)))

        else:
            raise PermissionDenied

    else:
        if draft:
            form = InforequestDraftForm(initial={
                u'obligee': draft.obligee.name if draft.obligee else u'',
                u'subject': draft.subject,
                u'content': draft.content,
                })
        else:
            form = InforequestDraftForm()

    if request.method == u'POST':
        try:
            obligee = Obligee.objects.filter(name=request.POST[u'obligee']).first()
        except:
            obligee = None
    else:
        obligee = draft.obligee if draft else None

    return render(request, u'inforequests/create.html', {
        u'form': form,
        u'obligee': obligee,
        })

@login_required
@require_http_methods([u'HEAD', u'GET'])
def detail(request, inforequest_id):
    inforequest = Inforequest.objects.owned_by(request.user).get_or_404(pk=inforequest_id)
    return render(request, u'inforequests/detail.html', {
        u'inforequest': inforequest,
        })

@login_required
@require_http_methods([u'POST'])
def delete_draft(request, draft_id):
    draft = InforequestDraft.objects.owned_by(request.user).get_or_404(pk=draft_id)
    draft.delete()
    return HttpResponseRedirect(reverse(u'inforequests:index'))

@login_required
@require_http_methods([u'POST'])
def decide_email(request, inforequest_id, receivedemail_id):
    inforequest = Inforequest.objects.owned_by(request.user).get_or_404(pk=inforequest_id)
    receivedemail = inforequest.receivedemail_set.undecided().get_or_404(pk=receivedemail_id)

    # We don't check whether ``receivedemail`` is the oldest ``inforequest`` undecided e-mail or
    # not. Although the frontend forces the user to decide the e-mails in the order they were
    # received, it is not a mistake to decide them in any other order. In the future we may even
    # add an advanced frontend to allow the user to decide the e-mails in any order, but to keep
    # the frontend simple, we don't do it now.

    operation = request.POST[u'operation'] if u'operation' in request.POST else None
    anchor = u'#undecided'

    if (operation == u'unrelated'):
        receivedemail.status = receivedemail.STATUSES.UNRELATED
        receivedemail.save()

    elif (operation == u'unknown'):
        receivedemail.status = receivedemail.STATUSES.UNKNOWN
        receivedemail.save()

    elif (operation == u'confirmation'):
        action = Action(
                history=inforequest.history,
                type=Action.TYPES.CONFIRMATION,
                subject=receivedemail.raw_email.subject,
                content=receivedemail.raw_email.text,
                effective_date=receivedemail.raw_email.processed,
                )
        action.save()
        receivedemail.status = receivedemail.STATUSES.OBLIGEE_ACTION
        receivedemail.save()
        anchor = u'#action-%d' % action.id

    elif (operation == u'extension'):
        action = Action(
                history=inforequest.history,
                type=Action.TYPES.EXTENSION,
                subject=receivedemail.raw_email.subject,
                content=receivedemail.raw_email.text,
                effective_date=receivedemail.raw_email.processed,
                )
        action.save()
        receivedemail.status = receivedemail.STATUSES.OBLIGEE_ACTION
        receivedemail.save()
        anchor = u'#action-%d' % action.id

    elif (operation == u'clarification-request'):
        action = Action(
                history=inforequest.history,
                type=Action.TYPES.CLARIFICATION_REQUEST,
                subject=receivedemail.raw_email.subject,
                content=receivedemail.raw_email.text,
                effective_date=receivedemail.raw_email.processed,
                )
        action.save()
        receivedemail.status = receivedemail.STATUSES.OBLIGEE_ACTION
        receivedemail.save()
        anchor = u'#action-%d' % action.id

    else:
        raise PermissionDenied

    return HttpResponseRedirect(reverse(u'inforequests:detail', args=(inforequest.id,)) + anchor)
