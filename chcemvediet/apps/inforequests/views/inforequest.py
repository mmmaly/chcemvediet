# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.contrib.sessions.models import Session
from django.shortcuts import render
from allauth.account.decorators import verified_email_required

from poleno.utils.views import login_required
from poleno.utils.forms import clean_button
from chcemvediet.apps.inforequests.forms import InforequestForm
from chcemvediet.apps.inforequests.models import InforequestDraft, Inforequest, Branch

@require_http_methods([u'HEAD', u'GET'])
@login_required
def inforequest_index(request):
    inforequests = (Inforequest.objects
            .not_closed()
            .owned_by(request.user)
            .order_by_submission_date()
            .select_undecided_emails_count()
            .prefetch_related(Inforequest.prefetch_main_branch(None, Branch.objects.select_related(u'historicalobligee')))
            )
    drafts = (InforequestDraft.objects
            .owned_by(request.user)
            .order_by_pk()
            .select_related(u'obligee')
            )
    closed_inforequests = (Inforequest.objects
            .closed()
            .owned_by(request.user)
            .order_by_submission_date()
            .prefetch_related(Inforequest.prefetch_main_branch(None, Branch.objects.select_related(u'historicalobligee')))
            )

    return render(request, u'inforequests/index.html', {
            u'inforequests': inforequests,
            u'drafts': drafts,
            u'closed_inforequests': closed_inforequests,
            })


@require_http_methods([u'HEAD', u'GET', u'POST'])
@transaction.atomic
@verified_email_required
def inforequest_create(request, draft_pk=None):
    template = u'inforequests/create.html'
    draft = InforequestDraft.objects.owned_by(request.user).get_or_404(pk=draft_pk) if draft_pk else None
    session = Session.objects.get(session_key=request.session.session_key)
    attached_to = (session, draft) if draft else (session,)

    if request.method != u'POST':
        form = InforequestForm(attached_to=attached_to, user=request.user)
        if draft:
            form.load_from_draft(draft)
        return render(request, template, dict(form=form))

    button = clean_button(request.POST, [u'submit', u'draft'])

    if button == u'draft':
        form = InforequestForm(request.POST, draft=True, attached_to=attached_to, user=request.user)
        if not form.is_valid():
            return render(request, template, dict(form=form))
        if not draft:
            draft = InforequestDraft(applicant=request.user)
        form.save_to_draft(draft)
        draft.save()
        return HttpResponseRedirect(reverse(u'inforequests:index'))

    if button == u'submit':
        form = InforequestForm(request.POST, attached_to=attached_to, user=request.user)
        if not form.is_valid():
            return render(request, template, dict(form=form))
        inforequest = Inforequest(applicant=request.user)
        form.save(inforequest)
        inforequest.save()
        inforequest.main_branch.last_action.send_by_email()
        if draft:
            draft.delete()
        return HttpResponseRedirect(reverse(u'inforequests:detail', args=(inforequest.pk,)))

    return HttpResponseBadRequest()


@require_http_methods([u'HEAD', u'GET'])
@login_required
def inforequest_detail(request, inforequest_pk):
    inforequest = Inforequest.objects.owned_by(request.user).prefetch_detail().get_or_404(pk=inforequest_pk)
    return render(request, u'inforequests/detail.html', {
            u'inforequest': inforequest,
            u'devtools': u'inforequests/detail-devtools.html',
            })


@require_http_methods([u'POST'])
@transaction.atomic
@login_required
def inforequest_delete_draft(request, draft_pk):
    draft = InforequestDraft.objects.owned_by(request.user).get_or_404(pk=draft_pk)
    draft.delete()
    return HttpResponseRedirect(reverse(u'inforequests:index'))
