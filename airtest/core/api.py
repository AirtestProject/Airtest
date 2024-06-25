# -*- coding: utf-8 -*-
"""
This module contains the Airtest Core APIs.
"""
import os
import time

from airtest.core.cv import Template, loop_find, try_log_screen
from airtest.core.error import TargetNotFoundError
from airtest.core.settings import Settings as ST
from airtest.utils.compat import script_log_dir
from airtest.utils.snippet import parse_device_uri
from airtest.core.helper import (G, delay_after_operation, import_device_cls,
                                 logwrap, set_logdir, using, log)
# Assertions
from airtest.core.assertions import (assert_exists, assert_not_exists, assert_equal, assert_not_equal,  # noqa
                                        assert_true, assert_false, assert_is, assert_is_not,
                                        assert_is_none, assert_is_not_none, assert_in, assert_not_in,
                                        assert_is_instance, assert_not_is_instance
                                     )


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
    :Example:

        >>> init_device(platform="Android",uuid="SJE5T17B17", cap_method="JAVACAP")
        >>> init_device(platform="Windows",uuid="123456")
    """
    cls = import_device_cls(platform)
    dev = cls(uuid, **kwargs)
    # Add device instance in G and set as current device.
    G.add_device(dev)
    return dev


@logwrap
def connect_device(uri):
    """
    Initialize device with uri, and set as current device.

    :param uri: an URI where to connect to device, e.g. `android://adbhost:adbport/serialno?param=value&param2=value2`
    :return: device instance
    :Example:

        >>> connect_device("Android:///")  # local adb device using default params
        >>> # local device with serial number SJE5T17B17 and custom params
        >>> connect_device("Android:///SJE5T17B17?cap_method=javacap&touch_method=adb")
        >>> # remote device using custom params Android://adbhost:adbport/serialno
        >>> connect_device("Android://127.0.0.1:5037/10.254.60.1:5555")
        >>> connect_device("Android://127.0.0.1:5037/10.234.60.1:5555?name=serialnumber")  # add serialno to params
        >>> connect_device("Windows:///")  # connect to the desktop
        >>> connect_device("Windows:///123456")  # Connect to the window with handle 123456
        >>> connect_device("windows:///?title_re='.*explorer.*'")  # Connect to the window that name include "explorer"
        >>> connect_device("Windows:///123456?foreground=False")  # Connect to the window without setting it foreground
        >>> connect_device("iOS:///127.0.0.1:8100")  # iOS device
        >>> connect_device("iOS:///http://localhost:8100/?mjpeg_port=9100")  # iOS with mjpeg port
        >>> connect_device("iOS:///http://localhost:8100/?mjpeg_port=9100&&udid=00008020-001270842E88002E")  # iOS with mjpeg port and udid
        >>> connect_device("iOS:///http://localhost:8100/?mjpeg_port=9100&&uuid=00008020-001270842E88002E")  # udid/uuid/serialno are all ok

    """
    platform, uuid, params = parse_device_uri(uri)
    dev = init_device(platform, uuid, **params)
    return dev


def device():
    """
    Return the current active device.

    :return: current device instance
    :Example:
        >>> dev = device()
        >>> dev.touch((100, 100))
    """
    return G.DEVICE


def set_current(idx):
    """
    Set current active device.

    :param idx: uuid or index of initialized device instance
    :raise IndexError: raised when device idx is not found
    :return: None
    :platforms: Android, iOS, Windows
    :Example:
        >>> # switch to the first phone currently connected
        >>> set_current(0)
        >>> # switch to the phone with serial number serialno1
        >>> set_current("serialno1")

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


def auto_setup(basedir=None, devices=None, logdir=None, project_root=None, compress=None):
    """
    Auto setup running env and try connect android device if not device connected.

    :param basedir: basedir of script, __file__ is also acceptable.
    :param devices: connect_device uri in list.
    :param logdir: log dir for script report, default is None for no log, set to ``True`` for ``<basedir>/log``.
    :param project_root: project root dir for `using` api.
    :param compress: The compression rate of the screenshot image, integer in range [1, 99], default is 10
    :Example:
        >>> auto_setup(__file__)
        >>> auto_setup(__file__, devices=["Android://127.0.0.1:5037/SJE5T17B17"],
        ...             logdir=True, project_root=r"D:\\test\\logs", compress=90)
    """
    if basedir:
        if os.path.isfile(basedir):
            basedir = os.path.dirname(basedir)
        if basedir not in G.BASEDIR:
            G.BASEDIR.append(basedir)
    if logdir:
        logdir = script_log_dir(basedir, logdir)
        set_logdir(logdir)
    if devices:
        for dev in devices:
            connect_device(dev)
    if project_root:
        ST.PROJECT_ROOT = project_root
    if compress:
        ST.SNAPSHOT_QUALITY = compress


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
    :Example:
        >>> # Execute commands on the current device adb shell ls
        >>> print(shell("ls"))

        >>> # Execute adb instructions for specific devices
        >>> dev = connect_device("Android:///device1")
        >>> dev.shell("ls")

        >>> # Switch to a device and execute the adb command
        >>> set_current(0)
        >>> shell("ls")
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
    :Example:
        >>> start_app("com.netease.cloudmusic")
        >>> start_app("com.apple.mobilesafari")  # on iOS
    """
    G.DEVICE.start_app(package, activity)


@logwrap
def stop_app(package):
    """
    Stop the target application on device

    :param package: name of the package to stop, see also `start_app`
    :return: None
    :platforms: Android, iOS
    :Example:
        >>> stop_app("com.netease.cloudmusic")
    """
    G.DEVICE.stop_app(package)


@logwrap
def clear_app(package):
    """
    Clear data of the target application on device

    :param package: name of the package,  see also `start_app`
    :return: None
    :platforms: Android
    :Example:
        >>> clear_app("com.netease.cloudmusic")
    """
    G.DEVICE.clear_app(package)


@logwrap
def install(filepath, **kwargs):
    """
    Install application on device

    :param filepath: the path to file to be installed on target device
    :param kwargs: platform specific `kwargs`, please refer to corresponding docs
    :return: None
    :platforms: Android, iOS
    :Example:
        >>> install(r"D:\demo\test.apk")  # install Android apk
        >>> # adb install -r -t D:\\demo\\test.apk
        >>> install(r"D:\demo\test.apk", install_options=["-r", "-t"])

        >>> install(r"D:\demo\test.ipa") # install iOS ipa
        >>> install("http://www.example.com/test.ipa") # install iOS ipa from url

    """
    return G.DEVICE.install_app(filepath, **kwargs)


@logwrap
def uninstall(package):
    """
    Uninstall application on device

    :param package: name of the package, see also `start_app`
    :return: None
    :platforms: Android, iOS
    :Example:
        >>> uninstall("com.netease.cloudmusic")
    """
    return G.DEVICE.uninstall_app(package)


@logwrap
def snapshot(filename=None, msg="", quality=None, max_size=None):
    """
    Take the screenshot of the target device and save it to the file.

    :param filename: name of the file where to save the screenshot. If the relative path is provided, the default
                     location is ``ST.LOG_DIR``
    :param msg: short description for screenshot, it will be recorded in the report
    :param quality: The image quality, integer in range [1, 99], default is 10
    :param max_size: the maximum size of the picture, e.g 1200
    :return: {"screen": filename, "resolution": resolution of the screen} or None
    :platforms: Android, iOS, Windows
    :Example:
        >>> snapshot(msg="index")
        >>> # save the screenshot to test.jpg
        >>> snapshot(filename="test.png", msg="test")

        The quality and size of the screenshot can be set::

        >>> # Set the screenshot quality to 30
        >>> ST.SNAPSHOT_QUALITY = 30
        >>> # Set the screenshot size not to exceed 600*600
        >>> # if not set, the default size is the original image size
        >>> ST.IMAGE_MAXSIZE = 600
        >>> # The quality of the screenshot is 30, and the size does not exceed 600*600
        >>> touch((100, 100))
        >>> # The quality of the screenshot of this sentence is 90
        >>> snapshot(filename="test.png", msg="test", quality=90)
        >>> # The quality of the screenshot is 90, and the size does not exceed 1200*1200
        >>> snapshot(filename="test2.png", msg="test", quality=90, max_size=1200)

    """
    if not quality:
        quality = ST.SNAPSHOT_QUALITY
    if not max_size and ST.IMAGE_MAXSIZE:
        max_size = ST.IMAGE_MAXSIZE
    if filename:
        if not os.path.isabs(filename):
            logdir = ST.LOG_DIR or "."
            filename = os.path.join(logdir, filename)
        screen = G.DEVICE.snapshot(filename, quality=quality, max_size=max_size)
        return try_log_screen(screen, quality=quality, max_size=max_size)
    else:
        return try_log_screen(quality=quality, max_size=max_size)


@logwrap
def wake():
    """
    Wake up and unlock the target device

    :return: None
    :platforms: Android
    :Example:
        >>> wake()

    .. note:: Might not work on some models
    """
    G.DEVICE.wake()


@logwrap
def home():
    """
    Return to the home screen of the target device.

    :return: None
    :platforms: Android, iOS
    :Example:
        >>> home()
    """
    G.DEVICE.home()


@logwrap
def touch(v, times=1, **kwargs):
    """
    Perform the touch action on the device screen

    :param v: target to touch, either a ``Template`` instance or absolute coordinates (x, y)
    :param times: how many touches to be performed
    :param kwargs: platform specific `kwargs`, please refer to corresponding docs
    :return: finial position to be clicked, e.g. (100, 100)
    :platforms: Android, Windows, iOS
    :Example:
        Click absolute coordinates::

        >>> touch((100, 100))

        Click the center of the picture(Template object)::

        >>> touch(Template(r"tpl1606730579419.png", target_pos=5))

        Click on relative coordinates, for example, click on the center of the screen::

        >>> touch((0.5, 0.5))

        Click 2 times::

        >>> touch((100, 100), times=2)

        Under Android and Windows platforms, you can set the click duration::

        >>> touch((100, 100), duration=2)

        Right click(Windows)::

        >>> touch((100, 100), right_click=True)

    """
    if isinstance(v, Template):
        pos = loop_find(v, timeout=ST.FIND_TIMEOUT)
    else:
        try_log_screen()
        pos = v
    for _ in range(times):
        # If pos is a relative coordinate, return the converted click coordinates.
        # iOS may all use vertical screen coordinates, so coordinates will not be returned.
        pos = G.DEVICE.touch(pos, **kwargs) or pos
        time.sleep(0.05)
    delay_after_operation()
    return pos

click = touch  # click is alias of touch


@logwrap
def double_click(v):
    """
    Perform double click

    :param v: target to touch, either a ``Template`` instance or absolute coordinates (x, y)
    :return: finial position to be clicked
    :Example:

        >>> double_click((100, 100))
        >>> double_click(Template(r"tpl1606730579419.png"))
    """
    if isinstance(v, Template):
        pos = loop_find(v, timeout=ST.FIND_TIMEOUT)
    else:
        try_log_screen()
        pos = v
    pos = G.DEVICE.double_click(pos) or pos
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
    :Example:

        >>> swipe(Template(r"tpl1606814865574.png"), vector=[-0.0316, -0.3311])
        >>> swipe((100, 100), (200, 200))

        Custom swiping duration and number of steps(Android and iOS)::

        >>> # swiping lasts for 1 second, divided into 6 steps
        >>> swipe((100, 100), (200, 200), duration=1, steps=6)

        Use relative coordinates to swipe, such as swiping from the center right to the left of the screen::

        >>> swipe((0.7, 0.5), (0.2, 0.5))

    """
    if isinstance(v1, Template):
        try:
            pos1 = loop_find(v1, timeout=ST.FIND_TIMEOUT)
        except TargetNotFoundError:
            # 如果由图1滑向图2，图1找不到，会导致图2的文件路径未被初始化，可能在报告中不能正确显示
            if v2 and isinstance(v2, Template):
                v2.filepath
            raise
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

    pos1, pos2 = G.DEVICE.swipe(pos1, pos2, **kwargs) or (pos1, pos2)
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
    :Example:

        Pinch in the center of the screen with two fingers::

        >>> pinch()

        Take (100,100) as the center and slide out with two fingers::

        >>> pinch('out', center=(100, 100))
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
    :Example:

        * ``Android``: it is equivalent to executing ``adb shell input keyevent KEYNAME`` ::

        >>> keyevent("HOME")
        >>> # The constant corresponding to the home key is 3
        >>> keyevent("3")  # same as keyevent("HOME")
        >>> keyevent("BACK")
        >>> keyevent("KEYCODE_DEL")

        .. seealso::

           Module :py:mod:`airtest.core.android.adb.ADB.keyevent`
              Equivalent to calling the ``android.adb.keyevent()``

           `Android Keyevent <https://developer.android.com/reference/android/view/KeyEvent#constants_1>`_
              Documentation for more ``Android.KeyEvent``

        * ``Windows``: Use ``pywinauto.keyboard`` module for key input::

        >>> keyevent("{DEL}")
        >>> keyevent("%{F4}")  # close an active window with Alt+F4

        .. seealso::

            Module :py:mod:`airtest.core.win.win.Windows.keyevent`

            `pywinauto.keyboard <https://pywinauto.readthedocs.io/en/latest/code/pywinauto.keyboard.html>`_
                Documentation for ``pywinauto.keyboard``

        * ``iOS``: Only supports home/volumeUp/volumeDown::

        >>> keyevent("HOME")
        >>> keyevent("volumeUp")

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
    :Example:

        >>> text("test")
        >>> text("test", enter=False)

        On Android, sometimes you need to click the search button after typing::

        >>> text("test", search=True)

        .. seealso::

            Module :py:mod:`airtest.core.android.ime.YosemiteIme.code`

            If you want to enter other keys on the keyboard, you can use the interface::

                >>> text("test")
                >>> device().yosemite_ime.code("3")  # 3 = IME_ACTION_SEARCH

            Ref: `Editor Action Code <http://developer.android.com/reference/android/view/inputmethod/EditorInfo.html>`_

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
    :Example:

        >>> sleep(1)
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
    :Example:

        >>> wait(Template(r"tpl1606821804906.png"))  # timeout after ST.FIND_TIMEOUT
        >>> # find Template every 3 seconds, timeout after 120 seconds
        >>> wait(Template(r"tpl1606821804906.png"), timeout=120, interval=3)

        You can specify a callback function every time the search target fails::

        >>> def notfound():
        >>>     print("No target found")
        >>> wait(Template(r"tpl1607510661400.png"), intervalfunc=notfound)

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
    :Example:

        >>> if exists(Template(r"tpl1606822430589.png")):
        >>>     touch(Template(r"tpl1606822430589.png"))

        Since ``exists()`` will return the coordinates, we can directly click on this return value to reduce one image search::

        >>> pos = exists(Template(r"tpl1606822430589.png"))
        >>> if pos:
        >>>     touch(pos)

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
    :return: list of results, [{'result': (x, y),
                                'rectangle': ( (left_top, left_bottom, right_bottom, right_top) ),
                                'confidence': 0.9},
                                ...]
    :platforms: Android, Windows, iOS
    :Example:

        >>> find_all(Template(r"tpl1607511235111.png"))
        [{'result': (218, 468), 'rectangle': ((149, 440), (149, 496), (288, 496), (288, 440)),
        'confidence': 0.9999996423721313}]

    """
    screen = G.DEVICE.snapshot(quality=ST.SNAPSHOT_QUALITY)
    return v.match_all_in(screen)


@logwrap
def get_clipboard(*args, **kwargs):
    """
    Get the content from the clipboard.

    :return: str
    :platforms: Android, iOS, Windows
    :Example:

        >>> text = get_clipboard()  # Android or local iOS
        >>> print(text)

        >>> # When the iOS device is a remote device, or more than one wda is installed on the device, you need to specify the wda_bundle_id
        >>> text = get_clipboard(wda_bundle_id="com.WebDriverAgentRunner.xctrunner")
        >>> print(text)

    """
    return G.DEVICE.get_clipboard(*args, **kwargs)


@logwrap
def set_clipboard(content, *args, **kwargs):
    """
    Set the content from the clipboard.

    :param content: str
    :return: None
    :platforms: Android, iOS, Windows
    :Example:

        >>> set_clipboard("content")  # Android or local iOS
        >>> print(get_clipboard())

        >>> # When the iOS device is a remote device, or more than one wda is installed on the device, you need to specify the wda_bundle_id
        >>> set_clipboard("content", wda_bundle_id="com.WebDriverAgentRunner.xctrunner")

    """
    G.DEVICE.set_clipboard(content, *args, **kwargs)


@logwrap
def paste(*args, **kwargs):
    """
    Paste the content from the clipboard.

    :platforms: Android, iOS, Windows
    :return: None
    :Example:

        >>> set_clipboard("content")
        >>> paste()  # will paste "content" to the device

    """
    G.DEVICE.paste(*args, **kwargs)


@logwrap
def push(local, remote, *args, **kwargs):
    """
    Push file from local to remote

    :param local: local file path
    :param remote: remote file path
    :return: filename of the pushed file
    :platforms: Android, iOS
    :Example:

        Android::

            >>> connect_device("android:///")
            >>> push(r"D:\demo\test.text", "/data/local/tmp/test.text")


        iOS::

            >>> connect_device("iOS:///http+usbmux://udid")
            >>> push("test.png", "/DCIM/")  # push to the DCIM directory
            >>> push(r"D:\demo\test.text", "/Documents", bundle_id="com.apple.Keynote")  # push to the Documents directory of the Keynote app

    """
    return G.DEVICE.push(local, remote, *args, **kwargs)


@logwrap
def pull(remote, local, *args, **kwargs):
    """
    Pull file from remote to local

    :param remote: remote file path
    :param local: local file path
    :return: filename of the pulled file
    :platforms: Android, iOS
    :Example:

        Android::

            >>> connect_device("android:///")
            >>> pull("/data/local/tmp/test.txt", r"D:\demo\test.txt")

        iOS::

            >>> connect_device("iOS:///http+usbmux://udid")
            >>> pull("/DCIM/test.png", r"D:\demo\test.png")
            >>> pull("/Documents/test.key", r"D:\demo\test.key", bundle_id="com.apple.Keynote")

    """
    return G.DEVICE.pull(remote, local, *args, **kwargs)

"""
Assertions: see airtest/core/assertions.py
"""
