# vim: expandtab
# -*- coding: utf-8 -*-

import os
PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), u'../../'))
SETTINGS_PATH = os.path.abspath(os.path.dirname(__file__))

exec(compile(open(os.path.join(SETTINGS_PATH, u'common.py')).read(), u'common.py', u'exec'))
exec(compile(open(os.path.join(SETTINGS_PATH, u'configured.py')).read(), u'configured.py', u'exec'))
