# vim: expandtab
# -*- coding: utf-8 -*-
import io
from os.path import splitext, join
from inspect import getfullargspec
from functools import partial

from django import template
from django.apps import apps
from django.template import TemplateSyntaxError, TemplateDoesNotExist, RequestContext
from django.template.library import parse_bits
from django.template.loader import render_to_string as django_render_to_string
from django.template.loaders.base import Loader as BaseLoader
from django.utils.translation import get_language

from .http import get_request
from .lazy import lazy_decorator
from .misc import squeeze


def render_to_string(template_name, dictionary=None, context_instance=None, dirs=None):
    request = get_request()
    return django_render_to_string(template_name, dictionary, request=request)

@lazy_decorator(str)
def lazy_render_to_string(*args, **kwargs):
    return render_to_string(*args, **kwargs)

@lazy_decorator(str)
def lazy_squeeze_render_to_string(*args, **kwargs):
    return squeeze(render_to_string(*args, **kwargs))


class TranslationLoader(BaseLoader):
    is_usable = True
    u"""
    Wrapper template loader that takes another template loader and uses it to load templates.
    However, before loading any template the loader tries to load its translated version first. For
    instance if the current language is 'en' and the loader is asked to load template
    'dir/file.html', it tries to load 'dir/file.en.html' first. The original template is loaded
    only if the translated template does not exist.

    The language code is inserted before the last template extenstion. If the template name has no
    extensions, the language code is appended at its end.

    To use this loader together with default Django template loaders set the TEMPLATES loaders
    option in 'settings.py' as follows:

        TEMPLATES = [{
            ...
            'OPTIONS': {
                'loaders': [
                    ('poleno.utils.template.TranslationLoader',
                        'django.template.loaders.filesystem.Loader'),
                    ('poleno.utils.template.TranslationLoader',
                        'django.template.loaders.app_directories.Loader'),
                ],
            },
        }]
    """

    def __init__(self, engine, loader):
        super(TranslationLoader, self).__init__(engine)
        self._loader = loader
        self._cached_loader = None

    @property
    def loader(self):
        # Resolve loader on demand as suggusted in django.template.loaders.cached.Loader
        if not self._cached_loader:
            self._cached_loader = self.engine.find_template_loader(self._loader)
        return self._cached_loader

    def get_template_sources(self, template_name):
        language = get_language()
        template_base, template_ext = splitext(template_name)
        translated_name = '{}.{}{}'.format(template_base, language, template_ext)
        for source in self.loader.get_template_sources(translated_name):
            yield source
        for source in self.loader.get_template_sources(template_name):
            yield source

    def get_contents(self, origin):
        return self.loader.get_contents(origin)

    def get_template(self, template_name, skip=None):
        language = get_language()
        template_base, template_ext = splitext(template_name)
        translated_name = '{}.{}{}'.format(template_base, language, template_ext)
        try:
            return self.loader.get_template(translated_name, skip)
        except TemplateDoesNotExist:
            return self.loader.get_template(template_name, skip)


class AppLoader(BaseLoader):
    is_usable = True
    u"""
    Django template loader that allows you to load a template from a specific application. This
    allows you to both extend and override a template at the same time. The default Django loaders
    require you to copy the entire template you want to override, even if you only want to override
    one small block.

    Template usage example::

        {% extends "admin:admin/base.html" %}

    Settings::

        TEMPLATES = [{
            ...
            'OPTIONS': {
                'loaders': [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                    'poleno.utils.template.AppLoader',
                ],
            },
        }]

    Based on: https://pypi.python.org/pypi/django-apptemplates/
    Which is based on: http://djangosnippets.org/snippets/1376/
    """

    def get_template_sources(self, template_name):
        from django.template import Origin
        if ':' not in template_name:
            return
        app_name, tmpl_name = template_name.split(':', 1)
        for app in apps.get_app_configs():
            if app.label == app_name:
                template_path = join(app.path, 'templates', tmpl_name)
                yield Origin(
                    name=template_path,
                    template_name=template_name,
                    loader=self,
                )

    def get_contents(self, origin):
        try:
            with io.open(origin.name, encoding=self.engine.file_charset) as fp:
                return fp.read()
        except IOError:
            raise TemplateDoesNotExist(origin)


class Library(template.Library):

    def simple_pair_tag(self, func=None, takes_context=None, name=None, lazy_content=None):

        def compiler(parser, token, params, varargs, varkw, defaults,
                name, takes_context, node_class):
            if params[0] == 'content':
                params = params[1:]
            else:
                raise TemplateSyntaxError(
                        u'The first argument of "{}" must be "content"'.format(name))

            bits = token.split_contents()[1:]
            args, kwargs = parse_bits(parser, bits, params, varargs, varkw, defaults,
                    takes_context, name)
            nodelist = parser.parse((u'end' + name,))
            parser.delete_first_token()
            return node_class(takes_context, nodelist, args, kwargs)

        def dec(func):

            class SimplePairNode(template.Node):

                def __init__(self, takes_context, nodelist, args, kwargs):
                    self.takes_context = takes_context
                    self.nodelist = nodelist
                    self.args = args
                    self.kwargs = kwargs

                def render(self, context):
                    resolved_args = [var.resolve(context) for var in self.args]
                    resolved_kwargs = dict((k, v.resolve(context)) for k, v in self.kwargs.items())

                    if lazy_content:
                        content = self.nodelist.render
                    else:
                        content = self.nodelist.render(context)

                    if self.takes_context:
                        return func(content, context, *resolved_args, **resolved_kwargs)
                    else:
                        return func(content, *resolved_args, **resolved_kwargs)

            params, varargs, varkw, defaults = getfullargspec(func)[:4]
            function_name = (name or getattr(func, u'_decorated_function', func).__name__)
            compile_func = partial(compiler, params=params, varargs=varargs, varkw=varkw,
                    defaults=defaults, name=function_name, takes_context=takes_context,
                    node_class=SimplePairNode)
            compile_func.__doc__ = func.__doc__
            self.tag(function_name, compile_func)
            return func

        if func is None:
            # @register.simple_pair_tag(...)
            return dec
        elif callable(func):
            # @register.simple_pair_tag
            return dec(func)
        else:
            raise TemplateSyntaxError(u'Invalid arguments provided to simple_pair_tag')
