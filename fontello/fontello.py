# vim: expandtab
# -*- coding: utf-8 -*-
import re
import os
import sys
import io
import shutil
import filecmp
import zipfile
import requests

FONTELLO_HOST = u'https://fontello.com'
WORKING_DIR = os.path.abspath(os.path.dirname(__file__))
TEMP_DIR = os.path.join(WORKING_DIR, u'_tmp')
OUTPUT_DIR = os.path.join(WORKING_DIR, u'output')
FONTELLO_DIR = os.path.join(OUTPUT_DIR, u'static/fontello')
SOURCE_CONFIG = os.path.join(WORKING_DIR, u'config.json')
BACKUP_CONFIG = os.path.join(OUTPUT_DIR, u'backup_config.json')

if os.path.exists(BACKUP_CONFIG) and filecmp.cmp(SOURCE_CONFIG, BACKUP_CONFIG):
    print(u'Fontello: No change since last run. Skipping.')
    sys.exit(0)

print(u'Fontello: Uploading config.json...')
with open(SOURCE_CONFIG) as config:
    # TODO: Remove `verify=False` after we upgrade
    response = requests.post(FONTELLO_HOST, files=dict(config=config), verify=False)
response.raise_for_status()
session = response.text

print(u'Fontello: Downloading fonts...')
# TODO: Remove `verify=False` after we upgrade
response = requests.get(u'{}/{}/get'.format(FONTELLO_HOST, session), verify=False)
response.raise_for_status()
zipped = io.BytesIO(response.content)

print(u'Fontello: Unzipping...')
shutil.rmtree(TEMP_DIR, ignore_errors=True)
with zipfile.ZipFile(zipped) as zipper:
    result = re.match(r'^fontello-\w*/', zipper.namelist()[0]).group(0)
    zipper.extractall(TEMP_DIR)

shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
shutil.move(os.path.join(TEMP_DIR, result), FONTELLO_DIR)
shutil.copy(SOURCE_CONFIG, BACKUP_CONFIG)
shutil.rmtree(TEMP_DIR)
print(u'Fontello: Done.')
