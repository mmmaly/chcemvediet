# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, HttpResponseRedirect
from django.template import Template, Context
from django.shortcuts import render
from django.contrib import admin

from poleno.utils.forms import clean_button

from . import forms
from ..pages import File, Page, InvalidFileError, InvalidPageError, PageOrigin
from ..urls import urlparams

@admin.site.register_view(u'pages/index/', urlname=u'pages_languages', visible=False)
@require_http_methods([u'HEAD', u'GET'])
def languages(request):
    return render(request, u'pages/admin/languages.html', {
            u'title': u'Select pages language',
            })

@admin.site.register_view(u'pages/index/{lang}/'.format(**urlparams), urlname=u'pages_index', visible=False)
@require_http_methods([u'HEAD', u'GET'])
def index(request, lang):
    pages = Page(u'/', lang).walk()

    return render(request, u'pages/admin/index.html', {
            u'is_popup': request.GET.get(u'popup', False),
            u'popup_target': request.GET.get(u'target', None),
            u'title': u'Select page to change (%s)' % lang.upper(),
            u'lang': lang,
            u'pages': pages,
            })

@require_http_methods([u'HEAD', u'GET', u'POST'])
def create_or_edit(request, lang, path, create):
    u"""
    If ``create`` is False, then ``path`` should point to the page we want to edit. If ``create``
    is True, then ``path`` should point to the page that will be the parent of the new page.
    """
    try:
        page = Page(path, lang, keep_last=True)
    except InvalidPageError:
        return HttpResponseNotFound()
    if page.lpath != path:
        return HttpResponseNotFound()
    if create and page.is_redirect:
        return HttpResponseNotFound()

    if request.method == u'POST':
        button = clean_button(request.POST, [u'save', u'save-and-continue'])

        if button in [u'save', u'save-and-continue']:
            form = forms.PageEditForm(page, create, request.POST)
            if form.is_valid():
                try:
                    new_page = form.save()
                except forms.FormSaveError:
                    pass
                else:
                    if button == u'save':
                        return HttpResponseRedirect(reverse(u'admin:pages_index', args=[lang]))
                    else: # save-and-continue
                        return HttpResponseRedirect(reverse(u'admin:pages_edit', args=[lang, new_page.lpath]))

        else: # Invalid button
            return HttpResponseBadRequest()

    else: # GET
        form = forms.PageEditForm(page, create)

    return render(request, u'pages/admin/edit.html', {
            u'title': u'Add Page' if create else u'Edit Page',
            u'create': create,
            u'lang': lang,
            u'page': page,
            u'form': form,
            })

@admin.site.register_view(u'pages/edit/{lang}/{path}'.format(**urlparams), urlname=u'pages_edit', visible=False)
def edit(request, lang, path):
    return create_or_edit(request, lang, path, create=False)

@admin.site.register_view(u'pages/create/{lang}/{path}'.format(**urlparams), urlname=u'pages_create', visible=False)
def create(request, lang, path):
    return create_or_edit(request, lang, path, create=True)

@admin.site.register_view(u'pages/delete/{lang}/{path}'.format(**urlparams), urlname=u'pages_delete', visible=False)
@require_http_methods([u'HEAD', u'GET', u'POST'])
def delete(request, lang, path):
    try:
        page = Page(path, lang, keep_last=True)
    except InvalidPageError:
        return HttpResponseNotFound()
    if page.lpath != path:
        return HttpResponseNotFound()
    if page.is_root:
        return HttpResponseNotFound()

    if request.method == u'POST':
        button = clean_button(request.POST, [u'delete'])

        if button == u'delete':
            page.delete()
            return HttpResponseRedirect(reverse(u'admin:pages_index', args=[lang]))

        else: # Invalid button
            return HttpResponseBadRequest()

    return render(request, u'pages/admin/delete.html', {
            u'title': u'Delete Page',
            u'lang': lang,
            u'page': page,
            })

@admin.site.register_view(u'pages/live_path/{lang}/'.format(**urlparams), urlname=u'pages_live_path', visible=False)
@require_http_methods([u'HEAD', u'GET'])
def live_path(request, lang):
    path = request.GET.get(u'path', None)
    res = forms.LivePath.render(lang, path)
    return HttpResponse(res)

@admin.site.register_view(u'pages/preview/', urlname=u'pages_preview', visible=False)
@require_http_methods([u'POST'])
def preview(request):
    template = request.POST[u'template']
    origin = PageOrigin(template, u'<input>')
    return render(request, u'pages/admin/preview.html', {
            u'content': Template(template, origin).render(Context({})),
            })

@require_http_methods([u'HEAD', u'GET', u'POST'])
def file_create_or_edit(request, lang, path, name, create):
    u"""
    If ``create`` is False, then ``name`` should point to the page file we want to edit. If
    ``create`` is True, then ``name`` is ignored.
    """
    try:
        page = Page(path, lang)
    except InvalidPageError:
        return HttpResponseNotFound()
    if page.lpath != path:
        return HttpResponseNotFound()

    try:
        file = File(page, name) if not create else None
    except InvalidFileError:
        return HttpResponseNotFound()

    if request.method == u'POST':
        button = clean_button(request.POST, [u'save', u'save-and-continue'])

        if button in [u'save', u'save-and-continue']:
            form = forms.FileEditForm(page, file, create, request.POST, request.FILES)
            if form.is_valid():
                try:
                    new_file = form.save()
                except forms.FormSaveError:
                    pass
                else:
                    if button == u'save':
                        return HttpResponseRedirect(reverse(u'admin:pages_edit', args=[lang, page.lpath]))
                    else: # save-and-continue
                        return HttpResponseRedirect(reverse(u'admin:pages_file_edit', args=[lang, page.lpath, new_file.name]))

        else: # Invalid button
            return HttpResponseBadRequest()

    else: # GET
        form = forms.FileEditForm(page, file, create)

    return render(request, u'pages/admin/file_edit.html', {
            u'title': u'Add Page Attachment' if create else u'Edit Page Attachment',
            u'create': create,
            u'lang': lang,
            u'page': page,
            u'file': file,
            u'form': form,
            })

@admin.site.register_view(u'pages/file/edit/{lang}/{path}{name}'.format(**urlparams), urlname=u'pages_file_edit', visible=False)
def file_edit(request, lang, path, name):
    return file_create_or_edit(request, lang, path, name, create=False)

@admin.site.register_view(u'pages/file/create/{lang}/{path}'.format(**urlparams), urlname=u'pages_file_create', visible=False)
def file_create(request, lang, path):
    return file_create_or_edit(request, lang, path, None, create=True)

@admin.site.register_view(u'pages/file/delete/{lang}/{path}{name}'.format(**urlparams), urlname=u'pages_file_delete', visible=False)
@require_http_methods([u'HEAD', u'GET', u'POST'])
def file_delete(request, lang, path, name):
    try:
        page = Page(path, lang)
    except InvalidPageError:
        return HttpResponseNotFound()
    if page.lpath != path:
        return HttpResponseNotFound()

    try:
        file = File(page, name)
    except InvalidFileError:
        return HttpResponseNotFound()

    if request.method == u'POST':
        button = clean_button(request.POST, [u'delete'])

        if button == u'delete':
            file.delete()
            return HttpResponseRedirect(reverse(u'admin:pages_edit', args=[lang, page.lpath]))

        else: # Invalid button
            return HttpResponseBadRequest()

    return render(request, u'pages/admin/file_delete.html', {
            u'title': u'Delete Page Attachment',
            u'lang': lang,
            u'page': page,
            u'file': file,
            })
