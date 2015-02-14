# vim: expandtab
# -*- coding: utf-8 -*-
import logging

from django.test.runner import DiscoverRunner

class CustomTestRunner(DiscoverRunner):
    u"""
    Custom test runner with the following features:
     -- Disabled logging while testing.
        Source: http://stackoverflow.com/questions/5255657/how-can-i-disable-logging-while-running-unit-tests-in-python-django
    """
    def run_tests(self, *args, **kwargs):
        logging.disable(logging.CRITICAL)
        return super(CustomTestRunner, self).run_tests(*args, **kwargs)
