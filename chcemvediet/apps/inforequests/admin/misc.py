# vim: expandtab
# -*- coding: utf-8 -*-
from django.contrib import admin

class ForeignKeyRawIdWidgetWithUrlParams(admin.widgets.ForeignKeyRawIdWidget):
    def __init__(self, *args, **kwargs):
        super(ForeignKeyRawIdWidgetWithUrlParams, self).__init__(*args, **kwargs)
        self.url_params = {}

    def base_url_parameters(self):
        params = super(ForeignKeyRawIdWidgetWithUrlParams, self).base_url_parameters()
        params.update(self.url_params)
        return params
