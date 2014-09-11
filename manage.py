#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chcemvediet.settings")

    # Timewarp is automaticaly disabled if settings.DEBUG is not True.
    from poleno.timewarp import timewarp
    timewarp.init()

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
