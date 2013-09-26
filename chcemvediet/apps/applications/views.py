# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.mail import send_mail

from chcemvediet.apps.obligees.models import Obligee, validate_obligee_name
from chcemvediet.apps.applications.models import Application


class ApplicationForm(forms.Form):
    obligee = forms.CharField(
            label=u'Povinná osoba',
            help_text=u'<span id="id_obligee_details">(Vyber povinnú osobu)</span>',
            validators=[validate_obligee_name],
            max_length=255,
            )
    subject = forms.CharField(
            label=u'Vec (subject)',
            initial=u'Žiadosť o informáciu',
            max_length=255,
            )
    message = forms.CharField(
            label=u'Znenie žiadosti',
            widget=forms.Textarea,
            )

@login_required
def create_view(request):
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            obligee_name = form.cleaned_data['obligee']
            obligee = Obligee.objects.filter(name=obligee_name)[0]

            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            sender_mail = 'todo@mail.chcemvediet.sk'
            sender_full = request.user.get_full_name() + ' <' + sender_mail + '>'
            recipient_mail = obligee.email

            application = Application(
                    applicant=request.user,
                    obligee=obligee,
                    subject=subject,
                    message=message,
                    sender_email=sender_mail,
                    recepient_email=recipient_mail,
                    )
            application.save()
            send_mail(subject, message, sender_full, [recipient_mail])
            return HttpResponseRedirect(reverse('applications:detail', args=(application.id,)))
    else:
        form = ApplicationForm()

    return render(request, 'applications/create.html', {
        'form': form,
        })

@login_required
def index_view(request):
    application_list = Application.objects.filter(applicant=request.user)
    return render(request, 'applications/index.html', {
        'application_list': application_list,
        })

@login_required
def detail_view(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    return render(request, 'applications/detail.html', {
        'application': application,
        })

