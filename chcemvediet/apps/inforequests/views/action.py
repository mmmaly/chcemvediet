# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseNotFound

from poleno.utils.views import require_ajax, login_required
from chcemvediet.apps.inforequests.forms import ExtendDeadlineForm
from chcemvediet.apps.inforequests.models import Inforequest, Action

from .shortcuts import render_form, json_form, json_success


@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@transaction.atomic
@login_required(raise_exception=True)
def action_extend_deadline(request, inforequest_pk, branch_pk, action_pk):
    inforequest = Inforequest.objects.not_closed().owned_by(request.user).get_or_404(pk=inforequest_pk)
    branch = inforequest.branch_set.get_or_404(pk=branch_pk)
    action = branch.last_action

    if action.pk != Action._meta.pk.to_python(action_pk):
        return HttpResponseNotFound()
    if not action.has_obligee_deadline:
        return HttpResponseNotFound()
    if not action.deadline_missed:
        return HttpResponseNotFound()
    if inforequest.has_undecided_emails:
        return HttpResponseNotFound()

    if request.method != u'POST':
        form = ExtendDeadlineForm(prefix=action.pk)
        return render_form(request, form, inforequest=inforequest, branch=branch, action=action)

    form = ExtendDeadlineForm(request.POST, prefix=action.pk)
    if not form.is_valid():
        return json_form(request, form, inforequest=inforequest, branch=branch, action=action)

    form.save(action)
    action.save(update_fields=[u'extension'])

    # The inforequest was changed, we need to refetch it
    inforequest = Inforequest.objects.prefetch_detail().get(pk=inforequest.pk)
    return json_success(request, inforequest)
