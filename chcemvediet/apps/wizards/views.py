# vim: expandtab
# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect, HttpResponseBadRequest

from poleno.utils.forms import clean_button

from . import WizardGroup, WizzardRollback

def wizard_view(wizard_class, request, index, finish, *args, **kwargs):

    if issubclass(wizard_class, WizardGroup):
        wizard = wizard_class.find_applicable(*args, **kwargs)
    else:
        wizard = wizard_class(*args, **kwargs)

    try:
        wizard.step(request, index)
    except WizzardRollback as e:
        return HttpResponseRedirect(e.step.get_url())

    if request.method != u'POST':
        return wizard.current_step.render(request)

    button = clean_button(request.POST, [u'save', u'next'])

    if button == u'save':
        wizard.commit()
        return HttpResponseRedirect(wizard.current_step.get_url())

    if button == u'next':
        if not wizard.current_step.is_valid():
            return wizard.current_step.render(request)
        wizard.commit()
        if not wizard.current_step.is_last():
            return HttpResponseRedirect(wizard.next_step().get_url())
        url = finish(wizard)
        wizard.reset()
        return HttpResponseRedirect(url)

    return HttpResponseBadRequest()
