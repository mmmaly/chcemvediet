# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect
from django.template import  RequestContext
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from allauth.account.decorators import verified_email_required

from poleno.utils.mail import mail_address_with_name
from poleno.utils.http import JsonResponse
from poleno.utils.views import require_ajax
from chcemvediet.apps.obligees.models import Obligee

from models import Inforequest, InforequestDraft, Action
from forms import InforequestForm, InforequestDraftForm, ExtensionEmailForm, DisclosureEmailForm, RefusalEmailForm

@require_http_methods([u'HEAD', u'GET'])
@login_required
def index(request):
    inforequest_list = Inforequest.objects.all().owned_by(request.user)
    draft_list = InforequestDraft.objects.owned_by(request.user)

    ctx = {}
    ctx[u'inforequest_list'] = inforequest_list
    ctx[u'draft_list'] = draft_list
    return render(request, u'inforequests/index.html', ctx)

@require_http_methods([u'HEAD', u'GET', u'POST'])
@verified_email_required
def create(request, draft_id=None):
    draft = InforequestDraft.objects.owned_by(request.user).get_or_404(pk=draft_id) if draft_id else None

    if request.method == u'POST':
        if u'save' in request.POST:
            form = InforequestDraftForm(request.POST)
            if form.is_valid():
                if not draft:
                    draft = InforequestDraft(applicant=request.user)
                form.save(draft)
                draft.save()
                return HttpResponseRedirect(reverse(u'inforequests:index'))

        elif u'submit' in request.POST:
            form = InforequestForm(request.POST)
            if form.is_valid():
                inforequest = Inforequest(applicant=request.user)
                form.save(inforequest)
                inforequest.save()

                action = Action(
                        history=inforequest.history,
                        type=Action.TYPES.REQUEST,
                        subject=form.cleaned_data[u'subject'],
                        content=form.cleaned_data[u'content'],
                        effective_date=inforequest.submission_date,
                        )
                action.save()

                sender_full = mail_address_with_name(inforequest.applicant_name, inforequest.unique_email)
                send_mail(action.subject, action.content, sender_full, [inforequest.history.obligee.email])

                if draft:
                    draft.delete()
                return HttpResponseRedirect(reverse(u'inforequests:detail', args=(inforequest.id,)))

        else:
            raise PermissionDenied

    else:
        if draft:
            initial = {}
            initial[u'obligee'] = draft.obligee.name if draft.obligee else u''
            initial[u'subject'] = draft.subject
            initial[u'content'] = draft.content
            form = InforequestDraftForm(initial=initial)
        else:
            form = InforequestDraftForm()

    if request.method == u'POST':
        try:
            obligee = Obligee.objects.filter(name=request.POST[u'obligee']).first()
        except:
            obligee = None
    else:
        obligee = draft.obligee if draft else None

    ctx = {}
    ctx[u'form'] = form
    ctx[u'obligee'] = obligee
    return render(request, u'inforequests/create.html', ctx)

@require_http_methods([u'HEAD', u'GET'])
@login_required
def detail(request, inforequest_id):
    inforequest = Inforequest.objects.owned_by(request.user).get_or_404(pk=inforequest_id)

    ctx = {}
    ctx[u'inforequest'] = inforequest
    ctx[u'forms'] = {}
    ctx[u'forms'][u'extension_email'] = ExtensionEmailForm()
    ctx[u'forms'][u'disclosure_email'] = DisclosureEmailForm()
    ctx[u'forms'][u'refusal_email'] = RefusalEmailForm()
    return render(request, u'inforequests/detail.html', ctx)

@require_http_methods([u'POST'])
@login_required
def delete_draft(request, draft_id):
    draft = InforequestDraft.objects.owned_by(request.user).get_or_404(pk=draft_id)
    draft.delete()

    return HttpResponseRedirect(reverse(u'inforequests:index'))

@require_http_methods([u'POST'])
@require_ajax
@login_required
def decide_email(request, inforequest_id, receivedemail_id):
    inforequest = Inforequest.objects.owned_by(request.user).get_or_404(pk=inforequest_id)
    receivedemail = inforequest.receivedemail_set.undecided().get_or_404(pk=receivedemail_id)

    # We don't check whether ``receivedemail`` is the oldest ``inforequest`` undecided e-mail or
    # not. Although the frontend forces the user to decide the e-mails in the order they were
    # received, it is not a mistake to decide them in any other order. In the future we may even
    # add an advanced frontend to allow the user to decide the e-mails in any order, but to keep
    # the frontend simple, we don't do it now.

    def do_decision(email_status, action_type=None, form_class=None, template=None):
        action = None
        if action_type is not None:

            form = None
            if form_class is not None:
                form = form_class(request.POST)
                if not form.is_valid():

                    ctx = {}
                    ctx[u'inforequest'] = inforequest
                    ctx[u'email'] = receivedemail
                    ctx[u'form'] = form
                    content = render_to_string(template, ctx, RequestContext(request))

                    res = {}
                    res[u'result'] = u'invalid'
                    res[u'content'] = content
                    return res

            action = Action(
                    history=inforequest.history,
                    type=action_type,
                    subject=receivedemail.raw_email.subject,
                    content=receivedemail.raw_email.text,
                    effective_date=receivedemail.raw_email.processed,
                    )
            if form:
                form.save(action)
            action.save()

        # FIXME: comment this if you are lazy to send e-mails while testing
        #receivedemail.status = email_status
        #receivedemail.save()

        ctx = {}
        ctx[u'inforequest'] = inforequest
        ctx[u'forms'] = {}
        ctx[u'forms'][u'extension_email'] = ExtensionEmailForm()
        ctx[u'forms'][u'disclosure_email'] = DisclosureEmailForm()
        ctx[u'forms'][u'refusal_email'] = RefusalEmailForm()
        content = render_to_string(u'inforequests/detail-main.html', ctx, RequestContext(request))

        res = {}
        res[u'result'] = u'success'
        res[u'content'] = content
        res[u'scroll_to'] = u'#action-%d' % action.id if action else u''
        return res

    available_decisions = {}
    available_decisions[u'unrelated'] = (receivedemail.STATUSES.UNRELATED,)
    available_decisions[u'unknown'] = (receivedemail.STATUSES.UNKNOWN,)
    available_decisions[u'confirmation'] = (receivedemail.STATUSES.OBLIGEE_ACTION, Action.TYPES.CONFIRMATION)
    available_decisions[u'extension'] = (receivedemail.STATUSES.OBLIGEE_ACTION, Action.TYPES.EXTENSION, ExtensionEmailForm, u'inforequests/actions/extension-email.html')
    available_decisions[u'clarification-request'] = (receivedemail.STATUSES.OBLIGEE_ACTION, Action.TYPES.CLARIFICATION_REQUEST)
    available_decisions[u'disclosure'] = (receivedemail.STATUSES.OBLIGEE_ACTION, Action.TYPES.DISCLOSURE, DisclosureEmailForm, u'inforequests/actions/disclosure-email.html')
    available_decisions[u'refusal'] = (receivedemail.STATUSES.OBLIGEE_ACTION, Action.TYPES.REFUSAL, RefusalEmailForm, u'inforequests/actions/refusal-email.html')

    try:
        decision = available_decisions[request.POST[u'decision']]
    except KeyError:
        raise PermissionDenied

    res = do_decision(*decision)
    return JsonResponse(res)

