# vim: expandtab
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from cms.menu_bases import CMSAttachMenu
from menus.base import NavigationNode
from menus.menu_pool import menu_pool

class ApplicationsMenu(CMSAttachMenu):
    name = _("Applications Menu")

    def get_nodes(self, request):
        return [
            NavigationNode(_('New Application'), reverse('applications:create'), 1),
            ]

menu_pool.register_menu(ApplicationsMenu) # cannot be used as a decorator (django-cms authors: wtf, why?)

