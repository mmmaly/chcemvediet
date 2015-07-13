# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.contrib.sessions.models import Session

from poleno.utils.views import require_ajax, login_required
from poleno.utils.forms import clean_button
from chcemvediet.apps.inforequests import forms
from chcemvediet.apps.inforequests.models import Inforequest, Branch, Action, ActionDraft

from .shortcuts import render_form, json_form, json_draft, json_success


@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@transaction.atomic
@login_required(raise_exception=True)
def _add_smail(request, inforequest_pk, form_class):
    assert form_class.action_type in Action.OBLIGEE_ACTION_TYPES

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
        if not inforequest.can_add_action(form_class.action_type):
            return HttpResponseNotFound()

    draft = inforequest.actiondraft_set.filter(type=form_class.action_type).order_by_pk().first()
    session = Session.objects.get(session_key=request.session.session_key)
    attached_to = (session, draft) if draft else (session,)

    if request.method != u'POST':
        form = form_class(inforequest=inforequest, attached_to=attached_to)
        if draft:
            form.load_from_draft(draft)
        return render_form(request, form, inforequest=inforequest)

    button = clean_button(request.POST, [u'add', u'draft'])

    if button == u'draft':
        form = form_class(request.POST, inforequest=inforequest, attached_to=attached_to, draft=True)
        if not form.is_valid():
            return json_form(request, form, inforequest=inforequest)
        if not draft:
            draft = ActionDraft(inforequest=inforequest, type=form_class.action_type)
        form.save_to_draft(draft)
        draft.save()
        return json_draft()

    if button == u'add':
        form = form_class(request.POST, inforequest=inforequest, attached_to=attached_to)
        if not form.is_valid():
            return json_form(request, form, inforequest=inforequest)
        action = Action(type=form_class.action_type)
        form.save(action)
        action.save()
        if draft:
            draft.delete()
        # The inforequest was changed, we need to refetch it
        inforequest = Inforequest.objects.prefetch_detail().get(pk=inforequest.pk)
        return json_success(request, inforequest, action)

    return HttpResponseBadRequest()

def add_smail_confirmation(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, forms.ConfirmationSmailForm)

def add_smail_extension(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, forms.ExtensionSmailForm)

def add_smail_advancement(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, forms.AdvancementSmailForm)

def add_smail_clarification_request(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, forms.ClarificationRequestSmailForm)

def add_smail_disclosure(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, forms.DisclosureSmailForm)

def add_smail_refusal(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, forms.RefusalSmailForm)

def add_smail_affirmation(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, forms.AffirmationSmailForm)

def add_smail_reversion(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, forms.ReversionSmailForm)

def add_smail_remandment(request, inforequest_pk):
    return _add_smail(request, inforequest_pk, forms.RemandmentSmailForm)
