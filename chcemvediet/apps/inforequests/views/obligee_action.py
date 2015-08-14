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

    def finish(wizard):
        print(wizard.values)
        raise NotImplementedError

    return wizard_view(ObligeeActionWizard, request, step_idx, finish, inforequest)
