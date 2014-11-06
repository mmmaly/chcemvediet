# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect, Http404, HttpResponseBadRequest
from django.template import RequestContext
from django.template.loader import render_to_string
from django.shortcuts import render
from allauth.account.decorators import verified_email_required

from poleno.attachments import views as attachments_views
from poleno.attachments.models import Attachment
from poleno.mail.models import Message as EmailMessage
from poleno.utils.http import JsonResponse
from poleno.utils.views import require_ajax, login_required
from poleno.utils.misc import Bunch
from poleno.utils.forms import clean_button
from poleno.utils.date import local_date, local_today

from . import forms
from .models import InforequestDraft, Inforequest, InforequestEmail, Action, ActionDraft

@require_http_methods([u'HEAD', u'GET'])
@login_required
def index(request):
    inforequest_list = Inforequest.objects.not_closed().owned_by(request.user)
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
    attached_to = (request.user, draft) if draft else (request.user,)

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

                action = inforequest.paperwork.action_set.requests().first()
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
def decide_email(request, action, inforequest_pk, email_pk):
    inforequest = Inforequest.objects.not_closed().owned_by(request.user).get_or_404(pk=inforequest_pk)
    email = inforequest.undecided_set.get_or_404(pk=email_pk)
    inforequestemail = inforequest.inforequestemail_set.get(email=email)

    available_actions = {
            u'unrelated': Bunch(
                template = u'inforequests/modals/unrelated-email.html',
                inforequestemail_type = InforequestEmail.TYPES.UNRELATED,
                action_type = None,
                form_class = None,
                ),
            u'unknown': Bunch(
                template = u'inforequests/modals/unknown-email.html',
                inforequestemail_type = InforequestEmail.TYPES.UNKNOWN,
                action_type = None,
                form_class = None,
                ),
            u'confirmation': Bunch(
                template = u'inforequests/modals/confirmation-email.html',
                inforequestemail_type = InforequestEmail.TYPES.OBLIGEE_ACTION,
                action_type = Action.TYPES.CONFIRMATION,
                form_class = forms.ConfirmationEmailForm,
                ),
            u'extension': Bunch(
                template = u'inforequests/modals/extension-email.html',
                inforequestemail_type = InforequestEmail.TYPES.OBLIGEE_ACTION,
                action_type = Action.TYPES.EXTENSION,
                form_class = forms.ExtensionEmailForm,
                ),
            u'advancement': Bunch(
                template = u'inforequests/modals/advancement-email.html',
                inforequestemail_type = InforequestEmail.TYPES.OBLIGEE_ACTION,
                action_type = Action.TYPES.ADVANCEMENT,
                form_class = forms.AdvancementEmailForm,
                ),
            u'clarification-request': Bunch(
                template = u'inforequests/modals/clarification_request-email.html',
                inforequestemail_type = InforequestEmail.TYPES.OBLIGEE_ACTION,
                action_type = Action.TYPES.CLARIFICATION_REQUEST,
                form_class = forms.ClarificationRequestEmailForm,
                ),
            u'disclosure': Bunch(
                template = u'inforequests/modals/disclosure-email.html',
                inforequestemail_type = InforequestEmail.TYPES.OBLIGEE_ACTION,
                action_type = Action.TYPES.DISCLOSURE,
                form_class = forms.DisclosureEmailForm,
                ),
            u'refusal': Bunch(
                template = u'inforequests/modals/refusal-email.html',
                inforequestemail_type = InforequestEmail.TYPES.OBLIGEE_ACTION,
                action_type = Action.TYPES.REFUSAL,
                form_class = forms.RefusalEmailForm,
                ),
            }

    try:
        template = available_actions[action].template
        inforequestemail_type = available_actions[action].inforequestemail_type
        action_type = available_actions[action].action_type
        form_class = available_actions[action].form_class
    except KeyError:
        raise Http404

    if email != inforequest.oldest_undecided_email:
        raise Http404
    if action_type and not inforequest.can_add_action(action_type):
        raise Http404

    if request.method == u'POST':
        action = None
        if action_type:
            form = form_class(request.POST, inforequest=inforequest, action_type=action_type)
            if not form.is_valid():
                return JsonResponse({
                        u'result': u'invalid',
                        u'content': render_to_string(template, context_instance=RequestContext(request), dictionary={
                            u'inforequest': inforequest,
                            u'email': email,
                            u'form': form,
                            }),
                        })
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

        inforequestemail.type = inforequestemail_type
        inforequestemail.save()

        return JsonResponse({
                u'result': u'success',
                u'scroll_to': u'#action-%d' % action.pk if action else u'',
                u'content': render_to_string(u'inforequests/detail-main.html', context_instance=RequestContext(request), dictionary={
                    u'inforequest': inforequest,
                    }),
                })

    else: # request.method != u'POST'
        form = form_class(inforequest=inforequest, action_type=action_type) if form_class else None
        return render(request, template, {
                u'inforequest': inforequest,
                u'email': email,
                u'form': form,
                })

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@login_required(raise_exception=True)
def add_smail(request, action, inforequest_pk):
    inforequest = Inforequest.objects.not_closed().owned_by(request.user).get_or_404(pk=inforequest_pk)

    available_actions = {
            u'confirmation': Bunch(
                template = u'inforequests/modals/confirmation-smail.html',
                action_type = Action.TYPES.CONFIRMATION,
                form_class = forms.ConfirmationSmailForm,
                ),
            u'extension': Bunch(
                template = u'inforequests/modals/extension-smail.html',
                action_type = Action.TYPES.EXTENSION,
                form_class = forms.ExtensionSmailForm,
                ),
            u'advancement': Bunch(
                template = u'inforequests/modals/advancement-smail.html',
                action_type = Action.TYPES.ADVANCEMENT,
                form_class = forms.AdvancementSmailForm,
                ),
            u'clarification-request': Bunch(
                template = u'inforequests/modals/clarification_request-smail.html',
                action_type = Action.TYPES.CLARIFICATION_REQUEST,
                form_class = forms.ClarificationRequestSmailForm,
                ),
            u'disclosure': Bunch(
                template = u'inforequests/modals/disclosure-smail.html',
                action_type = Action.TYPES.DISCLOSURE,
                form_class = forms.DisclosureSmailForm,
                ),
            u'refusal': Bunch(
                template = u'inforequests/modals/refusal-smail.html',
                action_type = Action.TYPES.REFUSAL,
                form_class = forms.RefusalSmailForm,
                ),
            u'affirmation': Bunch(
                template = u'inforequests/modals/affirmation-smail.html',
                action_type = Action.TYPES.AFFIRMATION,
                form_class = forms.AffirmationSmailForm,
                ),
            u'reversion': Bunch(
                template = u'inforequests/modals/reversion-smail.html',
                action_type = Action.TYPES.REVERSION,
                form_class = forms.ReversionSmailForm,
                ),
            u'remandment': Bunch(
                template = u'inforequests/modals/remandment-smail.html',
                action_type = Action.TYPES.REMANDMENT,
                form_class = forms.RemandmentSmailForm,
                ),
            }

    try:
        template = available_actions[action].template
        action_type = available_actions[action].action_type
        form_class = available_actions[action].form_class
    except KeyError:
        raise Http404

    if request.method != u'POST': # The user cas save a draft even if he may not submit.
        if inforequest.has_undecided_email:
            raise Http404
        if not inforequest.can_add_action(action_type):
            raise Http404

    draft = inforequest.actiondraft_set.filter(type=action_type).first()
    attached_to = (request.user, draft) if draft else (request.user,)

    if request.method == u'POST':
        button = clean_button(request.POST, [u'add', u'draft'])
        form = form_class(request.POST, inforequest=inforequest, action_type=action_type, draft=(button == u'draft'), attached_to=attached_to)
        if not button or not form.is_valid():
            return JsonResponse({
                    u'result': u'invalid',
                    u'content': render_to_string(template, context_instance=RequestContext(request), dictionary={
                        u'inforequest': inforequest,
                        u'form': form,
                        }),
                    })

        if button == u'draft':
            if not draft:
                draft = ActionDraft(
                        inforequest=inforequest,
                        type=action_type
                        )
            form.save_to_draft(draft)
            draft.save()
            return JsonResponse({
                    u'result': u'success',
                    })

        action = Action(
                type=action_type,
                )
        form.save(action)
        action.save()

        return JsonResponse({
                u'result': u'success',
                u'scroll_to': u'#action-%d' % action.pk,
                u'content': render_to_string(u'inforequests/detail-main.html', context_instance=RequestContext(request), dictionary={
                    u'inforequest': inforequest,
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

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@login_required(raise_exception=True)
def new_action(request, action, inforequest_pk):
    inforequest = Inforequest.objects.not_closed().owned_by(request.user).get_or_404(pk=inforequest_pk)

    available_actions = {
            u'clarification-response': Bunch(
                template = u'inforequests/modals/clarification_response.html',
                action_type = Action.TYPES.CLARIFICATION_RESPONSE,
                form_class = forms.ClarificationResponseForm,
                can_email = True,
                ),
            u'appeal': Bunch(
                template = u'inforequests/modals/appeal.html',
                action_type = Action.TYPES.APPEAL,
                form_class = forms.AppealForm,
                can_email = False,
                ),
            }

    try:
        template = available_actions[action].template
        action_type = available_actions[action].action_type
        form_class = available_actions[action].form_class
        can_email = available_actions[action].can_email
    except KeyError:
        raise Http404

    if request.method != u'POST': # The user cas save a draft even if he may not submit.
        if inforequest.has_undecided_email:
            raise Http404
        if not inforequest.can_add_action(action_type):
            raise Http404

    draft = inforequest.actiondraft_set.filter(type=action_type).first()
    attached_to = (request.user, draft) if draft else (request.user,)

    if request.method == u'POST':
        button = clean_button(request.POST, [u'email', u'print', u'draft'] if can_email else [u'print', u'draft'])
        form = form_class(request.POST, inforequest=inforequest, action_type=action_type, draft=(button == u'draft'), attached_to=attached_to)
        if not button or not form.is_valid():
            return JsonResponse({
                    u'result': u'invalid',
                    u'content': render_to_string(template, context_instance=RequestContext(request), dictionary={
                        u'inforequest': inforequest,
                        u'form': form,
                        }),
                    })

        if button == u'draft':
            if not draft:
                draft = ActionDraft(
                        inforequest=inforequest,
                        type=action_type
                        )
            form.save_to_draft(draft)
            draft.save()
            return JsonResponse({
                    u'result': u'success',
                    })

        if action_type == Action.TYPES.APPEAL:
            form.cleaned_data[u'paperwork'].add_expiration_if_expired()

        action = Action(
                effective_date=local_today(),
                type=action_type,
                )
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

    else: # request.method != u'POST'
        form = form_class(inforequest=inforequest, action_type=action_type, attached_to=attached_to)
        if draft:
            form.load_from_draft(draft)
        return render(request, template, {
                u'inforequest': inforequest,
                u'form': form,
                })

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@login_required(raise_exception=True)
def extend_deadline(request, inforequest_pk, paperwork_pk, action_pk):
    inforequest = Inforequest.objects.not_closed().owned_by(request.user).get_or_404(pk=inforequest_pk)
    paperwork = inforequest.paperwork_set.get_or_404(pk=paperwork_pk)
    action = paperwork.action_set.get_or_404(pk=action_pk)

    if action != paperwork.action_set.last():
        raise Http404
    if not action.has_obligee_deadline:
        raise Http404
    if not action.deadline_missed:
        raise Http404
    if inforequest.has_undecided_email:
        raise Http404

    if request.method == u'POST':
        form = forms.ExtendDeadlineForm(request.POST, prefix=action.pk)
        if not form.is_valid():
            return JsonResponse({
                    u'result': u'invalid',
                    u'content': render_to_string(u'inforequests/modals/extend-deadline.html', context_instance=RequestContext(request), dictionary={
                        u'inforequest': inforequest,
                        u'paperwork': paperwork,
                        u'action': action,
                        u'form': form,
                        }),
                    })
        form.save(action)
        action.save()

        return JsonResponse({
                u'result': u'success',
                u'content': render_to_string(u'inforequests/detail-main.html', context_instance=RequestContext(request), dictionary={
                    u'inforequest': inforequest,
                    }),
                })

    else: # request.method != u'POST'
        form = forms.ExtendDeadlineForm(prefix=action.pk)
        return render(request, u'inforequests/modals/extend-deadline.html', {
                u'inforequest': inforequest,
                u'paperwork': paperwork,
                u'action': action,
                u'form': form,
                })

@require_http_methods([u'POST'])
@require_ajax
@login_required(raise_exception=True)
def upload_attachment(request):
    download_url_func = (lambda a: reverse(u'inforequests:download_attachment', args=(a.pk,)))
    return attachments_views.upload(request, request.user, download_url_func)

@require_http_methods([u'HEAD', u'GET'])
@login_required(raise_exception=True)
def download_attachment(request, attachment_pk):
    attached_to = (
            request.user,
            EmailMessage.objects.filter(inforequest__applicant=request.user),
            InforequestDraft.objects.filter(applicant=request.user),
            Action.objects.filter(paperwork__inforequest__applicant=request.user),
            ActionDraft.objects.filter(inforequest__applicant=request.user),
            )
    attachment = Attachment.objects.attached_to(*attached_to).get_or_404(pk=attachment_pk)
    return attachments_views.download(request, attachment)
