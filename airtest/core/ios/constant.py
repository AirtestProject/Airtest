# -*- coding: utf-8 -*-
import os
import re
from enum import Enum
from airtest.utils.compat import decode_path


THISPATH = decode_path(os.path.dirname(os.path.realpath(__file__)))
STATICPATH = os.path.join(THISPATH, "static")
DEFAULT_ADB_SERVER = ('127.0.0.1', 8100)
DEBUG = True
MINICAPLIB = os.path.join(STATICPATH, "minicap")
IP_PATTERN = re.compile(r'(\d+\.){3}\d+')

# When some devices (6P/7P/8P) are in landscape mode, the desktop will also change to landscape mode,
# but the click coordinates are vertical screen coordinates and require special processing
# 部分设备（6P/7P/8P）在横屏时，桌面也会变成横屏，但是点击坐标是竖屏坐标，需要特殊处理
# 由于wda不能获取到手机型号，暂时用屏幕尺寸来识别是否是plus手机
# https://developer.apple.com/design/human-interface-guidelines/ios/visual-design/adaptivity-and-layout/
LANDSCAPE_PAD_RESOLUTION = [(1242, 2208)]


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

    UIA_DEVICE_ORIENTATION_LANDSCAPERIGHT = 90
    UIA_DEVICE_ORIENTATION_PORTRAIT_UPSIDEDOWN = 0


    @classmethod
    def _missing_(cls, value):
        # default is PORTRAIT
        return ROTATION_MODE.PORTRAIT


class KEY_EVENTS(Enum):
    home = "home"
    volumeUp = "volumeup"
    volumeDown = "volumedown"
