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

LOGGING = {
    u'version': 1,
    u'disable_existing_loggers': True,
    u'formatters': {
        u'verbose': {
            u'format': u'[%(asctime)s] %(name)s %(levelname)s %(message)s',
            },
        },
    u'handlers': {
        u'console': {
            u'level': u'INFO',
            u'class': u'logging.StreamHandler',
            u'formatter': u'verbose',
            },
        #u'file_db': {
        #    u'level': u'DEBUG',
        #    u'class': u'logging.FileHandler',
        #    u'filename': os.path.join(PROJECT_PATH, u'logs/db.log'),
        #    u'formatter': u'verbose',
        #    },
        },
    u'loggers': {
        #u'django.db.backends': {
        #    u'handlers': [u'file_db'],
        #    u'level': u'DEBUG',
        #    u'propagate': False,
        #    },
        },
    u'root': {
        u'handlers': [u'console'],
        u'level': u'INFO',
        },
    }
