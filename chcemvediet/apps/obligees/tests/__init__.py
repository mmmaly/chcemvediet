# vim: expandtab
# -*- coding: utf-8 -*-
from django.template import Context, Template
from django.test import TestCase

from ..models import Obligee

class ObligeesTestCaseMixin(TestCase):

    def _create_obligee(self, omit=(), **kwargs):
        defaults = {
                u'name': u'Default Testing Name',
                u'street': u'Default Testing Street',
                u'city': u'Default Testing City',
                u'zip': u'00000',
                u'emails': u'default_testing_mail@example.com',
                u'status': Obligee.STATUSES.PENDING,
                }
        defaults.update(kwargs)
        for key in omit:
            del defaults[key]
        return Obligee.objects.create(**defaults)

    def _render(self, template, **context):
        return Template(template).render(Context(context))

