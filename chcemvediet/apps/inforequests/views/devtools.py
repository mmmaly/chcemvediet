# vim: expandtab
# -*- coding: utf-8 -*-
import datetime

from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect
from django.contrib import messages

from poleno.mail.models import Message, Recipient
from poleno.utils.views import login_required
from chcemvediet.apps.inforequests.models import Inforequest, Action


@require_http_methods([u'POST'])
@transaction.atomic
@login_required
def devtools_mock_response(request, inforequest_pk):
    assert settings.DEBUG

    inforequest = (Inforequest.objects
            .owned_by(request.user)
            .get_or_404(pk=inforequest_pk)
            )

    outbound = inforequest.email_set.outbound().order_by_processed().last()
    sender = outbound.recipient_set.first() if outbound else None
    address = (sender.name, sender.mail) if sender else inforequest.main_branch.obligee.emails_parsed[0]
    subject = u'Re: ' + outbound.subject if outbound else u'Mock Response'
    content = request.POST.get(u'content', None) or u'Mock Response'

    email = Message.objects.create(
            type=Message.TYPES.INBOUND,
            processed=None,
            from_name=address[0],
            from_mail=address[1],
            subject=subject,
            text=content,
            )
    recipient = Recipient.objects.create(
            message=email,
            name=inforequest.applicant.get_full_name(),
            mail=inforequest.unique_email,
            type=Recipient.TYPES.TO,
            status=Recipient.STATUSES.INBOUND,
            )

    messages.success(request, u'Mock obligee response queued. It will be processed in a minute or two.')
    return HttpResponseRedirect(reverse(u'inforequests:detail', args=(inforequest.pk,)))

@require_http_methods([u'POST'])
@transaction.atomic
@login_required
def devtools_push_history(request, inforequest_pk):
    assert settings.DEBUG

    inforequest = (Inforequest.objects
            .owned_by(request.user)
            .get_or_404(pk=inforequest_pk)
            )

    try:
        days = int(request.POST[u'days'])
    except (KeyError, ValueError):
        days = 0

    if days >= 1 and days <= 200:
        delta = datetime.timedelta(days=days)
        Inforequest.objects.filter(pk=inforequest.pk).update(
                submission_date=F(u'submission_date') - delta,
                last_undecided_email_reminder=F(u'last_undecided_email_reminder') - delta,
                )
        inforequest.email_set.all().update(
                processed=F(u'processed') - delta,
                )
        Action.objects.filter(branch__inforequest=inforequest).update(
                effective_date=F(u'effective_date') - delta,
                last_deadline_reminder=F(u'last_deadline_reminder') - delta,
                )
        messages.success(request, u'The inforequest was pushed in history by %s days.' % days)
    else:
        messages.error(request, u'Invalid number of days.')

    return HttpResponseRedirect(reverse(u'inforequests:detail', args=(inforequest.pk,)))
