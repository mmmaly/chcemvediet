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
            u'class': u'django.utils.log.AdminEmailHandler',
            },
        u'file_warnings': {
            u'level': u'WARNING',
            u'class': u'logging.handlers.TimedRotatingFileHandler',
            u'filename': os.path.join(PROJECT_PATH, u'logs/warnings.log'),
            u'when': u'w0', # Monday
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
        },
    u'loggers': {
        u'py.warnings': {
            u'handlers': [u'file_warnings'],
            u'level': u'WARNING',
            u'propagate': False,
            },
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
        u'poleno.cron': {
            u'handlers': [u'file_cron'],
            u'level': u'INFO',
            u'propagate': False,
            },
        },
    }
