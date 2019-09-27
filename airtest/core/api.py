# -*- coding: utf-8 -*-
"""
This module contains the Airtest Core APIs.
"""
import os
import time

from six.moves.urllib.parse import parse_qsl, urlparse

from airtest.core.cv import Template, loop_find, try_log_screen
from airtest.core.error import TargetNotFoundError
from airtest.core.settings import Settings as ST
from airtest.utils.compat import script_log_dir
from airtest.core.helper import (G, delay_after_operation, import_device_cls,
                                 logwrap, set_logdir, using, log)


"""
Device Setup APIs
"""


def init_device(platform="Android", uuid=None, **kwargs):
    """
    Initialize device if not yet, and set as current device.

    :param platform: Android, IOS or Windows
    :param uuid: uuid for target device, e.g. serialno for Android, handle for Windows, uuid for iOS
    :param kwargs: Optional platform specific keyword args, e.g. `cap_method=JAVACAP` for Android
    :return: device instance
    """
    cls = import_device_cls(platform)
    dev = cls(uuid, **kwargs)
    for index, instance in enumerate(G.DEVICE_LIST):
        if dev.uuid == instance.uuid:
            G.LOGGING.warn("Device:%s updated %s -> %s" % (dev.uuid, instance, dev))
            G.DEVICE_LIST[index] = dev
            break
    else:
        G.add_device(dev)
    return dev


def connect_device(uri):
    """
    Initialize device with uri, and set as current device.

    :param uri: an URI where to connect to device, e.g. `android://adbhost:adbport/serialno?param=value&param2=value2`
    :return: device instance
    :Example:
        * ``android:///`` # local adb device using default params
        * ``android://adbhost:adbport/1234566?cap_method=javacap&touch_method=adb``  # remote device using custom params
        * ``windows:///`` # local Windows application
        * ``ios:///`` # iOS device
    """
    d = urlparse(uri)
    platform = d.scheme
    host = d.netloc
    uuid = d.path.lstrip("/")
    params = dict(parse_qsl(d.query))
    if host:
        params["host"] = host.split(":")
    dev = init_device(platform, uuid, **params)
    return dev


def device():
    """
    Return the current active device.

    :return: current device instance
    """
    return G.DEVICE


def set_current(idx):
    """
    Set current active device.

    :param idx: uuid or index of initialized device instance
    :raise IndexError: raised when device idx is not found
    :return: None
    :platforms: Android, iOS, Windows
    """

    dev_dict = {dev.uuid: dev for dev in G.DEVICE_LIST}
    if idx in dev_dict:
        current_dev = dev_dict[idx]
    elif isinstance(idx, int) and idx < len(G.DEVICE_LIST):
        current_dev = G.DEVICE_LIST[idx]
    else:
        raise IndexError("device idx not found in: %s or %s" % (
            list(dev_dict.keys()), list(range(len(G.DEVICE_LIST)))))
    G.DEVICE = current_dev


def auto_setup(basedir=None, devices=None, logdir=None, project_root=None):
    """
    Auto setup running env and try connect android device if not device connected.

    :param basedir: basedir of script, __file__ is also acceptable.
    :param devices: connect_device uri in list.
    :param logdir: log dir for script report, default is None for no log, set to `True` for <basedir>/log.
    :param project_root: project root dir for `using` api.
    """
    if basedir:
        if os.path.isfile(basedir):
            basedir = os.path.dirname(basedir)
        if basedir not in G.BASEDIR:
            G.BASEDIR.append(basedir)
    if devices:
        for dev in devices:
            connect_device(dev)
    if logdir:
        logdir = script_log_dir(basedir, logdir)
        set_logdir(logdir)
    if project_root:
        ST.PROJECT_ROOT = project_root


"""
Device Operations
"""


@logwrap
def shell(cmd):
    """
    Start remote shell in the target device and execute the command

    :param cmd: command to be run on device, e.g. "ls /data/local/tmp"
    :return: the output of the shell cmd
    :platforms: Android
    """
    return G.DEVICE.shell(cmd)


@logwrap
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
def stop_app(package):
    """
    Stop the target application on device

    :param package: name of the package to stop, see also `start_app`
    :return: None
    :platforms: Android, iOS
    """
    G.DEVICE.stop_app(package)


@logwrap
def clear_app(package):
    """
    Clear data of the target application on device

    :param package: name of the package,  see also `start_app`
    :return: None
    :platforms: Android
    """
    G.DEVICE.clear_app(package)


@logwrap
def install(filepath, **kwargs):
    """
    Install application on device

    :param filepath: the path to file to be installed on target device
    :param kwargs: platform specific `kwargs`, please refer to corresponding docs
    :return: None
    :platforms: Android
    """
    return G.DEVICE.install_app(filepath, **kwargs)


@logwrap
def uninstall(package):
    """
    Uninstall application on device

    :param package: name of the package, see also `start_app`
    :return: None
    :platforms: Android
    """
    return G.DEVICE.uninstall_app(package)


@logwrap
def snapshot(filename=None, msg=""):
    """
    Take the screenshot of the target device and save it to the file.

    :param filename: name of the file where to save the screenshot. If the relative path is provided, the default
                     location is ``ST.LOG_DIR``
    :param msg: short description for screenshot, it will be recorded in the report
    :return: absolute path of the screenshot
    :platforms: Android, iOS, Windows
    """
    if filename:
        if not os.path.isabs(filename):
            logdir = ST.LOG_DIR or "."
            filename = os.path.join(logdir, filename)
        screen = G.DEVICE.snapshot(filename)
        return try_log_screen(screen)
    else:
        return try_log_screen()


@logwrap
def wake():
    """
    Wake up and unlock the target device

    :return: None
    :platforms: Android

    .. note:: Might not work on some models
    """
    G.DEVICE.wake()


@logwrap
def home():
    """
    Return to the home screen of the target device.

    :return: None
    :platforms: Android, iOS
    """
    G.DEVICE.home()


@logwrap
def touch(v, times=1, **kwargs):
    """
    Perform the touch action on the device screen

    :param v: target to touch, either a Template instance or absolute coordinates (x, y)
    :param times: how many touches to be performed
    :param kwargs: platform specific `kwargs`, please refer to corresponding docs
    :return: finial position to be clicked
    :platforms: Android, Windows, iOS
    """
    if isinstance(v, Template):
        pos = loop_find(v, timeout=ST.FIND_TIMEOUT)
    else:
        try_log_screen()
        pos = v
    for _ in range(times):
        G.DEVICE.touch(pos, **kwargs)
        time.sleep(0.05)
    delay_after_operation()
    return pos

click = touch  # click is alias of touch


@logwrap
def double_click(v):
    if isinstance(v, Template):
        pos = loop_find(v, timeout=ST.FIND_TIMEOUT)
    else:
        try_log_screen()
        pos = v
    G.DEVICE.double_click(pos)
    delay_after_operation()
    return pos


@logwrap
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
    :return: Origin position and target position
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
    return pos1, pos2


@logwrap
def pinch(in_or_out='in', center=None, percent=0.5):
    """
    Perform the pinch action on the device screen

    :param in_or_out: pinch in or pinch out, enum in ["in", "out"]
    :param center: center of pinch action, default as None which is the center of the screen
    :param percent: percentage of the screen of pinch action, default is 0.5
    :return: None
    :platforms: Android
    """
    try_log_screen()
    G.DEVICE.pinch(in_or_out=in_or_out, center=center, percent=percent)
    delay_after_operation()


@logwrap
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
def text(text, enter=True, **kwargs):
    """
    Input text on the target device. Text input widget must be active first.

    :param text: text to input, unicode is supported
    :param enter: input `Enter` keyevent after text input, default is True
    :return: None
    :platforms: Android, Windows, iOS
    """
    G.DEVICE.text(text, enter=enter, **kwargs)
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
