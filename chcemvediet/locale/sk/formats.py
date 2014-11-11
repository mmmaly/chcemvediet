# vim: expandtab
# -*- coding: utf-8 -*-
DATE_INPUT_FORMATS = (
        # The first format is default output format
        u'%d.%m.%Y', # '25.10.2006'
        u'%d.%m.%y', # '25.10.06'
        u'%Y-%m-%d', # '2006-10-25'
        )
DATETIME_INPUT_FORMATS = (
        # The first format is default output format
        u'%d.%m.%Y %H:%M:%S',    # '25.10.2006 14:30:59'
        u'%d.%m.%Y %H:%M:%S.%f', # '25.10.2006 14:30:59.000200'
        u'%d.%m.%Y %H:%M',       # '25.10.2006 14:30'
        u'%d.%m.%Y',             # '25.10.2006'
        u'%d.%m.%y %H:%M:%S',    # '25.10.06 14:30:59'
        u'%d.%m.%y %H:%M:%S.%f', # '25.10.06 14:30:59.000200'
        u'%d.%m.%y %H:%M',       # '25.10.06 14:30'
        u'%d.%m.%y',             # '25.10.06'
        u'%Y-%m-%d %H:%M:%S',    # '2006-10-25 14:30:59'
        u'%Y-%m-%d %H:%M:%S.%f', # '2006-10-25 14:30:59.000200'
        u'%Y-%m-%d %H:%M',       # '2006-10-25 14:30'
        u'%Y-%m-%d',             # '2006-10-25'
        )
