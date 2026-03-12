# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf import settings
from django.urls import re_path, include
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView
from django.contrib import admin
from django.contrib.sitemaps import views as sitemaps_views
from django.utils.translation import gettext_lazy as _
from django.views.static import serve

from poleno.utils.lazy import lazy_format

from . import views
from .sitemaps import sitemaps


urlpatterns = [
    re_path(r'^sitemap[.]xml$', sitemaps_views.sitemap, kwargs=dict(sitemaps=sitemaps)),
    re_path(r'^mandrill/', include(u'poleno.mail.transports.mandrill.urls', namespace=u'mandrill')),
    re_path(r'^styleguide/$', TemplateView.as_view(template_name=u'styleguide/main.html'), name=u'styleguide'),
    re_path(r'^i18n/', include(u'django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    re_path(r'^$', views.homepage, name=u'homepage'),
    re_path(lazy_format(r'^{0}/$', _(u'main:urls:search')),       views.search, name=u'search'),
    re_path(lazy_format(r'^{0}/',  _(u'main:urls:obligees')),     include(u'chcemvediet.apps.obligees.urls', namespace=u'obligees')),
    re_path(lazy_format(r'^{0}/',  _(u'main:urls:inforequests')), include(u'chcemvediet.apps.inforequests.urls', namespace=u'inforequests')),
    re_path(lazy_format(r'^{0}/',  _(u'main:urls:invitations')),  include(u'poleno.invitations.urls', namespace=u'invitations')),
    re_path(r'^accounts/', include(u'allauth.urls')),
    re_path(r'^accounts/', include(u'chcemvediet.apps.accounts.urls', namespace=u'accounts')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'', include(u'poleno.pages.urls', namespace=u'pages')),
)

if settings.DEBUG: # pragma: no cover
    urlpatterns = [
        re_path(r'^media/(?P<path>.*)$', serve, {u'document_root': settings.MEDIA_ROOT, u'show_indexes': True}),
        re_path(r'', include(u'django.contrib.staticfiles.urls')),
    ] + urlpatterns
