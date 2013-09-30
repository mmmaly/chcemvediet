# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.core.exceptions import ValidationError


class Obligee(models.Model):
    name = models.CharField(max_length=255)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    zip = models.CharField(max_length=10)
    email = models.EmailField(max_length=255)
    slug = models.SlugField(max_length=255)
    def __unicode__(self):
        return self.name

def validate_obligee_name_exists(value):
    if not Obligee.objects.filter(name=value).exists():
        raise ValidationError(u'Neznáma povinná osoba. Vyber z menu.')

