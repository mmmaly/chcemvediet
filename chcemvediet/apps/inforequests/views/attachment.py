# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseNotFound
from django.contrib.sessions.models import Session

from poleno.attachments import views as attachments_views
from poleno.attachments.models import Attachment
from poleno.mail.models import Message
from poleno.utils.views import require_ajax, login_required

from chcemvediet.apps.inforequests.models import InforequestDraft, Action, ActionDraft


@require_http_methods([u'POST'])
@require_ajax
@transaction.atomic
@login_required(raise_exception=True)
def attachment_upload(request):
    session = Session.objects.get(session_key=request.session.session_key)
    download_url_func = (lambda a: reverse(u'inforequests:download_attachment', args=(a.pk,)))
    return attachments_views.upload(request, session, download_url_func)

@require_http_methods([u'HEAD', u'GET'])
@login_required(raise_exception=True)
def attachment_download(request, attachment_pk):
    permitted = {
            Session: Q(session_key=request.session.session_key),
            Message: Q(inforequest__applicant=request.user),
            InforequestDraft: Q(applicant=request.user),
            Action: Q(branch__inforequest__applicant=request.user),
            ActionDraft: Q(inforequest__applicant=request.user),
            }

    attachment = Attachment.objects.get_or_404(pk=attachment_pk)
    attached_to_class = attachment.generic_type.model_class()

    try:
        condition = permitted[attached_to_class]
    except KeyError:
        return HttpResponseNotFound()

    try:
        attached_to_class.objects.filter(condition).get(pk=attachment.generic_id)
    except attached_to_class.DoesNotExist:
        return HttpResponseNotFound()

    return attachments_views.download(request, attachment)
