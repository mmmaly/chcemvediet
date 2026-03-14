# vim: expandtab
# -*- coding: utf-8 -*-
from .anonymization import ANONYMIZATION_STRING


def constants(request):
    return {
            u'ANONYMIZATION_STRING': ANONYMIZATION_STRING,
            }
