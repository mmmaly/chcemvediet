# vim: expandtab
# -*- coding: utf-8 -*-

###
### SETTINGS FOR ONLINE DEVELOPMENT SERVER
###

DEBUG = True
TEMPLATE_DEBUG = DEBUG

PREPEND_WWW = True

DATABASES = {
    u'default': {
        u'ENGINE': u'django.db.backends.mysql',
        u'CONN_MAX_AGE': 60,
        # Filled in 'configured.py'
        u'NAME': u'',
        u'USER': u'',
        u'PASSWORD': u'',
        },
    }

INSTALLED_APPS += (
    u'poleno.timewarp',
    )
