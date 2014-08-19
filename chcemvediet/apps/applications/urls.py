# vim: expandtab
from django.conf.urls import patterns, url
from django.utils.translation import ugettext_lazy as _

import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(_(r'^create/$'), views.create, name='create'),
    url(_(r'^create/(?P<draft_id>\d+)/$'), views.create, name='create_from_draft'),
    url(_(r'^detail/(?P<application_id>\d+)/$'), views.detail, name='detail'),
    url(_(r'^delete-draft/(?P<draft_id>\d+)/$'), views.delete_draft, name='delete_draft'),
)

