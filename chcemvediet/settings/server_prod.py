# vim: expandtab
# -*- coding: utf-8 -*-

###
### SETTINGS FOR PRODUCTION SERVER
###

DEBUG = False

PREPEND_WWW = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
LIBSASS_OUTPUT_STYLE = u'compressed'

# English on production server is disabled for now.
LANGUAGES = (
    (u'sk', u'Slovensky'),
    )

DATABASES = {
    u'default': {
        u'ENGINE': u'django.db.backends.mysql',
        u'CONN_MAX_AGE': 60,
        u'OPTIONS': {'charset': 'utf8mb4'},
        # Filled in 'configured.py'
        u'NAME': u'',
        u'USER': u'',
        u'PASSWORD': u'',
        },
    }

CACHES = {
    u'default': {
        u'BACKEND': u'django.core.cache.backends.memcached.PyMemcacheCache',
        u'LOCATION': u'127.0.0.1:11211',
        # Filled in 'configured.py'
        u'KEY_PREFIX': None,
        u'VERSION': None,
    },
    # django_compressor keeps one cache object per process (a module-level
    # ``SimpleLazyObject(lambda: caches[...])``) that all mod_wsgi threads share, and pymemcache
    # clients are not thread-safe: concurrent page renders read each other's replies and fail
    # with 500/504. Give the compressor its own in-process cache, which is thread-safe.
    u'compressor': {
        u'BACKEND': u'django.core.cache.backends.locmem.LocMemCache',
        u'LOCATION': u'compressor',
        u'TIMEOUT': None,
        u'OPTIONS': {u'MAX_ENTRIES': 2000},
    },
}
COMPRESS_CACHE_BACKEND = u'compressor'

LOGGING = {
    u'version': 1,
    u'disable_existing_loggers': True,
    u'formatters': {
        u'verbose': {
            u'format': u'[%(asctime)s] %(name)s %(levelname)s %(message)s',
            },
        },
    u'handlers': {
        u'mail_admins': {
            u'level': u'ERROR',
            u'class': u'logging.handlers.WatchedFileHandler',
            u'filename': os.path.join(PROJECT_PATH, u'logs/mail_admins.log'),
            u'formatter': u'verbose',
            },
        u'file_request': {
            u'level': u'WARNING',
            u'class': u'logging.handlers.TimedRotatingFileHandler',
            u'filename': os.path.join(PROJECT_PATH, u'logs/request.log'),
            u'when': u'w0', # Monday
            u'formatter': u'verbose',
            },
        u'file_security': {
            u'level': u'WARNING',
            u'class': u'logging.handlers.TimedRotatingFileHandler',
            u'filename': os.path.join(PROJECT_PATH, u'logs/security.log'),
            u'when': u'w0', # Monday
            u'formatter': u'verbose',
            },
        u'file_cron': {
            u'level': u'INFO',
            u'class': u'logging.handlers.TimedRotatingFileHandler',
            u'filename': os.path.join(PROJECT_PATH, u'logs/cron.log'),
            u'when': u'w0', # Monday
            u'formatter': u'verbose',
            },
        u'file_general': {
            u'level': u'WARNING',
            u'class': u'logging.handlers.TimedRotatingFileHandler',
            u'filename': os.path.join(PROJECT_PATH, u'logs/general.log'),
            u'when': u'w0', # Monday
            u'formatter': u'verbose',
            },
        },
    u'loggers': {
        u'django.request': {
            u'handlers': [u'mail_admins', u'file_request'],
            u'level': u'WARNING',
            u'propagate': False,
            },
        u'django.security': {
            u'handlers': [u'mail_admins', u'file_security'],
            u'level': u'WARNING',
            u'propagate': False,
            },
        u'django': {
            u'handlers': [u'mail_admins', u'file_general'],
            u'level': u'WARNING',
            },
        u'poleno.cron': {
            u'handlers': [u'mail_admins', u'file_cron'],
            u'level': u'INFO',
            u'propagate': False,
            },
        u'poleno': {
            u'handlers': [u'mail_admins', u'file_general'],
            u'level': u'WARNING',
            },
        u'chcemvediet': {
            u'handlers': [u'mail_admins', u'file_general'],
            u'level': u'WARNING',
            },
        },
    u'root': {
        u'handlers': [u'mail_admins', u'file_general'],
        u'level': u'WARNING',
        },
    }

# Django-allauth settings
ACCOUNT_DEFAULT_HTTP_PROTOCOL = u'https'

# Chcemvediet settings
INVITATIONS_INVITATION_ONLY = False
AUTOPUBLISH_INFOREQUESTS = False
