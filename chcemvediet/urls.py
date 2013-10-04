# vim: expandtab
from django.conf.urls import patterns, include, url
from django.contrib import admin

import views

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^accounts/', include('chcemvediet.apps.accounts.urls', namespace='accounts')),
    url(r'^obligees/', include('chcemvediet.apps.obligees.urls', namespace='obligees')),
    url(r'^applications/', include('chcemvediet.apps.applications.urls', namespace='applications')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
)

