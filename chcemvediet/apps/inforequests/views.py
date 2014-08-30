# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect, Http404
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
            form = InforequestDraftForm(initial={
                    u'obligee': draft.obligee.name if draft.obligee else u'',
                    u'subject': draft.subject,
                    u'content': draft.content,
                    })
        else:
            form = InforequestDraftForm()

    if request.method == u'POST':
        try:
            obligee = Obligee.objects.filter(name=request.POST[u'obligee']).first()
        except:
            obligee = None
    else:
        obligee = draft.obligee if draft else None

    return render(request, u'inforequests/create.html', {
            u'form': form,
            u'obligee': obligee,
            })

@require_http_methods([u'HEAD', u'GET'])
@login_required
def detail(request, inforequest_id):
    inforequest = Inforequest.objects.owned_by(request.user).get_or_404(pk=inforequest_id)
    return render(request, u'inforequests/detail.html', {
            u'inforequest': inforequest,
            })

@require_http_methods([u'POST'])
@login_required
def delete_draft(request, draft_id):
    draft = InforequestDraft.objects.owned_by(request.user).get_or_404(pk=draft_id)
    draft.delete()
    return HttpResponseRedirect(reverse(u'inforequests:index'))

@require_http_methods([u'HEAD', u'GET', u'POST'])
@require_ajax
@login_required
def decide_email(request, inforequest_id, receivedemail_id, action):
    inforequest = Inforequest.objects.owned_by(request.user).get_or_404(pk=inforequest_id)
    receivedemail = inforequest.receivedemail_set.undecided().get_or_404(pk=receivedemail_id)

    # We don't check whether ``receivedemail`` is the oldest ``inforequest`` undecided e-mail or
    # not. Although the frontend forces the user to decide the e-mails in the order they were
    # received, it is not a mistake to decide them in any other order. In the future we may even
    # add an advanced frontend to allow the user to decide the e-mails in any order, but to keep
    # the frontend simple, we don't do it now.

    def do_action(template, email_status, action_type=None, form_class=None):
        if request.method == u'POST':
            action = None
            if action_type is not None:
                form = None
                if form_class is not None:
                    form = form_class(request.POST)
                    if not form.is_valid():
                        return JsonResponse({
                                u'result': u'invalid',
                                u'content': render_to_string(template, context_instance=RequestContext(request), dictionary={
                                    u'inforequest': inforequest,
                                    u'email': receivedemail,
                                    u'form': form,
                                    }),
                                })
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

            return JsonResponse({
                    u'result': u'success',
                    u'scroll_to': u'#action-%d' % action.id if action else u'',
                    u'content': render_to_string(u'inforequests/detail-main.html', context_instance=RequestContext(request), dictionary={
                        u'inforequest': inforequest,
                        }),
                    })

        else:
            form = None
            if form_class is not None:
                form = form_class()
            return render(request, template, {
                    u'inforequest': inforequest,
                    u'email': receivedemail,
                    u'form': form,
                    })

    available_actions = {
            u'unrelated': {
                u'template': u'inforequests/actions/unrelated-email.html',
                u'email_status': receivedemail.STATUSES.UNRELATED,
                },
            u'unknown': {
                u'template': u'inforequests/actions/unknown-email.html',
                u'email_status': receivedemail.STATUSES.UNKNOWN,
                },
            u'confirmation': {
                u'template': u'inforequests/actions/confirmation-email.html',
                u'email_status': receivedemail.STATUSES.OBLIGEE_ACTION,
                u'action_type': Action.TYPES.CONFIRMATION,
                },
            u'extension': {
                u'template': u'inforequests/actions/extension-email.html',
                u'email_status': receivedemail.STATUSES.OBLIGEE_ACTION,
                u'action_type': Action.TYPES.EXTENSION,
                u'form_class': ExtensionEmailForm,
                },
            u'clarification-request': {
                u'template': u'inforequests/actions/clarification_request-email.html',
                u'email_status': receivedemail.STATUSES.OBLIGEE_ACTION,
                u'action_type': Action.TYPES.CLARIFICATION_REQUEST,
                },
            u'disclosure': {
                u'template': u'inforequests/actions/disclosure-email.html',
                u'email_status': receivedemail.STATUSES.OBLIGEE_ACTION,
                u'action_type': Action.TYPES.DISCLOSURE,
                u'form_class': DisclosureEmailForm,
                },
            u'refusal': {
                u'template': u'inforequests/actions/refusal-email.html',
                u'email_status': receivedemail.STATUSES.OBLIGEE_ACTION,
                u'action_type': Action.TYPES.REFUSAL,
                u'form_class': RefusalEmailForm,
                },
            }

    try:
        kwargs = available_actions[action]
    except KeyError:
        raise Http404(u'Invalid action.')

    return do_action(**kwargs)

