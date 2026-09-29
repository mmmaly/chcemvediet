# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.exceptions import SuspiciousOperation
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect, Http404
from django.contrib.sessions.models import Session
from django.shortcuts import render
from allauth.account.decorators import verified_email_required

from poleno.utils.urls import reverse
from poleno.utils.views import login_required
from poleno.utils.forms import clean_button
from chcemvediet.apps.inforequests.forms import InforequestForm
from chcemvediet.apps.inforequests.models import InforequestDraft, Inforequest, Branch
from chcemvediet.apps.inforequests.constants import INFOREQUESTS_PER_PAGE


@require_http_methods([u'HEAD', u'GET'])
def inforequest_index(request):
    published_inforequests = (Inforequest.objects
            .published()
            .order_by_submission_date()
            .reverse()
            )
    paginator = Paginator(published_inforequests, INFOREQUESTS_PER_PAGE)

    page = request.GET.get(u'page')
    try:
        inforequest_page = paginator.page(page)
    except PageNotAnInteger:
        inforequest_page = paginator.page(1)
    except EmptyPage:
        inforequest_page = paginator.page(paginator.num_pages)

    return render(request, u'inforequests/index/index.html', {
            u'inforequest_page': inforequest_page,
            })

@require_http_methods([u'HEAD', u'GET'])
@login_required
def inforequest_mine(request):
    # The tables show the main obligee, the branches advanced from each action, the last action
    # with its deadline and the disclosure level. Fetch all branches and actions in a few queries
    # instead of several queries per inforequest.
    def prefetch_tree(queryset):
        return queryset.prefetch_related(
                Inforequest.prefetch_branches(None,
                    Branch.objects.select_related(u'historicalobligee')),
                Branch.prefetch_actions(u'branches'),
                )

    pending_inforequests = prefetch_tree(Inforequest.objects
            .not_closed()
            .owned_by(request.user)
            .order_by_submission_date()
            .select_undecided_emails_count()
            )
    drafts = (InforequestDraft.objects
            .owned_by(request.user)
            .order_by_pk()
            .select_related(u'obligee')
            )
    successful_inforequests = prefetch_tree(Inforequest.objects
            .successful()
            .owned_by(request.user)
            .order_by_submission_date()
            .reverse()
            )
    unsuccessful_inforequests = prefetch_tree(Inforequest.objects
            .unsuccessful()
            .owned_by(request.user)
            .order_by_submission_date()
            .reverse()
            )

    return render(request, u'inforequests/mine/mine.html', {
            u'pending_inforequests': pending_inforequests,
            u'drafts': drafts,
            u'successful_inforequests': successful_inforequests,
            u'unsuccessful_inforequests': unsuccessful_inforequests,
            })

@require_http_methods([u'HEAD', u'GET', u'POST'])
@transaction.atomic
@verified_email_required
def inforequest_create(request, draft_pk=None):
    template = u'inforequests/create/create.html'
    draft = (InforequestDraft.objects.owned_by(request.user)
                .get_or_404(pk=draft_pk) if draft_pk else None)
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
        return HttpResponseRedirect(reverse(u'inforequests:mine'))

    if button == u'submit':
        form = InforequestForm(request.POST, attached_to=attached_to, user=request.user)
        if not form.is_valid():
            return render(request, template, dict(form=form))
        inforequest = form.save()
        inforequest.save()
        inforequest.main_branch.last_action.send_by_email()
        if draft:
            draft.delete()
        return HttpResponseRedirect(inforequest.get_absolute_url())

    raise SuspiciousOperation()

@require_http_methods([u'HEAD', u'GET'])
def inforequest_detail(request, inforequest_slug, inforequest_pk):
    inforequest = (Inforequest.objects.prefetch_detail()
                    .get_or_404(pk=inforequest_pk))

    if inforequest.applicant != request.user and not inforequest.published:
        raise Http404()

    if inforequest_slug != inforequest.slug:
        return HttpResponseRedirect(
                reverse(u'inforequests:detail', kwargs=dict(inforequest=inforequest)))

    return render(request, u'inforequests/detail/detail.html', {
            u'inforequest': inforequest,
            u'devtools': u'inforequests/detail/devtools.html',
            })

@require_http_methods([u'POST'])
@transaction.atomic
@login_required
def inforequest_delete_draft(request, draft_pk):
    draft = InforequestDraft.objects.owned_by(request.user).get_or_404(pk=draft_pk)
    draft.delete()
    return HttpResponseRedirect(reverse(u'inforequests:mine'))

@require_http_methods([u'HEAD', u'GET'])
@login_required
def obligee_action_dispatcher(request):
    inforequests = (Inforequest.objects
            .not_closed()
            .owned_by(request.user)
            .order_by_submission_date()
            .select_undecided_emails_count()
            .prefetch_related(
                Inforequest.prefetch_main_branch(None,
                    Branch.objects.select_related(u'historicalobligee')))
            )

    # If the user has an inforequest with a new email, continue with it. If there is no new email
    # and the user has only one pending inforequest, continue with it. If the user has no pending
    # inforequests, return to inforequest index. Finally, if the user has at least two pending
    # inforequests, let him choose with which to continue.
    for inforequest in inforequests:
        if inforequest.has_undecided_emails:
            return HttpResponseRedirect(
                    reverse(u'inforequests:obligee_action', kwargs=dict(inforequest=inforequest)))
    if len(inforequests) == 1:
        return HttpResponseRedirect(
                reverse(u'inforequests:obligee_action', kwargs=dict(inforequest=inforequests[0])))
    if len(inforequests) == 0:
        return HttpResponseRedirect(reverse(u'inforequests:mine'))

    return render(request, u'inforequests/obligee_action_dispatcher/dispatcher.html', {
            u'inforequests': inforequests,
            })
