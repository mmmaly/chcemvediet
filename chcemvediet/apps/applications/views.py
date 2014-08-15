# vim: expandtab
# -*- coding: utf-8 -*-
import random

from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.db import IntegrityError
from allauth.account.decorators import verified_email_required

from chcemvediet.apps.obligees.models import Obligee
from chcemvediet.apps.applications.models import Application

import forms

@verified_email_required
def create(request):
    if request.method == 'POST':
        form = forms.ApplicationForm(request.POST)
        if form.is_valid():
            obligee_name = form.cleaned_data['obligee']
            obligee = Obligee.objects.filter(name=obligee_name)[0]

            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
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

            sender_full = '%s <%s>' % (request.user.get_full_name(), sender_mail)
            send_mail(subject, message, sender_full, [recipient_mail])
            return HttpResponseRedirect(reverse('applications:detail', args=(application.id,)))
    else:
        form = forms.ApplicationForm()

    return render(request, 'applications/create.html', {
        'form': form,
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
def index(request):
    application_list = Application.objects.filter(applicant=request.user)
    return render(request, 'applications/index.html', {
        'application_list': application_list,
        })

@login_required
def detail(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    return render(request, 'applications/detail.html', {
        'application': application,
        })

