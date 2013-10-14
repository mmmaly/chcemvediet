# vim: expandtab
from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

from menu import ObligeesMenu

@apphook_pool.register
class ObligeesApp(CMSApp):
    app_name = 'obligees'
    name = _('Obligees App')
    urls = ['chcemvediet.apps.obligees.urls']
    menus = [ObligeesMenu]

