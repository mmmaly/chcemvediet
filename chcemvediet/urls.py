# vim: expandtab
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^', include('chcemvediet.apps.main.urls', namespace='main')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^accounts/', include('chcemvediet.apps.accounts.urls', namespace='accounts')),
    url(r'^obligees/', include('chcemvediet.apps.obligees.urls', namespace='obligees')),
    url(r'^applications/', include('chcemvediet.apps.applications.urls', namespace='applications')),
    url(r'^admin/', include(admin.site.urls)),
)

