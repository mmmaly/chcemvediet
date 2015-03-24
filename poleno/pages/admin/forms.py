# vim: expandtab
# -*- coding: utf-8 -*-
import datetime

from django import forms
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import format_html, format_html_join
from django.utils.formats import date_format
from django.contrib.staticfiles.storage import staticfiles_storage

from poleno.utils.misc import Bunch, norm_new_lines
from poleno.utils.translation import translation

from .. import pages

class FormSaveError(RuntimeError):
    pass


class FakeField(object):

    def __init__(self, label, text, errors=()):
        self.label = label
        self.text = text
        self.errors = errors
        self.is_hidden = False

    def label_tag(self):
        return format_html(u'<label>{0}:</label>', self.label)

    def __unicode__(self):
        return format_html(u'<div style="margin: 4px 0 0 106px;">{0}</div>', self.text)

class LivePath(FakeField):

    def __init__(self, lang, field):
        super(LivePath, self).__init__(u'    • Details', format_html(
            u'<span class="live-path" data-field="{field}" data-value="{value}" data-url="{url}">{content}</span>',
            field=field.auto_id,
            url=reverse(u'admin:pages_live_path', args=[lang]),
            value=field.value(),
            content=self.render(lang, field.value()),
            ))

    @classmethod
    def _render_ancestors(cls, page):
        return render_to_string(u'pages/admin/snippets/ancestors.html', {
            u'page': page,
            u'inclusive': True,
            })

    @classmethod
    def render(cls, lang, path):
        res = []
        if not path:
            res.append([u'--'])
        else:
            try:
                page = pages.Page(path, lang)
            except pages.InvalidPageError as e:
                res.append([format_html(u'Error: {0}', e)])
            else:
                if page.path != path:
                    res.append([format_html(u'Redirected to: {0}', page.path)])
                res.append([cls._render_ancestors(page)])

        return format_html(u'<span>{0}</span>', format_html_join(u'', u'{0}<br>', res))

class PreviewFileInput(forms.FileInput):

    def render(self, name, value, attrs=None):
        change = super(PreviewFileInput, self).render(name, value, attrs)

        if isinstance(value, pages.File):
            if value.content_type.startswith(u'image/'):
                preview = format_html(u'<a href="{0}"><img src="{0}?{1}" alt="{2}" style="max-width: 500px;"></a>', value.url, value.mtime, value)
            else:
                preview = format_html(u'Current file: <a href="{0}">{1}</a>', value.url, value)
            return format_html(u'<div style="margin-left: 106px;">{1}<br>Change: {0}</div>', change, preview)
        return change


class PageEditForm(forms.Form):
    u"""
                   create  edit      edit     edit
    Fields:       subpage  root  redirect  regular
     -- parent          -     -         -        y
     -- name            y     -         -        y
     -- title           y     y         -        y
     -- label           y     y         -        y
     -- order           y     -         -        y
     -- lang_*          y     -         -        y
     -- redirect        -     -         y        -
     -- disabled        y     y         -        y
     -- raw             y     y         -        y
     -- template        y     y         -        y
    """

    def __init__(self, page, create, *args, **kwargs):
        super(PageEditForm, self).__init__(*args, **kwargs)
        self.page = page
        self.create = create

        edit_root = not create and page.is_root
        edit_redirect = not create and page.is_redirect
        edit_regular = not create and not page.is_root and not page.is_redirect
        assert bool(create) + bool(edit_root) + bool(edit_redirect) + bool(edit_regular) == 1

        self.fieldsets = [
                Bunch(label=None, collapse=False, fields=[]),
                Bunch(label=u'Raw Config', collapse=True, fields=[]),
                Bunch(label=u'Page Content', collapse=False, fields=[]),
                ]

        if edit_regular:
            self.fields[u'parent'] = forms.CharField(
                label=u'URL Path',
                validators=[
                    RegexValidator(pages.path_regex, u'Enter a valid path. It must be an absolute path with respect to the root page starting and ending with a slash.'),
                    ],
                widget=forms.TextInput(attrs={
                    u'class': u'popup-path',
                    u'style': u'width: 50em;',
                    u'data-popup-url': reverse(u'admin:pages_index', args=[page.lang]),
                    u'data-icon': staticfiles_storage.url(u'admin/img/selector-search.gif'),
                    }),
                )
            self.initial[u'parent'] = page.ppath
            self.fieldsets[0].fields.append(self[u'parent'])
            self.fieldsets[0].fields.append(LivePath(page.lang, self[u'parent']))
        else:
            self.fieldsets[0].fields.append(FakeField(u'URL Path', page.path))

        if create or edit_regular:
            self.fields[u'name'] = forms.CharField(
                label=u'URL Name',
                validators=[
                    RegexValidator(pages.slug_regex, u'Enter a valid slug. Only letters, numbers and dashes are allowed.'),
                    ],
                )
            if not create:
                self.initial[u'name'] = page.name
            self.fieldsets[0].fields.append(self[u'name'])

        if create or edit_root or edit_regular:
            self.fields[u'title'] = forms.CharField(
                label=u'Page Title',
                required=False,
                widget=forms.TextInput(attrs={
                    u'style': u'width: 50em;',
                    }),
                )
            if not create:
                self.initial[u'title'] = page._config.get(u'title')
            self.fieldsets[0].fields.append(self[u'title'])

        if create or edit_root or edit_regular:
            self.fields[u'label'] = forms.CharField(
                label=u'Menu Label',
                required=False,
                )
            if not create:
                self.initial[u'label'] = page._config.get(u'label')
            self.fieldsets[0].fields.append(self[u'label'])

        if create or edit_regular:
            self.fields[u'order'] = forms.CharField(
                label=u'Sort Key',
                required=False,
                )
            if not create:
                self.initial[u'order'] = page._config.get(u'order')
            self.fieldsets[0].fields.append(self[u'order'])

        if create or edit_regular:
            for lang, _ in settings.LANGUAGES:
                if lang != page.lang:
                    key = u'lang_%s' % lang
                    self.fields[key] = forms.CharField(
                        label=u'Translation %s' % lang.upper(),
                        required=False,
                        validators=[
                            RegexValidator(pages.path_regex, u'Enter a valid path. It must be an absolute path with respect to the root page starting and ending with a slash.'),
                            ],
                        widget=forms.TextInput(attrs={
                            u'class': u'popup-path',
                            u'style': u'width: 50em;',
                            u'data-popup-url': reverse(u'admin:pages_index', args=[lang]),
                            u'data-icon': staticfiles_storage.url(u'admin/img/selector-search.gif'),
                            }),
                        )
                    if not create:
                        self.initial[key] = page._config.get(key)
                    self.fieldsets[0].fields.append(self[key])
                    self.fieldsets[0].fields.append(LivePath(lang, self[key]))

        if edit_redirect:
            self.fields[u'redirect'] = forms.CharField(
                label=u'Redirect',
                validators=[
                    RegexValidator(pages.path_regex, u'Enter a valid path. It must be an absolute path with respect to the root page starting and ending with a slash.'),
                    ],
                widget=forms.TextInput(attrs={
                    u'class': u'popup-path',
                    u'style': u'width: 50em;',
                    u'data-popup-url': reverse(u'admin:pages_index', args=[page.lang]),
                    u'data-icon': staticfiles_storage.url(u'admin/img/selector-search.gif'),
                    }),
                )
            self.initial[u'redirect'] = page.redirect_path
            self.fieldsets[0].fields.append(self[u'redirect'])
            self.fieldsets[0].fields.append(LivePath(page.lang, self[u'redirect']))

        if create or edit_root or edit_regular:
            self.fields[u'disabled'] = forms.BooleanField(
                label=u'Disabled',
                required=False,
                )
            if not create:
                self.initial[u'disabled'] = bool(page._config.get(u'disabled'))
            self.fieldsets[0].fields.append(self[u'disabled'])

        if create or edit_root or edit_regular:
            self.fields[u'raw'] = forms.CharField(
                label=u'',
                required=False,
                widget=forms.Textarea(attrs={
                    u'style': u'width: 100%; height: 10em;',
                    }),
                )
            if not create:
                self.initial[u'raw'] = page.raw_config
            self.fieldsets[1].fields.append(self[u'raw'])

        if create or edit_root or edit_regular:
            with translation(page.lang):
                url = reverse(u'admin:pages_preview')
            self.fields[u'template'] = forms.CharField(
                label=u'',
                required=False,
                widget=forms.Textarea(attrs={
                    u'class': u'template-widget',
                    u'data-url': url,
                    }),
                )
            if not create:
                self.initial[u'template'] = page.template
            self.fieldsets[2].fields.append(self[u'template'])

    def save(self):
        page = self.page
        create = self.create

        config = {}

        # String config options
        keys = [u'title', u'label', u'order'] + [u'lang_%s' % l for l, _ in settings.LANGUAGES]
        for key in keys:
            if key in self.fields:
                old_value = page._config.get(key) if not create else None
                new_value = self.cleaned_data[key] or None
                if new_value != old_value:
                    config[key] = new_value

        # Boolean config options
        keys = [u'disabled']
        for key in keys:
            if key in self.fields:
                old_value = page._config.get(key) if not create else None
                new_value = key if self.cleaned_data[key] else None
                if new_value != old_value:
                    config[key] = new_value

        if u'raw_config' in self.fields:
            old_raw = page.raw_config if not create else u''
            new_raw = norm_new_lines(self.cleaned_data[u'raw'])
            if new_raw != old_raw:
                config[u'raw_config'] = new_raw

        if u'template' in self.fields:
            template = norm_new_lines(self.cleaned_data[u'template'] or None)

        try:
            if create:
                name = self.cleaned_data[u'name']
                return page.create_subpage(name, template, **config)

            if page.is_redirect:
                redirect = self.cleaned_data[u'redirect']
                if redirect != page.redirect_path:
                    page.save_redirect(redirect)
                return page

            if config:
                page.save_config(**config)

            if template != page.template:
                page.save_template(template)

            if not page.is_root:
                parent = pages.Page(self.cleaned_data[u'parent'], page.lang)
                name = self.cleaned_data[u'name']
                if parent.path + name + u'/' != page.path:
                    return page.move(parent, name)

            return page

        except pages.ParseConfigError as e:
            self._add_save_error(u'raw', e)
        except pages.SetConfigError as e:
            self._add_save_error(e.key, e)
        except (pages.InvalidPageError, pages.PageParentError) as e:
            self._add_save_error(u'parent', e)
        except pages.PageNameError as e:
            self._add_save_error(u'name', e)
        except pages.PageRedirectError as e:
            self._add_save_error(u'redirect', e)
        except pages.PageError as e:
            self._add_save_error(None, e)
        raise FormSaveError

    def _add_save_error(self, field, e):
        self.add_error(field if field in self.fields else None, u'%s' % e)

class FileEditForm(forms.Form):
    u"""
    Fields:
     -- name
     -- content
    """

    def __init__(self, page, file, create, *args, **kwargs):
        super(FileEditForm, self).__init__(*args, **kwargs)
        self.page = page
        self.file = file
        self.create = create

        self.fieldsets = [
                Bunch(label=None, collapse=False, fields=[]),
                ]

        self.fieldsets[0].fields.append(FakeField(u'Page', LivePath.render(page.lang, page.path)))

        self.fields[u'name'] = forms.CharField(
            label=u'File Name',
            validators=[
                RegexValidator(pages.file_regex, u'Enter a valid file name. Only letters, numbers, dashes and dots are allowed.'),
                ],
            )
        if not create:
            self.initial[u'name'] = file.name
        self.fieldsets[0].fields.append(self[u'name'])

        if not create:
            self.fieldsets[0].fields.append(FakeField(u'Content Type', file.content_type))
            self.fieldsets[0].fields.append(FakeField(u'Modified',
                date_format(datetime.datetime.fromtimestamp(file.mtime), u'DATETIME_FORMAT')))

        self.fields[u'content'] = forms.FileField(
            label=u'Content',
            widget=PreviewFileInput,
            )
        if not create:
            self.initial[u'content'] = file
        self.fieldsets[0].fields.append(self[u'content'])

    def save(self):
        name = self.cleaned_data[u'name']
        content = self.cleaned_data[u'content']
        try:
            if self.create:
                return self.page.create_file(name, content)
            if isinstance(content, UploadedFile):
                self.file.save_content(content)
            if name != self.file.name:
                return self.file.rename(name)
            return self.file

        except pages.FileNameError as e:
            self._add_save_error(u'name', e)
        except pages.FileError as e:
            self._add_save_error(None, e)
        raise FormSaveError

    def _add_save_error(self, field, e):
        self.add_error(field if field in self.fields else None, u'%s' % e)
