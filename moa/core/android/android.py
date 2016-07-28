#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author:  hzsunshx
# Created: 2015-07-02 19:56
# Modified: 2015-11 gzliuxin  add minitouch minicap
# Modified: 2016-06 gzliuxin  add testlab support


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
from moa.core.utils import SafeSocket, NonBlockingStreamReader, reg_cleanup, is_list, get_adb_path, retries, split_cmd
from moa.aircv import aircv
from moa.core.android.ime_helper import AdbKeyboardIme

from moa.core.android.emulator.emulator_config import EMULATOR_INFO
from moa.core.android.emulator.android_emulator import EmulatorHelper
import win32gui


THISPATH = os.path.dirname(os.path.realpath(__file__))
ADBPATH = get_adb_path()
STFLIB = os.path.join(THISPATH, "libs")
DEFAULT_ADB_SERVER = ('127.0.0.1', 5037)
PROJECTIONRATE = 1
MINICAPTIMEOUT = None
ORIENTATION_MAP = {0: 0, 1: 90, 2: 180, 3: 270}
DEBUG = True
RELEASELOCK_APK = os.path.join(THISPATH, "releaselock.apk")
RELEASELOCK_PACKAGE = "com.netease.releaselock"
ACCESSIBILITYSERVICE_APK = os.path.join(THISPATH, "AccessibilityService.apk")
ACCESSIBILITYSERVICE_PACKAGE = "com.netease.accessibility"
ACCESSIBILITYSERVICE_VERSION = 2.0
ROTATIONWATCHER_APK = os.path.join(THISPATH, "RotationWatcher.apk")
ROTATIONWATCHER_PACKAGE = "jp.co.cyberagent.stf.rotationwatcher"


class ADB(object):
    """adb client for one serialno"""

    _forward_local = 11111

    status_device = "device"
    status_offline = "offline"

    def __init__(self, serialno=None, adb_path=None, server_addr=None):
        self.adb_path = adb_path or ADBPATH
        self.adb_server_addr = server_addr or self.default_server()
        self.set_serialno(serialno)
        self._props_cache = {}

    @staticmethod
    def default_server():
        """get default adb server"""
        host = DEFAULT_ADB_SERVER[0]
        port = os.environ.get("ANDROID_ADB_SERVER_PORT", DEFAULT_ADB_SERVER[1])
        return (host, port)

    def set_serialno(self, serialno):
        """set serialno after init"""
        self.serialno = serialno
        self.connect()

    def start_server(self):
        """adb start-server, cannot assign any -H -P -s"""
        if self.adb_server_addr[0] not in ("localhost", "127.0.0.1"):
            raise RuntimeError("cannot start-server on other host")
        return subprocess.check_call([self.adb_path, "start-server"])

    def start_cmd(self, cmds, device=True):
        """
        start a subprocess to run adb cmd
        device: specify -s serialno if True
        """
        cmds = split_cmd(cmds)
        if cmds == ["start-server"]:
            raise RuntimeError("please use self.start_server instead")

        host, port = self.adb_server_addr
        prefix = [self.adb_path, '-H', host, '-P', str(port)]
        if device:
            if not self.serialno:
                raise RuntimeError("please set_serialno first")
            prefix += ['-s', self.serialno]
        cmds = prefix + cmds
        if DEBUG:
            print ' '.join(cmds)
            sys.stdout.flush()
        proc = subprocess.Popen(
            cmds,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return proc

    def cmd(self, cmds, device=True):
        """
        get adb cmd output
        device: specify -s serialno if True
        """
        proc = self.start_cmd(cmds, device)
        stdout, stderr = proc.communicate()
        if proc.returncode > 0:
            raise AdbError(stdout, stderr)
        return stdout

    def version(self):
        """adb version, 1.0.36 for windows, 1.0.32 for linux/mac"""
        return self.cmd("version", device=False).strip()

    def devices(self, state=None):
        """adb devices"""
        patten = re.compile(r'^[\w\d.:-]+\t[\w]+$')
        device_list = []
        self.start_server()
        output = self.cmd("devices", device=False)
        for line in output.splitlines():
            line = line.strip()
            if not line or not patten.match(line):
                continue
            serialno, cstate = line.split('\t')
            if state and cstate != state:
                continue
            device_list.append((serialno, cstate))
        return device_list

    def connect(self, force=False):
        """adb connect, if remote devices, connect first"""
        if self.serialno and ":" in self.serialno and (force or self.get_status() != "device"):
            print self.cmd("connect %s" % self.serialno)

    def disconnect(self):
        """adb disconnect"""
        if ":" in self.serialno:
            print self.cmd("disconnect %s" % self.serialno)

    def get_status(self):
        """get device's adb status"""
        # old way...
        # for dev, status in self.devices():
        #     if dev == self.serialno:
        #         return status
        # return None

        # new way!
        proc = self.start_cmd("get-state")
        stdout, stderr = proc.communicate()
        if proc.returncode == 0:
            return stdout.strip()
        elif "not found" in stderr:
            return None
        else:
            raise AdbError(stdout, stderr)

    def wait_for_device(self, timeout=5):
        """
        adb wait-for-device
        if timeout, raise MoaError
        """
        proc = self.start_cmd("wait-for-device")
        timer = threading.Timer(timeout, proc.kill)
        timer.start()
        ret = proc.wait()
        if ret == 0:
            timer.cancel()
        else:
            raise MoaError("device not ready")

    def shell(self, cmds, not_wait=False):
        """
        adb shell
        not_wait: 
            return subprocess if True
            return output if False
        """
        if isinstance(cmds, basestring):
            cmds = 'shell '+ cmds
        else:
            cmds = ['shell'] + list(cmds)
        if not_wait:
            return self.start_cmd(cmds)
        else:
            return self.cmd(cmds)

    def getprop(self, key, strip=True):
        """adb shell getprop"""
        prop = self.shell(['getprop', key])
        if strip:
            prop = prop.rstrip('\r\n')
        return prop

    @property
    def sdk_version(self):
        """adb shell get sdk version"""
        keyname = 'ro.build.version.sdk'
        if keyname not in self._props_cache:
            self._props_cache[keyname] = int(self.getprop(keyname))
        return self._props_cache[keyname]

    def pull(self, remote, local):
        """adb pull"""
        self.cmd(["pull", remote, local])

    def forward(self, local, remote, no_rebind=True):
        """adb forward"""
        cmds = ['forward']
        if no_rebind:
            cmds += ['--no-rebind']
        self.cmd(cmds + [local, remote])
        def try_remove_forward():
            try:
                self.remove_forward(local)
            except:
                pass
        reg_cleanup(try_remove_forward)

    def get_forwards(self):
        """adb forward --list"""
        out = self.cmd(['forward', '--list'])
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            cols = line.split()
            if len(cols) != 3:
                continue
            serialno, local, remote = cols
            yield serialno, local, remote

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
        """adb forward --remove"""
        if local:
            cmds = ["forward", "--remove", local]
        else:
            cmds = ["forward", "--remove-all"]
        self.cmd(cmds)

    def install(self, filepath):
        """adb install"""
        if not os.path.isfile(filepath):
            raise RuntimeError("%s is not valid file" % filepath)
        proc = self.start_cmd(['install', filepath])
        nbsp = NonBlockingStreamReader(proc.stdout)
        proc.wait()

    def uninstall(self, package):
        """adb uninstall"""
        return self.cmd(['uninstall', package])

    def snapshot(self):
        """take a screenshot"""
        raw = self.shell(['screencap', '-p'])
        if platform.system() == "Windows":
            link_breaker = "\r\r\n"
        else:
            link_breaker = "\r\n"
        return raw.replace(link_breaker, "\n")

    def touch(self, (x, y)):
        """touch screen"""
        self.shell('input tap %d %d' % (x, y))
        time.sleep(0.1)

    def swipe(self, (x0, y0), (x1, y1), duration=500):
        """swipe screen"""
        version = self.sdk_version
        if version <= 15:
            raise MoaError('swipe: API <= 15 not supported (version=%d)' % version)
        elif version <= 17:
            self.shell('input swipe %d %d %d %d' % (x0, y0, x1, y1))
        else:
            self.shell('input touchscreen swipe %d %d %d %d %d' % (x0, y0, x1, y1, duration))


class Minicap(object):

    """quick screenshot from minicap  https://github.com/openstf/minicap"""

    VERSION = 4

    def __init__(self, serialno, size=None, projection=PROJECTIONRATE, localport=None, adb=None, stream=True):
        self.serialno = serialno
        self.localport = localport
        self.server_proc = None
        self.projection = projection
        self.adb = adb or ADB(serialno)
        # get_display_info may segfault, so use size info from adb dumpsys
        self.size = size or self.get_display_info()
        self.install()
        self.stream_mode = stream
        self.frame_gen = None
        self.stream_lock = threading.Lock()
        self.init_stream()

    def install(self, reinstall=False):
        """install or upgrade minicap"""
        output = self.adb.shell("ls /data/local/tmp")
        if not reinstall and "minicap\r" in output and "minicap.so\r" in output:
            output = self.adb.shell("LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -v")
            try:
                version = int(output.split(":")[1])
            except (ValueError, IndexError):
                version = -1
            if version >= self.VERSION:
                print 'minicap install skipped'
                return
            else:
                print output
                print 'upgrading minicap to lastest version:', self.VERSION

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
        path = os.path.join(STFLIB, abi, binfile).replace("\\", r"\\")
        self.adb.cmd("push %s %s/minicap" % (path, device_dir)) 
        self.adb.shell("chmod 755 %s/minicap" % (device_dir))

        path = os.path.join(STFLIB, 'minicap-shared/aosp/libs/android-%d/%s/minicap.so' % (sdk, abi)).replace("\\", r"\\")
        self.adb.cmd("push %s %s" % (path, device_dir))    
        self.adb.shell("chmod 755 %s/minicap.so" % (device_dir))
        print "minicap install finished"

    def _get_params(self, use_ori_size=False):
        """get minicap start params, and count projection"""
        real_width = self.size["width"]
        real_height = self.size["height"]
        real_orientation = self.size["rotation"]
        if use_ori_size or not self.projection:
            proj_width, proj_height = real_width, real_height
        elif is_list(self.projection):
            proj_width, proj_height = self.projection
        elif isinstance(self.projection, (int, float)):
            proj_width = self.projection * real_width
            proj_height = self.projection * real_height
        else:
            raise RuntimeError("invalid projection type: %s"%repr(self.projection))
        return real_width, real_height, proj_width, proj_height, real_orientation

    def _setup(self, adb_port=None, lazy=False):
        """setup minicap process on device"""
        # 可能需要改变参数重新setup，所以之前setup过的先关掉
        if self.server_proc:
            print "****************resetup****************"
            sys.stdout.flush()
            self.server_proc.kill()
            self.nbsp.kill()
            self.server_proc = None
            self.adb.remove_forward("tcp:%s" % self.localport)

        real_width, real_height, proj_width, proj_height, real_orientation = self._get_params()

        @retries(3)
        def set_up_forward():
            localport = adb_port or self.localport or self.adb.get_available_forward_local()
            # localport = 11154
            device_port = "moa_minicap_%s" % localport
            self.adb.forward("tcp:%s"%localport, "localabstract:%s"%device_port)
            return localport, device_port

        self.localport, device_port = set_up_forward()
        other_opt = "-l" if lazy else ""
        proc = self.adb.shell(
            "LD_LIBRARY_PATH=/data/local/tmp/ /data/local/tmp/minicap -n '%s' -P %dx%d@%dx%d/%d %s" % (
                device_port,
                real_width, real_height,
                proj_width, proj_height,
                real_orientation, other_opt),
            not_wait=True
        )
        nbsp = NonBlockingStreamReader(proc.stdout, print_output=True)
        while True:
            line = nbsp.readline(timeout=5.0)
            if line is None:
                raise RuntimeError("minicap setup error")
            if "Server start" in line:
                break

        if proc.poll() is not None:
            # minicap server setup error, may be already setup by others
            # subprocess exit immediately
            raise RuntimeError("minicap setup error")
        reg_cleanup(proc.kill)
        self.server_proc = proc
        self.nbsp = nbsp

    def get_display_info(self):
        """
        get display info by minicap
        warning: it may segfault, so we prefer to get from adb
        """
        display_info = self.adb.shell("LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -i")
        display_info = json.loads(display_info)
        if display_info['width'] > display_info['height'] and display_info['rotation'] in [90, 270]:
            display_info['width'], display_info['height'] = display_info['height'], display_info['width']
        self.size = display_info
        return display_info

    def get_frame(self, use_ori_size=True):
        """
        get single frame from minicap -s, slower than get_frames
        1. shell cmd
        2. remove log info
        3. \r\r\n -> \n ... fuck adb
        """
        real_width, real_height, proj_width, proj_height, real_orientation = self._get_params(use_ori_size)

        raw_data = self.adb.shell(
            "LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -n 'moa_minicap' -P %dx%d@%dx%d/%d -s" %
            (real_width, real_height, proj_width, proj_height, real_orientation)
        )
        if platform.system() == "Windows":
            link_breaker = "\r\r\n"
        else:
            link_breaker = "\r\n"
        jpg_data = raw_data.split("for JPG encoder"+link_breaker)[-1].replace(link_breaker, "\n")
        return jpg_data

    def get_frames(self, max_cnt=1000000000, adb_port=None, lazy=False):
        """
        use adb forward and socket communicate
        lazy: use minicap lazy mode (provided by gzmaruijie)
              long connection, send 1 to server, than server return one lastest frame
        """
        self._setup(adb_port, lazy=lazy)
        s = SafeSocket()
        adb_port = adb_port or self.localport
        s.connect(("localhost", adb_port))
        t = s.recv(24)
        # minicap info
        yield struct.unpack("<2B5I2B", t)

        cnt = 0
        while cnt <= max_cnt:
            if lazy:
                s.send("1")
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
                # print 'frame_size',frame_size
                # recv image data
                one_frame = s.recv(frame_size)
                yield one_frame
        s.close()

    def get_header(self):
        """get minicap header info"""
        pass

    def init_stream(self):
        """init minicap stream if stream_mode"""
        if self.stream_mode:
            self.frame_gen = self.get_frames(lazy=True)
            print "minicap header: " + str(self.frame_gen.next())

    def get_frame_from_stream(self):
        """get one frame from minicap stream"""
        with self.stream_lock:
            if self.frame_gen is None:
                self.init_stream()
            return self.frame_gen.next()

    def update_rotation(self, rotation):
        """update rotation, and reset backend stream generator"""
        with self.stream_lock:
            self.size["rotation"] = rotation
            self.frame_gen = None


class Minitouch(object):
    """quick operation from minitouch  https://github.com/openstf/minitouch"""
    def __init__(self, serialno, localport=None, size=None, backend=False, adb=None, adb_addr=DEFAULT_ADB_SERVER):
        self.serialno = serialno
        self.server_proc = None
        self.client = None
        self.max_x, self.max_y = None, None
        self.size = size
        self.adb = adb or ADB(serialno, server_addr=adb_addr)
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
        self.adb.cmd(r"push %s %s/minitouch" % (path, device_dir)) 
        self.adb.shell("chmod 755 %s/minitouch" % (device_dir))
        print "install_minitouch finished"

    def __transform_xy(self, x, y):
        # 根据设备方向、长宽来转换xy值
        if not (self.size and self.size['max_x'] and self.size['max_y']):
            return x, y

        width ,height = self.size['width'], self.size['height']
        print '__transform', x, y
        print self.size
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
            else:
                self.max_x = 32768
                self.max_y = 32768
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

    def __init__(self, serialno=None, addr=DEFAULT_ADB_SERVER, init_display=True, props=None, minicap=True, minicap_stream=True, minitouch=True, init_ime=True):
        self.serialno = serialno or ADB().devices(state="device")[0][0]
        self.adb = ADB(self.serialno, server_addr=addr)
        self.adb.start_server()
        self.adb.wait_for_device()
        if init_display:
            self._init_display(props)
            # 目前几台设备不能用stream_mode，他们的特点是sdk=17，先这样写看看
            # if self.sdk_version == 17:
            #     print "minicap_stream mode not available on sdk 17"
            #     minicap_stream = False
            # minicap version > 2 解决了17的问题，先注释掉看看
            self.minicap = Minicap(serialno, size=self.size, adb=self.adb, stream=minicap_stream) if minicap else None
            self.minitouch = Minitouch(serialno, size=self.size, adb=self.adb) if minitouch else None
        if init_ime:
            self.ime = AdbKeyboardIme(self.adb)
            self.toggle_shell_ime()
            reg_cleanup(self.ime.end)

    def _init_display(self, props=None):
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

    def ampath(self, package):
        output = self.adb.shell(['pm', 'path', package])
        if 'package:' not in output:
            raise MoaError('package not found, output:[%s]'%output)
        return output.split(":")[1].strip()

    def amcheck(self, package):
        output = self.adb.shell(['pm', 'list', 'packages', package])
        if 'package:' not in output:
            raise MoaError('package not found, output:[%s]'%output)
        return output.strip()

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
        """
        安装应用
        """
        # 先解析apk，看是否存在已安装的app
        packages = self.amlist()
        apk = apkparser.APK(filepath)
        apk_package = apk.get_package()
        if apk_package in packages:
            # 如果reinstall=True，先卸载掉之前的apk，防止签名不一致导致的无法覆盖
            if reinstall:
                print "package:%s already exists, uninstall first" % apk_package
                self.uninstall(apk_package)
            # 否则直接return True
            else:
                print "package:%s already exists, skip reinstall" % apk_package
                return True

        # 唤醒设备
        self.wake()
        # 预装accessibility的apk，用于自动点掉各种弹框
        if ACCESSIBILITYSERVICE_PACKAGE not in packages:
            self.adb.install(ACCESSIBILITYSERVICE_APK)
        else:
            output = self.adb.shell("dumpsys package "+ACCESSIBILITYSERVICE_PACKAGE)
            try:
                version = re.search("versionName=(\S+)", output)
                version = float(version.group().split("=")[1])
            except (ValueError, IndexError, AttributeError):
                version = -1
            if version >= ACCESSIBILITYSERVICE_VERSION:
                print 'accessibility service install skipped'
            else:
                print 'current version:', version
                print 'upgrading accessibility service to lastest version:', ACCESSIBILITYSERVICE_VERSION
                self.uninstall(ACCESSIBILITYSERVICE_PACKAGE)
                self.adb.install(ACCESSIBILITYSERVICE_APK)

        # http://phone.nie.netease.com:7100/#!/control/JTJ4C15710038858
        # 为了兼容上面那台设备，先调换下面两句的执行顺序，观察一下其他设备
        # by liuxin 2016.6.17
        self.adb.shell('settings put secure enabled_accessibility_services com.netease.accessibility/com.netease.accessibility.MyAccessibilityService:com.netease.testease/com.netease.testease.service.MyAccessibilityService')
        self.adb.shell('settings put secure accessibility_enabled 1')

        # rm all apks in /data/local/tmp to get enouph space
        self.adb.shell("rm -f /data/local/tmp/*.apk")
        self.adb.install(filepath)
        if check:
            self.amcheck(apk_package)

        self.adb.shell('settings put secure accessibility_enabled 0')
        self.adb.shell('settings put secure enabled_accessibility_services 0')

    def uninstall(self, package):
        return self.adb.uninstall(package)

    def snapshot(self, filename="tmp.png", ensure_orientation=True):
        if self.minicap and self.minicap.stream_mode:
            screen = self.minicap.get_frame_from_stream()
        elif self.minicap:
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
        self.adb.shell(['am', 'start', '-a', 'jp.co.cyberagent.stf.ACTION_IDENTIFY'])

        # todo:
        # 1. 还需要按power键吗？
        # 2. 如果非锁屏状态，上面步骤可以省略

        # 1. release apk里面有，不需要按电源键了，
        # 2. is_screenon有些设备不起效
        # if not self.is_screenon():
        #     self.keyevent("POWER")

        self.keyevent("HOME")

    def home(self):
        self.keyevent("HOME")

    def text(self, text):
        if getattr(self, "ime", None):
            text = text.decode("utf-8").encode(sys.stdin.encoding or sys.getfilesystemencoding())
            self.adb.shell("am broadcast -a ADB_INPUT_TEXT --es msg '%s'" % text)
            self.adb.shell(["input", "keyevent", "ENTER"])
        else:
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
        print self.size
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
            self.minicap.update_rotation(self.size["rotation"])
            # self.minicap.get_display_info()

    def _initOrientationWatcher(self):
        try:
            apk_path = self.ampath(ROTATIONWATCHER_PACKAGE)
        except MoaError:
            self.install(ROTATIONWATCHER_APK)
            apk_path = self.ampath(ROTATIONWATCHER_PACKAGE)
        p = self.adb.shell('export CLASSPATH=%s;exec app_process /system/bin jp.co.cyberagent.stf.rotationwatcher.RotationWatcher' % apk_path, not_wait=True)
        if p.poll() is not None:
            raise RuntimeError("orientationWatcher setup error")
        return p

    def orientationWatcher(self):
        self.ow_proc = self._initOrientationWatcher()
        reg_cleanup(self.ow_proc.kill)


        def _refresh_by_ow():
            line = self.ow_proc.stdout.readline()
            if not line:
                print "orientationWatcher has ended"
                return None

            ori = int(line) / 90
            self.refreshOrientationInfo(ori)
            return ori

        def _refresh_orientation(self):
            while True:
                ori = _refresh_by_ow()
                if ori is None:
                    break
                if getattr(self, "ow_callback", None):
                    self.ow_callback(ori, *self.ow_callback_args)

        _refresh_by_ow()
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


class Emulator(Android):
    """ android emulator
    注意init第一个参数是模拟器的名字
    """
    _props_tmp = "/data/local/tmp/moa_props.tmp"

    def __init__(self, emulator_name='bluestacks', serialno=None, addr=DEFAULT_ADB_SERVER, init_display=True, props=None, minicap=True, \
                 minicap_stream=False, minitouch=True, init_ime=False):
        from moa.core.android.emulator.android_emulator import EMULATOR_INFO
        if EMULATOR_INFO.get(emulator_name):
            self.emulator_name = emulator_name
            self.emulator_info = EMULATOR_INFO[emulator_name]
        else:
            raise RuntimeError("please use the Bluestacks emulator")
        self.init_emulator()
        if not self.serialno:
            self.serialno = serialno or ADB('').devices(state="device")[0][0]
        self.adb = ADB(self.serialno, server_addr=addr)
        self.adb.start_server()
        self.adb.wait_for_device()
        if init_display:
            self._init_display(props)
            self.minitouch = Minitouch(serialno, size=self.size, adb=self.adb) if minitouch else None
        if init_ime:
            self.ime = AdbKeyboardIme(self.adb)
            self.toggle_shell_ime()

    def _init_display(self, props=None):
        # read props from outside or cached source, to save init time
        self.props = props or self._load_props()
        self.get_display_info()
        # 直接读props的配置可能有点问题，屏幕的朝向不正确
        #self.get_display_info()
        self.orientationWatcher()
        self.sdk_version = self.props.get("sdk_version") or self.adb.sdk_version
        self._dump_props()

    def get_display_info(self):
        """
        发现新版bluestacks有应用分辨率与实际软件设置分辨率大小不匹配的情况
        改用窗口获取大小的方式来拿分辨率准确一点
        :return:
        """
        self.size = self.getPhysicalDisplayInfo()
        self.size["orientation"] = self.getDisplayOrientation()
        self.size["rotation"] = self.size["orientation"] * 90
        self.size["max_x"], self.size["max_y"] = self.getEventInfo()

        hwnd = self.emulator_hwnd
        print 'hwnd', hwnd
        rect = win32gui.GetClientRect(hwnd)
        width = abs(rect[2] - rect[0])
        height = abs(rect[3] - rect[1])
        if self.size['width'] != width or self.size['height'] != height:
            self.size['width'] = width
            self.size['height'] = height
        return self.size

    def getPhysicalDisplayInfo(self):
        # android那边会保证width < height
        # 但是模拟器如果坚持保证宽比长小的话可能会有转置的问题
        info = self._getPhysicalDisplayInfo()
        return info

    def init_emulator(self):
        """
        初始化模拟器，需要1.找到对应的窗口句柄 2.连上adb
        :return:
        """
        emu_info = self.emulator_info
        if not emu_info:
            self.emulator_hwnd = 0
            self.emulator_info = {}
        else:
            self.emulator_info = emu_info
        if emu_info and emu_info['adb_connect']:
            self.serialno = emu_info['adb_connect']
        else:
            self.serialno = ''
        self.emulator_hwnd = EmulatorHelper.find_emu_windows_hwnd(self.emulator_name) or 0
        if not self.emulator_hwnd:
            # 如果模拟器已经被嵌入到IDE里的话，会找不到句柄的，要重新搜索IDE下面的子窗口句柄才能找到
            self.emulator_hwnd = EmulatorHelper.find_emu_embed_airtestide(self.emulator_name) or 0
        if not self.emulator_hwnd or not self.emulator_name:
            print 'please launch a emulator first'

    def wake(self):
        """
        模拟器的解锁屏幕有点问题，这里直接return先
        :return:
        """
        return True

    def getDisplayOrientation(self):
        """
        模拟器里的横屏和竖屏，跟真机好像是相反的，一些老版本的机型上可能也有同样问题
        目前尝试过的orientation值：
        网易模拟器：横屏0
        逍遥安卓： 横屏0，竖屏3
        TODO: genymotion 待测，尤其是最后一种返回情况
        但是虽然值不同，坐标的转换规则是一样的，就是即使是横屏，坐标也不需要转换，后续更多情况待测试
        :return:
        """
        SurfaceFlingerRE = re.compile('orientation=(\d+)')
        output = self.adb.shell('dumpsys SurfaceFlinger')
        m = SurfaceFlingerRE.search(output)
        if m:
            ori = int(m.group(1))
            return ori

        # Fallback method to obtain the orientation
        # See https://github.com/dtmilano/AndroidViewClient/issues/128
        surfaceOrientationRE = re.compile('SurfaceOrientation:\s+(\d+)')
        output = self.adb.shell('dumpsys input')
        m = surfaceOrientationRE.search(output)
        if m:
            ori = int(m.group(1))
            return ori

        # 几乎大部分模拟器都是横屏，但是height依然会大于width，先默认返回1
        return 0 if self.size["height"] > self.size['width'] else 1

    def snapshot_bluestacks(self, filename="tmp.png", ensure_orientation=True):
        """这种截图方法是windows窗口截图，不能截最小化状态下的模拟器，
        只能截bluestacks内核的相关模拟器，如果是海马玩等其他类别的模拟器暂不支持

        """
        import win32gui
        import win32ui
        import win32con
        import cv2
        hwnd = self.emulator_hwnd
        if not hwnd:
            raise RuntimeError("please launch a emulator first ")
        try:
            rect = win32gui.GetClientRect(hwnd)
        except:
            print "snapshot failed"
            raise RuntimeError("please launch a emulator first ")
        width = abs(rect[2] - rect[0])
        height = abs(rect[3] - rect[1])
        if width != self.size['width']:
            self.size['width'] = width
        if height != self.size['height']:
            self.size['height'] = height
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
        saveBitMap.SaveBitmapFile(saveDC, filename)
        img = cv2.imread(filename)
        return img

    def snapshot_win_game(self, filename="tmp.png", ensure_orientation=True):
        """
        这种截图方法比上一种稍微慢一些，能够截游戏窗口、genymotion模拟器
        不能截windows下的aero效果，不能截海马玩
        """
        import ctypes, win32con
        import cv2
        from PyQt4 import QtGui
        # getWindowRect取得的是整个窗口的RECT坐标，left, top, right, bottom
        client_hwnd = self.emulator_hwnd
        rect = win32gui.GetClientRect(client_hwnd)
        width = abs(rect[2] - rect[0])
        height = abs(rect[3] - rect[1])

        gdi = ctypes.windll.gdi32
        targetDC = ctypes.windll.user32.GetDC(client_hwnd)
        bitmapDC = gdi.CreateCompatibleDC(targetDC)
        hBitmap = gdi.CreateCompatibleBitmap(targetDC, width, height)
        oldBitmap = gdi.SelectObject(bitmapDC, hBitmap)
        gdi.BitBlt(bitmapDC, 0, 0, width, height, targetDC, 0, 0, win32con.SRCCOPY)
        iBPP = gdi.GetDeviceCaps(bitmapDC, 12)
        flag = QtGui.QImage.Format_RGB16 if iBPP == 16 else QtGui.QImage.Format_ARGB32
        flashImage = QtGui.QImage(width, height, flag)
        pBits = flashImage.bits()
        gdi.GetBitmapBits(hBitmap, width*height*iBPP/8, int(pBits))
        gdi.SelectObject(bitmapDC, oldBitmap)
        gdi.DeleteDC(bitmapDC)
        gdi.DeleteObject(hBitmap)

        ctypes.windll.user32.ReleaseDC(client_hwnd, targetDC)
        flashImage.save(filename)
        img = cv2.imread(filename)
        return img

    def snapshot(self, filename="tmp.png", ensure_orientation=True):
        """
        模拟器的截图
        """
        if self.emulator_info.get('kernel') in ['bluestacks']:
            if not self.emulator_hwnd:
                raise RuntimeError("please lanuch a emulator first")
            return self.snapshot_bluestacks(filename, ensure_orientation)
        else:
            screen = self.adb.snapshot()
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
    # serialno = "10.250.210.118:57217"
    # t = time.clock()
    serialno = None
    a = Android(serialno, minicap_stream=True)
    # gen = a.minicap.get_frames()
    print a.sdk_version
    # a.home()
    # a.amclear("com.netease.my")
    # for i in range(10):
    #     print "get next frame"
    #     # frame = gen.next()
    #     frame = a.snapshot()
    #     time.sleep(1)
    # a.amstart("com.netease.my")
    # header = gen.next()
    a.amclear("com.netease.my")
    a.amstart("com.netease.my")
    for i in range(1000):
        print "get next frame"
        # frame = gen.next()
        # screen = aircv.string_2_img(frame)
        # aircv.imwrite("tmp.png", screen)
        frame = a.snapshot()
        time.sleep(1)
    # # a.uninstall(RELEASELOCK_PACKAGE)
    # # a.wake()
    # a.amstart("com.netease.my")
    # t = time.clock()
    # a = Android(serialno, init_display=False, minicap=False, minitouch=False, init_ime=False)
    # # a.uninstall(RELEASELOCK_PACKAGE)
    # # a.wake()
    # a.amstart("com.netease.my")
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
