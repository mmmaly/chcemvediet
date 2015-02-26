# vim: expandtab
# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.test.runner import DiscoverRunner

class CustomTestRunner(DiscoverRunner):
    u"""
    Custom test runner with the following features:
     -- Disabled logging while testing.
        Source: http://stackoverflow.com/questions/5255657/how-can-i-disable-logging-while-running-unit-tests-in-python-django
     -- Forced language code 'en'
    """

    def setup_test_environment(self, **kwargs):
        super(CustomTestRunner, self).setup_test_environment(**kwargs)
        settings.LANGUAGE_CODE = u'en'

    def run_tests(self, *args, **kwargs):
        logging.disable(logging.CRITICAL)
        return super(CustomTestRunner, self).run_tests(*args, **kwargs)
