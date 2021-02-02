#! /usr/bin/env python
# -*- coding: utf-8 -*-

import time
import base64
import traceback
import wda
import inspect
from functools import wraps
from airtest import aircv
from airtest.core.device import Device
from airtest.core.ios.constant import CAP_METHOD, TOUCH_METHOD, IME_METHOD
from airtest.core.ios.rotation import XYTransformer, RotationWatcher
from airtest.utils.logger import get_logger


LOGGING = get_logger(__name__)

DEFAULT_ADDR = "http://localhost:8100/"

ROTATION_MODE = {
    0: PORTRAIT,
    270: LANDSCAPE,
    90: LANDSCAPE_RIGHT,
    180: PORTRAIT_UPSIDEDOWN
}

KEYS_EVENTS = {
    'home': 'home',
    'volumeup': 'volumeUp',
    'volumedown': 'volumeDown'
}

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
            tries = 3
            while tries > 0:
                try:
                    self._fetch_new_session()
                except:
                    if tries == 1:
                        raise
                    tries -= 1
                    continue
                else:
                    break
            return func(self, *args, **kwargs)
    return wrapper


def decorator_retry_for_class(cls):
    """
    Add decorators to all methods in the class
    为class里的所有method添加装饰器decorator_retry_session
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

    def __init__(self, addr=DEFAULT_ADDR):
        super(IOS, self).__init__()

        # if none or empty, use default addr
        LOGGING.info("Using default ios devices")
        self.addr = addr or DEFAULT_ADDR

        # fit wda format, make url start with http://
        if not self.addr.startswith("http://"):
            self.addr = "http://" + addr

        """here now use these supported cap touch and ime method"""
        self.cap_method = CAP_METHOD.WDACAP
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
        self.defaultSession = None

        # start up RotationWatcher with default session
        self.rotation_watcher = RotationWatcher(self)
        self._register_rotation_watcher()

        self.alert_watch_and_click = self.driver.alert.watch_and_click

        # helper of run process like iproxy
        # self.instruct_helper = InstructHelper()

    @property
    def uuid(self):
        return self.addr

    @property
    def session(self):
        if not self.defaultSession:
            self.defaultSession = self.driver.session()
        return self.defaultSession

    def _fetch_new_session(self):
        """
        Re-acquire a new session, will not automatically retry
        重新获取新的session，不会自动重试
        :return:
        """
        self.defaultSession = self.driver.session()

    @property
    def is_pad(self):
        """
        Determine whether it is an ipad, if it is, in the case of horizontal screen + desktop,
        the coordinates need to be switched to vertical screen coordinates to click correctly (WDA bug)
        判断是否是ipad，如果是，在横屏+桌面的情况下，坐标需要切换成竖屏坐标才能正确点击（WDA的bug）
        Returns:

        """
        if self._is_pad is None:
            info = self.driver.device_info()
            self._is_pad = info["model"] == "iPad"
        return self._is_pad

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
                Size(wide , hight)
        """

        window_size = self.session.window_size()
        return window_size

    # @property
    # @retry_session
    # def orientation(self):
    #     """
    #         return device oritantation status
    #         in  LANDSACPE POR
    #     """
    #     return self.session.orientation

    @property
    def orientation(self):
        """
            return device oritantation status
            in  LANDSACPE POR
        """
        if not self._current_orientation:
            z = self.driver._session_http.get('rotation').value.get('z')
            self._current_orientation = ROTATION_MODE(z).name
        return self._current_orientation

    @property
    def display_info(self):
        if not self._size['width'] or not self._size['height']:
            self._display_info()

        return {'width': self._size['width'], 'height': self._size['height'], 'orientation': self.orientation,
                'physical_width': self._size['width'], 'physical_height': self._size['height']}

    def _display_info(self):
        window_size = self.window_size()
        scale = self.driver.scale
        self._size['width'] = scale * window_size.width
        self._size['height'] = scale * window_size.height
        self._touch_factor = 1 / scale

    @property
    def touch_factor(self):
        if not self._touch_factor:
            self._display_info()
        return self._touch_factor

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
        if self.display_info["orientation"] in [ROTATION_MODE.LANDSCAPE.name,
                                                ROTATION_MODE.UIA_DEVICE_ORIENTATION_LANDSCAPERIGHT.name]:
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

    def snapshot(self, filename=None, strType=False, quality=10, max_size=None):
        """
        take snapshot

        Args:
            filename: save screenshot to filename
            quality: The image quality, integer in range [1, 99]
            max_size: the maximum size of the picture, e.g 1200

        Returns:
            display the screenshot

        """
        data = None

        # 暂时只有一种截图方法, WDACAP
        if self.cap_method == CAP_METHOD.WDACAP:
            data = self._neo_wda_screenshot()  # wda 截图不用考虑朝向

        # 实时刷新手机画面，直接返回base64格式，旋转问题交给IDE处理
        if strType:
            if filename:
                with open(filename, 'wb') as f:
                    f.write(data)
            return data

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
        LOGGING.info("touch original-postion at (%s, %s)", pos[0], pos[1])
        x, y = self._transform_xy(pos)

        LOGGING.info("touch last-postion at (%s, %s)", x, y)
        self.session.click(x, y, duration)

    def double_click(self, pos):
        x, y = self._transform_xy(pos)
        self.session.double_tap(x, y)

    def swipe(self, fpos, tpos, duration=0, *args):
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

        LOGGING.info("swipe postion1 (%s, %s) to postion2 (%s, %s), for duration: %s", fx, fy, tx, ty, duration)
        self.session.swipe(fx, fy, tx, ty, duration)

    def keyevent(self, keyname, **kwargs):
        """
        Perform keyevent on the device

        Args:
            keyname: home/volumeUp/volumeDown
            **kwargs:

        Returns:

        """
        try:
            keyname = KEY_EVENTS(keyname.lower()).name
        except KeyError:
            raise ValueError("Invalid name: %s, should be one of ('home', 'volumeUp', 'volumeDown')" % keyname)
        else:
            self.press(keyname)

    def press(self, keys):
        """some keys in ["home", "volumeUp", "volumeDown"] can be pressed"""
        self.session.press(keys)

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
        self.session.send_keys(text)

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

        # 部分设备如ipad，在横屏+桌面的情况下，点击坐标依然需要按照竖屏坐标额外做一次旋转处理
        if self.is_pad and self.orientation in [ROTATION_MODE.LANDSCAPE.name, ROTATION_MODE.LANDSCAPE_RIGHT.name]:
            app_current_bundleid = self.app_current()["bundleId"]
            if app_current_bundleid not in ['com.apple.springboard']:
                return x, y

            if not (x < 1 and y < 1):
                x, y = XYTransformer.up_2_ori(
                    (x, y),
                    (self.display_info['width'], self.display_info["height"]),
                    self.orientation
                )
            else:
                x, y = y, x
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
        # when Arg type is list, click the first match, raise ValueError if no match
        示例： ["设置", "信任", "安装"]

        Notes:
            Might not work on all devices

        Returns:
            None

        """
        return self.driver.alert.click(buttons)

    def device_info(self):
        """
        get the device info. 
        Notes:
            Might not work on all devices

        Returns:
            dict for device info

        """
        return self.session.info

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
