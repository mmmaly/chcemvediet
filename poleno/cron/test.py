# vim: expandtab
# -*- coding: utf-8 -*-
import mock
import contextlib

from django.conf import settings

@contextlib.contextmanager
def mock_cron_jobs():
    u"""
    Mocks all registered cron jobs, so running cron server would call only mock objects instead of
    real jobs. Usefull for testing if particulars job are run by the cron server without worrying
    about their side effects.

    Example:
        with mock_cron_jobs() as mocks:
            call_command('runcrons')
        assert mocks['package.cron.job'].call_count == 1
    """
    patchers = {}
    mocks = {}
    for job in settings.CRON_CLASSES:
        patchers[job] = mock.patch(u'%s.do' % job)
        mocks[job] = patchers[job].start()
    try:
        yield mocks
    finally:
        for patcher in patchers.values():
            patcher.stop()
