# vim: expandtab
# -*- coding: utf-8 -*-

import os
_ = lambda s: s

# Django settings for chcemvediet project.
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = []
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
ALLOWED_HOSTS = [u'127.0.0.1']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = u'Europe/Bratislava'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = u'en'

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
    #u'django.contrib.staticfiles.finders.FileSystemFinder',
    #u'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #u'django.contrib.staticfiles.finders.DefaultStorageFinder',
    u'pipeline.finders.FileSystemFinder',
    u'pipeline.finders.AppDirectoriesFinder',
    u'pipeline.finders.PipelineFinder',
    #u'pipeline.finders.CachedFileFinder',
)

STATICFILES_STORAGE = u'pipeline.storage.PipelineStorage'
#STATICFILES_STORAGE = u'pipeline.storage.PipelineCachedStorage'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    (u'poleno.utils.template.TranslationLoader', u'django.template.loaders.filesystem.Loader'),
    (u'poleno.utils.template.TranslationLoader', u'django.template.loaders.app_directories.Loader'),
    (u'poleno.utils.template.TranslationLoader', u'apptemplates.Loader'),
#     u'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    u'django.middleware.common.CommonMiddleware',
    u'django.contrib.sessions.middleware.SessionMiddleware',
    u'django.middleware.csrf.CsrfViewMiddleware',
    u'django.contrib.auth.middleware.AuthenticationMiddleware',
    u'django.contrib.messages.middleware.MessageMiddleware',
    u'django.middleware.locale.LocaleMiddleware',
    u'django.middleware.clickjacking.XFrameOptionsMiddleware',
    u'simple_history.middleware.HistoryRequestMiddleware',
    #u'pipeline.middleware.MinifyHTMLMiddleware',
)

AUTHENTICATION_BACKENDS = (
    u'django.contrib.auth.backends.ModelBackend',
    u'allauth.account.auth_backends.AuthenticationBackend',
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
    # For django-admin-tools; must be before "django.contrib.auth":
    u'admin_tools',
    u'admin_tools.theming',
    u'admin_tools.menu',
    u'admin_tools.dashboard',
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
    u'adminplus',
    u'django_cron',
    u'simple_history',
    u'pipeline',
    # Reused apps
    u'poleno.utils',
    u'poleno.dummymail',
    u'poleno.cron',
    u'poleno.attachments',
    u'poleno.mail',
    # Local to the project
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
    u'poleno.mail.cron.mail',
    u'chcemvediet.apps.inforequests.cron.undecided_email_reminder',
    u'chcemvediet.apps.inforequests.cron.obligee_deadline_reminder',
    u'chcemvediet.apps.inforequests.cron.applicant_deadline_reminder',
    u'chcemvediet.apps.inforequests.cron.close_inforequests',
)

# Mail settings
EMAIL_BACKEND = u'poleno.mail.backend.EmailBackend'

# JS and CSS assets
ASSETS = (
    # JQuery
    u'//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js',
    # JQuery UI
    u'//ajax.googleapis.com/ajax/libs/jqueryui/1.10.3/themes/smoothness/jquery-ui.min.css',
    u'//ajax.googleapis.com/ajax/libs/jqueryui/1.10.3/jquery-ui.min.js',
    u'main/3part/jqueryui/1.10.3/datepicker-sk.js',
    # Bootstrap
    u'//netdna.bootstrapcdn.com/twitter-bootstrap/2.3.2/css/bootstrap-combined.min.css',
    u'//netdna.bootstrapcdn.com/twitter-bootstrap/2.3.2/js/bootstrap.min.js',
    # JQuery File Upload (Requires: jquery.ui.widget.js)
    u'main/3part/jqueryplugins/jquery.iframe-transport.js',
    u'main/3part/jqueryplugins/jquery.fileupload.js',
    # Other JQuery plugins
    u'main/3part/jqueryplugins/jquery.cookie.js',
    u'main/3part/jqueryplugins/jquery.PrintArea.js',
    # Reused apps
    u'poleno/js/*.js',
    u'attachments/js/*.js',
    # Local to the project
    u'obligees/css/*.css',
    u'obligees/js/*.js',
    u'inforequests/js/*.js',
    u'main/css/*.css',
)

#PIPELINE_ENABLED = True
PIPELINE_JS_COMPRESSOR = None
PIPELINE_CSS_COMPRESSOR = None
PIPELINE_JS = {
    u'main': {
        u'source_filenames': [a for a in ASSETS if not a.startswith(u'//') and a.endswith(u'.js')],
        u'output_filename': u'js/main.js',
    },
}
PIPELINE_CSS = {
    u'main': {
        u'source_filenames': [a for a in ASSETS if not a.startswith(u'//') and a.endswith(u'.css')],
        u'output_filename': u'css/main.css',
    },
}
EXTERNAL_JS = [a for a in ASSETS if a.startswith(u'//') and a.endswith(u'.js')]
EXTERNAL_CSS = [a for a in ASSETS if a.startswith(u'//') and a.endswith(u'.css')]

# Django-admin-tools settings
ADMIN_TOOLS_MENU = u'chcemvediet.admin.CustomMenu'
ADMIN_TOOLS_INDEX_DASHBOARD = u'chcemvediet.admin.CustomIndexDashboard'
ADMIN_TOOLS_APP_INDEX_DASHBOARD = u'chcemvediet.admin.CustomAppIndexDashboard'
