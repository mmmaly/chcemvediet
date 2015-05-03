# vim: expandtab
# -*- coding: utf-8 -*-
import os
import re

from django.core.files.storage import default_storage
from django.conf import settings
from django.template import Template, TemplateSyntaxError
from django.template.defaulttags import URLNode

from poleno import datacheck

from . import pages

def _check_rec(lang, basedir, rootdir, curdir, autofix):
    filenames = set(os.listdir(curdir))

    # Configuration file
    filename = u'page.conf'
    if filename in filenames:
        filenames.remove(filename)
        filepath = os.path.join(curdir, filename)
        filerel = os.path.relpath(filepath, basedir)
        if not os.path.isfile(filepath) or os.path.islink(filepath):
            yield datacheck.Error(u'Page config /%s is not a regular file', filerel)
        else:
            try:
                config = pages.Config(filepath)
            except pages.ParseConfigError as e:
                yield datacheck.Error(u'Page config /%s parse error: %s', filerel, e)
            else:
                # Check lang_* options
                config_fixes = {}
                for trans_lang, _ in settings.LANGUAGES:
                    trans_key = u'lang_%s' % trans_lang
                    trans_path = config.get(trans_key)
                    if trans_path is not None:
                        try:
                            trans_page = pages.Page(trans_path, trans_lang)
                        except pages.InvalidPageError as e:
                            yield datacheck.Error(u'Page /%s has invalid %s translation: %s', filerel, trans_lang.upper(), e)
                        else:
                            if trans_page.path != trans_path:
                                yield datacheck.Warning(u'Page /%s %s translation is %s but its canonical form is %s',
                                        filerel, trans_lang.upper(), trans_path, trans_page.path, autofixable=True)
                                if autofix:
                                    config_fixes[trans_key] = trans_page.path
                if config_fixes:
                    config.set_multiple(**config_fixes)
                    config.write(filepath)

    # Template file
    filename = u'page.html'
    if filename in filenames:
        filenames.remove(filename)
        filepath = os.path.join(curdir, filename)
        filerel = os.path.relpath(filepath, basedir)
        if not os.path.isfile(filepath) or os.path.islink(filepath):
            yield datacheck.Error(u'Page template /%s is not a regular file', filerel)
        else:
            try:
                with open(filepath) as f:
                    template = f.read()
            except IOError as e:
                yield datacheck.Error(u'Page template /%s read error: %s', filerel, e)
            else:
                try:
                    compiled = Template(template)
                except TemplateSyntaxError as e:
                    yield datacheck.Error(u'Page template /%s parse error: %s', filerel, e)

    # Subpages and redirects
    for filename in list(filenames):
        if pages.slug_regex.match(filename):
            filenames.remove(filename)
            filepath = os.path.join(curdir, filename)
            filerel = os.path.relpath(filepath, basedir)
            if os.path.islink(filepath):
                link = os.readlink(filepath)
                if u'/@/' in link:
                    target = os.path.realpath(os.path.join(rootdir, link.split(u'/@/', 1)[1]))
                else:
                    target = os.path.realpath(os.path.join(curdir, link))
                target_path = target[len(rootdir):] + u'/'
                target_link = os.path.relpath(rootdir, curdir) + u'/@' + target_path
                if not target.startswith(rootdir + os.sep) and target != rootdir:
                    yield datacheck.Error(u'Redirect /%s goes outside root dir %s', filerel, link)
                elif not os.path.isdir(target):
                    yield datacheck.Error(u'Redirect /%s points to %s which expands to %s which is not a directory', filerel, link, target_path)
                elif not pages.path_regex.match(target_path):
                    yield datacheck.Error(u'Redirect /%s points to %s which expands to %s which is not a valid path', filerel, link, target_path)
                elif link != target_link:
                    yield datacheck.Warning(u'Redirect /%s points to %s but its canonical form is %s', filerel, link, target_link, autofixable=True)
                    if autofix:
                        os.remove(filepath)
                        os.symlink(target_link, filepath)
            elif os.path.isdir(filepath):
                for issue in _check_rec(lang, basedir, rootdir, filepath, autofix):
                    yield issue
            else:
                yield datacheck.Error(u'Subpage /%s is not a directory or a symlink', filerel)

    # Rootlinks
    if curdir == rootdir:
        filenames.discard(u'@')
        rootlink = os.path.join(rootdir, u'@')
        if not os.path.islink(rootlink) or os.readlink(rootlink) != u'.':
            yield datacheck.Warning(u'Invalid or missing rootlink /%s/@', lang, autofixable=True)
            if autofix:
                if os.path.lexists(rootlink):
                    os.remove(rootlink)
                os.symlink(u'.', rootlink)

    # Unexpected files
    if filenames:
        dirrel = os.path.relpath(curdir, basedir)
        yield datacheck.Warning(u'Unexpected files in /%s: %s', dirrel, u', '.join(filenames))

@datacheck.register
def check(superficial, autofix):
    u"""
    Checks pages structure and reference integrity.
    """
    # This check is slow. We skip it if running from cron or the user asked for superficial tests
    # only.
    if superficial:
        return

    basedir = os.path.realpath(default_storage.path(u'pages'))
    for lang, _ in settings.LANGUAGES:
        rootdir = os.path.join(basedir, lang)
        if os.path.isdir(rootdir):
            for issue in _check_rec(lang, basedir, rootdir, rootdir, autofix):
                yield issue
