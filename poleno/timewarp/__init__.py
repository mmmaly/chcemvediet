# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from .timewarp import timewarp

assert settings.DEBUG, u'Timewarp may NOT be enabled if settings.DEBUG is False.'
timewarp.enable()
