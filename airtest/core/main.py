# -*- coding: utf-8 -*-
"""
Airtest is a automated test framework for games, cross platform and based on image recognition.
"""
import os
import time
from urlparse import urlparse, parse_qsl
from airtest.core.cv import Template, loop_find, cv_match_all
from airtest.core.error import TargetNotFoundError
from airtest.core.helper import G, logwrap, on_platform, import_device_cls, delay_after_operation
from airtest.core.settings import Settings as ST


"""
Device Setup
"""


def connect_device(uri):
    """
    Initialize device with uri.

    :param uri: eg: android://adbhost:adbport/serialno?p1=v1
    :return: device instance
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
    Get current active device.

    :return: current device instance
    """
    return G.DEVICE


@on_platform(["Android", "Windows", "IOS"])
def set_current(index):
    """
    Set current active device.

    :param index: index of initialized device instance
    :return: None
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
    Execute shell command on device. Android only.

    :param cmd: command line, e.g. "ls /data/local/tmp"
    :return: output of shell cmd
    """
    return G.DEVICE.shell(cmd)


@logwrap
@on_platform(["Android", "IOS"])
def start_app(package, activity=None):
    """
    Start app on device.

    :param package: package name of the app, e.g. "com.netease.my"
    :param activity: activity to start, default as None to start main activity
    :return: None
    """
    G.DEVICE.start_app(package, activity)


@logwrap
@on_platform(["Android", "IOS"])
def stop_app(package):
    """
    Stop app on device.

    :param package: package name of the app, same with `start_app`
    :return: None
    """
    G.DEVICE.stop_app(package)


@logwrap
@on_platform(["Android", "IOS"])
def clear_app(package):
    """
    Clear data of an app on device.

    :param package: package name of the app, same with `start_app`
    :return: None
    """
    G.DEVICE.clear_app(package)


@logwrap
@on_platform(["Android", "IOS"])
def install(filepath):
    """
    Install app on device.

    :param filepath: filepath of the app on host machine
    :return: None
    """
    return G.DEVICE.install_app(filepath)


@logwrap
@on_platform(["Android", "IOS"])
def uninstall(package):
    """
    Uninstall app on device.

    :param package: package name of the app, same with `start_app`
    :return: None
    """
    return G.DEVICE.uninstall_app(package)


@logwrap
def snapshot(filename, msg=""):
    """
    Get the screenshot of the device and save to file.

    :param filename: filename to save the screenshot. Save to ST.LOG_DIR if it's a relative path
    :param msg: message of the screenshot, will be displayed in the report
    :return: None
    """
    if not os.path.isabs(filename):
        filepath = os.path.join(ST.LOG_DIR, ST.SCREEN_DIR, filename)
    else:
        filepath = filename
    G.DEVICE.snapshot(filepath)


@logwrap
@on_platform(["Android", "IOS"])
def wake():
    """
    Wake up and unlock the device. May not work on some models.

    :return: None
    """
    G.DEVICE.wake()


@logwrap
@on_platform(["Android", "IOS"])
def home():
    """
    Return to the home screen of the device.

    :return: None
    """
    G.DEVICE.home()


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def touch(v, **kwargs):
    """
    Touch on device screen.

    :param v: target to touch, either a Template instance or absolute coordinates (x, y)
    :param kwargs: platform specific kwargs, please refer to corresponding docs
    :return: None
    """
    if isinstance(v, Template):
        try:
            pos = loop_find(v, timeout=ST.FIND_TIMEOUT)
        except TargetNotFoundError:
            raise
    else:
        pos = v

    G.DEVICE.touch(pos, **kwargs)
    delay_after_operation()


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def swipe(v1, v2=None, vector=None, **kwargs):
    """
    Swipe on device screen.

    two way of assigning the params:
    1. swipe(v1, v2)   swipe from v1 to v2
    2. swipe(v1, vector) swipe starts at v1 and move along the vector.
    :param v1: start point of swipe, either a Template instance of absolute coordinates
    :param v2: end point of swipe, either a Template instance of absolute coordinates
    :param vector: vector of swipe action, either absolute coordinates (x, y) or percentage of screen e.g.(0.5, 0.5)
    :param kwargs: platform specific kwargs, please refer to corresponding docs
    :return: None

    滑动，共有2种参数方式：
       1. swipe(v1, v2) v1/v2分别是起始点和终止点，可以是(x,y)坐标或者是图片
       2. swipe(v1, vector) v1是起始点，vector是滑动向量，向量数值小于1会被当作屏幕百分比，否则是坐标
    """
    if isinstance(v1, Template):
        pos1 = loop_find(v1, timeout=ST.FIND_TIMEOUT)
    else:
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
        raise Exception("no enouph params for swipe")

    G.DEVICE.swipe(pos1, pos2, **kwargs)
    delay_after_operation()


@logwrap
@on_platform(["Android"])
def pinch(in_or_out='in', center=None, percent=0.5):
    """
    Pinch on device screen. Android Only.

    :param in_or_out: pinch in or pinch out, enum in ["in", "out"]
    :param center: center of pinch action, default as None to be center of screen
    :param percent: percentage of screen of pinch action, default to be 0.5
    :return: None
    """
    G.DEVICE.pinch(in_or_out=in_or_out, center=center, percent=percent)
    delay_after_operation()


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def keyevent(keyname, **kwargs):
    """
    Input keyboard event on device.

    :param keyname: platform specific keyname
    :param kwargs: platform specific kwargs
    :return: None
    """
    G.DEVICE.keyevent(keyname, **kwargs)
    delay_after_operation()


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def text(text, enter=True):
    """
    Input text on device.

    text input widget must be active first.
    :param text: text to input, unicode supported
    :param enter: input keyevent Enter after text input
    :return: None
    """
    """
        enter: 输入后执行enter操作
    """
    G.DEVICE.text(text, enter=enter)
    delay_after_operation()


@logwrap
def sleep(secs=1.0):
    """
    time.sleep, will be displayed in report.

    :param secs: seconds to sleep
    :return: None
    """
    time.sleep(secs)


@logwrap
def wait(v, timeout=None, interval=0.5, intervalfunc=None):
    """
    Wait for Template on device screen.

    :param v: target to wait, instance of Template
    :param timeout: timeout of wait, default as None to be ST.FIND_TIMEOUT
    :param interval: interval seconds after cv match when waiting
    :param intervalfunc: interval function to be called after each cv match when target not found
    :return: coordinates of the target found. raise TargetNotFoundError after timeout
    """
    timeout = timeout or ST.FIND_TIMEOUT
    pos = loop_find(v, timeout=timeout, interval=interval, intervalfunc=intervalfunc)
    return pos


@logwrap
def exists(v):
    """
    Return if the target exists on device screen.

    :param v: target to find
    :return: False if not exists else coordinates of target
    """
    try:
        pos = loop_find(v, timeout=ST.FIND_TIMEOUT_TMP)
        return pos
    except TargetNotFoundError:
        return False


@logwrap
def find_all(v):
    """
    Find all pos of the target on device screen.

    :param v: target to find
    :return: list of coordinates, [(x, y), (x1, y1), ...]
    """
    screen = G.DEVICE.snapshot()
    return cv_match_all(screen, v)


"""
Assertions
"""


@logwrap
def assert_exists(v, msg=""):
    """
    Assert target exists on device screen.

    :param v: target to find
    :param msg: message of assertion, will be displayed in the report
    :return: coordinates of the target found. raise AssertionError if assertion failed
    """
    try:
        pos = loop_find(v, timeout=ST.FIND_TIMEOUT, threshold=ST.THRESHOLD_STRICT)
        return pos
    except TargetNotFoundError:
        raise AssertionError("%s does not exist in screen, message: %s" % (v, msg))


@logwrap
def assert_not_exists(v, msg=""):
    """
    Assert target does not exist on device screen.

    :param v: target to find
    :param msg: message of assertion, will be displayed in the report
    :return: None. raise AssertionError if assertion failed
    """
    try:
        pos = loop_find(v, timeout=ST.FIND_TIMEOUT_TMP)
        raise AssertionError("%s exists unexpectedly at pos: %s, message: %s" % (v, pos, msg))
    except TargetNotFoundError:
        pass


@logwrap
def assert_equal(first, second, msg=""):
    """
    Assert first and second are equal.

    :param first: first value
    :param second: second value
    :param msg: message of assertion, will be displayed in the report
    :return: None, raise AssertionError if assertion failed
    """
    if first != second:
        raise AssertionError("%s and %s are not equal, message: %s" % (first, second, msg))


@logwrap
def assert_not_equal(first, second, msg=""):
    """
    Assert first and second are not equal.

    :param first: first value
    :param second: second value
    :param msg: message of assertion, will be displayed in the report
    :return: None, raise AssertionError if assertion failed
    """
    if first == second:
        raise AssertionError("%s and %s are equal, message: %s" % (first, second, msg))
