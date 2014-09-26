# vim: expandtab
# -*- coding: utf-8 -*-

import os
PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), u'../../'))
SETTINGS_PATH = os.path.abspath(os.path.dirname(__file__))

execfile(os.path.join(SETTINGS_PATH, u'common.py'))
execfile(os.path.join(SETTINGS_PATH, u'configured.py'))
