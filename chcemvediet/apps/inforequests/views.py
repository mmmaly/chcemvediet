# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponseBadRequest, JsonResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.contrib.sessions.models import Session
from django.shortcuts import render
from allauth.account.decorators import verified_email_required

from poleno.attachments import views as attachments_views
from poleno.attachments.models import Attachment
from poleno.mail.models import Message as EmailMessage
from poleno.utils.views import require_ajax, login_required
from poleno.utils.misc import Bunch
from poleno.utils.forms import clean_button
from poleno.utils.date import local_date, local_today

from . import forms
from .models import InforequestDraft, Inforequest, InforequestEmail, Action, ActionDraft

@require_http_methods([u'HEAD', u'GET'])
@login_required
def index(request):
    inforequest_list = Inforequest.objects.not_closed().owned_by(request.user).prefetch_has_undecided_email()
    draft_list = InforequestDraft.objects.owned_by(request.user)
    closed_list = Inforequest.objects.closed().owned_by(request.user)

    return render(request, u'inforequests/index.html', {
            u'inforequest_list': inforequest_list,
            u'draft_list': draft_list,
            u'closed_list': closed_list,
            })

@require_http_methods([u'HEAD', u'GET', u'POST'])
@verified_email_required
def create(request, draft_pk=None):
    draft = InforequestDraft.objects.owned_by(request.user).get_or_404(pk=draft_pk) if draft_pk else None
    session = Session.objects.get(session_key=request.session.session_key)
    attached_to = (session, draft) if draft else (session,)

    if request.method == u'POST':
        button = clean_button(request.POST, [u'submit', u'draft'])

        if button == u'draft':
            form = forms.InforequestForm(request.POST, draft=True, attached_to=attached_to)
            if form.is_valid():
                if not draft:
                    draft = InforequestDraft(applicant=request.user)
                form.save_to_draft(draft)
                draft.save()
                return HttpResponseRedirect(reverse(u'inforequests:index'))

        elif button == u'submit':
            form = forms.InforequestForm(request.POST, attached_to=attached_to)
            if form.is_valid():
                inforequest = Inforequest(applicant=request.user)
                form.save(inforequest)
                inforequest.save()

                action = inforequest.branch.action_set.requests().first()
                action.send_by_email()

                if draft:
                    draft.delete()
                return HttpResponseRedirect(reverse(u'inforequests:detail', args=(inforequest.pk,)))

        else: # Invalid button
            return HttpResponseBadRequest()

    else:
        form = forms.InforequestForm(attached_to=attached_to)
        if draft:
            form.load_from_draft(draft)

    return render(request, u'inforequests/create.html', {
            u'form': form,
            })

@require_http_methods([u'HEAD', u'GET'])
@login_required
def detail(request, inforequest_pk):
    inforequest = Inforequest.objects.owned_by(request.user).get_or_404(pk=inforequest_pk)
    return render(request, u'inforequests/detail.html', {
            u'inforequest': inforequest,
            })

@require_http_methods([u'POST'])
@login_required
def delete_draft(request, draft_pk):
    draft = InforequestDraft.objects.owned_by(request.user).get_or_404(pk=draft_pk)
    draft.delete()
    return HttpResponseRedirect(reverse(u'inforequests:index'))

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@login_required(raise_exception=True)
def _decide_email(request, inforequest_pk, email_pk, action_type, form_class, template):
    assert action_type in Action.OBLIGEE_EMAIL_ACTION_TYPES

    inforequest = Inforequest.objects.not_closed().owned_by(request.user).get_or_404(pk=inforequest_pk)
    email = inforequest.undecided_set.get_or_404(pk=email_pk)
    inforequestemail = inforequest.inforequestemail_set.get(email=email)

    if email != inforequest.oldest_undecided_email:
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

            for attch in email.attachment_set.all():
                attachment = attch.clone()
                attachment.generic_object = action
                attachment.save()

            inforequestemail.type = InforequestEmail.TYPES.OBLIGEE_ACTION
            inforequestemail.save()

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

def decide_email_confirmation(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, Action.TYPES.CONFIRMATION,
            forms.ConfirmationEmailForm, u'inforequests/modals/confirmation-email.html')

def decide_email_extension(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, Action.TYPES.EXTENSION,
            forms.ExtensionEmailForm, u'inforequests/modals/extension-email.html')

def decide_email_advancement(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, Action.TYPES.ADVANCEMENT,
            forms.AdvancementEmailForm, u'inforequests/modals/advancement-email.html')

def decide_email_clarification_request(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, Action.TYPES.CLARIFICATION_REQUEST,
            forms.ClarificationRequestEmailForm, u'inforequests/modals/clarification_request-email.html')

def decide_email_disclosure(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, Action.TYPES.DISCLOSURE,
            forms.DisclosureEmailForm, u'inforequests/modals/disclosure-email.html')

def decide_email_refusal(request, inforequest_pk, email_pk):
    return _decide_email(request, inforequest_pk, email_pk, Action.TYPES.REFUSAL,
            forms.RefusalEmailForm, u'inforequests/modals/refusal-email.html')

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@login_required(raise_exception=True)
def decide_email_unrelated(request, inforequest_pk, email_pk):
    inforequest = Inforequest.objects.not_closed().owned_by(request.user).get_or_404(pk=inforequest_pk)
    email = inforequest.undecided_set.get_or_404(pk=email_pk)
    inforequestemail = inforequest.inforequestemail_set.get(email=email)

    if email != inforequest.oldest_undecided_email:
        return HttpResponseNotFound()

    if request.method == u'POST':
        inforequestemail.type = InforequestEmail.TYPES.UNRELATED
        inforequestemail.save()

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
@login_required(raise_exception=True)
def decide_email_unknown(request, inforequest_pk, email_pk):
    inforequest = Inforequest.objects.not_closed().owned_by(request.user).get_or_404(pk=inforequest_pk)
    email = inforequest.undecided_set.get_or_404(pk=email_pk)
    inforequestemail = inforequest.inforequestemail_set.get(email=email)

    if email != inforequest.oldest_undecided_email:
        return HttpResponseNotFound()

    if request.method == u'POST':
        inforequestemail.type = InforequestEmail.TYPES.UNKNOWN
        inforequestemail.save()

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

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@login_required(raise_exception=True)
def _add_smail(request, inforequest_pk, action_type, form_class, template):
    assert action_type in Action.OBLIGEE_ACTION_TYPES

    inforequest = Inforequest.objects.not_closed().owned_by(request.user).get_or_404(pk=inforequest_pk)

    if request.method != u'POST': # The user can save a draft even if he may not submit.
        if inforequest.has_undecided_email:
            return HttpResponseNotFound()
        if not inforequest.can_add_action(action_type):
            return HttpResponseNotFound()

    draft = inforequest.actiondraft_set.filter(type=action_type).first()
    session = Session.objects.get(session_key=request.session.session_key)
    attached_to = (session, draft) if draft else (session,)

    if request.method == u'POST':
        button = clean_button(request.POST, [u'add', u'draft'])

        if button == u'draft':
            form = form_class(request.POST, inforequest=inforequest, action_type=action_type, attached_to=attached_to, draft=True)
            if form.is_valid():
                if not draft:
                    draft = ActionDraft(inforequest=inforequest, type=action_type)
                form.save_to_draft(draft)
                draft.save()
                return JsonResponse({
                        u'result': u'success',
                        })

        elif button == u'add':
            form = form_class(request.POST, inforequest=inforequest, action_type=action_type, attached_to=attached_to)
            if form.is_valid():
                action = Action(type=action_type)
                form.save(action)
                action.save()

                if draft:
                    draft.delete()

                return JsonResponse({
                        u'result': u'success',
                        u'scroll_to': u'#action-%d' % action.pk,
                        u'content': render_to_string(u'inforequests/detail-main.html', context_instance=RequestContext(request), dictionary={
                            u'inforequest': inforequest,
                            }),
                        })

        else: # Invalid button
            return HttpResponseBadRequest()

        return JsonResponse({
                u'result': u'invalid',
                u'content': render_to_string(template, context_instance=RequestContext(request), dictionary={
                    u'inforequest': inforequest,
                    u'form': form,
                    }),
                })

    else: # request.method != u'POST'
        form = form_class(inforequest=inforequest, action_type=action_type, attached_to=attached_to)
        if draft:
            form.load_from_draft(draft)
        return render(request, template, {
                u'inforequest': inforequest,
                u'form': form,
                })

def add_smail_confirmation(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.CONFIRMATION,
            forms.ConfirmationSmailForm, u'inforequests/modals/confirmation-smail.html')

def add_smail_extension(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.EXTENSION,
            forms.ExtensionSmailForm, u'inforequests/modals/extension-smail.html')

def add_smail_advancement(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.ADVANCEMENT,
            forms.AdvancementSmailForm, u'inforequests/modals/advancement-smail.html')

def add_smail_clarification_request(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.CLARIFICATION_REQUEST,
            forms.ClarificationRequestSmailForm, u'inforequests/modals/clarification_request-smail.html')

def add_smail_disclosure(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.DISCLOSURE,
            forms.DisclosureSmailForm, u'inforequests/modals/disclosure-smail.html')

def add_smail_refusal(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.REFUSAL,
            forms.RefusalSmailForm, u'inforequests/modals/refusal-smail.html')

def add_smail_affirmation(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.AFFIRMATION,
            forms.AffirmationSmailForm, u'inforequests/modals/affirmation-smail.html')

def add_smail_reversion(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.REVERSION,
            forms.ReversionSmailForm, u'inforequests/modals/reversion-smail.html')

def add_smail_remandment(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.REMANDMENT,
            forms.RemandmentSmailForm, u'inforequests/modals/remandment-smail.html')

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@login_required(raise_exception=True)
def _new_action(request, inforequest_pk, action_type, form_class, template):
    assert action_type in Action.APPLICANT_ACTION_TYPES

    inforequest = Inforequest.objects.not_closed().owned_by(request.user).get_or_404(pk=inforequest_pk)

    if request.method != u'POST': # The user can save a draft even if he may not submit.
        if inforequest.has_undecided_email:
            return HttpResponseNotFound()
        if not inforequest.can_add_action(action_type):
            return HttpResponseNotFound()

    draft = inforequest.actiondraft_set.filter(type=action_type).first()
    session = Session.objects.get(session_key=request.session.session_key)
    attached_to = (session, draft) if draft else (session,)

    if request.method == u'POST':
        if action_type in Action.APPLICANT_EMAIL_ACTION_TYPES:
            button = clean_button(request.POST, [u'email', u'print', u'draft'])
        else:
            button = clean_button(request.POST, [u'print', u'draft'])

        if button == u'draft':
            form = form_class(request.POST, inforequest=inforequest, action_type=action_type, attached_to=attached_to, draft=True)
            if form.is_valid():
                if not draft:
                    draft = ActionDraft(inforequest=inforequest, type=action_type)
                form.save_to_draft(draft)
                draft.save()
                return JsonResponse({
                        u'result': u'success',
                        })

        elif button in [u'email', u'print']:
            form = form_class(request.POST, inforequest=inforequest, action_type=action_type, attached_to=attached_to)
            if form.is_valid():
                if action_type == Action.TYPES.APPEAL:
                    form.cleaned_data[u'branch'].add_expiration_if_expired()

                action = Action(effective_date=local_today(), type=action_type)
                form.save(action)
                action.save()

                if button == u'email':
                    action.send_by_email()

                if draft:
                    draft.delete()

                json = {
                        u'result': u'success',
                        u'scroll_to': u'#action-%d' % action.pk,
                        u'content': render_to_string(u'inforequests/detail-main.html', context_instance=RequestContext(request), dictionary={
                            u'inforequest': inforequest,
                            }),
                        }
                if button == u'print':
                    json.update({
                            u'print': render_to_string(u'inforequests/modals/print.html', context_instance=RequestContext(request), dictionary={
                                u'inforequest': inforequest,
                                u'action': action,
                                }),
                            })
                return JsonResponse(json)

        else: # Invalid button
            return HttpResponseBadRequest()

        return JsonResponse({
                u'result': u'invalid',
                u'content': render_to_string(template, context_instance=RequestContext(request), dictionary={
                    u'inforequest': inforequest,
                    u'form': form,
                    }),
                })

    else: # request.method != u'POST'
        form = form_class(inforequest=inforequest, action_type=action_type, attached_to=attached_to)
        if draft:
            form.load_from_draft(draft)
        return render(request, template, {
                u'inforequest': inforequest,
                u'form': form,
                })

def new_action_clarification_response(request, inforequest_pk):
    return _new_action(request, inforequest_pk, Action.TYPES.CLARIFICATION_RESPONSE,
            forms.ClarificationResponseForm, u'inforequests/modals/clarification_response.html')

def new_action_appeal(request, inforequest_pk):
    return _new_action(request, inforequest_pk, Action.TYPES.APPEAL,
            forms.AppealForm, u'inforequests/modals/appeal.html')

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@login_required(raise_exception=True)
def extend_deadline(request, inforequest_pk, branch_pk, action_pk):
    inforequest = Inforequest.objects.not_closed().owned_by(request.user).get_or_404(pk=inforequest_pk)
    branch = inforequest.branch_set.get_or_404(pk=branch_pk)
    action = branch.action_set.get_or_404(pk=action_pk)

    if action != branch.action_set.last():
        return HttpResponseNotFound()
    if not action.has_obligee_deadline:
        return HttpResponseNotFound()
    if not action.deadline_missed:
        return HttpResponseNotFound()
    if inforequest.has_undecided_email:
        return HttpResponseNotFound()

    if request.method == u'POST':
        form = forms.ExtendDeadlineForm(request.POST, prefix=action.pk)
        if form.is_valid():
            form.save(action)
            action.save()

            return JsonResponse({
                    u'result': u'success',
                    u'content': render_to_string(u'inforequests/detail-main.html', context_instance=RequestContext(request), dictionary={
                        u'inforequest': inforequest,
                        }),
                    })

        return JsonResponse({
                u'result': u'invalid',
                u'content': render_to_string(u'inforequests/modals/extend-deadline.html', context_instance=RequestContext(request), dictionary={
                    u'inforequest': inforequest,
                    u'branch': branch,
                    u'action': action,
                    u'form': form,
                    }),
                })

    else: # request.method != u'POST'
        form = forms.ExtendDeadlineForm(prefix=action.pk)
        return render(request, u'inforequests/modals/extend-deadline.html', {
                u'inforequest': inforequest,
                u'branch': branch,
                u'action': action,
                u'form': form,
                })

@require_http_methods([u'POST'])
@require_ajax
@login_required(raise_exception=True)
def upload_attachment(request):
    session = Session.objects.get(session_key=request.session.session_key)
    download_url_func = (lambda a: reverse(u'inforequests:download_attachment', args=(a.pk,)))
    return attachments_views.upload(request, session, download_url_func)

@require_http_methods([u'HEAD', u'GET'])
@login_required(raise_exception=True)
def download_attachment(request, attachment_pk):
    attached_to = (
            Session.objects.get(session_key=request.session.session_key),
            EmailMessage.objects.filter(inforequest__applicant=request.user),
            InforequestDraft.objects.filter(applicant=request.user),
            Action.objects.filter(branch__inforequest__applicant=request.user),
            ActionDraft.objects.filter(inforequest__applicant=request.user),
            )
    attachment = Attachment.objects.attached_to(*attached_to).get_or_404(pk=attachment_pk)
    return attachments_views.download(request, attachment)
