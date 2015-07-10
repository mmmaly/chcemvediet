# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseNotFound, HttpResponseBadRequest, JsonResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.contrib.sessions.models import Session
from django.shortcuts import render

from poleno.utils.views import require_ajax, login_required
from poleno.utils.forms import clean_button
from poleno.utils.date import local_today
from chcemvediet.apps.inforequests import forms
from chcemvediet.apps.inforequests.models import Inforequest, Branch, Action, ActionDraft


@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@transaction.atomic
@login_required(raise_exception=True)
def _new_action(request, inforequest_pk, action_type, form_class, template):
    assert action_type in Action.APPLICANT_ACTION_TYPES

    inforequest = (Inforequest.objects
            .not_closed()
            .owned_by(request.user)
            .prefetch_related(Inforequest.prefetch_branches(None, Branch.objects.select_related(u'historicalobligee')))
            .prefetch_related(Branch.prefetch_last_action(u'branches'))
            .get_or_404(pk=inforequest_pk)
            )

    if request.method != u'POST': # The user can save a draft even if he may not submit.
        if inforequest.has_undecided_emails:
            return HttpResponseNotFound()
        if not inforequest.can_add_action(action_type):
            return HttpResponseNotFound()

    draft = inforequest.actiondraft_set.filter(type=action_type).order_by_pk().first()
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

                if draft:
                    draft.delete()

                # The inforequest was changed, we need to refetch it. We alse prefetch all related
                # models used by ``detail-main`` template later.
                inforequest = Inforequest.objects.prefetch_detail().get(pk=inforequest.pk)
                action.branch = inforequest.branch_by_pk(action.branch_id)

                if button == u'email':
                    action.send_by_email()

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

def clarification_response(request, inforequest_pk):
    return _new_action(request, inforequest_pk, Action.TYPES.CLARIFICATION_RESPONSE,
            forms.ClarificationResponseForm, u'inforequests/modals/clarification_response.html')

def appeal(request, inforequest_pk):
    return _new_action(request, inforequest_pk, Action.TYPES.APPEAL,
            forms.AppealForm, u'inforequests/modals/appeal.html')
