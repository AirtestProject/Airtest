# -*- coding: utf-8 -*-
import functools
import os
import six
import sys
import time
import inspect
import traceback
from airtest.core.settings import Settings as ST
from airtest.utils.logger import get_logger
from airtest.utils.logwraper import Logwrap, AirtestLogger
from airtest.core.error import NoDeviceError


class DeviceMetaProperty(type):

    @property
    def DEVICE(cls):
        if G._DEVICE is None:
            raise NoDeviceError("No devices added.")
        return G._DEVICE

    @DEVICE.setter
    def DEVICE(cls, dev):
        cls._DEVICE = dev


class G(object, metaclass=DeviceMetaProperty):
    """Represent the globals variables"""
    BASEDIR = []
    LOGGER = AirtestLogger(None)
    LOGGING = get_logger("airtest.core.api")
    SCREEN = None
    _DEVICE = None
    DEVICE_LIST = []
    RECENT_CAPTURE = None
    RECENT_CAPTURE_PATH = None
    CUSTOM_DEVICES = {}

    @classmethod
    def add_device(cls, dev):
        """
        Add device instance in G and set as current device.

        Examples:
            G.add_device(Android())

        Args:
            dev: device to init

        Returns:
            None

        """
        for index, instance in enumerate(cls.DEVICE_LIST):
            if dev.uuid == instance.uuid:
                cls.LOGGING.warn("Device:%s updated %s -> %s" % (dev.uuid, instance, dev))
                cls.DEVICE_LIST[index] = dev
                cls.DEVICE = dev
                break
        else:
            cls.DEVICE = dev
            cls.DEVICE_LIST.append(dev)

    @classmethod
    def register_custom_device(cls, device_cls):
        cls.CUSTOM_DEVICES[device_cls.__name__.lower()] = device_cls


"""
helper functions
"""


def set_logdir(dirpath):
    """set log dir for logfile and screenshots.

    Args:
        dirpath: directory to save logfile and screenshots

    Returns:

    """
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    ST.LOG_DIR = dirpath
    G.LOGGER.set_logfile(os.path.join(ST.LOG_DIR, ST.LOG_FILE))


def log(arg, timestamp=None, desc="", snapshot=False):
    """
    Insert user log, will be displayed in Html report.

    Args:
        arg: log message or Exception object
        timestamp: the timestamp of the log, default is time.time()
        desc: description of log, default is arg.class.__name__
        snapshot: whether to take a screenshot, default is False

    Returns:
        None

    Examples:
        >>> log("hello world", snapshot=True)
        >>> log({"key": "value"}, timestamp=time.time(), desc="log dict")
        >>> try:
                1/0
            except Exception as e:
                log(e)

    """
    from airtest.core.cv import try_log_screen
    if G.LOGGER:
        depth = 0
        if snapshot:
            # 如果指定了snapshot参数，强制保存一张图片
            save_image = ST.SAVE_IMAGE
            ST.SAVE_IMAGE = True
            try:
                try_log_screen(depth=2)
            except AttributeError:
                # if G.DEVICE is None
                pass
            else:
                depth = 1
            finally:
                ST.SAVE_IMAGE = save_image
        if isinstance(arg, Exception):
            if hasattr(arg, "__traceback__"):
                # in PY3, arg.__traceback__ is traceback object
                trace_msg = ''.join(traceback.format_exception(type(arg), arg, arg.__traceback__))
            else:
                trace_msg = arg.message  # PY2
            G.LOGGER.log("info", {
                    "name": desc or arg.__class__.__name__,
                    "traceback": trace_msg,
                }, depth=depth, timestamp=timestamp)
            G.LOGGING.error(trace_msg)
        elif isinstance(arg, six.string_types):
            # 普通文本log内容放在"log"里，如果有trace内容放在"traceback"里
            # 在报告中，假如"traceback"有内容，将会被识别为报错，这个步骤会被判定为不通过
            G.LOGGER.log("info", {"name": desc or arg, "traceback": None, "log": arg}, depth=depth, timestamp=timestamp)
            G.LOGGING.info(arg)
        else:
            G.LOGGER.log("info", {"name": desc or repr(arg), "traceback": None, "log": repr(arg)}, depth=depth,
                         timestamp=timestamp)
            G.LOGGING.info(repr(arg))


def logwrap(f):
    """
    A decorator used to add the current function to the airtest log,
    which can be seen on the report html page

    Args:
        f: The function being decorated

    Returns:
        The decorated function

    Examples:

        Add foo() to the airtest report html page::

            @logwrap
            def foo():
                pass

    """
    return Logwrap(f, G.LOGGER)


def device_platform(device=None):
    if not device:
        device = G.DEVICE
    return device.__class__.__name__


def using(path):
    """
    Import a function from another .air script, the ``using`` interface will find the image path from the imported function.

    Args:
        path: relative or absolute. This function transforms a given relative path, searching in the project root, \
        current working directory, or the current script's directory, into an absolute path \
         and adds it to the sys.path and G.BASEDIR.

    Returns:

    Examples:

        Suppose our project structure is as follows::

            demo/
                foo/
                    bar.air
                baz.air
                main.py

        If we want to reference `foo/bar.air` and `baz.air` in main.py, we can set the project root path to ``ST.PROJECT_ROOT``, \
        or make sure the project root path is the `current working directory`. We can write::

            # main.py
            from airtest.core.api import *
            ST.PROJECT_ROOT = r"D:\demo"  # This line can be ignored if it is the current working directory
            using("foo/bar.air")
            using("baz.air")

        If we want to reference `baz.air` in `foo/bar.air`, we can write::

            # foo/bar.air
            from airtest.core.api import *
            using("../baz.air")

    """
    if not os.path.isabs(path):
        # if path is relative, try to find it in project root
        # e.g. path: PROJECT_ROOT/foo/bar.air, using("foo/bar.air")
        if os.path.exists(os.path.join(ST.PROJECT_ROOT, path)):
            path = os.path.join(ST.PROJECT_ROOT, path)
        # try to find it in current working directory
        # e.g. path: CWD/foo/bar.air, using("foo/bar.air")
        elif os.path.exists(os.path.join(os.getcwd(), path)):
            path = os.path.abspath(os.path.join(os.getcwd(), path))
        else:
            # try to find it relative to the current script
            # e.g. path: foo/bar1.air, foo/bar2.air, in bar1.air: using("../bar2.air")
            script_path = os.path.abspath(inspect.stack()[1].filename)
            script_dir = os.path.dirname(script_path)
            if os.path.exists(os.path.join(script_dir, path)):
                path = os.path.abspath(os.path.join(script_dir, path))
            elif os.path.exists(os.path.join(script_path, path)):
                path = os.path.abspath(os.path.join(script_path, path))

    G.LOGGING.debug("using path: %s", path)
    if path not in sys.path:
        sys.path.append(path)
    G.BASEDIR.append(path)


def import_device_cls(platform):
    """lazy import device class"""
    platform = platform.lower()
    if platform in G.CUSTOM_DEVICES:
        cls = G.CUSTOM_DEVICES[platform]
    elif platform == "android":
        from airtest.core.android.android import Android as cls
    elif platform == "windows":
        from airtest.core.win.win import Windows as cls
    elif platform == "ios":
        from airtest.core.ios import IOS as cls
    elif platform == "linux":
        from airtest.core.linux.linux import Linux as cls
    else:
        raise RuntimeError("Unknown platform: %s" % platform)
    return cls


def delay_after_operation():
    time.sleep(ST.OPDELAY)
