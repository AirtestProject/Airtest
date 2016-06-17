#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author:  hzsunshx
# Created: 2015-07-02 19:56
# Modified: 2015-11 gzliuxin  add minitouch minicap
# Modified: 2016-06 gzliuxin  testlab support


import os
import sys
import re
import time
import json
import warnings
import subprocess
import socket
import shlex
import struct
import threading
import platform
import Queue
import random
import traceback
import axmlparserpy.apk as apkparser
from moa.core.error import MoaError, AdbError
from moa.core.utils import SafeSocket, NonBlockingStreamReader, reg_cleanup, _islist, get_adb_path, retries
from moa.aircv import aircv
from moa.core.android.ime_helper import UiautomatorIme


THISPATH = os.path.dirname(os.path.realpath(__file__))
ADBPATH = get_adb_path()
STFLIB = os.path.join(THISPATH, "libs")
LOCALADBADRR = ('127.0.0.1', 5037)
PROJECTIONRATE = 1
MINICAPTIMEOUT = None
ORIENTATION_MAP = {0:0,1:90,2:180,3:270}
DEBUG = True
RELEASELOCK_APK = os.path.join(THISPATH, "releaselock.apk")
RELEASELOCK_PACKAGE = "com.netease.releaselock"
ACCESSIBILITYSERVICE_APK = os.path.join(THISPATH, "accessibilityservice.apk")
ACCESSIBILITYSERVICE_PACKAGE = "com.netease.accessibility"
ROTATIONWATCHER_APK = os.path.join(THISPATH, "RotationWatcher.apk")
ROTATIONWATCHER_PACKAGE = "jp.co.cyberagent.stf.rotationwatcher"


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
        # cmds = shlex.split(cmds)  # disable auto removing \
        cmds = cmds.split()
    else:
        cmds = list(cmds)
    # start-server cannot assign -H -P -s
    if cmds == ["start-server"] and addr == LOCALADBADRR:
        subprocess.check_call([adbpath, "start-server"])
        return

    host, port = addr
    prefix = [adbpath, '-H', host, '-P', str(port)]
    if serialno:
        prefix += ['-s', serialno]
    cmds = prefix + cmds
    if DEBUG:
        print ' '.join(cmds)
        sys.stdout.flush()
    proc = subprocess.Popen(cmds,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if not_wait:
        return proc
    # return subprocess.check_output(cmds)
    stdout, stderr = proc.communicate()
    if proc.returncode:
        raise AdbError(stdout, stderr)
    return stdout


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


class ADB(object):
    """adb client for one serialno"""

    _forward_local = 11111

    def __init__(self, serialno, adbpath=None, addr=('127.0.0.1', 5037)):
        self.adbpath = ADBPATH if not adbpath else adbpath
        self.addr = addr
        self.serialno = serialno
        self.props = {}
        self.connect()

    def connect(self, force=False):
        # if remote devices, connect first
        if ":" in self.serialno and (force or self.get_status() != "device"):
            print adbrun("connect %s"%self.serialno)

    def get_status(self):
        for dev, status in adb_devices(addr=self.addr):
            if dev == self.serialno:
                return status
        return None

    def disconnect(self):
        if ":" in self.serialno:
            adbrun("disconnect %s"%self.serialno)

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
            return True, self.run(*args, **kwargs)
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

    def pull(self, remote, local):
        self.run(["pull", remote, local])

    def forward(self, local, remote, no_rebind=True):
        cmds = ['forward']
        if no_rebind:
            cmds += ['--no-rebind']
        self.run(cmds + [local, remote])
        reg_cleanup(self.remove_forward, local)

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

    @classmethod
    def _get_forward_local(cls):
        port = cls._forward_local
        cls._forward_local += random.randint(1, 100)
        return port

    def get_available_forward_local(self):
        """
        1. do not repeat in different process, by check forward list(latency when setting up)
        2. do not repeat in one process, by cls._forward_local
        """
        forwards = self.get_forwards()
        localports = [i[1] for i in forwards]
        times = 100
        for i in range(times):
            port = self._get_forward_local()
            if "tcp:%s"%port not in localports:
                return port
        raise RuntimeError("No available adb forward local port for %s times" % (times))

    def remove_forward(self, local=None):
        if local:
            self.safe_run(["forward", "--remove", local])
        else:
            self.safe_run(["forward", "--remove-all"])

    def install(self, filepath):
        if not os.path.isfile(filepath):
            raise RuntimeError("%s is not valid file" % filepath)
        p = self.run(['install', filepath], not_wait=True)
        nbsp = NonBlockingStreamReader(p.stdout)
        p.wait()

    def uninstall(self, package):
        return self.run(['uninstall', package])

    def snapshot(self):
        raw = self.shell(['screencap', '-p'])
        if platform.system() == "Windows":
            link_breaker = "\r\r\n"
        else:
            link_breaker = "\r\n"
        return raw.replace(link_breaker, "\n")

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
    def __init__(self, serialno, size=None, projection=PROJECTIONRATE, localport=None, adb=None):
        self.serialno = serialno
        self.localport = localport
        self.server_proc = None
        self.projection = projection
        self.speedygen = None
        self.adb = adb or ADB(serialno)
        # get_display_info may segfault, so use size info from adb dumpsys
        self.size = size or self.get_display_info()
        self.install()
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

    def _get_params(self, use_ori_size=False):
        real_width = self.size["width"]
        real_height = self.size["height"]
        real_orientation = self.size["rotation"]
        if use_ori_size or not self.projection:
            proj_width, proj_height = real_width, real_height
        elif _islist(self.projection):
            proj_width, proj_height = self.projection
        elif isinstance(self.projection, float):
            proj_width = self.projection * real_width
            proj_height = self.projection * real_height
        else:
            raise RuntimeError("invalid projection type")
        return real_width, real_height, proj_width, proj_height, real_orientation

    def _setup(self, adb_port=None):
        # 可能需要改变参数重新setup，所以之前setup过的先关掉
        if self.server_proc:
            self.server_proc.kill()
            self.server_proc = None
            self.adb.remove_forward("tcp:%s" % self.localport)

        real_width, real_height, proj_width, proj_height, real_orientation = self._get_params()

        @retries(3)
        def set_up_forward():
            localport = adb_port or self.localport or self.adb.get_available_forward_local()
            device_port = "moa_minicap_%s" % localport
            self.adb.forward("tcp:%s"%localport, "localabstract:%s"%device_port)
            return localport, device_port

        self.localport, device_port = set_up_forward()
        p = self.adb.shell("LD_LIBRARY_PATH=/data/local/tmp/ /data/local/tmp/minicap -n '%s' -P %dx%d@%dx%d/%d" % (
            device_port,
            real_width, real_height,
            proj_width,proj_height,
            real_orientation), not_wait=True)
        nbsp = NonBlockingStreamReader(p.stdout)
        info = nbsp.read(0.5)
        # print info
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

    def get_frame(self, use_ori_size=True):
        """
        1. shell cmd
        2. remove log info
        3. \r\r\n -> \n ... fuck adb
        """
        # self.get_display_info() # 设备的朝向发生更改时，由脚本层进行负责更新朝向并进行更新。
        real_width, real_height, proj_width, proj_height, real_orientation = self._get_params(use_ori_size)

        raw_data = self.adb.shell("LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -n 'moa_minicap' -P %dx%d@%dx%d/%d -s" % (
            real_width, real_height, proj_width, proj_height, real_orientation))
        os = platform.system()
        if os == "Windows":
            link_breaker = "\r\r\n"
        else:
            link_breaker = "\r\n"
        jpg_data = raw_data.split("for JPG encoder"+link_breaker)[-1].replace(link_breaker, "\n")
        return jpg_data

    def get_frame_speedy(self):
        """unfinished: get frame from server, return None immediately if blocked"""
        if not self.speedygen:
            self.speedygen = self.get_frames(adb_port=self.localport+1)
            print self.speedygen.next()
        return self.speedygen.next()

    def get_frames(self, max_cnt=100000, adb_port=None):
        """use adb forward and socket communicate"""
        self._setup(adb_port)
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
                print "header is None"
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
    def __init__(self, serialno, addr, localport=None, size=None, backend=False, adb=None):
        self.serialno = serialno
        self.server_proc = None
        self.client = None
        self.max_x, self.max_y = None, None
        self.size = size
        self.adb = adb or ADB(serialno, addr=addr)
        self.localport = localport
        self.install()
        self.setup_server()
        self.backend=backend
        if backend:
            self.setup_client_backend()
        else:
            self.setup_client()

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

        nx = x * self.max_x / width
        ny = y * self.max_y / height
        return nx, ny

    def setup_server(self, adb_port=None):
        """set up minitouch server and adb forward"""
        if self.server_proc:
            self.server_proc.kill()
            self.server_proc = None

        @retries(3)
        def set_up_forward():
            localport = adb_port or self.localport or self.adb.get_available_forward_local()
            deviceport = "minitouch_%s" % localport
            self.adb.forward("tcp:%s" % localport, "localabstract:%s" % deviceport)
            return localport, deviceport

        self.localport, deviceport  = set_up_forward()
        p = self.adb.shell("/data/local/tmp/minitouch -n '%s'" % deviceport, not_wait=True)
        self.nbsp = NonBlockingStreamReader(p.stdout)
        while True:
            line = self.nbsp.readline(timeout=5.0)
            if line is None:
                raise RuntimeError("minitouch setup error")
            # 识别出setup成功的log，并匹配出max_x, max_y
            m = re.match("Type \w touch device .+ \((\d+)x(\d+) with \d+ contacts\) detected on .+ \(.+\)", line)
            if m:
                self.max_x, self.max_y = int(m.group(1)), int(m.group(2))
                break

        # self.nbsp.kill() # 保留，不杀了，后面还会继续读取并pirnt
        if p.poll() is not None:
            # server setup error, may be already setup by others
            # subprocess exit immediately
            raise RuntimeError("minitouch setup error")
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
        self.handle("d 0 %d %d 50\nc\n" % (x, y))
        time.sleep(duration)
        self.handle("u 0\nc\n")

    def swipe(self, (from_x, from_y), (to_x, to_y), duration=0.8, steps=5):
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
        self.handle("d 0 %d %d 50\nc\n" % (from_x, from_y))
        time.sleep(interval)
        for i in range(1, steps):
            self.handle("m 0 %d %d 50\nc\n" % (
                from_x+(to_x-from_x)*i/steps, 
                from_y+(to_y-from_y)*i/steps)
            )
            time.sleep(interval)
        self.handle("m 0 %d %d 50\nc\n" % (to_x, to_y))
        time.sleep(interval)
        self.handle("u 0\nc\n")

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
            raise RuntimeError("invalid operate args: %s"%args)
        self.handle(cmd)

    def _backend_worker(self):
        while not self.backend_stop_event.isSet():
            cmd = self.backend_queue.get()
            self.client.send(cmd)

    def setup_client_backend(self):
        self.backend_queue = Queue.Queue()
        self.backend_stop_event = threading.Event()
        self.setup_client()
        t = threading.Thread(target=self._backend_worker)
        t.daemon = True
        t.start()
        self.backend_thread = t
        self.handle = self.backend_queue.put

    def setup_client(self):
        """
        1. connect to server
        2. recv header
            v <version>
            ^ <max-contacts> <max-x> <max-y> <max-pressure>
            $ <pid>
        3. prepare to send
        """
        s = SafeSocket()
        s.connect(("localhost", self.localport))
        s.sock.settimeout(2)
        header = ""
        while True:
            try:
                header += s.sock.recv(4096) # size is not strict, so use raw socket.recv
            except socket.timeout:
                raise RuntimeError("minitouch setup client error")
            if header.count('\n') >= 3:
                break
        print "minitouch header:", repr(header)
        self.client = s
        self.handle = self.client.send

    def teardown(self):
        if hasattr(self, "backend_stop_event"):
            self.backend_stop_event.set()
        self.client.close()
        # 添加判断，防止报错NoneType
        if self.server_proc:
            self.server_proc.kill()


def autoretry(func):
    def f(self, *args, **kwargs):
        def fail_hook(tries_remaining, e, mydelay):
            # print "autoretry", tries_remaining, repr(e), mydelay
            try:
                self.reconnect()
            except:
                traceback.print_exc()

        @retries(1, hook=fail_hook)
        def f_with_retries(self, *args, **kwargs):
            # print self, args, kwargs
            return func(self, *args, **kwargs)

        ret = f_with_retries(self, *args, **kwargs)
        return ret
    return f


class Android(object):

    """Android Client"""
    _props_tmp = "/data/local/tmp/moa_props.tmp"

    def __init__(self, serialno=None, addr=LOCALADBADRR, init_display=True, props={}, minicap=True, minitouch=True, init_ime=True):
        self.serialno = serialno or adb_devices(state="device").next()[0]
        self.adb = ADB(self.serialno, addr=addr)
        self._check_status()
        if init_display:
            self._init_display(props)
        self.minicap = Minicap(serialno, size=self.size, adb=self.adb) if minicap else None
        self.minitouch = Minitouch(serialno, size=self.size, adb=self.adb) if minitouch else None
        if init_ime:
            self.ime = UiautomatorIme(self.adb)

    def _init_display(self, props={}):
        # read props from outside or cached source, to save init time
        self.props = props or self._load_props()
        if "display_info" in self.props:
            self.size = self.props["display_info"]
            # self.refreshOrientationInfo()
        else:
            self.get_display_info()
        self.orientationWatcher()
        #注意，minicap在sdk<=16时只能截竖屏的图(无论是否横竖屏)，>=17后才可以截横屏的图
        self.sdk_version = self.props.get("sdk_version") or self.adb.sdk_version
        self._dump_props()

    def _load_props(self):
        try:
            props = self.adb.shell("cat %s" % self._props_tmp)
            print "load props:\n", props
            props = json.loads(props)
        except ValueError as err:
            # traceback.print_exc()
            print "load props failed:", err.message
            props = {}
        return props

    def _dump_props(self):
        data = {
            "display_info": self.size,
            "sdk_version": self.sdk_version,
        }
        data = json.dumps(data).replace(r'"', r'\"')
        print data
        self.adb.shell(r"echo %s > %s" % (data, self._props_tmp))

    @retries(5, delay=0.5)
    def _check_status(self):
        status = self.adb.get_status()
        if status != "device":
            raise MoaError("device status error:%s %s"%(self.serialno, status))

    def amlist(self, third_only=False):
        """
        pm list packages: prints all packages, optionally only
          those whose package name contains the text in FILTER.  Options:
            -f: see their associated file.
            -d: filter to only show disbled packages.
            -e: filter to only show enabled packages.
            -s: filter to only show system packages.
            -3: filter to only show third party packages.
            -i: see the installer for the packages.
            -u: also include uninstalled packages.
        """
        cmd = ["pm", "list", "packages"]
        if third_only:
            cmd.append("-3")
        output = self.adb.shell(cmd)
        packages = output.splitlines()
        # remove all ""; "package:xxx" -> "xxx"
        packages = [p.split(":")[1] for p in packages if p]
        return packages

    def amcheck(self, package):
        output = self.adb.shell(['pm', 'path', package])
        if 'package:' not in output:
            raise MoaError('package not found, output:[%s]'%output)
        return output.split(":")[1].strip()

    def amstart(self, package, activity=None):
        self.amcheck(package)
        if not activity:
            self.adb.shell(['monkey', '-p', package, '-c', 'android.intent.category.LAUNCHER', '1'])
        else:
            self.adb.shell(['am', 'start', '-n', '%s/%s.%s'%(package, package, activity)])

    def amstop(self, package):
        self.amcheck(package)
        self.adb.shell(['am', 'force-stop', package])

    def amclear(self, package):
        self.amcheck(package)
        self.adb.shell(['pm', 'clear', package])

    def amuninstall(self, package, keepdata=False):
        cmd = ['pm', 'uninstall', package]
        if keepdata:
            cmd.append('-k')
        self.adb.shell(cmd)

    def install(self, filepath, reinstall=False, check=True):
        self.wake()
        self.keyevent("HOME")

        # 预装accessibility的apk，用于自动点掉各种弹框
        packages = self.amlist()
        if ACCESSIBILITYSERVICE_PACKAGE not in packages:
            self.adb.install(ACCESSIBILITYSERVICE_APK)
        self.adb.shell('settings put secure accessibility_enabled 1')
        self.adb.shell('settings put secure enabled_accessibility_services com.netease.accessibility/com.netease.accessibility.MyAccessibilityService:com.netease.testease/com.netease.testease.service.MyAccessibilityService')

        # 如果reinstall=True，先卸载掉之前的apk，防止签名不一致导致的无法覆盖
        apk = apkparser.APK(filepath)
        apk_package = apk.get_package()
        if reinstall:
            if apk_package in packages:
                self.uninstall(apk_package)
        # rm all apks in /data/local/tmp to get enouph space
        self.adb.shell("rm /data/local/tmp/*.apk")
        self.adb.install(filepath)
        if check:
            self.amcheck(apk_package)

    def uninstall(self, package):
        return self.adb.uninstall(package)

    @autoretry
    def snapshot(self, filename="tmp.png", ensure_orientation=True):
        if self.minicap:
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
        keyname = keyname.upper()
        self.adb.shell(["input", "keyevent", keyname])

    def wake(self):
        #check and install accessibility service and release lock app
        packages = self.amlist()

        if RELEASELOCK_PACKAGE not in packages:
            self.adb.install(RELEASELOCK_APK)
        #start release lock app
        self.amstop(RELEASELOCK_PACKAGE)
        self.amstart(RELEASELOCK_PACKAGE)

        # todo:
        # 1. 还需要按power键吗？
        # 2. 如果非锁屏状态，上面步骤可以省略
        if not self.is_screenon():
            self.keyevent("POWER")

        self.keyevent("HOME")

    def home(self):
        self.keyevent("HOME")

    def text(self, text):
        self.adb.shell(["input", "text", text])

    def toggle_shell_ime(self, on=True):
        """切换到shell的输入法，用于text"""
        if on:
            self.ime.start()
        else:
            self.ime.end()

    @autoretry
    def touch(self, pos, duration=0.01):
        # print "touch...........", pos
        pos = map(lambda x: x/PROJECTIONRATE, pos)
        pos = self._transformPointByOrientation(pos)
        if self.minitouch:
            self.minitouch.touch(pos, duration=duration)
        else:
            self.adb.touch(pos)

    @autoretry
    def swipe(self, p1, p2, duration=0.5):
        p1 = self._transformPointByOrientation(p1)
        p2 = self._transformPointByOrientation(p2)
        if self.minitouch:
            self.minitouch.swipe(p1, p2, duration=duration)
        else:
            duration = duration*1000 # adb的swipe操作时间是以毫秒为单位的。
            self.adb.swipe(p1, p2, duration=duration)

    @autoretry
    def operate(self, tar):
        x, y = tar.get("x"), tar.get("y")
        if (x, y) != (None, None):
            x, y = self._transformPointByOrientation((x, y))
            tar.update({"x": x, "y": y})
        self.minitouch.operate(tar)

    def start_recording(self, max_time=180, savefile="/sdcard/screen.mp4"):
        if getattr(self, "recording_proc", None):
            raise MoaError("recording_proc has already started")
        p = self.adb.shell(["screenrecord", savefile, "--time-limit", str(max_time)], not_wait=True)
        nbsp = NonBlockingStreamReader(p.stdout)
        info = nbsp.read(0.5)
        print info
        nbsp.kill()
        if p.poll() is not None:
            print "start_recording error:", p.communicate()
            return
        self.recording_proc = p
        self.recording_file = savefile

    def stop_recording(self, output="screen.mp4"):
        if not getattr(self, "recording_proc", None):
            raise MoaError("start_recording first")
        self.recording_proc.kill()
        self.recording_proc = None
        self.adb.pull(self.recording_file, output)

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
        return self.adb.getprop(key, strip)

    def get_display_info(self):
        self.size = self.getPhysicalDisplayInfo()
        self.size["orientation"] = self.getDisplayOrientation()
        self.size["rotation"] = self.size["orientation"] * 90
        self.size["max_x"], self.size["max_y"] = self.getEventInfo()
        return self.size

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
        # another way to get orientation, for old sumsung device(sdk version 15) from xiaoma
        SurfaceFlingerRE = re.compile('orientation=(\d+)')
        output = self.adb.shell('dumpsys SurfaceFlinger')
        m = SurfaceFlingerRE.search(output)
        if m:
            return int(m.group(1))

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
        print "refreshOrientationInfo:", ori
        self.size["orientation"] = ori
        self.size["rotation"] = ori * 90
        if getattr(self, "minicap", None) and self.minicap:
            # self.minicap.get_display_info()
            self.minicap.size["rotation"] = self.size["rotation"]

    def _initOrientationWatcher(self):
        try:
            apk_path = self.amcheck(ROTATIONWATCHER_PACKAGE)
        except MoaError:
            self.install(ROTATIONWATCHER_APK)
            apk_path = self.amcheck(ROTATIONWATCHER_PACKAGE)
        p = self.adb.shell('export CLASSPATH=%s;exec app_process /system/bin jp.co.cyberagent.stf.rotationwatcher.RotationWatcher' % apk_path, not_wait=True)
        if p.poll() is not None:
            raise RuntimeError("orientationWatcher setup error")
        return p

    def orientationWatcher(self):
        self.ow_proc = self._initOrientationWatcher()
        reg_cleanup(self.ow_proc.kill)

        def _refresh_orientation(self):
            while True:
                line = self.ow_proc.stdout.readline()
                if not line:
                    print "orientationWatcher has ended"
                    if getattr(self, "ow_callback", None):
                        self.ow_callback(None, *self.ow_callback_args)
                    break
                ori = int(line) / 90
                self.refreshOrientationInfo(ori)
                if getattr(self, "ow_callback", None):
                    self.ow_callback(ori, *self.ow_callback_args)

        self._t = threading.Thread(target=_refresh_orientation, args=(self, ))
        self._t.daemon = True
        self._t.start()

    def reg_ow_callback(self, ow_callback, *ow_callback_args):
        """方向变化的时候的回调函数，第一个参数一定是ori，如果断掉了，ori传None"""
        self.ow_callback = ow_callback
        self.ow_callback_args = ow_callback_args

    def reconnect(self):
        self.adb.disconnect()
        self.adb._setup()
        self.minitouch.setup_server()
        if self.minitouch.backend:
            self.minitouch.setup_client_backend()
        else:
            self.minitouch.setup_client()


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
    size = Android(serialno, minitouch=False, minicap=False).size
    mi = Minitouch(serialno, size=size, backend=False)
    # mi.touch((100,100))
    # time.sleep(1)
    # mi.swipe((100, 100), (1000, 100))
    # time.sleep(1)
    mi.operate({"type":"down", "x":100, "y":100})
    time.sleep(1)
    mi.operate({"type": "up"})
    time.sleep(1)

    mi.teardown()


def test_android():
    serialno = adb_devices(state="device").next()[0]
    # serialno = "10.250.210.118:57217"
    t = time.clock()
    a = Android(serialno, init_display=False, minicap=False, minitouch=False, init_ime=False)
    # a.uninstall(RELEASELOCK_PACKAGE)
    # a.wake()
    a.amstart("com.netease.my")
    # def heihei(ori, nimei):
    #     print ori, nimei
    # a.reg_ow_callback(heihei, ({1: 2}, ))
    # time.sleep(100)
    # print a.amlist()
    # a.amuninstall("com.netease.kittycraft")
    # a.install(r"I:\init\moaworkspace\apk\g18\g18_netease_baidu_pc_pz_dev_1.79.0.apk", reinstall=True)
    # a.uninstall("com.netease.com")
    # print time.clock() - t, "111"
    # a.start_recording(max_time=3)
    # time.sleep(5)
    # a.stop_recording()
    # screen = a.adb.snapshot()
    # with open("screen.png", "wb") as f:
    #     f.write(screen)
    # a.touch((100, 100))
    # a.amstart("com.netease.my", "AppActivity")
    # import time
    # t = time.time()
    # print a.getDisplayOrientation()
    # print time.time() - t
    # print a.minicap.get_display_info()
    # print time.time() - t
    # print len(a.minicap.get_frame_speedy())
    # gen = a.minicap.get_frames(adb_port=11314)
    # print gen.next()
    # print len(gen.next())
    # ret = a.adb.install(r"C:\Users\game-netease\Desktop\netease.apk")
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
    # serialno = adb_devices(state="device").next()[0]
    # print serialno
    # serialno = "192.168.40.111:7401"
    # adb = ADB(serialno)
    # print adb.getprop('ro.build.version.sdk')
    # test_minicap(serialno)
    # test_minitouch(serialno)
    # time.sleep(10)
    test_android()
