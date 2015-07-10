# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseNotFound, JsonResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.shortcuts import render

from poleno.mail.models import Message
from poleno.utils.views import require_ajax, login_required
from poleno.utils.date import local_date
from chcemvediet.apps.inforequests import forms
from chcemvediet.apps.inforequests.models import Inforequest, InforequestEmail, Branch, Action

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@transaction.atomic
@login_required(raise_exception=True)
def _decide_email(request, inforequest_pk, email_pk, action_type, form_class, template):
    assert action_type in Action.OBLIGEE_EMAIL_ACTION_TYPES

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
    if not inforequest.can_add_action(action_type):
        return HttpResponseNotFound()

    if request.method == u'POST':
        form = form_class(request.POST, inforequest=inforequest, action_type=action_type)
        if form.is_valid():
            action = Action(
                    subject=email.subject,
                    content=email.text,
                    effective_date=local_date(email.processed),
                    email=email,
                    type=action_type,
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
            return JsonResponse({
                    u'result': u'success',
                    u'scroll_to': u'#action-%d' % action.pk,
                    u'content': render_to_string(u'inforequests/detail-main.html', context_instance=RequestContext(request), dictionary={
                        u'inforequest': inforequest,
                        }),
                    })

        return JsonResponse({
                u'result': u'invalid',
                u'content': render_to_string(template, context_instance=RequestContext(request), dictionary={
                    u'inforequest': inforequest,
                    u'email': email,
                    u'form': form,
                    }),
                })

    else: # request.method != u'POST'
        form = form_class(inforequest=inforequest, action_type=action_type)
        return render(request, template, {
                u'inforequest': inforequest,
                u'email': email,
                u'form': form,
                })

def confirmation(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, Action.TYPES.CONFIRMATION,
            forms.ConfirmationEmailForm, u'inforequests/modals/confirmation-email.html')

def extension(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, Action.TYPES.EXTENSION,
            forms.ExtensionEmailForm, u'inforequests/modals/extension-email.html')

def advancement(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, Action.TYPES.ADVANCEMENT,
            forms.AdvancementEmailForm, u'inforequests/modals/advancement-email.html')

def clarification_request(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, Action.TYPES.CLARIFICATION_REQUEST,
            forms.ClarificationRequestEmailForm, u'inforequests/modals/clarification_request-email.html')

def disclosure(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, Action.TYPES.DISCLOSURE,
            forms.DisclosureEmailForm, u'inforequests/modals/disclosure-email.html')

def refusal(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, Action.TYPES.REFUSAL,
            forms.RefusalEmailForm, u'inforequests/modals/refusal-email.html')

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@transaction.atomic
@login_required(raise_exception=True)
def unrelated(request, inforequest_pk, email_pk):
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

    if request.method == u'POST':
        inforequestemail.type = InforequestEmail.TYPES.UNRELATED
        inforequestemail.save(update_fields=[u'type'])

        # The inforequest was changed, we need to refetch it
        inforequest = Inforequest.objects.prefetch_detail().get(pk=inforequest.pk)
        return JsonResponse({
                u'result': u'success',
                u'content': render_to_string(u'inforequests/detail-main.html', context_instance=RequestContext(request), dictionary={
                    u'inforequest': inforequest,
                    }),
                })

    else: # request.method != u'POST'
        return render(request, u'inforequests/modals/unrelated-email.html', {
                u'inforequest': inforequest,
                u'email': email,
                })

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@transaction.atomic
@login_required(raise_exception=True)
def unknown(request, inforequest_pk, email_pk):
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

    if request.method == u'POST':
        inforequestemail.type = InforequestEmail.TYPES.UNKNOWN
        inforequestemail.save(update_fields=[u'type'])

        # The inforequest was changed, we need to refetch it
        inforequest = Inforequest.objects.prefetch_detail().get(pk=inforequest.pk)
        return JsonResponse({
                u'result': u'success',
                u'content': render_to_string(u'inforequests/detail-main.html', context_instance=RequestContext(request), dictionary={
                    u'inforequest': inforequest,
                    }),
                })

    else: # request.method != u'POST'
        return render(request, u'inforequests/modals/unknown-email.html', {
                u'inforequest': inforequest,
                u'email': email,
                })
