# vim: expandtab
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^', include('chcemvediet.apps.main.urls', namespace='main')),
    url(r'^accounts/', include('chcemvediet.apps.accounts.urls', namespace='accounts')),
    url(r'^obligees/', include('chcemvediet.apps.obligees.urls', namespace='obligees')),
    url(r'^applications/', include('chcemvediet.apps.applications.urls', namespace='applications')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
