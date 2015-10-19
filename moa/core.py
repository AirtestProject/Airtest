#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author:  hzsunshx
# Created: 2015-07-02 19:56

import os
import re
import time
import platform
import fnmatch
import warnings
import subprocess
import shlex
import socket
import struct
from error import MoaError

ADBPATH = None
LOCALADBADRR = ('127.0.0.1', 5037)
PROJECTIONRATE = 1.0


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

def init_adb():
    global ADBPATH
    if ADBPATH:
        return
    ADBPATH = look_path('adb')
    if not ADBPATH:
        raise MoaError("moa require adb in PATH, \n\tdownloads from: http://adbshell.com/downloads")

def adbrun(cmds, adbpath=ADBPATH, addr=LOCALADBADRR, serialno=None, not_wait=False):
    if adbpath is None:
        init_adb()
        adbpath = ADBPATH
    if isinstance(cmds, basestring):
        cmds = shlex.split(cmds)
    else:
        cmds = list(cmds)
    # start-server cannot assign -H -P -s
    if cmds == ["start-server"] and addr == LOCALADBADRR:
        return subprocess.check_output("adb start-server")

    host, port = addr
    prefix = [adbpath, '-H', host, '-P', str(port)]
    if serialno:
        prefix += ['-s', serialno]
    cmds = prefix + cmds
    print ' '.join(cmds)
    if not_wait:
        return subprocess.Popen(cmds)
    return subprocess.check_output(cmds)

def adb_devices(state=None, addr=LOCALADBADRR):
    ''' Get all device list '''
    patten = re.compile(r'^[\w\d]+\t[\w]+$')
    adbrun('start-server')
    for line in adbrun('devices', addr=addr).splitlines():
        line = line.strip()
        if not line or not patten.match(line):
            continue
        serialno, cstate = line.split('\t')
        if state and cstate != state:
            continue
        yield (serialno, cstate)


class ADB():
    def __init__(self, serialno, adbpath=None, addr=('127.0.0.1', 5037)):
        self.adbpath = ADBPATH if not adbpath else adbpath
        self.addr = addr
        self.serialno = serialno
        self.props = {}

    def run(self, cmds, not_wait=False):
        return adbrun(cmds, adbpath=self.adbpath, addr=self.addr, serialno=self.serialno, not_wait=not_wait)

    @property
    def sdk_version(self):
        keyname = 'ro.build.version.sdk'
        if keyname not in self.props:
            self.props[keyname] = int(self.getprop(keyname))
        return self.props[keyname]

    def safe_run(self, *args, **kwargs):
        try:
            return True, adbrun(*args, **kwargs)
        except Exception as e:
            return False, e

    def shell(self, cmds, not_wait=False):
        if isinstance(cmds, basestring):
            cmds = 'shell '+ cmds
        else:
            cmds = ['shell'] + list(cmds)
        return self.run(cmds, not_wait=not_wait)

    def getprop(self, key, strip=True):
        prop = self.shell(['getprop', key])
        if strip:
            prop = prop.rstrip('\r\n')
        return prop

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

    def snapshot(self):
        pass

    def touch(self, (x, y)):
        self.shell('input tap %d %d' % (x, y))
        time.sleep(0.1)

    def swipe(self, (x0, y0), (x1, y1), duration=500, steps=1):
        version = self.sdk_version
        if version <= 15:
            raise MoaError('swipe: API <= 15 not supported (version=%d)' % version)
        elif version <= 17:
            self.shell('input swipe %d %d %d %d' % (x0, y0, x1, y1))
        else:
            self.shell('input touchscreen swipe %d %d %d %d %d' % (x0, y0, x1, y1, duration))


class Minicap(object):
    """quick screenshot from minicap  https://github.com/openstf/minicap"""
    def __init__(self, serialno, size, localport=1313):
        self.serialno = serialno
        self.size = size
        self.localport = localport
        self.adb = ADB(serialno)

    def _setup(self):
        self.adb.forward("tcp:%s"%self.localport, "localabstract:minicap")
        p = self.adb.shell("LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P %dx%d@%dx%d/0" % (
            self.size["width"], self.size["height"],
            self.size["width"]*PROJECTIONRATE,
            self.size["height"]*PROJECTIONRATE), not_wait=True)
        time.sleep(1.0)
        # p.kill()

    def get_header(self):
        pass

    def get_frame(self):
        """
        1. shell cmd
        2. remove log info
        3. \r\r\n -> \n ... fuck adb
        """
        raw_data = self.adb.shell("LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P %dx%d@%dx%d/0 -s" % (
            self.size["width"], self.size["height"],
            self.size["width"]*PROJECTIONRATE, self.size["height"]*PROJECTIONRATE))
        jpg_data = raw_data.split("for JPG encoder\r\r\n")[-1].replace("\r\r\n", "\n")
        return jpg_data

    def get_frames(self, max_cnt=10):
        """use adb forward and socket communicate"""
        self._setup()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", self.localport))
        t = s.recv(24)
        # print repr(t)
        yield struct.unpack("<2B5I2B", t)

        cnt = 0
        while cnt <= max_cnt:
            cnt += 1
            # frame_size = struct.unpack("<I", s.recv(4))[0]
            trunk = ""
            while len(trunk) < 4:
                trunk += s.recv(4)
            header, trunk = trunk[:4], trunk[4:]
            frame_size = struct.unpack("<I", header)[0]

            while len(trunk) < frame_size:
                trunk_size = min(4096, frame_size - len(trunk))
                trunk += s.recv(trunk_size)
            yield trunk
        s.close()


class Minitouch(object):
    """quick operation from minitouch  https://github.com/openstf/minitouch"""
    def __init__(self, serialno, localport=1111):
        self.serialno = serialno
        self.localport = localport
        self.adb = ADB(serialno)
        self._setup()

    def _setup(self):
        self.adb.forward("tcp:%s"%self.localport, "localabstract:minitouch")
        p = self.adb.shell("/data/local/tmp/minitouch", not_wait=True)
        time.sleep(0.5)
        # p.kill()

    def touch(self, (x, y), duration=0.01):
        """
        d 0 10 10 50
        c
        <wait in your own code>
        u 0
        c
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", self.localport))
        # header = s.recv(4096)
        s.send("d 0 %d %d 50\nc\n" % (x, y))
        time.sleep(duration)
        s.send("u 0\nc\n")
        time.sleep(0.01) # wait send
        s.close()

    def swipe(self, (from_x, from_y), (to_x, to_y), duration=0.3, steps=5):
        """
        d 0 0 0 50
        c
        m 0 20 0 50
        c
        m 0 40 0 50
        c
        m 0 60 0 50
        c
        m 0 80 0 50
        c
        m 0 100 0 50
        c
        u 0
        c
        """
        interval = float(duration)/(steps+1)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", self.localport))
        # header = s.recv(4096)
        s.send("d 0 %s %s 50\nc\n" % (from_x, from_y))
        time.sleep(interval)
        for i in range(1, steps):
            s.send("m 0 %s %s 50\nc\n" % (
                from_x+(to_x-from_x)*i/steps, 
                from_y+(to_y-from_y)*i/steps)
            )
            time.sleep(interval)
        s.send("d 0 %s %s 50\nc\n" % (to_x, to_y))
        time.sleep(interval)
        s.send("u 0\nc\n")
        time.sleep(0.01)
        s.close()

    def pinch(self):
        """
        d 0 0 100 50
        d 1 100 0 50
        c
        m 0 10 90 50
        m 1 90 10 50
        c
        m 0 20 80 50
        m 1 80 20 50
        c
        m 0 20 80 50
        m 1 80 20 50
        c
        m 0 30 70 50
        m 1 70 30 50
        c
        m 0 40 60 50
        m 1 60 40 50
        c
        m 0 50 50 50
        m 1 50 50 50
        c
        u 0
        u 1
        c
        """
        pass


class Android(object):
    """Android Client"""
    def __init__(self, serialno=None, addr=LOCALADBADRR, minicap=True, minitouch=False):
        self.serialno = serialno or adb_devices(state="device").next()[0]
        self.adb = ADB(self.serialno, addr=addr)
        self.size = self.getPhysicalDisplayInfo()
        self.minicap = Minicap(serialno, self.size) if minicap else None
        self.minitouch = Minitouch(serialno) if minitouch else None
        self.props = {}
        self.props['ro.build.version.sdk'] = int(self.getprop('ro.build.version.sdk'))
        self.props['ro.build.version.release'] = self.getprop('ro.build.version.release')
        
    def amstart(self, package):
        output = self.adb.shell(['pm', 'path', package])
        if not output.startswith('package:'):
            raise MoaError('amstart package not found')
        self.adb.shell(['monkey', '-p', package, '-c', 'android.intent.category.LAUNCHER', '1'])

    def amstop(self, package):
        self.adb.shell(['am', 'force-stop', package])

    def amclear(self, package):
        self.adb.shell(['pm', 'clear', package])

    def snapshot(self, filename=None):
        if self.minicap:
            screen = self.minicap.get_frame()
        else:
            screen = self.adb.snapshot()
        if filename:
            with open(filename, "wb") as f:
                f.write(screen)
        return screen

    def shell(self, *args):
        return self.adb.shell(*args)

    def keyevent(self, keyname):
        self.adb.shell(["input", "keyevent", keyname])

    def wake(self):
        if not self.is_screenon():
            self.keyevent("POWER")

    def home(self):
        self.keyevent("HOME")

    def text(self, text):
        self.adb.shell(["input", "text", text])

    def touch(self, pos):
        pos = map(lambda x: x/PROJECTIONRATE, pos)
        print pos
        if self.minitouch:
            self.minitouch.touch(pos)
        else:
            self.adb.touch(pos)

    def swipe(self, p1, p2):
        if self.minitouch:
            self.minitouch.swipe(p1, p2)
        else:
            self.adb.swipe(p1, p2)

    def get_top_activity_name_and_pid(self):
        dat = self.adb.shell('dumpsys activity top')
        lines = dat.replace('\r', '').splitlines()
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
        dim = self.adb.shell('dumpsys input_method')
        if dim:
            return "mInputShown=true" in dim
        return False

    def is_screenon(self):
        screenOnRE = re.compile('mScreenOnFully=(true|false)')
        m = screenOnRE.search(self.adb.shell('dumpsys window policy'))
        if m:
            return (m.group(1) == 'true')
        raise MoaError("Couldn't determine screen ON state")

    def is_locked(self):
        """not work on xiaomi 2s"""
        lockScreenRE = re.compile('mShowingLockscreen=(true|false)')
        m = lockScreenRE.search(self.adb.shell('dumpsys window policy'))
        if not m:
            raise MoaError("Couldn't determine screen lock state")
        return (m.group(1) == 'true')

    def unlock(self):
        """not work on many devices"""
        self.adb.shell('input keyevent MENU')
        self.adb.shell('input keyevent BACK')

    def getprop(self, key, strip=True):
        prop = self.adb.shell(['getprop', key])
        if strip:
            prop = prop.rstrip('\r\n')
        return prop

    def getPhysicalDisplayInfo(self):
        ''' Gets C{mPhysicalDisplayInfo} values from dumpsys. This is a method to obtain display dimensions and density'''
        phyDispRE = re.compile('Physical size: (?P<width>)x(?P<height>).*Physical density: (?P<density>)', re.MULTILINE)
        m = phyDispRE.search(self.adb.shell('wm size; wm density'))
        if m:
            displayInfo = {}
            for prop in [ 'width', 'height' ]:
                displayInfo[prop] = int(m.group(prop))
            for prop in [ 'density' ]:
                displayInfo[prop] = float(m.group(prop))
            return displayInfo

        phyDispRE = re.compile('.*PhysicalDisplayInfo{(?P<width>\d+) x (?P<height>\d+), .*, density (?P<density>[\d.]+).*')
        for line in self.adb.shell('dumpsys display').splitlines():
            m = phyDispRE.search(line, 0)
            if m:
                displayInfo = {}
                for prop in [ 'width', 'height' ]:
                    displayInfo[prop] = int(m.group(prop))
                for prop in [ 'density' ]:
                    # In mPhysicalDisplayInfo density is already a factor, no need to calculate
                    displayInfo[prop] = float(m.group(prop))
                return displayInfo

        # This could also be mSystem or mOverscanScreen
        phyDispRE = re.compile('\s*mUnrestrictedScreen=\((?P<x>\d+),(?P<y>\d+)\) (?P<width>\d+)x(?P<height>\d+)')
        # This is known to work on older versions (i.e. API 10) where mrestrictedScreen is not available
        dispWHRE = re.compile('\s*DisplayWidth=(?P<width>\d+) *DisplayHeight=(?P<height>\d+)')
        for line in self.adb.shell('dumpsys window').splitlines():
            m = phyDispRE.search(line, 0)
            if not m:
                m = dispWHRE.search(line, 0)
            if m:
                displayInfo = {}
                for prop in [ 'width', 'height' ]:
                    displayInfo[prop] = int(m.group(prop))
                for prop in [ 'density' ]:
    
                    d = self.__getDisplayDensity(None, strip=True)
                    if d:
                        displayInfo[prop] = d
                    else:
                        # No available density information
                        displayInfo[prop] = -1.0
                return displayInfo

    def __getDisplayDensity(self, key, strip=True):
        BASE_DPI = 160.0
        d = self.getprop('ro.sf.lcd_density', strip)
        if d:
            return float(d)/BASE_DPI
        d = self.getprop('qemu.sf.lcd_density', strip)
        if d:
            return float(d)/BASE_DPI
        return -1.0


def test_minicap(serialno):
    mi = Minicap(serialno, {"width": 1080, "height": 1920})
    frame = mi.get_frame()
    with open("test.jpg", "wb") as f:
        f.write(frame)
    gen = mi.get_frames()
    print gen.next()
    print repr(gen.next())


def test_minitouch(serialno):
    mi = Minitouch(serialno)
    t =time.time()
    mi.touch((100, 100))
    # mi.swipe((100, 200), (1280, 200))
    # time.sleep(1)
    # mi.swipe((1080, 200), (0, 200))
    print time.time() - t


def test_android():
    a = Android()
    print a.size
    print a.shell("ls")
    a.wake()
    return
    print a.is_screenon()
    a.keyevent("POWER")
    print a.snapshot()
    print a.get_top_activity_name()
    print a.is_keyboard_shown()
    # print a.is_locked()
    # a.unlock()


if __name__ == '__main__':
    serialno = adb_devices(state="device").next()[0]
    test_minicap(serialno)
    # test_minitouch(serialno)
    # test_android()
