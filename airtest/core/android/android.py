#! /usr/bin/env python
# -*- coding: utf-8 -*-
from airtest import aircv
from airtest.core.device import Device
from airtest.core.utils import get_logger
from airtest.core.android.ime import YosemiteIme
from airtest.core.android.constant import CAP_METHOD, TOUCH_METHOD, IME_METHOD
from airtest.core.android.adb import ADB
from airtest.core.android.minicap import Minicap
from airtest.core.android.minitouch import Minitouch
from airtest.core.android.javacap import Javacap
from airtest.core.android.rotation import RotationWatcher, XYTransformer
from airtest.core.android.recorder import Recorder
LOGGING = get_logger('android')


class Android(Device):

    """Android Device"""

    def __init__(self, serialno=None, adbhost=None,
                 cap_method=CAP_METHOD.MINICAP_STREAM,
                 touch_method=TOUCH_METHOD.MINITOUCH,
                 ime_method=IME_METHOD.YOSEMITEIME):
        super(Android, self).__init__()
        self.serialno = serialno or ADB().devices(state="device")[0][0]
        self.cap_method = cap_method
        self.touch_method = touch_method
        self.ime_method = ime_method
        # init adb
        self.adb = ADB(self.serialno, server_addr=adbhost)
        self.adb.wait_for_device()
        self.sdk_version = self.adb.sdk_version
        # init components
        self.rotation_watcher = RotationWatcher(self.adb)
        self.minicap = Minicap(serialno, adb=self.adb)
        self.javacap = Javacap(serialno, adb=self.adb)
        self.minitouch = Minitouch(serialno, adb=self.adb)
        self.yosemite_ime = YosemiteIme(self)
        self.recorder = Recorder(self.adb)
        self._register_rotation_watcher()

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
        self.adb.install_app(filepath, replace=replace)

    def uninstall_app(self, package):
        return self.adb.uninstall_app(package)

    def snapshot(self, filename=None, ensure_orientation=True):
        """default not write into file."""
        if self.cap_method == CAP_METHOD.MINICAP_STREAM:
            self.rotation_watcher.get_ready()
            screen = self.minicap.get_frame_from_stream()
        elif self.cap_method == CAP_METHOD.MINICAP:
            screen = self.minicap.get_frame()
        elif self.cap_method == CAP_METHOD.JAVACAP:
            screen = self.javacap.get_frame()
        else:
            screen = self.adb.snapshot()
        # 输出cv2对象
        screen = aircv.utils.string_2_img(screen)

        # 保证方向是正的
        if ensure_orientation and self.display_info["orientation"]:
            # minicap截图根据sdk_version不一样
            if self.cap_method in (CAP_METHOD.MINICAP, CAP_METHOD.MINICAP_STREAM) and self.sdk_version <= 16:
                h, w = screen.shape[:2]  # cv2的shape是高度在前面!!!!
                if w < h:  # 当前是横屏，但是图片是竖的，则旋转，针对sdk<=16的机器
                    screen = aircv.rotate(screen, self.display_info["orientation"] * 90, clockwise=False)
            # adb 截图总是要根据orientation旋转
            elif self.cap_method == CAP_METHOD.ADBCAP:
                screen = aircv.rotate(screen, self.display_info["orientation"] * 90, clockwise=False)
        if filename:
            aircv.imwrite(filename, screen)
        return screen

    def shell(self, *args, **kwargs):
        return self.adb.shell(*args, **kwargs)

    def keyevent(self, keyname, **kwargs):
        self.adb.shell(["input", "keyevent", keyname.upper()])

    def wake(self):
        self.home()
        self.recorder.get_ready()  # 暂时Yosemite只用了ime
        self.adb.shell(['am', 'start', '-a', 'com.netease.nie.yosemite.ACTION_IDENTIFY'])
        self.keyevent("HOME")

    def home(self):
        self.keyevent("HOME")

    def text(self, text, enter=True):
        if self.ime_method == IME_METHOD.YOSEMITEIME:
            self.yosemite_ime.text(text)
        else:
            self.adb.shell(["input", "text", text])

        # 游戏输入时，输入有效内容后点击Enter确认，如不需要，enter置为False即可。
        if enter:
            self.adb.shell(["input", "keyevent", "ENTER"])

    def touch(self, pos, times=1, duration=0.01):
        pos = self._touch_point_by_orientation(pos)
        for _ in range(times):
            if self.touch_method == TOUCH_METHOD.MINITOUCH:
                self.minitouch.touch(pos, duration=duration)
            else:
                self.adb.touch(pos)

    def swipe(self, p1, p2, duration=0.5, steps=5):
        p1 = self._touch_point_by_orientation(p1)
        p2 = self._touch_point_by_orientation(p2)
        if self.minitouch:
            self.minitouch.swipe(p1, p2, duration=duration, steps=steps)
        else:
            duration *= 1000  # adb的swipe操作时间是以毫秒为单位的。
            self.adb.swipe(p1, p2, duration=duration)

    def pinch(self, *args, **kwargs):
        return self.minitouch.pinch(*args, **kwargs)

    def logcat(self, *args, **kwargs):
        return self.adb.logcat(*args, **kwargs)

    def getprop(self, key, strip=True):
        return self.adb.getprop(key, strip)

    def get_top_activity_name_and_pid(self):
        """not working on all devices"""
        return self.adb.get_top_activity_name_and_pid()

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

    def get_display_info(self):
        return self.adb.get_display_info()

    def get_current_resolution(self):
        """get current resolution after rotation"""
        # 注意黑边问题，需要用安卓接口获取区分两种分辨率
        w, h = self.display_info["width"], self.display_info["height"]
        if self.display_info["orientation"] in [1, 3]:
            w, h = h, w
        return w, h

    def start_recording(self, *args, **kwargs):
        self.recorder.start_recording(*args, **kwargs)

    def stop_recording(self, *args, **kwargs):
        self.recorder.stop_recording(*args, **kwargs)

    def _register_rotation_watcher(self):
        """auto refresh android.display when rotation changed"""
        def refresh_ori(ori):
            self.display_info["orientation"] = ori
            self.display_info["rotation"] = ori * 90

        self.rotation_watcher.reg_callback(refresh_ori)
        self.rotation_watcher.reg_callback(lambda x: self.minicap.update_rotation(x * 90))

    def _touch_point_by_orientation(self, tuple_xy):
        """图片坐标转换为物理坐标，即相对于手机物理左上角的坐标(minitouch点击的是物理坐标)."""
        x, y = tuple_xy
        x, y = XYTransformer.up_2_ori(
            (x, y),
            (self.display_info["physical_width"], self.display_info["physical_height"]),
            self.display_info["orientation"]
        )
        return x, y
