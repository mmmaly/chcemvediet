# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseNotFound

from poleno.utils.views import login_required
from chcemvediet.apps.wizards.views import wizard_view
from chcemvediet.apps.inforequests.models import Inforequest, Action
from chcemvediet.apps.inforequests.forms import AppealWizards, ClarificationResponseWizard


@require_http_methods([u'HEAD', u'GET', u'POST'])
@transaction.atomic
@login_required(raise_exception=True)
def clarification_response(request, inforequest_pk, branch_pk, step_idx=None):
    inforequest = Inforequest.objects.not_closed().owned_by(request.user).get_or_404(pk=inforequest_pk)
    branch = inforequest.branch_set.get_or_404(pk=branch_pk)

    if not branch.can_add_clarification_response:
        return HttpResponseNotFound()
    if inforequest.has_undecided_emails:
        return HttpResponseNotFound()

    def finish(wizard):
        action = Action(type=Action.TYPES.CLARIFICATION_RESPONSE)
        wizard.save(action)
        action.save()
        action.send_by_email()
        return action.get_absolute_url()

    return wizard_view(ClarificationResponseWizard, request, step_idx, finish, branch)

@require_http_methods([u'HEAD', u'GET', u'POST'])
@transaction.atomic
@login_required(raise_exception=True)
def appeal(request, inforequest_pk, branch_pk, step_idx=None):
    inforequest = Inforequest.objects.not_closed().owned_by(request.user).get_or_404(pk=inforequest_pk)
    branch = inforequest.branch_set.get_or_404(pk=branch_pk)

    if not branch.can_add_appeal:
        return HttpResponseNotFound()
    if inforequest.has_undecided_emails:
        return HttpResponseNotFound()

    def finish(wizard):
        branch.add_expiration_if_expired()
        action = Action(type=Action.TYPES.APPEAL)
        wizard.save(action)
        action.save()
        return action.get_absolute_url()

    return wizard_view(AppealWizards, request, step_idx, finish, branch)
