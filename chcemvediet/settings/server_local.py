# vim: expandtab
# -*- coding: utf-8 -*-

###
### SETTINGS FOR LOCAL DEVELOPMENT SERVER DEVELOPERS RUN ON THEIR WORKSTATIONS
###

DEBUG = True
TEMPLATE_DEBUG = DEBUG

PREPEND_WWW = False

INSTALLED_APPS += (
    u'poleno.timewarp',
    )
