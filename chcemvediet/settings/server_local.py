# vim: expandtab
# -*- coding: utf-8 -*-

###
### SETTINGS FOR LOCAL DEVELOPMENT SERVER DEVELOPERS RUN ON THEIR WORKSTATIONS
###

DEBUG = True
TEMPLATES[0][u'OPTIONS'][u'debug'] = True

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

CACHES = {
    u'default': {
        u'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        u'LOCATION': os.path.join(PROJECT_PATH, u'cache'),
        # Filled in 'configured.py'
        u'KEY_PREFIX': None,
        u'VERSION': None,
    },
}

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
        u'django': {
            u'handlers': [u'console'],
            u'level': u'INFO',
            },
        u'poleno': {
            u'handlers': [u'console'],
            u'level': u'INFO',
            },
        u'chcemvediet': {
            u'handlers': [u'console'],
            u'level': u'INFO',
            },
        },
    u'root': {
        u'handlers': [u'console'],
        u'level': u'INFO',
        },
    }

# Django-allauth settings
ACCOUNT_DEFAULT_HTTP_PROTOCOL = u'http'
