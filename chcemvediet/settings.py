# vim: expandtab
# -*- coding: utf-8 -*-

# Useful workarounds
import os
_ = lambda s: s
PROJECT_PATH = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]

# Django settings for chcemvediet project.
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    (u'Admin', u'admin@chcemvediet.sk'),
)

MANAGERS = ADMINS

DATABASES = {
    u'default': {
        u'ENGINE': u'django.db.backends.sqlite3', # Add u'postgresql_psycopg2', u'mysql', u'sqlite3' or u'oracle'.
        u'NAME': os.path.join(PROJECT_PATH, u'test.db'), # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        u'USER': u'',
        u'PASSWORD': u'',
        u'HOST': u'',                      # Empty for localhost through domain sockets or u'127.0.0.1' for localhost through TCP.
        u'PORT': u'',                      # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = u'Europe/Bratislava'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = u'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, u'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = u'/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(PROJECT_PATH, u'static')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = u'/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, u'chcemvediet/static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    u'django.contrib.staticfiles.finders.FileSystemFinder',
    u'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    u'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = u'j9n03fl6sw%97=gosszi-y6s6t%j8np6t56m=f1*ka&bne8ua5'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    (u'poleno.utils.template.TranslationLoader', u'django.template.loaders.filesystem.Loader'),
    (u'poleno.utils.template.TranslationLoader', u'django.template.loaders.app_directories.Loader'),
#     u'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    u'django.middleware.common.CommonMiddleware',
    u'django.contrib.sessions.middleware.SessionMiddleware',
    u'django.middleware.csrf.CsrfViewMiddleware',
    u'django.contrib.auth.middleware.AuthenticationMiddleware',
    u'django.contrib.messages.middleware.MessageMiddleware',
    u'django.middleware.locale.LocaleMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    u'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = (
    u'django.contrib.auth.backends.ModelBackend',
    "allauth.account.auth_backends.AuthenticationBackend",
)

ROOT_URLCONF = u'chcemvediet.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = u'chcemvediet.wsgi.application'

TEMPLATE_CONTEXT_PROCESSORS = (
    u'django.contrib.auth.context_processors.auth',
    u'django.core.context_processors.debug',
    u'django.core.context_processors.i18n',
    u'django.core.context_processors.media',
    u'django.core.context_processors.static',
    u'django.core.context_processors.request',
    u'django.core.context_processors.tz',
    u'django.contrib.messages.context_processors.messages',
    u'sekizai.context_processors.sekizai',
    u'allauth.account.context_processors.account',
    u'allauth.socialaccount.context_processors.socialaccount',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, u'chcemvediet/templates'),
)

INSTALLED_APPS = (
    # For django itself:
    u'django.contrib.auth',
    u'django.contrib.contenttypes',
    u'django.contrib.sessions',
    u'django.contrib.sites',
    u'django.contrib.messages',
    u'django.contrib.staticfiles',
    u'django.contrib.admin',
    u'django.contrib.sitemaps',
    # For django-allauth:
    u'allauth',
    u'allauth.account',
    u'allauth.socialaccount',
    u'allauth.socialaccount.providers.facebook',
    u'allauth.socialaccount.providers.google',
    u'allauth.socialaccount.providers.linkedin',
    u'allauth.socialaccount.providers.twitter',
    # Other 3part apps
    u'south',
    u'widget_tweaks',
    u'hvad',
    u'sekizai',
    u'django_mailbox',
    u'adminplus',
    u'django_cron',
    # Reused apps
    u'poleno.utils',
    u'poleno.dummymail',
    u'poleno.cron',
    # Local to the project
    u'chcemvediet.apps.attachments',
    u'chcemvediet.apps.accounts',
    u'chcemvediet.apps.obligees',
    u'chcemvediet.apps.inforequests',
)

if DEBUG:
    INSTALLED_APPS += (
        u'poleno.timewarp',
        )

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    u'version': 1,
    u'disable_existing_loggers': False,
    u'filters': {
        u'require_debug_false': {
            u'()': u'django.utils.log.RequireDebugFalse'
        }
    },
    u'handlers': {
        u'mail_admins': {
            u'level': u'ERROR',
            u'filters': [u'require_debug_false'],
            u'class': u'django.utils.log.AdminEmailHandler'
        }
    },
    u'loggers': {
        u'django.request': {
            u'handlers': [u'mail_admins'],
            u'level': u'ERROR',
            u'propagate': True,
        },
    }
}

# FIXME: We should probably use memcache on production environment
CACHES = {
    u'default': {
        u'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        u'LOCATION': os.path.join(PROJECT_PATH, u'cache'),
    },
}

# E-mail configuration
EMAIL_BACKEND = u'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = u'localhost'
EMAIL_PORT = 1025

# Where to search for initial data
FIXTURE_DIRS = (
    u'./fixtures',
)

# Django-allauth configuration
ACCOUNT_AUTHENTICATION_METHOD = u'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = u'mandatory'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_FORM_CLASS = u'chcemvediet.apps.accounts.forms.SignupForm'
SOCIALACCOUNT_EMAIL_VERIFICATION = u'none'
SOCIALACCOUNT_AUTO_SIGNUP = False

# List of available languages
LANGUAGES = (
    (u'sk', u'Slovensky'),
    (u'en', u'English'),
)

# Where to search for translations
LOCALE_PATHS = (
    os.path.join(PROJECT_PATH, u'chcemvediet/locale'),
    os.path.join(PROJECT_PATH, u'chcemvediet/locale/3part/allauth'),
)

# Where to search for formats localization
FORMAT_MODULE_PATH = u'chcemvediet.locale'

# Where to look for holidays definition
HOLIDAYS_MODULE_PATH = u'chcemvediet.holidays'

# Cron jobs
CRON_CLASSES = (
    u'chcemvediet.cron.get_mail',
)
