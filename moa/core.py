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
import shlex
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
        cmds = shlex.split(cmds)
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

    def forward(self, local, remote, rebind=True):
        cmds = ['forward']
        if not rebind:
            cmds += ['--no-rebind']
        self.run(cmds + [local, remote])

    def get_forwards(self):
        out = self.run(['forward', '--list'])
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            ss = line.split()
            if len(ss) != 3:
                continue
            sn, local, remote = ss
            yield sn, local, remote

    def getprop(self, key, strip=True):
        prop = self.shell(['getprop', key])
        if strip:
            prop = prop.rstrip('\r\n')
        return prop

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


if __name__ == '__main__':
    adb = ADB('cff039ebb31fa11', addr=('10.240.186.236', 5037)) #'cff*')
    print list(adb.get_forwards())
    #print adb.get_top_activity_name()
    #print 'keyboard shown:', adb.is_keyboard_shown()
    #print 'screen on:', adb.is_screenon()
    #if not adb.is_screenon():
    #    adb.wake()
    #    adb.unlock()
