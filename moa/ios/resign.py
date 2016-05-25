#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
from ..error import MoaError, ICmdError
from utils import run_cmd
import plistlib
from certificate_config import CERTIFICATE

basedir = os.path.dirname(os.path.abspath(__file__))
TEAM_ID = "L894CK4886"
PROVISION = os.path.join(basedir,"resign/development_test.mobileprovision")
ENTITLEMENTS = os.path.join(basedir,"resign/entitlements.plist")


def sign(ipaname, certificate=CERTIFICATE, provision=PROVISION, entitlements=ENTITLEMENTS):
    """sign an app"""

    new_ipaname = re.search('(.+)\.ipa', ipaname).group(1) + '-resigned.ipa'
    # get appid
    cmd = 'security cms -D -i %s' %(provision)
    stdout = run_cmd(cmd)
    plistRoot = plistlib.readPlistFromString(stdout)
    appid = plistRoot['Entitlements']['application-identifier']
    appid = re.search('[0-9A-Z]{10}\.(.+)',appid).group(1)

    sign_script = os.path.join(basedir,"floatsign.sh")
    # codesign script
    cmd = '%s %s "%s" -p "%s" -e %s -b "%s" %s' %(sign_script,ipaname,certificate,provision,entitlements,appid,new_ipaname)
    run_cmd(cmd)
    return new_ipaname

def test():
    sign("./BBS.ipa")

if __name__ == '__main__':
    test()
