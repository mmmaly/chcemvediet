# vim: expandtab
# -*- coding: utf-8 -*-
import os

from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.http import require_http_methods

from poleno.mail.models import Attachment as MailAttachment
from poleno.utils.http import JsonResponse, send_file_response
from poleno.utils.views import require_ajax, login_required

from models import Attachment

@require_http_methods([u'POST'])
@require_ajax
@login_required(raise_exception=True)
def upload(request):
    res = []
    for file in request.FILES.getlist(u'files'):
        attachment = Attachment(
                owner=request.user,
                file=file,
                name=file.name,
                content_type=file.content_type,
                size=file.size,
                )
        attachment.save()
        res.append({
                u'id': attachment.id,
                u'name': attachment.name,
                u'size': attachment.size,
                u'url': reverse(u'attachments:download', args=(attachment.id,)),
            })

    return JsonResponse({u'files': res})

@require_http_methods([u'HEAD', u'GET'])
@login_required
def download(request, attachment_id):
    attachment = Attachment.objects.owned_by(request.user).get_or_404(pk=attachment_id)

    # FIXME: If ``attachment.content_type`` is among whitelisted content types, we should use it.
    path = os.path.join(settings.MEDIA_ROOT, attachment.file.name)
    return send_file_response(request, path, attachment.name, u'application/octet-stream')

@require_http_methods([u'HEAD', u'GET'])
@login_required
def mail_download(request, attachment_id):
    attachment = MailAttachment.objects.filter(message__inforequest__applicant=request.user).distinct().get_or_404(pk=attachment_id)

    # FIXME: If ``attachment.content_type`` is among whitelisted content types, we should use it.
    path = os.path.join(settings.MEDIA_ROOT, attachment.file.name)
    return send_file_response(request, path, attachment.name, u'application/octet-stream')
