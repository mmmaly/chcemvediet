# vim: expandtab
# -*- coding: utf-8 -*-

###
### SETTINGS FOR LOCAL DEVELOPMENT SERVER DEVELOPERS RUN ON THEIR WORKSTATIONS
###

DEBUG = True
TEMPLATE_DEBUG = DEBUG

PREPEND_WWW = False

DATABASES = {
    u'default': {
        u'ENGINE': u'django.db.backends.sqlite3',
        u'NAME': os.path.join(PROJECT_PATH, u'test.db'),
        },
    }

INSTALLED_APPS += (
    u'poleno.timewarp',
    )
