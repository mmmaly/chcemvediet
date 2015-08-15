# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import transaction
from django.views.decorators.http import require_http_methods

from poleno.utils.views import login_required
from chcemvediet.apps.wizards.views import wizard_view
from chcemvediet.apps.inforequests.models import Inforequest
from chcemvediet.apps.inforequests.forms import ObligeeActionWizard


@require_http_methods([u'HEAD', u'GET', u'POST'])
@transaction.atomic
@login_required(raise_exception=True)
def obligee_action(request, inforequest_pk, step_idx=None):
    inforequest = Inforequest.objects.not_closed().owned_by(request.user).get_or_404(pk=inforequest_pk)
    inforequestemail = inforequest.inforequestemail_set.undecided().oldest().get_or_none()
    email = inforequestemail.email if inforequestemail is not None else None

    def finish(wizard):
        result = wizard.values[u'result']
        if result == u'action':
            action = wizard.save_action()
            return action.get_absolute_url()
        if result == u'help':
            wizard.save_help()
            return inforequest.get_absolute_url()
        if result == u'unrelated':
            wizard.save_unrelated()
            return inforequest.get_absolute_url()
        raise ValueError

    return wizard_view(ObligeeActionWizard, request, step_idx, finish,
            inforequest, inforequestemail, email)
