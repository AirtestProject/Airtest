# -*- coding: utf-8 -*-
"""
    api definition
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
    """用uri连接设备, eg:
    android://adbhost:adbport/serialno?p1=v1
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
    return G.DEVICE


@on_platform(["Android", "Windows", "IOS"])
def set_current(index):
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
    return G.DEVICE.shell(cmd)


@logwrap
@on_platform(["Android", "IOS"])
def start_app(package, activity=None):
    G.DEVICE.start_app(package, activity)


@logwrap
@on_platform(["Android", "IOS"])
def stop_app(package):
    G.DEVICE.stop_app(package)


@logwrap
@on_platform(["Android", "IOS"])
def clear_app(package):
    G.DEVICE.clear_app(package)


@logwrap
@on_platform(["Android", "IOS"])
def install(filepath):
    return G.DEVICE.install_app(filepath)


@logwrap
@on_platform(["Android", "IOS"])
def uninstall(package):
    return G.DEVICE.uninstall_app(package)


@logwrap
def snapshot(filename, msg=""):
    """capture device screen and save it into file."""
    if not os.path.isabs(filename):
        filepath = os.path.join(ST.LOG_DIR, ST.SCREEN_DIR, filename)
    else:
        filepath = filename
    G.DEVICE.snapshot(filepath)


@logwrap
@on_platform(["Android", "IOS"])
def wake():
    G.DEVICE.wake()


@logwrap
@on_platform(["Android", "IOS"])
def home():
    G.DEVICE.home()


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def touch(v, timeout=0, **kwargs):
    timeout = timeout or ST.FIND_TIMEOUT
    if isinstance(v, Template):
        try:
            pos = loop_find(v, timeout=timeout)
        except TargetNotFoundError:
            raise
    else:
        pos = v

    G.DEVICE.touch(pos, **kwargs)
    delay_after_operation()


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def swipe(v1, v2=None, vector=None, timeout=0, **kwargs):
    """滑动，共有2种参数方式：
       1. swipe(v1, v2) v1/v2分别是起始点和终止点，可以是(x,y)坐标或者是图片
       2. swipe(v1, vector) v1是起始点，vector是滑动向量，向量数值小于1会被当作屏幕百分比，否则是坐标
    """
    if isinstance(v1, Template):
        timeout = timeout or ST.FIND_TIMEOUT
        pos1 = loop_find(v1, timeout=timeout)
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
    G.DEVICE.pinch(in_or_out=in_or_out, center=center, percent=percent)
    delay_after_operation()


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def keyevent(keyname, **kwargs):
    """模拟设备的按键功能.
    """
    G.DEVICE.keyevent(keyname, **kwargs)
    delay_after_operation()


@logwrap
@on_platform(["Android", "Windows", "IOS"])
def text(text, enter=True):
    """
        输入文字
        enter: 输入后执行enter操作
    """
    G.DEVICE.text(text, enter=enter)
    delay_after_operation()


@logwrap
def sleep(secs=1.0):
    time.sleep(secs)


@logwrap
def wait(v, timeout=0, interval=0.5, intervalfunc=None):
    timeout = timeout or ST.FIND_TIMEOUT
    pos = loop_find(v, timeout=timeout, interval=interval, intervalfunc=intervalfunc)
    return pos


@logwrap
def exists(v, timeout=0):
    timeout = timeout or ST.FIND_TIMEOUT_TMP
    try:
        pos = loop_find(v, timeout=timeout)
        return pos
    except TargetNotFoundError:
        return False


@logwrap
def find_all(v):
    screen = G.DEVICE.snapshot()
    return cv_match_all(screen, v)


"""
Assertions
"""


@logwrap
def assert_exists(v, msg="", timeout=0):
    timeout = timeout or ST.FIND_TIMEOUT
    try:
        pos = loop_find(v, timeout=timeout, threshold=ST.THRESHOLD_STRICT)
        return pos
    except TargetNotFoundError:
        raise AssertionError("%s does not exist in screen" % v)


@logwrap
def assert_not_exists(v, msg="", timeout=0):
    timeout = timeout or ST.FIND_TIMEOUT_TMP
    try:
        pos = loop_find(v, timeout=timeout)
        raise AssertionError("%s exists unexpectedly at pos: %s" % (v, pos))
    except TargetNotFoundError:
        pass


@logwrap
def assert_equal(first, second, msg=""):
    if first != second:
        raise AssertionError("%s and %s are not equal" % (first, second))


@logwrap
def assert_not_equal(first, second, msg=""):
    if first == second:
        raise AssertionError("%s and %s are equal" % (first, second))
