# vim: expandtab
# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.utils import override_settings

class AccountsTestCaseMixin(TestCase):

    def _pre_setup(self):
        super(AccountsTestCaseMixin, self)._pre_setup()
        self.settings_override = override_settings(
            PASSWORD_HASHERS=(u'django.contrib.auth.hashers.MD5PasswordHasher',),
            )
        self.settings_override.enable()

    def _post_teardown(self):
        self.settings_override.disable()
        super(AccountsTestCaseMixin, self)._post_teardown()
