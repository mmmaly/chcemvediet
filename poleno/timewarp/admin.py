# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from poleno.utils.form import clean_button

import timewarp
import forms

@admin.site.register_view(u'timewarp/', name=_(u'Timewarp'), urlname=u'timewarp')
@require_http_methods([u'HEAD', u'GET', u'POST'])
def index(request):
    if request.method == u'POST':
        button = clean_button(request.POST, [u'jump', u'reset'])

        if button == u'jump':
            form = forms.WarpForm(request.POST)
            if form.is_valid():
                jumpto = form.cleaned_data[u'jumpto']
                speedup = form.cleaned_data[u'speedup']
                if jumpto is not None or speedup is not None:
                    timewarp.jump(jumpto, speedup)
                return HttpResponseRedirect(reverse(u'admin:timewarp'))

        if button == u'reset':
            timewarp.reset()
            return HttpResponseRedirect(reverse(u'admin:timewarp'))
    else:
        form = forms.WarpForm()

    return render(request, u'timewarp/timewarp.html', {
            u'is_warped': timewarp.is_warped(),
            u'time_real': timewarp.time_real(),
            u'time_warped': timewarp.time_warped(),
            u'speedup': timewarp.speedup,
            u'form': form,
            u'title': _(u'Timewarp'),
            })
