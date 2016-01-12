#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author:  hzsunshx
# Created: 2015-07-02 19:56
# Modified: 2015-11 gzliuxin  add minitouch minicap


import os
import re
import time
import json
import warnings
import subprocess
import shlex
import socket
import struct
import threading
import platform
import Queue
from error import MoaError
from utils import SafeSocket, NonBlockingStreamReader, reg_cleanup, _islist, get_adb_path
from ..aircv import aircv


THISPATH = os.path.dirname(os.path.realpath(__file__))
ADBPATH = get_adb_path()
STFLIB = os.path.join(THISPATH, "libs")
LOCALADBADRR = ('127.0.0.1', 5037)
PROJECTIONRATE = 1
MINICAPTIMEOUT = None
ORIENTATION_MAP = {0:0,1:90,2:180,3:270}
DEBUG = True


def init_adb():
    global ADBPATH
    if ADBPATH:
        return
    ADBPATH = get_adb_path()
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
        return subprocess.check_output([adbpath, "start-server"])

    host, port = addr
    prefix = [adbpath, '-H', host, '-P', str(port)]
    if serialno:
        prefix += ['-s', serialno]
    cmds = prefix + cmds
    if DEBUG:
        print ' '.join(cmds)
    if not_wait:
        return subprocess.Popen(cmds,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    return subprocess.check_output(cmds)

def adb_devices(state=None, addr=LOCALADBADRR):
    ''' Get all device list '''
    patten = re.compile(r'^[\w\d.:-]+\t[\w]+$')
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
        self._setup()

    def _setup(self):
        # if remote devices, connect first
        if ":" in self.serialno:
            print adbrun("connect %s"%self.serialno)
            time.sleep(1.0)

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

    def install(self, filepath):
        if not os.path.isfile(filepath):
            raise RuntimeError("%s is not valid file" % filepath)
        return self.run(['install', filepath])

    def uninstall(self, package):
        return self.run(['uninstall', package])

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
    def __init__(self, serialno, projection=PROJECTIONRATE, localport=11313):
        self.serialno = serialno
        self.localport = localport
        self.adb = ADB(serialno)
        self.install()
        self.server_proc = None
        self.get_display_info()
        self.projection = projection
        self.speedygen = None
        # self._setup() #单帧截图minicap不需要setup

    def install(self, reinstall=False):
        output = self.adb.shell("ls /data/local/tmp")
        if not reinstall and "minicap\r" in output and "minicap.so\r" in output:
            print "install_minicap skipped"
            return

        self.adb.shell("rm /data/local/tmp/minicap*")
        abi = self.adb.getprop("ro.product.cpu.abi")
        sdk = int(self.adb.getprop("ro.build.version.sdk"))
        rel = self.adb.getprop("ro.build.version.release")
        # print abi, sdk, rel
        if sdk >= 16:
            binfile = "minicap"
        else:
            binfile = "minicap-nopie"

        device_dir = "/data/local/tmp"
        path = os.path.join(STFLIB, abi,binfile).replace("\\", r"\\")
        self.adb.run("push %s %s/minicap" % (path, device_dir)) 
        self.adb.shell("chmod 755 %s/minicap" % (device_dir))

        path = os.path.join(STFLIB, 'minicap-shared/aosp/libs/android-%d/%s/minicap.so' 
            % (sdk, abi)).replace("\\", r"\\")
        self.adb.run("push %s %s" % (path, device_dir))    
        self.adb.shell("chmod 755 %s/minicap.so" % (device_dir))
        print "install_minicap finished"

    def _setup(self, adb_port=None):
        # 可能需要改变参数重新setup，所以之前setup过的先关掉
        if self.server_proc:
            self.server_proc.kill()
            self.server_proc = None
        real_width = self.size["width"]
        real_height = self.size["height"]
        real_orientation = self.size["rotation"]
        if _islist(self.projection):
            proj_width, proj_height = self.projection
        elif isinstance(self.projection, float):
            proj_width = self.projection * real_width
            proj_height = self.projection * real_height
        else:
            proj_width, proj_height = real_width, real_height

        adb_port = adb_port or self.localport
        minicap_port = "moa_minicap_%s" % adb_port
        self.adb.forward("tcp:%s"%adb_port, "localabstract:%s"%minicap_port)
        p = self.adb.shell("LD_LIBRARY_PATH=/data/local/tmp/ /data/local/tmp/minicap -n '%s' -P %dx%d@%dx%d/%d" % (
            minicap_port,
            real_width, real_height,
            proj_width,proj_height,
            real_orientation), not_wait=True)
        nbsp = NonBlockingStreamReader(p.stdout)
        info = nbsp.read(0.5)
        print info
        nbsp.kill()

        if p.poll() is not None:
            # minicap server setup error, may be already setup by others
            # subprocess exit immediately
            print "minicap setup error"
            return None
        reg_cleanup(p.kill)
        self.server_proc = p

    def get_header(self):
        pass

    def get_display_info(self):
        display_info = self.adb.shell("LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -i")
        display_info = json.loads(display_info)
        if display_info['width'] > display_info['height'] and display_info['rotation'] in [90,270]:
            display_info['width'],display_info['height'] = display_info['height'],display_info['width']
        self.size = display_info
        return display_info

    def get_frame(self):
        """
        1. shell cmd
        2. remove log info
        3. \r\r\n -> \n ... fuck adb
        """
        real_width = self.size["width"]
        real_height = self.size["height"]
        real_orientation = self.size["rotation"]

        raw_data = self.adb.shell("LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -n 'moa_minicap' -P %dx%d@%dx%d/%d -s" % (
            real_width, real_height,
            real_width*PROJECTIONRATE, real_height*PROJECTIONRATE, real_orientation))
        os = platform.system()
        if os == "Windows":
            link_breaker = "\r\r\n"
        else:
            link_breaker = "\r\n"
        jpg_data = raw_data.split("for JPG encoder"+link_breaker)[-1].replace(link_breaker, "\n")
        return jpg_data

    def get_frame_speedy(self):
        if not self.speedygen:
            self.speedygen = self.get_frames(adb_port=self.localport+1)
            print self.speedygen.next()
        return self.speedygen.next()

    def get_frames(self, max_cnt=100000, adb_port=None):
        """use adb forward and socket communicate"""
        self._setup(adb_port)
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s = SafeSocket()
        adb_port = adb_port or self.localport
        s.connect(("localhost", adb_port))
        t = s.recv(24)
        # minicap info
        yield struct.unpack("<2B5I2B", t)

        cnt = 0
        while cnt <= max_cnt:
            cnt += 1
            # recv header, count frame_size
            if MINICAPTIMEOUT is not None:
                header = s.recv_with_timeout(4, MINICAPTIMEOUT)
            else:
                header = s.recv(4)
            if header is None:
                # recv timeout, if not frame updated, maybe screen locked
                yield None
            else:
                frame_size = struct.unpack("<I", header)[0]
                # recv image data
                one_frame = s.recv(frame_size)
                yield one_frame
        s.close()


class Minitouch(object):
    """quick operation from minitouch  https://github.com/openstf/minitouch"""
    def __init__(self, serialno, localport=11111, size=None):
        self.serialno = serialno
        self.localport = localport
        self.adb = ADB(serialno)
        self.install()
        self.server_proc = None
        self._setup()
        self.op_server_proc = None
        self.op_queue = None
        self.op_sock = None
        self.op_thread = None
        self.op_adbport = 11112
        self._stop_long_op = None
        self.size = size

    def install(self, reinstall=False):
        output = self.adb.shell("ls /data/local/tmp")
        if not reinstall and "minitouch\r" in output:
            print "install_minitouch skipped"
            return

        abi = self.adb.getprop("ro.product.cpu.abi")
        sdk = int(self.adb.getprop("ro.build.version.sdk"))

        if sdk >= 16:
            binfile = "minitouch"
        else:
            binfile = "minitouch-nopie"

        device_dir = "/data/local/tmp"
        path = os.path.join(STFLIB, abi, binfile).replace("\\", r"\\")
        self.adb.run(r"push %s %s/minitouch" % (path, device_dir)) 
        self.adb.shell("chmod 755 %s/minitouch" % (device_dir))
        print "install_minitouch finished"

    def __transform_xy(self, x, y):
        # 根据设备方向、长宽来转换xy值
        if not (self.size and self.size['max_x'] and self.size['max_y']):
            return x, y

        width ,height = self.size['width'], self.size['height']
        if width > height and self.size['orientation'] in [1,3]:
            width, height = height, width
        max_x , max_y = self.size['max_x'], self.size['max_y']
        # print width, height, max_x, max_y
        nx = x * max_x / width
        ny = y * max_y / height
        return nx, ny

    def _setup(self, adb_port=None, device_port='moa_minitouch'):
        if self.server_proc:
            self.server_proc.kill()
            self.server_proc = None
        adb_port = adb_port or self.localport
        self.adb.forward("tcp:%s"%adb_port, "localabstract:%s" % device_port)
        p = self.adb.shell("/data/local/tmp/minitouch -n '%s'" % device_port, not_wait=True)
        nbsp = NonBlockingStreamReader(p.stdout)
        info = nbsp.read(1.0)
        # print "minitouch _setup", info
        nbsp.kill() # kill掉stdout的reader，目前后面不会再读了
        if p.poll() is not None:
            # server setup error, may be already setup by others
            # subprocess exit immediately
            print "minitouch setup error"
            return None
        reg_cleanup(p.kill)
        self.server_proc = p
        return p

    def touch(self, (x, y), duration=0.01):
        """
        d 0 10 10 50
        c
        <wait in your own code>
        u 0
        c
        """
        x, y = self.__transform_xy(x, y)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", self.localport))
        # header = s.recv(4096)
        s.send("d 0 %d %d 50\nc\n" % (x, y))
        time.sleep(duration)
        s.send("u 0\nc\n")
        time.sleep(0.05) # wait send
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
        from_x, from_y = self.__transform_xy(from_x, from_y)
        to_x, to_y = self.__transform_xy(to_x, to_y)

        interval = float(duration)/(steps+1)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", self.localport))
        # header = s.recv(4096)
        s.send("d 0 %d %d 50\nc\n" % (from_x, from_y))
        time.sleep(interval)
        for i in range(1, steps):
            s.send("m 0 %d %d 50\nc\n" % (
                from_x+(to_x-from_x)*i/steps, 
                from_y+(to_y-from_y)*i/steps)
            )
            time.sleep(interval)
        s.send("m 0 %d %d 50\nc\n" % (to_x, to_y))
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

    def setup_long_operate(self, adb_port=None, device_port="moa_minitouch_l"):
        if adb_port:
            self.op_adbport = adb_port
        self.op_server_proc = self._setup(adb_port=self.op_adbport, device_port=device_port)
        self.op_queue = Queue.Queue()
        self._stop_long_op = threading.Event()
        t = threading.Thread(target=self._operate_worker)
        t.daemon = True
        t.start()
        self.op_thread = t

    def _operate_worker(self):
        self.op_sock = SafeSocket()
        self.op_sock.connect(("localhost", self.op_adbport))
        print "recv", repr(self.op_sock.sock.recv(4096))
        while not self._stop_long_op.isSet():
            cmd = self.op_queue.get()
            self.op_sock.send(cmd)
        self.op_sock.close()

    def operate(self, args):
        cmd = ""
        if args["type"] == "down":
            x, y = self.__transform_xy(args["x"], args["y"])
            cmd = "d 0 %d %d 50\nc\n" % (x, y)
        elif args["type"] == "move":
            x, y = self.__transform_xy(args["x"], args["y"])
            cmd = "m 0 %d %d 50\nc\n" % (x, y)
        elif args["type"] == "up":
            cmd = "u 0\nc\n"
        else:
            return#no process

        self.op_queue.put(cmd)

    def teardown_long_operate(self):
        self._stop_long_op.set()
        self._stop_long_op = None
        self.op_server_proc.kill()
        self.op_thread = None
        self.op_queue = None
        self.op_sock = None


class Android(object):
    """Android Client"""
    def __init__(self, serialno=None, addr=LOCALADBADRR, minicap=True, minitouch=True):
        self.serialno = serialno or adb_devices(state="device").next()[0]
        self.adb = ADB(self.serialno, addr=addr)
        self.size = self.getPhysicalDisplayInfo()
        self.size["orientation"] = self.getDisplayOrientation()
        self.size["max_x"], self.size["max_y"] = self.getEventInfo()
        self.minicap = Minicap(serialno) if minicap else None
        self.minitouch = Minitouch(serialno, size=self.size) if minitouch else None
        self.props = {}
        self.props['ro.build.version.sdk'] = int(self.getprop('ro.build.version.sdk'))
        self.props['ro.build.version.release'] = self.getprop('ro.build.version.release')

        #注意，minicap在sdk<=16时只能截竖屏的图(无论是否横竖屏)，>=17后才可以截横屏的图
        self.sdk_version = self.props['ro.build.version.sdk']

    def check_status(self):
        dev_list = list(adb_devices())
        for dev, status in dev_list:
            if dev == self.serialno:
                return status
        return None

    def amstart(self, package):
        output = self.adb.shell(['pm', 'path', package])
        if not output.startswith('package:'):
            raise MoaError('amstart package not found')
        self.adb.shell(['monkey', '-p', package, '-c', 'android.intent.category.LAUNCHER', '1'])

    def amstop(self, package):
        self.adb.shell(['am', 'force-stop', package])

    def amclear(self, package):
        self.adb.shell(['pm', 'clear', package])

    def install(self, filepath):
        return self.adb.install(filepath)

    def uninstall(self, package):
        return self.adb.uninstall(package)

    def snapshot(self, filename="tmp.png", ensure_orientation=True):
        if self.minicap:
            if self.minicap.speedygen:
                screen = self.minicap.get_frame_speedy()
            else:
                screen = self.minicap.get_frame()
        else:
            screen = self.adb.snapshot()
        # 输出cv2对象
        screen = aircv.string_2_img(screen)
        # 保证方向是正的
        if ensure_orientation and self.sdk_version <=16 and self.size["orientation"]:
            h, w = screen.shape[:2] #cv2的shape是高度在前面!!!!
            if w < h: #当前是横屏，但是图片是竖的，则旋转，针对sdk<=16的机器
                screen = aircv.rotate(screen, self.size["orientation"]*90, clockwise=False)
        if filename:  # 这里图像格式不对，要写+读才对，to be fixed
            # open(filename, "wb").write(screen)
            aircv.imwrite(filename, screen)
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
        pos = self._transformPointByOrientation(pos)
        if self.minitouch:
            self.minitouch.touch(pos)
        else:
            self.adb.touch(pos)

    def swipe(self, p1, p2):
        p1 = self._transformPointByOrientation(p1)
        p2 = self._transformPointByOrientation(p2)
        if self.minitouch:
            self.minitouch.swipe(p1, p2)
        else:
            self.adb.swipe(p1, p2)

    def operate(self, tar):
        x, y = tar.get("x"), tar.get("y")
        if (x, y) != (None, None):
            x, y = self._transformPointByOrientation((x, y))
            tar.update({"x": x, "y": y})
        self.minitouch.operate(tar)


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

    def getEventInfo(self):
        ret = self.adb.shell('getevent -p').split('\n')
        max_x, max_y = None, None
        for i in ret:
            if i.find("0035") != -1:
                patten = re.compile(r'max [0-9]+')
                ret = patten.search(i)
                if ret:
                    max_x = int(ret.group(0).split()[1])

            if i.find("0036") != -1:
                patten = re.compile(r'max [0-9]+')
                ret = patten.search(i)
                if ret:
                    max_y = int(ret.group(0).split()[1])
        return max_x, max_y

    def getCurrentScreenResolution(self):
        w, h = self.size["width"], self.size["height"]
        if self.size["orientation"] in [1, 3]:
            w, h = h, w
        return w, h

    def getPhysicalDisplayInfo(self):
        # 不同sdk版本规则不一样，这里保证height>width
        info = self._getPhysicalDisplayInfo()
        if info["width"] > info["height"]:
            info["height"], info["width"] = info["width"], info["height"]
        return info

    def _getPhysicalDisplayInfo(self):
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

    def getDisplayOrientation(self):
        # Fallback method to obtain the orientation
        # See https://github.com/dtmilano/AndroidViewClient/issues/128
        surfaceOrientationRE = re.compile('SurfaceOrientation:\s+(\d+)')
        output = self.adb.shell('dumpsys input')
        m = surfaceOrientationRE.search(output)
        if m:
            return int(m.group(1))
        # We couldn't obtain the orientation
        # return -1
        return 0 if self.size["height"] > self.size['width'] else 1

    def _transformPointByOrientation(self, (x, y)):
        x, y = XYTransformer.up_2_ori(
            (x, y),
            (self.size["width"], self.size["height"]),
            self.size["orientation"]
        )
        return x, y

    def refreshOrientationInfo(self, ori=None):
        """
        update dev orientation
        if ori is assigned, set to it(useful when running a orientation monitor outside)
        """
        if ori is None:
            ori = self.getDisplayOrientation()
        self.size["orientation"] = ori
        if self.minicap:
            self.minicap.get_display_info()


class XYTransformer(object):
    """
    transform xy by orientation
    upright<-->original
    """
    @staticmethod
    def up_2_ori((x, y), (w, h), orientation):
        if orientation == 1:
            x, y = w - y, x
        elif orientation == 2:
            x, y = w - x, h - y
        elif orientation == 3:
            x, y = y, h - x
        return x, y

    @staticmethod
    def ori_2_up((x, y), (w, h), orientation):
        if orientation == 1:
            x, y = y, w - x
        elif orientation == 2:
            x, y = w - x, h - y
        elif orientation == 3:
            x, y = h - y, x
        return x, y


def test_minicap(serialno):
    mi = Minicap(serialno, {"width": 854, "height": 480, "orientation": 0})
    gen = mi.get_frames()
    print '-' * 72
    print gen.next()
    # print repr(gen.next())
    frame = mi.get_frame()
    with open("test.jpg", "wb") as f:
        f.write(gen.next())

    
def test_minitouch(serialno):
    mi = Minitouch(serialno)
    t =time.time()
    # mi.touch((100, 100))
    # mi.swipe((575, 1089), (575, 451))
    # time.sleep(1)
    # mi.swipe((1080, 200), (0, 200))
    # print time.time() - t
    mi.setup_long_operate()
    delay = 0.1
    mi.operate({"type":"down", "x":44, "y":139})
    time.sleep(delay)
    mi.operate({"type": "up"})
    time.sleep(3)
    return
    mi.operate({"type":"down", "x":100, "y":999})
    time.sleep(delay)
    mi.operate({"type": "up"})
    time.sleep(3)
    mi.operate({"type":"down", "x":100, "y":1000})
    time.sleep(delay)
    mi.operate({"type": "up"})
    time.sleep(1)
    mi.teardown_long_operate()

    # mi.touch((100, 100))
    # print mi.transform_xy(100,100)


def test_android():
    serialno = adb_devices(state="device").next()[0]
    a = Android(serialno)
    print len(a.minicap.get_frame_speedy())
    print len(a.minicap.get_frame_speedy())
    print len(a.minicap.get_frame_speedy())
    print len(a.minicap.get_frame_speedy())
    # gen = a.minicap.get_frames(adb_port=11314)
    # print gen.next()
    # print len(gen.next())
    # ret = a.adb.install(r"C:\Users\game-netease\Desktop\netese.apk")
    # ret = a.adb.uninstall("com.example.netease")
    # print repr(ret)
    # print a.size
    # print a.shell("ls")
    # a.wake()
    # return
    # print a.is_screenon()
    # a.keyevent("POWER")
    # a.snapshot('test.jpg')
    # a.snapshot('test1.jpg')
        
    # print a.get_top_activity_name()
    # print a.is_keyboard_shown()
    # print a.is_locked()
    # a.unlock()
    # print a.minicap.get_display_info()
    # print a.getDisplayOrientation()
    # a.touch((100, 100))
    # print a.minitouch.transform_xy(100,100)


if __name__ == '__main__':
    serialno = adb_devices(state="device").next()[0]
    # print serialno
    # serialno = "192.168.40.111:7401"
    # adb = ADB(serialno)
    # print adb.getprop('ro.build.version.sdk')
    # test_minicap(serialno)
    # test_minitouch(serialno)
    # time.sleep(10)
    test_android()
