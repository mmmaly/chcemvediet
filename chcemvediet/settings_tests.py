# vim: expandtab
# -*- coding: utf-8 -*-
u"""
Self-contained settings for running the test suite without ``setup.py`` and without a MySQL
account that may create databases: SQLite, file cache, no mail, all external tools mocked.

    env310/bin/python manage.py test poleno.mail --settings=chcemvediet.settings_tests
"""
import os
import sys

PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), u'../'))
SETTINGS_PATH = os.path.join(PROJECT_PATH, u'chcemvediet/settings')

VENDOR_PATH = os.path.join(PROJECT_PATH, u'vendor')
if VENDOR_PATH not in sys.path:
    sys.path.insert(0, VENDOR_PATH)

for _name in (u'common.py', u'server_local.py', u'mail_nomail.py'):
    with open(os.path.join(SETTINGS_PATH, _name)) as _f:
        exec(compile(_f.read(), _name, u'exec'))

MOCK_LIBREOFFICE = True
MOCK_IMAGEMAGIC = True
MOCK_OCR = True
SECRET_KEY = u'not-a-secret-just-for-tests'
ALLOWED_HOSTS = [u'*']
SERVER_EMAIL = u'admin@example.com'
ADMINS[len(ADMINS):] = [(u'Admin', u'admin@example.com')]
SUPPORT_EMAIL = u'info@example.com'
INFOREQUEST_UNIQUE_EMAIL = u'{token}@mail.example.com'
DEFAULT_FROM_EMAIL = u'info@example.com'
OBLIGEE_DUMMY_MAIL = u'mail@{name}.example.com'
DEVBAR_MESSAGE = u''
CACHES[u'default'][u'KEY_PREFIX'] = u'tests'
CACHES[u'default'][u'VERSION'] = 1
SEARCH_API_KEY = u''
RECAPTCHA_PUBLIC_KEY = u'6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
RECAPTCHA_PRIVATE_KEY = u'6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
CSRF_TRUSTED_ORIGINS = [u'http://testserver', u'https://testserver']
