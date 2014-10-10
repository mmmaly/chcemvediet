# vim: expandtab
# -*- coding: utf-8 -*-
import os

from django.conf import settings

from poleno.utils.http import JsonResponse, send_file_response

from .models import Attachment

def upload(request, generic_object, download_url_func):
    res = []
    for file in request.FILES.getlist(u'files'):
        attachment = Attachment(
                generic_object=generic_object,
                file=file,
                name=file.name,
                content_type=file.content_type,
                )
        attachment.save()
        res.append({
                u'pk': attachment.pk,
                u'name': attachment.name,
                u'size': attachment.size,
                u'url': download_url_func(attachment),
            })
    return JsonResponse({u'files': res})

def download(request, attachment):
    # FIXME: If ``attachment.content_type`` is among whitelisted content types, we should use it.
    path = os.path.join(settings.MEDIA_ROOT, attachment.file.name)
    return send_file_response(request, path, attachment.name, u'application/octet-stream')
