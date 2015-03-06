# vim: expandtab
# -*- coding: utf-8 -*-
import warnings
from django.contrib import admin
from django.utils.deprecation import RemovedInDjango18Warning
from adminplus.sites import AdminSitePlus

# Imported from ``urls.py`` to initialize the project after all included apps were initialized.

admin.site = AdminSitePlus()
admin.site.disable_action('delete_selected')
admin.autodiscover()

# Django-admin-tools raises deprecation warnings in Django 1.7. We silence them until they fix it.
# See: https://bitbucket.org/izi/django-admin-tools/issue/153/django-17-firstof-cycle-deprecation
warnings.filterwarnings(u'ignore',
        message=u"'The `(firstof|cycle)` template tag is changing to escape its arguments; the non-autoescaping version is deprecated. .*",
        category=RemovedInDjango18Warning,
        )
