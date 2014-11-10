# vim: expandtab
# -*- coding: utf-8 -*-
from django.test import TestCase

from poleno.utils.test import ViewTestCaseMixin

from .. import InforequestsTestCaseMixin

class AbstractTests(object):
    u"""
    Abstract base class for mixin tests we will later add to some view test cases. We cannot
    explicitly inherit ``TestCase`` here, because we don't want theese tests to be performed unless
    their are mixed into some real test case class.
    """
    form_prefix = u''

    def _create_scenario(self, **kwargs):
        raise NotImplementedError

    def _create_url(self, scenario, **kwargs):
        raise NotImplementedError

    def _create_post_data(self, **kwargs):
        omit = kwargs.pop(u'omit', [])
        prefix = kwargs.pop(u'prefix', self.form_prefix)
        not_prefixed = kwargs.pop(u'not_prefixed', [])
        for key in omit:
            kwargs.pop(key)
        kwargs = {k if k in not_prefixed else u'%s-%s' % (prefix, k): v for k, v in kwargs.iteritems()}
        return kwargs

class CustomTestCase(InforequestsTestCaseMixin, ViewTestCaseMixin, TestCase):
    u"""
    Extended ``TestCase`` for testing inforequest views.
    """
    pass
