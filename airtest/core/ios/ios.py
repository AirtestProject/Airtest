#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys

import requests.exceptions
import wda
import time
import base64
import inspect
import logging
import traceback
from logzero import setup_logger
from functools import wraps
from urllib.parse import urlparse
from tidevice._usbmux import Usbmux
from tidevice._device import BaseDevice
from tidevice._proto import MODELS
from tidevice.exceptions import MuxError

from airtest import aircv
from airtest.core.device import Device
from airtest.core.ios.constant import CAP_METHOD, TOUCH_METHOD, IME_METHOD, ROTATION_MODE, KEY_EVENTS, \
    LANDSCAPE_PAD_RESOLUTION, IP_PATTERN
from airtest.core.ios.rotation import XYTransformer, RotationWatcher
from airtest.core.ios.instruct_cmd import InstructHelper
from airtest.utils.logger import get_logger
from airtest.core.ios.mjpeg_cap import MJpegcap
from airtest.core.settings import Settings as ST
from airtest.aircv.screen_recorder import ScreenRecorder, resize_by_max, get_max_size
from airtest.core.error import LocalDeviceError, AirtestError


LOGGING = get_logger(__name__)

DEFAULT_ADDR = "http://localhost:8100/"


def decorator_retry_session(func):
    """
    When the operation fails due to session failure, try to re-acquire the session,
    retry at most 3 times.

    当因为session失效而操作失败时，尝试重新获取session，最多重试3次。
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


def decorator_pairing_dialog(func):
    """
    When the device is not paired, trigger the trust dialogue and try again.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MuxError:
            LOGGING.error("Device is not yet paired. Triggered the trust dialogue. Please accept and try again." + "(iTunes is required on Windows.) " if sys.platform.startswith("win") else "")
            raise
    return wrapper


def add_decorator_to_methods(decorator):
    """
    This function takes a decorator as input and returns a decorator wrapper function. The decorator wrapper function takes a class as input and decorates all the methods of the class by applying the input decorator to each method.

    Parameters:
        - decorator: A decorator function that will be applied to the methods of the input class.

    Returns:
        - decorator_wrapper: A function that takes a class as input and decorates all the methods of the class by applying the input decorator to each method.
    """
    def decorator_wrapper(cls):
        # 获取要装饰的类的所有方法
        methods = [attr for attr in dir(cls) if callable(getattr(cls, attr)) and not attr.startswith("_")]

        # 为每个方法添加装饰器
        for method in methods:
            setattr(cls, method, decorator(getattr(cls, method)))

        return cls
    return decorator_wrapper


@add_decorator_to_methods(decorator_pairing_dialog)
class TIDevice:
    """Below staticmethods are provided by Tidevice.
    """

    @staticmethod
    def devices():
        """
        Get all available devices connected by USB, return a list of UDIDs.

        Returns:
            list: A list of UDIDs. 
            e.g. ['539c5fffb18f2be0bf7f771d68f7c327fb68d2d9']
        """
        return Usbmux().device_udid_list()
    
    @staticmethod
    def list_app(udid, app_type="user"):
        """
        Returns a list of installed applications on the device.

        Args:
            udid (str): The unique identifier of the device.
            app_type (str, optional): The type of applications to list. Defaults to "user".
                Possible values are "user", "system", or "all".

        Returns:
            list: A list of tuples containing the bundle ID, display name,
                and version of the installed applications.
            e.g. [('com.apple.mobilesafari', 'Safari', '8.0'), ...]
        """
        app_type = {
            "user": "User",
            "system": "System",
            "all": None,
        }.get(app_type.lower(), None)
        app_list = []
        for info in BaseDevice(udid, Usbmux()).installation.iter_installed(app_type=app_type):
            bundle_id = info['CFBundleIdentifier']
            try:
                display_name = info['CFBundleDisplayName']
                version = info.get('CFBundleShortVersionString', '')
                app_list.append((bundle_id, display_name, version))
            except BrokenPipeError:
                break
        return app_list

    @staticmethod
    def list_wda(udid):
        """Get all WDA on device that meet certain naming rules.

        Returns:
            List of WDA bundleID.
        """
        app_list = TIDevice.list_app(udid)
        wda_list = []
        for app in app_list:
            bundle_id, display_name, _ = app
            if ".xctrunner" in bundle_id or display_name == "WebDriverAgentRunner-Runner":
                wda_list.append(bundle_id)
        return wda_list
    
    @staticmethod
    def device_info(udid):
        """
        Retrieves device information based on the provided UDID.

        Args:
            udid (str): The unique device identifier.

        Returns:
            dict: A dictionary containing selected device information. The keys include:
                - productVersion (str): The version of the product.
                - productType (str): The type of the product.
                - modelNumber (str): The model number of the device.
                - serialNumber (str): The serial number of the device.
                - phoneNumber (str): The phone number associated with the device.
                - timeZone (str): The time zone of the device.
                - uniqueDeviceID (str): The unique identifier of the device.
                - marketName (str): The market name of the device.

        """
        device_info = BaseDevice(udid, Usbmux()).device_info()
        tmp_dict = {}
        # chose some useful device info from tidevice
        """
        'DeviceName', 'ProductVersion', 'ProductType',
        'ModelNumber', 'SerialNumber', 'PhoneNumber',
        'CPUArchitecture', 'ProductName', 'ProtocolVersion',
        'RegionInfo', 'TimeIntervalSince1970', 'TimeZone',
        'UniqueDeviceID', 'WiFiAddress', 'BluetoothAddress',
        'BasebandVersion'
        """
        for attr in ('ProductVersion', 'ProductType',
            'ModelNumber', 'SerialNumber', 'PhoneNumber', 
            'TimeZone', 'UniqueDeviceID'):
            key = attr[0].lower() + attr[1:]
            if attr in device_info:
                tmp_dict[key] = device_info[attr]
        try:
            tmp_dict["marketName"] = MODELS.get(device_info['ProductType'])
        except:
            tmp_dict["marketName"] = ""
        return tmp_dict
    
    @staticmethod
    def install_app(udid, file_or_url):
        BaseDevice(udid, Usbmux()).app_install(file_or_url)

    @staticmethod
    def uninstall_app(udid, bundle_id):
        BaseDevice(udid, Usbmux()).app_uninstall(bundle_id=bundle_id)

    @staticmethod
    def start_app(udid, bundle_id):
        BaseDevice(udid, Usbmux()).app_start(bundle_id=bundle_id)

    @staticmethod
    def stop_app(udid, bundle_id):
        # Note: seems not work.
        BaseDevice(udid, Usbmux()).app_stop(pid_or_name=bundle_id)

    @staticmethod
    def ps(udid):
        """
        Retrieves the process list of the specified device.

        Parameters:
            udid (str): The unique device identifier.

        Returns:
            list: A list of dictionaries containing information about each process. Each dictionary contains the following keys:
                - pid (int): The process ID.
                - name (str): The name of the process.
                - bundle_id (str): The bundle identifier of the process.
                - display_name (str): The display name of the process.
            e.g. [{'pid': 1, 'name': 'MobileSafari', 'bundle_id': 'com.apple.mobilesafari', 'display_name': 'Safari'}, ...]

        """
        with BaseDevice(udid, Usbmux()).connect_instruments() as ts:
            app_infos = list(BaseDevice(udid, Usbmux()).installation.iter_installed(app_type=None))
            ps = list(ts.app_process_list(app_infos))
        ps_list = []
        keys = ['pid', 'name', 'bundle_id', 'display_name']
        for p in ps:
            if not p['isApplication']:
                continue
            ps_list.append({key: p[key] for key in keys})
        return ps_list
    
    @staticmethod
    def ps_wda(udid):
        """Get all running WDA on device that meet certain naming rules.

        Returns:
            List of running WDA bundleID.
        """
        with BaseDevice(udid, Usbmux()).connect_instruments() as ts:
            app_infos = list(BaseDevice(udid, Usbmux()).installation.iter_installed(app_type=None))
            ps = list(ts.app_process_list(app_infos))
        ps_wda_list = []
        for p in ps:
            if not p['isApplication']:
                continue
            if ".xctrunner" in p['bundle_id'] or p['display_name'] == "WebDriverAgentRunner-Runner":
                ps_wda_list.append(p['bundle_id'])
            else:
                continue
        return ps_wda_list
    
    @staticmethod
    def xctest(udid, wda_bundle_id):
        return BaseDevice(udid, Usbmux()).xctest(fuzzy_bundle_id=wda_bundle_id, logger=setup_logger(level=logging.INFO))


@add_decorator_to_methods(decorator_retry_session)
class IOS(Device):
    """IOS client.

        - before this you have to run `WebDriverAgent <https://github.com/AirtestProject/iOS-Tagent>`_

        - ``xcodebuild -project path/to/WebDriverAgent.xcodeproj -scheme WebDriverAgentRunner -destination "id=$(idevice_id -l)" test``

        - ``iproxy $port 8100 $udid``
    """

    def __init__(self, addr=DEFAULT_ADDR, cap_method=CAP_METHOD.MJPEG, mjpeg_port=None, udid=None, name=None, serialno=None, wda_bundle_id=None):
        super().__init__()

        # If none or empty, use default addr.
        self.addr = addr or DEFAULT_ADDR

        # Fit wda format, make url start with http://,
        # e.g., http://localhost:8100/ or http+usbmux://00008020-001270842E88002E
        # with mjpeg_port: http://localhost:8100/?mjpeg_port=9100
        # with udid(udid/uuid/serialno are all ok): http://localhost:8100/?mjpeg_port=9100&&udid=00008020-001270842E88002E.
        if not self.addr.startswith("http"):
            self.addr = "http://" + addr

        # Here now use these supported cap touch and ime method.
        self.cap_method = cap_method
        self.touch_method = TOUCH_METHOD.WDATOUCH
        self.ime_method = IME_METHOD.WDAIME

        # Wda driver, use to home, start app, click/swipe/close app/get wda size.
        # Init wda session, updata when start app.
        wda.DEBUG = False
        # The three connection modes are determined by the addr.
        # e.g., connect remote device http://10.227.70.247:20042
        # e.g., connect local device http://127.0.0.1:8100 or http://localhost:8100 or http+usbmux://00008020-001270842E88002E
        self.udid = udid or name or serialno
        self._wda_bundle_id = wda_bundle_id
        parsed = urlparse(self.addr).netloc.split(":")[0] if ":" in urlparse(self.addr).netloc else urlparse(self.addr).netloc
        if parsed not in ["localhost", "127.0.0.1"] and "." in parsed:
            # Connect remote device via url.
            self.is_local_device = False
            self.driver = wda.Client(self.addr) 
        else:   
            # Connect local device via url.
            self.is_local_device = True
            if parsed in ["localhost", "127.0.0.1"]:
                if not udid:
                    udid = self._get_default_device()
                self.udid = udid
            else:
                self.udid = parsed
            self.driver = wda.USBClient(udid=self.udid, port=8100, wda_bundle_id=self.wda_bundle_id)
        # Record device's width and height.
        self._size = {'width': None, 'height': None}
        self._current_orientation = None
        self._touch_factor = None
        self._last_orientation = None
        self._is_pad = None
        self._using_ios_tagent = None
        self._device_info = {}
        self.instruct_helper = InstructHelper(self.device_info['uuid'])
        self.mjpegcap = MJpegcap(self.instruct_helper, ori_function=lambda: self.display_info,
                                 ip=self.ip, port=mjpeg_port)
        # Start up RotationWatcher with default session.
        self.rotation_watcher = RotationWatcher(self)
        self._register_rotation_watcher()

        self.alert_watch_and_click = self.driver.alert.watch_and_click

        # Recorder.
        self.recorder = None

        # Since uuid and udid are very similar, both names are allowed.
        self._udid = udid or name or serialno

    def _get_default_device(self):
        """Get local default device when no udid.

        Returns:
            Local device udid.
        """
        device_udid_list = TIDevice.devices()
        if device_udid_list:
            return device_udid_list[0]
        raise IndexError("iOS devices not found, please connect device first.")
    
    def _get_default_wda_bundle_id(self):
        """Get local default device's WDA bundleID when no WDA bundleID.

        Returns:
            Local device's WDA bundleID.
        """ 
        try:
            wda_list = TIDevice.list_wda(self.udid)
            return wda_list[0]
        except IndexError:
            raise IndexError("WDA bundleID not found, please install WDA on device.")
        
    def _get_default_running_wda_bundle_id(self):
        """Get the bundleID of the WDA that is currently running on local device.

        Returns:
            Local device's running WDA bundleID.
        """ 
        try:
            running_wda_list = TIDevice.ps_wda(self.udid)
            return running_wda_list[0]
        except IndexError:
            raise IndexError("Running WDA bundleID not found, please makesure WDA was started.")

    @property
    def wda_bundle_id(self):
        if not self._wda_bundle_id and self.is_local_device:
            self._wda_bundle_id = self._get_default_wda_bundle_id()
        return self._wda_bundle_id
        
    @property
    def ip(self):
        """Returns the IP address of the host connected to the iOS phone.

        It is not the IP address of the iOS phone.
        If you want to get the IP address of the phone, you can access the interface `get_ip_address`.
        For example: when the device is connected via http://localhost:8100, return localhost.
        If it is a remote device http://192.168.xx.xx:8100, it returns the IP address of 192.168.xx.xx.

        Returns:
            IP.
        """
        match = re.search(IP_PATTERN, self.addr)
        if match:
            ip = match.group(0)
        else:
            ip = 'localhost'
        return ip

    @property
    def uuid(self):
        return self._udid or self.addr

    @property
    def using_ios_tagent(self):
        """
        当前基础版本：appium/WebDriverAgent 4.1.4
        基于上述版本，2022.3.30之后发布的iOS-Tagent版本，在/status接口中新增了一个Version参数，如果能检查到本参数，说明使用了新版本ios-Tagent
        该版本基于Appium版的WDA做了一些改动，可以更快地进行点击和滑动，并优化了部分UI树的获取逻辑
        但是所有的坐标都为竖屏坐标，需要airtest自行根据方向做转换
        同时，大于4.1.4版本的appium/WebDriverAgent不再需要针对ipad进行特殊的横屏坐标处理了

        Returns:
            True if using ios-tagent, else False.
        """
        if self._using_ios_tagent is None:
            status = self.driver.status()
            if 'Version' in status:
                self._using_ios_tagent = True
            else:
                self._using_ios_tagent = False
        return self._using_ios_tagent

    def _fetch_new_session(self):
        """Re-acquire a new session.
        """
        # 根据facebook-wda的逻辑，直接设为None就会自动获取一个新的默认session
        self.driver.session_id = None

    @property
    def is_pad(self):
        """
        Determine whether it is an ipad(or 6P/7P/8P), if it is, in the case of horizontal screen + desktop,
        the coordinates need to be switched to vertical screen coordinates to click correctly (WDA bug).

        判断是否是ipad(或 6P/7P/8P)，如果是，在横屏+桌面的情况下，坐标需要切换成竖屏坐标才能正确点击（WDA的bug）

        Returns:
            True if it is an ipad, else False.
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
        """ Get the device info.

        Notes:
            Might not work on all devices.

        Returns:
            Dict for device info,
            e.g. AttrDict({
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
            device_info = self.driver.info
            try:
                # Add some device info.
                if not self.is_local_device:
                    raise LocalDeviceError()
                tmp_dict = TIDevice.device_info(self.udid)
                device_info.update(tmp_dict)
            except:
                pass
            finally:
                self._device_info = device_info
        return self._device_info

    def _register_rotation_watcher(self):
        """
        Register callbacks for Android and minicap when rotation of screen has changed,
        callback is called in another thread, so be careful about thread-safety.
        """
        self.rotation_watcher.reg_callback(lambda x: setattr(self, "_current_orientation", x))

    def window_size(self):
        """
        Returns: 
            Window size (width, height).
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
        Returns:
            Device orientation status in LANDSACPE POR.
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
        # Function window_size() return UIKit size, while screenshot() image size is Native Resolution.
        window_size = self.window_size()
        # When use screenshot, the image size is pixels size. e.g.(1080 x 1920)
        snapshot = self.snapshot()
        if self.orientation in [wda.LANDSCAPE, wda.LANDSCAPE_RIGHT]:
            self._size['window_width'], self._size['window_height'] = window_size.height, window_size.width
            width, height = snapshot.shape[:2]
        else:
            self._size['window_width'], self._size['window_height'] = window_size.width, window_size.height
            height, width = snapshot.shape[:2]
        self._size["width"] = width
        self._size["height"] = height

        # Use session.scale can get UIKit scale factor.
        # So self._touch_factor = 1 / self.driver.scale, but the result is incorrect on some devices(6P/7P/8P).
        self._touch_factor = float(self._size['window_height']) / float(height)
        self.rotation_watcher.get_ready()

        # 当前版本: wda 4.1.4 获取到的/window/size，在ipad+桌面横屏下拿到的是 height * height，需要修正。
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
        Func touch_factor is used to convert click coordinates: mobile phone real coordinates = touch_factor * screen coordinates.
        In general, no manual settings are required.

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
        """
        self._touch_factor = float(factor)

    def get_render_resolution(self):
        """Return render resolution after rotation.

        Returns:
            offset_x, offset_y, offset_width and offset_height of the display.
        """
        w, h = self.get_current_resolution()
        return 0, 0, w, h

    def get_current_resolution(self):
        w, h = self.display_info["width"], self.display_info["height"]
        if self.display_info["orientation"] in [wda.LANDSCAPE, wda.LANDSCAPE_RIGHT]:
            w, h = h, w
        return w, h

    def home(self):
        # Press("home") faster than home().
        return self.driver.press("home")

    def _neo_wda_screenshot(self):
        """
        This is almost same as wda implementation, but without png header check,
        as response data is now jpg format in mid quality.
        """
        value = self.driver.http.get('screenshot').value
        raw_value = base64.b64decode(value)
        return raw_value

    def snapshot(self, filename=None, quality=10, max_size=None):
        """Take snapshot.

        Args:
            filename: save screenshot to filename
            quality: The image quality, integer in range [1, 99]
            max_size: the maximum size of the picture, e.g 1200

        Returns:
            Screen snapshot's cv2 object.
        """
        data = self._neo_wda_screenshot()
        # Output cv2 object.
        try:
            screen = aircv.utils.string_2_img(data)
        except:
            # May be black/locked screen or other reason, print exc for debugging.
            traceback.print_exc()
            return None

        # Save as file if needed.
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

        Returns: None(iOS may all use vertical screen coordinates, so coordinates will not be returned.)

        Examples:
            >>> touch((100, 100))
            >>> touch((0.5, 0.5), duration=1)

        """
        x, y = pos
        if not (x < 1 and y < 1):
            x, y = int(x * self.touch_factor), int(y * self.touch_factor)
        # 根据用户安装的wda版本判断是否调用快速点击接口
        if self.using_ios_tagent:
            x, y = self._transform_xy(pos)
            self._quick_click(x, y, duration)
        else:
            self.driver.click(x, y, duration)

    def _quick_click(self, x, y, duration):
        """
        The method extended from the facebook-wda third-party library.
        Use modified appium wda to perform quick click.
        
        Args:
            x, y (int, float): float(percent), int(coordicate)
            duration (optional): tap_hold duration
        """
        x, y = self.driver._percent2pos(x, y)
        data = {'x': x, 'y': y, 'duration': duration}
        # 为了兼容改动直接覆盖原生接口的自制版wda。
        try:
            return self.driver._session_http.post('/wda/tap', data=data)
        except wda.WDARequestError as e:
            if e.status == 110:
                self.driver.click(x, y, duration)
                
    def double_click(self, pos):
        x, y = self._transform_xy(pos)
        self.driver.double_tap(x, y)

    def swipe(self, fpos, tpos, duration=0, delay=None, *args, **kwargs):
        """
        Args:
            fpos: start point
            tpos: end point
            duration (float): start coordinate press duration (seconds), default is None
            delay (float): start coordinate to end coordinate duration (seconds)

        Returns:
            None

        Examples:
            >>> swipe((1050, 1900), (150, 1900))
            >>> swipe((0.2, 0.5), (0.8, 0.5))
        """
        fx, fy = fpos
        tx, ty = tpos
        if not (fx < 1 and fy < 1):
            fx, fy = int(fx * self.touch_factor), int(fy * self.touch_factor)
        if not (tx < 1 and ty < 1):
            tx, ty = int(tx * self.touch_factor), int(ty * self.touch_factor)
        # 如果是通过ide来滑动，且安装的是自制版的wda就调用快速滑动接口，其他时候不关心滑动速度就使用原生接口保证滑动精确性。
        def ios_tagent_swipe(fpos, tpos, delay=None):
            # 调用自定义的wda swipe接口需要进行坐标转换。
            fx, fy = self._transform_xy(fpos)
            tx, ty = self._transform_xy(tpos)
            self._quick_swipe(fx, fy, tx, ty, delay or 0.2)

        if delay:
            if self.using_ios_tagent:
                ios_tagent_swipe(fpos, tpos, delay)
            else:
                self.driver.swipe(fx, fy, tx, ty)
        else:
            try:
                self.driver.swipe(fx, fy, tx, ty, duration)
            except wda.WDARequestError as e:
                if e.status == 110:
                    # 部分低版本iOS在滑动时，可能会有报错，调用一次ios-Tagent的快速滑动接口来尝试解决
                    if self.using_ios_tagent:
                        ios_tagent_swipe(fpos, tpos, delay)
                    else:
                        raise

    def _quick_swipe(self, x1, y1, x2, y2, delay):
        """
        The method extended from the facebook-wda third-party library.
        Use modified appium wda to perform quick swipe.
        
        Args:
            x1, y1, x2, y2 (int, float): float(percent), int(coordicate)
            delay (float): start coordinate to end coordinate duration (seconds)
        """
        if any(isinstance(v, float) for v in [x1, y1, x2, y2]):
            size = self.window_size()
            x1, y1 = self.driver._percent2pos(x1, y1, size)
            x2, y2 = self.driver._percent2pos(x2, y2, size)

        data = dict(fromX=x1, fromY=y1, toX=x2, toY=y2, delay=delay)
        # 为了兼容改动直接覆盖原生接口的自制版wda。
        try:
            return self.driver._session_http.post('/wda/swipe', data=data)
        except wda.WDARequestError as e:
            if e.status == 110:
                self.driver.swipe(x1, y1, x2, y2)

    def keyevent(self, keyname, **kwargs):
        """Perform keyevent on the device.

        Args:
            keyname: home/volumeUp/volumeDown
            **kwargs:
        """
        try:
            keyname = KEY_EVENTS[keyname.lower()]
        except KeyError:
            raise ValueError("Invalid name: %s, should be one of ('home', 'volumeUp', 'volumeDown')" % keyname)
        else:
            self.press(keyname)

    def press(self, keys):
        """Some keys in ["home", "volumeUp", "volumeDown"] can be pressed.
        """
        self.driver.press(keys)

    def text(self, text, enter=True):
        """Input text on the device.

        Args:
            text:  text to input
            enter: True if you need to enter a newline at the end

        Examples:
            >>> text("test")
            >>> text("中文")
        """
        if enter:
            text += '\n'
        self.driver.send_keys(text)
        
    def install_app(self, file_or_url, **kwargs):
        """
        curl -X POST $JSON_HEADER \
        -d "{\"desiredCapabilities\":{\"bundleId\":\"com.apple.mobilesafari\", \"app\":\"[host_path]/magicapp.app\"}}" \
        $DEVICE_URL/session
        https://github.com/facebook/WebDriverAgent/wiki/Queries

        Install app from the device.

        Args:
            file_or_url: file or url to install

        Returns:
            bundle ID

        Raises:
            LocalDeviceError: If the device is remote.
        """
        if not self.is_local_device:
            raise LocalDeviceError()
        return TIDevice.install_app(self.udid, file_or_url)
    
    def uninstall_app(self, bundle_id):
        """Uninstall app from the device.

        Notes: 
            It seems always return True.

        Args:
            bundle_id: the app bundle id, e.g ``com.apple.mobilesafari``

        Raises:
            LocalDeviceError: If the device is remote.
        """
        if not self.is_local_device:
            raise LocalDeviceError()
        return TIDevice.uninstall_app(self.udid, bundle_id)

    def start_app(self, bundle_id, *args, **kwargs):
        """
        Args:
            bundle_id: the app bundle id, e.g ``com.apple.mobilesafari``

        Returns:
            Process ID.

        Examples:
            >>> start_app('com.apple.mobilesafari')
        """
        if not self.is_local_device:
            # Note: If the bundle_id does not exist, it may get stuck.
            try:
                return self.driver.app_launch(bundle_id)
            except requests.exceptions.ReadTimeout:
                raise AirtestError(f"App launch timeout, please check if the app is installed: {bundle_id}")
        else:
            return TIDevice.start_app(self.udid, bundle_id)
    
    def stop_app(self, bundle_id):
        """
        Note: Both ways of killing the app may fail, nothing responds or just closes the 
        app to the background instead of actually killing it and no error will be reported.
        """
        try:
            if not self.is_local_device:
                raise LocalDeviceError()
            TIDevice.stop_app(self.udid, bundle_id)
        except:
            pass
        finally:
            self.driver.app_stop(bundle_id=bundle_id)

    def list_app(self, type="user"):
        """
        Returns a list of installed applications on the device.

        Args:
            type (str, optional): The type of applications to list. Defaults to "user".
                Possible values are "user", "system", or "all".

        Returns:
            list: A list of tuples containing the bundle ID, display name,
                and version of the installed applications.
            e.g. [('com.apple.mobilesafari', 'Safari', '8.0'), ...]

        Raises:
            LocalDeviceError: If the device is remote.
        """
        if not self.is_local_device:
            raise LocalDeviceError()
        return TIDevice.list_app(self.udid, app_type=type)

    def app_state(self, bundle_id):
        """ Get app state and ruturn.

        Args:
            bundle_id: Bundle ID of app.

        Returns:
            {
                "value": 4,
                "sessionId": "0363BDC5-4335-47ED-A54E-F7CCB65C6A65"
            }

            Value 1(not running) 2(running in background) 3(running in foreground)? 4(running).
        """
        return self.driver.app_state(bundle_id=bundle_id)

    def app_current(self):
        """Get the app current.

        Notes:
            Might not work on all devices.

        Returns:
            Current app state dict, eg:
            {"pid": 1281,
             "name": "",
             "bundleId": "com.netease.cloudmusic"}
        """
        return self.driver.app_current()
    
    def get_clipboard(self, wda_bundle_id=None, *args, **kwargs):
        """Get clipboard text.

        Before calling the WDA interface, you need to ensure that WDA was foreground.  
        If there are multiple WDA on your device, please specify the active WDA by parameter wda_bundle_id.
        
        Args:
            wda_bundle_id: The bundle id of the running WDA, if None, will use default WDA bundle id.

        Returns:
            Clipboard text.

        Raises:
            LocalDeviceError: If the device is remote and the wda_bundle_id parameter is not provided.

        Notes:
            If you want to use this function, you have to set WDA foreground which would switch the 
            current screen of the phone. Then we will try to switch back to the screen before.
        """
        if wda_bundle_id is None:
            if not self.is_local_device:
                raise LocalDeviceError("Remote device need to set running wda bundle id parameter, \
                                       e.g. get_clipboard('wda_bundle_id').")
            wda_bundle_id = self.wda_bundle_id
        # Set wda foreground, it's necessary.
        try:
            current_app_bundle_id = self.app_current().get("bundleId", None)
        except:
            current_app_bundle_id = None
        try:
            self.driver.app_launch(wda_bundle_id)
        except:
            pass
        # 某些机型版本下，有一定概率获取失败，尝试重试一次
        clipboard_text = self.driver._session_http.post("/wda/getPasteboard").value
        if not clipboard_text:
            clipboard_text = self.driver._session_http.post("/wda/getPasteboard").value
        decoded_text = base64.b64decode(clipboard_text).decode('utf-8')

        # Switch back to the screen before.
        if current_app_bundle_id:
            self.driver.app_launch(current_app_bundle_id)
        else:
            LOGGING.warning("we can't switch back to the app before, because can't get bundle id.")
        return decoded_text
    
    def set_clipboard(self, content, wda_bundle_id=None, *args, **kwargs):
        """
        Set the clipboard content on the device.

        Args:
            content (str): The content to be set on the clipboard.
            wda_bundle_id (str, optional): The bundle ID of the WDA app. Defaults to None.

        Raises:
            LocalDeviceError: If the device is remote and the wda_bundle_id parameter is not provided.

        Returns:
            None
        """
        if wda_bundle_id is None:
            if not self.is_local_device:
                raise LocalDeviceError("Remote device need to set running wda bundle id parameter, \
                                        e.g. set_clipboard('content', 'wda_bundle_id').")
            wda_bundle_id = self.wda_bundle_id
        # Set wda foreground, it's necessary.
        try:
            current_app_bundle_id = self.app_current().get("bundleId", None)
        except:
            current_app_bundle_id = None
        try:
            self.driver.app_launch(wda_bundle_id)
        except:
            pass
        self.driver.set_clipboard(content)
        clipboard_text = self.driver._session_http.post("/wda/getPasteboard").value
        decoded_text = base64.b64decode(clipboard_text).decode('utf-8')
        if decoded_text != content:
            # 部分机型偶现设置剪切板失败，重试一次
            self.driver.set_clipboard(content)
        # Switch back to the screen before.
        if current_app_bundle_id:
            self.driver.app_launch(current_app_bundle_id)
        else:
            LOGGING.warning("we can't switch back to the app before, because can't get bundle id.")

    def paste(self, wda_bundle_id=None, *args, **kwargs):
        """
        Paste the current clipboard content on the device.

        Args:
            wda_bundle_id (str, optional): The bundle ID of the WDA app. Defaults to None.

        Raises:
            LocalDeviceError: If the device is remote and the wda_bundle_id parameter is not provided.

        Returns:
            None
        """
        self.text(self.get_clipboard(wda_bundle_id=wda_bundle_id))

    def get_ip_address(self):
        """Get ip address from WDA.

        Returns:
            If no IP address has been found, otherwise return the IP address.
        """
        ios_status = self.driver.status()['ios']
        # If use modified WDA, try to get real wifi IP first.
        return ios_status.get('wifiIP', ios_status['ip'])

    def device_status(self):
        """Show status return by WDA.

        Returns:
            Dicts of infos.
        """
        return self.driver.status()

    def _touch_point_by_orientation(self, tuple_xy):
        """
        Convert image coordinates to physical display coordinates, the arbitrary point (origin) is upper left corner
        of the device physical display.

        Args:
            tuple_xy: image coordinates (x, y)

        Returns:
            physical coordinates (x, y)
        """
        x, y = tuple_xy

        # 1. 如果使用了2022.03.30之后发布的iOS-Tagent版本，则必须要进行竖屏坐标转换。
        # 2. 如果使用了appium/WebDriverAgent>=4.1.4版本，直接使用原坐标即可，无需转换。
        # 3. 如果使用了appium/WebDriverAgent<4.1.4版本，或低版本的iOS-Tagent，并且ipad下横屏点击异常，请改用airtest<=1.2.4。
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

        # Scale touch postion.
        if not (x < 1 and y < 1):
            x, y = int(x * self.touch_factor), int(y * self.touch_factor)

        return x, y

    def _check_orientation_change(self):
        pass

    def is_locked(self):
        """
        Return True or False whether the device is locked or not.

        Notes:
            Might not work on some devices.

        Returns:
            True or False.
        """
        return self.driver.locked()

    def unlock(self):
        """Unlock the device, unlock screen, double press home.

        Notes:
            Might not work on all devices.
        """
        return self.driver.unlock()

    def lock(self):
        """Lock the device, lock screen.

        Notes:
            Might not work on all devices.
        """
        return self.driver.lock()

    def setup_forward(self, port):
        """
        Setup port forwarding from device to host.
        Args:
            port: device port

        Returns:
            host port, device port

        Raises:
            LocalDeviceError: If the device is remote.

        """
        return self.instruct_helper.setup_proxy(int(port))

    def ps(self):
        """Get the process list of the device.

        Returns:
            Process list of the device.
        """
        if not self.is_local_device:
            raise LocalDeviceError()
        return TIDevice.ps(self.udid)

    def alert_accept(self):
        """ Alert accept-Actually do click first alert button.

        Notes:
            Might not work on all devices.
        """
        return self.driver.alert.accept()

    def alert_dismiss(self):
        """Alert dissmiss-Actually do click second alert button.

        Notes:
            Might not work on all devices.
        """
        return self.driver.alert.dismiss()

    def alert_wait(self, time_counter=2):
        """If alert apper in time_counter second it will return True,else return False (default 20.0).

        Notes:
            Might not work on all devices.
        """
        return self.driver.alert.wait(time_counter)

    def alert_buttons(self):
        """Get alert buttons text. 

        Notes:
            Might not work on all devices.

        Returns:
             # example return: ("设置", "好")

        """
        return self.driver.alert.buttons()

    def alert_exists(self):
        """ Get True for alert exists or False.

        Notes:
            Might not work on all devices

        Returns:
            True or False
        """
        return self.driver.alert.exists

    def alert_click(self, buttons):
        """When Arg type is list, click the first match, raise ValueError if no match.

        e.g. ["设置", "信任", "安装"]

        Notes:
            Might not work on all devices.
        """
        return self.driver.alert.click(buttons)

    def home_interface(self):
        """Get True for the device status is on home interface. 

        Reason:
            Some devices can Horizontal screen on the home interface.

        Notes:
            Might not work on all devices.

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
        """Disconnected mjpeg and rotation_watcher.
        """
        if self.cap_method == CAP_METHOD.MJPEG:
            self.mjpegcap.teardown_stream()
        if self.rotation_watcher:
            self.rotation_watcher.teardown()
    
    def start_recording(self, max_time=1800, output=None, fps=10,
                        snapshot_sleep=0.001, orientation=0, max_size=None, *args, **kwargs):
        """Start recording the device display.

        Args:
            max_time: maximum screen recording time, default is 1800
            output: ouput file path
            fps: frames per second will record
            snapshot_sleep: sleep time for each snapshot.
            orientation: 1: portrait, 2: landscape, 0: rotation, default is 0
            max_size: max size of the video frame, e.g.800, default is None. Smaller sizes lead to lower system load.

        Returns:
            save_path: path of video file

        Examples:

            Record 30 seconds of video and export to the current directory test.mp4:

            >>> from airtest.core.api import connect_device, sleep
            >>> dev = connect_device("IOS:///")
            >>> save_path = dev.start_recording(output="test.mp4")
            >>> sleep(30)
            >>> dev.stop_recording()
            >>> print(save_path)

            >>> # the screen is portrait
            >>> portrait_mp4 = dev.start_recording(output="portrait.mp4", orientation=1)  # or orientation="portrait"
            >>> sleep(30)
            >>> dev.stop_recording()

            >>> # the screen is landscape
            >>> landscape_mp4 = dev.start_recording(output="landscape.mp4", orientation=2)  # or orientation="landscape"

            You can specify max_size to limit the video's maximum width/length. Smaller video sizes result in lower CPU load.

            >>> dev.start_recording(output="test.mp4", max_size=800)

        """
        if fps > 10 or fps < 1:
            LOGGING.warning("fps should be between 1 and 10, becuase of the recording effiency")
            if fps > 10:
                fps = 10
            if fps < 1:
                fps = 1

        if self.recorder and self.recorder.is_running():
            LOGGING.warning("recording is already running, please don't call again")
            return None
        
        logdir = "./"
        if ST.LOG_DIR is not None:
            logdir = ST.LOG_DIR
        if output is None:
            save_path = os.path.join(logdir, "screen_%s.mp4" % (time.strftime("%Y%m%d%H%M%S", time.localtime())))
        else:
            if os.path.isabs(output):
                save_path = output
            else:
                save_path = os.path.join(logdir, output)

        max_size = get_max_size(max_size)
        def get_frame():
            data = self.get_frame_from_stream()
            frame = aircv.utils.string_2_img(data)
            
            if max_size is not None:
                frame = resize_by_max(frame, max_size)
            return frame

        self.recorder = ScreenRecorder(
            save_path, get_frame, fps=fps,
            snapshot_sleep=snapshot_sleep, orientation=orientation)
        self.recorder.stop_time = max_time
        self.recorder.start()
        LOGGING.info("start recording screen to {}".format(save_path))
        return save_path

    def stop_recording(self,):
        """ Stop recording the device display. Recoding file will be kept in the device.
        """
        LOGGING.info("stopping recording")
        self.recorder.stop()
        return None
