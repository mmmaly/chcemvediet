# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponseBadRequest, JsonResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.contrib.sessions.models import Session
from django.shortcuts import render
from allauth.account.decorators import verified_email_required

from poleno.utils.views import require_ajax, login_required
from poleno.utils.forms import clean_button
from chcemvediet.apps.inforequests import forms
from chcemvediet.apps.inforequests.models import InforequestDraft, Inforequest, Branch, Action

@require_http_methods([u'HEAD', u'GET'])
@login_required
def index(request):
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
def create(request, draft_pk=None):
    draft = (InforequestDraft.objects
            .owned_by(request.user)
            .get_or_404(pk=draft_pk)
                if draft_pk else None
            )
    session = Session.objects.get(session_key=request.session.session_key)
    attached_to = (session, draft) if draft else (session,)

    if request.method == u'POST':
        button = clean_button(request.POST, [u'submit', u'draft'])

        if button == u'draft':
            form = forms.InforequestForm(request.POST, draft=True, attached_to=attached_to, user=request.user)
            if form.is_valid():
                if not draft:
                    draft = InforequestDraft(applicant=request.user)
                form.save_to_draft(draft)
                draft.save()
                return HttpResponseRedirect(reverse(u'inforequests:index'))

        elif button == u'submit':
            form = forms.InforequestForm(request.POST, attached_to=attached_to, user=request.user)
            if form.is_valid():
                inforequest = Inforequest(applicant=request.user)
                form.save(inforequest)
                inforequest.save()

                action = inforequest.main_branch.last_action
                action.send_by_email()

                if draft:
                    draft.delete()
                return HttpResponseRedirect(reverse(u'inforequests:detail', args=(inforequest.pk,)))

        else: # Invalid button
            return HttpResponseBadRequest()

    else:
        form = forms.InforequestForm(attached_to=attached_to, user=request.user)
        if draft:
            form.load_from_draft(draft)

    return render(request, u'inforequests/create.html', {
            u'form': form,
            })

@require_http_methods([u'HEAD', u'GET'])
@login_required
def detail(request, inforequest_pk):
    inforequest = Inforequest.objects.owned_by(request.user).prefetch_detail().get_or_404(pk=inforequest_pk)
    return render(request, u'inforequests/detail.html', {
            u'inforequest': inforequest,
            u'devtools': u'inforequests/detail-devtools.html',
            })

@require_http_methods([u'POST'])
@transaction.atomic
@login_required
def delete_draft(request, draft_pk):
    draft = (InforequestDraft.objects
            .owned_by(request.user)
            .get_or_404(pk=draft_pk)
            )
    draft.delete()
    return HttpResponseRedirect(reverse(u'inforequests:index'))

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@transaction.atomic
@login_required(raise_exception=True)
def extend_deadline(request, inforequest_pk, branch_pk, action_pk):
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

    if request.method == u'POST':
        form = forms.ExtendDeadlineForm(request.POST, prefix=action.pk)
        if form.is_valid():
            form.save(action)
            action.save(update_fields=[u'extension'])

            # The inforequest was changed, we need to refetch it
            inforequest = Inforequest.objects.prefetch_detail().get(pk=inforequest.pk)
            return JsonResponse({
                    u'result': u'success',
                    u'content': render_to_string(u'inforequests/detail-main.html', context_instance=RequestContext(request), dictionary={
                        u'inforequest': inforequest,
                        }),
                    })

        return JsonResponse({
                u'result': u'invalid',
                u'content': render_to_string(u'inforequests/modals/extend-deadline.html', context_instance=RequestContext(request), dictionary={
                    u'inforequest': inforequest,
                    u'branch': branch,
                    u'action': action,
                    u'form': form,
                    }),
                })

    else: # request.method != u'POST'
        form = forms.ExtendDeadlineForm(prefix=action.pk)
        return render(request, u'inforequests/modals/extend-deadline.html', {
                u'inforequest': inforequest,
                u'branch': branch,
                u'action': action,
                u'form': form,
                })
