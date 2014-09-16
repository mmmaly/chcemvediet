# vim: expandtab
# -*- coding: utf-8 -*-
import os
import stat

from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.static import was_modified_since
from django.http import HttpResponseNotModified, CompatibleStreamingHttpResponse
from django.utils.http import http_date, urlquote

from poleno.utils.http import JsonResponse
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
def download(request, attachment_id):
    attachment = Attachment.objects.owned_by(request.user).get_or_404(pk=attachment_id)

    # FIXME: If running on real Apache server, we should use "X-SENDFILE" header to let Apache
    # server the file. It's much faster.

    # FIXME: "Content-Disposition" filename is very fragile if contains non-ASCII characters.
    # Current implementation works on Firefox, but probably fails on other browsers. We should test
    # and fix it for them and/or sanitize and normalize file names.

    # Based on: django.views.static.serve
    fullpath = os.path.join(settings.MEDIA_ROOT, attachment.file.name)
    statobj = os.stat(fullpath)
    if not was_modified_since(request.META.get(u'HTTP_IF_MODIFIED_SINCE'), statobj.st_mtime, statobj.st_size):
        return HttpResponseNotModified()
    response = CompatibleStreamingHttpResponse(open(fullpath, u'rb'), content_type=u'application/octet-stream')
    response[u'Last-Modified'] = http_date(statobj.st_mtime)
    response[u'Content-Disposition'] = "attachment; filename*=UTF-8''%s" % urlquote(attachment.name)
    if stat.S_ISREG(statobj.st_mode):
        response[u'Content-Length'] = statobj.st_size
    return response
