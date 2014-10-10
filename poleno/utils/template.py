# vim: expandtab
# -*- coding: utf-8 -*-
from os.path import splitext
from django.template.base import TemplateDoesNotExist
from django.template.loader import BaseLoader, find_template_loader
from django.utils.translation import get_language

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

