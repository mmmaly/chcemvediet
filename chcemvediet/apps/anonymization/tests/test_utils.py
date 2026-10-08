import os
import subprocess
import time
from unittest import mock

from django.test import TestCase
from django.test.utils import override_settings

from chcemvediet.apps.anonymization import finalization
from chcemvediet.apps.anonymization.utils import run_command, process_output


class RunCommandTest(TestCase):
    u"""
    Tests ``run_command()`` and ``process_output()`` helpers.
    """

    def test_successful_command_returns_output(self):
        p = run_command([u'sh', u'-c', u'echo out; echo err >&2'], timeout=10)
        self.assertEqual((p.stdout, p.stderr), (b'out\n', b'err\n'))
        self.assertEqual(process_output(p, None), (u'out\n', u'err\n'))

    def test_failed_command_raises_error_with_output(self):
        with self.assertRaises(subprocess.CalledProcessError) as cm:
            run_command([u'sh', u'-c', u'echo problem >&2; exit 3'], timeout=10)
        self.assertEqual(cm.exception.returncode, 3)
        self.assertEqual(process_output(None, cm.exception), (u'', u'problem\n'))

    def test_timeout_kills_child_processes_too(self):
        # the shell starts a background child, like the libreoffice launcher starts soffice.bin
        with self.assertRaises(subprocess.TimeoutExpired) as cm:
            run_command([u'sh', u'-c', u'sleep 60 & echo $!; wait'], timeout=1)
        child = int(cm.exception.stdout.split()[0])
        time.sleep(0.2)
        with self.assertRaises(OSError):
            os.kill(child, 0)
        self.assertEqual(process_output(None, cm.exception)[1], u'')

    def test_process_output_of_exception_without_output(self):
        self.assertEqual(process_output(None, subprocess.TimeoutExpired([u'x'], 1)), (u'', u''))
        self.assertEqual(process_output(None, ValueError(u'x')), (u'', u''))


class FinalizationTimeoutTest(TestCase):
    u"""
    A LibreOffice timeout must be recorded as a failed finalization. If it is not, the pipeline
    picks the same attachment again every minute and nothing behind it is ever finalized.
    """

    @override_settings(MOCK_LIBREOFFICE=False)
    def test_timeout_creates_failed_finalization(self):
        anonymization = mock.Mock(content_type=u'application/vnd.oasis.opendocument.text')
        anonymization.file.path = __file__
        error = subprocess.TimeoutExpired([u'libreoffice'], 300)
        with mock.patch.object(finalization, u'libreoffice_convert_to_pdf', side_effect=error):
            with mock.patch.object(finalization.AttachmentFinalization.objects, u'create') as create:
                with mock.patch.object(finalization, u'cron_logger'):
                    finalization.finalize_using_libreoffice(anonymization)
        self.assertEqual(create.call_count, 1)
        kwargs = create.call_args[1]
        self.assertFalse(kwargs[u'successful'])
        self.assertIn(u'TimeoutExpired', kwargs[u'debug'])
