# vim: expandtab
# -*- coding: utf-8 -*-
import re
import random

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from allauth.account.decorators import verified_email_required

from chcemvediet.apps.obligees.models import Obligee
from chcemvediet.apps.applications.models import Application, ApplicationDraft

import forms

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
            form = forms.ApplicationFormDraft(request.POST)
            if form.is_valid():
                obligee_name = form.cleaned_data['obligee']
                obligee = Obligee.objects.filter(name=obligee_name)[0] if obligee_name else None
                subject = form.cleaned_data['subject']
                content = form.cleaned_data['content']

                if draft:
                    draft.obligee = obligee
                    draft.subject = subject
                    draft.content = content
                else:
                    draft = ApplicationDraft(
                            applicant=request.user,
                            obligee=obligee,
                            subject=subject,
                            content=content,
                            )
                draft.save()

                return HttpResponseRedirect(reverse('applications:index'))

        elif 'submit' in request.POST:
            form = forms.ApplicationForm(request.POST)
            if form.is_valid():
                obligee_name = form.cleaned_data['obligee']
                obligee = Obligee.objects.filter(name=obligee_name)[0]
                subject = form.cleaned_data['subject']
                message = form.cleaned_data['content']
                recipient_mail = obligee.email

                application = Application(
                        applicant=request.user,
                        obligee=obligee,
                        subject=subject,
                        message=message,
                        recepient_email=recipient_mail,
                        )

                # Use unique random sender email address
                length = 2
                while True:
                    sender_mail = _random_email_address('mail.chcemvediet.sk', length)
                    application.sender_email = sender_mail
                    try:
                        application.save()
                    except IntegrityError:
                        length += 1
                        continue
                    break

                # To prevent any unexpected e-mail behaviour, we filter all special characters from
                # e-mail phrase. See: https://www.ietf.org/rfc/rfc0822.txt
                sender_name = request.user.get_full_name()
                sender_name = re.sub(r'[()<>@,;:\\".\[\]\s]+', ' ', sender_name, flags=re.U)
                sender_full = '%s <%s>' % (sender_name, sender_mail)
                send_mail(subject, message, sender_full, [recipient_mail])

                if draft:
                    draft.delete()

                return HttpResponseRedirect(reverse('applications:detail', args=(application.id,)))

        else: # missing operation
            form = forms.ApplicationFormDraft(request.POST)

    else:
        initial = {}
        if draft and draft.obligee:
            initial['obligee'] = draft.obligee.name
        if draft:
            initial['subject'] = draft.subject
            initial['content'] = draft.content
        form = forms.ApplicationFormDraft(initial=initial)

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

def _random_email_address(domain, length):
    """
    Returns a random e-mail address with `domain` for its domain part.

    The local part of the generated e-mail address has form of

    [:vowel:]? ([:consonant:][:vowel:]){length} [:consonant:]?

    where `[:vowel:]` is the set of all vowels `[aeiouy]` and `['consonant']` is the set of
    consonants `[bcdfghjklmnprstvxz]`.
    """
    vowels = 'aeiouy'
    consonants = 'bcdfghjklmnprstvxz'

    res = []
    if random.random() < 0.5:
        res.append(random.choice(vowels))
    for i in range(length):
        res.append(random.choice(consonants))
        res.append(random.choice(vowels))
    if random.random() < 0.5:
        res.append(random.choice(consonants))
    res.append('@')
    res.append(domain)

    return ''.join(res)

@login_required
@require_http_methods(['HEAD', 'GET'])
def detail(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    return render(request, 'applications/detail.html', {
        'application': application,
        })

@login_required
@require_http_methods(['POST'])
def delete_draft(request, draft_id):
    draft = get_object_or_404(ApplicationDraft, id=draft_id, applicant=request.user)
    draft.delete()
    return HttpResponseRedirect(reverse('applications:index'))

