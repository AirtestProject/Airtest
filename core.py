#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author:  hzsunshx
# Created: 2015-07-02 19:56

import os
import platform

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
    raise RuntimeError("moa require adb in PATH, \n\tdownloads from: http://adbshell.com/downloads")


def adbrun(cmds, adbpath=None, host='127.0.0.1', port=5037, serialno=None):
    if isinstance(cmds, basestring):
        cmds = list(shlex(cmds))
    else:
        cmds = list(cmds)

    if not adbpath:
        adbpath = ADBPATH

    prefix = [adbpath, '-H', host, '-P', str(port)]
    if serialno:
        prefix += ['-s', serialno]
    cmds = prefix + cmds
    return subprocess.check_output(cmds)

def safe_adbrun(*args, **kwargs):
    try:
        return True, adbrun(*args, **kwargs)
    except Exception as e:
        return False, e


def get_devices():
    ''' Get all device list '''
    patten = re.compile(r'^[\w\d]+\t[\w]+$')
    for line in adbrun('devices').splitlines():
        line = line.strip()
        if not line or not patten.match(line):
            continue
        serialno, state = line.split('\t')
        yield (serialno, state)

