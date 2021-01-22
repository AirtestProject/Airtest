# -*- coding: utf-8 -*-
import os
import re
import sys
from enum import Enum
from airtest.utils.compat import decode_path
from wda import LANDSCAPE, PORTRAIT, LANDSCAPE_RIGHT, PORTRAIT_UPSIDEDOWN

THISPATH = decode_path(os.path.dirname(os.path.realpath(__file__)))
STATICPATH = os.path.join(THISPATH, "static")

DEFAULT_ADB_SERVER = ('127.0.0.1', 8100)
DEBUG = True
MINICAPLIB = os.path.join(STATICPATH, "minicap")
IP_PATTERN = re.compile(r'(\d+\.){3}\d+')


class CAP_METHOD(object):
    MINICAP = "MINICAP"
    MINICAP_STREAM = "MINICAP_STREAM"
    WDACAP = "WDACAP"


# now touch and ime only support wda
class TOUCH_METHOD(object):
    WDATOUCH = "WDATOUCH"


class IME_METHOD(object):
    WDAIME = "WDAIME"


class ROTATION_MODE(Enum):
    PORTRAIT = 0
    LANDSCAPE = 270
    LANDSCAPE_RIGHT = 90
    PORTRAIT_UPSIDEDOWN = 180

    @classmethod
    def _missing_(cls, value):
        # default is PORTRAIT
        return ROTATION_MODE.PORTRAIT


class KEY_EVENTS(Enum):
    home = "home"
    volumeUp = "volumeup"
    volumeDown = "volumedown"
