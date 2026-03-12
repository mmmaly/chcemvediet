# vim: expandtab
# -*- coding: utf-8 -*-
from chcemvediet import sass_functions

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
DEFAULT_AUTO_FIELD = u'django.db.models.AutoField'

TIME_ZONE = u'Europe/Bratislava'
LANGUAGE_CODE = u'sk'
LANGUAGES = (
    (u'sk', u'Slovensky'),
    (u'en', u'English'),
    )
LOCALE_PATHS = (
    os.path.join(PROJECT_PATH, u'chcemvediet/locale/overrides'),
    )

INSTALLED_APPS = (
    # Project core app
    u'chcemvediet',
    # For django itself:
    u'django.contrib.auth',
    u'django.contrib.contenttypes',
    u'django.contrib.sessions',
    u'django.contrib.sites',
    u'django.contrib.messages',
    u'django.contrib.redirects',
    u'django.contrib.staticfiles',
    u'django.contrib.admin.apps.SimpleAdminConfig', # See "django-adminplus" docs for Django 1.7
    u'django.contrib.sitemaps',
    # For django-allauth:
    u'allauth',
    u'allauth.account',
    u'allauth.socialaccount',
    u'allauth.socialaccount.providers.google',
    # Other 3part apps
    u'vendor.adminplus',
    u'django_cron',
    u'simple_history',
    u'widget_tweaks',
    u'compressor',
    u'vendor.bootstrap_sass',
    u'captcha',
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
    u'chcemvediet.apps.wizards',
    u'chcemvediet.apps.accounts',
    u'chcemvediet.apps.geounits',
    u'chcemvediet.apps.obligees',
    u'chcemvediet.apps.inforequests',
    u'chcemvediet.apps.anonymization',
)

MIDDLEWARE = (
    u'poleno.utils.http.RequestProviderMiddleware',
    u'django.middleware.common.CommonMiddleware',
    u'django.contrib.sessions.middleware.SessionMiddleware',
    u'django.middleware.csrf.CsrfViewMiddleware',
    u'django.contrib.auth.middleware.AuthenticationMiddleware',
    u'django.contrib.messages.middleware.MessageMiddleware',
    u'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    u'django.middleware.locale.LocaleMiddleware',
    u'django.middleware.clickjacking.XFrameOptionsMiddleware',
    u'simple_history.middleware.HistoryRequestMiddleware',
    )

AUTHENTICATION_BACKENDS = (
    u'chcemvediet.auth_backends.DjangoModelBackendWithAdminLoginAs',
    u'chcemvediet.auth_backends.AllauthAuthenticationBackendWithAdminLoginAs',
    )

TEMPLATES = [
    {
        u'BACKEND': u'django.template.backends.django.DjangoTemplates',
        u'DIRS': [],
        u'APP_DIRS': False,
        u'OPTIONS': {
            u'loaders': [
                (u'poleno.utils.template.TranslationLoader', u'django.template.loaders.filesystem.Loader'),
                (u'poleno.utils.template.TranslationLoader', u'django.template.loaders.app_directories.Loader'),
                (u'poleno.utils.template.TranslationLoader', u'poleno.utils.template.AppLoader'),
            ],
            u'context_processors': [
                u'django.contrib.auth.context_processors.auth',
                u'django.template.context_processors.debug',
                u'django.template.context_processors.i18n',
                u'django.template.context_processors.media',
                u'django.template.context_processors.static',
                u'django.template.context_processors.request',
                u'django.template.context_processors.tz',
                u'django.contrib.messages.context_processors.messages',
                u'poleno.mail.context_processors.constants',
                u'poleno.utils.context_processors.idgenerator',
                u'chcemvediet.apps.obligees.context_processors.constants',
                u'chcemvediet.apps.inforequests.context_processors.constants',
                u'chcemvediet.apps.anonymization.context_processors.constants',
                u'chcemvediet.context_processors.settings',
            ],
        },
    },
]

# Daily jobs do all their work the first time they are run in a day. Duplicte runs in the same day
# should do nothing. However, we run them multiple times in a day in case something was broken and
# the jobs failed earlier.
CRON_USER_INTERACTION_TIMES = [u'09:00', u'10:00', u'11:00', u'12:00', u'13:00', u'14:00']
CRON_IMPORTANT_MAINTENANCE_TIMES = [u'02:00', u'03:00', u'04:00', u'05:00']
CRON_UNIMPORTANT_MAINTENANCE_TIMES = [u'04:00']
CRON_CLASSES = (
    u'poleno.cron.cron.clear_old_cronlogs',
    u'poleno.datacheck.cron.datacheck',
    u'poleno.mail.cron.mail',
    u'chcemvediet.apps.wizards.cron.delete_old_drafts',
    u'chcemvediet.apps.inforequests.cron.undecided_email_reminder',
    u'chcemvediet.apps.inforequests.cron.obligee_deadline_reminder',
    u'chcemvediet.apps.inforequests.cron.applicant_deadline_reminder',
    u'chcemvediet.apps.inforequests.cron.close_inforequests',
    u'chcemvediet.apps.inforequests.cron.publish_inforequests',
    u'chcemvediet.apps.inforequests.cron.add_expirations',
    u'chcemvediet.apps.anonymization.cron.anonymization',
    u'chcemvediet.cron.clear_expired_sessions',
    u'chcemvediet.cron.send_admin_error_logs',
    )

# FIXME: Static and media files in production?
MEDIA_ROOT = os.path.join(PROJECT_PATH, u'media')
MEDIA_URL = u'/media/'
STATIC_ROOT = os.path.join(PROJECT_PATH, u'static')
STATIC_URL = u'/static/'

STATICFILES_DIRS = (
    os.path.join(PROJECT_PATH, u'fontello/output/static'),
    )

STATICFILES_FINDERS = (
    u'django.contrib.staticfiles.finders.FileSystemFinder',
    u'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    u'compressor.finders.CompressorFinder',
    )

COMPRESS_PRECOMPILERS = (
    (u'text/x-scss', u'django_libsass.SassCompiler'),
    )

LIBSASS_CUSTOM_FUNCTIONS = {
    u'static': sass_functions.static,
    u'md5': sass_functions.md5,
    }

# JS and CSS assets settings
ASSETS = (
    # JQuery
    u'//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js',
    # JQuery UI
    u'//ajax.googleapis.com/ajax/libs/jqueryui/1.10.3/themes/smoothness/jquery-ui.min.css',
    u'//ajax.googleapis.com/ajax/libs/jqueryui/1.10.3/jquery-ui.min.js',
    u'main/3part/jqueryui/1.10.3/datepicker-sk.js',
    # JQuery File Upload (Requires: jquery.ui.widget.js)
    u'main/3part/jqueryplugins/jquery.iframe-transport.js',
    u'main/3part/jqueryplugins/jquery.fileupload.js',
    # Other JQuery plugins
    u'main/3part/jqueryplugins/jquery.cookie.js',
    u'main/3part/jqueryplugins/jquery.PrintArea.js',
    # Fonts
    u'//fonts.googleapis.com/css?family=Ubuntu:400,500,700',
    u'fontello/css/fontello-codes.css',
    # Custom Bootstrap (tooltip must be before popover)
    u'main/css/main.sass',
    u'javascripts/affix.js',
    u'javascripts/alert.js',
    u'javascripts/button.js',
    u'javascripts/carousel.js',
    u'javascripts/collapse.js',
    u'javascripts/dropdown.js',
    u'javascripts/modal.js',
    u'javascripts/tooltip.js',
    u'javascripts/popover.js',
    u'javascripts/scrollspy.js',
    u'javascripts/tab.js',
    u'javascripts/transition.js',
    # Reused apps
    u'poleno/js/00.confirm_button.js',
    u'poleno/js/ajax.js',
    u'poleno/js/autocomplete.js',
    u'poleno/js/autosize_textarea.js',
    u'poleno/js/collapsable.js',
    u'poleno/js/composite_text.js',
    u'poleno/js/datepicker.js',
    u'poleno/js/editable.js',
    u'poleno/js/hide_bootstrap_modal.js',
    u'poleno/js/not_implemented.js',
    u'poleno/js/post_link.js',
    u'poleno/js/print_button.js',
    u'poleno/js/range_widget.js',
    u'poleno/js/recursive_bootstrap_modal.js',
    u'poleno/js/reload_button.js',
    u'poleno/js/scrollto.js',
    u'poleno/js/toggle_changed.js',
    u'poleno/js/tooltip.js',
    u'attachments/js/fileupload.js',
    # Local to the project
    u'obligees/js/obligee_widget.js',
    u'main/js/01.bootstrapfix.js',
    u'main/css/02.jqueryfix.css',
    u'main/css/03.gcsefix.css',
    )

# Django-allauth settings
ACCOUNT_ADAPTER = u'chcemvediet.adapters.AccountAdapter'
ACCOUNT_AUTHENTICATION_METHOD = u'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = u'optional'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_FORMS = {
    u'signup': u'chcemvediet.apps.accounts.forms.SignupForm',
    u'login': u'chcemvediet.apps.accounts.forms.LoginForm',
    u'reset_password': u'chcemvediet.apps.accounts.forms.ResetPasswordForm',
    }
SOCIALACCOUNT_EMAIL_VERIFICATION = u'none'
SOCIALACCOUNT_AUTO_SIGNUP = False
LOGIN_REDIRECT_URL = u'inforequests:mine'

# Django-recaptcha settings
NOCAPTCHA = True

# Chcemvediet settings
INVITATIONS_INVITATION_ONLY = False
INVITATIONS_USERS_CAN_INVITE = True
AUTOPUBLISH_INFOREQUESTS = True
