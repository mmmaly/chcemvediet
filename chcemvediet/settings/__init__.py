# vim: expandtab
# -*- coding: utf-8 -*-

import os
PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), u'../../'))
SETTINGS_PATH = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(SETTINGS_PATH, u'common.py')) as f:
    exec(compile(f.read(), u'common.py', u'exec'))
with open(os.path.join(SETTINGS_PATH, u'configured.py')) as f:
    exec(compile(f.read(), u'configured.py', u'exec'))
