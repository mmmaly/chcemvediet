# vim: expandtab
from textwrap import dedent
from optparse import make_option

from django.core.management.base import NoArgsCommand
from cms.models import Placeholder, CMSPlugin, Page

class Command(NoArgsCommand):
    help = dedent("""\
        Run to delete orphaned Placeholder instances from the database.

        In "django-cms", After you delete a published page, some of its placeholder
        instances are left in the database undeleted. If the orphaned placeholders
        contain any plugins, the plugins are left undeleted as well. This command
        deletes these orphaned instances.

        For details see: https://github.com/divio/django-cms/issues/2262""")

    option_list = NoArgsCommand.option_list + (
        make_option('--noinput', action='store_true', dest='noinput', default=False,
            help='Do not prompt the user for input of any kind.'),
        )

    def handle_noargs(self, **options):
        models = [('%s.%s' % (Page.__module__, Page.__name__), 'page')]
        for related in Placeholder._meta.get_all_related_objects():
            if related.model == CMSPlugin:
                continue
            class_name = '%s.%s' % (related.model.__module__, related.model.__name__)
            var_name = related.var_name
            models.append((class_name, var_name))

        self.stdout.write(dedent("""\
            Searching for Placeholder instances with no references in related database
            models. Checking for references in the following models:"""))
        for model in models:
            self.stdout.write(' -- %s' % model[0])
        self.stdout.write('')

        kwargs = {v: None for c, v in models}
        placeholders = Placeholder.objects.filter(**kwargs).order_by('id')
        kwargs = {'placeholder__' + v: None for c, v in models}
        plugins = CMSPlugin.objects.filter(**kwargs).order_by('placeholder__id')

        if not placeholders:
            self.stdout.write('No orphaned Placeholder instances found. Nothig to do.')
            return

        self.stdout.write('The following orphaned instances were found: '
            '(%d Placeholder and %d CMSPlugin instances)' % (len(placeholders), len(plugins)))
        it = iter(plugins)
        plugin = next(it, None)
        for placeholder in placeholders:
            self._print_placeholder(placeholder)
            while plugin and plugin.placeholder == placeholder:
                self._print_plugin(plugin)
                plugin = next(it, None)
        if plugin:
            self._print_placeholder(None)
            while plugin:
                self._print_plugin(plugin)
                plugin = next(it, None)
        self.stdout.write('')

        if options.get('noinput'):
            confirm = 'yes'
        else:
            confirm = raw_input(dedent("""\
                Do you really want to delete these Placeholder and CMSPlugin instances?
                They should be orphaned and unused, so it should be safe to delete them.
                However, it is a risky operation and modifies your database. You should
                backup it! Do you want to continue? ('yes' or 'no'): """))
            self.stdout.write('')

        if confirm != 'yes':
            self.stdout.write('Canceled.')
            return

        # Deletion order is inportant. We have to delete plugins before deleting their
        # placeholders. Otherwise we would get some strange strange error raised.
        plugins.delete()
        placeholders.delete()
        self.stdout.write('The instances were deleted.')

    def _print_placeholder(self, placeholder):
        if not placeholder:
            self.stdout.write(' -- (Missing Placeholder)')
            return
        self.stdout.write(' -- %s: id=%d slot=%s' % (
            placeholder.__class__.__name__,
            placeholder.id,
            placeholder.slot,
            ))

    def _print_plugin(self, plugin):
        instance = plugin.get_plugin_instance()[0]
        self.stdout.write('     -- %s: id=%d language=%s type=%s %s' % (
            plugin.__class__.__name__,
            plugin.id,
            plugin.language,
            plugin.plugin_type,
            unicode(repr(instance), 'utf8').replace('\n',' '),
            ))

