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

from models import Application, ApplicationDraft, Act
from forms import ApplicationForm, ApplicationFormDraft

@login_required
@require_http_methods(['HEAD', 'GET'])
def index(request):
    application_list = Application.objects.filter(applicant=request.user)
    draft_list = ApplicationDraft.objects.filter(applicant=request.user)
    return render(request, 'applications/index.html', {
        'application_list': application_list,
        'draft_list': draft_list,
        })

@verified_email_required
@require_http_methods(['HEAD', 'GET', 'POST'])
def create(request, draft_id=None):
    draft = get_object_or_404(ApplicationDraft, id=draft_id, applicant=request.user) if draft_id else None

    if request.method == 'POST':
        if 'save' in request.POST:
            form = ApplicationFormDraft(request.POST)
            if form.is_valid():
                if not draft:
                    draft = ApplicationDraft(applicant=request.user)
                form.save(draft)
                return HttpResponseRedirect(reverse('applications:index'))

        elif 'submit' in request.POST:
            form = ApplicationForm(request.POST)
            if form.is_valid():
                application = Application(applicant=request.user)
                form.save(application)

                act = Act()
                act.type = act.REQUEST
                act.application = application
                act.subject = form.cleaned_data['subject']
                act.content = form.cleaned_data['content']
                act.save()

                sender_full = mail_address_with_name(application.applicant_name, application.unique_email)
                send_mail(act.subject, act.content, sender_full, [application.obligee.email])

                if draft:
                    draft.delete()
                return HttpResponseRedirect(reverse('applications:detail', args=(application.id,)))

        else:
            raise PermissionDenied

    else:
        if draft:
            form = ApplicationFormDraft(initial={
                'obligee': draft.obligee.name if draft.obligee else '',
                'subject': draft.subject,
                'content': draft.content,
                })
        else:
            form = ApplicationFormDraft()

    if request.method == 'POST':
        try:
            obligee = Obligee.objects.filter(name=request.POST['obligee'])[0]
        except:
            obligee = None
    else:
        obligee = draft.obligee if draft else None

    return render(request, 'applications/create.html', {
        'form': form,
        'obligee': obligee,
        })

@login_required
@require_http_methods(['HEAD', 'GET'])
def detail(request, application_id):
    application = get_object_or_404(Application, id=application_id, applicant=request.user)
    return render(request, 'applications/detail.html', {
        'application': application,
        })

@login_required
@require_http_methods(['POST'])
def delete_draft(request, draft_id):
    draft = get_object_or_404(ApplicationDraft, id=draft_id, applicant=request.user)
    draft.delete()
    return HttpResponseRedirect(reverse('applications:index'))

