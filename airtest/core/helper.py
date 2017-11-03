# -*- coding: utf-8 -*-
import functools
import time
from airtest.core.settings import Settings as ST
from airtest.utils.logwraper import Logwrap, AirtestLogger
from airtest.utils.logger import get_logger


class G(object):
    """Represent the globals variables"""
    BASEDIR = None
    LOGGER = AirtestLogger(None)
    LOGGING = get_logger("main")
    SCREEN = None
    DEVICE = None
    DEVICE_LIST = []
    RECENT_CAPTURE = None
    RECENT_CAPTURE_PATH = None

    @classmethod
    def add_device(cls, dev):
        """
        Initialize the device and adds global variables

        Examples:
            init_Device(Android())

        Args:
            dev: device to init

        Returns:
            None

        """
        cls.DEVICE = dev
        cls.DEVICE_LIST.append(dev)


"""
helper functions
"""


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


def import_device_cls(platform):
    """lazy import device class"""
    platform = platform.lower()
    if platform == "android":
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
            pf = device_platform()
            if pf is None:
                raise RuntimeError("Device not initialized yet.")
            if pf not in platforms:
                raise NotImplementedError("Method not implememted on {}. required {}.".format(pf, platforms))
            r = f(*args, **kwargs)
            return r
        return wrapper
    return decorator


def delay_after_operation():
    time.sleep(ST.OPDELAY)
