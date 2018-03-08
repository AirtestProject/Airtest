# -*- coding: utf-8 -*-
import functools
import shutil
import time
import os
from airtest.core.settings import Settings as ST
from airtest.utils.logwraper import Logwrap, AirtestLogger
from airtest.utils.logger import get_logger


class G(object):
    """Represent the globals variables"""
    BASEDIR = None
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

    And create dir at `dirpath/ST.SCREEN_DIR` for screenshots

    Args:
        dirpath: directory to save logfile and screenshots

    Returns:

    """
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    ST.LOG_DIR = dirpath
    G.LOGGER.set_logfile(os.path.join(ST.LOG_DIR, ST.LOG_FILE))


def log(tag, data, in_stack=True):
    if G.LOGGER:
        G.LOGGER.log(tag, data, in_stack)


def log_in_func(data):
    if G.LOGGER:
        G.LOGGER.extra_log.update(data)


def logwrap(f):
    return Logwrap(f, G.LOGGER)


def device_platform():
    return G.DEVICE.__class__.__name__


NATIVE_PFS = ["Android", "Windows", "IOS"]


def import_device_cls(platform):
    """lazy import device class"""
    platform = platform.lower()
    if platform in G.CUSTOM_DEVICES:
        cls = G.CUSTOM_DEVICES[platform]
    elif platform == "android":
        from .android import Android as cls
    elif platform == "windows":
        from .win import Windows as cls
    elif platform == "ios":
        from .ios import IOS as cls
    else:
        raise RuntimeError("Unknown platform: %s" % platform)
    return cls


def on_platform(platforms):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if G.DEVICE is None:
                raise RuntimeError("Device not connected yet.")
            pf = device_platform()
            if pf in NATIVE_PFS and pf not in platforms:
                raise NotImplementedError("Method not implememted on {}. required {}.".format(pf, platforms))
            r = f(*args, **kwargs)
            return r
        return wrapper
    return decorator


def delay_after_operation():
    time.sleep(ST.OPDELAY)
