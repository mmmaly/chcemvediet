# vim: expandtab
# -*- coding: utf-8 -*-

###
### SETTINGS FOR PRODUCTION SERVER
###

DEBUG = False
TEMPLATE_DEBUG = DEBUG

PREPEND_WWW = True
ALLOWED_HOSTS = [u'.chcemvediet.sk']

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
