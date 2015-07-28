# vim: expandtab
# -*- coding: utf-8 -*-
from os.path import splitext
from inspect import getargspec
from functools import partial

from django import template
from django.template import TemplateSyntaxError, TemplateDoesNotExist
from django.template.base import parse_bits
from django.template.loader import BaseLoader, find_template_loader, render_to_string
from django.utils.translation import get_language
from django.utils.functional import lazy

from .misc import squeeze


def lazy_render_to_string(*args, **kwargs):
    return lazy(render_to_string, unicode)(*args, **kwargs)

def lazy_squeeze_render_to_string(*args, **kwargs):
    return lazy(squeeze, unicode)(lazy_render_to_string(*args, **kwargs))


class TranslationLoader(BaseLoader):
    u"""
    Wrapper template loader that takes another template loader and uses it to load templates.
    However, before loading any template the loader tries to load its translated version first. For
    instance if the current language is 'en' and the loader is asked to load template
    'dir/file.html', it tries to load 'dir/file.en.html' first. The original template is loaded
    only if the translated template does not exist.

    The language code is inserted before the last template extenstion. If the template name has no
    extensions, the language code is appended at its end.

    To use this loader together with default Django template loaders set TEMPLATE_LOADERS in
    'settings.py' as follows:

        TEMPLATE_LOADERS = (
            ('poleno.utils.template.TranslationLoader', 'django.template.loaders.filesystem.Loader'),
            ('poleno.utils.template.TranslationLoader', 'django.template.loaders.app_directories.Loader'),
        )
    """
    is_usable = True

    def __init__(self, loader):
        super(TranslationLoader, self).__init__()
        self._loader = loader
        self._cached_loader = None

    @property
    def loader(self):
        # Resolve loader on demand as suggusted in django.template.loaders.cached.Loader
        if not self._cached_loader:
            self._cached_loader = find_template_loader(self._loader)
        return self._cached_loader

    def load_template(self, template_name, template_dirs=None):
        language = get_language()
        template_base, template_ext = splitext(template_name)
        try:
            return self.loader(u'%s.%s%s' % (template_base, language, template_ext), template_dirs)
        except TemplateDoesNotExist:
            return self.loader(template_name, template_dirs)


class Library(template.Library):

    def simple_pair_tag(self, func=None, takes_context=None, name=None):

        def compiler(parser, token, params, varargs, varkw, defaults, name, takes_context, node_class):
            if params[0] == 'content':
                params = params[1:]
            else:
                raise TemplateSyntaxError(u'The first argument of "%s" must be "content"' % name)

            bits = token.split_contents()[1:]
            args, kwargs = parse_bits(parser, bits, params, varargs, varkw, defaults, takes_context, name)
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

                def get_resolved_arguments(self, context):
                    resolved_args = [var.resolve(context) for var in self.args]
                    if self.takes_context:
                        resolved_args = [context] + resolved_args
                    resolved_args = [self.nodelist.render(context)] + resolved_args
                    resolved_kwargs = dict((k, v.resolve(context)) for k, v in self.kwargs.items())
                    return resolved_args, resolved_kwargs

                def render(self, context):
                    resolved_args, resolved_kwargs = self.get_resolved_arguments(context)
                    return func(*resolved_args, **resolved_kwargs)

            params, varargs, varkw, defaults = getargspec(func)
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
