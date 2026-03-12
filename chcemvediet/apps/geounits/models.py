# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Q, F

from poleno import datacheck
from poleno.utils.models import QuerySet
from poleno.utils.misc import FormatMixin, squeeze, decorate, slugify


class RegionQuerySet(QuerySet):
    def order_by_pk(self):
        return self.order_by(u'pk')
    def order_by_name(self):
        return self.order_by(u'name') # no tiebreaker, name is unique

class Region(FormatMixin, models.Model): # "Kraj"
    # Primary key
    id = models.CharField(max_length=32, primary_key=True,
            help_text=squeeze(u"""
                Region primary key. Example: "SK031" (REGPJ.RSUJ3)
                """))

    # Should NOT be empty
    name = models.CharField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique human readable region name. (REGPJ.NAZKRJ, REGPJ.NAZRSUJ3)
                """))

    # Should NOT be empty; Read-only; Automaticly computed in save()
    slug = models.SlugField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique slug to identify the region used in urls. Automaticly computed from the
                region name. May not be changed manually.
                """))

    # Backward relations:
    #
    #  -- district_set: by District.region
    #     May be empty
    #
    #  -- municipality_set: by Municipality.region
    #     May be empty
    #
    #  -- neighbourhood_set: by Neighbourhood.region
    #     May be empty

    # Indexes:
    #  -- id:   primary_key
    #  -- name: unique
    #  -- slug: unique

    objects = RegionQuerySet.as_manager()

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        update_fields = kwargs.get(u'update_fields', None)

        # Generate and save slug if saving name
        if update_fields is None or u'name' in update_fields:
            self.slug = slugify(self.name)
            if update_fields is not None:
                update_fields.append(u'slug')

        super(Region, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'[{}] {}'.format(self.pk, self.name)


class DistrictQuerySet(QuerySet):
    def order_by_pk(self):
        return self.order_by(u'pk')
    def order_by_name(self):
        return self.order_by(u'name') # no tiebreaker, name is unique

class District(FormatMixin, models.Model): # "Okres"
    # Primary key
    id = models.CharField(max_length=32, primary_key=True,
            help_text=squeeze(u"""
                District primary key. Example: "SK031B" (REGPJ.LSUJ1)
                """))

    # Should NOT be empty
    name = models.CharField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique human readable district name. (REGPJ.NAZOKS, REGPJ.NAZLSUJ1)
                """))

    # Should NOT be empty; Read-only; Automaticly computed in save()
    slug = models.SlugField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique slug to identify the district used in urls. Automaticly computed from the
                district name. May not be changed manually.
                """))

    # May NOT be NULL
    region = models.ForeignKey(Region, on_delete=models.CASCADE, help_text=u'Region the district belongs to.')

    # Backward relations:
    #
    #  -- municipality_set: by Municipality.district
    #     May be empty
    #
    #  -- neighbourhood_set: by Neighbourhood.district
    #     May be empty

    # Backward relations added to other models:
    #
    #  -- Region.district_set
    #     May be empty

    # Indexes:
    #  -- id:     primary_key
    #  -- name:   unique
    #  -- slug:   unique
    #  -- region: ForeignKey

    objects = DistrictQuerySet.as_manager()

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        update_fields = kwargs.get(u'update_fields', None)

        # Generate and save slug if saving name
        if update_fields is None or u'name' in update_fields:
            self.slug = slugify(self.name)
            if update_fields is not None:
                update_fields.append(u'slug')

        super(District, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'[{}] {}'.format(self.pk, self.name)


class MunicipalityQuerySet(QuerySet):
    def order_by_pk(self):
        return self.order_by(u'pk')
    def order_by_name(self):
        return self.order_by(u'name') # no tiebreaker, name is unique

class Municipality(FormatMixin, models.Model): # "Obec"
    # Primary key
    id = models.CharField(max_length=32, primary_key=True,
            help_text=squeeze(u"""
                Municipality primary key. Example: "SK031B518042" (REGPJ.LSUJ2)
                """))

    # Should NOT be empty
    name = models.CharField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique human readable municipality name. If municipality name is ambiguous it
                should be amedned with its district name. (REGPJ.NAZZUJ, REGPJ.NAZLSUJ2)
                """))

    # Should NOT be empty; Read-only; Automaticly computed in save()
    slug = models.SlugField(max_length=255, unique=True,
            help_text=squeeze(u"""
                Unique slug to identify the municipality used in urls. Automaticly computed from
                the municipality name. May not be changed manually.
                """))

    # May NOT be NULL
    district = models.ForeignKey(District, on_delete=models.CASCADE, help_text=u'District the municipality belongs to.')
    region = models.ForeignKey(Region, on_delete=models.CASCADE, help_text=u'Region the municipality belongs to.')

    # Backward relations:
    #
    #  -- neighbourhood_set: by Neighbourhood.municipality
    #     May be empty

    # Backward relations added to other models:
    #
    #  -- District.municipality_set
    #     May be empty
    #
    #  -- Region.municipality_set
    #     May be empty

    # Indexes:
    #  -- id:       primary_key
    #  -- name:     unique
    #  -- slug:     unique
    #  -- region:   ForeignKey
    #  -- district: ForeignKey

    objects = MunicipalityQuerySet.as_manager()

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs):
        update_fields = kwargs.get(u'update_fields', None)

        # Generate and save slug if saving name
        if update_fields is None or u'name' in update_fields:
            self.slug = slugify(self.name)
            if update_fields is not None:
                update_fields.append(u'slug')

        super(Municipality, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'[{}] {}'.format(self.pk, self.name)


class NeighbourhoodQuerySet(QuerySet):
    def order_by_pk(self):
        return self.order_by(u'pk')

class Neighbourhood(FormatMixin, models.Model): # "Základná sídelná jednotka"
    # Primary key
    id = models.CharField(max_length=32, primary_key=True,
            help_text=squeeze(u"""
                Neighbourhood primary key. Example: "26289" (REGPJ.ICZSJ)
                """))

    # Should NOT be empty
    name = models.CharField(max_length=255,
            help_text=squeeze(u"""
                Human readable neighbourhood name. Neighbourhood names are not unique, not even
                within a municipality. (REGPJ.NAZZSJ)
                """))

    # Should NOT be empty
    cadastre = models.CharField(max_length=255,
            help_text=squeeze(u"""
                Human readable neighbourhood cadastre name. (REGPJ.NAZUTJ)
                """))

    # May NOT be NULL
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE,
            help_text=u'Municipality the neighbourhood belongs to.')
    district = models.ForeignKey(District, on_delete=models.CASCADE,
            help_text=u'District the neighbourhood belongs to.')
    region = models.ForeignKey(Region, on_delete=models.CASCADE,
            help_text=u'Region the neighbourhood belongs to.')

    # Backward relations added to other models:
    #
    #  -- Municipality.neighbourhood_set
    #     May be empty
    #
    #  -- District.neighbourhood_set
    #     May be empty
    #
    #  -- Region.neighbourhood_set
    #     May be empty

    # Indexes:
    #  -- id:                 primary_key
    #  -- region:             ForeignKey
    #  -- district:           ForeignKey
    #  -- municipality:       ForeignKey

    objects = NeighbourhoodQuerySet.as_manager()

    def __unicode__(self):
        return u'[{}] {}'.format(self.pk, self.name)


@datacheck.register
def datachecks(superficial, autofix):
    u"""
    Checks that Region, District, Municipality and Neighbourhood relations are consistent.
    """
    # Checks that municipality.region is municipality.district.region
    municipalities = (Municipality.objects
            .filter(~Q(district__region=F(u'region')))
            .select_related(u'district')
            )
    if superficial:
        municipalities = municipalities[:5+1]
    issues = [u'{} has region_id="{}" but district.region_id="{}"'.format(
            m, m.region_id, m.district.region_id) for m in municipalities]
    if superficial and issues:
        if len(issues) > 5:
            issues[-1] = u'More municipalities have invalid region references'
        issues = [u'; '.join(issues)]
    for issue in issues:
        yield datacheck.Error(issue + u'.')

    # Checks that neighbourhood.district is neighbourhood.municipality.district
    neighbourhoods = (Neighbourhood.objects
            .filter(~Q(municipality__district=F(u'district')))
            .select_related(u'municipality')
            )
    if superficial:
        neighbourhoods = neighbourhoods[:5+1]
    issues = [u'{} has district_id="{}" but municipality.district_id="{}"'.format(
            n, n.district_id, n.municipality.district_id) for n in neighbourhoods]
    if superficial and issues:
        if len(issues) > 5:
            issues[-1] = u'More neighbourhoods have invalid district references'
        issues = [u'; '.join(issues)]
    for issue in issues:
        yield datacheck.Error(issue + u'.')

    # Checks that neighbourhood.region is neighbourhood.district.region
    neighbourhoods = (Neighbourhood.objects
            .filter(~Q(district__region=F(u'region')))
            .select_related(u'district')
            )
    if superficial:
        neighbourhoods = neighbourhoods[:5+1]
    issues = [u'{} has region_id="{}" but district.region_id="{}"'.format(
            n, n.region_id, n.district.region_id) for n in neighbourhoods]
    if superficial and issues:
        if len(issues) > 5:
            issues[-1] = u'More neighbourhoods have invalid region references'
        issues = [u'; '.join(issues)]
    for issue in issues:
        yield datacheck.Error(issue + u'.')
