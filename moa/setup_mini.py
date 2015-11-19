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

def setup_minitouch(sno, reinstall=False):
    adb =  core.ADB(sno)

    output = adb.shell("ls /data/local/tmp")
    if not reinstall and "minitouch" in output:
        print "setup_minitouch skipped"
        return

    abi = adb.getprop("ro.product.cpu.abi")
    sdk = int(adb.getprop("ro.build.version.sdk"))

    if sdk >= 16:
        binfile = "minitouch"
    else:
        binfile = "minitouch-nopie"

    device_dir = "/data/local/tmp"
    path = os.path.join(ROOT, 'libs', abi,binfile).replace("\\", r"\\")
    adb.run(r"push %s %s/minitouch" % (path, device_dir)) 
    adb.shell("chmod 777 %s/%s" % (device_dir, binfile))
    print "setup_minitouch finished"

def setup_minicap(sno, reinstall=False):
    adb = core.ADB(sno)

    output = adb.shell("ls /data/local/tmp")
    if not reinstall and "minicap" in output:
        print "setup_minicap skipped"
        return

    abi = adb.getprop("ro.product.cpu.abi")
    sdk = int(adb.getprop("ro.build.version.sdk"))
    rel = adb.getprop("ro.build.version.release")

    # print abi, sdk, rel
    if sdk >= 16:
        binfile = "minicap"
    else:
        binfile = "minicap-nopie"

    device_dir = "/data/local/tmp"
    path = os.path.join(ROOT, 'libs', abi,binfile).replace("\\", r"\\")
    adb.run("push %s %s/minicap" % (path, device_dir)) 
    adb.shell("chmod 777 %s/%s" % (device_dir, binfile))

    path = os.path.join(ROOT, 'libs/minicap-shared/aosp/libs/android-%d/%s/minicap.so' 
        % (sdk, abi)).replace("\\", r"\\")
    adb.run("push %s %s" % (path, device_dir))    
    print "setup_minicap finished"
        

if __name__ == '__main__':
    serialno = core.adb_devices(state="device").next()[0]
    setup_minitouch(serialno)
    # setup_minicap(serialno)
