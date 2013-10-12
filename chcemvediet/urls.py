# vim: expandtab
from django.conf.urls import patterns, include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.conf import settings
from cms.sitemaps import CMSSitemap

#import views

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^sitemap[.]xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': {'cmspages': CMSSitemap}}),
)

urlpatterns += i18n_patterns('',
    url(r'^accounts/', include('allauth.urls')),
    url(r'^accounts/', include('chcemvediet.apps.accounts.urls', namespace='accounts')),
    url(r'^obligees/', include('chcemvediet.apps.obligees.urls', namespace='obligees')),
    url(r'^applications/', include('chcemvediet.apps.applications.urls', namespace='applications')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^', include('cms.urls')),
)

if settings.DEBUG:
    urlpatterns = patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        url(r'', include('django.contrib.staticfiles.urls')),
    ) + urlpatterns

