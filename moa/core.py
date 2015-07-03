#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author:  hzsunshx
# Created: 2015-07-02 19:56

import os
import re
import platform
import fnmatch
import warnings
import subprocess
from shlex import shlex
from error import MoaError

def look_path(program):
    system = platform.system()

    def is_exe(fpath):
        if system.startswith('Windows') and not fpath.lower().endswith('.exe'):
            fpath += '.exe'
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


ADBPATH = look_path('adb')
if not ADBPATH:
    raise MoaError("moa require adb in PATH, \n\tdownloads from: http://adbshell.com/downloads")


def adbrun(cmds, adbpath=None, addr=('127.0.0.1', 5037), serialno=None):
    if isinstance(cmds, basestring):
        cmds = list(shlex(cmds))
    else:
        cmds = list(cmds)

    if not adbpath:
        adbpath = ADBPATH

    host, port = addr
    prefix = [adbpath, '-H', host, '-P', str(port)]
    if serialno:
        prefix += ['-s', serialno]
    cmds = prefix + cmds
    print ' '.join(cmds)
    return subprocess.check_output(cmds)

def safe_adbrun(*args, **kwargs):
    try:
        return True, adbrun(*args, **kwargs)
    except Exception as e:
        return False, e


class ADB():
    def __init__(self, serialno, adbpath=None, addr=('127.0.0.1', 5037)):
        self.adbpath = ADBPATH if not adbpath else adbpath
        self.addr = addr
        self.serialno = serialno
        self.props = {}
        self.props['ro.build.version.sdk'] = int(self.getprop('ro.build.version.sdk'))
        self.props['ro.build.version.release'] = self.getprop('ro.build.version.release')

    def run(self, cmds):
        return adbrun(cmds, adbpath=self.adbpath, addr=self.addr, serialno=self.serialno)

    @property
    def sdk_version(self):
        return self.props['ro.build.version.sdk']

    def safe_run(self, cmds):
        try:
            return True, adbrun(*args, **kwargs)
        except Exception as e:
            return False, e

    def shell(self, cmds):
        if isinstance(cmds, basestring):
            cmds = 'shell '+ cmds
        else:
            cmds = ['shell'] + list(cmds)
        return self.run(cmds)

    def getprop(self, key, strip=True):
        prop = self.shell(['getprop', key])
        if strip:
            prop = prop.rstrip('\r\n')
        return prop

    def is_locked(self):
        lockScreenRE = re.compile('mShowingLockscreen=(true|false)')
        m = lockScreenRE.search(self.shell('dumpsys window policy'))
        if m:
            return (m.group(1) == 'true')
        raise MoaError("Couldn't determine screen lock state")

    def unlock(self):
        # REWRITE ME
        if self.serialno == 'cff039ebb31fa11':
            self.swipe((360, 915), (370, 1203))
        else:
            self.shell('input keyevent MENU')
            self.shell('input keyevent BACK')

    def is_screenon(self):
        screenOnRE = re.compile('mScreenOnFully=(true|false)')
        m = screenOnRE.search(self.shell('dumpsys window policy'))
        if m:
            return (m.group(1) == 'true')
        raise MoaError("Couldn't determine screen ON state")

    def wake(self):
        if not self.is_screenon():
            self.shell('input keyevent POWER')

    def touch(self, x, y):
        self.shell('input tap %d %d' % (x, y))

    def swipe(self, (x0, y0), (x1, y1), duration=500, steps=1):
        version = self.sdk_version
        if version <= 15:
            raise MoaError('swipe: API <= 15 not supported (version=%d)' % version)
        elif version <= 17:
            self.shell('input swipe %d %d %d %d' % (x0, y0, x1, y1))
        else:
            self.shell('input touchscreen swipe %d %d %d %d %d' % (x0, y0, x1, y1, duration))

    def get_top_activity_name_and_pid(self):
        dat = self.shell('dumpsys activity top')
        lines = dat.splitlines()
        activityRE = re.compile('\s*ACTIVITY ([A-Za-z0-9_.]+)/([A-Za-z0-9_.]+) \w+ pid=(\d+)')
        m = activityRE.search(lines[1]) 
        if m:
            return (m.group(1), m.group(2), m.group(3))
        else:
            warnings.warn("NO MATCH:" + lines[1])
            return None

    def get_top_activity_name(self):
        tanp = self.get_top_activity_name_and_pid()
        if tanp:
            return tanp[0] + '/' + tanp[1]
        else:
            return None

    def is_keyboard_shown(self):
        dim = self.shell('dumpsys input_method')
        if dim:
            return "mInputShown=true" in dim
        return False


def get_devices():
    ''' Get all device list '''
    patten = re.compile(r'^[\w\d]+\t[\w]+$')
    for line in adbrun('devices').splitlines():
        line = line.strip()
        if not line or not patten.match(line):
            continue
        serialno, state = line.split('\t')
        yield (serialno, state)


if __name__ == '__main__':
    #print get_devices()
    adb = ADB('cff039ebb31fa11', addr=('10.240.186.236', 5037)) #'cff*')
    print adb.get_top_activity_name()
    print 'keyboard shown:', adb.is_keyboard_shown()
    print 'screen on:', adb.is_screenon()
    if not adb.is_screenon():
        adb.wake()
        adb.unlock()
