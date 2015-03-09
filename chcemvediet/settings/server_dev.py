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

# FIXME: ``logging.handlers.TimedRotatingFileHandler`` and all python logging file handlers in
# general are broken when running multiple processes. Concurrent processes will overwrite each
# other logs. Sadly, there is no solution for it in Django. Django does not even mention this issue
# in their documentation. We need to use a file handler that locks the log file, or we need to run
# a separate process that collects logs from all Django processes over sockets. Writing a separate
# deamon process seems too complicated, however. We'd need to watch the process and respawn it when
# it crashes, watch source files and reload them when they change a so.
#
# For instance ``ConcurrentLogHandler`` uses locks, but it does not retate them in timed manner
# like ``TimedRotatingFileHandler``. I have not found any package using locks that would rotate the
# log file in timed manner. We will propably need to impletent it by ourselfs.
# See: https://pypi.python.org/pypi/ConcurrentLogHandler
#
# There are two issues with logging file handlers running multiple processes actually. The first
# issue is that long log entries from different processes can intermingle. The second much more
# severe issue is that all processes try to rotate the log file resulting in overwritten rotated
# files losing all their entries. If we won't care that log entries may still intermingle, we can
# fix the second issue without file locking by implementing more a carefull file rotation using
# ``os.link(src, dest)`` or ``os.create(dest, O_CREAT | O_EXCL)`` that is atomic and fails if
# ``dest`` file already exists.
#
# So far, we are using only one Django wsgi process and one cron process on dev server, so the risk
# of conflicts is minimal. However, on production server, we rather use several wsgi processes, so
# we need to fix it.

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
        u'poleno.cron': {
            u'handlers': [u'mail_admins', u'file_cron'],
            u'level': u'INFO',
            u'propagate': False,
            },
        },
    u'root': {
        u'handlers': [u'mail_admins', u'file_general'],
        u'level': u'WARNING',
        },
    }
