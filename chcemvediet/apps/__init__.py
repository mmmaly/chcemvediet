from django.apps import AppConfig


class ChcemvedietConfig(AppConfig):
    name = u'chcemvediet'

    def init_admin_site_plus(self):
        from vendor.adminplus.sites import AdminSitePlus
        from django.contrib import admin
        from django.contrib.admin import sites as admin_sites
        admin.site = AdminSitePlus()
        admin_sites.site = admin.site
        admin.site.disable_action(u'delete_selected')
        admin.autodiscover()

    def ready(self):
        self.init_admin_site_plus()
