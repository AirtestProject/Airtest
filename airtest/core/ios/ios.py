#! /usr/bin/env python
# -*- coding: utf-8 -*-


# from airtest.core.ios.wda_client import LANDSCAPE, PORTRAIT, LANDSCAPE_RIGHT, PORTRAIT_UPSIDEDOWN, WDAError, DEBUG, Client
# from airtest.utils.logger import get_logger
# from airtest.core.ios.instruct_cmd import InstructHelper
# from airtest.core.ios.fake_minitouch import fakeMiniTouch
# from airtest.core.ios.rotation import XYTransformer, RotationWatcher
# from airtest.core.ios.constant import CAP_METHOD, TOUCH_METHOD, IME_METHOD
# from airtest.core.device import Device
# from airtest import aircv
import requests
import six
import time
import json
import base64
import traceback
import wda

if six.PY3:
    from urllib.parse import urljoin
else:
    from urlparse import urljoin

from airtest import aircv
from airtest.core.device import Device
from airtest.core.ios.constant import CAP_METHOD, TOUCH_METHOD, IME_METHOD
from airtest.core.ios.rotation import XYTransformer, RotationWatcher
from airtest.core.ios.fake_minitouch import fakeMiniTouch
from airtest.utils.logger import get_logger

from wda import LANDSCAPE, PORTRAIT, LANDSCAPE_RIGHT, PORTRAIT_UPSIDEDOWN
from wda import WDAError

logger = get_logger(__name__)

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

# retry when saved session failed
def retry_session(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except WDAError as err:
            # 6 : Session does not exist
            if err.value.has_key('error'):
                self._fetchNewSession()
                return func(self, *args, **kwargs)
            else:
                raise err
    return wrapper


class IOS(Device):
    """ios client

        - before this you have to run `WebDriverAgent <https://github.com/AirtestProject/iOS-Tagent>`_

        - ``xcodebuild -project path/to/WebDriverAgent.xcodeproj -scheme WebDriverAgentRunner -destination "id=$(idevice_id -l)" test``

        - ``iproxy $port 8100 $udid``
    """

    def __init__(self, addr=DEFAULT_ADDR):
        super(IOS, self).__init__()

        # if none or empty, use default addr
        print("Using default ios devices")
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
        self._touch_factor = 0.5
        self._last_orientation = None
        self.defaultSession = None

        # start up RotationWatcher with default session
        self.rotation_watcher = RotationWatcher(self)

        # fake minitouch to simulate swipe
        self.minitouch = fakeMiniTouch(self)

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

    def _fetchNewSession(self):
        self.defaultSession = self.driver.session()

    @retry_session
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
    @retry_session
    def orientation(self):
        """
            return device oritantation status
            in  LANDSACPE POR
        """
        z = self.driver._session_http.get('rotation').value.get('z')
        return ROTATION_MODE.get(z, PORTRAIT)

    @property
    def display_info(self):
        if not self._size['width'] or not self._size['height']:
            self.snapshot()

        return {'width': self._size['width'], 'height': self._size['height'], 'orientation': self.orientation,
                'physical_width': self._size['width'], 'physical_height': self._size['height']}

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
        if self.display_info["orientation"] in ['LANDSCAPE', 'UIA_DEVICE_ORIENTATION_LANDSCAPERIGHT']:
            w, h = h, w
        return w, h

    def home(self):
        return self.driver.home()

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

        if self.cap_method == CAP_METHOD.MINICAP:
            raise NotImplementedError
        elif self.cap_method == CAP_METHOD.MINICAP_STREAM:
            raise NotImplementedError
        elif self.cap_method == CAP_METHOD.WDACAP:
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

        h, w = screen.shape[:2]

        # save last res for portrait
        if self.orientation in [LANDSCAPE, 'UIA_DEVICE_ORIENTATION_LANDSCAPERIGHT']:
            self._size['height'] = w
            self._size['width'] = h
        else:
            self._size['height'] = h
            self._size['width'] = w

        winw, winh = self.window_size()

        self._touch_factor = float(winh) / float(h)

        # save as file if needed
        if filename:
            aircv.imwrite(filename, screen, quality, max_size=max_size)

        return screen

    @retry_session
    def touch(self, pos, duration=0.01):
        # trans pos of click, pos can be percentage or real coordinate
        logger.info("touch original-postion at (%s, %s)", pos[0], pos[1])
        pos = self._touch_point_by_orientation(pos)

        # scale touch postion
        x, y = pos[0] * self._touch_factor, pos[1] * self._touch_factor

        logger.info("touch last-postion at (%s, %s)", x, y)
        if duration >= 0.5:
            self.session.tap_hold(x, y, duration)
        else:
            self.session.tap(x, y)

    def double_click(self, pos):
        # trans pos of click
        pos = self._touch_point_by_orientation(pos)

        x, y = pos[0] * self._touch_factor, pos[1] * self._touch_factor
        self.session.double_tap(x, y)

    def swipe(self, fpos, tpos, duration=0.5, steps=5, fingers=1):
        # trans pos of swipe, pos is percentage 
        fx, fy = self._touch_point_by_orientation(fpos)
        tx, ty = self._touch_point_by_orientation(tpos)

        fxp, fyp = fx * self._touch_factor, fy * self._touch_factor
        txp, typ = tx * self._touch_factor, ty * self._touch_factor
        fxp, fyp = float('%.2f' % fxp), float('%.2f' % fyp)
        txp, typ = float('%.2f' % txp), float('%.2f' % typ)

        logger.info("swipe postion1 (%s, %s) to postion2 (%s, %s), for duration: %s", fxp, fyp, txp, typ, duration)
        self.session.swipe(fxp, fyp, txp, typ, duration)

    def keyevent(self, keys):
        """just use as home event"""
        keys = keys.lower()
        if keys not in ['home',"volumeup", "volumedown"]:
            raise NotImplementedError
        self.press(KEYS_EVENTS.get(keys))
    
    def press(self, keys):
        """some keys in ["home", "volumeUp", "volumeDown"] can be pressed"""
        self.session.press(keys)

    @retry_session
    def text(self, text, enter=True):
        """bug in wda for now"""
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

    def start_app(self, package, activity=None):
        self.driver.app_launch(bundle_id=package)

    def stop_app(self, package):
        self.driver.app_stop(bundle_id=package)
    
    def app_state(self, package):
        # output {"value": 4, "sessionId": "xxxxxx"}
        # different value means 1: die, 2: background, 4: running
        return self.driver.app_state(bundle_id=package)
    
    def app_current(self):
        """
        get the app current 

        Notes:
            Might not work on all devices

        Returns:
            current app state

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
        try:
            app_current_dict = self.app_current()
            app_current_bundleId = app_current_dict.get('bundleId')
            logger.info("app_current_bundleId %s", app_current_bundleId)
        except Exception as err:
            logger.error(err)
            app_current_bundleId = 'example_bundleID'
        if app_current_bundleId not in ['com.apple.springboard']:
            return x, y

        # use correct w and h due to now orientation
        # _size 只对应竖直时候长宽
        now_orientation = self.orientation

        logger.info("current orientation for %s", now_orientation)
        if now_orientation in ['PORTRAIT', 'UIA_DEVICE_ORIENTATION_PORTRAIT_UPSIDEDOWN']:
            width, height = self._size['width'], self._size["height"]
        else:
            height, width = self._size['width'], self._size["height"]

        logger.info("current save window_size for (%s, %s)", self._size['width'], self._size["height"])
        # check if not get screensize when touching
        if not width or not height:
            # use snapshot to get current resuluton
            self.snapshot()
            # use the new get screen size to reinitialize width and height
            if now_orientation in ['PORTRAIT', 'UIA_DEVICE_ORIENTATION_PORTRAIT_UPSIDEDOWN']:
                width, height = self._size['width'], self._size["height"]
            else:
                height, width = self._size['width'], self._size["height"]

        x, y = XYTransformer.up_2_ori(
            (x, y),
            (width, height),
            now_orientation
        )
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

    def alert_click(self, buttons:list):
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
            logger.info("app_current_bundleId %s", app_current_bundleId)
        except Exception as err:
            logger.error(err)
            app_current_bundleId = 'example_bundleID'
        if app_current_bundleId in ['com.apple.springboard']:
            return True
        else:
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
