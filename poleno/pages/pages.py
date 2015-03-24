# vim: expandtab
# -*- coding: utf-8 -*-
import os
import re
import shutil
import functools
import collections
import codecs
import logging
import mimetypes

from django.core.urlresolvers import reverse
from django.core.files.storage import default_storage
from django.template import Context, Template, Origin
from django.utils.functional import cached_property
from django.utils.translation import get_language

from poleno.utils.translation import translation

path_regex = re.compile(r'^/(?:[a-z0-9]+(?:-[a-z0-9]+)*/)*$')
slug_regex = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
file_regex = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*(?:[.][a-z0-9]+)+$')

class FileError(Exception):
    pass

class InvalidFileError(FileError):
    pass

class FileNameError(FileError):
    pass

class PageError(Exception):
    pass

class ParseConfigError(PageError):
    pass

class SetConfigError(PageError):
    def __init__(self, *args, **kwargs):
        self.key = kwargs.pop(u'key', None)
        super(PageError, self).__init__(*args, **kwargs)

class InvalidPageError(PageError):
    pass

class PageNameError(PageError):
    pass

class PageParentError(PageError):
    pass

class PageRedirectError(PageError):
    pass


class Config(object):

    def __init__(self, confpath=None):
        self._config = collections.OrderedDict()
        if confpath:
            self.read(confpath)

    def read(self, confpath):
        with codecs.open(confpath, u'rb', u'utf-8') as f:
            data = f.read()
        self.read_from_string(data)

    def write(self, confpath):
        data = self.write_to_string()
        with codecs.open(confpath, u'wb', u'utf-8') as f:
            f.write(data)

    def read_from_string(self, data):
        res = collections.OrderedDict()
        for idx, line in enumerate(data.splitlines()):
            if line == u'' or line.isspace() or line.startswith(u'#'):
                res[idx] = line
            else:
                try:
                    key, val = line.split(u'=', 1)
                except ValueError:
                    raise ParseConfigError(u'Parse error on line %d: "%s"' % (idx, line))
                key = key.strip()
                if not key:
                    raise ParseConfigError(u'Parse error on line %d: "%s"' % (idx, line))
                res[key] = val.strip()
        self._config = res

    def write_to_string(self):
        res = []
        for key, val in self._config.items():
            if not isinstance(key, basestring):
                res.append(u'%s\n' % val)
            elif val is not None:
                res.append(u'%s = %s\n' % (key, val))
        return u''.join(res)

    def get(self, key, default=None):
        res = self._config.get(key, None)
        return default if res is None else res

    def set(self, key, value):
        if not isinstance(key, basestring):
            raise SetConfigError(u'Key must be a string.', key=key)
        if u'\n' in key or u'\r' in key:
            raise SetConfigError(u'Key may not contain linebreaks.', key=key)
        if value is not None and (u'\n' in value or u'\r' in value):
            raise SetConfigError(u'Value may not contain linebreaks.', key=key)
        self._config[key] = value

    def set_multiple(self, **entries):
        for key, val in entries.items():
            self.set(key, val)

class PageOrigin(Origin):

    def __init__(self, source, path):
        super(PageOrigin, self).__init__(path)
        self.source = source

    def reload(self):
        return self.source

def fix_slashes(path):
    if not path.startswith(u'/'):
        path = u'/' + path
    if not path.endswith(u'/'):
        path = path + u'/'
    return path


@functools.total_ordering
class File(object):
    u"""
    Represents a file attached to a page. A file named "foo.ext" is stored in "foo.ext" file in the
    page "_files/" directory.
    """

    ##########
    # Magic methods
    ##########

    def __init__(self, page, name):
        if not file_regex.match(name):
            raise InvalidFileError(u'Invalid file name: %s' % name)

        filesdir = os.path.join(page._pagedir, u'_files')
        filepath = os.path.join(filesdir, name)
        if not os.path.exists(filepath):
            raise InvalidFileError(u'Page %s has no file: %s' % (page.path, name))
        if not os.path.isfile(filepath):
            raise InvalidFileError(u'Page %s file "%s" is not a regular file' % (page.path, name))

        # Private properties
        self._page = page
        self._name = name
        self._filesdir = filesdir
        self._filepath = filepath

    def __eq__(self, other):
        if isinstance(other, File):
            return self._page == other._page and self._name == other._name
        else:
            return NotImplemented

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        u"""
        Note that you can sort files attached to the same page. If you try to sort pages that belog
        to different pages, they will mix together.
        """
        if isinstance(other, File):
            return self._name < other._name
        else:
            return NotImplemented

    def __unicode__(self):
        return self._name

    ##########
    # Public properties
    ##########

    @property
    def page(self):
        return self._page

    @property
    def name(self):
        return self._name

    @cached_property
    def content_type(self):
        return mimetypes.guess_type(self._name)[0] or u'application/octet-stream'

    @cached_property
    def mtime(self):
        return os.stat(self._filepath).st_mtime

    @property
    def filepath(self):
        return self._filepath

    @cached_property
    def url(self):
        with translation(self._page._lang):
            return reverse(u'pages:file', args=[self._page.lpath, self._name])

    @cached_property
    def content(self):
        try:
            with open(self._filepath, u'rb') as f:
                return f.read()
        except IOError:
            return None

    ##########
    # Mutable public methods
    ##########

    def delete(self):
        os.remove(self._filepath)
        try:
            os.rmdir(self._filesdir)
        except OSError:
            pass

    def rename(self, name):
        if not file_regex.match(name):
            raise FileNameError(u'Invalid target file name: %s' % name)

        filepath = os.path.join(self._filesdir, name)
        if os.path.lexists(filepath):
            raise FileNameError(u'Target file already exists: %s' % name)

        os.rename(self._filepath, filepath)
        return File(self._page, name)

    def save_content(self, content):
        tmp = self._filepath + u'.tmp~'
        try:
            with open(tmp, u'wb') as f:
                for chunk in content.chunks():
                    f.write(chunk)
            os.rename(tmp, self._filepath)
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass

@functools.total_ordering
class Page(object):
    u"""
    Represents a page or a redirect to a page. A page named "foo" is defined with "foo/" directory
    inside its parent page. The page directory may contain "page.conf" file with the page
    configuration, "page.html" file with its template and any number of subdirectories with
    subpages. Further, every page directory must contain a symlink "_root" pointing to its parent
    page "_root" symlink which is pointing to the root page directory, eventually. Page name may
    contain only dashes, numbers and lowercase ascii letters. It may not contain two consecutive
    dashes nor begin or end with a dash.

    Redirect represents a permalink to a new page location if the page was moved or renamed.
    A redirect named "foo" is defined with "foo" symlink inside its parent page pointing to the
    target page directory or to another redirection symlink. Redirects do not have any
    configurations, templates, nor subpages. Redirects are absolute with respect to the root page.
    Every redirect symlink must begin with "_root/" and end with a slash.

    The page configuration file contains a list of page options. All options are optional.
    Supported options:
     -- title = <string>
            Page title. Defaults to the capitalized page name.
     -- label = <string>
            Shorter page name used in menus. Same as title if ommited.
     -- order = <string>
            Defines the page order among its siblings. Defaults to the page name. The order for the
            root page is ignored. Redirects are ordered by their names and are put after regular
            pages.
     -- lang_xx = <path>
            Path to a translation page, where "xx" is the target language code. The path to the
            translation page is always an absolute path with respect to the target language root
            page starting and ending with a slash. Any translations defined for the root page are
            ignored. The translations of the root page are always the respective root pages.
     -- disabled = 'disabled'
            Marks that the page is disabled. Disabled pages are invisible to public, however, the
            admin may enable them again. Note that disabled pages may contain subpages that are not
            disabled.

    The page html file contains Django template which defines the page content. The template may
    use all Django template tags and template context. Moreover, ``page`` variable with the current
    Page object is passed to the template when rendering it.

    Note that internal page state is cached and it should be manually refetched if anything changes
    in the page structure. In particular, mutable methods may invalidate any current ``Page``
    instance.
    """

    ##########
    # Private methods
    ##########

    def _resolve_path(self, rootdir, path):
        pagedir = os.path.realpath(rootdir + path)

        if not pagedir.startswith(rootdir + os.sep) and pagedir != rootdir:
            raise InvalidPageError(u'Redirected outside root dir.')
        if not os.path.exists(pagedir):
            raise InvalidPageError(u'Page does not exist: /%s' % os.path.relpath(pagedir, rootdir))
        if not os.path.isdir(pagedir):
            raise InvalidPageError(u'Not a directory: /%s' % os.path.relpath(pagedir, rootdir))

        realpath = pagedir[len(rootdir):] + u'/'

        if not path_regex.match(realpath):
            raise InvalidPageError(u'Redirected to an invalid path: %s' % realpath)

        return realpath, pagedir

    def _read_conf_file(self, pagedir):
        conffile = os.path.join(pagedir, u'page.conf')
        try:
            if os.path.isfile(conffile):
                return Config(conffile)
            else:
                return Config()
        except (IOError, PageError) as e:
            raise InvalidPageError(e)

    def _read_symlink(self, pagedir):
        link = os.readlink(pagedir)
        if u'/@/' not in link:
            raise InvalidPageError(u'Invalid redirect: %s' % link)

        redirect = u'/' + link.split(u'/@/', 1)[1]
        if not path_regex.match(redirect):
            raise InvalidPageError(u'Invalid redirect: %s' % link)

        return redirect

    def _fix_redirects(self, pagedir):
        stack = [pagedir]
        while stack:
            curdir = stack.pop()
            for filename in os.listdir(curdir):
                if slug_regex.match(filename):
                    filepath = os.path.join(curdir, filename)
                    if os.path.islink(filepath):
                        link = os.readlink(pagedir)
                        if u'/@/' in link:
                            new_link = os.path.relpath(self._rootdir, curdir) + u'/@/' + link.split(u'/@/', 1)[1]
                            if new_link != link:
                                os.remove(pagedir)
                                os.symlink(new_link, pagedir)
                    elif os.path.isdir(filepath):
                        stack.append(filepath)

    ##########
    # Magic methods
    ##########

    def __init__(self, path, lang=None, keep_last=False):
        u"""
        Returns the page on ``path`` recursively expanding all redirects. If ``keep_last`` is True,
        the last path component is not expanded and returned as is even if it is a redirect.
        Usefull if we want to get the redirect object itself. The path in an absolute path but does
        not have to start or end with a slash, the slashes are added as needed. Use ``warning`` to
        log a warning if the page is redirected.
        """
        lang = lang or get_language()
        path = _path = fix_slashes(path)
        if not path_regex.match(path):
            raise InvalidPageError(u'Invalid path: %s' % path)

        rootdir = os.path.realpath(default_storage.path(u'pages/' + lang))
        if not os.path.lexists(rootdir):
            os.makedirs(rootdir)
            os.symlink(u'.', os.path.join(rootdir, u'@'))

        isroot = (path == u'/')
        if keep_last and not isroot and os.path.islink(rootdir + path.rstrip(u'/')):
            name = path.rsplit(u'/', 2)[-2]
            ppath = path[:-len(name)-1]
            ppath, ppagedir = self._resolve_path(rootdir, ppath)
            path = ppath + name + u'/'
            pagedir = os.path.join(ppagedir, name)
            config = None
            redirect = self._read_symlink(pagedir)
        else:
            path, pagedir = self._resolve_path(rootdir, path)
            name = path.rsplit(u'/', 2)[-2]
            ppath = path[:-len(name)-1]
            isroot = (path == u'/')
            config = self._read_conf_file(pagedir)
            redirect = None

        # Private properties
        self._lang = lang
        self._path = path
        self._ppath = ppath
        self._name = name
        self._isroot = isroot
        self._pagedir = pagedir    # os path to the page dir/symlink
        self._rootdir = rootdir    # os path to the root page dir
        self._config = config      # None iff redirect
        self._redirect = redirect  # None iff not redirect

    def __eq__(self, other):
        if isinstance(other, Page):
            return self._lang == other._lang and self._path == other._path
        else:
            return NotImplemented

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        u"""
        Note that you can sort only siblings. If you try to sort pages that are not siblings they
        will mix together.
        """
        if isinstance(other, Page):
            return self.order < other.order
        else:
            return NotImplemented

    ##########
    # Tree traversal
    ##########

    @cached_property
    def parent(self):
        if self._isroot:
            return None
        return Page(self._ppath, self._lang)

    @cached_property
    def ancestors(self):
        res = []
        ancestor = self.parent
        while ancestor is not None:
            res.append(ancestor)
            ancestor = ancestor.parent
        res.reverse()
        return res

    @cached_property
    def subpages(self):
        if not os.path.isdir(self._pagedir) or os.path.islink(self._pagedir):
            return []

        res = []
        for file in os.listdir(self._pagedir):
            path = os.path.join(self._pagedir, file)
            if os.path.isdir(path) or os.path.islink(path):
                if slug_regex.match(file):
                    try:
                        res.append(self.subpage(file))
                    except InvalidPageError as e:
                        logging.getLogger(u'poleno.pages').error(u'Page /%s%s%s/ is broken: %s', self._lang, self._path, file, e)
        res.sort()
        return res

    def subpage(self, name):
        return Page(self._path + name + u'/', self._lang, keep_last=True)

    def walk(self):
        stack = [self]
        while stack:
            page = stack.pop()
            yield page
            stack.extend(reversed(page.subpages))

    ##########
    # is_* properties
    ##########

    @property
    def is_root(self):
        return self._isroot

    @property
    def is_redirect(self):
        return self._redirect is not None

    @cached_property
    def is_disabled(self):
        if self._config is None:
            return None
        return self._config.get(u'disabled') is not None

    ##########
    # Other public properties
    ##########

    @property
    def lang(self):
        return self._lang

    @property
    def path(self):
        return self._path

    @property
    def ppath(self):
        return self._ppath

    @property
    def lpath(self):
        u""" Path with the leftmost slash stripped. """
        return self._path.lstrip(u'/')

    @property
    def lppath(self):
        u""" Parent path with the leftmost slash stripped. """
        return self._ppath.lstrip(u'/')

    @property
    def name(self):
        return self._name

    @cached_property
    def url(self):
        with translation(self._lang):
            return reverse(u'pages:view', args=[self.lpath])

    @cached_property
    def level(self):
        return self._path.count(u'/') - 1

    @cached_property
    def title(self):
        if self._config is None:
            return None
        return self._config.get(u'title') or self._name.replace(u'-', u' ').capitalize() or u'(unnamed)'

    @cached_property
    def label(self):
        if self._config is None:
            return None
        return self._config.get(u'label') or self.title

    @cached_property
    def order(self):
        if self._config is None:
            return u'~' + self._name
        return self._config.get(u'order') or self._name

    @property
    def redirect_path(self):
        return self._redirect

    @cached_property
    def raw_config(self):
        if self._config is None:
            return None
        return self._config.write_to_string()

    @cached_property
    def template(self):
        if self._redirect is not None:
            return None

        try:
            with open(os.path.join(self._pagedir, u'page.html'), u'rb') as f:
                return f.read()
        except IOError:
            return None

    ##########
    # Non-mutable public methods
    ##########

    def translation_path(self, lang):
        if self._isroot:
            return u'/'
        if self._config is None:
            return None
        return self._config.get(u'lang_%s' % lang)

    def translation(self, lang):
        if lang == self._lang:
            return self
        path = self.translation_path(lang)
        if not path:
            return None
        page = Page(path, lang)
        if page.path != path:
            logging.getLogger(u'poleno.pages').warning(u'Page /%s%s has redirected translation: /%s%s -> /%s%s',
                    self._lang, self._path, lang, fix_slashes(path), page.lang, page.path)

    def render(self):
        if self.template:
            origin = PageOrigin(self.template, self._path)
            return Template(self.template, origin).render(Context({
                u'page': self,
                }))
        else:
            return u''

    ##########
    # Mutable public methods
    ##########

    def delete(self):
        if self._isroot:
            raise PageError(u'Root page may not be deleted.')

        if self._redirect is None:
            shutil.rmtree(self._pagedir)
        else:
            os.remove(self._pagedir)

    def create_subpage(self, name, template=None, raw_config=None, **entries):
        if self._redirect is not None:
            raise PageError(u'Redirects may not have subpages.')
        if not slug_regex.match(name):
            raise PageNameError(u'Invalid page name: "%s"' % name)
        if raw_config is not None and entries:
            raise ParseConfigError(u'Cannot set raw config and individual options at the same time.')

        path = self._path + name + u'/'
        pagedir = os.path.join(self._pagedir, name)

        if os.path.lexists(pagedir):
            raise PageNameError(u'Target page already exists: %s' % path)

        os.mkdir(pagedir)

        config = Config()
        if raw_config is not None:
            config.read_from_string(raw_config)
        else:
            config.set_multiple(**entries)
        config.write(os.path.join(pagedir, u'page.conf'))

        if template is not None:
            with open(os.path.join(pagedir, u'page.html'), u'wb') as f:
                f.write(template)

        return Page(path, self._lang)

    def move(self, parent, name):
        if self._isroot:
            raise PageError(u'Root page may not be moved.')
        if self._redirect is not None:
            raise PageError(u'Moving redirects makes no sense.')
        if self._lang != parent._lang:
            raise PageError(u'Cannot move between pages in different languages.')
        if parent._redirect is not None:
            raise PageParentError(u'Redirects may not have subpages.')
        if parent._path.startswith(self._path):
            raise PageParentError(u'Cannot move the page to a subpage of itself.')
        if not slug_regex.match(name):
            raise PageNameError(u'Invalid target name: "%s"' % name)

        path = parent._path + name + u'/'
        pagedir = os.path.join(parent._pagedir, name)

        if os.path.lexists(pagedir):
            raise PageNameError(u'Target page already exists: %s' % path)

        os.rename(self._pagedir, pagedir)
        os.symlink(os.path.relpath(self._rootdir, os.path.dirname(self._pagedir)) + u'/@' + path, self._pagedir)
        self._fix_redirects(pagedir)

        return Page(path, self._lang)

    def save_redirect(self, redirect):
        if self._redirect is None:
            raise PageError(u'Page is not a redirect.')

        try:
            target = Page(redirect, self._lang)
        except InvalidPageError as e:
            raise PageRedirectError(e)

        os.remove(self._pagedir)
        os.symlink(os.path.relpath(self._rootdir, os.path.dirname(self._pagedir)) + u'/@' + target.path, self._pagedir)

    def save_config(self, raw_config=None, **entries):
        if self._redirect is not None:
            raise PageError(u'Cannot save config for a redirect.')
        if raw_config is not None and entries:
            raise ParseConfigError(u'Cannot change raw config and individual options at the same time.')

        if raw_config is not None:
            self._config.read_from_string(raw_config)
        else:
            self._config.set_multiple(**entries)
        self._config.write(os.path.join(self._pagedir, u'page.conf'))

    def save_template(self, template):
        if self._redirect is not None:
            raise PageError(u'Cannot save template for a redirect.')

        htmlfile = os.path.join(self._pagedir, u'page.html')
        if template is None:
            try:
                os.remove(htmlfile)
            except OSError:
                pass
        else:
            tmp = htmlfile + u'.tmp'
            try:
                with open(tmp, u'wb') as f:
                    f.write(template)
                os.rename(tmp, htmlfile)
            finally:
                try:
                    os.remove(tmp)
                except OSError:
                    pass

    ##########
    # Attached files
    ##########

    @cached_property
    def files(self):
        filesdir = os.path.join(self._pagedir, u'_files')
        if not os.path.isdir(filesdir):
            return []

        res = []
        for file in os.listdir(filesdir):
            if file_regex.match(file):
                try:
                    res.append(self.file(file))
                except InvalidFileError as e:
                    logging.getLogger(u'poleno.pages').error(u'Page /%s%s file "%s" is broken: %s', self._lang, self._path, file, e)
        res.sort()
        return res

    def file(self, name):
        return File(self, name)

    def create_file(self, name, content):
        if not file_regex.match(name):
            raise FileNameError(u'Invalid file name: %s' % name)

        filesdir = os.path.join(self._pagedir, u'_files')
        if not os.path.lexists(filesdir):
            os.mkdir(filesdir)

        filepath = os.path.join(filesdir, name)
        if os.path.lexists(filepath):
            raise FileNameError(u'Target file already exists: %s' % name)

        with open(filepath, u'wb') as f:
            for chunk in content.chunks():
                f.write(chunk)

        return File(self, name)
