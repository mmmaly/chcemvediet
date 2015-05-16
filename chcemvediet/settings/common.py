# vim: expandtab
# -*- coding: utf-8 -*-

SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True
ADMINS = [] # Filled in 'configured.py'
MANAGERS = ADMINS

ROOT_URLCONF = u'chcemvediet.urls'
FORMAT_MODULE_PATH = u'chcemvediet.locale'
HOLIDAYS_MODULE_PATH = u'chcemvediet.holidays'
EMAIL_BACKEND = u'poleno.mail.backend.EmailBackend'
TEST_RUNNER = u'chcemvediet.tests.CustomTestRunner'
WSGI_APPLICATION = u'chcemvediet.wsgi.application'

TIME_ZONE = u'Europe/Bratislava'
LANGUAGE_CODE = u'sk'
LANGUAGES = (
    (u'sk', u'Slovensky'),
    (u'en', u'English'),
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
    u'django.contrib.admin.apps.SimpleAdminConfig', # See "django-adminplus" docs for Django 1.7
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
    u'sekizai',
    u'adminplus',
    u'django_cron',
    u'simple_history',
    u'pipeline',
    # Reused apps
    u'poleno.utils',
    u'poleno.dummymail',
    u'poleno.datacheck',
    u'poleno.cron',
    u'poleno.attachments',
    u'poleno.mail',
    u'poleno.pages',
    u'poleno.invitations',
    # Local to the project
    u'chcemvediet.apps.accounts',
    u'chcemvediet.apps.obligees',
    u'chcemvediet.apps.inforequests',
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

TEMPLATE_LOADERS = (
    (u'poleno.utils.template.TranslationLoader', u'django.template.loaders.filesystem.Loader'),
    (u'poleno.utils.template.TranslationLoader', u'django.template.loaders.app_directories.Loader'),
    (u'poleno.utils.template.TranslationLoader', u'apptemplates.Loader'),
    )

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, u'chcemvediet/templates'),
    )

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
    u'chcemvediet.context_processors.settings',
    )

CRON_CLASSES = (
    u'poleno.cron.cron.clear_old_cronlogs',
    u'poleno.datacheck.cron.datacheck',
    u'poleno.mail.cron.mail',
    u'chcemvediet.apps.inforequests.cron.undecided_email_reminder',
    u'chcemvediet.apps.inforequests.cron.obligee_deadline_reminder',
    u'chcemvediet.apps.inforequests.cron.applicant_deadline_reminder',
    u'chcemvediet.apps.inforequests.cron.close_inforequests',
    u'chcemvediet.cron.clear_expired_sessions',
    u'chcemvediet.cron.send_admin_error_logs',
    )

LOCALE_PATHS = (
    os.path.join(PROJECT_PATH, u'chcemvediet/locale'),
    os.path.join(PROJECT_PATH, u'chcemvediet/locale/3part/allauth'),
    )

# FIXME: We should probably not use filebased cache on production environment
CACHES = {
    u'default': {
        u'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        u'LOCATION': os.path.join(PROJECT_PATH, u'cache'),
    },
}

# FIXME: Static and media files in production?
MEDIA_ROOT = os.path.join(PROJECT_PATH, u'media')
MEDIA_URL = u'/media/'
STATIC_ROOT = os.path.join(PROJECT_PATH, u'static')
STATIC_URL = u'/static/'

STATICFILES_STORAGE = u'pipeline.storage.PipelineStorage'
#STATICFILES_STORAGE = u'pipeline.storage.PipelineCachedStorage'

STATICFILES_DIRS = (
    os.path.join(PROJECT_PATH, u'chcemvediet/static'),
    )

STATICFILES_FINDERS = (
    u'django.contrib.staticfiles.finders.FileSystemFinder',
    u'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    u'pipeline.finders.PipelineFinder',
    #u'pipeline.finders.CachedFileFinder',
    )

# JS and CSS assets settings
# FIXME: enable pipeline and compressor in production?
ASSETS = (
    # JQuery
    u'//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js',
    # JQuery UI
    u'//ajax.googleapis.com/ajax/libs/jqueryui/1.10.3/themes/smoothness/jquery-ui.min.css',
    u'//ajax.googleapis.com/ajax/libs/jqueryui/1.10.3/jquery-ui.min.js',
    u'main/3part/jqueryui/1.10.3/datepicker-sk.js',
    # Bootstrap; Version 2.3.2 has broken navbar on mobiles
    u'//netdna.bootstrapcdn.com/twitter-bootstrap/2.3.1/css/bootstrap-combined.min.css',
    u'//netdna.bootstrapcdn.com/twitter-bootstrap/2.3.1/js/bootstrap.min.js',
    # JQuery File Upload (Requires: jquery.ui.widget.js)
    u'main/3part/jqueryplugins/jquery.iframe-transport.js',
    u'main/3part/jqueryplugins/jquery.fileupload.js',
    # Other JQuery plugins
    u'main/3part/jqueryplugins/jquery.cookie.js',
    u'main/3part/jqueryplugins/jquery.PrintArea.js',
    # Reused apps
    u'poleno/css/*.css',
    u'poleno/js/*.js',
    u'attachments/css/*.css',
    u'attachments/js/*.js',
    # Local to the project
    u'obligees/css/*.css',
    u'obligees/js/*.js',
    u'inforequests/css/*.css',
    u'inforequests/js/*.js',
    u'main/css/*.css',
    u'main/js/*.js',
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

# Django-allauth settings
ACCOUNT_ADAPTER = u'poleno.invitations.adapters.InvitationsAdapter'
ACCOUNT_AUTHENTICATION_METHOD = u'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = u'mandatory'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_FORM_CLASS = u'chcemvediet.apps.accounts.forms.SignupForm'
SOCIALACCOUNT_EMAIL_VERIFICATION = u'none'
SOCIALACCOUNT_AUTO_SIGNUP = False
INVITATIONS_INVITATION_ONLY = False
INVITATIONS_USERS_CAN_INVITE = True

# Django-admin-tools settings
ADMIN_TOOLS_MENU = u'chcemvediet.admin.CustomMenu'
ADMIN_TOOLS_INDEX_DASHBOARD = u'chcemvediet.admin.CustomIndexDashboard'
ADMIN_TOOLS_APP_INDEX_DASHBOARD = u'chcemvediet.admin.CustomAppIndexDashboard'
