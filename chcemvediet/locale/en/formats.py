# vim: expandtab
# -*- coding: utf-8 -*-
DATE_INPUT_FORMATS = (
        # The first format is default output format
        u'%m/%d/%Y', # '10/25/2006'
        u'%m/%d/%y', # '10/25/06'
        u'%Y-%m-%d', # '2006-10-25'
        )
DATETIME_INPUT_FORMATS = (
        # The first format is default output format
        u'%m/%d/%Y %H:%M:%S',    # '10/25/2006 14:30:59'
        u'%m/%d/%Y %H:%M:%S.%f', # '10/25/2006 14:30:59.000200'
        u'%m/%d/%Y %H:%M',       # '10/25/2006 14:30'
        u'%m/%d/%Y',             # '10/25/2006'
        u'%m/%d/%y %H:%M:%S',    # '10/25/06 14:30:59'
        u'%m/%d/%y %H:%M:%S.%f', # '10/25/06 14:30:59.000200'
        u'%m/%d/%y %H:%M',       # '10/25/06 14:30'
        u'%m/%d/%y',             # '10/25/06'
        u'%Y-%m-%d %H:%M:%S',    # '2006-10-25 14:30:59'
        u'%Y-%m-%d %H:%M:%S.%f', # '2006-10-25 14:30:59.000200'
        u'%Y-%m-%d %H:%M',       # '2006-10-25 14:30'
        u'%Y-%m-%d',             # '2006-10-25'
        )
