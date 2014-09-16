# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import timezone
from django.shortcuts import render
from allauth.account.decorators import verified_email_required

from poleno.utils.http import JsonResponse
from poleno.utils.views import require_ajax, login_required
from poleno.utils.misc import Bunch
from poleno.utils.form import clean_button
from chcemvediet.apps.obligees.models import Obligee

from models import Inforequest, InforequestDraft, Action, ActionDraft
import forms

@require_http_methods([u'HEAD', u'GET'])
@login_required
def index(request):
    inforequest_list = Inforequest.objects.all().owned_by(request.user)
    draft_list = InforequestDraft.objects.owned_by(request.user)

    ctx = {}
    ctx[u'inforequest_list'] = inforequest_list
    ctx[u'draft_list'] = draft_list
    return render(request, u'inforequests/index.html', ctx)

@require_http_methods([u'HEAD', u'GET', u'POST'])
@verified_email_required
def create(request, draft_id=None):
    draft = InforequestDraft.objects.owned_by(request.user).get_or_404(pk=draft_id) if draft_id else None

    if request.method == u'POST':
        button = clean_button(request.POST, [u'submit', u'draft'])
        form = forms.InforequestForm(request.POST, user=request.user, draft=(button == u'draft'))

        if button == u'draft':
            if form.is_valid():
                if not draft:
                    draft = InforequestDraft(applicant=request.user)
                form.save_to_draft(draft)
                draft.save()
                return HttpResponseRedirect(reverse(u'inforequests:index'))

        if button == u'submit':
            if form.is_valid():
                inforequest = Inforequest(applicant=request.user)
                form.save(inforequest)
                inforequest.save()

                action = inforequest.history.action_set.requests().first()
                action.send_by_email()

                if draft:
                    draft.delete()
                return HttpResponseRedirect(reverse(u'inforequests:detail', args=(inforequest.id,)))

    else:
        form = forms.InforequestForm(user=request.user)
        if draft:
            form.load_from_draft(draft)

    return render(request, u'inforequests/create.html', {
            u'form': form,
            })

@require_http_methods([u'HEAD', u'GET'])
@login_required
def detail(request, inforequest_id):
    inforequest = Inforequest.objects.owned_by(request.user).get_or_404(pk=inforequest_id)
    return render(request, u'inforequests/detail.html', {
            u'inforequest': inforequest,
            })

@require_http_methods([u'POST'])
@login_required
def delete_draft(request, draft_id):
    draft = InforequestDraft.objects.owned_by(request.user).get_or_404(pk=draft_id)
    draft.delete()
    return HttpResponseRedirect(reverse(u'inforequests:index'))

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@login_required(raise_exception=True)
def decide_email(request, action, inforequest_id, receivedemail_id):
    inforequest = Inforequest.objects.owned_by(request.user).get_or_404(pk=inforequest_id)
    receivedemail = inforequest.receivedemail_set.undecided().get_or_404(pk=receivedemail_id)

    available_actions = {
            u'unrelated': Bunch(
                template = u'inforequests/modals/unrelated-email.html',
                email_status = receivedemail.STATUSES.UNRELATED,
                action_type = None,
                form_class = None,
                ),
            u'unknown': Bunch(
                template = u'inforequests/modals/unknown-email.html',
                email_status = receivedemail.STATUSES.UNKNOWN,
                action_type = None,
                form_class = None,
                ),
            u'confirmation': Bunch(
                template = u'inforequests/modals/confirmation-email.html',
                email_status = receivedemail.STATUSES.OBLIGEE_ACTION,
                action_type = Action.TYPES.CONFIRMATION,
                form_class = forms.ConfirmationEmailForm,
                ),
            u'extension': Bunch(
                template = u'inforequests/modals/extension-email.html',
                email_status = receivedemail.STATUSES.OBLIGEE_ACTION,
                action_type = Action.TYPES.EXTENSION,
                form_class = forms.ExtensionEmailForm,
                ),
            u'advancement': Bunch(
                template = u'inforequests/modals/advancement-email.html',
                email_status = receivedemail.STATUSES.OBLIGEE_ACTION,
                action_type = Action.TYPES.ADVANCEMENT,
                form_class = forms.AdvancementEmailForm,
                ),
            u'clarification-request': Bunch(
                template = u'inforequests/modals/clarification_request-email.html',
                email_status = receivedemail.STATUSES.OBLIGEE_ACTION,
                action_type = Action.TYPES.CLARIFICATION_REQUEST,
                form_class = forms.ClarificationRequestEmailForm,
                ),
            u'disclosure': Bunch(
                template = u'inforequests/modals/disclosure-email.html',
                email_status = receivedemail.STATUSES.OBLIGEE_ACTION,
                action_type = Action.TYPES.DISCLOSURE,
                form_class = forms.DisclosureEmailForm,
                ),
            u'refusal': Bunch(
                template = u'inforequests/modals/refusal-email.html',
                email_status = receivedemail.STATUSES.OBLIGEE_ACTION,
                action_type = Action.TYPES.REFUSAL,
                form_class = forms.RefusalEmailForm,
                ),
            }

    try:
        template = available_actions[action].template
        email_status = available_actions[action].email_status
        action_type = available_actions[action].action_type
        form_class = available_actions[action].form_class
    except KeyError:
        raise Http404

    if receivedemail != inforequest.receivedemail_set.undecided().first():
        raise Http404
    if action_type and not inforequest.can_add_action(action_type):
        raise Http404

    if request.method == u'POST':
        action = None
        if action_type:
            form = form_class(request.POST, user=request.user, inforequest=inforequest, action_type=action_type)
            if not form.is_valid():
                return JsonResponse({
                        u'result': u'invalid',
                        u'content': render_to_string(template, context_instance=RequestContext(request), dictionary={
                            u'inforequest': inforequest,
                            u'email': receivedemail,
                            u'form': form,
                            }),
                        })
            action = Action(
                    subject=receivedemail.raw_email.subject,
                    content=receivedemail.raw_email.text,
                    effective_date=receivedemail.raw_email.processed,
                    receivedemail=receivedemail,
                    type=action_type,
                    )
            form.save(action)
            action.save()

        receivedemail.status = email_status
        receivedemail.save()

        return JsonResponse({
                u'result': u'success',
                u'scroll_to': u'#action-%d' % action.id if action else u'',
                u'content': render_to_string(u'inforequests/detail-main.html', context_instance=RequestContext(request), dictionary={
                    u'inforequest': inforequest,
                    }),
                })

    else: # request.method != u'POST'
        form = form_class(user=request.user, inforequest=inforequest, action_type=action_type) if form_class else None
        return render(request, template, {
                u'inforequest': inforequest,
                u'email': receivedemail,
                u'form': form,
                })

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@login_required(raise_exception=True)
def add_smail(request, action, inforequest_id):
    inforequest = Inforequest.objects.owned_by(request.user).get_or_404(pk=inforequest_id)

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
        if inforequest.has_waiting_email:
            raise Http404
        if not inforequest.can_add_action(action_type):
            raise Http404

    draft = inforequest.actiondraft_set.filter(type=action_type).first()

    if request.method == u'POST':
        button = clean_button(request.POST, [u'add', u'draft'])
        form = form_class(request.POST, user=request.user, inforequest=inforequest, action_type=action_type, draft=(button == u'draft'))
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
                u'scroll_to': u'#action-%d' % action.id,
                u'content': render_to_string(u'inforequests/detail-main.html', context_instance=RequestContext(request), dictionary={
                    u'inforequest': inforequest,
                    }),
                })

    else: # request.method != u'POST'
        form = form_class(user=request.user, inforequest=inforequest, action_type=action_type)
        if draft:
            form.load_from_draft(draft)
        return render(request, template, {
                u'inforequest': inforequest,
                u'form': form,
                })

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@login_required(raise_exception=True)
def new_action(request, action, inforequest_id):
    inforequest = Inforequest.objects.owned_by(request.user).get_or_404(pk=inforequest_id)

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
        if inforequest.has_waiting_email:
            raise Http404
        if not inforequest.can_add_action(action_type):
            raise Http404

    draft = inforequest.actiondraft_set.filter(type=action_type).first()

    if request.method == u'POST':
        button = clean_button(request.POST, [u'email', u'print', u'draft'] if can_email else [u'print', u'draft'])
        form = form_class(request.POST, user=request.user, inforequest=inforequest, action_type=action_type, draft=(button == u'draft'))
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
            form.cleaned_data[u'history'].add_expiration_if_expired()

        action = Action(
                effective_date=timezone.now(),
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
                u'scroll_to': u'#action-%d' % action.id,
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
        form = form_class(user=request.user, inforequest=inforequest, action_type=action_type)
        if draft:
            form.load_from_draft(draft)
        return render(request, template, {
                u'inforequest': inforequest,
                u'form': form,
                })

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@login_required(raise_exception=True)
def extend_deadline(request, inforequest_id, history_id, action_id):
    inforequest = Inforequest.objects.owned_by(request.user).get_or_404(pk=inforequest_id)
    history = inforequest.history_set.get_or_404(pk=history_id)
    action = history.action_set.get_or_404(pk=action_id)

    if action != history.action_set.last():
        raise Http404
    if not action.has_obligee_deadline:
        raise Http404
    if not action.deadline_missed:
        raise Http404
    if inforequest.has_waiting_email:
        raise Http404

    if request.method == u'POST':
        form = forms.ExtendDeadlineForm(request.POST, prefix=action.pk)
        if not form.is_valid():
            return JsonResponse({
                    u'result': u'invalid',
                    u'content': render_to_string(u'inforequests/modals/extend-deadline.html', context_instance=RequestContext(request), dictionary={
                        u'inforequest': inforequest,
                        u'history': history,
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
                u'history': history,
                u'action': action,
                u'form': form,
                })

