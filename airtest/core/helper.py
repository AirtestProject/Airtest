# -*- coding: utf-8 -*-
import time
import sys
import os
import six
import traceback
from airtest.core.settings import Settings as ST
from airtest.utils.logwraper import Logwrap, AirtestLogger
from airtest.utils.logger import get_logger


class G(object):
    """Represent the globals variables"""
    BASEDIR = []
    LOGGER = AirtestLogger(None)
    LOGGING = get_logger("airtest.core.api")
    SCREEN = None
    DEVICE = None
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


def log(arg, timestamp=None, desc=""):
    """
    Insert user log, will be displayed in Html report.

    Args:
        arg: log message or Exception object
        timestamp: the timestamp of the log, default is time.time()
        desc: description of log, default is arg.class.__name__

    Returns:
        None

    Examples:
        >>> log("hello world")
        >>> log({"key": "value"}, timestamp=time.time(), desc="log dict")
        >>> try:
                1/0
            except Exception as e:
                log(e)

    """
    if G.LOGGER:
        if isinstance(arg, Exception):
            if hasattr(arg, "__traceback__"):
                # in PY3, arg.__traceback__ is traceback object
                trace_msg = ''.join(traceback.format_exception(type(arg), arg, arg.__traceback__))
            else:
                trace_msg = arg.message  # PY2
            G.LOGGER.log("info", {
                    "name": desc or arg.__class__.__name__,
                    "traceback": trace_msg,
                }, timestamp=timestamp)
        elif isinstance(arg, six.string_types):
            # 普通文本log内容放在"log"里，如果有trace内容放在"traceback"里
            # 在报告中，假如"traceback"有内容，将会被识别为报错，这个步骤会被判定为不通过
            G.LOGGER.log("info", {"name": desc or arg, "traceback": None, "log": arg}, 0, timestamp=timestamp)
        else:
            G.LOGGER.log("info", {"name": desc or repr(arg), "traceback": None, "log": repr(arg)}, 0,
                         timestamp=timestamp)


def logwrap(f):
    return Logwrap(f, G.LOGGER)


def device_platform(device=None):
    if not device:
        device = G.DEVICE
    return device.__class__.__name__


def using(path):
    if not os.path.isabs(path):
        abspath = os.path.join(ST.PROJECT_ROOT, path)
        if os.path.exists(abspath):
            path = abspath
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
        from airtest.core.ios.ios import IOS as cls
    elif platform == "linux":
        from airtest.core.linux.linux import Linux as cls
    else:
        raise RuntimeError("Unknown platform: %s" % platform)
    return cls


def delay_after_operation():
    time.sleep(ST.OPDELAY)
