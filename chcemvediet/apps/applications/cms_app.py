# vim: expandtab
from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

from menu import ApplicationsMenu

@apphook_pool.register
class ApplicationsApp(CMSApp):
    app_name = 'applications'
    name = _('Applications App')
    urls = ['chcemvediet.apps.applications.urls']
    menus = [ApplicationsMenu]

