# vim: expandtab
# -*- coding: utf-8 -*-
from numbers import Number, Real, Integral
from collections import Mapping, defaultdict

from django.core.exceptions import ValidationError

from poleno.utils.misc import slugify, ensure_tuple

from .datasheets import common_repr, CellError


class Columns(object):

    def __init__(self, **kwargs):
        for name, column in kwargs.items():
            column.name = name
            if column.field is not None:
                column.field.name = name
                column.field.column = column
        vars(self).update(kwargs)

class Column(object):
    value_type = None

    def __init__(self, label, default=None, null=False, blank=False, choices=None, unique=False,
            validators=None, coercers=None, post_coerce_validators=None, field=None):
        self.name = None
        self.label = label
        self.default = default # pre coerce
        self.null = null # pre coerce
        self.blank = blank # post coerce
        self.choices = choices # pre coerce + coerce if it is mapping
        self.unique = unique # post coerce
        self.validators = validators # pre coerce
        self.coercers = coercers # coerce
        self.post_coerce_validators = post_coerce_validators # post coerce
        self.field = field

    def validate_type(self, value):
        if self.value_type is None:
            return
        if self.null and value is None:
            return
        if not isinstance(value, self.value_type):
            raise CellError(u'type', u'Expecting {} but found {}',
                    self.value_type.__name__, value.__class__.__name__)

    def validate_choices(self, value):
        if self.choices is None:
            return
        if value not in self.choices:
            raise CellError(u'choices', u'Expecting one of {} but found {}',
                    u', '.join(self.value_repr(c) for c in self.choices),
                    self.value_repr(value))

    def validate_pre_coerce_validators(self, value):
        if self.validators is None:
            return
        for validator in ensure_tuple(self.validators):
            try:
                validator(value)
            except ValidationError as e:
                raise CellError((u'validator', validator.__name__), u'; '.join(e.messages))

    def do_pre_coerce_validation(self, sheet, row_idx, value):
        self.validate_type(value)
        self.validate_choices(value)
        self.validate_pre_coerce_validators(value)

    def apply_choices(self, value):
        if not isinstance(self.choices, Mapping):
            return value
        return self.choices[value]

    def apply_coercers(self, value):
        if self.coercers is None:
            return value
        for coercer in ensure_tuple(self.coercers):
            value = coercer(value)
        return value

    def do_coerce(self, sheet, row_idx, value):
        value = self.apply_choices(value)
        value = self.apply_coercers(value)
        return value

    def validate_blank(self, value):
        if self.blank:
            return
        if not value:
            raise CellError(u'blank', u'Expecting nonempty value but found {}',
                    self.coerced_repr(value))

    def validate_unique(self, sheet, row_idx, value):
        if not self.unique:
            return
        if not hasattr(sheet, u'_validate_unique_cache'):
            sheet._validate_unique_cache = defaultdict(dict)
        if value in sheet._validate_unique_cache[self]:
            raise CellError(u'unique', u'Expecting unique value but {} is in row {} as well',
                    self.coerced_repr(value), sheet._validate_unique_cache[self][value])
        sheet._validate_unique_cache[self][value] = row_idx

    def validate_post_coerce_validators(self, value):
        if self.post_coerce_validators is None:
            return
        for validator in ensure_tuple(self.post_coerce_validators):
            try:
                validator(value)
            except ValidationError as e:
                raise CellError((u'validator', validator.__name__), u'; '.join(e.messages))

    def do_post_ceorce_validation(self, sheet, row_idx, value):
        self.validate_blank(value)
        self.validate_unique(sheet, row_idx, value)
        self.validate_post_coerce_validators(value)

    def do_import(self, sheet, row_idx, value):
        self.do_pre_coerce_validation(sheet, row_idx, value)
        value = self.do_coerce(sheet, row_idx, value)
        self.do_post_ceorce_validation(sheet, row_idx, value)
        return value

    def value_repr(self, value):
        return common_repr(value)

    def coerced_repr(self, value):
        return common_repr(value)

class TextColumn(Column):
    value_type = str

    def __init__(self, label, min_length=None, max_length=None, regex=None, unique_slug=False,
            **kwargs):
        kwargs.setdefault(u'default', u'')
        super(TextColumn, self).__init__(label, null=False, **kwargs)
        self.min_length = min_length # pre coerce
        self.max_length = max_length # pre coerce
        self.regex = regex # pre coerce
        self.unique_slug = unique_slug # pre coerce

    def validate_min_length(self, value):
        if self.min_length is None:
            return
        if len(value) < self.min_length:
            raise CellError(u'min_length',
                    u'Expecting value not shorter than {} but found "{}" with length {}',
                    self.min_length, value, len(value))

    def validate_max_length(self, value):
        if self.max_length is None:
            return
        if len(value) > self.max_length:
            raise CellError(u'max_length',
                    u'Expecting value not longer than {} but found {} with length {}',
                    self.max_length, self.value_repr(value), len(value))

    def validate_regex(self, value):
        if self.regex is None:
            return
        if not self.regex.match(value):
            raise CellError(u'regex',
                    u'Expecting value matching "{}" but found {}',
                    self.regex.pattern, self.value_repr(value))

    def validate_unique_slug(self, sheet, row_idx, value):
        if not self.unique_slug:
            return
        if not hasattr(sheet, u'_validate_unique_slug_cache'):
            sheet._validate_unique_slug_cache = defaultdict(dict)
        slug = slugify(value)
        if slug in sheet._validate_unique_slug_cache[self]:
            other_row, other_value = sheet._validate_unique_slug_cache[self][slug]
            raise CellError(u'unique_slug',
                    u'Expecting value with unique slug but {} has the same slug as {} in row {}',
                    self.value_repr(value), self.value_repr(other_value), other_row)
        sheet._validate_unique_slug_cache[self][slug] = (row_idx, value)
        return value

    def do_pre_coerce_validation(self, sheet, row_idx, value):
        super(TextColumn, self).do_pre_coerce_validation(sheet, row_idx, value)
        self.validate_min_length(value)
        self.validate_max_length(value)
        self.validate_regex(value)
        self.validate_unique_slug(sheet, row_idx, value)

class NumericColumn(Column):
    value_type = Number

    def __init__(self, label, min_value=None, max_value=None, **kwargs):
        super(NumericColumn, self).__init__(label, **kwargs)
        self.min_value = min_value # pre coerce
        self.max_value = max_value # pre coerce

    def validate_min_value(self, value):
        if self.min_value is None:
            return
        if value < self.min_value:
            raise CellError(u'min_value',
                    u'Expecting value not smaller than {} but found {}',
                    self.min_value, self.value_repr(value))

    def validate_max_value(self, value):
        if self.max_value is None:
            return
        if value > self.max_value:
            raise CellError(u'max_value',
                    u'Expecting value not bigger than {} but found {}',
                    self.max_value, self.value_repr(value))

    def do_pre_coerce_validation(self, sheet, row_idx, value):
        super(NumericColumn, self).do_pre_coerce_validation(sheet, row_idx, value)
        self.validate_min_value(value)
        self.validate_max_value(value)

class FloatColumn(NumericColumn):
    value_type = Real

class IntegerColumn(NumericColumn):
    value_type = Integral

class FieldChoicesColumn(Column):
    value_type = None

    def __init__(self, label, field_choices, **kwargs):
        kwargs.setdefault(u'choices', {n: v for v, n in field_choices._inverse.items()})
        super(FieldChoicesColumn, self).__init__(label, **kwargs)
        self.field_choices = field_choices

    def coerced_repr(self, value):
        return self.field_choices._inverse[value]

class ForeignKeyColumn(Column):
    value_type = None

    def __init__(self, label, to_model, to_field=u'pk', **kwargs):
        super(ForeignKeyColumn, self).__init__(label, choices=None, **kwargs)
        self.to_model = to_model
        self.to_field = to_field

    def apply_relation(self, sheet, value):
        try:
            obj = self.to_model.objects.get(**{self.to_field: str(value)})
        except self.to_model.DoesNotExist:
            raise CellError(u'relation_not_found', u'There is no {} with {}={}',
                    self.to_model.__name__, self.to_field, self.value_repr(value))
        except self.to_model.MultipleObjectsReturned:
            raise CellError(u'relation_found_more', u'There are multiple {} with {}={}',
                    self.to_model.__name__, self.to_field, self.value_repr(value))
        except Exception as e:
            raise CellError(u'relation_type', u'Invalid value {} for {}: {}',
                    self.value_repr(value), self.to_field, e)
        if obj in sheet.book.marked_for_deletion:
            raise CellError(u'deleted', u'{} with {}={} was omitted and is going to be deleted',
                    self.to_model.__name__, self.to_field, self.value_repr(value))
        return obj

    def do_coerce(self, sheet, row_idx, value):
        value = super(ForeignKeyColumn, self).do_coerce(sheet, row_idx, value)
        value = self.apply_relation(sheet, value)
        return value

class ManyToManyColumn(ForeignKeyColumn):
    value_type = str

    def __init__(self, label, to_model, **kwargs):
        kwargs.setdefault(u'default', u'')
        super(ManyToManyColumn, self).__init__(label, to_model, null=False, unique=False, **kwargs)

    def apply_relation(self, sheet, value):
        res = []
        for key in value.split():
            obj = super(ManyToManyColumn, self).apply_relation(sheet, key)
            res.append(obj)
        return res
