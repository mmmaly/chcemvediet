# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseNotFound
from django.shortcuts import render

from poleno.mail.models import Message
from poleno.utils.views import require_ajax, login_required
from poleno.utils.date import local_date
from chcemvediet.apps.inforequests import forms
from chcemvediet.apps.inforequests.models import Inforequest, InforequestEmail, Branch, Action

from .shortcuts import render_form, json_form, json_success


@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@transaction.atomic
@login_required(raise_exception=True)
def _decide_email(request, inforequest_pk, email_pk, form_class):
    assert form_class.action_type in Action.OBLIGEE_EMAIL_ACTION_TYPES

    inforequest = (Inforequest.objects
            .not_closed()
            .owned_by(request.user)
            .prefetch_related(Inforequest.prefetch_branches(None, Branch.objects.select_related(u'historicalobligee')))
            .prefetch_related(Branch.prefetch_last_action(u'branches'))
            .get_or_404(pk=inforequest_pk)
            )
    inforequestemail = (inforequest.inforequestemail_set
            .undecided()
            .oldest()
            .select_related(u'email')
            .get_or_404()
            )
    email = inforequestemail.email

    if email.pk != Message._meta.pk.to_python(email_pk):
        return HttpResponseNotFound()
    if not inforequest.can_add_action(form_class.action_type):
        return HttpResponseNotFound()

    if request.method != u'POST':
        form = form_class(inforequest=inforequest)
        return render_form(request, form, inforequest=inforequest, email=email)

    form = form_class(request.POST, inforequest=inforequest)
    if not form.is_valid():
        return json_form(request, form, inforequest=inforequest, email=email)

    action = Action(
            subject=email.subject,
            content=email.text,
            effective_date=local_date(email.processed),
            email=email,
            type=form_class.action_type,
            )
    form.save(action)
    action.save()

    for attch in email.attachments:
        attachment = attch.clone(action)
        attachment.save()

    inforequestemail.type = InforequestEmail.TYPES.OBLIGEE_ACTION
    inforequestemail.save(update_fields=[u'type'])

    # The inforequest was changed, we need to refetch it
    inforequest = Inforequest.objects.prefetch_detail().get(pk=inforequest.pk)
    return json_success(request, inforequest, action)

def decide_email_confirmation(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, forms.ConfirmationEmailForm)

def decide_email_extension(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, forms.ExtensionEmailForm)

def decide_email_advancement(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, forms.AdvancementEmailForm)

def decide_email_clarification_request(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, forms.ClarificationRequestEmailForm)

def decide_email_disclosure(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, forms.DisclosureEmailForm)

def decide_email_refusal(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, forms.RefusalEmailForm)


@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@transaction.atomic
@login_required(raise_exception=True)
def decide_email_unrelated(request, inforequest_pk, email_pk):
    inforequest = (Inforequest.objects
            .not_closed()
            .owned_by(request.user)
            .get_or_404(pk=inforequest_pk)
            )
    inforequestemail = (inforequest.inforequestemail_set
            .undecided()
            .oldest()
            .select_related(u'email')
            .get_or_404()
            )
    email = inforequestemail.email

    if email.pk != Message._meta.pk.to_python(email_pk):
        return HttpResponseNotFound()

    if request.method != u'POST':
        template = u'inforequests/modals/unrelated_email.html'
        return render(request, template, dict(inforequest=inforequest, email=email))

    inforequestemail.type = InforequestEmail.TYPES.UNRELATED
    inforequestemail.save(update_fields=[u'type'])

    # The inforequest was changed, we need to refetch it
    inforequest = Inforequest.objects.prefetch_detail().get(pk=inforequest.pk)
    return json_success(request, inforequest)


@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@transaction.atomic
@login_required(raise_exception=True)
def decide_email_unknown(request, inforequest_pk, email_pk):
    inforequest = (Inforequest.objects
            .not_closed()
            .owned_by(request.user)
            .get_or_404(pk=inforequest_pk)
            )
    inforequestemail = (inforequest.inforequestemail_set
            .undecided()
            .oldest()
            .select_related(u'email')
            .get_or_404()
            )
    email = inforequestemail.email

    if email.pk != Message._meta.pk.to_python(email_pk):
        return HttpResponseNotFound()

    if request.method != u'POST':
        template = u'inforequests/modals/unknown_email.html'
        return render(request, template, dict(inforequest=inforequest, email=email))

    inforequestemail.type = InforequestEmail.TYPES.UNKNOWN
    inforequestemail.save(update_fields=[u'type'])

    # The inforequest was changed, we need to refetch it
    inforequest = Inforequest.objects.prefetch_detail().get(pk=inforequest.pk)
    return json_success(request, inforequest)
