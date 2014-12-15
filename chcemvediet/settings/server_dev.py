# vim: expandtab
# -*- coding: utf-8 -*-

###
### SETTINGS FOR ONLINE DEVELOPMENT SERVER
###

DEBUG = True
TEMPLATE_DEBUG = DEBUG

PREPEND_WWW = True

INSTALLED_APPS += (
    u'poleno.timewarp',
    )
