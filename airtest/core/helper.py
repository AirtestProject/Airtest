# -*- coding: utf-8 -*-
import functools
from airtest.core.utils import Logwrap, MoaLogger, TargetPos, is_str, get_logger


class g(object):
    """globals variables"""
    LOGGER = MoaLogger(None)
    LOGGING = get_logger("main")
    SCREEN = None
    DEVICE = None
    DEVICE_LIST = []
    KEEP_CAPTURE = False
    RECENT_CAPTURE = None
    RECENT_CAPTURE_PATH = None
    WATCHER = {}


"""
helper functions
"""


def log_in_func(data):
    if LOGGER:
        LOGGER.extra_log.update(data)


def logwrap(f):
    return Logwrap(f, LOGGER)


def moapicwrap(f):
    """
    put pic & related cv params into MoaPic object
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not is_str(args[0]):
            return f(*args, **kwargs)
        picname = args[0]
        picargs = {}
        opargs = {}
        for k, v in kwargs.iteritems():
            if k in ["whole_screen", "find_inside", "find_outside", "ignore", "focus", "rect", "threshold", "target_pos", "record_pos", "resolution", "rgb"]:
                picargs[k] = v
            else:
                opargs[k] = v
        pictarget = MoaPic(picname, **picargs)
        return f(pictarget, *args[1:], **opargs)
    return wrapper


def get_platform():
    for name, cls in device.DEV_TYPE_DICT.items():
        if DEVICE.__class__ == cls:
            return name
    return None 


def platform(on=["Android"]):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if get_platform() not in on:
                raise NotImplementedError()
            r = f(*args, **kwargs)
            return r
        return wrapper
    return decorator


def register_device(dev):
    global DEVICE, DEVICE_LIST
    DEVICE = dev
    DEVICE_LIST.append(dev)


def delay_after_operation(secs):
    delay = secs or OPDELAY
    time.sleep(delay)
