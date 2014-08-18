# vim: expandtab
from django.conf.urls import patterns, url
from django.utils.translation import ugettext_lazy as _

import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(_(r'^create/$'), views.create, name='create'),
    url(_(r'^detail/(?P<application_id>\d+)/$'), views.detail, name='detail'),
)

