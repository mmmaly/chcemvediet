# vim: expandtab
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from cms.menu_bases import CMSAttachMenu
from menus.base import NavigationNode
from menus.menu_pool import menu_pool

class ObligeesMenu(CMSAttachMenu):
    name = _("Obligees Menu")

    def get_nodes(self, request):
        return [
            #NavigationNode(_('Obligees'), reverse('obligees:index'), 1),
            ]

menu_pool.register_menu(ObligeesMenu) # cannot be used as a decorator (django-cms authors: wtf, why?)
