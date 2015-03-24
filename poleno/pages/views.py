# vim: expandtab
# -*- coding: utf-8 -*-
import logging

from django.core.urlresolvers import reverse
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.conf import settings
from django.shortcuts import render
from django.utils.translation import get_language

from poleno.utils.http import send_file_response
from poleno.utils.misc import decorate

from .pages import File, Page, InvalidFileError, InvalidPageError

def change_lang(lang, path):
    page = Page(path)
    tranlation = page.translation(lang)

    if tranlation:
        return u'pages:view', dict(path=tranlation.lpath)
    else:
        return u'pages:alternatives', dict(lang=page.lang, path=page.lpath)

@decorate(change_lang=change_lang)
@require_http_methods([u'HEAD', u'GET'])
def view(request, path):
    try:
        page = Page(path)
    except InvalidPageError:
        return HttpResponseNotFound()

    if page.lpath != path:
        logging.getLogger(u'poleno.pages').warning(u'Redirected request: /%s/%s -> /%s%s; Referer: %s',
                page.lang, path, page.lang, page.path, request.META.get(u'HTTP_REFERER', u'--'))

    if page.is_disabled:
        return HttpResponseNotFound()
    if page.lpath != path:
        return HttpResponseRedirect(reverse(u'pages:view', args=[page.lpath]))

    return render(request, u'pages/view.html', {
            u'page': page,
            })

@require_http_methods([u'HEAD', u'GET'])
def alternatives(request, lang, path):
    try:
        page = Page(path, lang)
    except InvalidPageError:
        return HttpResponseNotFound()

    if page.lpath != path:
        logging.getLogger(u'poleno.pages').warning(u'Redirected request: /%s/%s -> /%s%s; Referer: %s',
                lang, path, page.lang, page.path, request.META.get(u'HTTP_REFERER', u'--'))

    if page.is_disabled:
        return HttpResponseNotFound()
    if page.lpath != path:
        return HttpResponseRedirect(reverse(u'pages:alternatives', args=[lang, page.lpath]))

    alts = []
    current_lang = get_language()
    for alt_lang, alt_name in settings.LANGUAGES:
        alt_page = page.translation(alt_lang)
        if not alt_page:
            continue
        if alt_lang == current_lang:
            # And yet the translation is available
            return HttpResponseRedirect(alt_page.url)
        alts.append(dict(lang=alt_lang, name=alt_name, page=alt_page))

    return render(request, u'pages/alternatives.html', {
            u'alternatives': alts,
            })

@require_http_methods([u'HEAD', u'GET'])
def file(request, path, name):
    try:
        page = Page(path)
    except InvalidPageError:
        return HttpResponseNotFound()

    if page.lpath != path:
        logging.getLogger(u'poleno.pages').warning(u'Redirected request: /%s/%s -> /%s%s; Referer: %s',
                page.lang, path, page.lang, page.path, request.META.get(u'HTTP_REFERER', u'--'))

    try:
        file = File(page, name)
    except InvalidFileError:
        return HttpResponseNotFound()

    if page.lpath != path:
        return HttpResponseRedirect(reverse(u'pages:file', args=[page.lpath, name]))

    return send_file_response(request, file.filepath, file.name, file.content_type, attachment=False)
