#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    # Add vendor/ to sys.path so vendored packages shadow pip-installed ones
    vendor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vendor')
    if vendor_path not in sys.path:
        sys.path.insert(0, vendor_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chcemvediet.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
