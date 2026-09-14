# vim: expandtab
# -*- coding: utf-8 -*-

import os
import sys
PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), u'../../'))
SETTINGS_PATH = os.path.abspath(os.path.dirname(__file__))

# Vendored packages (``vendor/``) patched for Django 5.2 must shadow any pip-installed copies.
# ``manage.py`` does the same, but WSGI servers and ``setup.py`` import settings directly, so
# the path must be set up here as well.
VENDOR_PATH = os.path.join(PROJECT_PATH, u'vendor')
if VENDOR_PATH not in sys.path:
    sys.path.insert(0, VENDOR_PATH)

with open(os.path.join(SETTINGS_PATH, u'common.py')) as f:
    exec(compile(f.read(), u'common.py', u'exec'))
with open(os.path.join(SETTINGS_PATH, u'configured.py')) as f:
    exec(compile(f.read(), u'configured.py', u'exec'))

# Django >= 4.0 no longer trusts CSRF origins based on ``ALLOWED_HOSTS``; derive them from the
# configured hosts unless ``configured.py`` sets ``CSRF_TRUSTED_ORIGINS`` explicitly.
if u'CSRF_TRUSTED_ORIGINS' not in globals():
    CSRF_TRUSTED_ORIGINS = []
    for _host in globals().get(u'ALLOWED_HOSTS', []):
        if _host == u'*':
            continue
        if _host.startswith(u'.'):
            CSRF_TRUSTED_ORIGINS.append(u'https://*' + _host)
            CSRF_TRUSTED_ORIGINS.append(u'https://' + _host[1:])
        else:
            CSRF_TRUSTED_ORIGINS.append(u'https://' + _host)
    if globals().get(u'DEBUG'):
        CSRF_TRUSTED_ORIGINS += [u'http://' + o[len(u'https://'):] for o in CSRF_TRUSTED_ORIGINS]
    del _host
