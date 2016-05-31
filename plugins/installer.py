# coding=utf-8
__author__ = 'lxn3032'


import re
import os
import requests
import plistlib
from moa.core.main import logwrap


@logwrap
def plist_parse(plist_url):
    """analyse plist file, get ipa download link"""

    response = requests.get(plist_url,stream=True)
    if response.status_code == 200:
        plistStr = response.text
        plistRoot = plistlib.readPlistFromString(plistStr)
        ipa_url = plistRoot['items'][0]['assets'][0]['url']
        return ipa_url

@logwrap
def rm_installer(filename):
    if os.path.exists(filename):
        os.remove(filename)
        

@logwrap
def download_installer(app_url, appname):
    r = requests.get(app_url, stream=True)
    if r.status_code == 200:
        with open(appname, 'wb') as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)
        return True
    return False
