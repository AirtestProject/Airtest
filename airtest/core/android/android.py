#! /usr/bin/env python
# -*- coding: utf-8 -*-
from airtest import aircv
from airtest.utils.logger import get_logger
from airtest.core.device import Device
from airtest.core.android.ime import YosemiteIme
from airtest.core.android.constant import CAP_METHOD, TOUCH_METHOD, IME_METHOD
from airtest.core.android.adb import ADB
from airtest.core.android.minicap import Minicap
from airtest.core.android.minitouch import Minitouch
from airtest.core.android.javacap import Javacap
from airtest.core.android.rotation import RotationWatcher, XYTransformer
from airtest.core.android.recorder import Recorder
LOGGING = get_logger(__name__)


class Android(Device):

    """Android Device Class"""

    def __init__(self, serialno=None, host=None,
                 cap_method=CAP_METHOD.MINICAP_STREAM,
                 touch_method=TOUCH_METHOD.MINITOUCH,
                 ime_method=IME_METHOD.YOSEMITEIME):
        super(Android, self).__init__()
        self.serialno = serialno or ADB().devices(state="device")[0][0]
        self.cap_method = cap_method
        self.touch_method = touch_method
        self.ime_method = ime_method
        # init adb
        self.adb = ADB(self.serialno, server_addr=host)
        self.adb.wait_for_device()
        self.sdk_version = self.adb.sdk_version
        # init components
        self.rotation_watcher = RotationWatcher(self.adb)
        self.minicap = Minicap(self.adb)
        self.javacap = Javacap(self.adb)
        self.minitouch = Minitouch(self.adb)
        self.yosemite_ime = YosemiteIme(self.adb)
        self.recorder = Recorder(self.adb)
        self._register_rotation_watcher()

    def list_app(self, third_only=False):
        """
        Return list of packages

        Args:
            third_only: if True, only third party applications are listed

        Returns:
            array of applications

        """
        return self.adb.list_app(third_only)

    def path_app(self, package):
        """
        Print the full path to the package

        Args:
            package: package name

        Returns:
            the full path to the package

        """
        return self.adb.path_app(package)

    def check_app(self, package):
        """
        Check is package exists on the device

        Args:
            package: package name

        Returns:
            True or False whether the package exists on the device or not

        """
        return self.adb.check_app(package)

    def start_app(self, package, activity=None):
        """
        Start the application and activity

        Args:
            package: package name
            activity: activity name

        Returns:
            None

        """
        return self.adb.start_app(package, activity)

    def stop_app(self, package):
        """
        Stop the application

        Args:
            package: package name

        Returns:
            None

        """
        return self.adb.stop_app(package)

    def clear_app(self, package):
        """
        Clear all application data

        Args:
            package: package name

        Returns:
            None

        """
        return self.adb.clear_app(package)

    def install_app(self, filepath, replace=False):
        """
        Install the application on the device

        Args:
            filepath: full path to the `apk` file to be installed on the device
            replace: True or False to replace the existing application

        Returns:
            output from installation process

        """
        return self.adb.install_app(filepath, replace=replace)

    def uninstall_app(self, package):
        """
        Uninstall the application from the device

        Args:
            package: package name

        Returns:
            output from the uninstallation process

        """
        return self.adb.uninstall_app(package)

    def snapshot(self, filename=None, ensure_orientation=True):
        """
        Take the screenshot of the display. The output is send to stdout by default.

        Args:
            filename: name of the file where to store the screenshot, default is None which si stdout
            ensure_orientation: True or False whether to keep the orientation same as display

        Returns:
            screenshot output

        """
        """default not write into file."""
        if self.cap_method == CAP_METHOD.MINICAP_STREAM:
            self.rotation_watcher.get_ready()
            screen = self.minicap.get_frame_from_stream()
        elif self.cap_method == CAP_METHOD.MINICAP:
            screen = self.minicap.get_frame()
        elif self.cap_method == CAP_METHOD.JAVACAP:
            screen = self.javacap.get_frame_from_stream()
        else:
            screen = self.adb.snapshot()
        # output cv2 object
        try:
            screen = aircv.utils.string_2_img(screen)
        except:
            # may be black/locked screen or other reason, print exc for debugging
            import traceback
            traceback.print_exc()
            return None

        # ensure the orientation is right
        if ensure_orientation and self.display_info["orientation"]:
            # minicap screenshots are different for various sdk_version
            if self.cap_method in (CAP_METHOD.MINICAP, CAP_METHOD.MINICAP_STREAM) and self.sdk_version <= 16:
                h, w = screen.shape[:2]  # cvshape是高度在前面!!!!
                if w < h:  # 当前是横屏，但是图片是竖的，则旋转，针对sdk<=16的机器
                    screen = aircv.rotate(screen, self.display_info["orientation"] * 90, clockwise=False)
            # adb 截图总是要根据orientation旋转
            elif self.cap_method == CAP_METHOD.ADBCAP:
                screen = aircv.rotate(screen, self.display_info["orientation"] * 90, clockwise=False)
        if filename:
            aircv.imwrite(filename, screen)
        return screen

    def shell(self, *args, **kwargs):
        """
        Return `adb shell` interpreter
        Args:
            *args: optional shell commands
            **kwargs: optional shell commands

        Returns:
            None

        """
        return self.adb.shell(*args, **kwargs)

    def keyevent(self, keyname, **kwargs):
        """
        Perform keyevent on the device
        Args:
            keyname: keyeven name
            **kwargs: optional arguments

        Returns:
            None

        """
        self.adb.keyevent(keyname)

    def wake(self):
        """
        Perform wake up event

        Returns:
            None

        """
        self.home()
        self.recorder.install_or_upgrade()  # 暂时Yosemite只用了ime
        self.adb.shell(['am', 'start', '-a', 'com.netease.nie.yosemite.ACTION_IDENTIFY'])
        self.keyevent("HOME")

    def home(self):
        """
        Press HOME button

        Returns:
            None

        """
        self.keyevent("HOME")

    def text(self, text, enter=True):
        """
        Input text on the device

        Args:
            text: text to input
            enter: True or False whether to press `Enter` key

        Returns:
            None

        """
        if self.ime_method == IME_METHOD.YOSEMITEIME:
            self.yosemite_ime.text(text)
        else:
            self.adb.shell(["input", "text", text])

        # 游戏输入时，输入有效内容后点击Enter确认，如不需要，enter置为False即可。
        if enter:
            self.adb.shell(["input", "keyevent", "ENTER"])

    def touch(self, pos, times=1, duration=0.01):
        """
        Perform touch event on the device

        Args:
            pos: coordinates (x, y)
            times: how many touches to be performed
            duration: how long to touch the screen

        Returns:
            None

        """
        pos = self._touch_point_by_orientation(pos)
        for _ in range(times):
            if self.touch_method == TOUCH_METHOD.MINITOUCH:
                self.minitouch.touch(pos, duration=duration)
            else:
                self.adb.touch(pos)

    def swipe(self, p1, p2, duration=0.5, steps=5):
        """
        Perform swipe event on the device

        Args:
            p1: start point
            p2: end point
            duration: how long to swipe the screen, default 0.5
            steps: how big is the swipe step, default 5

        Returns:
            None

        """
        p1 = self._touch_point_by_orientation(p1)
        p2 = self._touch_point_by_orientation(p2)
        if self.touch_method == TOUCH_METHOD.MINITOUCH:
            self.minitouch.swipe(p1, p2, duration=duration, steps=steps)
        else:
            duration *= 1000  # adb的swipe操作时间是以毫秒为单位的。
            self.adb.swipe(p1, p2, duration=duration)

    def pinch(self, *args, **kwargs):
        """
        Perform pinch event on the device

        Args:
            *args: optional arguments
            **kwargs: optional arguments

        Returns:
            None

        """
        return self.minitouch.pinch(*args, **kwargs)

    def logcat(self, *args, **kwargs):
        """
        Perform `logcat`operations
        Args:
            *args: optional arguments
            **kwargs: optional arguments

        Returns:
            `logcat` output

        """
        return self.adb.logcat(*args, **kwargs)

    def getprop(self, key, strip=True):
        """
        Get properties for given key

        Args:
            key: key name
            strip: True or False whether to strip the output or not

        Returns:
            property value(s)

        """
        return self.adb.getprop(key, strip)

    def get_ip_address(self):
        """
        Perform several set of commands to obtain the IP address
            * `adb shell netcfg | grep wlan0`
            * `adb shell ifconfig`
            * `adb getprop dhcp.wlan0.ipaddress`

        Returns:
            None if no IP address has been found, otherwise return the IP address

        """
        return self.adb.get_ip_address()

    def get_top_activity(self):
        """
        Get the top activity

        Returns:
            package, activity and pid

        """
        return self.adb.get_top_activity()

    def get_top_activity_name_and_pid(self):
        import re
        dat = self.adb.shell('dumpsys activity top')
        activityRE = re.compile('\s*ACTIVITY ([A-Za-z0-9_.]+)/([A-Za-z0-9_.]+) \w+ pid=(\d+)')
        m = activityRE.search(dat)
        if m:
            return (m.group(1), m.group(2), m.group(3))
        else:
            warnings.warn("NO MATCH:" + dat)
            return None

    def get_top_activity_name(self):
        """
        Get the top activity name

        Returns:
            package, activity and pid

        """
        tanp = self.get_top_activity_name_and_pid()
        if tanp:
            return tanp[0] + '/' + tanp[1]
        else:
            return None

    def is_keyboard_shown(self):
        """
        Return True or False whether soft keyboard is shown or not

        Notes:
            Might not work on all devices

        Returns:
            True or False

        """
        return self.adb.is_keyboard_shown()

    def is_screenon(self):
        """
        Return True or False whether the screen is on or not

        Notes:
            Might not work on all devices

        Returns:
            True or False

        """
        return self.adb.is_screenon()

    def is_locked(self):
        """
        Return True or False whether the device is locked or not

        Notes:
            Might not work on all devices

        Returns:
            True or False

        """
        return self.adb.is_locked()

    def unlock(self):
        """
        Unlock the device

        Notes:
            Might not work on all devices

        Returns:
            None

        """
        return self.adb.unlock()

    @property
    def display_info(self):
        """
        Return the display info (orientation, rotation and max values for x and y coordinates)

        Returns:
            display information

        """
        return self.adb.display_info

    def get_display_info(self):
        """
        Return the display physical info (orientation, rotation and max values for x and y coordinates)

        Returns:
            display physical information

        """
        return self.adb.get_display_info()

    def get_current_resolution(self):
        """
        Return current resolution after rotaion

        Returns:
            width and height of the display

        """
        # 注意黑边问题，需要用安卓接口获取区分两种分辨率
        w, h = self.display_info["width"], self.display_info["height"]
        if self.display_info["orientation"] in [1, 3]:
            w, h = h, w
        return w, h

    def start_recording(self, *args, **kwargs):
        """
        Start recording the device display

        Args:
            *args: optional arguments
            **kwargs:  optional arguments

        Returns:
            None

        """
        return self.recorder.start_recording(*args, **kwargs)

    def stop_recording(self, *args, **kwargs):
        """
        Stop recording the device display. Recoding file will be kept in the device.

        Args:
            *args: optional arguments
            **kwargs: optional arguments

        Returns:
            None

        """
        return self.recorder.stop_recording(*args, **kwargs)

    def _register_rotation_watcher(self):
        """
        Auto refresh `android.display` when rotation of screen has changed

        Returns:
            None

        """
        def refresh_ori(ori):
            self.display_info["orientation"] = ori
            self.display_info["rotation"] = ori * 90

        self.rotation_watcher.reg_callback(refresh_ori)
        self.rotation_watcher.reg_callback(lambda x: self.minicap.update_rotation(x * 90))

    def _touch_point_by_orientation(self, tuple_xy):
        """
        Convert image coordinates to physical display coordinates, the arbitrary point (origin) is upper left corner
        of the device physical display

        Args:
            tuple_xy: image coordinates (x, y)

        Returns:

        """
        x, y = tuple_xy
        x, y = XYTransformer.up_2_ori(
            (x, y),
            (self.display_info["physical_width"], self.display_info["physical_height"]),
            self.display_info["orientation"]
        )
        return x, y
