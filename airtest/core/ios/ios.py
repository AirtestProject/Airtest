#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time
import base64
import traceback
import wda
import inspect
from functools import wraps
from airtest import aircv
from airtest.core.device import Device
from airtest.core.ios.constant import CAP_METHOD, TOUCH_METHOD, IME_METHOD, ROTATION_MODE, KEY_EVENTS, \
    LANDSCAPE_PAD_RESOLUTION, IP_PATTERN
from airtest.core.ios.rotation import XYTransformer, RotationWatcher
from airtest.core.ios.instruct_cmd import InstructHelper
from airtest.utils.logger import get_logger
from airtest.core.ios.mjpeg_cap import MJpegcap

LOGGING = get_logger(__name__)

DEFAULT_ADDR = "http://localhost:8100/"


def decorator_retry_session(func):
    """
    When the operation fails due to session failure, try to re-acquire the session,
    retry at most 3 times

    当因为session失效而操作失败时，尝试重新获取session，最多重试3次
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (RuntimeError, wda.WDAError):
            for i in range(3):
                try:
                    self._fetch_new_session()
                    return func(self, *args, **kwargs)
                except:
                    time.sleep(0.5)
                    continue
            raise

    return wrapper


def decorator_retry_for_class(cls):
    """
    Add decorators to all methods in the class

    为class里的所有method添加装饰器 ``decorator_retry_session``
    """
    for name, method in inspect.getmembers(cls):
        # Ignore built-in methods and private methods named _xxx
        # 忽略内置方法和下划线开头命名的私有方法 _xxx
        if (not inspect.ismethod(method) and not inspect.isfunction(method)) \
                or inspect.isbuiltin(method) or name.startswith("_"):
            continue
        setattr(cls, name, decorator_retry_session(method))
    return cls


@decorator_retry_for_class
class IOS(Device):
    """ios client

        - before this you have to run `WebDriverAgent <https://github.com/AirtestProject/iOS-Tagent>`_

        - ``xcodebuild -project path/to/WebDriverAgent.xcodeproj -scheme WebDriverAgentRunner -destination "id=$(idevice_id -l)" test``

        - ``iproxy $port 8100 $udid``
    """

    def __init__(self, addr=DEFAULT_ADDR, cap_method=CAP_METHOD.MJPEG, mjpeg_port=None):
        super(IOS, self).__init__()

        # if none or empty, use default addr
        self.addr = addr or DEFAULT_ADDR

        # fit wda format, make url start with http://
        # eg. http://localhost:8100/ or http+usbmux://00008020-001270842E88002E
        # with mjpeg_port: http://localhost:8100/?mjpeg_port=9100
        if not self.addr.startswith("http"):
            self.addr = "http://" + addr

        """here now use these supported cap touch and ime method"""
        self.cap_method = cap_method
        self.touch_method = TOUCH_METHOD.WDATOUCH
        self.ime_method = IME_METHOD.WDAIME

        # wda driver, use to home, start app
        # init wda session, updata when start app
        # use to click/swipe/close app/get wda size
        wda.DEBUG = False
        self.driver = wda.Client(self.addr)

        # record device's width
        self._size = {'width': None, 'height': None}
        self._current_orientation = None
        self._touch_factor = None
        self._last_orientation = None
        self._is_pad = None
        self._using_ios_tagent = None
        self._device_info = {}

        info = self.device_info
        self.instruct_helper = InstructHelper(info['uuid'])
        self.mjpegcap = MJpegcap(self.instruct_helper, ori_function=lambda: self.display_info,
                                 ip=self.ip, port=mjpeg_port)
        # start up RotationWatcher with default session
        self.rotation_watcher = RotationWatcher(self)
        self._register_rotation_watcher()

        self.alert_watch_and_click = self.driver.alert.watch_and_click

    @property
    def ip(self):
        """
        Returns the IP address of the host connected to the iOS phone
        It is not the IP address of the iOS phone.
        If you want to get the IP address of the phone, you can access the interface `get_ip_address`

        For example: when the device is connected via http://localhost:8100, return localhost
        If it is a remote device http://192.168.xx.xx:8100, it returns the IP address of 192.168.xx.xx

        Returns:

        """
        match = re.search(IP_PATTERN, self.addr)
        if match:
            ip = match.group(0)
        else:
            ip = 'localhost'
        return ip

    @property
    def uuid(self):
        return self.addr

    @property
    def using_ios_tagent(self):
        """
        当前基础版本：appium/WebDriverAgent 4.1.4
        基于上述版本，2022.3.30之后发布的iOS-Tagent版本，在/status接口中新增了一个Version参数，如果能检查到本参数，说明使用了新版本ios-Tagent
        该版本基于Appium版的WDA做了一些改动，可以更快地进行点击和滑动，并优化了部分UI树的获取逻辑
        但是所有的坐标都为竖屏坐标，需要airtest自行根据方向做转换
        同时，大于4.1.4版本的appium/WebDriverAgent不再需要针对ipad进行特殊的横屏坐标处理了
        Returns:

        """
        if self._using_ios_tagent is None:
            status = self.driver.status()
            if 'Version' in status:
                self._using_ios_tagent = True
            else:
                self._using_ios_tagent = False
        return self._using_ios_tagent

    def _fetch_new_session(self):
        """
        Re-acquire a new session
        重新获取新的session
        :return:
        """
        # 根据facebook-wda的逻辑，直接设为None就会自动获取一个新的默认session
        self.driver.session_id = None

    @property
    def is_pad(self):
        """
        Determine whether it is an ipad(or 6P/7P/8P), if it is, in the case of horizontal screen + desktop,
        the coordinates need to be switched to vertical screen coordinates to click correctly (WDA bug)

        判断是否是ipad(或 6P/7P/8P)，如果是，在横屏+桌面的情况下，坐标需要切换成竖屏坐标才能正确点击（WDA的bug）
        Returns:

        """
        if self._is_pad is None:
            info = self.device_info
            if info["model"] == "iPad" or \
                    (self.display_info["width"], self.display_info["height"]) in LANDSCAPE_PAD_RESOLUTION:
                # ipad与6P/7P/8P等设备，桌面横屏时的表现一样，都会变横屏
                self._is_pad = True
            else:
                self._is_pad = False
        return self._is_pad

    @property
    def device_info(self):
        """
        get the device info.

        .. note::
            Might not work on all devices

        Returns:
            dict for device info,
            eg. AttrDict({
                'timeZone': 'GMT+0800',
                'currentLocale': 'zh_CN',
                'model': 'iPhone',
                'uuid': '90CD6AB7-11C7-4E52-B2D3-61FA31D791EC',
                'userInterfaceIdiom': 0,
                'userInterfaceStyle': 'light',
                'name': 'iPhone',
                'isSimulator': False})
        """
        if not self._device_info:
            self._device_info = self.driver.info
        return self._device_info

    def _register_rotation_watcher(self):
        """
        Register callbacks for Android and minicap when rotation of screen has changed

        callback is called in another thread, so be careful about thread-safety

        Returns:
            None

        """
        self.rotation_watcher.reg_callback(lambda x: setattr(self, "_current_orientation", x))

    def window_size(self):
        """
            return window size
            namedtuple:
                Size(width , height)
        """
        try:
            return self.driver.window_size()
        except wda.exceptions.WDAStaleElementReferenceError:
            print("iOS connection failed, please try pressing the home button to return to the desktop and try again.")
            print("iOS连接失败，请尝试按home键回到桌面后再重试")
            raise

    @property
    def orientation(self):
        """
            return device oritantation status
            in  LANDSACPE POR
        """
        if not self._current_orientation:
            self._current_orientation = self.get_orientation()
        return self._current_orientation

    @orientation.setter
    def orientation(self, value):
        """

        Args:
            value(string): LANDSCAPE | PORTRAIT | UIA_DEVICE_ORIENTATION_LANDSCAPERIGHT |
                    UIA_DEVICE_ORIENTATION_PORTRAIT_UPSIDEDOWN

        Returns:

        """
        # 可以对屏幕进行旋转，但是可能会导致问题
        self.driver.orientation = value

    def get_orientation(self):
        # self.driver.orientation只能拿到LANDSCAPE，不能拿到左转/右转的确切方向
        # 因此手动调用/rotation获取屏幕实际方向
        rotation = self.driver._session_http.get('/rotation')
        # rotation dict eg. {'value': {'x': 0, 'y': 0, 'z': 90}, 'sessionId': 'xx', 'status': 0}
        if rotation:
            return ROTATION_MODE.get(rotation['value']['z'], wda.PORTRAIT)

    @property
    def display_info(self):
        if not self._size['width'] or not self._size['height']:
            self._display_info()

        self._size['orientation'] = self.orientation
        return self._size

    def _display_info(self):
        # function window_size() return UIKit size, While screenshot() image size is Native Resolution
        window_size = self.window_size()
        # when use screenshot, the image size is pixels size. eg(1080 x 1920)
        snapshot = self.snapshot()
        if self.orientation in [wda.LANDSCAPE, wda.LANDSCAPE_RIGHT]:
            self._size['window_width'], self._size['window_height'] = window_size.height, window_size.width
            width, height = snapshot.shape[:2]
        else:
            self._size['window_width'], self._size['window_height'] = window_size.width, window_size.height
            height, width = snapshot.shape[:2]
        self._size["width"] = width
        self._size["height"] = height

        # use session.scale can get UIKit scale factor
        # so self._touch_factor = 1 / self.driver.scale, but the result is incorrect on some devices(6P/7P/8P)
        self._touch_factor = float(self._size['window_height']) / float(height)
        self.rotation_watcher.get_ready()

        # 当前版本: wda 4.1.4 获取到的/window/size，在ipad+桌面横屏下拿到的是 height * height，需要修正
        if self.is_pad and self.home_interface():
            self._size['window_width'] = int(width * self._touch_factor)

    @property
    def touch_factor(self):
        if not self._touch_factor:
            self._display_info()
        return self._touch_factor

    @touch_factor.setter
    def touch_factor(self, factor):
        """
        touch_factor is used to convert click coordinates: mobile phone real coordinates = touch_factor * screen coordinates
        In general, no manual settings are required

        touch_factor用于换算点击坐标：手机真实坐标 = touch_factor * 屏幕坐标
        默认计算方式是： self.display_info['window_height'] / self.display_info['height']
        但在部分特殊型号手机上可能不准确，例如iOS14.4的7P，默认值为 1/3，但部分7P点击位置不准确，可自行设置为：self.touch_factor = 1 / 3.3
        （一般情况下，无需手动设置！）

        Examples:
            >>> device = connect_device("iOS:///")
            >>> device.touch((100, 100))  # wrong position
            >>> print(device.touch_factor)
            0.333333
            >>> device.touch_factor = 1 / 3.3  # default is 1/3
            >>> device.touch((100, 100))
        Args:
            factor: real_pos / pixel_pos, e.g: 1/self.driver.scale

        Returns:

        """
        self._touch_factor = float(factor)

    def get_render_resolution(self):
        """
        Return render resolution after rotation

        Returns:
            offset_x, offset_y, offset_width and offset_height of the display

        """
        w, h = self.get_current_resolution()
        return 0, 0, w, h

    def get_current_resolution(self):
        w, h = self.display_info["width"], self.display_info["height"]
        if self.display_info["orientation"] in [wda.LANDSCAPE, wda.LANDSCAPE_RIGHT]:
            w, h = h, w
        return w, h

    def home(self):
        # press("home") faster than home()
        return self.driver.press("home")

    def _neo_wda_screenshot(self):
        """
            this is almost same as wda implementation, but without png header check,
            as response data is now jpg format in mid quality
        """
        value = self.driver.http.get('screenshot').value
        raw_value = base64.b64decode(value)
        return raw_value

    def snapshot(self, filename=None, quality=10, max_size=None):
        """
        take snapshot

        Args:
            filename: save screenshot to filename
            quality: The image quality, integer in range [1, 99]
            max_size: the maximum size of the picture, e.g 1200

        Returns:

        """
        data = self._neo_wda_screenshot()
        # output cv2 object
        try:
            screen = aircv.utils.string_2_img(data)
        except:
            # may be black/locked screen or other reason, print exc for debugging
            traceback.print_exc()
            return None

        # save as file if needed
        if filename:
            aircv.imwrite(filename, screen, quality, max_size=max_size)

        return screen

    def get_frame_from_stream(self):
        if self.cap_method == CAP_METHOD.MJPEG:
            try:
                return self.mjpegcap.get_frame_from_stream()
            except ConnectionRefusedError:
                self.cap_method = CAP_METHOD.WDACAP
        return self._neo_wda_screenshot()

    def touch(self, pos, duration=0.01):
        """

        Args:
            pos: coordinates (x, y), can be float(percent) or int
            duration (optional): tap_hold duration

        Returns: None

        Examples:
            >>> touch((100, 100))
            >>> touch((0.5, 0.5), duration=1)

        """
        # trans pos of click, pos can be percentage or real coordinate
        x, y = self._transform_xy(pos)
        self.driver.click(x, y, duration)

    def double_click(self, pos):
        x, y = self._transform_xy(pos)
        self.driver.double_tap(x, y)

    def swipe(self, fpos, tpos, duration=0, *args, **kwargs):
        """

        Args:
            fpos: start point
            tpos: end point
            duration (float): start coordinate press duration (seconds), default is 0

        Returns:
            None

        Examples:
            >>> swipe((1050, 1900), (150, 1900))
            >>> swipe((0.2, 0.5), (0.8, 0.5))

        """
        fx, fy = self._transform_xy(fpos)
        tx, ty = self._transform_xy(tpos)
        self.driver.swipe(fx, fy, tx, ty, duration)

    def keyevent(self, keyname, **kwargs):
        """
        Perform keyevent on the device

        Args:
            keyname: home/volumeUp/volumeDown
            **kwargs:

        Returns:

        """
        try:
            keyname = KEY_EVENTS[keyname.lower()]
        except KeyError:
            raise ValueError("Invalid name: %s, should be one of ('home', 'volumeUp', 'volumeDown')" % keyname)
        else:
            self.press(keyname)

    def press(self, keys):
        """some keys in ["home", "volumeUp", "volumeDown"] can be pressed"""
        self.driver.press(keys)

    def text(self, text, enter=True):
        """
        Input text on the device
        Args:
            text:  text to input
            enter: True if you need to enter a newline at the end

        Returns:
            None

        Examples:
            >>> text("test")
            >>> text("中文")
        """
        if enter:
            text += '\n'
        self.driver.send_keys(text)

    def install_app(self, uri, package):
        """
        curl -X POST $JSON_HEADER \
        -d "{\"desiredCapabilities\":{\"bundleId\":\"com.apple.mobilesafari\", \"app\":\"[host_path]/magicapp.app\"}}" \
        $DEVICE_URL/session
        https://github.com/facebook/WebDriverAgent/wiki/Queries
        """
        raise NotImplementedError

    def start_app(self, package, *args):
        """

        Args:
            package: the app bundle id, e.g ``com.apple.mobilesafari``

        Returns:
            None

        Examples:
            >>> start_app('com.apple.mobilesafari')

        """
        self.driver.app_launch(bundle_id=package)

    def stop_app(self, package):
        """

        Args:
            package: the app bundle id, e.g ``com.apple.mobilesafari``

        Returns:

        """
        self.driver.app_stop(bundle_id=package)

    def app_state(self, package):
        """

        Args:
            package:

        Returns:
            {
                "value": 4,
                "sessionId": "0363BDC5-4335-47ED-A54E-F7CCB65C6A65"
            }

            value 1(not running) 2(running in background) 3(running in foreground)? 4(running)

        Examples:
            >>> dev = device()
            >>> start_app('com.apple.mobilesafari')
            >>> print(dev.app_state('com.apple.mobilesafari')["value"])  # --> output is 4
            >>> home()
            >>> print(dev.app_state('com.apple.mobilesafari')["value"])  # --> output is 3
            >>> stop_app('com.apple.mobilesafari')
            >>> print(dev.app_state('com.apple.mobilesafari')["value"])  # --> output is 1
        """
        # output {"value": 4, "sessionId": "xxxxxx"}
        # different value means 1: die, 2: background, 4: running
        return self.driver.app_state(bundle_id=package)

    def app_current(self):
        """
        get the app current 

        Notes:
            Might not work on all devices

        Returns:
            current app state dict, eg:
            {"pid": 1281,
             "name": "",
             "bundleId": "com.netease.cloudmusic"}

        """
        return self.driver.app_current()

    def get_ip_address(self):
        """
        get ip address from webDriverAgent

        Returns:
            raise if no IP address has been found, otherwise return the IP address

        """
        return self.driver.status()['ios']['ip']

    def device_status(self):
        """
        show status return by webDriverAgent
        Return dicts of infos
        """
        return self.driver.status()

    def _touch_point_by_orientation(self, tuple_xy):
        """
        Convert image coordinates to physical display coordinates, the arbitrary point (origin) is upper left corner
        of the device physical display

        Args:
            tuple_xy: image coordinates (x, y)

        Returns:

        """
        x, y = tuple_xy

        # 1. 如果使用了2022.03.30之后发布的iOS-Tagent版本，则必须要进行竖屏坐标转换
        # 2. 如果使用了appium/WebDriverAgent>=4.1.4版本，直接使用原坐标即可，无需转换
        # 3. 如果使用了appium/WebDriverAgent<4.1.4版本，或低版本的iOS-Tagent，并且ipad下横屏点击异常，请改用airtest<=1.2.4
        if self.using_ios_tagent:
            width = self.display_info["width"]
            height = self.display_info["height"]
            if self.orientation in [wda.LANDSCAPE, wda.LANDSCAPE_RIGHT]:
                width, height = height, width
            if x < 1 and y < 1:
                x = x * width
                y = y * height
            x, y = XYTransformer.up_2_ori(
                (x, y),
                (width, height),
                self.orientation
            )
        return x, y

    def _transform_xy(self, pos):
        x, y = self._touch_point_by_orientation(pos)

        # scale touch postion
        if not (x < 1 and y < 1):
            x, y = int(x * self.touch_factor), int(y * self.touch_factor)

        return x, y

    def _check_orientation_change(self):
        pass

    def is_locked(self):
        """
        Return True or False whether the device is locked or not

        Notes:
            Might not work on some devices

        Returns:
            True or False

        """
        return self.driver.locked()

    def unlock(self):
        """
        Unlock the device, unlock screen, double press home 

        Notes:
            Might not work on all devices

        Returns:
            None

        """
        return self.driver.unlock()

    def lock(self):
        """
        lock the device, lock screen 

        Notes:
            Might not work on all devices

        Returns:
            None

        """
        return self.driver.lock()

    def alert_accept(self):
        """
        Alert accept-Actually do click first alert button

        Notes:
            Might not work on all devices

        Returns:
            None

        """
        return self.driver.alert.accept()

    def alert_dismiss(self):
        """
        Alert dissmiss-Actually do click second alert button

        Notes:
            Might not work on all devices

        Returns:
            None

        """
        return self.driver.alert.dismiss()

    def alert_wait(self, time_counter=2):
        """
        if alert apper in time_counter second it will return True,else return False (default 20.0)
        time_counter default is 2 seconds

        Notes:
            Might not work on all devices

        Returns:
            None

        """
        return self.driver.alert.wait(time_counter)

    def alert_buttons(self):
        """
        get alert buttons text. 
        Notes:
            Might not work on all devices

        Returns:
             # example return: ("设置", "好")

        """
        return self.driver.alert.buttons()

    def alert_exists(self):
        """
        get True for alert exists or False.

        Notes:
            Might not work on all devices

        Returns:
            True or False

        """
        return self.driver.alert.exists

    def alert_click(self, buttons):
        """
        when Arg type is list, click the first match, raise ValueError if no match

        eg. ["设置", "信任", "安装"]

        Notes:
            Might not work on all devices

        Returns:
            None

        """
        return self.driver.alert.click(buttons)

    def home_interface(self):
        """
        get True for the device status is on home interface. 

        Reason:
            some devices can Horizontal screen on the home interface

        Notes:
            Might not work on all devices

        Returns:
            True or False

        """
        try:
            app_current_dict = self.app_current()
            app_current_bundleId = app_current_dict.get('bundleId')
            LOGGING.info("app_current_bundleId %s", app_current_bundleId)
        except:
            return False
        else:
            if app_current_bundleId in ['com.apple.springboard']:
                return True
        return False

    def disconnect(self):
        """
        discconect mjpeg and rotation_watcher

        Returns: None

        """
        if self.cap_method == CAP_METHOD.MJPEG:
            self.mjpegcap.teardown_stream()
        if self.rotation_watcher:
            self.rotation_watcher.teardown()


if __name__ == "__main__":
    start = time.time()
    ios = IOS("http://10.251.100.86:20003")

    ios.snapshot()
    # ios.touch((242 * 2 + 10, 484 * 2 + 20))

    # ios.start_app("com.tencent.xin")
    ios.home()
    ios.start_app('com.apple.mobilesafari')
    ios.touch((88, 88))
    ios.stop_app('com.apple.mobilesafari')
    ios.swipe((100, 100), (800, 100))

    print(ios.device_status())
    print(ios.get_ip_address())
