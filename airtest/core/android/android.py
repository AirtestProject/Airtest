#! /usr/bin/env python
# -*- coding: utf-8 -*-
import re
import warnings
from airtest import aircv
from airtest.core.device import Device
from airtest.core.error import MoaError, AdbShellError
from airtest.core.utils import NonBlockingStreamReader, reg_cleanup, get_logger
from airtest.core.android.ime import YosemiteIme
from airtest.core.android.constant import YOSEMITE_APK, YOSEMITE_PACKAGE
from airtest.core.android.adb import ADB
from airtest.core.android.minicap import Minicap
from airtest.core.android.minitouch import Minitouch
from airtest.core.android.javacap import Javacap
from airtest.core.android.rotation import RotationWatcher, XYTransformer
from airtest.core.utils.compat import apkparser
LOGGING = get_logger('android')


class Android(Device):

    """Android Client"""

    def __init__(self, serialno=None, adbhost=None, cap_method="minicap_stream", shell_ime=True):
        super(Android, self).__init__()
        self.serialno = serialno or ADB().devices(state="device")[0][0]
        self.adb = ADB(self.serialno, server_addr=adbhost)
        # self.adb.start_server()
        self.adb.wait_for_device()
        self.sdk_version = self.adb.sdk_version
        self._init_requirement_apk(YOSEMITE_APK, YOSEMITE_PACKAGE)
        self._size = None
        self._init_rw()
        self._init_cap(cap_method)
        self._init_touch(True)
        self.shell_ime = shell_ime

    def _init_cap(self, cap_method):
        self.cap_method = cap_method
        if cap_method in ("minicap", "minicap_stream"):
            stream = True if cap_method == "minicap_stream" else False
            self.minicap = Minicap(self.serialno, adb=self.adb, stream=stream)
            self.rw.reg_callback(lambda x: self.minicap.update_rotation(x * 90))
        elif cap_method == "javacap":
            self.javacap = Javacap(self.serialno, adb=self.adb)
        else:
            print("cap_method %s not found, use adb screencap" % cap_method)
            self.cap_method = None

    def _init_touch(self, minitouch=True):
        self.minitouch = Minitouch(self.serialno, adb=self.adb) if minitouch else None

    def _init_requirement_apk(self, apk_path, package):
        apk_version = apkparser.version(apk_path)
        installed_version = self.adb.get_package_version(package)
        LOGGING.info("local version code is {}, installed version code is {}".format(apk_version, installed_version))
        if not installed_version or apk_version > installed_version:
            self.install_app(apk_path, replace=True)

    def _init_rw(self):
        self.rw = RotationWatcher(self)
        # call self.rw.start when you need it.
        # minicap will call it in stream mode

        def refresh_ori(ori):
            self.display_info["orientation"] = ori
            self.display_info["rotation"] = ori * 90

        self.rw.reg_callback(refresh_ori)

    def list_app(self, third_only=False):
        return self.adb.list_app(third_only)

    def path_app(self, package):
        return self.adb.path_app(package)

    def check_app(self, package):
        return self.adb.check_app(package)

    def start_app(self, package, activity=None):
        return self.adb.start_app(package, activity)

    def stop_app(self, package):
        return self.adb.stop_app(package)

    def clear_app(self, package):
        return self.adb.clear_app(package)

    def install_app(self, filepath, replace=False):
        self.adb.install(filepath, replace=replace)

    def uninstall_app(self, package):
        return self.adb.uninstall(package)

    def snapshot(self, filename=None, ensure_orientation=True):
        """default not write into file."""
        if self.cap_method == "minicap_stream":
            self.rw.get_ready()
            screen = self.minicap.get_frame_from_stream()
        elif self.cap_method == "minicap":
            screen = self.minicap.get_frame()
        elif self.cap_method == "javacap":
            screen = self.javacap.get_frame()
        else:
            screen = self.adb.snapshot()
        # 输出cv2对象
        screen = aircv.utils.string_2_img(screen)

        # 保证方向是正的
        if ensure_orientation and self.display_info["orientation"]:
            # minicap截图根据sdk_version不一样
            if self.cap_method in ("minicap", "minicap_stream") and self.sdk_version <= 16:
                h, w = screen.shape[:2]  # cv2的shape是高度在前面!!!!
                if w < h:  # 当前是横屏，但是图片是竖的，则旋转，针对sdk<=16的机器
                    screen = aircv.rotate(screen, self.display_info["orientation"] * 90, clockwise=False)
            # adb 截图总是要根据orientation旋转
            elif self.cap_method is None:
                screen = aircv.rotate(screen, self.display_info["orientation"] * 90, clockwise=False)
        if filename:
            aircv.imwrite(filename, screen)
        return screen

    def shell(self, *args, **kwargs):
        return self.adb.shell(*args, **kwargs)

    def keyevent(self, keyname):
        self.adb.shell(["input", "keyevent", keyname.upper()])

    def wake(self):
        self.home()
        self.adb.shell(['am', 'start', '-a', 'com.netease.nie.yosemite.ACTION_IDENTIFY'])
        self.keyevent("HOME")

    def home(self):
        self.keyevent("HOME")

    def text(self, text, enter=True):
        if self.shell_ime:
            # shell_ime用于输入中文
            if not hasattr(self, "ime"):
                # 开启shell_ime
                self.toggle_shell_ime()
            self.ime.text(text)
        else:
            self.adb.shell(["input", "text", text])

        # 游戏输入时，输入有效内容后点击Enter确认，如不需要，enter置为False即可。
        if enter:
            self.adb.shell(["input", "keyevent", "ENTER"])

    def toggle_shell_ime(self, on=True):
        """切换到shell的输入法，用于text"""
        self.shell_ime = True
        if not hasattr(self, "ime"):
            self.ime = YosemiteIme(self)
        if on:
            self.ime.start()
            reg_cleanup(self.ime.end)
        else:
            self.ime.end()

    def touch(self, pos, times=1, duration=0.01):
        pos = self._transformPointByOrientation(pos)
        for _ in range(times):
            if self.minitouch:
                self.minitouch.touch(pos, duration=duration)
            else:
                self.adb.touch(pos)

    def swipe(self, p1, p2, duration=0.5, steps=5):
        p1 = self._transformPointByOrientation(p1)
        p2 = self._transformPointByOrientation(p2)
        if self.minitouch:
            self.minitouch.swipe(p1, p2, duration=duration, steps=steps)
        else:
            duration *= 1000  # adb的swipe操作时间是以毫秒为单位的。
            self.adb.swipe(p1, p2, duration=duration)

    def operate(self, tar):
        x, y = tar.get("x"), tar.get("y")
        if (x, y) != (None, None):
            x, y = self._transformPointByOrientation((x, y))
            tar.update({"x": x, "y": y})
        self.minitouch.operate(tar)

    def start_recording(self, max_time=1800, bit_rate=None, vertical=None):
        if getattr(self, "recording_proc", None):
            raise MoaError("recording_proc has already started")
        pkg_path = self.path_app(YOSEMITE_PACKAGE)
        max_time_param = "-Dduration=%d" % max_time if max_time else ""
        bit_rate_param = "-Dbitrate=%d" % bit_rate if bit_rate else ""
        if vertical == None:
            vertical_param = ""
        else:
            vertical_param = "-Dvertical=true" if vertical else "-Dvertical=false"
        p = self.adb.shell('CLASSPATH=%s exec app_process %s %s %s /system/bin %s.Recorder --start-record' % 
            (pkg_path, max_time_param, bit_rate_param, vertical_param, YOSEMITE_PACKAGE), not_wait=True)
        nbsp = NonBlockingStreamReader(p.stdout)
        while True:
            line = nbsp.readline(timeout=5)
            if line is None:
                raise RuntimeError("recording setup error")
            m = re.match("start result: Record start success! File path:(.*\.mp4)", line.strip())
            if m:
                output = m.group(1)
                self.recording_proc = p
                self.recording_file = output
                return True
        raise RuntimeError("recording setup error")

    def stop_recording(self, output="screen.mp4", is_interrupted=False):
        pkg_path = self.path_app(YOSEMITE_PACKAGE)
        p = self.adb.shell('CLASSPATH=%s exec app_process /system/bin %s.Recorder --stop-record' % (pkg_path, YOSEMITE_PACKAGE), not_wait=True)
        p.wait()
        self.recording_proc = None
        if is_interrupted:
            return
        for line in p.stdout.readlines():
            m = re.match("stop result: Stop ok! File path:(.*\.mp4)", line.strip())
            if m:
                self.recording_file = m.group(1)
                self.adb.pull(self.recording_file, output)
                self.adb.shell("rm %s" % self.recording_file)
                return
        raise MoaError("start_recording first")

    def get_top_activity_name_and_pid(self):
        """not working on all devices"""
        return self.get_top_activity_name_and_pid()

    def get_top_activity_name(self):
        """not working on all devices"""
        return self.adb.get_top_activity_name()

    def is_keyboard_shown(self):
        """not working on all devices"""
        return self.adb.is_keyboard_shown()

    def is_screenon(self):
        """not working on all devices"""
        return self.adb.is_screenon()

    def is_locked(self):
        """not working on all devices"""
        return self.adb.is_locked()

    def unlock(self):
        """not working on many devices"""
        return self.adb.unlock()

    @property
    def display_info(self):
        return self.adb.display_info

    def getprop(self, key, strip=True):
        return self.adb.getprop(key, strip)

    def get_display_info(self):
        return self.adb.get_display_info()

    def getCurrentScreenResolution(self):
        # 注意黑边问题，需要用安卓接口获取区分两种分辨率
        w, h = self.display_info["width"], self.display_info["height"]
        if self.display_info["orientation"] in [1, 3]:
            w, h = h, w
        return w, h

    def _transformPointByOrientation(self, tuple_xy):
        x, y = tuple_xy
        """图片坐标转换为物理坐标，即相对于手机物理左上角的坐标(minitouch点击的是物理坐标)."""
        x, y = XYTransformer.up_2_ori(
            (x, y),
            (self.display_info["physical_width"], self.display_info["physical_height"]),
            self.display_info["orientation"]
        )
        return x, y

    def logcat(self, *args, **kwargs):
        return self.adb.logcat(*args, **kwargs)

    def pinch(self, *args, **kwargs):
        return self.minitouch.pinch(*args, **kwargs)
