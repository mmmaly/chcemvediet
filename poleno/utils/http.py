# vim: expandtab
# -*- coding: utf-8 -*-
import os
import stat

from django.http import HttpResponseNotModified, FileResponse
from django.views.static import was_modified_since
from django.utils.http import http_date, urlquote

def send_file_response(request, path, name, content_type):
    # Based on: django.views.static.serve

    # FIXME: If running on real Apache server, we should use "X-SENDFILE" header to let Apache
    # serve the file. It's much faster. Possibly will be fixed in Django 1.8.
    # See: http://django.readthedocs.org/en/latest/ref/request-response.html#django.http.FileResponse

    # FIXME: "Content-Disposition" filename is very fragile if contains non-ASCII characters.
    # Current implementation works on Firefox, but probably fails on other browsers. We should test
    # and fix it for them and/or sanitize and normalize file names.
    statobj = os.stat(path)
    if not stat.S_ISREG(statobj.st_mode):
        raise OSError(u'Not a regular file: %s' % path)
    if not was_modified_since(request.META.get(u'HTTP_IF_MODIFIED_SINCE'), statobj.st_mtime, statobj.st_size):
        return HttpResponseNotModified()
    response = FileResponse(open(path, u'rb'), content_type=content_type)
    response[u'Last-Modified'] = http_date(statobj.st_mtime)
    response[u'Content-Disposition'] = "attachment; filename*=UTF-8''%s" % urlquote(name)
    response[u'Content-Length'] = statobj.st_size
    return response
