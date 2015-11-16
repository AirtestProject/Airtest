#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: gzmaruijie
# @Date:   2015-11-16 11:01:08
# @Last Modified by:   gzmaruijie
# @Last Modified time: 2015-11-16 14:36:51

import core
import sys
import os

ROOT = os.path.dirname(os.path.abspath(sys.argv[0]))
def setup_minitouch(sno):
    adb =  core.ADB(sno)
    abi = adb.getprop("ro.product.cpu.abi")
    sdk = int(adb.getprop("ro.build.version.sdk"))

    if sdk >= 16:
        binfile = "minitouch"
    else:
        binfile = "minitouch-nopie"

    dir = "/data/local/tmp"
    path = os.path.join(ROOT, 'libs\\%s\\%s' % (abi,binfile)).replace('\\', '/')
    print path
    adb.run("push %s %s/minitouch" % (path, dir)) 
    adb.shell("chmod 777 %s/%s" % (dir, binfile))

def setup_minicap(sno):
    adb =  core.ADB(sno)
    abi = adb.getprop("ro.product.cpu.abi")
    sdk = int(adb.getprop("ro.build.version.sdk"))
    rel = adb.getprop("ro.build.version.release")

    # print abi, sdk, rel
    if sdk >= 16:
        binfile = "minicap"
    else:
        binfile = "minicap-nopie"

    dir = "/data/local/tmp"
    
    path = os.path.join(ROOT, 'libs\\%s\\%s' % (abi,binfile)).replace('\\', '/')
    adb.run("push %s %s/minicap" % (path, dir)) 
    adb.shell("chmod 777 %s/%s" % (dir, binfile))

    path = os.path.join(ROOT, 'libs/minicap-shared/aosp/libs/android-%d/%s/minicap.so' % (sdk, abi)).replace('\\','/')
    adb.run("push %s %s" % (path, dir))    
        


if __name__ == '__main__':
    serialno = core.adb_devices(state="device").next()[0]
    setup_minitouch(serialno)
    setup_minicap(serialno)