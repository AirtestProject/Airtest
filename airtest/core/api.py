# -*- coding: utf-8 -*-
"""
This module contains the Airtest Core APIs.
"""
import os
import time
from airtest.utils.compat import urlparse, parse_qsl
from airtest.core.cv import Template, loop_find, try_log_screen
from airtest.core.error import TargetNotFoundError
from airtest.core.helper import G, set_logdir, logwrap, on_platform, import_device_cls, delay_after_operation
from airtest.core.settings import Settings as ST

"""
Device Setup APIs
"""


def connect_device(uri):
    """
    Initialize device with uri and set the device as the current one.

    :param uri: an URI where to connect to device, e.g. `android://adbhost:adbport/serialno?param=value&param2=value2`
    :return: device instance
    :Example:
        * ``android:///`` # local adb device using default params
        * ``android://adbhost:adbport/1234566?cap_method=javacap&touch_method=adb``  # remote adb device using custom params
        * ``windows:///`` # local Windows application
        * ``ios:///`` # iOS device

    :platforms: Android, iOS, Windows
    """
    d = urlparse(uri)
    platform = d.scheme
    host = d.netloc
    uuid = d.path.lstrip("/")
    params = dict(parse_qsl(d.query))

    if host:
        params["host"] = host.split(":")

    cls = import_device_cls(platform)
    dev = cls(uuid, **params)
    G.add_device(dev)
    return dev


def device():
    """
    Return the current active device.

    :return: current device instance
    :platforms: Android, iOS, Windows
    """
    return G.DEVICE


@on_platform(["Android", "Windows", "IOS"])
def set_current(index):
    """
    Set current active device.

    :param index: index of initialized device instance
    :raise IndexError: raised when device index is out of device list
    :return: None
    :platforms: Android, iOS, Windows
    """
    try:
        G.DEVICE = G.DEVICE_LIST[index]
    except IndexError:
        raise IndexError("device index out of range: %s/%s" % (index, len(G.DEVICE_LIST)))


"""
Device Operations
"""


@logwrap
@on_platform(["Android"])
def shell(cmd):
    """
    Start remote shell in the target device and execute the command

    :param cmd: command to be run on device, e.g. "ls /data/local/tmp"
    :return: the output of the shell cmd
    :platforms: Android
    """
    return G.DEVICE.shell(cmd)


@logwrap
@on_platform(["Android", "IOS"])
def start_app(package, activity=None):
    """
    Start the target application on device

    :param package: name of the package to be started, e.g. "com.netease.my"
    :param activity: the activity to start, default is None which means the main activity
    :return: None
    :platforms: Android, iOS
    """
    G.DEVICE.start_app(package, activity)


@logwrap
@on_platform(["Android", "IOS"])
def stop_app(package):
    """
    Stop the target application on device

    :param package: name of the package to stop, see also `start_app`
    :return: None
    :platforms: Android, iOS
    """
    G.DEVICE.stop_app(package)


@logwrap
@on_platform(["Android", "IOS"])
def clear_app(package):
    """
    Clear data of the target application on device

    :param package: name of the package,  see also `start_app`
    :return: None
    :platforms: Android, iOS
    """
    G.DEVICE.clear_app(package)


@logwrap
@on_platform(["Android", "IOS"])
def install(filepath):
    """
    Install application on device

    :param filepath: the path to file to be installed on target device
    :return: None
    :platforms: Android, iOS
    """
    return G.DEVICE.install_app(filepath)


@logwrap
@on_platform(["Android", "IOS"])
def uninstall(package):
    """
    Uninstall application on device

    :param package: name of the package, see also `start_app`
    :return: None
    :platforms: Android, iOS
    """
    return G.DEVICE.uninstall_app(package)


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def snapshot(filename=None, msg=""):
    """
    Take the screenshot of the target device and save it to the file.

    :param filename: name of the file where to save the screenshot. If the relative path is provided, the default
                     location is ``ST.LOG_DIR``
    :param msg: short description for screenshot, it will be recorded in the report
    :return: absolute path of the screenshot
    :platforms: Android, iOS, Windows
    """
    if not filename:
        filename = "%(time)d.jpg" % {'time': time.time() * 1000}
    if not os.path.isabs(filename):
        logdir = ST.LOG_DIR or "."
        filepath = os.path.join(logdir, filename)
    else:
        filepath = filename
    screen = G.DEVICE.snapshot(filepath)
    try_log_screen(screen)
    return filepath


@logwrap
@on_platform(["Android", "IOS"])
def wake():
    """
    Wake up and unlock the target device

    :return: None
    :platforms: Android, iOS

    .. note:: Might not work on some models
    """
    G.DEVICE.wake()


@logwrap
@on_platform(["Android", "IOS"])
def home():
    """
    Return to the home screen of the target device.

    :return: None
    :platforms: Android, iOS
    """
    G.DEVICE.home()


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def touch(v, **kwargs):
    """
    Perform the touch action on the device screen

    :param v: target to touch, either a Template instance or absolute coordinates (x, y)
    :param kwargs: platform specific `kwargs`, please refer to corresponding docs
    :return: None
    :platforms: Android, Windows, iOS
    """
    if isinstance(v, Template):
        try:
            pos = loop_find(v, timeout=ST.FIND_TIMEOUT)
        except TargetNotFoundError:
            raise
    else:
        try_log_screen()
        pos = v

    G.DEVICE.touch(pos, **kwargs)
    delay_after_operation()


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def swipe(v1, v2=None, vector=None, **kwargs):
    """
    Perform the swipe action on the device screen.

    There are two ways of assigning the parameters
        * ``swipe(v1, v2=Template(...))``   # swipe from v1 to v2
        * ``swipe(v1, vector=(x, y))``      # swipe starts at v1 and moves along the vector.


    :param v1: the start point of swipe,
               either a Template instance or absolute coordinates (x, y)
    :param v2: the end point of swipe,
               either a Template instance or absolute coordinates (x, y)
    :param vector: a vector coordinates of swipe action, either absolute coordinates (x, y) or percentage of
                   screen e.g.(0.5, 0.5)
    :param **kwargs: platform specific `kwargs`, please refer to corresponding docs
    :raise Exception: general exception when not enough parameters to perform swap action have been provided
    :return: None
    :platforms: Android, Windows, iOS
    """
    if isinstance(v1, Template):
        pos1 = loop_find(v1, timeout=ST.FIND_TIMEOUT)
    else:
        try_log_screen()
        pos1 = v1

    if v2:
        if isinstance(v2, Template):
            pos2 = loop_find(v2, timeout=ST.FIND_TIMEOUT_TMP)
        else:
            pos2 = v2
    elif vector:
        if vector[0] <= 1 and vector[1] <= 1:
            w, h = G.DEVICE.get_current_resolution()
            vector = (int(vector[0] * w), int(vector[1] * h))
        pos2 = (pos1[0] + vector[0], pos1[1] + vector[1])
    else:
        raise Exception("no enough params for swipe")

    G.DEVICE.swipe(pos1, pos2, **kwargs)
    delay_after_operation()


@logwrap
@on_platform(["Android"])
def pinch(in_or_out='in', center=None, percent=0.5):
    """
    Perform the pinch action on the device screen

    :param in_or_out: pinch in or pinch out, enum in ["in", "out"]
    :param center: center of pinch action, default as None which is the center of the screen
    :param percent: percentage of the screen of pinch action, default is 0.5
    :return: None
    :platforms: Android
    """
    G.DEVICE.pinch(in_or_out=in_or_out, center=center, percent=percent)
    delay_after_operation()


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def keyevent(keyname, **kwargs):
    """
    Perform key event on the device

    :param keyname: platform specific key name
    :param **kwargs: platform specific `kwargs`, please refer to corresponding docs
    :return: None
    :platforms: Android, Windows, iOS
    """
    G.DEVICE.keyevent(keyname, **kwargs)
    delay_after_operation()


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def text(text, enter=True):
    """
    Input text on the target device. Text input widget must be active first.

    :param text: text to input, unicode is supported
    :param enter: input `Enter` keyevent after text input, default is True
    :return: None
    :platforms: Android, Windows, iOS
    """
    G.DEVICE.text(text, enter=enter)
    delay_after_operation()


@logwrap
def sleep(secs=1.0):
    """
    Set the sleep interval. It will be recorded in the report

    :param secs: seconds to sleep
    :return: None
    :platforms: Android, Windows, iOS
    """
    time.sleep(secs)


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def wait(v, timeout=None, interval=0.5, intervalfunc=None):
    """
    Wait to match the Template on the device screen

    :param v: target object to wait for, Template instance
    :param timeout: time interval to wait for the match, default is None which is ``ST.FIND_TIMEOUT``
    :param interval: time interval in seconds to attempt to find a match
    :param intervalfunc: called after each unsuccessful attempt to find the corresponding match
    :raise TargetNotFoundError: raised if target is not found after the time limit expired
    :return: coordinates of the matched target
    :platforms: Android, Windows, iOS
    """
    timeout = timeout or ST.FIND_TIMEOUT
    pos = loop_find(v, timeout=timeout, interval=interval, intervalfunc=intervalfunc)
    return pos


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def exists(v):
    """
    Check whether given target exists on device screen

    :param v: target to be checked
    :return: False if target is not found, otherwise returns the coordinates of the target
    :platforms: Android, Windows, iOS
    """
    try:
        pos = loop_find(v, timeout=ST.FIND_TIMEOUT_TMP)
    except TargetNotFoundError:
        return False
    else:
        return pos


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def find_all(v):
    """
    Find all occurrences of the target on the device screen and return their coordinates

    :param v: target to find
    :return: list of coordinates, [(x, y), (x1, y1), ...]
    :platforms: Android, Windows, iOS
    """
    screen = G.DEVICE.snapshot()
    return v.match_all_in(screen)


"""
Assertions
"""


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def assert_exists(v, msg=""):
    """
    Assert target exists on device screen

    :param v: target to be checked
    :param msg: short description of assertion, it will be recorded in the report
    :raise AssertionError: if assertion fails
    :return: coordinates of the target
    :platforms: Android, Windows, iOS
    """
    try:
        pos = loop_find(v, timeout=ST.FIND_TIMEOUT, threshold=ST.THRESHOLD_STRICT)
        return pos
    except TargetNotFoundError:
        raise AssertionError("%s does not exist in screen, message: %s" % (v, msg))


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def assert_not_exists(v, msg=""):
    """
    Assert target does not exist on device screen

    :param v: target to be checked
    :param msg: short description of assertion, it will be recorded in the report
    :raise AssertionError: if assertion fails
    :return: None.
    :platforms: Android, Windows, iOS
    """
    try:
        pos = loop_find(v, timeout=ST.FIND_TIMEOUT_TMP)
        raise AssertionError("%s exists unexpectedly at pos: %s, message: %s" % (v, pos, msg))
    except TargetNotFoundError:
        pass


@logwrap
def assert_equal(first, second, msg=""):
    """
    Assert two values are equal

    :param first: first value
    :param second: second value
    :param msg: short description of assertion, it will be recorded in the report
    :raise AssertionError: if assertion fails
    :return: None
    :platforms: Android, Windows, iOS
    """
    if first != second:
        raise AssertionError("%s and %s are not equal, message: %s" % (first, second, msg))


@logwrap
def assert_not_equal(first, second, msg=""):
    """
    Assert two values are not equal

    :param first: first value
    :param second: second value
    :param msg: short description of assertion, it will be recorded in the report
    :raise AssertionError: if assertion
    :return: None
    :platforms: Android, Windows, iOS
    """
    if first == second:
        raise AssertionError("%s and %s are equal, message: %s" % (first, second, msg))
