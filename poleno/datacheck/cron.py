# vim: expandtab
# -*- coding: utf-8 -*-
from poleno.cron import cron_job, cron_logger

from .datacheck import run_checks

@cron_job(run_at_times=[u'04:00'])
def datacheck():
    issues = run_checks(superficial=True)
    for issue in issues:
        cron_logger.log(issue.level, u'%s', issue)
    cron_logger.info(u'Data check identified %s issues.', len(issues))
