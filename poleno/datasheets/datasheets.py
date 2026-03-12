# vim: expandtab
# -*- coding: utf-8 -*-
from collections import defaultdict, OrderedDict
from optparse import make_option
from openpyxl import load_workbook

from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import color_style
from django.db import transaction, DEFAULT_DB_ALIAS
from django.contrib.admin.utils import NestedObjects
from django.utils.text import capfirst

from poleno.utils.misc import squeeze, Bunch


def common_repr(value):
    if isinstance(value, str):
        return u'"{}"'.format(value)
    else:
        return repr(value)


class RollingError(Exception):
    def __init__(self, count=1):
        self.count = count
        super(RollingError, self).__init__()

class CellError(Exception):
    def __init__(self, code, msg, *args, **kwargs):
        self.code = code
        msg = msg.format(*args, **kwargs) if args or kwargs else msg
        super(CellError, self).__init__(msg)

class RollbackDryRun(Exception):
    pass


class Sheet(object):
    label = None
    model = None
    ignore_superfluous_columns = False
    delete_omitted = True
    columns = None

    def __init__(self, book, ws):
        self.book = book
        self.importer = book.importer
        self.ws = ws
        self.column_map = None

    def error(self, code, msg, *args, **kwargs):
        if code:
            code = (self.label, code)
        self.importer.error(code, msg, *args, **kwargs)

    def cell_error(self, code, row_idx, column, msg, *args, **kwargs):
        msg = msg.format(*args, **kwargs) if args or kwargs else msg
        self.error((column.label, code), u'Invalid value in row {} of "{}.{}": {}',
                row_idx, self.label, column.label, msg)

    def reset_model(self, model):
        count = model.objects.count()
        model.objects.all().delete()
        self.importer.write(1, u'Reset {}: {} deleted', model.__name__, count)

    def do_reset(self):
        self.reset_model(self.model)

    def validate_structure(self):
        errors = 0

        self.column_map = {}
        row = next(self.ws.rows, [])
        for col_idx, column in enumerate(row):
            if column.value is None or column.value.startswith(u'#'):
                continue
            if column.value in self.column_map:
                self.error(None, u'Sheet "{}" contains duplicate column: {}',
                        self.label, column.value)
                errors += 1
            else:
                self.column_map[column.value] = col_idx

        expected_columns = set(c.label for c in self.columns.__dict__.values())
        found_columns = set(self.column_map)
        missing_columns = expected_columns - found_columns
        superfluous_columns = found_columns - expected_columns
        for column in missing_columns:
            self.error(None, u'Sheet "{}" does not contain required column: {}', self.label, column)
            errors += 1
        if not self.ignore_superfluous_columns:
            for column in superfluous_columns:
                self.error(None, u'Sheet "{}" contains unexpected column: {}', self.label, column)
                errors += 1

        if errors:
            raise RollingError(errors)

    def process_cell(self, row_idx, row, column):
        try:
            col_idx = self.column_map[column.label]
        except KeyError:
            self.cell_error(u'missing', row_idx, column, u'Missing column')
            raise RollingError

        try:
            value = row[col_idx].value
        except IndexError:
            value = None
        if value is None:
            value = column.default

        try:
            return column.do_import(self, row_idx, value)
        except CellError as e:
            self.cell_error(e.code, row_idx, column, e)
            raise RollingError

    def process_row(self, row_idx, row):
        res = {}
        errors = 0
        for column in self.columns.__dict__.values():
            try:
                res[column.label] = self.process_cell(row_idx, row, column)
            except RollingError as e:
                errors += e.count
        if errors:
            raise RollingError(errors)
        return res

    def process_rows(self, rows):
        res = OrderedDict()
        errors = 0
        for row_idx, row in enumerate(rows, start=1):
            if row_idx == 1 or all(c.value is None for c in row):
                continue
            try:
                res[row_idx] = self.process_row(row_idx, row)
            except RollingError as e:
                errors += e.count
        if errors:
            raise RollingError(errors)
        return res

    def process_fields(self, row_idx, values, original):
        res = {}
        errors = 0
        for column in self.columns.__dict__.values():
            if column.field is not None:
                field = column.field
                try:
                    res[field.name] = field.do_import(self, row_idx, values, original)
                except RollingError as e:
                    errors += e.count
        if errors:
            raise RollingError(errors)
        return res

    def save_object(self, fields, original):
        # Save only if the instance is new or changed to prevent excessive change history. Many to
        # many relations may only be saved after the instance is created.
        obj = original or self.model()
        has_changed = False
        for column in self.columns.__dict__.values():
            if column.field is not None:
                field = column.field
                value = fields[field.name]
                if not field.is_related and field.has_changed(obj, value):
                    field.save(obj, value)
                    has_changed = True
        if has_changed:
            obj.save()
        for column in self.columns.__dict__.values():
            if column.field is not None:
                field = column.field
                value = fields[field.name]
                if field.is_related and field.has_changed(obj, value):
                    field.save(obj, value)
                    has_changed = True
        return obj, has_changed

    def save_objects(self, rows):
        errors = 0
        stats = Bunch(created=0, changed=0, unchanged=0, deleted=0)
        originals = {o.pk: o for o in self.model.objects.all()}
        for row_idx, values in rows.items():
            try:
                pk = values[self.columns.pk.label]
                original = originals.pop(pk, None)
                fields = self.process_fields(row_idx, values, original)
                assert fields[u'pk'] == pk

                obj, has_changed = self.save_object(fields, original)
                if has_changed and original:
                    self.importer.write(2, u'Changed {}', self.obj_repr(obj))
                    stats.changed += 1
                elif has_changed:
                    self.importer.write(2, u'Created {}', self.obj_repr(obj))
                    stats.created += 1
                else:
                    stats.unchanged += 1
            except RollingError as e:
                errors += e.count
        # Mark omitted instances for deletion or add an error if delete is not permitted. Don't
        # delete anything if there were any errors as we don't know which instances are missing for
        # real and which are missing because of errors. The instances will be deleted only after
        # all sheets are imported to prevent unintentional cascades.
        if errors:
            raise RollingError(errors)
        for obj in originals.values():
            if self.delete_omitted:
                self.book.marked_for_deletion[obj] = self
                stats.deleted += 1
            else:
                self.error(u'omitted', u'Omitted {}', self.obj_repr(obj))
                errors += 1
        if errors:
            raise RollingError(errors)
        return stats

    def do_import(self):
        self.importer.write(1, u'Importing {}...', self.model.__name__)
        errors = 0

        try:
            self.validate_structure()
        except RollingError as e:
            errors += e.count

        try:
            rows = self.process_rows(self.ws.rows)
            stats = self.save_objects(rows)
        except RollingError as e:
            errors += e.count

        if errors:
            self.importer.write(1, u'Importing {} failed.', self.model.__name__)
            raise RollingError(errors)

        self.importer.write(1,
                u'Imported {}: {} created, {} changed, {} unchanged and {} marked for deletion',
                self.model.__name__, stats.created, stats.changed, stats.unchanged, stats.deleted)

    def _collect_related_format(self, collected, level=0):
        res = []
        for obj in collected:
            if isinstance(obj, list):
                res.extend(self._collect_related_format(obj, level=level+1))
            else:
                res.append(u'\n\t{}-- {}: {}'.format(u'    '*level,
                        capfirst(obj._meta.verbose_name), common_repr(obj)))
        return res

    def _collect_related(self, obj):
        collector = NestedObjects(using=DEFAULT_DB_ALIAS)
        collector.collect([obj])
        collected = collector.nested()
        return u''.join(self._collect_related_format(collected))

    def delete_object(self, obj):
        inputed = self.importer.input_yes_no(
                u'{} was omitted. All the following related items will be deleted with it:{}',
                u'Are you sure, you want to delete it?',
                self.obj_repr(obj), self._collect_related(obj),
                default=u'N')
        if inputed != u'Y':
            raise RollingError
        obj.delete()

    def obj_repr(self, obj):
        return common_repr(obj)

class Book(object):
    sheets = None

    def __init__(self, importer, wbs):
        self.importer = importer
        self.wbs = wbs
        self.marked_for_deletion = None
        self.sheet_map = None

    def validate_structure(self):
        self.sheet_map = {}
        for wb in self.wbs:
            for sheet in wb.get_sheet_names():
                if sheet.startswith(u'#'):
                    continue
                if sheet in self.sheet_map:
                    raise CommandError(u'The files contain duplicate sheet: {}'.format(sheet))
                self.sheet_map[sheet] = wb[sheet]

        expected_sheets = set(s.label for s in self.sheets)
        found_sheets = set(self.sheet_map.keys())
        missing_sheets = expected_sheets - found_sheets
        superfluous_sheets = found_sheets - expected_sheets
        actual_sheets = expected_sheets & found_sheets
        if superfluous_sheets:
            inputed = self.importer.input_yes_no(
                    u'The files contain the following unexpected sheets:{}',
                    u'Ignore them?',
                    u''.join(u'\n\t-- {}'.format(s) for s in superfluous_sheets),
                    default=u'Y')
            if inputed != u'Y':
                raise CommandError(u'The files contain unexpected sheets')
        if missing_sheets:
            inputed = self.importer.input_yes_no(
                    u'The files contain only the following sheets:{}\n'
                    u'The following sheets are missing:{}',
                    u'Skip missing sheets and import only the present ones?',
                    u''.join(u'\n\t-- {}'.format(s) for s in actual_sheets),
                    u''.join(u'\n\t-- {}'.format(s) for s in missing_sheets),
                    default=u'Y')
            if inputed != u'Y':
                raise CommandError(u'The files do not contain required sheets')

    def do_import(self):
        errors = 0
        self.validate_structure()

        sheets = []
        for sheet in self.sheets:
            if sheet.label in self.sheet_map:
                ws = self.sheet_map[sheet.label]
                sheets.append(sheet(self, ws))

        if self.importer.reset:
            for sheet in reversed(sheets):
                sheet.do_reset()

        self.marked_for_deletion = OrderedDict()
        for sheet in sheets:
            try:
                sheet.do_import()
            except RollingError as e:
                errors += e.count

        for obj, sheet in reversed(self.marked_for_deletion.items()):
            try:
                sheet.delete_object(obj)
            except RollingError as e:
                errors += e.count

        if errors:
            raise RollingError(errors)

class Importer(object):

    def __init__(self, book, options, stdout):
        self.reset = options[u'reset']
        self.dry_run = options[u'dry_run']
        self.assume = options[u'assume']
        self.verbosity = int(options[u'verbosity'])
        self.stdout = stdout
        self.color_style = color_style()
        self.book = book

    def write(self, verbosity, msg, *args, **kwargs):
        if self.verbosity >= verbosity:
            self.stdout.write(msg.format(*args, **kwargs))

    def error(self, code, msg, *args, **kwargs):
        if not hasattr(self, u'_error_cache'):
            self._error_cache = defaultdict(int)

        msg = self.color_style.NOTICE(u'Error: ' + msg.format(*args, **kwargs))

        if self.verbosity == 1:
            if code:
                self._error_cache[code] += 1
                if self._error_cache[code] < 3:
                    self.stdout.write(msg)
                elif self._error_cache[code] == 3:
                    self.stdout.write(msg + u' (skipping further similar errors, use -v2 to see them)')
            else:
                self.stdout.write(msg)
        elif self.verbosity >= 2:
            self.stdout.write(msg)

    def input_yes_no(self, text, prompt, *args, **kwargs):
        default = kwargs.pop(u'default', u'')
        while True:
            self.stdout.write(self.color_style.WARNING(
                    u'Warning: {}'.format(text.format(*args, **kwargs))))
            self.stdout.write(self.color_style.ERROR(
                    u'{} Yes/No/Abort [{}]: '.format(prompt, default)), ending=u'')

            if self.assume:
                if self.assume == u'yes':
                    inputed = u'Yes'
                elif self.assume == u'no':
                    inputed = u'No'
                else:
                    inputed = default
                self.stdout.write(inputed)
            else:
                inputed = input() or default

            if not inputed:
                error = u'The value is required.'
            elif inputed.upper() in [u'A', u'ABORT']:
                raise CommandError(u'Aborted')
            elif inputed.upper() not in [u'Y', u'YES', u'N', u'NO']:
                error = u'Enter Yes, No or Abort.'
            else:
                return inputed.upper()[0]

            if self.assume:
                raise CommandError(error)
            self.stdout.write(self.color_style.ERROR(u'Error: {}'.format(error)))

    @transaction.atomic
    def do_import(self, filenames):
        if self.dry_run:
            self.write(0, u'Importing: {} (dry run)', u', '.join(filenames))
        else:
            self.write(0, u'Importing: {}', u', '.join(filenames))

        wbs = []
        for filename in filenames:
            try:
                wb = load_workbook(filename, read_only=True)
            except Exception as e:
                raise CommandError(u'Could not read input file: {}'.format(e))
            wbs.append(wb)

        try:
            self.book(self, wbs).do_import()
        except RollingError as e:
            raise CommandError(u'Detected {} errors; Rolled back'.format(e.count))

        if self.dry_run:
            self.write(0, u'Rolled back (dry run)')
            raise RollbackDryRun
        else:
            self.write(0, u'Done.')


class LoadSheetsCommand(BaseCommand):
    help = u'Loads .xlsx files with data'
    args = u'file [file ...]'
    option_list = BaseCommand.option_list + (
        make_option(u'--dry-run', action=u'store_true', default=False,
            help=squeeze(u"""
                Just show if the files would be imported correctly. Rollback all changes at the
                end.
                """)),
        make_option(u'--reset', action=u'store_true', default=False,
            help=squeeze(u"""
                Discard current data before imporing the files. Only data from sheets present in
                the files are discarded. Data from missing sheets are left untouched.
                """)),
        make_option(u'--assume', choices=[u'yes', u'no', u'default'],
            help=squeeze(u"""
                Assume yes/no/default answer to all yes/no questions.
                """)),
        )
    importer = Importer
    book = None

    def handle(self, *args, **options):
        if not args:
            raise CommandError(u'No file specified.')

        try:
            importer = self.importer(self.book, options, self.stdout)
            importer.do_import(args)
        except (KeyboardInterrupt, EOFError):
            self.stdout.write(u'\n')
            raise CommandError(u'Aborted')
        except RollbackDryRun:
            pass
