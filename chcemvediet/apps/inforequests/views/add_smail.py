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
from chcemvediet.apps.inforequests import forms
from chcemvediet.apps.inforequests.models import Inforequest, Branch, Action, ActionDraft


@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@transaction.atomic
@login_required(raise_exception=True)
def _add_smail(request, inforequest_pk, action_type, form_class, template):
    assert action_type in Action.OBLIGEE_ACTION_TYPES

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

                # The inforequest was changed, we need to refetch it
                inforequest = Inforequest.objects.prefetch_detail().get(pk=inforequest.pk)
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

def confirmation(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.CONFIRMATION,
            forms.ConfirmationSmailForm, u'inforequests/modals/confirmation-smail.html')

def extension(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.EXTENSION,
            forms.ExtensionSmailForm, u'inforequests/modals/extension-smail.html')

def advancement(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.ADVANCEMENT,
            forms.AdvancementSmailForm, u'inforequests/modals/advancement-smail.html')

def clarification_request(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.CLARIFICATION_REQUEST,
            forms.ClarificationRequestSmailForm, u'inforequests/modals/clarification_request-smail.html')

def disclosure(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.DISCLOSURE,
            forms.DisclosureSmailForm, u'inforequests/modals/disclosure-smail.html')

def refusal(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.REFUSAL,
            forms.RefusalSmailForm, u'inforequests/modals/refusal-smail.html')

def affirmation(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.AFFIRMATION,
            forms.AffirmationSmailForm, u'inforequests/modals/affirmation-smail.html')

def reversion(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.REVERSION,
            forms.ReversionSmailForm, u'inforequests/modals/reversion-smail.html')

def remandment(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, Action.TYPES.REMANDMENT,
            forms.RemandmentSmailForm, u'inforequests/modals/remandment-smail.html')
