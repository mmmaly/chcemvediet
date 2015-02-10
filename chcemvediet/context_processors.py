# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf import settings

def devbar(request):
    return {u'DEVBAR_MESSAGE': settings.DEVBAR_MESSAGE}
