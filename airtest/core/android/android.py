#! /usr/bin/env python
# -*- coding: utf-8 -*-
import time
import warnings
from copy import copy
from airtest import aircv
from airtest.core.device import Device
from airtest.core.android.ime import YosemiteIme
from airtest.core.android.constant import CAP_METHOD, TOUCH_METHOD, IME_METHOD, ORI_METHOD, \
    SDK_VERISON_ANDROID10
from airtest.core.android.adb import ADB

from airtest.core.android.rotation import RotationWatcher, XYTransformer
from airtest.core.android.recorder import Recorder
from airtest.core.android.touch_methods.touch_proxy import TouchProxy
from airtest.core.error import AdbError, AdbShellError
from airtest.core.android.cap_methods.screen_proxy import ScreenProxy

# Compatible with old code
from airtest.core.android.cap_methods.minicap import Minicap  # noqa
from airtest.core.android.cap_methods.javacap import Javacap  # noqa
from airtest.core.android.touch_methods.minitouch import Minitouch  # noqa
from airtest.core.android.touch_methods.maxtouch import Maxtouch  # noqa


class Android(Device):
    """Android Device Class"""

    def __init__(self, serialno=None, host=None,
                 cap_method=CAP_METHOD.MINICAP,
                 touch_method=TOUCH_METHOD.MINITOUCH,
                 ime_method=IME_METHOD.YOSEMITEIME,
                 ori_method=ORI_METHOD.MINICAP,
                 display_id=None,
                 input_event=None):
        super(Android, self).__init__()
        self.serialno = serialno or self.get_default_device()
        self._cap_method = cap_method.upper()
        self._touch_method = touch_method.upper()
        self.ime_method = ime_method.upper()
        self.ori_method = ori_method.upper()
        self.display_id = display_id
        self.input_event = input_event
        # init adb
        self.adb = ADB(self.serialno, server_addr=host, display_id=self.display_id, input_event=self.input_event)
        self.adb.wait_for_device()
        self.sdk_version = self.adb.sdk_version
        if self.sdk_version >= SDK_VERISON_ANDROID10 and self._touch_method == TOUCH_METHOD.MINITOUCH:
            self._touch_method = TOUCH_METHOD.MAXTOUCH
        self._display_info = {}
        self._current_orientation = None
        # init components
        self.rotation_watcher = RotationWatcher(self.adb, self.ori_method)
        self.yosemite_ime = YosemiteIme(self.adb)
        self.recorder = Recorder(self.adb)
        self._register_rotation_watcher()

        self._touch_proxy = None
        self._screen_proxy = None

    @property
    def touch_proxy(self):
        """
        Perform touch operation according to self.touch_method

        Module: :py:mod:`airtest.core.android.touch_methods.touch_proxy.TouchProxy`

        Returns:
            TouchProxy

        Examples:
            >>> dev = Android()
            >>> dev.touch_proxy.touch((100, 100))  # If the device uses minitouch, it is the same as dev.minitouch.touch
            >>> dev.touch_proxy.swipe_along([(0,0), (100, 100)])
        """
        if self._touch_proxy:
            return self._touch_proxy
        self._touch_proxy = TouchProxy.auto_setup(self.adb,
                                                  default_method=self._touch_method,
                                                  ori_transformer=self._touch_point_by_orientation,
                                                  size_info=self.display_info,
                                                  input_event=self.input_event)
        return self._touch_proxy

    @property
    def touch_method(self):
        """
        In order to be compatible with the previous `dev.touch_method`

        为了兼容以前的`dev.touch_method`

        Returns:
            "MINITOUCH" or "MAXTOUCH"

        Examples:
            >>> dev = Android()
            >>> print(dev.touch_method)  # "MINITOUCH"

        """
        return self.touch_proxy.method_name

    @property
    def cap_method(self):
        """
        In order to be compatible with the previous `dev.cap_method`

        为了兼容以前的`dev.cap_method`

        Returns:
            "MINICAP" or "JAVACAP"

        Examples:
            >>> dev = Android()
            >>> print(dev.cap_method)  # "MINICAP"

        """
        return self.screen_proxy.method_name

    @cap_method.setter
    def cap_method(self, name):
        """
        Specify the screen capture method for the device, but this is not recommended
        为设备指定屏幕截图方案，但不建议这样做

        Just to be compatible with some old codes
        仅为了兼容一些旧的代码

        Args:
            name: "MINICAP" or Minicap() object

        Returns:
            None

        Examples:
            >>> dev = Android()
            >>> dev.cap_method = "MINICAP"

        """
        warnings.warn("No need to manually specify cap_method, airtest will automatically specify a suitable screenshot method, when airtest>=1.1.2")
        self.screen_proxy = name

    @property
    def screen_proxy(self):
        """
        Similar to touch_proxy, it returns a proxy that can automatically initialize an available screenshot method, such as Minicap

        Afterwards, you only need to call ``self.screen_proxy.get_frame()`` to get the screenshot

        类似touch_proxy，返回一个代理，能够自动初始化一个可用的屏幕截图方法，例如Minicap

        后续只需要调用 ``self.screen_proxy.get_frame()``即可获取到屏幕截图

        Returns: ScreenProxy(Minicap())

        Examples:
            >>> dev = Android()
            >>> img = dev.screen_proxy.get_frame_from_stream()  # dev.minicap.get_frame_from_stream() is deprecated

        """
        if self._screen_proxy:
            return self._screen_proxy
        self._screen_proxy = ScreenProxy.auto_setup(self.adb, default_method=self._cap_method,
                                                    rotation_watcher=self.rotation_watcher,
                                                    display_id=self.display_id,
                                                    ori_function=lambda: self.display_info)
        return self._screen_proxy

    @screen_proxy.setter
    def screen_proxy(self, cap_method):
        """
        Specify a screenshot method, if the method fails to initialize, try to use other methods instead

        指定一个截图方法，如果该方法初始化失败，则尝试使用其他方法代替

        Args:
            cap_method: "MINICAP" or :py:mod:`airtest.core.android.cap_methods.minicap.Minicap` object

        Returns:
            ScreenProxy object

        Raises:
            ScreenError when the connection fails

        Examples:
            >>> dev = Android()
            >>> dev.screen_proxy = "MINICAP"

            >>> from airtest.core.android.cap_methods.minicap import Minicap
            >>> minicap = Minicap(dev.adb, rotation_watcher=dev.rotation_watcher)
            >>> dev.screen_proxy = minicap

        """
        if self._screen_proxy:
            self._screen_proxy.teardown_stream()
        self._screen_proxy = ScreenProxy.auto_setup(self.adb, default_method=cap_method)

    def get_deprecated_var(self, old_name, new_name):
        """
        Get deprecated class variables

        When the airtest version number>=1.1.2, the call device.minicap/device.javacap is removed, and relevant compatibility is made here, and DeprecationWarning is printed

        airtest版本号>=1.1.2时，去掉了device.minicap/device.javacap这样的调用，在此做了相关的兼容，并打印DeprecationWarning

        Usage:  Android.minicap=property(lambda self: self.get_deprecated_var("minicap", "screen_proxy"))

        Args:
            old_name: "minicap"
            new_name: "screen_proxy"

        Returns:
            New implementation of deprecated object, e.g self.minicap -> self.screen_proxy

            dev.minicap.get_frame_from_stream()  ->  dev.screen_proxy.get_frame_from_stream()

        Examples:

            >>> dev = Android()
            >>> isinstance(dev.minicap, ScreenProxy)  # True
            >>> dev.minicap.get_frame_from_stream()  # --> dev.screen_proxy.get_frame_from_stream()

        """
        warnings.simplefilter("always")
        warnings.warn("{old_name} is deprecated, use {new_name} instead".format(old_name=old_name, new_name=new_name),
                      DeprecationWarning)
        return getattr(self, new_name)

    def get_default_device(self):
        """
        Get local default device when no serialno

        Returns:
            local device serialno

        """
        if not ADB().devices(state="device"):
            raise IndexError("ADB devices not found")
        return ADB().devices(state="device")[0][0]

    @property
    def uuid(self):
        """
        Serial number

        :return:
        """
        ult = [self.serialno]
        if self.display_id:
            ult.append(self.display_id)
        if self.input_event:
            ult.append(self.input_event)
        return "_".join(ult)

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
        Check if package exists on the device

        Args:
            package: package name

        Returns:
            True if package exists on the device

        Raises:
             AirtestError: raised if package is not found

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

    def start_app_timing(self, package, activity):
        """
        Start the application and activity, and measure time

        Args:
            package: package name
            activity: activity name

        Returns:
            app launch time

        """
        return self.adb.start_app_timing(package, activity)

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

    def install_app(self, filepath, replace=False, install_options=None):
        """
        Install the application on the device

        Args:
            filepath: full path to the `apk` file to be installed on the device
            replace: True or False to replace the existing application
            install_options: list of options, default is []

        Returns:
            output from installation process

        """
        return self.adb.install_app(filepath, replace=replace, install_options=install_options)

    def install_multiple_app(self, filepath, replace=False, install_options=None):
        """
        Install multiple the application on the device

        Args:
            filepath: full path to the `apk` file to be installed on the device
            replace: True or False to replace the existing application
            install_options: list of options, default is []

        Returns:
            output from installation process
        """
        return self.adb.install_multiple_app(filepath, replace=replace, install_options=install_options)

    def uninstall_app(self, package):
        """
        Uninstall the application from the device

        Args:
            package: package name

        Returns:
            output from the uninstallation process

        """
        return self.adb.uninstall_app(package)

    def snapshot(self, filename=None, ensure_orientation=True, quality=10, max_size=None):
        """
        Take the screenshot of the display. The output is send to stdout by default.

        Args:
            filename: name of the file where to store the screenshot, default is None which is stdout
            ensure_orientation: True or False whether to keep the orientation same as display
            quality: The image quality, integer in range [1, 99]
            max_size: the maximum size of the picture, e.g 1200

        Returns:
            screenshot output

        """
        # default not write into file.
        screen = self.screen_proxy.snapshot(ensure_orientation=ensure_orientation)
        if filename:
            aircv.imwrite(filename, screen, quality, max_size=max_size)
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
            keyname: keyevent name
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
        time.sleep(0.5)
        self.home()

    def home(self):
        """
        Press HOME button

        Returns:
            None

        """
        self.keyevent("HOME")

    def text(self, text, enter=True, **kwargs):
        """
        Input text on the device

        Args:
            text: text to input
            enter: True or False whether to press `Enter` key
            search: True or False whether to press `Search` key on IME after input

        Returns:
            None

        """
        search = False if "search" not in kwargs else kwargs["search"]

        if self.ime_method == IME_METHOD.YOSEMITEIME:
            self.yosemite_ime.text(text)
        else:
            self.adb.shell(["input", "text", text])

        if search:
            self.yosemite_ime.code("3")
            return

        # 游戏输入时，输入有效内容后点击Enter确认，如不需要，enter置为False即可。
        if enter:
            self.adb.shell(["input", "keyevent", "ENTER"])

    def touch(self, pos, duration=0.01):
        """
        Perform touch event on the device

        Args:
            pos: coordinates (x, y)
            duration: how long to touch the screen

        Returns:
            None

        """
        self.touch_proxy.touch(pos, duration)

    def double_click(self, pos):
        self.touch(pos)
        time.sleep(0.05)
        self.touch(pos)

    def swipe(self, p1, p2, duration=0.5, steps=5, fingers=1):
        """
        Perform swipe event on the device

        Args:
            p1: start point
            p2: end point
            duration: how long to swipe the screen, default 0.5
            steps: how big is the swipe step, default 5
            fingers: the number of fingers. 1 or 2.

        Returns:
            None

        """
        self.touch_proxy.swipe(p1, p2, duration=duration, steps=steps, fingers=fingers)

    def pinch(self, center=None, percent=0.5, duration=0.5, steps=5, in_or_out='in'):
        """
        Perform pinch event on the device, only for minitouch and maxtouch

        Args:
            center: the center point of the pinch operation
            percent: pinch distance to half of screen, default is 0.5
            duration: time interval for swipe duration, default is 0.8
            steps: size of swipe step, default is 5
            in_or_out: pinch in or pinch out, default is 'in'

        Returns:
            None

        Raises:
            TypeError: An error occurred when center is not a list/tuple or None

        """
        self.touch_proxy.pinch(center=center, percent=percent, duration=duration, steps=steps, in_or_out=in_or_out)

    def swipe_along(self, coordinates_list, duration=0.8, steps=5):
        """
        Perform swipe event across multiple points in sequence, only for minitouch and maxtouch

        Args:
            coordinates_list: list of coordinates: [(x1, y1), (x2, y2), (x3, y3)]
            duration: time interval for swipe duration, default is 0.8
            steps: size of swipe step, default is 5

        Returns:
            None

        """
        self.touch_proxy.swipe_along(coordinates_list, duration=duration, steps=steps)

    def two_finger_swipe(self, tuple_from_xy, tuple_to_xy, duration=0.8, steps=5, offset=(0, 50)):
        """
        Perform two finger swipe action, only for minitouch and maxtouch

        Args:
            tuple_from_xy: start point
            tuple_to_xy: end point
            duration: time interval for swipe duration, default is 0.8
            steps: size of swipe step, default is 5
            offset: coordinate offset of the second finger, default is (0, 50)

        Returns:
            None
        """
        self.touch_proxy.two_finger_swipe(tuple_from_xy, tuple_to_xy, duration=duration, steps=steps, offset=offset)

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
            (package, activity, pid)

        """
        return self.adb.get_top_activity()

    def get_top_activity_name(self):
        """
        Get the top activity name

        Returns:
            (package, activity, pid)

        """
        tanp = self.get_top_activity()
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
            Might not work on some devices

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
        Return the display info (width, height, orientation and max_x, max_y)

        Returns:
            display information

        """
        if not self._display_info:
            self._display_info = self.get_display_info()
        display_info = copy(self._display_info)
        # update ow orientation, which is more accurate
        if self._current_orientation is not None:
            display_info.update({
                "rotation": self._current_orientation * 90,
                "orientation": self._current_orientation,
            })
        return display_info

    def get_display_info(self):
        """
        Return the display info (width, height, orientation and max_x, max_y)

        Returns:
            display information

        """
        self.rotation_watcher.get_ready()
        return self.adb.get_display_info()

    def get_current_resolution(self):
        """
        Return current resolution after rotation

        Returns:
            width and height of the display

        """
        # 注意黑边问题，需要用安卓接口获取区分两种分辨率
        w, h = self.display_info["width"], self.display_info["height"]
        if self.display_info["orientation"] in [1, 3]:
            w, h = h, w
        return w, h

    def get_render_resolution(self, refresh=False):
        """
        Return render resolution after rotation

        Args:
            refresh: whether to force refresh render resolution

        Returns:
            offset_x, offset_y, offset_width and offset_height of the display

        """
        if refresh or 'offset_x' not in self._display_info:
            self.adjust_all_screen()
        x, y, w, h = self._display_info.get('offset_x', 0), \
            self._display_info.get('offset_y', 0), \
            self._display_info.get('offset_width', 0), \
            self._display_info.get('offset_height', 0)
        if self.display_info["orientation"] in [1, 3]:
            x, y, w, h = y, x, h, w
        return x, y, w, h

    def start_recording(self, max_time=1800, bit_rate_level=1, bit_rate=None):
        """
        Start recording the device display

        Args:
            max_time: maximum screen recording time, default is 1800
            bit_rate_level: bit_rate=resolution*level, 0 < level <= 5, default is 1
            bit_rate: the higher the bitrate, the clearer the video

        Returns:
            None

        Examples:

            Record 30 seconds of video and export to the current directory test.mp4::

            >>> from airtest.core.api import connect_device, sleep
            >>> dev = connect_device("Android:///")
            >>> # Record the screen with the lowest quality
            >>> dev.start_recording(bit_rate_level=1)
            >>> sleep(30)
            >>> dev.stop_recording(output="test.mp4")

            Or set max_time=30, the screen recording will stop automatically after 30 seconds::

            >>> dev.start_recording(max_time=30, bit_rate_level=5)
            >>> dev.stop_recording(output="test_30s.mp4")

            The default value of `max_time` is 1800 seconds, so the maximum screen recording time is half an hour.
            You can modify its value to obtain a longer screen recording::

            >>> dev.start_recording(max_time=3600, bit_rate_level=5)
            >>> dev.stop_recording(output="test_hour.mp4")

        """
        if not bit_rate:
            if bit_rate_level > 5:
                bit_rate_level = 5
            bit_rate = self.display_info['width'] * self.display_info['height'] * bit_rate_level
        return self.recorder.start_recording(max_time=max_time, bit_rate=bit_rate)

    def stop_recording(self, output="screen.mp4", is_interrupted=False):
        """
        Stop recording the device display. Recoding file will be kept in the device.

        Args:
            output: default file is `screen.mp4`
            is_interrupted: True or False. Stop only, no pulling recorded file from device.

        Returns:
            None

        """
        return self.recorder.stop_recording(output=output, is_interrupted=is_interrupted)

    def _register_rotation_watcher(self):
        """
        Register callbacks for Android and minicap when rotation of screen has changed

        callback is called in another thread, so be careful about thread-safety

        Returns:
            None

        """
        self.rotation_watcher.reg_callback(lambda x: setattr(self, "_current_orientation", x))

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
            (self.display_info["width"], self.display_info["height"]),
            self.display_info["orientation"]
        )
        return x, y

    def adjust_all_screen(self):
        """
        Adjust the render resolution for all_screen device.

        Return:
            None

        """
        info = self.display_info
        ret = self.adb.get_display_of_all_screen(info)
        if ret:
            info.update(ret)
            self._display_info = info

# Compatible with old code, such as device.minicap
Android.minicap=property(lambda self: self.get_deprecated_var("minicap", "screen_proxy"))
Android.javacap=property(lambda self: self.get_deprecated_var("javacap", "screen_proxy"))
Android.minitouch=property(lambda self: self.get_deprecated_var("minitouch", "touch_proxy"))
Android.maxtouch=property(lambda self: self.get_deprecated_var("maxtouch", "touch_proxy"))