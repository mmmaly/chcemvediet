# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class Obligee(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    street = models.CharField(max_length=255, verbose_name=_('Street'))
    city = models.CharField(max_length=255, verbose_name=_('City'))
    zip = models.CharField(max_length=10, verbose_name=_('Zip'))
    email = models.EmailField(max_length=255, verbose_name=_('E-mail'))
    slug = models.SlugField(max_length=255, verbose_name=_('Slug'))
    def __unicode__(self):
        return self.name

def validate_obligee_name_exists(value):
    if not Obligee.objects.filter(name=value).exists():
        raise ValidationError(_(u'Invalid obligee name. Select one form the menu.'))

